@echo off
chcp 65001 >nul
title 一键启动：Redis + 后端 + 前端
cd /d "%~dp0"

echo ============================================================
echo   新闻资讯 App 一键启动
echo ============================================================
echo.

REM ---------- 1. 启动 Redis ----------
echo [1/3] 启动 Redis (127.0.0.1:6379) ...
netstat -ano | findstr ":6379 " | findstr "LISTENING" >nul
if errorlevel 1 (
    start "Redis" /min cmd /c ""%~dp0tools\redis\redis-server.exe" "%~dp0tools\redis\redis-local.conf""
    timeout /t 2 /nobreak >nul
    echo       Redis 已启动 - 独立窗口已最小化
) else (
    echo       Redis 已在运行，跳过
)
echo.

REM ---------- 2. 启动后端 ----------
echo [2/3] 启动后端 (http://127.0.0.1:8000) ...
start "Backend :8000" cmd /k "cd /d "%~dp0" && .venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000"
timeout /t 4 /nobreak >nul
echo       后端窗口已打开
echo.

REM ---------- 3. 启动前端 ----------
echo [3/3] 启动前端 (http://127.0.0.1:5173) ...
start "Frontend :5173" cmd /k "cd /d "%~dp0xwzx-news" && npm run dev"
timeout /t 4 /nobreak >nul
echo       前端窗口已打开
echo.

echo ============================================================
echo   启动完成，稍等几秒后打开浏览器：
echo.
echo     前端页面 : http://127.0.0.1:5173
echo     后端页面 : http://127.0.0.1:8000
echo     接口文档 : http://127.0.0.1:8000/docs
echo     健康检查 : http://127.0.0.1:8000/health
echo.
echo   关闭：直接关掉弹出的两个 cmd 窗口即可
echo ============================================================
echo.
start "" "http://127.0.0.1:5173"
pause
