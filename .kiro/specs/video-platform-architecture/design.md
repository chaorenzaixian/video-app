# Design Document: 视频平台架构优化

## Overview

本设计文档描述视频平台的最佳架构方案，基于现有系统分析和优化需求，提供一个高效、可扩展、安全的视频处理和分发系统。

### 核心设计原则

1. **分离关注点**: 转码服务器专注于视频处理，主服务器专注于业务逻辑
2. **减少网络传输**: 转码服务器本地完成所有处理后一次性上传
3. **异步处理**: 耗时操作使用任务队列异步执行
4. **缓存优先**: 热点数据优先从缓存读取
5. **安全第一**: 所有接口都有身份验证和限流保护

## Architecture

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              用户层 (User Layer)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Web 前端    │  │  移动端 App  │  │  管理后台    │  │  第三方接入  │    │
│  │  (Vue.js)    │  │  (Flutter)   │  │  (Vue.js)    │  │  (API)       │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           网关层 (Gateway Layer)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Nginx 反向代理                                │  │
│  │  • SSL/TLS 终止          • 静态文件服务      • 负载均衡              │  │
│  │  • 请求限流              • Gzip 压缩         • 缓存控制              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          应用层 (Application Layer)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    主服务器 (38.47.218.137)                         │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │    │
│  │  │  FastAPI     │  │  Celery      │  │  Redis       │              │    │
│  │  │  后端服务    │  │  任务队列    │  │  缓存/会话   │              │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │    │
│  │  │  PostgreSQL  │  │  文件存储    │  │  监控服务    │              │    │
│  │  │  数据库      │  │  /uploads    │  │  Prometheus  │              │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
┌───────────────────────────────────┐  ┌───────────────────────────────────┐
│     转码服务器 (198.176.60.121)    │  │         CDN 分发层                 │
├───────────────────────────────────┤  ├───────────────────────────────────┤
│  ┌─────────────────────────────┐  │  │  ┌─────────────────────────────┐  │
│  │  Windows Server + GPU       │  │  │  │  Cloudflare / 阿里云 CDN   │  │
│  │  • NVIDIA RTX GPU           │  │  │  │  • 全球节点加速             │  │
│  │  • FFmpeg + NVENC           │  │  │  │  • 边缘缓存                 │  │
│  │  • PowerShell 脚本          │  │  │  │  • DDoS 防护                │  │
│  └─────────────────────────────┘  │  │  └─────────────────────────────┘  │
│  ┌─────────────────────────────┐  │  └───────────────────────────────────┘
│  │  处理流程:                   │  │
│  │  1. 接收视频文件             │  │
│  │  2. GPU 加速转码             │  │
│  │  3. 生成封面 (WebP)          │  │
│  │  4. 生成预览 (MP4)           │  │
│  │  5. 上传到主服务器           │  │
│  │  6. 回调通知完成             │  │
│  └─────────────────────────────┘  │
└───────────────────────────────────┘
```


### 视频处理流程图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           视频处理完整流程                                    │
└─────────────────────────────────────────────────────────────────────────────┘

用户上传视频
      │
      ▼
┌─────────────┐
│  接收文件   │
│  验证格式   │
│  保存原始   │
└─────────────┘
      │
      ▼
┌─────────────┐     ┌─────────────────────────────────────────────────────┐
│  文件大小   │     │                    转码服务器处理                     │
│  > 500MB?   │────▶│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
└─────────────┘ Yes │  │ 下载    │→ │ GPU转码 │→ │ 生成    │→ │ 生成    │ │
      │ No          │  │ 视频    │  │ NVENC   │  │ 封面    │  │ 预览    │ │
      ▼             │  └─────────┘  └─────────┘  └─────────┘  └─────────┘ │
┌─────────────┐     │                      │                               │
│  本地处理   │     │                      ▼                               │
│  CPU/QSV    │     │  ┌─────────────────────────────────────────────────┐ │
└─────────────┘     │  │  SCP 上传到主服务器 (50MB/s)                     │ │
      │             │  │  • 转码后视频 → /uploads/videos/                 │ │
      │             │  │  • 封面图片   → /uploads/thumbnails/             │ │
      │             │  │  • 预览视频   → /uploads/previews/               │ │
      │             │  └─────────────────────────────────────────────────┘ │
      │             │                      │                               │
      │             │                      ▼                               │
      │             │  ┌─────────────────────────────────────────────────┐ │
      │             │  │  HTTP POST 回调                                  │ │
      │             │  │  /api/v1/admin/transcode-callback               │ │
      │             │  │  X-Transcode-Key: vYTWoms4FKOqySca1jCLtNHRVz3BAI6U │
      │             │  └─────────────────────────────────────────────────┘ │
      │             └─────────────────────────────────────────────────────┘
      │                                    │
      ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              更新数据库                                      │
│  • cover_url = /uploads/thumbnails/{video_id}.webp                          │
│  • preview_url = /uploads/previews/{video_id}_preview.mp4                   │
│  • hls_url = /uploads/hls/{video_id}/master.m3u8                            │
│  • status = PUBLISHED                                                        │
│  • published_at = NOW()                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────┐
│  视频发布   │
│  用户可见   │
└─────────────┘
```

## Components and Interfaces

### 1. 主服务器组件

#### 1.1 FastAPI 后端服务

```python
# 核心模块结构
backend/
├── app/
│   ├── api/                    # API 路由
│   │   ├── videos.py           # 视频上传/列表/详情
│   │   ├── transcode_callback.py  # 转码回调
│   │   ├── auth.py             # 认证授权
│   │   └── admin_*.py          # 管理后台
│   ├── core/                   # 核心配置
│   │   ├── config.py           # 配置管理
│   │   ├── database.py         # 数据库连接
│   │   ├── redis.py            # Redis 连接
│   │   ├── security.py         # 安全工具
│   │   └── rate_limiter.py     # 限流器
│   ├── models/                 # 数据模型
│   │   ├── video.py            # 视频模型
│   │   ├── user.py             # 用户模型
│   │   └── payment.py          # 支付模型
│   ├── services/               # 业务服务
│   │   ├── video_processor.py  # 视频处理
│   │   ├── cache_service.py    # 缓存服务
│   │   ├── payment_service.py  # 支付服务
│   │   └── audit_service.py    # 审计服务
│   └── tasks/                  # Celery 任务
│       ├── video_tasks.py      # 视频处理任务
│       ├── notification_tasks.py  # 通知任务
│       └── cleanup_tasks.py    # 清理任务
```

#### 1.2 转码回调接口

```python
# backend/app/api/transcode_callback.py

class TranscodeCallbackRequest(BaseModel):
    """转码回调请求模型"""
    video_id: int
    status: str  # success / failed
    thumbnail_url: Optional[str] = None  # 封面 URL
    preview_url: Optional[str] = None    # 预览 URL
    hls_url: Optional[str] = None        # HLS URL
    duration: Optional[float] = None     # 视频时长
    error_message: Optional[str] = None  # 错误信息

@router.post("/transcode-callback")
async def transcode_callback(
    request: TranscodeCallbackRequest,
    x_transcode_key: str = Header(None, alias="X-Transcode-Key")
):
    """
    转码完成回调接口
    
    安全验证:
    - 验证 X-Transcode-Key 请求头
    
    处理逻辑:
    - 成功: 更新 cover_url, preview_url, hls_url, duration, status
    - 失败: 更新 status 为 FAILED, 记录错误信息
    """
    pass
```


### 2. 转码服务器组件

#### 2.1 目录结构

```
D:\VideoTranscode\
├── downloads\          # 待处理视频
├── processing\         # 处理中视频
├── completed\          # 处理完成
├── logs\               # 日志文件
└── scripts\
    ├── transcode.ps1   # 转码脚本
    ├── upload.ps1      # 上传脚本
    └── watcher.ps1     # 监控脚本
```

#### 2.2 转码脚本接口

```powershell
# scripts/transcode_full.ps1

function Process-Video {
    param(
        [string]$InputFile,
        [int]$VideoId
    )
    
    # 1. GPU 加速转码 (NVENC)
    $transcodedFile = Transcode-WithNVENC -Input $InputFile
    
    # 2. 生成封面 (WebP, 640px, 85% quality)
    $coverFile = Generate-Cover -Input $transcodedFile -Position 0.3
    
    # 3. 生成预览 (MP4, 720p, 10秒, 无音频)
    $previewFile = Generate-Preview -Input $transcodedFile -Duration 10
    
    # 4. 上传到主服务器
    Upload-ToMainServer -Video $transcodedFile -Cover $coverFile -Preview $previewFile
    
    # 5. 回调通知
    Send-Callback -VideoId $VideoId -Status "success"
    
    # 6. 清理本地文件
    Remove-TempFiles -Files @($InputFile, $transcodedFile, $coverFile, $previewFile)
}
```

### 3. 缓存服务组件

```python
# backend/app/services/cache_service.py

class CacheService:
    """缓存服务 - 统一管理 Redis 缓存"""
    
    # 缓存键模式
    KEYS = {
        "user_vip": "user:vip:{user_id}",           # TTL: 5分钟
        "video_list": "video:list:{category}:{page}", # TTL: 5分钟
        "video_detail": "video:detail:{video_id}",   # TTL: 10分钟
        "hot_tags": "tags:hot",                      # TTL: 30分钟
        "system_config": "config:{key}",             # TTL: 1小时
    }
    
    @staticmethod
    async def get_or_set(key: str, factory: Callable, ttl: int = 300):
        """获取缓存，不存在则调用 factory 生成并缓存"""
        cached = await redis.get(key)
        if cached:
            return json.loads(cached)
        
        value = await factory()
        await redis.setex(key, ttl, json.dumps(value))
        return value
    
    @staticmethod
    async def invalidate_pattern(pattern: str):
        """批量失效匹配的缓存键"""
        cursor = 0
        while True:
            cursor, keys = await redis.scan(cursor, match=pattern, count=100)
            if keys:
                await redis.delete(*keys)
            if cursor == 0:
                break
```

### 4. 限流器组件

```python
# backend/app/core/rate_limiter.py

class RateLimiter:
    """API 限流器 - 基于 Redis 的滑动窗口限流"""
    
    # 限流配置
    LIMITS = {
        "/api/v1/auth/login": (3, 60),       # 3次/分钟
        "/api/v1/auth/register": (1, 60),    # 1次/分钟
        "/api/v1/payments": (5, 60),         # 5次/分钟
        "default": (60, 60),                 # 60次/分钟
    }
    
    @staticmethod
    async def check_rate_limit(key: str, limit: int, window: int) -> bool:
        """检查是否超过限流阈值"""
        current = await redis.incr(key)
        if current == 1:
            await redis.expire(key, window)
        return current <= limit
```

## Data Models

### 视频状态机

```
┌─────────────────────────────────────────────────────────────────┐
│                        视频状态转换图                            │
└─────────────────────────────────────────────────────────────────┘

                    ┌─────────────┐
                    │   PENDING   │  ← 初始状态（上传完成）
                    └─────────────┘
                          │
                          ▼
                    ┌─────────────┐
                    │ PROCESSING  │  ← 处理中
                    └─────────────┘
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
      ┌─────────────┐           ┌─────────────┐
      │  PUBLISHED  │           │   FAILED    │
      │  (已发布)   │           │  (处理失败) │
      └─────────────┘           └─────────────┘
            │                         │
            ▼                         ▼
      ┌─────────────┐           ┌─────────────┐
      │   HIDDEN    │           │   PENDING   │  ← 可重试
      │  (已隐藏)   │           └─────────────┘
      └─────────────┘
            │
            ▼
      ┌─────────────┐
      │   DELETED   │
      │  (已删除)   │
      └─────────────┘
```

### 核心数据模型

```python
# backend/app/models/video.py

class VideoStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PUBLISHED = "published"
    FAILED = "failed"
    HIDDEN = "hidden"
    DELETED = "deleted"

class VideoQuality(str, Enum):
    SD = "sd"      # 480p
    HD = "hd"      # 720p
    FHD = "fhd"    # 1080p
    UHD = "uhd"    # 4K

class Video(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # 文件路径
    original_url = Column(String(500))      # 原始文件
    hls_url = Column(String(500))           # HLS 播放地址
    cover_url = Column(String(500))         # 封面图片
    preview_url = Column(String(500))       # 预览视频
    
    # 视频信息
    duration = Column(Float, default=0)     # 时长（秒）
    quality = Column(Enum(VideoQuality))    # 清晰度
    status = Column(Enum(VideoStatus), default=VideoStatus.PENDING)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime)
    
    # 索引
    __table_args__ = (
        Index('idx_video_status_created', 'status', 'created_at'),
        Index('idx_video_category_status', 'category_id', 'status'),
    )
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: 视频上传验证

*For any* 视频文件上传请求，如果文件格式有效且大小在限制内，则上传成功后数据库中应存在对应的视频记录，且状态为 PENDING。

**Validates: Requirements 1.1, 1.3, 1.4**

### Property 2: 视频处理路由

*For any* 上传完成的视频，如果文件大小 > 500MB 且 GPU 转码可用，则视频应被推送到转码服务器处理；否则应在本地处理。

**Validates: Requirements 2.2, 2.3**

### Property 3: 视频状态转换

*For any* 视频处理流程，状态转换必须遵循：PENDING → PROCESSING → (PUBLISHED | FAILED)，不允许跳过中间状态。

**Validates: Requirements 2.1, 2.4, 2.5, 2.6**

### Property 4: 封面生成规范

*For any* 处理完成的视频，如果没有自定义封面，则应生成 WebP 格式封面，宽度为 640px，且数据库 cover_url 字段应被更新。

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

### Property 5: 预览生成规范

*For any* 处理完成的视频，应生成预览视频，时长不超过 10 秒，格式为 MP4，分辨率为 720p，无音频，且数据库 preview_url 字段应被更新。

**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

### Property 6: 转码服务器完整流程

*For any* 发送到转码服务器的视频，处理完成后应一次性上传视频、封面、预览三个文件，并调用回调接口通知主服务器。

**Validates: Requirements 5.1, 5.2, 5.3, 5.4**

### Property 7: 回调接口安全

*For any* 转码回调请求，如果 X-Transcode-Key 无效，则应返回 403 错误；如果视频 ID 不存在，则应返回 404 错误。

**Validates: Requirements 6.4, 6.5, 10.1**

### Property 8: 回调数据更新

*For any* 成功的转码回调，数据库中对应视频的 cover_url、preview_url、hls_url、duration 字段应被更新，状态应变为 PUBLISHED。

**Validates: Requirements 6.1, 6.2**

### Property 9: 多清晰度转码

*For any* 源视频，根据其分辨率应生成对应数量的清晰度版本：≥1080p 生成 3 个版本，≥720p 生成 2 个版本，<720p 生成 1 个版本。

**Validates: Requirements 7.1, 7.2, 7.3, 7.4**

### Property 10: 文件清理

*For any* 转码完成并上传成功的视频，转码服务器上的本地文件应被删除；*For any* 被删除的视频，主服务器上的关联文件应被同步删除。

**Validates: Requirements 8.1, 8.2**

### Property 11: 支付幂等性

*For any* 支付回调请求，如果订单已处理，则应直接返回成功而不重复处理；多次相同回调应产生相同结果。

**Validates: Requirements 11.1, 11.2, 11.3**

### Property 12: 缓存一致性

*For any* 数据更新操作，相关缓存应被主动失效；*For any* 缓存查询，如果缓存存在则应返回缓存数据，否则应查询数据库并缓存结果。

**Validates: Requirements 13.1, 13.2, 13.3, 13.4**

### Property 13: 限流保护

*For any* API 请求，如果超过限流阈值，则应返回 429 状态码；登录接口限制 3 次/分钟，注册接口限制 1 次/分钟，支付接口限制 5 次/分钟。

**Validates: Requirements 14.1, 14.2, 14.3, 14.4**

### Property 14: 异步任务重试

*For any* 失败的异步任务，应自动重试最多 3 次；重试间隔应递增（指数退避）。

**Validates: Requirements 15.3**

## Error Handling

### 错误处理策略

| 错误类型 | 处理方式 | 重试策略 |
|---------|---------|---------|
| 网络超时 | 记录日志，重试 | 最多 3 次，指数退避 |
| 转码失败 | 更新状态为 FAILED，通知管理员 | 可手动重试 |
| 上传失败 | 记录日志，重试 | 最多 3 次，间隔 30 秒 |
| 回调失败 | 记录日志，重试 | 最多 5 次，间隔 60 秒 |
| 磁盘空间不足 | 发送告警，暂停处理 | 清理后自动恢复 |
| 数据库连接失败 | 使用连接池重连 | 自动重连 |
| Redis 连接失败 | 降级到数据库查询 | 自动重连 |

### 错误码定义

```python
class ErrorCode(str, Enum):
    # 通用错误 (1xxx)
    INTERNAL_ERROR = "1000"
    INVALID_REQUEST = "1001"
    UNAUTHORIZED = "1002"
    FORBIDDEN = "1003"
    NOT_FOUND = "1004"
    RATE_LIMITED = "1005"
    
    # 视频错误 (2xxx)
    VIDEO_NOT_FOUND = "2001"
    VIDEO_FORMAT_INVALID = "2002"
    VIDEO_SIZE_EXCEEDED = "2003"
    VIDEO_PROCESSING_FAILED = "2004"
    
    # 支付错误 (3xxx)
    PAYMENT_FAILED = "3001"
    PAYMENT_AMOUNT_MISMATCH = "3002"
    ORDER_NOT_FOUND = "3003"
    ORDER_ALREADY_PROCESSED = "3004"
```

## Testing Strategy

### 测试框架

- **单元测试**: pytest + pytest-asyncio
- **属性测试**: hypothesis
- **集成测试**: pytest + httpx
- **性能测试**: locust

### 测试覆盖要求

| 模块 | 单元测试覆盖率 | 属性测试 |
|------|--------------|---------|
| 视频处理 | ≥ 80% | 5 个属性 |
| 支付服务 | ≥ 90% | 3 个属性 |
| 缓存服务 | ≥ 80% | 2 个属性 |
| 限流器 | ≥ 90% | 2 个属性 |
| 回调接口 | ≥ 90% | 2 个属性 |

### 属性测试示例

```python
# tests/test_video_processor_properties.py
from hypothesis import given, strategies as st

@given(
    file_size=st.integers(min_value=1, max_value=10*1024*1024*1024),
    gpu_available=st.booleans()
)
def test_video_routing_property(file_size, gpu_available):
    """
    Property 2: 视频处理路由
    For any 视频文件，根据大小和 GPU 可用性正确路由
    """
    threshold = 500 * 1024 * 1024  # 500MB
    
    result = determine_processor(file_size, gpu_available)
    
    if file_size > threshold and gpu_available:
        assert result == "gpu"
    else:
        assert result == "local"
```


## 转码监控系统问题分析

### 发现的问题

#### 问题 1: 预览视频格式不一致 ⚠️ 需要修复

**位置**: 
- `scripts/transcode_full.ps1` 第 130-180 行
- `scripts/upload_full.ps1` 第 100-110 行

**问题描述**:
- 转码脚本生成 `.webm` 格式预览视频
- 上传脚本回调时发送的 URL 后缀不正确
- 主服务器本地处理生成的也是 `.webm` 格式

**影响**: 前端播放器可能无法正确识别预览视频格式

**建议修复**: 统一使用 WebM 格式（已一致），确保回调 URL 正确

```powershell
# upload_full.ps1 修复
$previewFileName = if ($PreviewFile) { Split-Path $PreviewFile -Leaf } else { "" }
# 确保 URL 反映实际文件格式
$previewUrl = if ($uploadResults.preview) { "/uploads/previews/$previewFileName" } else { "" }
```

#### 问题 2: 短视频目录可能不存在 ⚠️ 需要确认

**位置**: `scripts/upload_full.ps1` 第 25-35 行

**问题描述**:
```powershell
if ($VideoType -eq "short") {
    $videoUploadPath = "/www/wwwroot/video-app/backend/uploads/shorts/"
    # ...
}
```

**建议**: 在主服务器上确认目录存在：
```bash
mkdir -p /www/wwwroot/video-app/backend/uploads/shorts/{thumbnails,previews}
chmod 755 /www/wwwroot/video-app/backend/uploads/shorts
```

#### 问题 3: GPU 服务配置过时 ⚠️ 已知问题

**位置**: `backend/app/services/gpu_transcode_service.py` 第 15-17 行

**问题描述**:
```python
GPU_SERVER_HOST = os.getenv("GPU_SERVER_HOST", "149.36.0.246")  # 旧 IP
GPU_SERVER_USER = os.getenv("GPU_SERVER_USER", "ubuntu")        # 旧用户
```

**实际配置**:
- 转码服务器 IP: `198.176.60.121`
- 用户: `Administrator`
- 系统: Windows

**建议**: 更新环境变量或禁用旧的 GPU 服务（当前使用的是独立的 PowerShell 脚本方案）

### 监控检查清单

```bash
# 在转码服务器 (198.176.60.121) 执行

# 1. 检查监控服务是否运行
Get-Process | Where-Object { $_.ProcessName -like "*powershell*" }

# 2. 查看最新日志
Get-Content D:\VideoTranscode\logs\watcher_$(Get-Date -Format 'yyyyMMdd').log -Tail 50

# 3. 检查待处理视频
Get-ChildItem D:\VideoTranscode\downloads\long -Filter "*.mp4"
Get-ChildItem D:\VideoTranscode\downloads\short -Filter "*.mp4"

# 4. 检查处理中视频
Get-ChildItem D:\VideoTranscode\processing -Filter "*.mp4"

# 5. 测试 SSH 连接
ssh -i C:\server_key root@38.47.218.137 "echo 'SSH OK'"

# 6. 测试回调接口
$body = @{
    video_id = 1
    status = "success"
    thumbnail_url = "/uploads/thumbnails/test.webp"
    preview_url = "/uploads/previews/test_preview.webm"
    hls_url = "/uploads/videos/test.mp4"
    duration = 60.0
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://38.47.218.137:8000/api/v1/admin/transcode-callback" `
    -Method POST `
    -Headers @{ "X-Transcode-Key" = "vYTWoms4FKOqySca1jCLtNHRVz3BAI6U"; "Content-Type" = "application/json" } `
    -Body $body
```

### 在主服务器检查

```bash
# 在主服务器 (38.47.218.137) 执行

# 1. 检查后端服务状态
systemctl status video-app-backend
# 或
ps aux | grep python | grep run.py

# 2. 检查上传目录权限
ls -la /www/wwwroot/video-app/backend/uploads/

# 3. 查看最近上传的文件
ls -lt /www/wwwroot/video-app/backend/uploads/videos/ | head -10
ls -lt /www/wwwroot/video-app/backend/uploads/thumbnails/ | head -10
ls -lt /www/wwwroot/video-app/backend/uploads/previews/ | head -10

# 4. 查看后端日志
tail -f /www/wwwroot/video-app/backend/logs/app.log | grep -i transcode

# 5. 检查数据库中最近的视频状态
# 进入 Python 环境
cd /www/wwwroot/video-app/backend
source venv/bin/activate
python -c "
from app.core.database import SessionLocal
from app.models.video import Video
from sqlalchemy import select, desc

with SessionLocal() as db:
    videos = db.execute(
        select(Video).order_by(desc(Video.created_at)).limit(5)
    ).scalars().all()
    for v in videos:
        print(f'ID: {v.id}, Status: {v.status}, Title: {v.title[:30]}')
"
```
