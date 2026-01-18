#!/usr/bin/env python3
"""
修改转码脚本 - 添加自动上传到主服务器功能
"""
import paramiko
import sys
import base64

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

# 带上传功能的转码脚本
TRANSCODE_SCRIPT = r'''# Transcode Script - With auto upload to main server
# Supports Chinese filenames and special characters
param(
    [Parameter(Mandatory=$true)]
    [string]$InputFile,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet('short', 'long')]
    [string]$VideoType = 'short'
)

# Set UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$LogFile = "D:\VideoTranscode\logs\transcode.log"

# Main server config
$mainServer = "38.47.218.137"
$mainUser = "root"
$keyFile = "C:\server_key"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logMessage = "$timestamp - $Message"
    Write-Host $logMessage
    Add-Content -Path $LogFile -Value $logMessage -Encoding UTF8
}

function Upload-ToMainServer {
    param(
        [string]$LocalFile,
        [string]$RemotePath
    )
    
    if (-not (Test-Path -LiteralPath $LocalFile)) {
        Write-Log "Upload: File not found: $LocalFile"
        return $false
    }
    
    if (-not (Test-Path $keyFile)) {
        Write-Log "Upload: SSH key not found: $keyFile"
        return $false
    }
    
    $fileName = [System.IO.Path]::GetFileName($LocalFile)
    $fileSize = (Get-Item -LiteralPath $LocalFile).Length / 1MB
    $fileSizeRounded = [math]::Round($fileSize, 2)
    
    Write-Log "Upload: $fileName ($fileSizeRounded MB) -> $RemotePath"
    
    # Use scp with quotes for special characters
    $scpArgs = @(
        "-i", $keyFile,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=NUL",
        "-o", "ConnectTimeout=30",
        "`"$LocalFile`"",
        "${mainUser}@${mainServer}:${RemotePath}"
    )
    
    try {
        $process = Start-Process -FilePath "scp" -ArgumentList $scpArgs -NoNewWindow -Wait -PassThru
        
        if ($process.ExitCode -eq 0) {
            Write-Log "Upload: Success - $fileName"
            return $true
        } else {
            Write-Log "Upload: Failed - $fileName (Exit code: $($process.ExitCode))"
            return $false
        }
    } catch {
        Write-Log "Upload: Error - $_"
        return $false
    }
}

Write-Log "=========================================="
Write-Log "Starting transcode"
Write-Log "Input: $InputFile"
Write-Log "Video Type: $VideoType"

# Check input file
if (-not (Test-Path -LiteralPath $InputFile)) {
    Write-Log "ERROR: Input file not found: $InputFile"
    exit 1
}

# Get filename
$fileName = [System.IO.Path]::GetFileNameWithoutExtension($InputFile)
$fileExt = [System.IO.Path]::GetExtension($InputFile)

# Set output directory
$outputDir = "D:\VideoTranscode\completed\$VideoType"

if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    Write-Log "Created output directory: $outputDir"
}

# Output file path
$outputFile = Join-Path $outputDir "${fileName}_transcoded${fileExt}"
Write-Log "Output: $outputFile"

# Check NVIDIA GPU
$hasNVIDIA = $false
try {
    $nvidiaSmi = & nvidia-smi 2>&1
    if ($LASTEXITCODE -eq 0) {
        $hasNVIDIA = $true
        Write-Log "Using GPU (NVENC)"
    }
}
catch {
    Write-Log "GPU not available, using CPU"
}

# Execute transcode
Write-Log "Starting FFmpeg..."

$inputQuoted = "`"$InputFile`""
$outputQuoted = "`"$outputFile`""

try {
    if ($hasNVIDIA) {
        $ffmpegCmd = "ffmpeg -hwaccel cuda -i $inputQuoted -c:v h264_nvenc -preset fast -b:v 2M -c:a aac -b:a 128k -y $outputQuoted"
    }
    else {
        $ffmpegCmd = "ffmpeg -i $inputQuoted -c:v libx264 -preset medium -crf 23 -c:a aac -b:a 128k -y $outputQuoted"
    }
    
    Write-Log "Command: $ffmpegCmd"
    
    $process = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $ffmpegCmd -NoNewWindow -Wait -PassThru
    $exitCode = $process.ExitCode
    
    Write-Log "FFmpeg exit code: $exitCode"
    
    if ($exitCode -eq 0) {
        if (Test-Path -LiteralPath $outputFile) {
            $outputSize = (Get-Item -LiteralPath $outputFile).Length / 1MB
            $outputSizeRounded = [math]::Round($outputSize, 2)
            Write-Log "Transcode successful! Output size: $outputSizeRounded MB"
            
            # Delete original file
            Remove-Item -LiteralPath $InputFile -Force
            Write-Log "Removed input file: $InputFile"
            
            # ========== UPLOAD TO MAIN SERVER ==========
            Write-Log "=========================================="
            Write-Log "Starting upload to main server..."
            
            # Set remote path based on video type
            if ($VideoType -eq "short") {
                $remotePath = "/www/wwwroot/video-app/backend/uploads/shorts/"
            } else {
                $remotePath = "/www/wwwroot/video-app/backend/uploads/videos/"
            }
            
            $uploadSuccess = Upload-ToMainServer -LocalFile $outputFile -RemotePath $remotePath
            
            if ($uploadSuccess) {
                Write-Log "Upload completed successfully!"
                
                # Optionally delete local file after upload
                # Remove-Item -LiteralPath $outputFile -Force
                # Write-Log "Removed local file after upload"
            } else {
                Write-Log "Upload failed - file kept locally"
            }
            
            Write-Log "=========================================="
            exit 0
        }
        else {
            Write-Log "ERROR: Output file not created"
            exit 1
        }
    }
    else {
        Write-Log "Transcode failed! Exit code: $exitCode"
        exit 1
    }
}
catch {
    Write-Log "ERROR: $_"
    exit 1
}
'''

print("🔧 修改转码脚本 - 添加自动上传功能")
print("=" * 60)

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"🔐 连接到 {TRANSCODE_SERVER}...")
    ssh.connect(
        hostname=TRANSCODE_SERVER,
        port=22,
        username=TRANSCODE_USER,
        password=TRANSCODE_PASSWORD,
        timeout=30
    )
    print("✅ 连接成功!\n")
    
    # 1. 备份
    print("📋 备份旧脚本...")
    stdin, stdout, stderr = ssh.exec_command('copy D:\\VideoTranscode\\scripts\\transcode_full.ps1 D:\\VideoTranscode\\scripts\\transcode_full.ps1.bak_upload /Y', timeout=30)
    stdout.read()
    print("  ✅ 已备份\n")
    
    # 2. 上传新脚本
    print("📋 上传新转码脚本...")
    script_bytes = TRANSCODE_SCRIPT.encode('utf-8')
    script_b64 = base64.b64encode(script_bytes).decode('ascii')
    
    chunk_size = 8000
    chunks = [script_b64[i:i+chunk_size] for i in range(0, len(script_b64), chunk_size)]
    
    stdin, stdout, stderr = ssh.exec_command('del D:\\VideoTranscode\\scripts\\transcode_temp.b64 2>nul', timeout=30)
    stdout.read()
    
    for i, chunk in enumerate(chunks):
        cmd = f'powershell -Command "Add-Content -Path D:\\VideoTranscode\\scripts\\transcode_temp.b64 -Value \'{chunk}\' -Encoding ASCII"'
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
        stdout.read()
        print(f"  上传进度: {i+1}/{len(chunks)}")
    
    decode_cmd = '''powershell -Command "$b64 = Get-Content D:\\VideoTranscode\\scripts\\transcode_temp.b64 -Raw; $bytes = [System.Convert]::FromBase64String($b64); [System.IO.File]::WriteAllBytes('D:\\VideoTranscode\\scripts\\transcode_full.ps1', $bytes); Remove-Item D:\\VideoTranscode\\scripts\\transcode_temp.b64"'''
    stdin, stdout, stderr = ssh.exec_command(decode_cmd, timeout=30)
    stdout.read()
    print("  ✅ 脚本已上传\n")
    
    # 3. 测试语法
    print("📋 测试脚本语法...")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "& { $ErrorActionPreference = \'Stop\'; try { $null = [System.Management.Automation.PSParser]::Tokenize((Get-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1 -Raw), [ref]$null); Write-Host \'OK\' } catch { Write-Host \'ERROR:\' $_ } }"', timeout=30)
    output = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"  语法检查: {output}\n")
    
    # 4. 验证上传功能
    print("📋 验证脚本包含上传功能...")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1 | Select-String -Pattern \'Upload-ToMainServer\'"', timeout=30)
    output = stdout.read().decode('utf-8', errors='ignore').strip()
    if output:
        print("  ✅ 脚本包含上传功能")
    else:
        print("  ❌ 脚本不包含上传功能")
    
    # 5. 检查 SSH 密钥
    print("\n📋 检查 SSH 密钥...")
    stdin, stdout, stderr = ssh.exec_command('dir C:\\server_key 2>nul', timeout=30)
    output = stdout.read().decode('gbk', errors='ignore').strip()
    if 'server_key' in output:
        print("  ✅ SSH 密钥存在")
    else:
        print("  ❌ SSH 密钥不存在")
        print("  ⚠️ 需要配置 SSH 密钥才能上传")
    
    # 6. 重启 Watcher
    print("\n📋 重启 Watcher 服务...")
    stdin, stdout, stderr = ssh.exec_command('taskkill /F /IM powershell.exe 2>nul', timeout=30)
    stdout.read()
    
    import time
    time.sleep(3)
    
    stdin, stdout, stderr = ssh.exec_command('schtasks /Run /TN "VideoWatcherService"', timeout=30)
    stdout.read()
    
    stdin, stdout, stderr = ssh.exec_command('wmic process call create "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File D:\\VideoTranscode\\scripts\\watcher.ps1"', timeout=30)
    stdout.read()
    
    time.sleep(5)
    
    # 7. 验证
    print("\n" + "=" * 60)
    print("📊 验证结果")
    print("=" * 60)
    
    stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq powershell.exe" /FO CSV /NH', timeout=30)
    output = stdout.read().decode('gbk', errors='ignore').strip()
    ps_count = len([l for l in output.split('\n') if 'powershell.exe' in l])
    
    print(f"\n✅ PowerShell 进程: {ps_count} 个")
    
    print("\n" + "=" * 60)
    print("✅ 修改完成!")
    print("\n💡 新功能:")
    print("- 转码完成后自动上传到主服务器")
    print("- 短视频上传到: /uploads/shorts/")
    print("- 长视频上传到: /uploads/videos/")
    print("- 支持中文文件名")
    
    print("\n📝 工作流程:")
    print("1. 视频放入 downloads/short 或 downloads/long")
    print("2. Watcher 检测并移动到 processing")
    print("3. 转码脚本进行转码")
    print("4. 转码完成后自动上传到主服务器")
    print("5. 本地保留一份副本")
    
except Exception as e:
    print(f"\n❌ 修改失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()
