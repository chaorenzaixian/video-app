@echo off
chcp 65001 >nul
title Soul视频 - 打包部署工具

echo ========================================
echo       Soul视频 打包部署工具
echo ========================================
echo.

set PROJECT_PATH=%~dp0
set DEPLOY_DIR=%PROJECT_PATH%deploy_package
set BACKEND_DIR=%PROJECT_PATH%backend
set FRONTEND_DIR=%PROJECT_PATH%frontend

echo 请选择操作:
echo 1. 打包后端 (backend.zip)
echo 2. 打包前端 (frontend.zip) 
echo 3. 打包全部 (deploy_full.zip)
echo 4. 仅更新数据库文件到部署包
echo 0. 退出
echo.
set /p choice=请输入选项 (0-4): 

if "%choice%"=="1" goto pack_backend
if "%choice%"=="2" goto pack_frontend
if "%choice%"=="3" goto pack_all
if "%choice%"=="4" goto update_db
if "%choice%"=="0" goto end

:pack_backend
echo.
echo [1/2] 复制后端文件...

:: 删除旧的部署目录
if exist "%DEPLOY_DIR%\backend" rmdir /s /q "%DEPLOY_DIR%\backend"
mkdir "%DEPLOY_DIR%\backend"
mkdir "%DEPLOY_DIR%\backend\app"
mkdir "%DEPLOY_DIR%\backend\uploads"
mkdir "%DEPLOY_DIR%\backend\data"

:: 复制后端代码
xcopy /s /e /y "%BACKEND_DIR%\app\*" "%DEPLOY_DIR%\backend\app\"
copy /y "%BACKEND_DIR%\run.py" "%DEPLOY_DIR%\backend\"
copy /y "%BACKEND_DIR%\requirements.txt" "%DEPLOY_DIR%\backend\"
copy /y "%BACKEND_DIR%\app.db" "%DEPLOY_DIR%\backend\"
copy /y "%BACKEND_DIR%\migrate_to_mysql.py" "%DEPLOY_DIR%\backend\" 2>nul
copy /y "%BACKEND_DIR%\requirements_mysql.txt" "%DEPLOY_DIR%\backend\" 2>nul

:: 复制数据目录
xcopy /s /e /y "%BACKEND_DIR%\data\*" "%DEPLOY_DIR%\backend\data\" 2>nul

:: 复制uploads目录结构（不含大文件）
xcopy /s /e /y "%BACKEND_DIR%\uploads\site\*" "%DEPLOY_DIR%\backend\uploads\site\" 2>nul
xcopy /s /e /y "%BACKEND_DIR%\uploads\images\*" "%DEPLOY_DIR%\backend\uploads\images\" 2>nul
copy /y "%BACKEND_DIR%\uploads\site_settings.json" "%DEPLOY_DIR%\backend\uploads\" 2>nul

echo [2/2] 打包为 backend.zip...
cd "%DEPLOY_DIR%"
powershell -Command "Compress-Archive -Path 'backend' -DestinationPath 'backend.zip' -Force"

echo.
echo ========================================
echo 打包完成! 文件位置:
echo %DEPLOY_DIR%\backend.zip
echo ========================================
goto end

:pack_frontend
echo.
echo [1/2] 构建前端...
cd "%FRONTEND_DIR%"
call npm run build

echo [2/2] 打包为 frontend.zip...
cd "%FRONTEND_DIR%"
powershell -Command "Compress-Archive -Path 'dist' -DestinationPath '%DEPLOY_DIR%\frontend.zip' -Force"

echo.
echo ========================================
echo 打包完成! 文件位置:
echo %DEPLOY_DIR%\frontend.zip
echo ========================================
goto end

:pack_all
echo.
echo [1/4] 复制后端文件...

:: 删除旧的部署目录
if exist "%DEPLOY_DIR%\backend" rmdir /s /q "%DEPLOY_DIR%\backend"
mkdir "%DEPLOY_DIR%\backend"
mkdir "%DEPLOY_DIR%\backend\app"
mkdir "%DEPLOY_DIR%\backend\uploads"
mkdir "%DEPLOY_DIR%\backend\data"

:: 复制后端代码
xcopy /s /e /y "%BACKEND_DIR%\app\*" "%DEPLOY_DIR%\backend\app\"
copy /y "%BACKEND_DIR%\run.py" "%DEPLOY_DIR%\backend\"
copy /y "%BACKEND_DIR%\requirements.txt" "%DEPLOY_DIR%\backend\"
copy /y "%BACKEND_DIR%\app.db" "%DEPLOY_DIR%\backend\"
copy /y "%BACKEND_DIR%\migrate_to_mysql.py" "%DEPLOY_DIR%\backend\" 2>nul
copy /y "%BACKEND_DIR%\requirements_mysql.txt" "%DEPLOY_DIR%\backend\" 2>nul
xcopy /s /e /y "%BACKEND_DIR%\data\*" "%DEPLOY_DIR%\backend\data\" 2>nul
xcopy /s /e /y "%BACKEND_DIR%\uploads\site\*" "%DEPLOY_DIR%\backend\uploads\site\" 2>nul
xcopy /s /e /y "%BACKEND_DIR%\uploads\images\*" "%DEPLOY_DIR%\backend\uploads\images\" 2>nul
copy /y "%BACKEND_DIR%\uploads\site_settings.json" "%DEPLOY_DIR%\backend\uploads\" 2>nul

echo [2/4] 构建前端...
cd "%FRONTEND_DIR%"
call npm run build

echo [3/4] 复制前端文件...
if exist "%DEPLOY_DIR%\frontend" rmdir /s /q "%DEPLOY_DIR%\frontend"
mkdir "%DEPLOY_DIR%\frontend"
xcopy /s /e /y "%FRONTEND_DIR%\dist\*" "%DEPLOY_DIR%\frontend\dist\"

echo [4/4] 打包为 deploy_full.zip...
cd "%DEPLOY_DIR%"
powershell -Command "Compress-Archive -Path 'backend','frontend' -DestinationPath 'deploy_full.zip' -Force"

echo.
echo ========================================
echo 打包完成! 文件位置:
echo %DEPLOY_DIR%\deploy_full.zip
echo ========================================
goto end

:update_db
echo.
echo 更新数据库文件...
copy /y "%BACKEND_DIR%\app.db" "%DEPLOY_DIR%\backend\"
echo.
echo 数据库文件已更新!
goto end

:end
echo.
pause






