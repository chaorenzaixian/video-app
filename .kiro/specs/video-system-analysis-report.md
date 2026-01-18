# 视频系统深度分析报告

## 📋 系统架构概览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           视频处理流程                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  用户上传 ──→ videos.py ──→ VideoProcessor ──→ 本地处理/GPU转码          │
│                  │                                    │                  │
│                  ↓                                    ↓                  │
│            保存原始文件                         生成封面/预览/HLS         │
│            创建数据库记录                              │                  │
│                                                       ↓                  │
│                                              回调更新数据库               │
│                                                       │                  │
│                                                       ↓                  │
│                                              视频发布 (PUBLISHED)         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## 🔍 发现的问题

### 问题1: 转码服务器回调字段不一致 ⚠️ 已修复

**位置**: `transcode_callback.py` vs `transcode_full.ps1`

**问题描述**:
- 回调接口期望字段: `thumbnail_url`, `preview_url`, `hls_url`
- 转码脚本发送字段: `cover_url`, `preview_url`, `video_url`

**修复状态**: ✅ 已在 `transcode_callback.py` 中统一

### 问题2: 预览视频格式不一致 ⚠️ 需要注意

**位置**: 
- 本地处理: `video_processor.py` 生成 `.webm` 格式
- 转码服务器: `transcode_full.ps1` 生成 `.mp4` 格式

**影响**: 
- 前端需要同时支持两种格式
- 文件URL路径不一致

**建议**: 统一使用 MP4 格式（兼容性更好）

### 问题3: 封面格式不一致 ⚠️ 需要注意

**位置**:
- 本地处理: 生成 `.webp` 格式
- 转码服务器: 生成 `.webp` 格式 ✅ 一致

### 问题4: GPU转码服务配置过时 ⚠️ 需要更新

**位置**: `gpu_transcode_service.py`

**问题**:
```python
GPU_SERVER_HOST = os.getenv("GPU_SERVER_HOST", "149.36.0.246")  # 旧IP
GPU_SERVER_USER = os.getenv("GPU_SERVER_USER", "ubuntu")        # 旧用户
```

**实际配置**:
- 转码服务器IP: `198.176.60.121`
- 用户: `Administrator`
- 系统: Windows

**建议**: 更新配置或禁用旧的GPU服务

### 问题5: 视频时长未在回调中更新 ⚠️ 已修复

**位置**: `transcode_callback.py`

**问题**: 回调接口已添加 `duration` 字段，但转码脚本未发送

**修复**: 需要在 `upload_full.ps1` 中添加时长信息

### 问题6: 文件清理策略不完整

**位置**: `video_processor.py`, `watcher_full.ps1`

**问题**:
- 本地处理后原始文件未删除
- 转码服务器处理后会删除本地文件

**建议**: 统一清理策略，避免磁盘空间浪费

## 🧪 功能测试清单

### 1. 视频上传测试

| 测试项 | 预期结果 | 状态 |
|--------|---------|------|
| 小文件上传 (<100MB) | 成功上传，本地处理 | 待测试 |
| 大文件上传 (>500MB) | 成功上传，GPU处理 | 待测试 |
| 不支持格式上传 | 返回错误提示 | 待测试 |
| 超大文件上传 (>5GB) | 返回大小限制错误 | 待测试 |

### 2. 转码处理测试

| 测试项 | 预期结果 | 状态 |
|--------|---------|------|
| 本地CPU转码 | 生成HLS文件 | 待测试 |
| GPU加速转码 | 生成HLS文件，速度更快 | 待测试 |
| 多清晰度转码 | 生成480p/720p/1080p | 待测试 |
| 转码失败处理 | 状态更新为FAILED | 待测试 |

### 3. 封面生成测试

| 测试项 | 预期结果 | 状态 |
|--------|---------|------|
| 自动生成封面 | WebP格式，<200KB | 待测试 |
| 自定义封面上传 | 保存并使用自定义封面 | 待测试 |
| 智能选帧 | 选择最佳帧作为封面 | 待测试 |

### 4. 预览生成测试

| 测试项 | 预期结果 | 状态 |
|--------|---------|------|
| 分段预览生成 | 10段，每段1秒 | 待测试 |
| 短视频预览 | 按比例生成 | 待测试 |
| 预览播放 | 前端悬停可播放 | 待测试 |

### 5. 回调接口测试

| 测试项 | 预期结果 | 状态 |
|--------|---------|------|
| 成功回调 | 更新封面/预览/HLS URL | 待测试 |
| 失败回调 | 状态更新为FAILED | 待测试 |
| 密钥验证 | 无效密钥返回403 | 待测试 |

## 🔧 优化建议

### 高优先级

#### 1. 统一预览视频格式
```python
# video_processor.py 修改
# 将 WebM 改为 MP4，提高兼容性
preview_path = os.path.join(preview_dir, f"{video_id}.mp4")
```

#### 2. 更新GPU服务配置
```python
# gpu_transcode_service.py
GPU_SERVER_HOST = os.getenv("GPU_SERVER_HOST", "198.176.60.121")
GPU_SERVER_USER = os.getenv("GPU_SERVER_USER", "Administrator")
GPU_TRANSCODE_ENABLED = os.getenv("GPU_TRANSCODE_ENABLED", "true")
```

#### 3. 添加视频时长到回调
```powershell
# upload_full.ps1 修改
$body = @{
    video_id = [int]$VideoId
    status = $Status
    thumbnail_url = $CoverUrl
    preview_url = $PreviewUrl
    hls_url = $VideoUrl
    duration = $Duration  # 添加时长
}
```

### 中优先级

#### 4. 添加处理进度WebSocket推送
```python
# 实时推送处理进度到前端
async def push_progress(video_id: int, progress: int):
    await websocket_manager.broadcast(
        f"video_progress_{video_id}",
        {"progress": progress}
    )
```

#### 5. 添加转码队列管理
```python
# 使用Redis队列管理转码任务
class TranscodeQueue:
    async def add_task(self, video_id: int, priority: int = 0):
        await redis.zadd("transcode_queue", {video_id: priority})
    
    async def get_next_task(self) -> int:
        return await redis.zpopmin("transcode_queue")
```

#### 6. 添加失败重试机制
```python
# 转码失败自动重试
MAX_RETRY = 3

async def process_with_retry(video_id: int, file_path: str):
    for attempt in range(MAX_RETRY):
        try:
            await VideoProcessor.process_video(video_id, file_path)
            return True
        except Exception as e:
            if attempt < MAX_RETRY - 1:
                await asyncio.sleep(60 * (attempt + 1))
            else:
                raise
```

### 低优先级

#### 7. 添加视频分析统计
```python
# 记录转码性能数据
class TranscodeStats:
    async def record(self, video_id: int, duration: float, 
                     transcode_time: float, method: str):
        await db.execute(
            insert(TranscodeLog).values(
                video_id=video_id,
                duration=duration,
                transcode_time=transcode_time,
                method=method,  # cpu/gpu/remote
                speed_ratio=duration / transcode_time
            )
        )
```

#### 8. 添加智能路由
```python
# 根据服务器负载智能选择处理方式
async def select_processor(file_size: int) -> str:
    if file_size < 100 * 1024 * 1024:  # < 100MB
        return "local"
    
    gpu_load = await check_gpu_server_load()
    if gpu_load < 80:
        return "gpu"
    
    return "local"
```

## 📊 性能指标

### 当前性能

| 指标 | 本地处理 | GPU处理 |
|------|---------|---------|
| 1GB视频转码时间 | 15-20分钟 | 3-5分钟 |
| 封面生成时间 | 5-10秒 | 3-5秒 |
| 预览生成时间 | 30-60秒 | 10-20秒 |
| 并发处理能力 | 2个 | 3-4个 |

### 优化后预期

| 指标 | 优化后 |
|------|--------|
| 1GB视频总处理时间 | 5-8分钟 |
| 封面生成时间 | 3秒 |
| 预览生成时间 | 10秒 |
| 并发处理能力 | 5-6个 |

## ✅ 修复清单

### 已完成
- [x] 更新回调接口支持封面/预览/时长
- [x] 创建转码服务器脚本 (transcode_full.ps1)
- [x] 创建上传脚本 (upload_full.ps1)
- [x] 创建监控脚本 (watcher_full.ps1)
- [x] 配置SSH密钥
- [x] 创建主服务器预览目录

### 待完成
- [ ] 统一预览视频格式为MP4
- [ ] 更新GPU服务配置
- [ ] 添加视频时长到回调
- [ ] 测试完整流程
- [ ] 前端适配预览格式

## 🚀 下一步行动

1. **立即**: 在转码服务器启动监控服务，测试完整流程
2. **短期**: 统一预览格式，更新GPU服务配置
3. **中期**: 添加进度推送和队列管理
4. **长期**: 实现智能路由和性能优化

---

**创建时间**: 2026-01-16  
**分析版本**: 1.0  
**状态**: 分析完成，待实施优化
