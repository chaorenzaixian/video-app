# GPU 转码服务器配置指南

## 架构概览

```
用户上传视频 → 主服务器接收 → 推送到GPU服务器 → GPU转码 → rsync同步回主服务器 → API回调更新状态
```

## 服务器信息

| 服务器 | IP | 用途 |
|--------|-----|------|
| 主服务器 | 38.47.218.137 | Web服务、数据库、文件存储 |
| GPU服务器 | 149.36.0.246 | 视频转码 (2x RTX A4000) |

## 启用 GPU 转码

在主服务器的 `.env` 文件中添加：

```bash
# GPU 转码配置
GPU_TRANSCODE_ENABLED=true
GPU_SERVER_HOST=149.36.0.246
GPU_SERVER_USER=ubuntu
GPU_SERVER_WORK_DIR=/home/ubuntu/video-transcode
```

## GPU 服务器配置

### 1. 目录结构
```
~/video-transcode/
├── uploads/          # 待处理视频
├── processed/        # 处理完成的文件
├── logs/             # 日志
├── transcode.sh      # 转码脚本
└── watch_service.sh  # 监控服务
```

### 2. 转码脚本使用

```bash
# 测试 GPU 编码
./transcode.sh test

# 处理单个视频
./transcode.sh process <video_id> <input_file>

# 示例
./transcode.sh process 123 /path/to/video.mp4
```

### 3. 监控服务

```bash
# 启动监控服务 (自动处理新上传的视频)
./watch_service.sh start

# 停止监控服务
./watch_service.sh stop

# 查看状态
./watch_service.sh status

# 重启
./watch_service.sh restart
```

### 4. 处理流程

1. **缩略图生成** (CPU) - 智能选帧，5个采样点选最佳
2. **预览视频生成** (GPU辅助) - 10段×1秒，WebM格式
3. **HLS多清晰度转码** (GPU NVENC) - 1080p/720p/480p
4. **rsync同步** - 同步到主服务器
5. **API回调** - 通知主服务器更新视频状态

## 主服务器 API

### 回调 API

```
POST /api/v1/admin/transcode-callback
Header: X-Transcode-Key: vYTWoms4FKOqySca1jCLtNHRVz3BAI6U

Body:
{
    "video_id": 123,
    "status": "success",  // success / failed
    "thumbnail_url": "/uploads/thumbnails/123.webp",
    "preview_url": "/uploads/previews/123.webm",
    "hls_url": "/uploads/hls/123/master.m3u8"
}
```

### GPU 状态 API

```
GET /api/v1/admin/gpu-status

Response:
{
    "enabled": true,
    "server": {
        "status": "online",
        "host": "149.36.0.246",
        "gpus": [
            {"name": "NVIDIA RTX A4000", "memory_used": "1024 MiB", "memory_total": "15352 MiB", "utilization": "5 %"}
        ]
    },
    "processing_queue": []
}
```

## 性能对比

| 操作 | CPU (主服务器) | GPU (RTX A4000) | 提升 |
|------|---------------|-----------------|------|
| 1080p HLS转码 (5分钟视频) | ~10分钟 | ~30秒 | 20x |
| 720p HLS转码 | ~5分钟 | ~20秒 | 15x |
| 预览视频生成 | ~30秒 | ~10秒 | 3x |
| 缩略图生成 | ~2秒 | ~2秒 | - |

## 安全配置

1. GPU服务器已配置SSH密钥访问主服务器
2. 回调API使用密钥验证 (X-Transcode-Key)
3. 密钥: `vYTWoms4FKOqySca1jCLtNHRVz3BAI6U`

## 故障排查

```bash
# 查看GPU状态
nvidia-smi

# 查看转码日志
tail -f ~/video-transcode/logs/transcode_*.log

# 查看监控服务日志
tail -f ~/video-transcode/logs/watch_*.log

# 测试SSH连接
ssh root@38.47.218.137 'echo OK'

# 测试rsync
rsync -avz --dry-run test.txt root@38.47.218.137:/tmp/
```
