"""数据库连接配置。

数据库地址通过环境变量 ``DATABASE_URL`` 注入，避免把账号密码写死在代码里
（写死的密码一旦推到 GitHub 就等于公开泄露）。
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# 项目根目录：保证无论从哪个目录启动服务，都能读到根目录下的 .env
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 统一在配置层加载 .env，保证任何入口导入本模块时环境变量都已就绪
load_dotenv(PROJECT_ROOT / ".env")

# 数据库URL
# 故意不提供带真实密码的默认值：配置缺失时直接报错，
# 好过静默连到一个「碰巧能用」的弱密码库上（那种默认值也会被提交进仓库）。
# "$" 开头的标记用于识别未展开的 shell 变量（如 docker-compose 里忘配 ${DATABASE_URL}）
_PLACEHOLDER_MARKERS = (
    "CHANGE_ME",
    "your-password",
    "your_password",
    "yourpassword",
    "${",
    "$(",
)

ASYNC_DATABASE_URL = (os.getenv("DATABASE_URL") or "").strip()

if not ASYNC_DATABASE_URL or any(m in ASYNC_DATABASE_URL for m in _PLACEHOLDER_MARKERS):
    raise RuntimeError(
        "未配置 DATABASE_URL。\n"
        "请复制 .env.example 为 .env，并把 DATABASE_URL 改成你自己的数据库连接串，例如：\n"
        "  DATABASE_URL=mysql+aiomysql://用户名:密码@localhost:3306/news_app?charset=utf8mb4"
    )

# echo=True 会把每条 SQL 都打印出来，只在调试时打开
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() in {"1", "true", "yes", "on"}

# 创建异步引擎
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=SQL_ECHO,
    pool_size=10,
    max_overflow=20,
    # 连接前先 ping 一下，避免 MySQL 断开空闲连接后取到失效连接
    pool_pre_ping=True,
    pool_recycle=3600,
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# 依赖项，用于获取数据库会话
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
