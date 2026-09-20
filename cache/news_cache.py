# 新闻相关的缓存方法：新闻分类、列表、详情、相关推荐的读写
# key - value
from typing import Any, Dict, List, Optional

from utils.cache import delete_cache, get_json_cache, set_cache
from utils.serializers import category_item, news_item, related_news_item

CATEGORIES_KEY = "news:categories"

NEWS_LIST_PREFIX = "news_list:"

NEWS_DETAIL_PREFIX = "news:detail:"

RELATED_NEWS_PREFIX = "news:related:"


# 获取新闻分类缓存
async def get_cached_categories() -> Optional[List[Dict[str, Any]]]:
    data = await get_json_cache(CATEGORIES_KEY)
    if not data:
        return None
    return [category_item(item) for item in data]


# 写入新闻分类缓存:缓存数据，过期时间
# 分类、配置: 7200；列表:600；详情:1800；验证码:120；--数据越稳定，缓存越持久
# 避免所有key同时过期，引起缓存雪崩
async def set_cache_categories(data: List[Dict[str, Any]], expire: int = 7200) -> bool:
    return await set_cache(CATEGORIES_KEY, data, expire)


# 写入缓存-新闻列表 key = news_list:分类ID:页码:每页数量 + 列表数据 + 过期时间
async def set_cache_news_list(
    category_id: Optional[int],
    page: int,
    page_size: int,
    data: List[Dict[str, Any]],
    expire: int = 600,
) -> bool:
    # 调用封装的 redis 设置的方法，存新闻列表到缓存
    return await set_cache(news_list_key(category_id, page, page_size), data, expire)


def news_list_key(category_id: Optional[int], page: int, page_size: int) -> str:
    """生成新闻列表的缓存 key。"""
    category_part = category_id if category_id is not None else "all"
    return f"{NEWS_LIST_PREFIX}{category_part}:{page}:{page_size}"


# 读取缓存-新闻列表（统一成小驼峰，兼容历史遗留的旧缓存数据）
async def get_cache_news_list(
    category_id: Optional[int], page: int, page_size: int
) -> Optional[List[Dict[str, Any]]]:
    data = await get_json_cache(news_list_key(category_id, page, page_size))
    if not data:
        return None
    return [news_item(item) for item in data]


async def get_cached_news_detail(news_id: int) -> Optional[Dict[str, Any]]:
    data = await get_json_cache(f"{NEWS_DETAIL_PREFIX}{news_id}")
    if not data:
        return None
    # 缓存里存的是不含 relatedNews 的详情，这里补一个空列表保证结构完整
    return news_item(data) | {"content": data.get("content") or ""}


async def cache_news_detail(
    news_id: int, news_data: Dict[str, Any], expire: int = 300
) -> bool:
    return await set_cache(f"{NEWS_DETAIL_PREFIX}{news_id}", news_data, expire)


async def cache_related_news(
    news_id: int,
    category_id: int,
    related_list: List[Dict[str, Any]],
    expire: int = 1800,
) -> bool:
    return await set_cache(
        f"{RELATED_NEWS_PREFIX}{news_id}:{category_id}", related_list, expire
    )


async def get_cached_related_news(
    news_id: int, category_id: int
) -> Optional[List[Dict[str, Any]]]:
    data = await get_json_cache(f"{RELATED_NEWS_PREFIX}{news_id}:{category_id}")
    if not data:
        return None
    return [related_news_item(item) for item in data]


async def clear_news_cache(news_id: Optional[int] = None) -> None:
    """清理缓存：新闻内容更新后调用，避免读到过期数据。"""
    keys = [CATEGORIES_KEY]
    if news_id is not None:
        keys.append(f"{NEWS_DETAIL_PREFIX}{news_id}")
    await delete_cache(*keys)
