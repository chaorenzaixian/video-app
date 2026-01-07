# Soul视频 一键部署脚本
# 使用方法: 右键 -> 使用 PowerShell 运行

$ErrorActionPreference = "Stop"

# ============ 配置区域 ============
$SERVER_IP = "38.181.44.148"
$SERVER_USER = "root"
$SERVER_PATH = "/www/wwwroot/video-app"
$LOCAL_PATH = $PSScriptRoot  # 自动获取脚本所在目录

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "       Soul视频 部署工具 v2.0" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "服务器: $SERVER_IP" -ForegroundColor Gray
Write-Host ""

Write-Host "请选择要部署的内容:" -ForegroundColor Yellow
Write-Host "1. 前端 (Frontend) - 构建并上传"
Write-Host "2. 后端 (Backend) - 会自动备份"
Write-Host "3. 前端 + 后端"
Write-Host "4. 仅上传安装包 (packages)"
Write-Host "5. 全部 (前端+后端+安装包)"
Write-Host "6. 仅备份服务器数据"
Write-Host "7. 下载服务器备份到本地"
Write-Host "8. Git 推送到 GitHub"
Write-Host "9. 服务器从 GitHub 拉取并重启"
Write-Host "0. 退出"
Write-Host ""

$choice = Read-Host "请输入选项 (0-9)"

function Build-Frontend {
    Write-Host "`n[构建] 构建前端..." -ForegroundColor Green
    Set-Location "$LOCAL_PATH\frontend"
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "前端构建失败" }
    Set-Location $LOCAL_PATH
    Write-Host "前端构建完成!" -ForegroundColor Green
}

function Deploy-Frontend {
    Write-Host "`n[上传] 上传前端到服务器..." -ForegroundColor Green
    $distPath = "$LOCAL_PATH\frontend\dist\*"
    $remotePath = "${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/frontend/dist/"
    scp -r $distPath $remotePath
    if ($LASTEXITCODE -ne 0) { throw "前端上传失败" }
    Write-Host "前端部署完成!" -ForegroundColor Green
}

function Backup-Server {
    Write-Host "`n[备份] 备份服务器数据..." -ForegroundColor Yellow
    $date = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupCmd = "cd ${SERVER_PATH} && mkdir -p backups && cp backend/app.db backups/app_${date}.db 2>/dev/null || true && echo '备份完成'"
    ssh ${SERVER_USER}@${SERVER_IP} $backupCmd
    Write-Host "服务器备份完成!" -ForegroundColor Green
}

function Deploy-Backend {
    Backup-Server
    Write-Host "`n[上传] 上传后端到服务器..." -ForegroundColor Green
    
    # 上传 app 目录
    scp -r "$LOCAL_PATH\backend\app" "${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/backend/"
    scp "$LOCAL_PATH\backend\requirements.txt" "${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/backend/"
    scp "$LOCAL_PATH\backend\run.py" "${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/backend/"
    
    Write-Host "`n[重启] 重启后端服务..." -ForegroundColor Green
    ssh ${SERVER_USER}@${SERVER_IP} "cd ${SERVER_PATH} && supervisorctl restart video-app 2>/dev/null || pm2 restart all 2>/dev/null || echo '请手动重启服务'"
    Write-Host "后端部署完成!" -ForegroundColor Green
}

function Download-Backup {
    Write-Host "`n下载服务器备份到本地..." -ForegroundColor Green
    $localBackupDir = "$LOCAL_PATH\backups"
    if (-not (Test-Path $localBackupDir)) {
        New-Item -ItemType Directory -Path $localBackupDir -Force | Out-Null
    }
    scp -r "${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/backups/*" $localBackupDir
    Write-Host "备份已下载到: $localBackupDir" -ForegroundColor Green
}

function Deploy-Packages {
    Write-Host "`n上传安装包..." -ForegroundColor Green
    $packagesPath = "$LOCAL_PATH\packages\*"
    $remotePath = "${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/frontend/dist/"
    scp -r $packagesPath $remotePath
    Write-Host "安装包上传完成!" -ForegroundColor Green
}

function Git-Push {
    Write-Host "`n[Git] 推送到 GitHub..." -ForegroundColor Green
    Set-Location $LOCAL_PATH
    
    $commitMsg = Read-Host "请输入提交信息 (直接回车使用默认)"
    if ([string]::IsNullOrWhiteSpace($commitMsg)) {
        $commitMsg = "update: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    }
    
    git add -A
    git commit -m $commitMsg
    git push origin main
    
    if ($LASTEXITCODE -ne 0) { 
        Write-Host "尝试推送到 master 分支..." -ForegroundColor Yellow
        git push origin master 
    }
    Write-Host "Git 推送完成!" -ForegroundColor Green
}

function Server-GitPull {
    Write-Host "`n[服务器] 从 GitHub 拉取更新..." -ForegroundColor Green
    
    $pullCmd = @"
cd ${SERVER_PATH}
git pull origin main 2>/dev/null || git pull origin master
cd frontend && npm run build
supervisorctl restart video-app 2>/dev/null || pm2 restart all 2>/dev/null || echo '请手动重启'
echo '更新完成!'
"@
    
    ssh ${SERVER_USER}@${SERVER_IP} $pullCmd
    Write-Host "服务器更新完成!" -ForegroundColor Green
}

try {
    switch ($choice) {
        "1" { Build-Frontend; Deploy-Frontend }
        "2" { Deploy-Backend }
        "3" { Build-Frontend; Deploy-Frontend; Deploy-Backend }
        "4" { Deploy-Packages }
        "5" { Build-Frontend; Deploy-Frontend; Deploy-Backend; Deploy-Packages }
        "6" { Backup-Server }
        "7" { Download-Backup }
        "8" { Git-Push }
        "9" { Server-GitPull }
        "0" { Write-Host "退出" -ForegroundColor Gray; exit }
        default { Write-Host "无效选项" -ForegroundColor Red; exit }
    }
    
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "       操作完成!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    
} catch {
    Write-Host "`n操作失败: $_" -ForegroundColor Red
}

Write-Host "`n按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
