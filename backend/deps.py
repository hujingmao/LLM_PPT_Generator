"""Shared FastAPI dependencies.

这里放所有接口都会复用的依赖函数，当前核心是“从 Bearer Token 解析当前用户”。
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.security import decode_access_token


bearer_scheme = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """读取请求头中的 JWT，并返回当前登录用户。

    依赖链路：
    1. FastAPI 从 Authorization: Bearer xxx 中提取 token。
    2. decode_access_token 校验签名和过期时间，取出用户 ID。
    3. 数据库中查询用户，并确认账户状态仍然可用。
    """

    try:
        user_id = int(decode_access_token(credentials.credentials))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录状态已失效，请重新登录",
        ) from exc

    user = db.get(User, user_id)
    # Token 合法不代表账户仍然有效，所以每次都重新查库确认状态。
    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
        )
    return user
