"""Request and response schemas."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserCreate(BaseModel):
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
    username: str
    password: str


class UserOut(BaseModel):
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
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class RechargeRequest(BaseModel):
    package_id: str = Field(..., min_length=1)


class RechargePackage(BaseModel):
    id: str
    name: str
    amount: Decimal
    points: int


class RechargeOrderOut(BaseModel):
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
    topic: str = Field(..., min_length=2, max_length=255)
    scene: str = Field(default="工作汇报", max_length=64)
    page_count: int = Field(default=8, ge=3, le=20)
    style: str = Field(default="简洁商务", max_length=64)
    retrieval_context: str = Field(default="", max_length=20000)
    use_images: bool = True
    template_path: str | None = Field(default=None, max_length=1024)


class PPTRecordOut(BaseModel):
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
    record: PPTRecordOut
    download_url: str | None = None
