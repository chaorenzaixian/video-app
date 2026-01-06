@echo off
chcp 65001 >nul
title Video App Starter

echo ========================================
echo   视频APP 服务启动器
echo ========================================
echo.

:: 获取当前脚本所在目录
set "ROOT_DIR=%~dp0"
echo 项目目录: %ROOT_DIR%
echo.

:: 启动后端
echo [1/2] 启动后端服务...
start "Backend Server" cmd /k "cd /d "%ROOT_DIR%backend" && call venv\Scripts\activate.bat && python run.py"

:: 等待3秒
timeout /t 3 /nobreak >nul

:: 启动前端
echo [2/2] 启动前端服务...
start "Frontend Server" cmd /k "cd /d "%ROOT_DIR%frontend" && npm run dev"

echo.
echo ========================================
echo   服务已启动！
echo ========================================
echo   后端: http://localhost:8001
echo   后端API文档: http://localhost:8001/api/docs
echo   前端: http://localhost:3000 或 http://localhost:5173
echo ========================================
echo.
echo 按任意键退出此窗口（服务将继续运行）...
pause >nul

