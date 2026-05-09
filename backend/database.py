"""SQLAlchemy database wiring.

该模块集中管理 SQLAlchemy 的 Engine、Session 工厂和 FastAPI 数据库依赖。
业务层只需要通过 get_db 获取会话，避免在接口中重复创建连接。
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.config import settings


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。

    SQLAlchemy 会通过这个 Base 收集模型元数据，用于 ORM 映射和后续迁移扩展。
    """

    pass


# Engine 是进程级对象，内部维护连接池；pool_pre_ping 可避免 MySQL 长连接超时后继续复用坏连接。
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    future=True,
)

# 每次请求会创建一个独立 Session；关闭请求时释放连接回连接池。
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：为一个请求提供一个数据库会话。

    yield 前创建会话，接口执行结束后 finally 中关闭，保证异常情况下也不会泄漏连接。
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
