# 转码架构优化实施计划

## 📋 项目概述

**目标**: 优化视频处理架构，让转码服务器直接处理本地下载的视频，避免不必要的网络传输

**预期收益**:
- 带宽节省 60-70%
- 处理时间减少 50%
- 架构更清晰合理

## 🏗️ 目标架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        转码服务器 (198.176.60.121)               │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ 视频下载  │ →  │ GPU转码  │ →  │ 生成封面  │ →  │ 生成预览  │  │
│  │ (本地)   │    │ (NVENC)  │    │ (FFmpeg) │    │ (FFmpeg) │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│                                                       ↓         │
│                                              ┌──────────────┐   │
│                                              │  打包上传     │   │
│                                              │  • 视频.mp4  │   │
│                                              │  • 封面.webp │   │
│                                              │  • 预览.mp4  │   │
│                                              └──────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                    ↓ SCP上传 (50MB/s)
┌─────────────────────────────────────────────────────────────────┐
│                        主服务器 (38.47.218.137)                  │
├─────────────────────────────────────────────────────────────────┤
│  /uploads/videos/      ← 转码后视频                              │
│  /uploads/thumbnails/  ← 封面图片                                │
│  /uploads/previews/    ← 预览视频                                │
│                                                                  │
│  接收回调 → 更新数据库 → 发布视频                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 📅 实施阶段

### 阶段1: 转码脚本升级 (Day 1)

#### 任务1.1: 修改转码脚本，增加封面和预览生成

**文件**: `scripts/gpu_transcode_v2.sh` (转码服务器)

**新增功能**:
```bash
# 生成封面 (在视频30%位置截图)
generate_cover() {
    local input="$1"
    local output="$2"
    local duration=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$input")
    local position=$(echo "$duration * 0.3" | bc)
    
    ffmpeg -ss "$position" -i "$input" \
        -vframes 1 \
        -vf "scale=480:-1" \
        -q:v 2 \
        "$output"
}

# 生成预览 (截取10秒精彩片段)
generate_preview() {
    local input="$1"
    local output="$2"
    local duration=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$input")
    local start=$(echo "$duration * 0.2" | bc)
    
    ffmpeg -ss "$start" -i "$input" \
        -t 10 \
        -vf "scale=720:-1" \
        -c:v h264_nvenc \
        -preset fast \
        -b:v 1M \
        -an \
        "$output"
}
```

#### 任务1.2: 修改上传脚本，支持多文件上传

**文件**: `scripts/upload_to_main.ps1` (转码服务器)

**修改内容**:
```powershell
# 上传转码结果（视频+封面+预览）
function Upload-TranscodeResult {
    param(
        [string]$VideoFile,
        [string]$CoverFile,
        [string]$PreviewFile,
        [string]$VideoId
    )
    
    # 上传视频
    scp -i C:\server_key "$VideoFile" "root@38.47.218.137:/www/wwwroot/video-app/backend/uploads/videos/"
    
    # 上传封面
    scp -i C:\server_key "$CoverFile" "root@38.47.218.137:/www/wwwroot/video-app/backend/uploads/thumbnails/"
    
    # 上传预览
    scp -i C:\server_key "$PreviewFile" "root@38.47.218.137:/www/wwwroot/video-app/backend/uploads/previews/"
    
    # 通知主服务器
    Invoke-RestMethod -Uri "http://38.47.218.137:8000/api/v1/admin/transcode-callback" `
        -Method POST `
        -Headers @{"X-Transcode-Key"="vYTWoms4FKOqySca1jCLtNHRVz3BAI6U"} `
        -Body (@{
            video_id = $VideoId
            status = "completed"
            video_url = "/uploads/videos/$($VideoFile | Split-Path -Leaf)"
            cover_url = "/uploads/thumbnails/$($CoverFile | Split-Path -Leaf)"
            preview_url = "/uploads/previews/$($PreviewFile | Split-Path -Leaf)"
        } | ConvertTo-Json) `
        -ContentType "application/json"
}
```

### 阶段2: 主服务器适配 (Day 1-2)

#### 任务2.1: 创建预览目录

```bash
# 在主服务器执行
mkdir -p /www/wwwroot/video-app/backend/uploads/previews
chmod 755 /www/wwwroot/video-app/backend/uploads/previews
```

#### 任务2.2: 修改回调接口

**文件**: `backend/app/api/transcode_callback.py`

**修改内容**: 接收并处理封面和预览URL

```python
@router.post("/transcode-callback")
async def transcode_callback(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    data = await request.json()
    
    video_id = data.get("video_id")
    status = data.get("status")
    video_url = data.get("video_url")
    cover_url = data.get("cover_url")      # 新增
    preview_url = data.get("preview_url")  # 新增
    
    # 更新视频记录
    video = await db.get(Video, video_id)
    if video:
        video.hls_url = video_url
        video.cover_url = cover_url
        video.preview_url = preview_url
        video.status = VideoStatus.PUBLISHED
        await db.commit()
```

#### 任务2.3: 更新Nginx配置

```nginx
# 添加预览目录的静态文件服务
location /uploads/previews {
    alias /www/wwwroot/video-app/backend/uploads/previews;
    expires 30d;
}
```

### 阶段3: 监控脚本升级 (Day 2)

#### 任务3.1: 修改watcher脚本

**文件**: `scripts/watcher_with_upload.ps1`

**完整处理流程**:
```powershell
function Process-Video {
    param([string]$InputFile)
    
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($InputFile)
    $videoId = $baseName  # 或从文件名解析
    
    # 1. 转码
    $transcodedFile = "D:\VideoTranscode\completed\${baseName}_transcoded.mp4"
    Start-Transcode -Input $InputFile -Output $transcodedFile
    
    # 2. 生成封面
    $coverFile = "D:\VideoTranscode\completed\${baseName}_cover.webp"
    Generate-Cover -Input $transcodedFile -Output $coverFile
    
    # 3. 生成预览
    $previewFile = "D:\VideoTranscode\completed\${baseName}_preview.mp4"
    Generate-Preview -Input $transcodedFile -Output $previewFile
    
    # 4. 上传全部文件
    Upload-TranscodeResult `
        -VideoFile $transcodedFile `
        -CoverFile $coverFile `
        -PreviewFile $previewFile `
        -VideoId $videoId
    
    # 5. 清理本地文件
    Remove-Item $InputFile -Force
    Remove-Item $transcodedFile -Force
    Remove-Item $coverFile -Force
    Remove-Item $previewFile -Force
    
    Write-Log "Completed: $baseName"
}
```

### 阶段4: 测试验证 (Day 3)

#### 测试用例

| 测试项 | 预期结果 | 验证方法 |
|--------|---------|---------|
| 转码功能 | 视频正常转码 | 检查输出文件 |
| 封面生成 | 生成WebP封面 | 检查文件大小和格式 |
| 预览生成 | 生成10秒预览 | 播放验证 |
| 文件上传 | 3个文件全部上传成功 | 检查主服务器目录 |
| 回调通知 | 数据库正确更新 | 查询视频记录 |
| 前端显示 | 封面和预览正常显示 | 浏览器访问 |

#### 测试脚本

```powershell
# 在转码服务器执行
# 1. 创建测试视频
ffmpeg -f lavfi -i testsrc=duration=60:size=1920x1080:rate=30 `
    -c:v h264 -pix_fmt yuv420p `
    D:\VideoTranscode\downloads\test_full_flow.mp4

# 2. 观察处理流程
Get-Content D:\VideoTranscode\logs\watcher.log -Tail 50 -Wait

# 3. 验证主服务器文件
ssh -i C:\server_key root@38.47.218.137 "ls -la /www/wwwroot/video-app/backend/uploads/videos/ | tail -5"
ssh -i C:\server_key root@38.47.218.137 "ls -la /www/wwwroot/video-app/backend/uploads/thumbnails/ | tail -5"
ssh -i C:\server_key root@38.47.218.137 "ls -la /www/wwwroot/video-app/backend/uploads/previews/ | tail -5"
```

## 📁 需要修改的文件清单

### 转码服务器 (198.176.60.121)

| 文件 | 修改内容 | 优先级 |
|------|---------|--------|
| `D:\VideoTranscode\scripts\transcode.ps1` | 添加封面/预览生成 | P0 |
| `D:\VideoTranscode\scripts\upload_to_main.ps1` | 支持多文件上传 | P0 |
| `D:\VideoTranscode\scripts\watcher.ps1` | 完整处理流程 | P0 |

### 主服务器 (38.47.218.137)

| 文件 | 修改内容 | 优先级 |
|------|---------|--------|
| `backend/app/api/transcode_callback.py` | 接收封面/预览URL | P0 |
| `/etc/nginx/sites-available/default` | 添加previews目录 | P1 |
| 创建目录 `/uploads/previews/` | 新建目录 | P0 |

## ⏱️ 时间估算

| 阶段 | 任务 | 时间 |
|------|------|------|
| 阶段1 | 转码脚本升级 | 2小时 |
| 阶段2 | 主服务器适配 | 1小时 |
| 阶段3 | 监控脚本升级 | 1小时 |
| 阶段4 | 测试验证 | 1小时 |
| **总计** | | **5小时** |

## ✅ 验收标准

### 功能验收
- [ ] 转码服务器能生成封面图片（WebP格式，<200KB）
- [ ] 转码服务器能生成预览视频（10秒，<5MB）
- [ ] 三个文件能成功上传到主服务器
- [ ] 回调接口正确更新数据库
- [ ] 前端能正常显示封面和预览

### 性能验收
- [ ] 封面生成时间 < 5秒
- [ ] 预览生成时间 < 30秒
- [ ] 总上传时间 < 15秒（500MB视频）
- [ ] 处理完成后本地文件已清理

### 质量验收
- [ ] 封面清晰度满足要求
- [ ] 预览流畅无卡顿
- [ ] 日志记录完整
- [ ] 错误处理正确

## 🚀 后续优化

1. **智能封面选择**: 使用AI选择最佳封面帧
2. **多分辨率预览**: 生成不同分辨率的预览
3. **HLS切片**: 在转码服务器生成HLS切片
4. **并行处理**: 同时生成封面和预览

---

**创建时间**: 2026-01-16  
**预计完成**: 2026-01-17  
**负责人**: 开发团队  
**状态**: 📋 待实施
