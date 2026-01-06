@echo off
chcp 65001 >nul
title Backend Server

echo ========================================
echo   启动后端服务
echo ========================================

:: 进入当前脚本所在目录
cd /d "%~dp0"

echo 当前目录: %CD%
echo.

:: 激活虚拟环境并运行
call venv\Scripts\activate.bat
python run.py

pause


