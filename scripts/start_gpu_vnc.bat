@echo off
chcp 65001 >nul
echo ========================================
echo   GPU 服务器 VNC 远程桌面启动脚本
echo ========================================
echo.

set GPU_KEY=C:\Users\garry\Downloads\temporary (1).pem
set GPU_HOST=ubuntu@149.36.0.246

echo [1/3] 启动 VNC 服务器...
ssh -i "%GPU_KEY%" %GPU_HOST% "vncserver -list | grep -q ':1' || vncserver :1 -geometry 1920x1080 -depth 24"

echo [2/3] 启动 noVNC Web 服务...
ssh -i "%GPU_KEY%" %GPU_HOST% "pkill -f 'websockify.*6080' 2>/dev/null; sleep 1; nohup websockify --web=/usr/share/novnc 6080 localhost:5901 > /tmp/novnc.log 2>&1 &"

echo [3/3] 等待服务启动...
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   VNC 服务已启动！
echo   访问地址: http://149.36.0.246:6080/vnc.html
echo ========================================
echo.

choice /C YN /M "是否立即打开浏览器"
if %ERRORLEVEL%==1 start http://149.36.0.246:6080/vnc.html

pause
