"""后端运行时配置。

数据库连接、JWT 密钥、CORS 等部署相关配置从环境变量读取。
为了避免把敏感信息写死到代码中，本文件不会提供真实密钥或数据库密码。
"""

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
load_dotenv(BASE_DIR / ".env")


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"缺少环境变量 {name}，请在 .env 或系统环境变量中配置。")
    return value


def _build_database_url() -> str:
    """优先使用 DATABASE_URL；没有时再由 MySQL 分项配置拼接。"""

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    password = _required_env("MYSQL_PASSWORD")
    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    user = os.getenv("MYSQL_USER", "root")
    database = os.getenv("MYSQL_DATABASE", "llm_ppt_generator")

    return (
        f"mysql+pymysql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{database}?charset=utf8mb4"
    )


class Settings:
    """后端全局配置对象。"""

    database_url: str = _build_database_url()
    jwt_secret_key: str = _required_env("JWT_SECRET_KEY")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    cors_origins: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000").split(",")
        if origin.strip()
    ]


settings = Settings()
