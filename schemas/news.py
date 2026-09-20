from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from schemas.base import NewsItemBase


class RelatedNewsResponse(BaseModel):
    """相关推荐：只返回列表展示需要的少量字段。"""

    id: int
    title: str
    image: Optional[str] = None
    views: int = 0

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )


class NewsDetailResponse(NewsItemBase):
    """新闻详情。"""

    content: str
    related_news: list[RelatedNewsResponse] = Field(
        default_factory=list, alias="relatedNews"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )


class CategoryResponse(BaseModel):
    """新闻分类。"""

    id: int
    name: str
    sort_order: int = Field(0, alias="sortOrder")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )
