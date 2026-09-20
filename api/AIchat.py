"""
AI 对话接口（DeepSeek / OpenAI 兼容协议）。

设计要点：
1. API Key 只保存在服务端 .env 中，绝不下发给前端，也不允许前端指定 Key。
2. 同时提供「一次性返回」和「SSE 流式返回」两种方式，前端默认使用流式。
3. 支持多轮对话：前端可以把历史消息一起传上来（history 字段）。
4. 统一返回 ``code / message / data`` 结构，出错时也保持同样的结构，
   前端只需要判断 code 即可。
"""

# 导入操作系统相关功能，用来读取环境变量
import os

# 导入 json，流式返回时把内容打包成 JSON，避免换行符搞乱 SSE 格式
import json

# 用于定位项目根目录下的 .env
from pathlib import Path

# 从 .env 文件加载环境变量
from dotenv import load_dotenv

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

# 导入 Pydantic 的 BaseModel，用来定义前端发来的数据格式
from pydantic import BaseModel, ConfigDict, Field, field_validator

# 导入异步 OpenAI 客户端，DeepSeek 兼容 OpenAI 接口
from openai import AsyncOpenAI

# 项目根目录：保证无论从哪个目录启动服务，都能读到根目录下的 .env
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 读取 .env 文件里的配置（DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL / DEEPSEEK_MODEL）
load_dotenv(PROJECT_ROOT / ".env")

router = APIRouter(prefix="/api/AIchat", tags=["AIchat"])

# ---------------------------------------------------------------------------
# 服务端配置
# ---------------------------------------------------------------------------

# DeepSeek 的 OpenAI 兼容地址，可通过环境变量覆盖（例如换成自建网关）
BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

# 默认使用的模型，可通过环境变量覆盖
DEFAULT_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# 系统提示词：约束 AI 的角色和回答范围
SYSTEM_PROMPT = os.getenv(
    "AI_SYSTEM_PROMPT",
    "你是一个专业、友好的新闻资讯助手，名字叫「小讯」。"
    "你擅长解读时事新闻、梳理事件背景、总结要点。"
    "回答时请使用简体中文，条理清晰，必要时使用 Markdown 列表或标题，"
    "对于无法确认的信息要明确说明，不要编造事实。",
)

# 单条消息的最大长度，防止超大请求打爆 token 额度
MAX_MESSAGE_LENGTH = int(os.getenv("AI_MAX_MESSAGE_LENGTH", "4000"))

# 最多携带多少轮历史消息
MAX_HISTORY_LENGTH = int(os.getenv("AI_MAX_HISTORY_LENGTH", "20"))


def get_api_key() -> str:
    """读取并校验 API Key，未配置时给出明确的错误提示。"""
    api_key = (os.getenv("DEEPSEEK_API_KEY") or "").strip()
    if not api_key or api_key.startswith("sk-your") or api_key == "your-api-key-here":
        raise HTTPException(
            status_code=503,
            detail="服务端未配置 DEEPSEEK_API_KEY，请在 api/.env 中填写后重启服务",
        )
    return api_key


def get_client() -> AsyncOpenAI:
    """按需创建异步 DeepSeek 客户端（每次读取最新的环境变量）。"""
    return AsyncOpenAI(api_key=get_api_key(), base_url=BASE_URL)


def friendly_error(exc: Exception) -> tuple[int, str]:
    """把底层异常翻译成「HTTP 状态码 + 用户可读的中文提示」。"""
    text = str(exc)
    lowered = text.lower()

    if "401" in text or "authentication" in lowered or "invalid_api_key" in lowered:
        return 401, "AI 服务鉴权失败，请检查 DEEPSEEK_API_KEY 是否正确"
    if "402" in text or "insufficient" in lowered or "balance" in lowered:
        return 402, "AI 账户余额不足，请前往 DeepSeek 控制台充值"
    if "429" in text or "rate limit" in lowered:
        return 429, "请求过于频繁，请稍后再试"
    if "timeout" in lowered or "timed out" in lowered:
        return 504, "AI 服务响应超时，请稍后再试"
    if "connect" in lowered or "network" in lowered or "dns" in lowered:
        return 502, "无法连接 AI 服务，请检查服务器网络"
    return 500, f"AI 服务调用失败：{text}"


# ---------------------------------------------------------------------------
# 请求 / 响应模型
# ---------------------------------------------------------------------------


class ChatMessage(BaseModel):
    """一条对话消息。"""

    role: str = Field(..., description="角色：system / user / assistant")
    content: str = Field(..., description="消息内容")

    @field_validator("role")
    @classmethod
    def check_role(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in {"system", "user", "assistant"}:
            raise ValueError("role 只能是 system、user 或 assistant")
        return value

    @field_validator("content")
    @classmethod
    def check_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("消息内容不能为空")
        if len(value) > MAX_MESSAGE_LENGTH:
            raise ValueError(f"单条消息长度不能超过 {MAX_MESSAGE_LENGTH} 个字符")
        return value


class ChatRequest(BaseModel):
    """前端发来的请求体：既支持单条 message，也支持多轮 history。"""

    message: str | None = Field(None, description="用户本次输入的问题")
    history: list[ChatMessage] | None = Field(
        None, description="可选的历史消息，用于多轮对话"
    )
    model: str | None = Field(None, description="可选，覆盖默认模型")

    model_config = ConfigDict(populate_by_name=True)

    def build_messages(self) -> list[dict]:
        """把请求体整理成 OpenAI 需要的 messages 列表。"""
        messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

        # 历史消息：过滤掉 system（避免前端覆盖系统提示词），只保留最近 N 条
        for item in (self.history or [])[-MAX_HISTORY_LENGTH:]:
            if item.role == "system":
                continue
            messages.append({"role": item.role, "content": item.content})

        # 本次问题：history 里如果已经带了同一条 user 消息就不要再重复追加
        if self.message is not None:
            text = self.message.strip()
            if not text:
                raise HTTPException(status_code=422, detail="问题内容不能为空")
            if len(text) > MAX_MESSAGE_LENGTH:
                raise HTTPException(
                    status_code=422,
                    detail=f"单条消息长度不能超过 {MAX_MESSAGE_LENGTH} 个字符",
                )
            if not (
                messages
                and messages[-1]["role"] == "user"
                and messages[-1]["content"] == text
            ):
                messages.append({"role": "user", "content": text})

        # 必须至少有一条 user 消息，否则模型不知道该回答什么
        if not any(m["role"] == "user" for m in messages):
            raise HTTPException(status_code=422, detail="请至少提供一条用户消息")

        return messages

    def resolve_model(self) -> str:
        """决定本次请求使用哪个模型；只允许服务端白名单里的模型。"""
        allow_extra = [
            m.strip()
            for m in os.getenv("DEEPSEEK_ALLOWED_MODELS", "").split(",")
            if m.strip()
        ]
        allowed = {DEFAULT_MODEL, "deepseek-chat", "deepseek-reasoner", *allow_extra}
        if self.model and self.model in allowed:
            return self.model
        return DEFAULT_MODEL


# ---------------------------------------------------------------------------
# 接口实现
# ---------------------------------------------------------------------------


@router.get("/config")
async def get_ai_config():
    """告知前端 AI 功能是否可用，以及用的是什么模型（不泄露任何密钥）。"""
    configured = bool((os.getenv("DEEPSEEK_API_KEY") or "").strip())
    return {
        "code": 200,
        "message": "获取 AI 配置成功",
        "data": {
            "enabled": configured,
            "model": DEFAULT_MODEL,
            "stream": True,
            "endpoint": "/api/AIchat/chat/stream",
        },
    }


@router.post("/chat")
async def chat(request: ChatRequest):
    """普通对话接口：一次性返回完整答案。"""
    messages = request.build_messages()
    client = get_client()
    try:
        response = await client.chat.completions.create(
            model=request.resolve_model(),
            messages=messages,
            stream=False,
        )
        reply = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        return {
            "code": 200,
            "message": "success",
            "data": {
                "reply": reply,
                "model": response.model,
                "usage": usage.model_dump() if usage is not None else None,
            },
        }
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 - 统一转换成友好提示
        status_code, detail = friendly_error(exc)
        raise HTTPException(status_code=status_code, detail=detail) from exc
    finally:
        await client.close()


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """流式对话接口：以 SSE 形式逐字返回，前端边收边显示。"""
    # 先把请求体解析好，这样参数错误可以直接返回 4xx，而不是在流里面报错
    messages = request.build_messages()
    model = request.resolve_model()

    async def event_generator():
        client = get_client()
        try:
            stream = await client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
            )
            async for chunk in stream:
                choices = getattr(chunk, "choices", None) or []
                if not choices:
                    continue
                content = choices[0].delta.content
                if content:
                    data = json.dumps({"content": content}, ensure_ascii=False)
                    yield f"data: {data}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:  # noqa: BLE001 - 流已经开始了，只能用事件体报错
            _, detail = friendly_error(exc)
            payload = json.dumps(
                {"error": detail, "code": "AI_ERROR"}, ensure_ascii=False
            )
            yield f"data: {payload}\n\n"
            yield "data: [DONE]\n\n"
        finally:
            # 关闭连接，释放底层 HTTP 连接池
            try:
                await client.close()
            except Exception:  # noqa: BLE001 - 关闭失败不影响已返回的内容
                pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # 关闭 Nginx 等反向代理的缓冲，保证逐字输出的效果
            "X-Accel-Buffering": "no",
        },
    )
