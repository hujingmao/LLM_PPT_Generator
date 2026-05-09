"""Database models for commercial user flows."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class User(Base):
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


class RechargeOrder(Base):
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


class PPTRecord(Base):
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
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    template_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(Enum("generating", "success", "failed"), nullable=False, default="generating")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship(back_populates="ppt_records")
