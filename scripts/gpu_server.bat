@echo off
chcp 65001 >nul
setlocal

set GPU_KEY=C:\Users\garry\Downloads\temporary (1).pem
set GPU_HOST=ubuntu@149.36.0.246

:menu
cls
echo ╔════════════════════════════════════════╗
echo ║     GPU 服务器管理工具 (149.36.0.246)   ║
echo ╠════════════════════════════════════════╣
echo ║  1. 启动 VNC 远程桌面                   ║
echo ║  2. 查看 GPU 状态                       ║
echo ║  3. 查看转码服务状态                    ║
echo ║  4. 启动转码监控服务                    ║
echo ║  5. 停止转码监控服务                    ║
echo ║  6. 查看转码日志                        ║
echo ║  7. SSH 连接到服务器                    ║
echo ║  0. 退出                                ║
echo ╚════════════════════════════════════════╝
echo.

set /p choice=请选择操作 [0-7]: 

if "%choice%"=="1" goto vnc
if "%choice%"=="2" goto gpu_status
if "%choice%"=="3" goto transcode_status
if "%choice%"=="4" goto start_watch
if "%choice%"=="5" goto stop_watch
if "%choice%"=="6" goto logs
if "%choice%"=="7" goto ssh
if "%choice%"=="0" goto end

echo 无效选择，请重试
timeout /t 2 >nul
goto menu

:vnc
echo.
echo [启动 VNC 服务...]
ssh -i "%GPU_KEY%" %GPU_HOST% "vncserver -list | grep -q ':1' || vncserver :1 -geometry 1920x1080 -depth 24 2>/dev/null"
ssh -i "%GPU_KEY%" %GPU_HOST% "pkill -f 'websockify.*6080' 2>/dev/null; sleep 1; nohup websockify --web=/usr/share/novnc 6080 localhost:5901 > /tmp/novnc.log 2>&1 &"
echo.
echo VNC 已启动: http://149.36.0.246:6080/vnc.html
start http://149.36.0.246:6080/vnc.html
pause
goto menu

:gpu_status
echo.
echo [GPU 状态]
ssh -i "%GPU_KEY%" %GPU_HOST% "nvidia-smi"
echo.
pause
goto menu

:transcode_status
echo.
echo [转码服务状态]
ssh -i "%GPU_KEY%" %GPU_HOST% "cd ~/video-transcode && ./watch_service.sh status"
echo.
pause
goto menu

:start_watch
echo.
echo [启动转码监控服务...]
ssh -i "%GPU_KEY%" %GPU_HOST% "cd ~/video-transcode && ./watch_service.sh start"
echo.
pause
goto menu

:stop_watch
echo.
echo [停止转码监控服务...]
ssh -i "%GPU_KEY%" %GPU_HOST% "cd ~/video-transcode && ./watch_service.sh stop"
echo.
pause
goto menu

:logs
echo.
echo [最近转码日志 - 按 Ctrl+C 退出]
ssh -i "%GPU_KEY%" %GPU_HOST% "tail -50 ~/video-transcode/logs/transcode_*.log 2>/dev/null || echo '暂无日志'"
echo.
pause
goto menu

:ssh
echo.
echo [连接到 GPU 服务器 - 输入 exit 退出]
ssh -i "%GPU_KEY%" %GPU_HOST%
goto menu

:end
echo 再见！
exit /b 0
