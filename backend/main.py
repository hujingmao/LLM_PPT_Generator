"""FastAPI app for the commercial PPT generator backend.

这是前后端分离版本的唯一后端入口：
1. 提供注册、登录、JWT 鉴权。
2. 提供充值套餐、模拟支付和订单查询。
3. 提供 PPT 生成、历史记录和文件下载。
4. 挂载 frontend/ 静态页面，让一个 uvicorn 进程即可跑完整演示。
"""

from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.config import FRONTEND_DIR, settings
from backend.database import get_db
from backend.deps import get_current_user
from backend.models import PPTRecord, RechargeOrder, User
from backend.schemas import (
    PPTGenerateRequest,
    PPTGenerateResponse,
    PPTRecordOut,
    RechargeOrderOut,
    RechargePackage,
    RechargeRequest,
    TokenOut,
    UserCreate,
    UserLogin,
    UserOut,
)
from backend.security import create_access_token, hash_password, verify_password
from backend.services.recharge_service import create_mock_paid_order, list_packages
from config.settings import DEFAULT_PPT_COST_PER_PAGE, DEFAULT_TEMPLATE_PATH, TEMPLATE_DIR
from services.outline_service import OutlineService
from services.ppt_service import PPTService


app = FastAPI(title="LLM PPT Generator API", version="1.0.0")

# 允许前端跨域访问 API。当前默认前端由同一个 FastAPI 服务托管，也兼容独立部署。
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    """健康检查接口，用于确认后端进程是否正常启动。"""

    return {"status": "ok"}


@app.post("/api/auth/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> TokenOut:
    """用户注册。

    注册成功后直接签发 JWT，前端无需再额外登录一次。
    """

    # 支持 username 必填、email 可选；如果传了 email，则两个字段都要做唯一性检查。
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
        # commit 可能因为并发注册触发唯一索引冲突，所以这里仍然捕获 IntegrityError。
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名或邮箱已存在") from exc

    db.refresh(user)
    token = create_access_token(str(user.id))
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@app.post("/api/auth/login", response_model=TokenOut)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenOut:
    """用户登录。

    username 字段允许传用户名或邮箱，验证成功后刷新 last_login_at 并签发 JWT。
    """

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
    """返回当前登录用户信息，前端刷新页面时用它恢复登录态。"""

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
    """模拟支付充值。

    当前接口点击后立即到账，适合演示商业化闭环。
    真实产品中应改为：创建 pending 订单 -> 跳转支付 -> 支付回调更新订单和积分。
    """

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


@app.post("/api/ppt/generate", response_model=PPTGenerateResponse)
def generate_ppt(
    payload: PPTGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PPTGenerateResponse:
    """同步生成 PPT 并扣除积分。

    主要流程：
    1. 按页数计算积分消耗并做余额预检查。
    2. 创建 generating 状态的 PPT 记录，方便失败时也能留下错误原因。
    3. 调用大模型生成结构化大纲，再交给 PPTService 写入 .pptx。
    4. 再次检查余额，扣积分并把记录更新为 success。
    """

    points_cost = payload.page_count * DEFAULT_PPT_COST_PER_PAGE
    if current_user.points_balance < points_cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"积分不足，本次需要 {points_cost} 积分",
        )

    # template_path 为空时使用 templates/default_master.pptx；不存在则使用代码内置版式。
    template_path = _resolve_template_path(payload.template_path)
    effective_template_path = template_path or (DEFAULT_TEMPLATE_PATH if DEFAULT_TEMPLATE_PATH.exists() else None)
    record = PPTRecord(
        user_id=current_user.id,
        ppt_topic=payload.topic,
        scene=payload.scene,
        style=payload.style,
        page_count=payload.page_count,
        points_cost=points_cost,
        template_name=effective_template_path.name if effective_template_path else None,
        image_provider="auto" if payload.use_images else None,
        status="generating",
    )
    db.add(record)
    # 先落库生成记录，确保后续生成失败时也能反写 failed 状态和错误信息。
    db.commit()
    db.refresh(record)

    try:
        outline_service = OutlineService()
        plan = outline_service.generate_plan(
            topic=payload.topic,
            scene=payload.scene,
            page_count=payload.page_count,
            style=payload.style,
            retrieval_context=payload.retrieval_context,
        )
        output_path = PPTService().generate_ppt(
            plan=plan,
            topic=payload.topic,
            template_path=effective_template_path,
            use_images=payload.use_images,
        )

        # 生成过程可能比较久，这里重新查用户余额，避免并发请求重复使用旧余额。
        fresh_user = db.get(User, current_user.id)
        if not fresh_user or fresh_user.points_balance < points_cost:
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="积分不足")

        # 扣积分和生成记录更新放在同一事务提交，保证账务和历史记录一致。
        fresh_user.points_balance -= points_cost
        record.status = "success"
        record.page_count = len(plan.pages) + 3
        record.file_path = str(output_path)
        record.generated_at = datetime.now()
        db.commit()
        db.refresh(record)
    except HTTPException:
        _mark_ppt_record_failed(db, record.id, "积分不足")
        raise
    except Exception as exc:
        _mark_ppt_record_failed(db, record.id, str(exc))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"PPT 生成失败：{exc}") from exc

    return PPTGenerateResponse(
        record=PPTRecordOut.model_validate(record),
        download_url=f"/api/ppt/download/{record.id}",
    )


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


@app.get("/api/ppt/download/{record_id}")
def download_ppt(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """下载某条生成记录对应的 PPT 文件。

    下载时必须校验记录归属当前用户，避免用户通过猜 ID 下载别人的文件。
    """

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


def _resolve_template_path(template_path: str | None) -> Path | None:
    """解析前端传入的模板路径，并确保它指向真实的 .pptx 文件。"""

    if not template_path:
        return None
    path = Path(template_path)
    if not path.is_absolute():
        template_candidate = TEMPLATE_DIR / path
        path = template_candidate if template_candidate.exists() else Path.cwd() / path
    path = path.resolve()
    if path.suffix.lower() != ".pptx" or not path.exists():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="模板文件不存在或不是 .pptx")
    return path


def _mark_ppt_record_failed(db: Session, record_id: int, error_message: str) -> None:
    """把生成记录标记为失败。

    先 rollback 是因为调用方可能刚经历异常，当前 Session 处于不可继续提交的状态。
    """

    db.rollback()
    record = db.get(PPTRecord, record_id)
    if not record:
        return
    record.status = "failed"
    record.error_message = error_message[:2000]
    db.commit()


if FRONTEND_DIR.exists():
    # 放在最后挂载静态页面，避免 "/" 抢先匹配 API 路由。
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
