from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_db
from crud import users
from models.users import User
from schemas.users import (
    UserAuthResponse,
    UserChangePasswordRequest,
    UserInfoResponse,
    UserLoginRequest,
    UserRequest,
    UserUpdateRequest,
)
from utils.auth import get_current_user
from utils.response import success_response

router = APIRouter(prefix="/api/user", tags=["users"])


@router.post("/register")
async def register(user_data: UserRequest, db: AsyncSession = Depends(get_db)):
    # 注册逻辑：1.验证用户是否存在 > 2.创建用户 > 3.生成Token > 4.返回结果
    existing_user = await users.get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户已存在")

    user = await users.create_user(db, user_data)
    token = await users.create_token(db, user.id)
    response_data = UserAuthResponse(
        token=token, userInfo=UserInfoResponse.model_validate(user)
    )
    return success_response(message="注册成功", data=response_data)


@router.post("/login")
async def login(user_data: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    # 登录逻辑：1.验证用户是否存在 > 2.验证密码 > 3.生成Token > 4.返回结果
    user = await users.authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )

    token = await users.create_token(db, user.id)
    response_data = UserAuthResponse(
        token=token, userInfo=UserInfoResponse.model_validate(user)
    )
    return success_response(message="登录成功", data=response_data)


# 获取用户信息: 1.获取用户ID > 2.查Token是否有效 > 3.返回结果
# 查Token查用户 > 封装crud > 功能整合成一个工具函数 > 路由导入使用 : 依赖注入的方式
@router.get("/info")
async def get_user_info(user: User = Depends(get_current_user)):
    return success_response(
        message="获取用户信息成功", data=UserInfoResponse.model_validate(user)
    )


# 修改用户信息：验证Token > 更新 (用户输入数据 put 提交 > 请求体参数 > 定义pydantic模型类) > 返回结果
# 参数：用户输入 + 验证Token + db（调用crud更新方法）
@router.put("/update")
async def update_user_info(
    user_data: UserUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    updated_user = await users.update_user(db, user.username, user_data)
    return success_response(
        message="修改用户信息成功", data=UserInfoResponse.model_validate(updated_user)
    )


@router.put("/password")
async def update_password(
    password_data: UserChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await users.change_password(
        db, user, password_data.old_password, password_data.new_password
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="原密码错误，修改密码失败"
        )
    return success_response(message="修改密码成功")


@router.post("/logout")
async def logout(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """退出登录：删除当前用户的令牌记录。"""
    await users.remove_token(db, user.id)
    return success_response(message="退出登录成功")
