from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from crud import news as news_crud
from config.db_conf import get_db

# 创建 APIRouter 实例
# prefix 路由前缀（API接口规范文档）
# tags 分组 标签
router = APIRouter(prefix="/api/news", tags=["news"])

# 接口实现流程
# 1.模块化路由 > API 接口规范文档
# 2.定义模型类 > 数据库表（数据库设计文档）
# 3.在crud 文件夹里面创建文件，封装数据库的方法
# 4.在路由处理函数里调用crud 封装好的方法，响应结果


@router.get("/categories")
async def get_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    # 先获取数据库里面新闻分类数据 > 先定义模型类 封装查询数据的方法
    categories = await news_crud.get_categories(db, skip, limit)
    return {
        "code": 200,
        "message": "获取新闻分类成功",
        "data": categories,
    }


@router.get("/list")
async def get_news_list(
    category_id: int = Query(..., alias="categoryId"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
):
    # 先获取数据库里面新闻数据 > 先定义模型类 封装查询数据的方法

    # 思路：处理分页规则 > 查询新闻列表 > 计算总量 > 计算是否还有更多
    news_list = await news_crud.get_news_list(db, category_id, page, page_size)
    total = await news_crud.get_news_count(db, category_id)
    # 跳过的 + 当前列表的 < 总量
    has_more = (page - 1) * page_size + len(news_list) < total
    return {
        "code": 200,
        "message": "获取新闻列表成功",
        "data": {
            "list": news_list,
            "total": total,
            "hasMore": has_more,
        },
    }


@router.get("/detail")
async def get_news_detail(
    news_id: int = Query(..., alias="id"), db: AsyncSession = Depends(get_db)
):
    # 获取新闻查询 + 浏览量 +1 + 相关新闻
    news_data = await news_crud.get_news_detail(db, news_id)
    if not news_data:
        raise HTTPException(status_code=404, detail="新闻不存在")

    # 浏览量自增失败不阻断详情返回（例如新闻刚好被删除）
    await news_crud.increase_news_views(db, news_id)

    related_news = await news_crud.get_related_news(
        db, news_id, news_data["categoryId"]
    )

    return {
        "code": 200,
        "message": "success",
        "data": {**news_data, "relatedNews": related_news},
    }
