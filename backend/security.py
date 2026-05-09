"""Password hashing and JWT helpers.

认证安全相关逻辑集中在这里，接口层不直接接触 bcrypt 或 JWT 细节。
"""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.config import settings


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """将明文密码转换为不可逆哈希。

    数据库永远只保存哈希值，不保存明文密码。
    """

    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """校验用户输入密码和数据库中的哈希是否匹配。"""

    return password_context.verify(password, password_hash)


def create_access_token(subject: str) -> str:
    """生成访问令牌。

    subject 这里放用户 ID；exp 是标准 JWT 过期字段，后续 decode 时会自动校验。
    """

    expire_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": expire_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    """解析并校验访问令牌，返回 token 中的用户 ID。"""

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Token 无效或已过期") from exc

    subject = payload.get("sub")
    if not subject:
        raise ValueError("Token 缺少用户标识")
    return str(subject)
