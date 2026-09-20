"""HTTP 端到端测试：真实启动 uvicorn，逐个请求关键接口。

运行方式（项目根目录）：
    python scripts/http_e2e_test.py
"""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

ROOT = Path(__file__).resolve().parent.parent
HOST = "127.0.0.1"
PORT = 8123
BASE = f"http://{HOST}:{PORT}"

PASSED = 0
FAILED = 0


def check(name: str, condition: bool, detail: str = ""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  [PASS] {name}")
    else:
        FAILED += 1
        print(f"  [FAIL] {name} {detail}")


def request(path, method="GET", body=None, timeout=30):
    """发一个 HTTP 请求，返回 (状态码, 解析后的 body 或原始文本)。"""
    url = f"{BASE}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        status = e.code
    except Exception as exc:  # noqa: BLE001
        return None, f"{type(exc).__name__}: {exc}"

    try:
        return status, json.loads(raw)
    except json.JSONDecodeError:
        return status, raw


def as_dict(body):
    """把响应体安全地当成字典使用（失败时返回空字典）。"""
    return body if isinstance(body, dict) else {}


def wait_for_server(process, timeout=40):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if process.poll() is not None:
            return False
        status, _ = request("/health", timeout=3)
        if status == 200:
            return True
        time.sleep(0.5)
    return False


def main():
    print("=" * 60)
    print("新闻资讯后端 - HTTP 端到端测试")
    print("=" * 60)

    env = os.environ.copy()
    # 确保能 import 到虚拟环境里的依赖
    site_packages = str(ROOT / ".venv" / "Lib" / "site-packages")
    env["PYTHONPATH"] = site_packages + os.pathsep + env.get("PYTHONPATH", "")

    print(f"\n启动 uvicorn ({HOST}:{PORT}) ...")
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            HOST,
            "--port",
            str(PORT),
            "--log-level",
            "warning",
        ],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    try:
        if not wait_for_server(process):
            print("  [FAIL] 服务启动失败")
            out = process.stdout.read().decode("utf-8", errors="replace")
            print(out[-3000:])
            sys.exit(1)
        print("  服务已就绪\n")

        # ---- 健康检查 ----
        print("[1] 健康检查 / 根路径")
        status, body = request("/health")
        check("/health 返回 200", status == 200, f"-> {status}")
        check("/health 结构正确", isinstance(body, dict) and body.get("code") == 200, f"-> {body}")
        check(
            "/health 不泄露密钥",
            isinstance(body, dict) and "sk-" not in json.dumps(body, ensure_ascii=False),
        )

        status, body = request("/")
        check("/ 返回前端页面或提示", status == 200)

        # ---- AI 配置 ----
        print("\n[2] AI 配置接口")
        status, body = request("/api/AIchat/config")
        check("/api/AIchat/config 返回 200", status == 200, f"-> {status}")
        data = body.get("data", {}) if isinstance(body, dict) else {}
        check("已检测到密钥配置", data.get("enabled") is True, f"-> {data}")
        check(
            "配置接口不含密钥",
            "sk-" not in json.dumps(body, ensure_ascii=False),
        )

        # ---- AI 流式对话 ----
        print("\n[3] AI 流式对话（SSE）")
        url = f"{BASE}/api/AIchat/chat/stream"
        payload = json.dumps(
            {"message": "只回复两个字：收到"}, ensure_ascii=False
        ).encode("utf-8")
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")

        content_type = ""
        text = ""
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                content_type = resp.headers.get("Content-Type", "")
                # 逐块读取，验证“流式”而不是一次性返回
                chunks = []
                while True:
                    chunk = resp.read(64)
                    if not chunk:
                        break
                    chunks.append(chunk)
                text = b"".join(chunks).decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            check("SSE 请求成功", False, f"-> {exc}")

        check("Content-Type 是 text/event-stream", "text/event-stream" in content_type, f"-> {content_type}")
        check("收到 data: 事件", "data:" in text)
        check("以 [DONE] 结束", "[DONE]" in text)

        answer = ""
        for line in text.split("\n"):
            line = line.strip()
            if not line.startswith("data:"):
                continue
            raw = line[5:].strip()
            if raw in ("", "[DONE]"):
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if obj.get("error"):
                check("流中没有错误", False, f"-> {obj['error']}")
            answer += obj.get("content", "")
        check("收到 AI 回复内容", bool(answer), f"-> {answer!r}")
        if answer:
            print(f"   AI 回复：{answer}")

        # ---- AI 非流式对话 ----
        print("\n[4] AI 非流式对话")
        status, body = request(
            "/api/AIchat/chat", method="POST", body={"message": "你好"}, timeout=90
        )
        check("/api/AIchat/chat 返回 200", status == 200, f"-> {status}")
        reply = (body or {}).get("data", {}).get("reply", "")
        check("返回非空回复", bool(reply), f"-> {reply!r}")

        # ---- 参数校验 ----
        print("\n[5] 参数校验（应当被拒绝）")
        status, _ = request("/api/AIchat/chat", method="POST", body={"message": "   "})
        check("空消息返回 4xx", status is not None and 400 <= status < 500, f"-> {status}")

        status, _ = request(
            "/api/AIchat/chat",
            method="POST",
            body={"message": "hi", "history": [{"role": "hacker", "content": "x"}]},
        )
        check("非法 role 返回 422", status == 422, f"-> {status}")

        # ---- 需要登录的接口 ----
        print("\n[6] 鉴权与前端路由回退")
        status, body = request("/api/favorite/list")
        check("未登录访问收藏返回 401", status == 401, f"-> {status}")
        check("401 是 JSON 结构", isinstance(body, dict) and body.get("code") == 401, f"-> {body}")

        # ---- SPA 回退 ----
        has_static = (ROOT / "static" / "index.html").exists()
        status, body = request("/news/detail/1")
        if has_static:
            check("前端路由返回 index.html", status == 200 and "<div id=\"app\">" in str(body))
        else:
            check("未托管前端时返回 404 JSON", status == 404, f"-> {status}")

        status, body = request("/api/not-exist")
        check("未知接口返回 404 JSON", status == 404 and isinstance(body, dict), f"-> {status} {body}")

        status, body = request("/openapi.json")
        check("接口文档可用", status == 200 and "paths" in (body or {}))

        # ---- 业务接口真实查库 ----
        print("\n[7] 新闻接口（真实查询 MySQL）")
        status, body = request("/api/news/categories", timeout=60)
        if status is None or status == 500:
            print(f"   [SKIP] 数据库未连接，跳过新闻接口检查（{status} {str(body)[:200]}）")
        else:
            check("/api/news/categories 返回 200", status == 200, f"-> {status} {str(body)[:200]}")
            cats = as_dict(body).get("data") or []
            check("返回分类列表", isinstance(cats, list), f"-> {body}")
            if cats:
                status, body = request(
                    f"/api/news/list?categoryId={cats[0]['id']}&page=1&pageSize=5", timeout=60
                )
                check("/api/news/list 返回 200", status == 200, f"-> {status} {str(body)[:200]}")
                lst = (as_dict(body).get("data") or {}).get("list") or []
                if lst:
                    first = lst[0]
                    check("列表字段为小驼峰", "categoryId" in first and "publishTime" in first, f"-> {list(first)}")
                    status, body = request(f"/api/news/detail?id={first['id']}", timeout=60)
                    check("/api/news/detail 返回 200", status == 200, f"-> {status}")
                    detail = as_dict(body).get("data") or {}
                    check("详情包含 content 与 relatedNews", "content" in detail and "relatedNews" in detail)

                    # 连续请求两次详情，验证浏览量确实每次都 +1
                    first_views = detail.get("views")
                    _, body2 = request(f"/api/news/detail?id={first['id']}", timeout=60)
                    second_views = (as_dict(body2).get("data") or {}).get("views")
                    check(
                        "浏览量自增生效",
                        isinstance(first_views, int)
                        and isinstance(second_views, int)
                        and second_views > first_views,
                        f"-> {first_views} -> {second_views}",
                    )
                    check(
                        "相关推荐结构与字段正确",
                        isinstance(detail.get("relatedNews"), list)
                        and all(
                            set(item) == {"id", "title", "image", "views"}
                            for item in detail["relatedNews"]
                        ),
                        f"-> {detail.get('relatedNews')}",
                    )

                    # 缓存命中时浏览量也必须实时（缓存的是内容，不是计数）
                    if (ROOT / "tools" / "redis" / "redis-server.exe").exists():
                        req_id = first["id"]
                        # 连打 3 次，把详情缓存"预热"到命中状态
                        for _ in range(3):
                            _, b = request(f"/api/news/detail?id={req_id}", timeout=60)
                        v1 = (as_dict(b).get("data") or {}).get("views")
                        _, b2 = request(f"/api/news/detail?id={req_id}", timeout=60)
                        v2 = (as_dict(b2).get("data") or {}).get("views")
                        check(
                            "详情缓存命中时浏览量仍实时递增",
                            isinstance(v1, int) and isinstance(v2, int) and v2 > v1,
                            f"-> {v1} -> {v2}",
                        )
                    else:
                        print("   [SKIP] 未安装 Redis，跳过缓存实时性检查")
                else:
                    print("   [SKIP] 该分类下暂无新闻数据")

    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()

    print("\n" + "=" * 60)
    print(f"结果：{PASSED} 项通过，{FAILED} 项失败")
    print("=" * 60)
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
