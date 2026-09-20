"""新闻相关的数据库操作（带 Redis 缓存）。

约定：
* 所有函数返回的都是 **普通字典**（小驼峰字段名），这样 ORM 查询和缓存命中
  两条路径给前端的结构完全一致。
* 缓存只是加速手段，任何缓存异常都会自动回源数据库。
"""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from cache.news_cache import (
    cache_news_detail,
    cache_related_news,
    get_cache_news_list,
    get_cached_categories,
    get_cached_news_detail,
    get_cached_related_news,
    set_cache_categories,
    set_cache_news_list,
)
from models.news import Category, News
from utils.serializers import category_item, news_detail, news_item, related_news_item


# 查所有分类
async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 10) -> list[dict]:
    # 先尝试从缓存中获取
    cached_categories = await get_cached_categories()
    if cached_categories:
        return cached_categories

    stmt = select(Category).order_by(Category.sort_order).offset(skip).limit(limit)
    result = await db.execute(stmt)
    categories = [category_item(item) for item in result.scalars().all()]

    # 写入缓存
    if categories:
        await set_cache_categories(categories)
    return categories


# 查指定分类下的新闻
async def get_news_list(
    db: AsyncSession, category_id: int, page: int = 1, page_size: int = 10
) -> list[dict]:
    # 先尝试从缓存获取新闻列表
    cached_list = await get_cache_news_list(category_id, page, page_size)
    if cached_list is not None:
        # 浏览量变化频繁，不能直接用缓存里的旧数字，这里批量补齐一次
        return await fill_views(db, cached_list)

    # 从数据库获取
    offset = (page - 1) * page_size
    stmt = (
        select(News)
        .where(News.category_id == category_id)
        .order_by(News.publish_time.desc(), News.id.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    news_list = [news_item(item) for item in result.scalars().all()]

    # 写入缓存
    if news_list:
        await set_cache_news_list(category_id, page, page_size, news_list)
    return news_list


# 用数据库里的最新浏览量覆盖列表数据（一次查询搞定，避免 N+1）
async def fill_views(db: AsyncSession, items: list[dict]) -> list[dict]:
    ids = [item["id"] for item in items if item.get("id") is not None]
    if not ids:
        return items

    result = await db.execute(select(News.id, News.views).where(News.id.in_(ids)))
    views_map = {news_id: views for news_id, views in result.all()}
    for item in items:
        if item.get("id") in views_map:
            item["views"] = views_map[item["id"]]
    return items


# 查指定分类下的新闻数量
async def get_news_count(db: AsyncSession, category_id: int) -> int:
    stmt = select(func.count(News.id)).where(News.category_id == category_id)
    result = await db.execute(stmt)
    return result.scalar_one()  # 只能有一个结果，否则报错


# 查指定新闻的详情（统一返回 camelCase 字典）
async def get_news_detail(db: AsyncSession, news_id: int) -> dict | None:
    # 先尝试从缓存中获取
    cached_news = await get_cached_news_detail(news_id)
    if cached_news:
        detail = news_detail(cached_news)
        # 浏览量是高频变化的，如果直接返回缓存值，详情页会一直显示旧数字。
        # 这里只把浏览量从数据库补齐，其余内容继续用缓存。
        detail["views"] = await get_news_views(db, news_id)
        return detail

    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    news = result.scalar_one_or_none()
    if not news:
        return None

    detail = news_detail(news)
    # 写入缓存（缓存里不包含 relatedNews，相关推荐单独缓存）
    await cache_news_detail(news_id, detail)
    return detail


# 只查浏览量（缓存命中时用来保证计数实时）
async def get_news_views(db: AsyncSession, news_id: int) -> int:
    stmt = select(News.views).where(News.id == news_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() or 0


# 更新浏览量
async def increase_news_views(db: AsyncSession, news_id: int) -> bool:
    stmt = update(News).where(News.id == news_id).values(views=News.views + 1)
    result = await db.execute(stmt)
    await db.commit()
    # 更新 > 检查数据库是否真的命中了数据 > 命中返回 true
    return result.rowcount > 0


# 查相关新闻（新闻推荐）
async def get_related_news(
    db: AsyncSession, news_id: int, category_id: int, limit: int = 5
) -> list[dict]:
    cached_related_news = await get_cached_related_news(news_id, category_id)
    if cached_related_news:
        return cached_related_news

    stmt = (
        select(News)
        .where(News.category_id == category_id, News.id != news_id)
        .order_by(News.views.desc(), News.publish_time.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    related_data = [related_news_item(item) for item in result.scalars().all()]
    if related_data:
        await cache_related_news(news_id, category_id, related_data)
    return related_data
