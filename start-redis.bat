@echo off
chcp 65001 >nul
title Redis Server (6379)
cd /d "%~dp0"

echo ============================================================
echo   Redis 5.0.14.1 for Windows
echo   监听地址: 127.0.0.1:6379
echo   配置文件: tools\redis\redis-local.conf
echo ============================================================
echo.
echo 关闭本窗口或按 Ctrl+C 即可停止 Redis。
echo.

"%~dp0tools\redis\redis-server.exe" "%~dp0tools\redis\redis-local.conf"

echo.
echo Redis 已停止。
pause
