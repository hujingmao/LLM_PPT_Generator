"""FastAPI 请求和响应模型。

Pydantic 模型负责接口入参校验和出参序列化。这里尽量保留旧接口字段，
同时为上传资料、RAG 大纲、新导出流程补充新的稳定结构。
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


class UserCreate(BaseModel):
    """注册请求参数。"""

    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    email: str | None = Field(default=None, max_length=255)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        username = value.strip()
        if not username:
            raise ValueError("用户名不能为空")
        return username


class UserLogin(BaseModel):
    """登录请求。username 可以传用户名或邮箱。"""

    username: str
    password: str


class UserOut(BaseModel):
    """用户信息响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str | None = None
    points_balance: int
    account_balance: Decimal
    status: str
    created_at: datetime
    last_login_at: datetime | None = None


class TokenOut(BaseModel):
    """登录/注册成功后的统一响应。"""

    access_token: str
    token_type: str = "bearer"
    user: UserOut


class RechargeRequest(BaseModel):
    """模拟充值请求。"""

    package_id: str = Field(..., min_length=1)


class RechargePackage(BaseModel):
    """充值套餐响应。"""

    id: str
    name: str
    amount: Decimal
    points: int


class RechargeOrderOut(BaseModel):
    """充值订单响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_no: str
    amount: Decimal
    points: int
    status: str
    pay_channel: str
    paid_at: datetime | None = None
    created_at: datetime


class UploadedFileOut(BaseModel):
    """上传文件响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    original_filename: str
    stored_filename: str
    file_path: str
    file_type: str
    file_size: int
    parse_status: str
    parse_error: str | None = None
    created_at: datetime


class TemplateOut(BaseModel):
    """PPT 模板列表响应。前端只展示 name，id 交给导出接口。"""

    id: str
    name: str
    path: str
    exists: bool = False


class PPTGenerateRequest(BaseModel):
    """旧版一键生成接口请求。

    保留该模型是为了兼容原有 /api/ppt/generate。新页面优先使用
    /api/ppt/outline + /api/ppt/export 两步流程。
    """

    topic: str = Field(..., min_length=2, max_length=255)
    scene: str = Field(default="工作汇报", max_length=64)
    page_count: int = Field(default=8, ge=3, le=20)
    style: str = Field(default="简洁商务", max_length=64)
    retrieval_context: str = Field(default="", max_length=20000)
    reference_context: str = Field(default="", max_length=20000)
    uploaded_file_ids: list[int] = Field(default_factory=list)
    use_images: bool = True
    template_path: str | None = Field(default=None, max_length=1024)
    template_id: str | None = Field(default="default", max_length=64)


class PPTOutlineRequest(BaseModel):
    """生成 PPT 大纲请求。"""

    model_config = ConfigDict(populate_by_name=True)

    topic: str = Field(
        ...,
        min_length=2,
        max_length=255,
        validation_alias=AliasChoices("topic", "title"),
        description="PPT 主题",
    )
    scene: str = Field(default="毕业答辩", max_length=64)
    page_count: int = Field(default=8, ge=3, le=20)
    style: str = Field(default="科技蓝白", max_length=64)
    uploaded_file_ids: list[int] = Field(default_factory=list)
    reference_context: str = Field(default="", max_length=30000)


class SlideOutlineOut(BaseModel):
    """前端可编辑的单页大纲结构。"""

    page_no: int
    page_title: str
    layout_type: str = "text"
    bullets: list[str] = Field(default_factory=list)
    speaker_notes: str = ""
    image_keywords: list[str] = Field(default_factory=list)


class PPTOutlineOut(BaseModel):
    """生成大纲响应。"""

    title: str
    subtitle: str = ""
    slides: list[SlideOutlineOut]
    retrieved_context: str = ""


class PPTExportRequest(BaseModel):
    """根据用户确认后的大纲导出 PPT。"""

    outline_json: dict[str, Any] = Field(..., description="用户确认或编辑后的大纲 JSON")
    template_id: str | None = Field(default="default", max_length=64)
    template_path: str | None = Field(default=None, max_length=1024)
    style: str = Field(default="科技蓝白", max_length=64)
    use_images: bool = True
    scene: str | None = Field(default=None, max_length=64)


class PPTExportResponse(BaseModel):
    """PPT 导出成功响应。"""

    ppt_record_id: int
    download_url: str
    filename: str


class PPTRecordStatusOut(BaseModel):
    """生成进度查询响应。"""

    status: str
    progress_step: str | None = None
    error_message: str | None = None


class PPTRecordOut(BaseModel):
    """PPT 生成记录响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ppt_topic: str
    scene: str | None = None
    style: str | None = None
    page_count: int
    points_cost: int
    file_path: str | None = None
    download_url: str | None = None
    template_id: str | None = None
    template_name: str | None = None
    image_provider: str | None = None
    outline_json: str | None = None
    progress_step: str | None = None
    status: str
    error_message: str | None = None
    generated_at: datetime | None = None
    created_at: datetime


class PPTGenerateResponse(BaseModel):
    """旧版一键生成接口响应。"""

    record: PPTRecordOut
    download_url: str | None = None
