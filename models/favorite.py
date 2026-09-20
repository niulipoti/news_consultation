"""收藏表的 ORM 模型。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from models.news import News
from models.users import Base, User


class Favorite(Base):
    """
    收藏表ORM模型
    """

    __tablename__ = "favorite"
    # 创建索引
    # UniqueConstraint: 创建唯一索引，保证同一用户对同一篇新闻只能收藏一次
    __table_args__ = (
        UniqueConstraint("user_id", "news_id", name="user_news_unique"),
        Index("fk_favorite_user_idx", "user_id"),
        Index("fk_favorite_news_idx", "news_id"),
    )
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="收藏ID"
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(User.id), nullable=False, comment="用户ID"
    )
    news_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(News.id), nullable=False, comment="新闻ID"
    )
    # 统一使用本地时间（naive datetime），与 history.view_time 保持一致，
    # 避免 aware / naive 混用导致比较时报 TypeError
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False, comment="收藏时间"
    )

    def __repr__(self):
        return (
            f"<Favorite(id={self.id},user_id={self.user_id},"
            f"news_id={self.news_id},created_at={self.created_at})>"
        )
