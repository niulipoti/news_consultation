from fastapi import FastAPI, HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from utils.exception import (
    general_exception_handler,
    http_exception_handler,
    integrity_error_handler,
    sqlalchemy_error_handler,
)


def register_exception_handlers(app: FastAPI, not_found_handler=None):
    """
    注册全局异常: 子类在前，父类在后；具体在前，抽象在后。

    ``not_found_handler`` 可选：用于在托管前端页面时把 404 交给 SPA 路由处理。
    """
    # Starlette 的 HTTPException 是 FastAPI HTTPException 的父类，
    # 先注册它，才能让自定义的 404 逻辑对「路由未匹配」也生效。
    app.add_exception_handler(
        StarletteHTTPException, not_found_handler or http_exception_handler
    )
    app.add_exception_handler(HTTPException, http_exception_handler)  # 业务层
    app.add_exception_handler(IntegrityError, integrity_error_handler)  # 数据完整性约束
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)  # 数据库层面
    app.add_exception_handler(Exception, general_exception_handler)  # 兜底
