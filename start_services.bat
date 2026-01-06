@echo off
chcp 65001 >nul
echo ========================================
echo    VOD Platform - Starting Services
echo ========================================
echo.

echo [1/2] Starting Backend Server...
start "VOD-Backend" cmd /k "chcp 65001 >nul && cd /d "%~dp0backend" && python -m uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend Server...
start "VOD-Frontend" cmd /k "chcp 65001 >nul && cd /d "%~dp0frontend" && npm run dev"

echo.
echo ========================================
echo    Services Started!
echo ========================================
echo.
echo    Backend:  http://localhost:3000
echo    Frontend: http://localhost:5173
echo    API Docs: http://localhost:3000/docs
echo.
echo    Press any key to close this window...
pause >nul
