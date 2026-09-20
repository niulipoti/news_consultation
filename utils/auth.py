from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_db
from crud import users


async def get_current_user(
    # auto_error=False：缺少 Authorization 头时由我们自己抛 401，
    # 否则 FastAPI 会返回 422，前端无法识别成「未登录」
    authorization: str | None = Header(None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    """根据 Authorization 头里的 token 查询用户，返回用户信息。

    兼容 ``Bearer xxx`` 和直接传 ``xxx`` 两种写法（前端历史上两种都用过）。
    """
    token = (authorization or "").strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少登录令牌"
        )

    user = await users.get_user_by_token(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已过期，请重新登录"
        )
    return user
