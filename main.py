"""FastAPI 应用入口。

启动方式（开发）：
    uvicorn main:app --reload --port 8000
启动方式（生产）：
    uvicorn main:app --host 0.0.0.0 --port 8000

如果前端已经执行过 ``npm run build`` 并把产物放到项目根目录的 ``static/``，
本服务会顺带把前端页面一起托管，实现「一个端口同时提供接口和页面」。
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from api import AIchat
from routers import favorite, history, news, users

from utils.cache import close_redis
from utils.exception_handlers import register_exception_handlers

# 先加载环境变量，后面的配置读取才有值
load_dotenv(Path(__file__).resolve().parent / ".env")

# 前端构建产物目录（可选）
STATIC_DIR = Path(__file__).resolve().parent / "static"

# 允许跨域的来源：
#   默认放开常见的本地开发端口；生产环境通过 CORS_ORIGINS 环境变量指定
DEFAULT_ORIGINS = (
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:8080,http://localhost:3000,http://localhost,"
    "http://127.0.0.1:8000"
)
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", DEFAULT_ORIGINS).split(",")
    if origin.strip()
]

# 这些前缀属于「接口/文档」，404 时要返回 JSON 而不是前端页面
API_PREFIXES = ("api", "docs", "redoc", "openapi.json", "health")


def build_spa_error_handler(static_dir: Path):
    """生成「接口返回 JSON、页面走 SPA 回退」的异常处理器。"""

    async def handler(request: Request, exc: StarletteHTTPException):
        path = request.url.path.lstrip("/")
        is_api = path.split("/")[0] in API_PREFIXES

        # 前端路由地址（如 /news/detail/1）直接返回 index.html
        if exc.status_code == 404 and not is_api:
            index_file = static_dir / "index.html"
            if index_file.exists():
                return FileResponse(index_file)

        from utils.exception import http_exception_handler

        return await http_exception_handler(request, exc)

    return handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动 / 关闭时的资源管理工作。"""
    # 启动
    yield
    # 关闭：释放 Redis 连接和数据库连接池
    from config.db_conf import async_engine

    await close_redis()
    await async_engine.dispose()


app = FastAPI(
    title="新闻资讯 API",
    description="基于 FastAPI + SQLAlchemy + Redis 的新闻资讯后端，内置 AI 问答接口。",
    version="1.1.0",
    lifespan=lifespan,
)

# 注册异常处理器（如果启用了前端静态托管，404 会额外做 SPA 回退）
register_exception_handlers(
    app,
    not_found_handler=build_spa_error_handler(STATIC_DIR) if STATIC_DIR.exists() else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    # 匹配任意本地端口（vite dev server 换端口时不用改配置）
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,  # 允许携带cookie
    allow_methods=["*"],  # 允许的请求方法
    allow_headers=["*"],  # 允许的请求头
)


@app.get("/health", tags=["system"])
async def health():
    """健康检查：部署到服务器后可以用它确认服务是否存活。"""
    return {
        "code": 200,
        "message": "ok",
        "data": {
            "service": "toutiao-backend",
            "version": app.version,
            # 只暴露「有没有配置」，绝不返回密钥本身
            "ai_configured": bool((os.getenv("DEEPSEEK_API_KEY") or "").strip()),
        },
    }


# 挂载路由 注册
app.include_router(news.router)
app.include_router(users.router)
app.include_router(favorite.router)
app.include_router(history.router)
app.include_router(AIchat.router)


@app.get("/", tags=["system"])
async def root():
    # 如果前端已经构建，就直接返回页面，否则返回接口提示
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "message": "Hello world",
        "docs": "/docs",
        "health": "/health",
    }


# ---------------------------------------------------------------------------
# 静态资源托管（可选，必须放在所有 API 路由之后注册）
# 前端 `npm run build` 之后把 dist 里的文件复制到项目根目录的 static/ 即可。
# ---------------------------------------------------------------------------
if STATIC_DIR.exists():
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
