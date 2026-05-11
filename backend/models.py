"""数据库 ORM 模型。

本文件只描述业务数据结构，接口层通过 SQLAlchemy Session 操作这些模型。
已有的用户、充值订单、PPT 生成记录保持兼容，新功能在现有表上增量扩展。
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class User(Base):
    """用户账户表。

    保存登录信息、积分余额、累计充值金额和账户状态。密码只保存哈希值，
    不保存明文，便于答辩时说明系统的基本安全设计。
    """

    __tablename__ = "Users"

    id: Mapped[int] = mapped_column(mysql.BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    points_balance: Mapped[int] = mapped_column(mysql.INTEGER(unsigned=True), nullable=False, default=0)
    account_balance: Mapped[Decimal] = mapped_column(mysql.DECIMAL(10, 2), nullable=False, default=Decimal("0.00"))
    status: Mapped[str] = mapped_column(Enum("active", "disabled"), nullable=False, default="active")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    recharge_orders: Mapped[list["RechargeOrder"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    ppt_records: Mapped[list["PPTRecord"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    uploaded_files: Mapped[list["UploadedFile"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class RechargeOrder(Base):
    """积分充值订单表。

    当前项目使用模拟支付，保留订单表可以完整展示“充值 -> 积分到账 -> 生成扣费”的闭环。
    """

    __tablename__ = "Recharge_Orders"

    id: Mapped[int] = mapped_column(mysql.BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        ForeignKey("Users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(mysql.DECIMAL(10, 2), nullable=False)
    points: Mapped[int] = mapped_column(mysql.INTEGER(unsigned=True), nullable=False)
    status: Mapped[str] = mapped_column(Enum("pending", "paid", "failed", "closed"), nullable=False, default="pending")
    pay_channel: Mapped[str] = mapped_column(String(32), nullable=False, default="mock")
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship(back_populates="recharge_orders")


class UploadedFile(Base):
    """用户上传资料表。

    只保存文件基础信息和解析状态。解析后的文本片段写入 Chroma 向量库，
    并在 metadata 中记录 user_id/file_id，便于按用户和文件做检索过滤。
    """

    __tablename__ = "uploaded_files"

    id: Mapped[int] = mapped_column(mysql.BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        ForeignKey("Users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_type: Mapped[str] = mapped_column(String(16), nullable=False)
    file_size: Mapped[int] = mapped_column(mysql.BIGINT(unsigned=True), nullable=False, default=0)
    parse_status: Mapped[str] = mapped_column(Enum("pending", "success", "failed"), nullable=False, default="pending")
    parse_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="uploaded_files")


class PPTRecord(Base):
    """PPT 生成记录表。

    旧字段继续保留，新流程新增 outline_json、progress_step、download_url 等字段，
    用于展示“大纲预览 -> 用户确认 -> 导出 PPT”的完整状态。
    """

    __tablename__ = "PPT_Records"

    id: Mapped[int] = mapped_column(mysql.BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        ForeignKey("Users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    ppt_topic: Mapped[str] = mapped_column(String(255), nullable=False)
    scene: Mapped[str | None] = mapped_column(String(64), nullable=True)
    style: Mapped[str | None] = mapped_column(String(64), nullable=True)
    page_count: Mapped[int] = mapped_column(mysql.INTEGER(unsigned=True), nullable=False, default=0)
    points_cost: Mapped[int] = mapped_column(mysql.INTEGER(unsigned=True), nullable=False, default=0)
    template_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    template_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    outline_json: Mapped[str | None] = mapped_column(mysql.LONGTEXT, nullable=True)
    progress_step: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    download_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("outline_ready", "generating", "success", "failed"),
        nullable=False,
        default="generating",
    )
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship(back_populates="ppt_records")
