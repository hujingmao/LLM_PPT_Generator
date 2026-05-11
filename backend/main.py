"""FastAPI 后端入口。

功能覆盖：
1. 注册、登录、JWT 鉴权。
2. 积分充值、余额查询。
3. 参考资料上传、解析、写入 Chroma 向量库。
4. RAG 检索增强生成 PPT 大纲。
5. 用户确认大纲后导出 PPT、扣除积分、保存历史记录和下载文件。
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.config import FRONTEND_DIR, settings
from backend.database import get_db
from backend.deps import get_current_user
from backend.models import PPTRecord, RechargeOrder, UploadedFile, User
from backend.schemas import (
    PPTExportRequest,
    PPTExportResponse,
    PPTGenerateRequest,
    PPTGenerateResponse,
    PPTOutlineOut,
    PPTOutlineRequest,
    PPTRecordOut,
    PPTRecordStatusOut,
    RechargeOrderOut,
    RechargePackage,
    RechargeRequest,
    TemplateOut,
    TokenOut,
    UploadedFileOut,
    UserCreate,
    UserLogin,
    UserOut,
)
from backend.security import create_access_token, hash_password, verify_password
from backend.services.recharge_service import create_mock_paid_order, list_packages
from config.settings import DEFAULT_PPT_COST_PER_PAGE, UPLOAD_DIR
from models.ppt_schema import PPTPlan
from services.file_parser_service import FileParserService
from services.outline_service import OutlineService
from services.ppt_service import PPTService
from services.retrieval_service import RetrievalService
from services.template_service import TemplateService
from utils.filename_utils import sanitize_filename


app = FastAPI(title="LLM PPT Generator API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    """健康检查。"""

    return {"status": "ok"}


@app.post("/api/auth/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> TokenOut:
    """用户注册，成功后直接返回 JWT。"""

    exists_stmt = select(User).where(User.username == payload.username)
    if payload.email:
        exists_stmt = select(User).where(or_(User.username == payload.username, User.email == payload.email))
    if db.execute(exists_stmt).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名或邮箱已存在")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        points_balance=0,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名或邮箱已存在") from exc

    db.refresh(user)
    token = create_access_token(str(user.id))
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@app.post("/api/auth/login", response_model=TokenOut)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenOut:
    """用户名/邮箱登录。"""

    user = db.execute(
        select(User).where(or_(User.username == payload.username, User.email == payload.username))
    ).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账户已被禁用")

    user.last_login_at = datetime.now()
    db.commit()
    db.refresh(user)
    token = create_access_token(str(user.id))
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@app.get("/api/users/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)) -> UserOut:
    """返回当前登录用户信息。"""

    return UserOut.model_validate(current_user)


@app.get("/api/recharge/packages", response_model=list[RechargePackage])
def get_recharge_packages() -> list[dict]:
    """返回系统内置充值套餐。"""

    return list_packages()


@app.post("/api/recharge/simulate", response_model=RechargeOrderOut)
def simulate_recharge(
    payload: RechargeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RechargeOrderOut:
    """模拟支付充值。"""

    order = create_mock_paid_order(db, current_user, payload.package_id)
    return RechargeOrderOut.model_validate(order)


@app.get("/api/recharge/orders", response_model=list[RechargeOrderOut])
def list_recharge_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RechargeOrder]:
    """查询当前用户最近 50 条充值订单。"""

    return list(
        db.execute(
            select(RechargeOrder)
            .where(RechargeOrder.user_id == current_user.id)
            .order_by(RechargeOrder.created_at.desc())
            .limit(50)
        )
        .scalars()
        .all()
    )


@app.get("/api/templates", response_model=list[TemplateOut])
def list_templates() -> list[dict]:
    """返回可用模板列表。前端只展示模板名称。"""

    return TemplateService().list_templates()


@app.post("/api/files/upload", response_model=UploadedFileOut)
async def upload_reference_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UploadedFileOut:
    """上传参考资料，解析文本并写入 Chroma 向量库。"""

    original_filename = Path(file.filename or "unknown").name
    suffix = Path(original_filename).suffix.lower()
    file_type = suffix.lstrip(".")
    if file_type not in FileParserService.SUPPORTED_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{original_filename}：暂不支持该文件格式")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{original_filename}：文件为空")

    user_upload_dir = UPLOAD_DIR / str(current_user.id)
    user_upload_dir.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{uuid.uuid4().hex}_{sanitize_filename(Path(original_filename).stem)}{suffix}"
    file_path = user_upload_dir / stored_filename
    file_path.write_bytes(content)

    record = UploadedFile(
        user_id=current_user.id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_path=str(file_path),
        file_type=file_type,
        file_size=len(content),
        parse_status="pending",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    try:
        text = FileParserService().parse_file(file_path, original_filename)
        RetrievalService().ingest_file_text(current_user.id, record.id, original_filename, text)
        record.parse_status = "success"
        record.parse_error = None
    except Exception as exc:
        # 上传记录保留下来，便于前端展示具体失败原因。
        record.parse_status = "failed"
        record.parse_error = str(exc)[:2000]

    db.commit()
    db.refresh(record)
    return UploadedFileOut.model_validate(record)


@app.get("/api/files", response_model=list[UploadedFileOut])
def list_uploaded_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[UploadedFile]:
    """查询当前用户最近上传的参考资料。"""

    return list(
        db.execute(
            select(UploadedFile)
            .where(UploadedFile.user_id == current_user.id)
            .order_by(UploadedFile.created_at.desc())
            .limit(50)
        )
        .scalars()
        .all()
    )


@app.post("/api/ppt/outline", response_model=PPTOutlineOut)
def generate_ppt_outline(
    payload: PPTOutlineRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PPTOutlineOut:
    """第一步：基于主题、上传资料和补充资料生成可编辑 PPT 大纲。"""

    retrieval_context = _build_reference_context(
        db=db,
        current_user=current_user,
        topic=payload.topic,
        uploaded_file_ids=payload.uploaded_file_ids,
        reference_context=payload.reference_context,
    )

    try:
        plan = OutlineService().generate_plan(
            topic=payload.topic,
            scene=payload.scene,
            page_count=payload.page_count,
            style=payload.style,
            retrieval_context=retrieval_context,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="大模型服务暂时不可用，请稍后重试",
        ) from exc

    outline = plan.to_outline_dict()
    outline["retrieved_context"] = retrieval_context
    return PPTOutlineOut.model_validate(outline)


@app.post("/api/ppt/export", response_model=PPTExportResponse)
def export_ppt(
    payload: PPTExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PPTExportResponse:
    """第二步：根据用户确认或编辑后的大纲导出 PPT，并在成功后扣除积分。"""

    try:
        plan = PPTPlan.model_validate(payload.outline_json)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"大纲 JSON 格式不正确：{exc}") from exc

    page_count = max(len(plan.pages), 1)
    points_cost = page_count * DEFAULT_PPT_COST_PER_PAGE
    if current_user.points_balance < points_cost:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="积分不足，请先充值")

    template_path, template_meta = TemplateService().resolve_template(payload.template_id, payload.template_path)
    record = PPTRecord(
        user_id=current_user.id,
        ppt_topic=plan.ppt_title,
        scene=payload.scene,
        style=payload.style,
        page_count=page_count,
        points_cost=points_cost,
        template_id=template_meta.get("id"),
        template_name=template_meta.get("name"),
        image_provider="auto" if payload.use_images else None,
        outline_json=json.dumps(plan.to_outline_dict(), ensure_ascii=False),
        status="generating",
        progress_step="正在生成 PPT 页面……",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    try:
        if payload.use_images:
            _update_record_progress(db, record.id, "正在自动配图……")
        output_path = PPTService().generate_ppt(
            plan=plan,
            topic=plan.ppt_title,
            template_path=template_path,
            use_images=payload.use_images,
        )
        _update_record_progress(db, record.id, "正在导出 PPT 文件……")

        fresh_user = db.get(User, current_user.id)
        if not fresh_user or fresh_user.points_balance < points_cost:
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="积分不足，请先充值")

        fresh_user.points_balance -= points_cost
        record = db.get(PPTRecord, record.id)
        record.status = "success"
        record.progress_step = "生成完成"
        record.file_path = str(output_path)
        record.download_url = f"/api/ppt/download/{record.id}"
        record.generated_at = datetime.now()
        db.commit()
        db.refresh(record)
    except HTTPException as exc:
        _mark_ppt_record_failed(db, record.id, exc.detail)
        raise
    except Exception as exc:
        _mark_ppt_record_failed(db, record.id, str(exc))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="PPT 生成失败，请稍后重试") from exc

    return PPTExportResponse(
        ppt_record_id=record.id,
        download_url=record.download_url or f"/api/ppt/download/{record.id}",
        filename=Path(record.file_path).name if record.file_path else "",
    )


@app.post("/api/ppt/generate", response_model=PPTGenerateResponse)
def generate_ppt(
    payload: PPTGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PPTGenerateResponse:
    """旧版一键生成接口，保留兼容。

    内部仍然走“大纲生成 -> PPT 导出”的思路，但不会暴露中间编辑步骤。
    """

    points_cost = payload.page_count * DEFAULT_PPT_COST_PER_PAGE
    if current_user.points_balance < points_cost:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="积分不足，请先充值")

    template_path, template_meta = TemplateService().resolve_template(payload.template_id, payload.template_path)
    record = PPTRecord(
        user_id=current_user.id,
        ppt_topic=payload.topic,
        scene=payload.scene,
        style=payload.style,
        page_count=payload.page_count,
        points_cost=points_cost,
        template_id=template_meta.get("id"),
        template_name=template_meta.get("name"),
        image_provider="auto" if payload.use_images else None,
        status="generating",
        progress_step="正在生成 PPT 大纲……",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    try:
        reference_context = payload.reference_context or payload.retrieval_context
        retrieval_context = _build_reference_context(
            db=db,
            current_user=current_user,
            topic=payload.topic,
            uploaded_file_ids=payload.uploaded_file_ids,
            reference_context=reference_context,
        )
        plan = OutlineService().generate_plan(
            topic=payload.topic,
            scene=payload.scene,
            page_count=payload.page_count,
            style=payload.style,
            retrieval_context=retrieval_context,
        )
        record.outline_json = json.dumps(plan.to_outline_dict(), ensure_ascii=False)
        record.progress_step = "正在生成 PPT 页面……"
        db.commit()

        output_path = PPTService().generate_ppt(
            plan=plan,
            topic=payload.topic,
            template_path=template_path,
            use_images=payload.use_images,
        )

        fresh_user = db.get(User, current_user.id)
        if not fresh_user or fresh_user.points_balance < points_cost:
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="积分不足，请先充值")

        fresh_user.points_balance -= points_cost
        record.status = "success"
        record.progress_step = "生成完成"
        record.page_count = len(plan.pages)
        record.file_path = str(output_path)
        record.download_url = f"/api/ppt/download/{record.id}"
        record.generated_at = datetime.now()
        db.commit()
        db.refresh(record)
    except HTTPException as exc:
        _mark_ppt_record_failed(db, record.id, exc.detail)
        raise
    except Exception as exc:
        _mark_ppt_record_failed(db, record.id, str(exc))
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="大模型服务暂时不可用，请稍后重试") from exc

    return PPTGenerateResponse(record=PPTRecordOut.model_validate(record), download_url=record.download_url)


@app.get("/api/ppt/records", response_model=list[PPTRecordOut])
def list_ppt_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PPTRecord]:
    """查询当前用户最近 50 条 PPT 生成记录。"""

    return list(
        db.execute(
            select(PPTRecord)
            .where(PPTRecord.user_id == current_user.id)
            .order_by(PPTRecord.created_at.desc())
            .limit(50)
        )
        .scalars()
        .all()
    )


@app.get("/api/ppt/records/{record_id}/status", response_model=PPTRecordStatusOut)
def get_ppt_record_status(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PPTRecordStatusOut:
    """查询某条 PPT 生成记录的状态。"""

    record = db.get(PPTRecord, record_id)
    if not record or record.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="记录不存在")
    return PPTRecordStatusOut(
        status=record.status,
        progress_step=record.progress_step,
        error_message=record.error_message,
    )


@app.get("/api/ppt/download/{record_id}")
def download_ppt(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """下载某条生成记录对应的 PPT 文件。"""

    record = db.get(PPTRecord, record_id)
    if not record or record.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="记录不存在")
    if record.status != "success" or not record.file_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PPT 尚未生成成功")

    file_path = Path(record.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PPT 文件不存在")

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )


def _build_reference_context(
    db: Session,
    current_user: User,
    topic: str,
    uploaded_file_ids: list[int],
    reference_context: str,
) -> str:
    """拼接向量检索结果和用户手动补充资料。"""

    context_parts: list[str] = []
    clean_file_ids = [file_id for file_id in uploaded_file_ids if file_id]
    if clean_file_ids:
        files = _get_owned_uploaded_files(db, current_user.id, clean_file_ids)
        failed_files = [item for item in files if item.parse_status != "success"]
        if failed_files:
            messages = [
                f"{item.original_filename}：{item.parse_error or '解析失败'}"
                for item in failed_files
            ]
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件解析失败：" + "；".join(messages))
        try:
            retrieved = RetrievalService().retrieve_context(topic, current_user.id, clean_file_ids)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="检索服务暂时不可用，请稍后重试") from exc
        if retrieved:
            context_parts.append("【向量检索结果】\n" + retrieved)

    if reference_context and reference_context.strip():
        context_parts.append("【用户手动补充资料】\n" + reference_context.strip())
    return "\n\n".join(context_parts)


def _get_owned_uploaded_files(db: Session, user_id: int, file_ids: list[int]) -> list[UploadedFile]:
    """确认资料属于当前用户，避免越权引用他人文件。"""

    files = list(
        db.execute(
            select(UploadedFile)
            .where(UploadedFile.user_id == user_id, UploadedFile.id.in_(file_ids))
        )
        .scalars()
        .all()
    )
    found_ids = {item.id for item in files}
    missing_ids = [file_id for file_id in file_ids if file_id not in found_ids]
    if missing_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"上传文件不存在：{missing_ids}")
    return files


def _update_record_progress(db: Session, record_id: int, progress_step: str) -> None:
    record = db.get(PPTRecord, record_id)
    if not record:
        return
    record.progress_step = progress_step
    db.commit()


def _mark_ppt_record_failed(db: Session, record_id: int, error_message: str) -> None:
    """把生成记录标记为失败。"""

    db.rollback()
    record = db.get(PPTRecord, record_id)
    if not record:
        return
    record.status = "failed"
    record.progress_step = "生成失败"
    record.error_message = (error_message or "未知错误")[:2000]
    db.commit()


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
