from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_db
from crud import history
from models.users import User
from schemas.history import HistoryAddRequest, HistoryListResponse
from utils.auth import get_current_user
from utils.response import success_response

router = APIRouter(prefix="/api/history", tags=["history"])


# 添加浏览记录
@router.post("/add")
async def add_history(
    data: HistoryAddRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await history.add_news_history(db, user.id, data.news_id)
    return success_response(message="添加成功", data={"newsId": data.news_id})


# 获取浏览记录列表
@router.get("/list")
async def get_history_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows, total = await history.get_history_list(db, user.id, page, page_size)
    has_more = total > page * page_size
    data = HistoryListResponse(list=rows, total=total, hasMore=has_more)
    return success_response(message="获取成功", data=data)


# 删除浏览记录
@router.delete("/delete/{history_id}")
async def delete_history(
    history_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await history.delete_history(db, user.id, history_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="历史记录不存在"
        )
    return success_response(message="删除成功")


# 清空浏览记录
@router.delete("/clear")
async def clear_history(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await history.delete_history_list(db, user.id)
    return success_response(message=f"清空{result}条历史记录")
