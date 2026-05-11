"""密码哈希与 JWT 工具。"""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.config import settings


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """把明文密码转换为不可逆哈希。"""

    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """校验用户输入密码是否与数据库中的哈希匹配。"""

    return password_context.verify(password, password_hash)


def create_access_token(subject: str) -> str:
    """生成 JWT 访问令牌。subject 当前保存用户 ID。"""

    expire_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": expire_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    """解析并校验访问令牌，返回用户 ID。"""

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Token 无效或已过期") from exc

    subject = payload.get("sub")
    if not subject:
        raise ValueError("Token 缺少用户标识")
    return str(subject)
