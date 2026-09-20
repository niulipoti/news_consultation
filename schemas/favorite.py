from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from schemas.base import NewsItemBase


class FavoriteCheckResponse(BaseModel):
    """查看收藏状态。"""

    is_favorite: bool = Field(..., alias="isFavorite")

    model_config = ConfigDict(populate_by_name=True)


class FavoriteAddRequest(BaseModel):
    """添加收藏的请求体（写操作不应该复用响应模型）。"""

    news_id: int = Field(..., alias="newsId", description="新闻ID")

    model_config = ConfigDict(populate_by_name=True)


class FavoriteAddResponse(BaseModel):
    """添加收藏的结果。"""

    id: int = Field(..., description="收藏记录ID")
    news_id: int = Field(..., alias="newsId", description="新闻ID")
    created_at: Optional[datetime] = Field(None, alias="createdAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class FavoriteNewsItemResponse(NewsItemBase):
    """收藏列表项 = 新闻字段 + 收藏信息。"""

    favorite_id: int = Field(alias="favoriteId")
    favorite_time: datetime = Field(alias="favoriteTime")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )


class FavoriteListResponse(BaseModel):
    """收藏列表接口响应的模型类。"""

    list: list[FavoriteNewsItemResponse]
    total: int
    has_more: bool = Field(alias="hasMore")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )
