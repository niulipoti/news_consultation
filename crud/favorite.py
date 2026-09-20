from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.favorite import Favorite
from models.news import News
from utils.serializers import news_item


# 检查收藏状态：当前用户是否收藏了这一条新闻
async def is_news_favorite(db: AsyncSession, user_id: int, news_id: int) -> bool:
    query = select(Favorite.id).where(
        Favorite.user_id == user_id, Favorite.news_id == news_id
    )
    result = await db.execute(query)
    # 是否有收藏记录
    return result.scalar_one_or_none() is not None


# 添加收藏
async def add_news_favorite(db: AsyncSession, user_id: int, news_id: int):
    favorite = Favorite(user_id=user_id, news_id=news_id)
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)
    return favorite


# 删除收藏
async def delete_news_favorite(db: AsyncSession, user_id: int, news_id: int) -> bool:
    stmt = delete(Favorite).where(
        Favorite.user_id == user_id, Favorite.news_id == news_id
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


# 收藏列表:获取当前用户收藏的列表，分页功能
async def get_favorite_list(
    db: AsyncSession, user_id: int, page: int = 1, page_size: int = 10
):
    # 总量 + 收藏新闻列表
    count_query = select(func.count(Favorite.id)).where(Favorite.user_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # 获取收藏列表 - 联表查询 + 收藏时间 + 分页
    #  select(查询主体模型，字段别名)
    #    .join(联合查询的模型类，联合查询的条件)
    #    .where() .order_by() .offset() .limit()
    offset = (page - 1) * page_size
    query = (
        select(
            News,
            Favorite.created_at.label("favorite_time"),
            Favorite.id.label("favorite_id"),
        )
        .join(Favorite, Favorite.news_id == News.id)
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc(), Favorite.id.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)

    # 统一转成「新闻字段 + 收藏字段」的字典，避免把 ORM 对象直接塞进响应
    rows = [
        {
            **news_item(news),
            "favoriteId": favorite_id,
            "favoriteTime": favorite_time,
        }
        for news, favorite_time, favorite_id in result.all()
    ]
    return rows, total


# 清除收藏列表:当前用户的收藏列表
async def remove_all_favorite(db: AsyncSession, user_id: int) -> int:
    stmt = delete(Favorite).where(Favorite.user_id == user_id)
    result = await db.execute(stmt)
    await db.commit()
    # 返回删除的数量
    return result.rowcount or 0
