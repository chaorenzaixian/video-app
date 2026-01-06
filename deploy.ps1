# Soul视频 一键部署脚本
# 使用方法: 右键 -> 使用 PowerShell 运行

$ErrorActionPreference = "Stop"

# ============ 配置区域 ============
$SERVER_IP = "8.155.23.109"
$SERVER_USER = "root"
$SERVER_PATH = "/www/wwwroot/video-app"
$LOCAL_PATH = "C:\Users\garry\OneDrive\Desktop\video-app"

# SSH 密钥路径（如果有）
# $SSH_KEY = "C:\Users\garry\.ssh\id_rsa"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "       Soul视频 部署工具 v1.0" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 选择部署内容
Write-Host "请选择要部署的内容:" -ForegroundColor Yellow
Write-Host "1. 前端 (Frontend)"
Write-Host "2. 后端 (Backend) - 会自动备份"
Write-Host "3. 前端 + 后端"
Write-Host "4. 仅上传安装包 (packages)"
Write-Host "5. 全部 (前端+后端+安装包)"
Write-Host "6. 仅备份服务器数据"
Write-Host "7. 下载服务器备份到本地"
Write-Host "0. 退出"
Write-Host ""

$choice = Read-Host "请输入选项 (0-7)"

function Build-Frontend {
    Write-Host "`n[1/3] 构建前端..." -ForegroundColor Green
    Set-Location "$LOCAL_PATH\frontend"
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "前端构建失败" }
    Write-Host "前端构建完成!" -ForegroundColor Green
}

function Deploy-Frontend {
    Write-Host "`n[2/3] 上传前端到服务器..." -ForegroundColor Green
    
    # 使用 scp 上传
    $distPath = "$LOCAL_PATH\frontend\dist\*"
    $remotePath = "${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/frontend/dist/"
    
    scp -r $distPath $remotePath
    if ($LASTEXITCODE -ne 0) { throw "前端上传失败" }
    
    Write-Host "前端部署完成!" -ForegroundColor Green
}

function Backup-Server {
    Write-Host "`n[备份] 备份服务器数据..." -ForegroundColor Yellow
    
    $date = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupCmd = @"
cd ${SERVER_PATH}
mkdir -p backups
cp backend/video_app.db backups/video_app_${date}.db
tar -czf backups/uploads_${date}.tar.gz backend/uploads/ 2>/dev/null || true
echo "备份完成: backups/video_app_${date}.db"
"@
    
    ssh ${SERVER_USER}@${SERVER_IP} $backupCmd
    Write-Host "服务器备份完成!" -ForegroundColor Green
}

function Deploy-Backend {
    # 先备份
    Backup-Server
    
    Write-Host "`n[2/3] 上传后端到服务器..." -ForegroundColor Green
    
    # 上传后端文件
    $backendFiles = @(
        "backend/app",
        "backend/requirements.txt",
        "backend/main.py"
    )
    
    foreach ($file in $backendFiles) {
        $localFile = "$LOCAL_PATH\$file"
        $remoteFile = "${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/$file"
        
        if (Test-Path $localFile) {
            scp -r $localFile $remoteFile
        }
    }
    
    # 重启后端服务
    Write-Host "`n[3/3] 重启后端服务..." -ForegroundColor Green
    ssh ${SERVER_USER}@${SERVER_IP} "cd ${SERVER_PATH} && supervisorctl restart video-app"
    
    Write-Host "后端部署完成!" -ForegroundColor Green
}

function Download-Backup {
    Write-Host "`n下载服务器备份到本地..." -ForegroundColor Green
    
    # 创建本地备份目录
    $localBackupDir = "$LOCAL_PATH\backups"
    if (-not (Test-Path $localBackupDir)) {
        New-Item -ItemType Directory -Path $localBackupDir -Force | Out-Null
    }
    
    # 下载最新备份
    scp -r "${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/backups/*" $localBackupDir
    
    Write-Host "备份已下载到: $localBackupDir" -ForegroundColor Green
}

function Deploy-Packages {
    Write-Host "`n上传安装包..." -ForegroundColor Green
    
    $packagesPath = "$LOCAL_PATH\packages\*"
    $remotePath = "${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/frontend/dist/"
    
    scp -r $packagesPath $remotePath
    if ($LASTEXITCODE -ne 0) { throw "安装包上传失败" }
    
    Write-Host "安装包上传完成!" -ForegroundColor Green
}

try {
    switch ($choice) {
        "1" {
            Build-Frontend
            Deploy-Frontend
        }
        "2" {
            Deploy-Backend
        }
        "3" {
            Build-Frontend
            Deploy-Frontend
            Deploy-Backend
        }
        "4" {
            Deploy-Packages
        }
        "5" {
            Build-Frontend
            Deploy-Frontend
            Deploy-Backend
            Deploy-Packages
        }
        "6" {
            Backup-Server
        }
        "7" {
            Download-Backup
        }
        "0" {
            Write-Host "退出" -ForegroundColor Gray
            exit
        }
        default {
            Write-Host "无效选项" -ForegroundColor Red
            exit
        }
    }
    
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "       部署完成!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    
} catch {
    Write-Host "`n部署失败: $_" -ForegroundColor Red
}

Write-Host "`n按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")





$ErrorActionPreference = "Stop"

# ============ 配置区域 ============
$SERVER_IP = "8.155.23.109"
$SERVER_USER = "root"
$SERVER_PATH = "/www/wwwroot/video-app"
$LOCAL_PATH = "C:\Users\garry\OneDrive\Desktop\video-app"

# SSH 密钥路径（如果有）
# $SSH_KEY = "C:\Users\garry\.ssh\id_rsa"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "       Soul视频 部署工具 v1.0" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 选择部署内容
Write-Host "请选择要部署的内容:" -ForegroundColor Yellow
Write-Host "1. 前端 (Frontend)"
Write-Host "2. 后端 (Backend) - 会自动备份"
Write-Host "3. 前端 + 后端"
Write-Host "4. 仅上传安装包 (packages)"
Write-Host "5. 全部 (前端+后端+安装包)"
Write-Host "6. 仅备份服务器数据"
Write-Host "7. 下载服务器备份到本地"
Write-Host "0. 退出"
Write-Host ""

$choice = Read-Host "请输入选项 (0-7)"

function Build-Frontend {
    Write-Host "`n[1/3] 构建前端..." -ForegroundColor Green
    Set-Location "$LOCAL_PATH\frontend"
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "前端构建失败" }
    Write-Host "前端构建完成!" -ForegroundColor Green
}

function Deploy-Frontend {
    Write-Host "`n[2/3] 上传前端到服务器..." -ForegroundColor Green
    
    # 使用 scp 上传
    $distPath = "$LOCAL_PATH\frontend\dist\*"
    $remotePath = "${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/frontend/dist/"
    
    scp -r $distPath $remotePath
    if ($LASTEXITCODE -ne 0) { throw "前端上传失败" }
    
    Write-Host "前端部署完成!" -ForegroundColor Green
}

function Backup-Server {
    Write-Host "`n[备份] 备份服务器数据..." -ForegroundColor Yellow
    
    $date = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupCmd = @"
cd ${SERVER_PATH}
mkdir -p backups
cp backend/video_app.db backups/video_app_${date}.db
tar -czf backups/uploads_${date}.tar.gz backend/uploads/ 2>/dev/null || true
echo "备份完成: backups/video_app_${date}.db"
"@
    
    ssh ${SERVER_USER}@${SERVER_IP} $backupCmd
    Write-Host "服务器备份完成!" -ForegroundColor Green
}

function Deploy-Backend {
    # 先备份
    Backup-Server
    
    Write-Host "`n[2/3] 上传后端到服务器..." -ForegroundColor Green
    
    # 上传后端文件
    $backendFiles = @(
        "backend/app",
        "backend/requirements.txt",
        "backend/main.py"
    )
    
    foreach ($file in $backendFiles) {
        $localFile = "$LOCAL_PATH\$file"
        $remoteFile = "${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/$file"
        
        if (Test-Path $localFile) {
            scp -r $localFile $remoteFile
        }
    }
    
    # 重启后端服务
    Write-Host "`n[3/3] 重启后端服务..." -ForegroundColor Green
    ssh ${SERVER_USER}@${SERVER_IP} "cd ${SERVER_PATH} && supervisorctl restart video-app"
    
    Write-Host "后端部署完成!" -ForegroundColor Green
}

function Download-Backup {
    Write-Host "`n下载服务器备份到本地..." -ForegroundColor Green
    
    # 创建本地备份目录
    $localBackupDir = "$LOCAL_PATH\backups"
    if (-not (Test-Path $localBackupDir)) {
        New-Item -ItemType Directory -Path $localBackupDir -Force | Out-Null
    }
    
    # 下载最新备份
    scp -r "${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/backups/*" $localBackupDir
    
    Write-Host "备份已下载到: $localBackupDir" -ForegroundColor Green
}

function Deploy-Packages {
    Write-Host "`n上传安装包..." -ForegroundColor Green
    
    $packagesPath = "$LOCAL_PATH\packages\*"
    $remotePath = "${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/frontend/dist/"
    
    scp -r $packagesPath $remotePath
    if ($LASTEXITCODE -ne 0) { throw "安装包上传失败" }
    
    Write-Host "安装包上传完成!" -ForegroundColor Green
}

try {
    switch ($choice) {
        "1" {
            Build-Frontend
            Deploy-Frontend
        }
        "2" {
            Deploy-Backend
        }
        "3" {
            Build-Frontend
            Deploy-Frontend
            Deploy-Backend
        }
        "4" {
            Deploy-Packages
        }
        "5" {
            Build-Frontend
            Deploy-Frontend
            Deploy-Backend
            Deploy-Packages
        }
        "6" {
            Backup-Server
        }
        "7" {
            Download-Backup
        }
        "0" {
            Write-Host "退出" -ForegroundColor Gray
            exit
        }
        default {
            Write-Host "无效选项" -ForegroundColor Red
            exit
        }
    }
    
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "       部署完成!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    
} catch {
    Write-Host "`n部署失败: $_" -ForegroundColor Red
}

Write-Host "`n按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
