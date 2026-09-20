import uuid
from datetime import datetime, timedelta

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from models.users import User, UserToken
from schemas.users import UserRequest, UserUpdateRequest
from utils import security
from utils.security import get_password_hash


# 用户名查询数据库
async def get_user_by_username(db: AsyncSession, username: str):
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    return result.scalar_one_or_none()


# 创建用户
async def create_user(db: AsyncSession, user_data: UserRequest):
    # 先密码加密 > add
    hashed_password = get_password_hash(user_data.password)
    user = User(username=user_data.username, password=hashed_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)  # 从数据库读回最新的 user
    return user


# 生成Token
async def create_token(db: AsyncSession, user_id: int):
    # 生成 Token > 设置过期时间 > 查询数据库当前用户是否有Token > 更新；没有Token > 添加
    token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(days=7)
    query = select(UserToken).where(UserToken.user_id == user_id)
    result = await db.execute(query)
    user_token = result.scalar_one_or_none()

    if user_token:
        user_token.token = token
        user_token.expires_at = expires_at
    else:
        user_token = UserToken(user_id=user_id, token=token, expires_at=expires_at)
        db.add(user_token)
    await db.commit()
    return token


# 验证用户
async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not security.verify_password(password, user.password):
        return None

    return user


# 根据Token查询用户：验证Token有效性 > 获取用户ID
async def get_user_by_token(db: AsyncSession, token: str):
    if not token:
        return None
    query = select(UserToken).where(UserToken.token == token)
    result = await db.execute(query)
    db_token = result.scalar_one_or_none()
    if not db_token:
        return None
    if db_token.expires_at < datetime.now():
        return None
    query = select(User).where(User.id == db_token.user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


# 退出登录：删除该用户的令牌记录
async def remove_token(db: AsyncSession, user_id: int) -> bool:
    stmt = delete(UserToken).where(UserToken.user_id == user_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


# 更新用户信息 update更新 > 检查是否命中了数据 > 获取更新后的用户
async def update_user(db: AsyncSession, username: str, user_data: UserUpdateRequest):
    # query = update(User).where(User.username == username).values(字段 = 值, ...)
    # user_data 是一个 pydantic 类型，用 model_dump 得到字典
    # 没有设置值的不更新
    values = user_data.model_dump(exclude_unset=True, exclude_none=True)
    if values:
        query = update(User).where(User.username == username).values(**values)
        result = await db.execute(query)
        await db.commit()
        # 检查更新
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="用户不存在")

    # 获取更新后的用户信息
    return await get_user_by_username(db, username)


# 修改密码：验证旧密码 > 新密码加密 > 修改密码
async def change_password(
    db: AsyncSession, user: User, old_password: str, new_password: str
):
    if not security.verify_password(old_password, user.password):
        return False
    hashed_new_pwd = security.get_password_hash(new_password)
    user.password = hashed_new_pwd
    # 更新：由 SQLAlchemy 真正接管这个 user 对象，确保可以 commit
    # 规避 session 过期或关闭导致的不能提交的问题
    db.add(user)  # 确保数据更新到数据库
    await db.commit()
    await db.refresh(user)
    return True
