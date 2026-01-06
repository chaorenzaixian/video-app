@echo off
chcp 65001 >nul
cd /d "%~dp0frontend"
echo ========================================
echo    Starting Frontend Server...
echo ========================================
npm run dev
pause

