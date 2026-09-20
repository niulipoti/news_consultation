from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def success_response(message: str = "success", data=None, code: int = 200):
    """统一的成功响应结构：code / message / data。

    ``by_alias=True`` 保证 Pydantic 模型按小驼峰（camelCase）输出，
    与前端约定的字段名保持一致。
    """
    content = {
        "code": code,
        "message": message,
        "data": jsonable_encoder(data, by_alias=True),
    }
    return JSONResponse(content=content)
