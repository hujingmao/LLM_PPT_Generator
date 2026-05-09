"""Backend runtime configuration."""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@127.0.0.1:3306/llm_ppt_generator?charset=utf8mb4",
    )
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-this-secret-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    cors_origins: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000").split(",")
        if origin.strip()
    ]


settings = Settings()
