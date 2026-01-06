@echo off
chcp 65001 >nul
cd /d "%~dp0backend"
echo ========================================
echo    Starting Backend Server...
echo ========================================
python -m uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
pause

