# 新闻资讯 App（FastAPI + Vue3 + DeepSeek AI）

一个前后端分离的移动端新闻资讯应用：后端使用 **FastAPI + SQLAlchemy(异步) + MySQL + Redis**，
前端使用 **Vue 3 + Vite + Vant 4 + Pinia**，并内置了基于 **DeepSeek** 的 AI 问答（流式输出）。

> 前端界面布局与风格保持不变，本次改造重点是**修复缺陷**和**打通 AI 对话链路**。

---

## 功能一览

| 模块 | 说明 |
| --- | --- |
| 用户 | 注册、登录、退出登录、查看/修改资料、修改密码（bcrypt 加密 + Token 鉴权） |
| 新闻 | 分类列表、分类下的新闻分页列表、新闻详情、浏览量自增、相关推荐 |
| 收藏 | 收藏、取消收藏、收藏状态查询、收藏列表分页、清空收藏 |
| 历史 | 自动记录浏览历史、历史列表分页、删除单条、清空 |
| **AI 问答** | **多轮对话、SSE 流式输出、Markdown 渲染、可随时中断、错误友好提示** |
| 其他 | 主题切换、中英双语、Redis 缓存（含熔断降级） |

---

## 目录结构

```
toutiao_backend/
├── main.py                  # FastAPI 入口（路由挂载、CORS、静态托管）
├── requirements.txt         # 后端依赖
├── .env.example             # 环境变量模板（复制为 .env 使用）
│
├── api/
│   └── AIchat.py            # AI 对话接口（流式 + 非流式）
├── config/
│   └── db_conf.py           # 数据库连接（从环境变量读取）
├── models/                  # SQLAlchemy ORM 模型
├── schemas/                 # Pydantic 请求/响应模型
├── crud/                    # 数据库操作
├── cache/                   # Redis 缓存 key 管理
├── routers/                 # 各模块路由
├── utils/                   # 鉴权、缓存、序列化、异常处理等工具
├── scripts/                 # 测试脚本
└── xwzx-news/               # 前端工程（Vue 3 + Vite）
    └── src/
        ├── config/          # api.js / http.js（统一 axios 实例）
        ├── views/           # 页面（含 AIChat.vue）
        ├── store/           # Pinia 状态管理
        └── i18n/            # 中英文语言包
```

---

## 快速开始

### 0. 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- Redis 6.0+（**可选**，未安装时把 `REDIS_ENABLED` 设为 `false` 即可；Windows 版见下方 0.1）

#### 0.1 Windows 安装 Redis（可选）

Windows 官方早已停止维护 Redis，社区最常用的移植版是
[tporadowski/redis](https://github.com/tporadowski/redis/releases)（v5.0.14.1，稳定可用）。

本仓库已内置一份解压好的 Redis 与专用配置，**无需再手动下载**：

```powershell
# 双击运行，或在终端执行
.\start-redis.bat
```

脚本会用 `tools\redis\redis-local.conf` 启动服务并监听 `127.0.0.1:6379`。
关闭窗口即可停止。

> ⚠️ **协议兼容提示**：Redis 5.0 不支持 RESP3，
> 而 `redis-py` 8.x 默认会先发 `HELLO 3` 握手，直接连会报
> `unknown command 'HELLO'` 导致缓存全部失效。
> 本项目已在 `utils/cache.py` 中显式指定 `protocol=2` 解决，请勿删除该参数。

若想从零手动安装，也可以下载 `Redis-x64-5.0.14.1.zip` 解压后执行：

```powershell
.\redis-server.exe redis-local.conf
```

### 1. 准备数据库

```sql
CREATE DATABASE news_app DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

准备好 `news_category`、`news`、`user`、`user_token`、`favorite`、`history` 这几张表
（表结构见 `models/` 目录下的 ORM 定义）。

### 2. 配置环境变量

```bash
cp .env.example .env      # Windows: copy .env.example .env
```

然后编辑 `.env`，**必须**填写：

```ini
DEEPSEEK_API_KEY=sk-你的密钥        # https://platform.deepseek.com/api_keys
DATABASE_URL=mysql+aiomysql://root:你的密码@localhost:3306/news_app?charset=utf8mb4
```

> `.env` 已在 `.gitignore` 中，不会被提交到 GitHub。

### 3. 启动后端

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

- 接口文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/health

> 若使用虚拟环境（本仓库自带 `.venv`），用
> `.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000` 更稳妥，
> 可以绕过 PowerShell 的脚本执行策略限制。

### 4. 启动前端

```bash
cd xwzx-news
npm install
npm run dev
```

打开 http://127.0.0.1:5173

> 前端通过 Vite 代理把 `/api` 请求转发到 `http://127.0.0.1:8000`，
> 因此**不存在跨域问题**，代码里也不需要写死后端地址。
> 如需修改后端地址，在 `xwzx-news/.env.local` 中设置 `VITE_PROXY_TARGET`。

#### 4.1 一键启动（Windows）

不想开三个窗口的话，直接双击项目根目录的：

```
start-all.bat
```

它会依次检查并启动 **Redis → 后端 → 前端**，最后自动打开浏览器。
关闭弹出的命令行窗口即可停止对应服务。

### 5. 生产部署（单端口）

```bash
cd xwzx-news && npm run build
# 把 dist 里的文件复制到项目根目录的 static/
cd .. && xcopy /E /I xwzx-news\dist static      # Windows
# cp -r xwzx-news/dist static                    # Linux / macOS

uvicorn main:app --host 0.0.0.0 --port 8000
```

此时 `http://服务器:8000` 会同时提供前端页面和 API，
刷新 `/news/detail/1` 这类前端路由也不会 404（已做 SPA 回退）。

---

## 接口一览

完整文档见启动后的 `/docs`，以下为摘要。

### 用户 `/api/user`

| 方法 | 路径 | 说明 | 鉴权 |
| --- | --- | --- | --- |
| POST | `/register` | 注册 | 否 |
| POST | `/login` | 登录 | 否 |
| GET | `/info` | 获取当前用户信息 | 是 |
| PUT | `/update` | 修改资料 | 是 |
| PUT | `/password` | 修改密码 | 是 |
| POST | `/logout` | 退出登录 | 是 |

### 新闻 `/api/news`

| 方法 | 路径 | 参数 | 说明 |
| --- | --- | --- | --- |
| GET | `/categories` | `skip`,`limit` | 分类列表 |
| GET | `/list` | `categoryId`,`page`,`pageSize` | 新闻分页列表 |
| GET | `/detail` | `id` | 新闻详情（含浏览量 +1、相关推荐） |

### 收藏 `/api/favorite`（全部需要鉴权）

| 方法 | 路径 | 参数 |
| --- | --- | --- |
| GET | `/check` | `newsId` |
| POST | `/add` | body `{ "newsId": 1 }` |
| DELETE | `/remove` | `newsId` |
| GET | `/list` | `page`,`pageSize` |
| DELETE | `/clear` | - |

### 历史 `/api/history`（全部需要鉴权）

| 方法 | 路径 | 参数 |
| --- | --- | --- |
| POST | `/add` | body `{ "newsId": 1 }` |
| GET | `/list` | `page`,`pageSize` |
| DELETE | `/delete/{historyId}` | - |
| DELETE | `/clear` | - |

### AI 对话 `/api/AIchat`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/config` | 查询 AI 是否可用（不返回密钥） |
| POST | `/chat` | 一次性返回完整回答 |
| POST | `/chat/stream` | **SSE 流式返回**（前端默认使用） |

**请求体**（既支持单条消息，也支持多轮对话）：

```json
{
  "message": "今天有什么值得关注的新闻？",
  "history": [
    { "role": "user", "content": "你好" },
    { "role": "assistant", "content": "你好，我是小讯。" }
  ]
}
```

**流式响应**（`text/event-stream`）：

```
data: {"content":"我"}
data: {"content":"是"}
data: {"content":"小讯"}
data: [DONE]
```

出错时会在流中间推送：`data: {"error":"AI 服务鉴权失败，请检查 DEEPSEEK_API_KEY 是否正确","code":"AI_ERROR"}`

---

## 安全说明

- **密钥只保存在服务端**。前端不再持有任何大模型 API Key，所有 AI 请求都经由自己的后端转发。
- `.env` 已加入 `.gitignore`，`api/.env` 只保留占位符。
- 如果你曾经把真实密钥提交到过公开仓库，请立刻到服务商控制台**吊销并重新生成**。
- 生产环境建议把 `utils/exception.py` 里的 `DEBUG_MODE` 改为 `False`，避免异常堆栈外泄。
- 生产环境请通过 `CORS_ORIGINS` 环境变量限定允许的来源域名。

---

## 测试

```bash
# 离线冒烟测试（含一次真实的 DeepSeek 流式调用）
python scripts/smoke_test.py

# HTTP 端到端测试（会临时启动 uvicorn 并请求真实接口）
python scripts/http_e2e_test.py

# 上传 GitHub 前的安全自检（检查密钥、敏感路径、大文件）
python scripts/security_check.py
```

三个脚本都是自包含的，失败的项目会在控制台以 `[FAIL]` 标出。

### 上传 GitHub 前的检查清单

```bash
python scripts/security_check.py    # 退出码为 0 才继续
git status                          # 确认清单里没有 .env / .venv / node_modules
```

脚本会自动验证：

- `.env`、`api/.env`、`.venv/`、`tools/`、`static/`、`node_modules/` 均被忽略
- 即将提交的内容里没有真实密钥（OpenAI / AWS / GitHub / Google / Slack 等格式）
- 代码文件中没有硬编码的数据库凭据
- 单个文件不超过 5 MB
- `.env.example` 里只有占位符

> ⚠️ 有一点脚本无法替你判断：**如果你曾经把真实密钥以明文形式提交过**
> （哪怕之后又删除），Git 历史仍会永久保留旧内容。
> 这种情况**必须到服务商控制台吊销并重新生成密钥**，这是唯一彻底的补救方式。

---

## 常见问题

**Q：AI 回复提示「服务端未配置 DEEPSEEK_API_KEY」？**
根目录 `.env` 里没填密钥，或填写后没有重启后端服务。

**Q：Redis 没装会不会影响使用？**
不会。缓存读写失败会自动回源数据库，连续失败还会自动熔断 60 秒，
接口不会因此变慢或报错。也可以直接在 `.env` 里设 `REDIS_ENABLED=false`。

**Q：前端登录后刷新页面就掉登录状态？**
已修复。现在使用 `pinia-plugin-persistedstate` v4 的正确写法持久化 token，
并且单个 `localStorage` 存储失败也不会影响整个应用的启动。

**Q：新闻列表里的时间/字段都是空的？**
已修复。后端统一以 **camelCase**（`publishTime`、`categoryId`、`hasMore` 等）
返回，缓存命中与数据库查询两条路径产出的结构完全一致。

---

## License

仅用于学习与技术交流。
