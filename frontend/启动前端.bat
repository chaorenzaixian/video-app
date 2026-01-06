@echo off
chcp 65001 >nul
title Frontend Server

echo ========================================
echo   启动前端服务
echo ========================================

:: 进入当前脚本所在目录
cd /d "%~dp0"

echo 当前目录: %CD%
echo.

:: 检查 node_modules 是否存在
if not exist "node_modules" (
    echo [!] node_modules 不存在，正在安装依赖...
    npm install
    echo.
)

echo [*] 启动开发服务器...
npm run dev

pause


