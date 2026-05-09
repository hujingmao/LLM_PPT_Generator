"""Database models for commercial user flows.

这些类和 database/schema.sql 中的表保持一致。
SQLAlchemy ORM 负责把 Python 对象映射到 MySQL 表，接口层只操作对象，不手写 SQL。
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class User(Base):
    """用户账户表。

    保存登录信息、积分余额、累计充值金额和账户状态。
    密码字段只保存 bcrypt 哈希，永远不保存明文密码。
    """

    __tablename__ = "Users"

    # BIGINT UNSIGNED 对齐 MySQL 表结构，便于后续用户量增长。
    id: Mapped[int] = mapped_column(mysql.BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    # username/email 建唯一索引，用于注册查重和登录查询。
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # points_balance 是业务扣费依据；account_balance 记录累计充值金额，方便后台统计。
    points_balance: Mapped[int] = mapped_column(mysql.INTEGER(unsigned=True), nullable=False, default=0)
    account_balance: Mapped[Decimal] = mapped_column(mysql.DECIMAL(10, 2), nullable=False, default=Decimal("0.00"))
    status: Mapped[str] = mapped_column(Enum("active", "disabled"), nullable=False, default="active")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # ORM 关系方便从 user.recharge_orders / user.ppt_records 反查用户关联数据。
    recharge_orders: Mapped[list["RechargeOrder"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    ppt_records: Mapped[list["PPTRecord"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class RechargeOrder(Base):
    """充值订单表。

    记录用户每一次充值行为。当前为 mock 支付，后续接入真实支付时可增加第三方交易号字段。
    """

    __tablename__ = "Recharge_Orders"

    id: Mapped[int] = mapped_column(mysql.BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    # order_no 是业务订单号，给前端展示和支付平台回调匹配使用。
    order_no: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        ForeignKey("Users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(mysql.DECIMAL(10, 2), nullable=False)
    points: Mapped[int] = mapped_column(mysql.INTEGER(unsigned=True), nullable=False)
    # pending -> paid 是正常支付链路；failed/closed 预留给真实支付失败和超时关闭。
    status: Mapped[str] = mapped_column(Enum("pending", "paid", "failed", "closed"), nullable=False, default="pending")
    pay_channel: Mapped[str] = mapped_column(String(32), nullable=False, default="mock")
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship(back_populates="recharge_orders")


class PPTRecord(Base):
    """PPT 生成记录表。

    记录每次生成任务的主题、消耗积分、文件路径和最终状态，支持前端历史记录与下载。
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
    # file_path 记录服务器本地文件路径；如果后续上云，可改为对象存储 URL。
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    template_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # generating 便于将来改成异步任务；当前同步生成也先写入 generating，再更新最终状态。
    status: Mapped[str] = mapped_column(Enum("generating", "success", "failed"), nullable=False, default="generating")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship(back_populates="ppt_records")
