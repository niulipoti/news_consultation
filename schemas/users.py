from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserRequest(BaseModel):
    """注册请求体。"""

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=64, description="密码")


class UserLoginRequest(BaseModel):
    """登录请求体：只校验非空，避免历史弱密码用户无法登录。"""

    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, max_length=64, description="密码")


class UserInfoBase(BaseModel):
    """
    用户信息基础数据模型
    """

    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")


class UserInfoResponse(UserInfoBase):
    id: int
    username: str

    # 模型类配置
    model_config = ConfigDict(
        from_attributes=True,  # 允许从 ORM 对象属性中取值
        populate_by_name=True,
    )


class UserAuthResponse(BaseModel):
    """登录 / 注册成功后的 data 部分。"""

    token: str
    user_info: UserInfoResponse = Field(..., alias="userInfo")

    # 模型类配置
    model_config = ConfigDict(
        populate_by_name=True,  # alias / 字段名兼容
        from_attributes=True,  # 允许从 ORM 对象属性中取值
    )


class UserUpdateRequest(BaseModel):
    """更新用户信息的模型类。"""

    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")


class UserChangePasswordRequest(BaseModel):
    """更改密码的模型类。"""

    old_password: str = Field(..., alias="oldPassword", description="旧密码")
    new_password: str = Field(
        ..., min_length=6, max_length=64, alias="newPassword", description="新密码"
    )

    model_config = ConfigDict(populate_by_name=True)
