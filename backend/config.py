"""Backend runtime configuration.

本模块只负责读取运行时配置，不直接创建数据库连接或业务对象。
所有配置优先从环境变量读取，便于本地开发、服务器部署和容器部署复用同一套代码。
"""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


class Settings:
    """后端全局配置对象。

    这里没有使用 Pydantic Settings，是为了减少额外配置文件复杂度。
    如果后续需要区分 dev/test/prod，可把这个类替换为 pydantic-settings。
    """

    # MySQL 连接串。默认值方便本地快速启动，生产环境必须通过环境变量覆盖密码。
    database_url: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@127.0.0.1:3306/llm_ppt_generator?charset=utf8mb4",
    )

    # JWT 签名密钥与算法。jwt_secret_key 生产环境必须换成高强度随机字符串。
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-this-secret-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")

    # Token 默认有效期为 1 天，适合毕业设计/管理后台演示；正式产品可改短并加入刷新令牌。
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # CORS 白名单，允许前端单独部署在其他域名或端口。
    cors_origins: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000").split(",")
        if origin.strip()
    ]


# 导出单例配置，其他模块只读取它，不在运行过程中修改它。
settings = Settings()
