from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from schemas.base import NewsItemBase


class HistoryAddRequest(BaseModel):
    """添加浏览记录的请求体。"""

    news_id: int = Field(..., alias="newsId", description="新闻ID")

    model_config = ConfigDict(populate_by_name=True)


class HistoryNewsItemResponse(NewsItemBase):
    """浏览历史列表项 = 新闻字段 + 历史信息。"""

    history_id: int = Field(alias="historyId")
    history_view: datetime = Field(alias="historyView")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )


class HistoryListResponse(BaseModel):
    """浏览历史列表接口响应的模型类。"""

    list: list[HistoryNewsItemResponse]
    total: int
    has_more: bool = Field(alias="hasMore")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )
