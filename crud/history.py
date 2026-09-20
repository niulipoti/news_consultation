from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.history import History
from models.news import News
from utils.serializers import news_item


# 添加浏览记录
async def add_news_history(db: AsyncSession, user_id: int, news_id: int):
    query = select(History).where(
        History.user_id == user_id, History.news_id == news_id
    )
    result = await db.execute(query)
    existing_history = result.scalar_one_or_none()
    if existing_history:
        # 已经浏览过：只更新时间，保证同一篇新闻在列表里只有一条
        existing_history.view_time = datetime.now()
        await db.commit()
        await db.refresh(existing_history)
        return existing_history

    history = History(user_id=user_id, news_id=news_id)
    db.add(history)
    await db.commit()
    await db.refresh(history)
    return history


async def get_history_list(
    db: AsyncSession, user_id: int, page: int = 1, page_size: int = 10
):
    offset = (page - 1) * page_size
    count_query = select(func.count(History.id)).where(History.user_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    query = (
        select(
            News,
            History.view_time.label("view_time"),
            History.id.label("history_id"),
        )
        .join(History, History.news_id == News.id)
        .where(History.user_id == user_id)
        .order_by(History.view_time.desc(), History.id.desc())
        .offset(offset)
        .limit(page_size)
    )

    result = await db.execute(query)
    # 统一转成「新闻字段 + 历史字段」的字典
    rows = [
        {
            **news_item(news),
            "historyId": history_id,
            "historyView": view_time,
        }
        for news, view_time, history_id in result.all()
    ]
    return rows, total


async def delete_history(db: AsyncSession, user_id: int, history_id: int) -> bool:
    query = delete(History).where(
        History.id == history_id, History.user_id == user_id
    )
    result = await db.execute(query)
    await db.commit()
    return result.rowcount > 0


async def delete_history_list(db: AsyncSession, user_id: int) -> int:
    query = delete(History).where(History.user_id == user_id)
    result = await db.execute(query)
    await db.commit()
    return result.rowcount or 0
