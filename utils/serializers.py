"""统一的序列化工具。

背景：同一份数据既可能来自数据库（ORM 对象），也可能来自 Redis 缓存（dict）。
如果两条路径返回的字段名/类型不一致，前端就会出现「有时正常、刷新后又空白」的问题。
这里把两条路径统一收敛成 **小驼峰（camelCase）** 的普通字典。
"""

from datetime import date, datetime
from typing import Any, Mapping, Optional

# 缓存或前端可能传进来的时间字段候选名（同时兼容下划线和驼峰）
_TIME_KEYS = ("publish_time", "publishTime", "history_view", "historyView",
              "favorite_time", "favoriteTime", "created_at", "createdAt",
              "view_time", "viewTime")


def _pick(source: Any, *names: str, default: Any = None) -> Any:
    """依次尝试用属性或字典键取值，取不到时返回默认值。"""
    for name in names:
        if isinstance(source, Mapping):
            if name in source and source[name] is not None:
                return source[name]
        else:
            value = getattr(source, name, None)
            if value is not None:
                return value
    return default


def to_iso(value: Any) -> Optional[str]:
    """把 datetime / date 统一转成 ISO 字符串，其它类型原样透传。"""
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def find_time(data: Mapping[str, Any]) -> Optional[str]:
    """从字典里找出时间字段并转成 ISO 字符串。"""
    for key in _TIME_KEYS:
        if key in data and data[key] is not None:
            return to_iso(data[key])
    return None


def news_item(source: Any) -> dict:
    """把 ORM 对象或缓存字典转成统一的新闻列表项。"""
    if isinstance(source, Mapping):
        return {
            "id": _pick(source, "id"),
            "title": _pick(source, "title", default=""),
            "description": _pick(source, "description"),
            "image": _pick(source, "image"),
            "author": _pick(source, "author"),
            "categoryId": _pick(source, "category_id", "categoryId"),
            "views": _pick(source, "views", default=0),
            "publishTime": find_time(source),
        }
    return {
        "id": _pick(source, "id"),
        "title": _pick(source, "title", default=""),
        "description": _pick(source, "description"),
        "image": _pick(source, "image"),
        "author": _pick(source, "author"),
        "categoryId": _pick(source, "category_id", "categoryId"),
        "views": _pick(source, "views", default=0),
        "publishTime": to_iso(_pick(source, "publish_time", "publishTime")),
    }


def news_detail(source: Any, related: Optional[list] = None) -> dict:
    """把 ORM 对象或缓存字典转成统一的新闻详情。"""
    data = news_item(source)
    data["content"] = _pick(source, "content", default="")
    data["relatedNews"] = related if related is not None else []
    return data


def related_news_item(source: Any) -> dict:
    """相关推荐项。"""
    return {
        "id": _pick(source, "id"),
        "title": _pick(source, "title", default=""),
        "image": _pick(source, "image"),
        "views": _pick(source, "views", default=0),
    }


def category_item(source: Any) -> dict:
    """新闻分类项。"""
    return {
        "id": _pick(source, "id"),
        "name": _pick(source, "name", default=""),
        "sortOrder": _pick(source, "sort_order", "sortOrder", default=0),
    }
