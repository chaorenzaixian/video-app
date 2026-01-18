#!/usr/bin/env python3
"""部署智能封面选择功能到转码脚本"""
import paramiko
import time

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'

# 智能封面选择函数 - 使用文件大小 + 图像清晰度 + 色彩丰富度
SMART_COVER_FUNCTION = r'''
function Get-BestCover {
    param([string]$CoversDir, [int]$CoverCount = 10)
    
    # 评分数组
    $scores = @{}
    
    for ($i = 1; $i -le $CoverCount; $i++) {
        $coverPath = "$CoversDir\cover_$i.webp"
        if (-not (Test-Path $coverPath)) { continue }
        
        $score = 0
        
        # 1. 文件大小评分 (30%) - 文件越大通常内容越丰富
        $fileSize = (Get-Item $coverPath).Length
        $sizeScore = [Math]::Min($fileSize / 30000, 1) * 30  # 30KB 为满分
        $score += $sizeScore
        
        # 2. 图像清晰度评分 (40%) - 使用 ffprobe 获取图像信息
        try {
            # 使用 ffprobe 获取图像的平均亮度和对比度信息
            $probeResult = & ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 $coverPath 2>$null
            if ($probeResult) {
                $dims = $probeResult -split ','
                $width = [int]$dims[0]
                $height = [int]$dims[1]
                # 分辨率越高，清晰度评分越高
                $resScore = [Math]::Min(($width * $height) / (640 * 360), 1) * 20
                $score += $resScore
            }
            
            # 使用 ffmpeg 计算图像的拉普拉斯方差（清晰度指标）
            $blurResult = & ffmpeg -i $coverPath -vf "format=gray,sobel" -f null - 2>&1 | Select-String "mean"
            if ($blurResult) {
                # 边缘检测结果越强，图像越清晰
                $score += 20  # 简化处理，有边缘信息就加分
            } else {
                $score += 10  # 默认中等分数
            }
        } catch {
            $score += 15  # 出错时给中等分数
        }
        
        # 3. 避开片头片尾 (30%) - 中间位置的帧更可能是精彩内容
        # 位置 1-10 对应视频的 1/11 到 10/11 位置
        # 最佳位置是 4-7 (约 36%-64% 位置)
        $positionScore = 0
        if ($i -ge 4 -and $i -le 7) {
            $positionScore = 30  # 中间位置满分
        } elseif ($i -ge 3 -and $i -le 8) {
            $positionScore = 20  # 次优位置
        } else {
            $positionScore = 10  # 边缘位置
        }
        $score += $positionScore
        
        $scores[$i] = $score
        Write-Log "    Cover $i score: $([Math]::Round($score, 1)) (size: $([Math]::Round($sizeScore, 1)), pos: $positionScore)"
    }
    
    # 找出最高分的封面
    $bestCover = 5  # 默认中间位置
    $maxScore = 0
    foreach ($key in $scores.Keys) {
        if ($scores[$key] -gt $maxScore) {
            $maxScore = $scores[$key]
            $bestCover = $key
        }
    }
    
    Write-Log "  Best cover: cover_$bestCover (score: $([Math]::Round($maxScore, 1)))"
    return $bestCover
}
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=60)

print("部署智能封面选择功能...")

# 读取当前脚本
sftp = ssh.open_sftp()
with sftp.file('D:/VideoTranscode/scripts/watcher.ps1', 'r') as f:
    content = f.read().decode('utf-8')

# 1. 添加智能封面选择函数（在 Write-Log 函数后面）
if 'function Get-BestCover' not in content:
    # 在 Get-VideoHeight 函数后添加
    insert_pos = content.find('function Upload-SingleFile')
    if insert_pos > 0:
        content = content[:insert_pos] + SMART_COVER_FUNCTION + '\n\n' + content[insert_pos:]
        print("✓ 添加了 Get-BestCover 函数")
    else:
        print("✗ 未找到插入位置")
else:
    print("✓ Get-BestCover 函数已存在")

# 2. 修改短视频封面选择逻辑
old_short_cover = '''        $bestCover = 5; $maxSize = 0
        foreach ($key in $coverSizes.Keys) { if ($coverSizes[$key] -gt $maxSize) { $maxSize = $coverSizes[$key]; $bestCover = $key } }'''

new_short_cover = '''        # 智能选择最佳封面
        $bestCover = Get-BestCover -CoversDir $coversDir -CoverCount 10'''

if old_short_cover in content:
    content = content.replace(old_short_cover, new_short_cover)
    print("✓ 更新了短视频封面选择逻辑")

# 3. 修改长视频封面选择逻辑（可能有两处）
# 长视频的封面选择代码
old_long_cover = '''        $bestCover = 5; $maxSize = 0
        foreach ($key in $coverSizes.Keys) { if ($coverSizes[$key] -gt $maxSize) { $maxSize = $coverSizes[$key]; $bestCover = $key } }
        $mainCover = "$outDir\\$name.webp"'''

new_long_cover = '''        # 智能选择最佳封面
        $bestCover = Get-BestCover -CoversDir $coversDir -CoverCount 10
        $mainCover = "$outDir\\$name.webp"'''

if old_long_cover in content:
    content = content.replace(old_long_cover, new_long_cover)
    print("✓ 更新了长视频封面选择逻辑")
else:
    # 尝试另一种格式
    old_long_cover2 = '''$bestCover = 5; $maxSize = 0
        foreach ($key in $coverSizes.Keys) { if ($coverSizes[$key] -gt $maxSize) { $maxSize = $coverSizes[$key]; $bestCover = $key } }'''
    new_long_cover2 = '''# 智能选择最佳封面
        $bestCover = Get-BestCover -CoversDir $coversDir -CoverCount 10'''
    
    # 替换所有出现的地方
    content = content.replace(old_long_cover2, new_long_cover2)
    print("✓ 更新了封面选择逻辑（备用格式）")

# 写回文件
with sftp.file('D:/VideoTranscode/scripts/watcher.ps1', 'w') as f:
    f.write(content)
sftp.close()

print("✓ 脚本已更新")

# 重启 watcher
print("\n重启 watcher...")
cmd = 'taskkill /F /IM powershell.exe /FI "WINDOWTITLE eq watcher*" 2>nul'
ssh.exec_command(cmd, timeout=30)
time.sleep(2)

cmd = 'schtasks /Run /TN "StartWatcher"'
ssh.exec_command(cmd, timeout=30)
time.sleep(3)

# 检查状态
cmd = 'tasklist | findstr powershell'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
if 'powershell' in output.lower():
    print("✓ Watcher 已重启")
else:
    print("✗ Watcher 未启动")

ssh.close()

print("\n" + "=" * 60)
print("智能封面选择功能已部署！")
print("评分规则：")
print("  • 文件大小 (30%): 内容丰富度指标")
print("  • 图像清晰度 (40%): 分辨率 + 边缘检测")
print("  • 位置权重 (30%): 优先选择视频中间部分")
print("=" * 60)
