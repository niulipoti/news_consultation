"""Redis 缓存工具。

设计目标：**缓存不可用不能拖垮业务**。
1. Redis 宕机 / 没装时所有函数安静降级（读返回 None、写返回 False），上层自动回源数据库。
2. 连续失败达到阈值后自动「熔断」一段时间，期间直接跳过缓存，
   避免每个请求都白等一次连接超时（否则接口会莫名其妙变慢好几秒）。
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
import redis.asyncio as redis

# 项目根目录：保证无论从哪个目录启动服务，都能读到根目录下的 .env
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") or None

# 开关：本地没装 Redis 时可以设 REDIS_ENABLED=false 直接跳过缓存
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "true").lower() in {"1", "true", "yes", "on"}

# 连续失败多少次后熔断 / 熔断持续多少秒
FAILURE_THRESHOLD = int(os.getenv("REDIS_FAILURE_THRESHOLD", "2"))
COOLDOWN_SECONDS = int(os.getenv("REDIS_COOLDOWN_SECONDS", "60"))

# 创建 Redis 连接对象
redis_client = redis.Redis(
    host=REDIS_HOST,  # redis 主机地址
    port=REDIS_PORT,  # redis 端口号
    db=REDIS_DB,  # redis 数据库编号，0~15 一共16个
    password=REDIS_PASSWORD,
    decode_responses=True,  # 将字节解码为字符串
    # 必须显式指定 RESP2：
    # redis-py 8.x 默认用 RESP3 协议，连接时会先发 `HELLO 3`，
    # 而 Redis 5.0（目前 Windows 上最稳定的移植版）不支持 HELLO 命令，
    # 不指定就会报 "unknown command `HELLO`"，缓存会全部失效。
    protocol=2,
    socket_connect_timeout=1,  # 连接超时，避免 Redis 挂掉时接口被拖慢
    socket_timeout=1,
)

# 熔断状态
_failure_count = 0
_open_until = 0.0


def _circuit_open() -> bool:
    """熔断期内直接返回 True，跳过一切缓存操作。"""
    return time.monotonic() < _open_until


def _record_success() -> None:
    global _failure_count, _open_until
    _failure_count = 0
    _open_until = 0.0


def _record_failure() -> None:
    global _failure_count, _open_until
    _failure_count += 1
    if _failure_count >= FAILURE_THRESHOLD:
        _open_until = time.monotonic() + COOLDOWN_SECONDS
        print(
            f"[cache] Redis 连续失败 {_failure_count} 次，"
            f"暂停使用缓存 {COOLDOWN_SECONDS} 秒（业务自动回源数据库）"
        )
        _failure_count = 0


def _skip() -> bool:
    """是否需要跳过缓存。"""
    return not REDIS_ENABLED or _circuit_open()


async def _run(operation, key: str, *args):
    """执行一次缓存操作，统一处理失败与熔断。"""
    try:
        result = await operation(key, *args)
        _record_success()
        return result
    except Exception as e:  # noqa: BLE001 - 缓存异常不影响主流程
        _record_failure()
        print(f"缓存操作失败（key={key}）：{type(e).__name__}: {e}")
        return None


# 读取：字符串(从 redis 缓存中读取数据)
async def get_cache(key: str) -> Optional[str]:
    if _skip():
        return None
    return await _run(redis_client.get, key)


# 读取：列表或字典
async def get_json_cache(key: str) -> Optional[Any]:
    if _skip():
        return None

    data = await _run(redis_client.get, key)
    if not data:
        return None
    try:
        return json.loads(data)  # 反序列化
    except (TypeError, json.JSONDecodeError) as e:
        # 脏数据：当作缓存未命中处理
        print(f"缓存内容不是合法 JSON（key={key}）：{e}")
        return None


# 设置缓存 setex(key, expire, value)
async def set_cache(key: str, value: Any, expire: int = 3600) -> bool:
    if _skip():
        return False

    if isinstance(value, (dict, list)):  # 判断是否为字典或列表
        try:
            value = json.dumps(value, ensure_ascii=False)  # 避免中文乱码
        except (TypeError, ValueError) as e:
            print(f"缓存内容无法序列化（key={key}）：{e}")
            return False

    result = await _run(redis_client.setex, key, expire, value)
    return bool(result)


async def delete_cache(*keys: str) -> int:
    """删除缓存（新闻更新后用来清理脏数据）。"""
    if not keys or _skip():
        return 0
    result = await _run(redis_client.delete, *keys)
    return int(result or 0)


async def close_redis() -> None:
    """应用关闭时释放 Redis 连接。"""
    try:
        # redis-py 5.0+ 用 aclose()，老版本只有 close()
        aclose = getattr(redis_client, "aclose", None) or redis_client.close
        await aclose()
    except Exception:  # noqa: BLE001
        pass
