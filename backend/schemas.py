"""Request and response schemas.

Pydantic 模型用于接口入参校验和出参序列化。
请求模型控制用户能传什么，响应模型控制哪些字段能返回给前端，避免泄露 password_hash。
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserCreate(BaseModel):
    """注册请求参数。"""

    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    email: str | None = Field(default=None, max_length=255)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        """清理用户名首尾空格，并拒绝空用户名。"""

        username = value.strip()
        if not username:
            raise ValueError("用户名不能为空")
        return username


class UserLogin(BaseModel):
    """登录请求参数。username 字段既可传用户名，也可传邮箱。"""

    username: str
    password: str


class UserOut(BaseModel):
    """用户信息响应。

    from_attributes=True 允许直接从 SQLAlchemy ORM 对象转换为响应模型。
    """

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
    """模拟充值请求，只需要传套餐 ID。"""

    package_id: str = Field(..., min_length=1)


class RechargePackage(BaseModel):
    """前端展示的充值套餐。"""

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


class PPTGenerateRequest(BaseModel):
    """PPT 生成请求。

    retrieval_context 可由前端粘贴参考资料，也可以后续替换成文件上传/知识库检索结果。
    """

    topic: str = Field(..., min_length=2, max_length=255)
    scene: str = Field(default="工作汇报", max_length=64)
    page_count: int = Field(default=8, ge=3, le=20)
    style: str = Field(default="简洁商务", max_length=64)
    retrieval_context: str = Field(default="", max_length=20000)
    use_images: bool = True
    template_path: str | None = Field(default=None, max_length=1024)


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
    template_name: str | None = None
    image_provider: str | None = None
    status: str
    error_message: str | None = None
    generated_at: datetime | None = None
    created_at: datetime


class PPTGenerateResponse(BaseModel):
    """PPT 生成成功后的响应，包含记录信息和下载地址。"""

    record: PPTRecordOut
    download_url: str | None = None
