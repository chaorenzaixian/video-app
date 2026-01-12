"""
API 限流中间件
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Tuple
import time
import asyncio
from collections import defaultdict

from app.core.config import settings
from app.core.redis import RedisCache


class RateLimitConfig:
    """限流配置"""
    # 默认限流：每分钟60次
    DEFAULT = (60, 60)
    
    # 特定路径限流配置 (次数, 时间窗口秒)
    # 安全敏感接口使用更严格的限制
    PATHS = {
        # 认证相关 - 严格限制防暴力破解
        "/api/v1/auth/login": (3, 60),           # 登录：3次/分钟
        "/api/v1/auth/register": (1, 60),        # 注册：1次/分钟（防批量注册）
        "/api/v1/auth/guest/register": (3, 60),  # 游客注册：3次/分钟
        "/api/v1/auth/reset-password": (2, 300), # 重置密码：2次/5分钟
        "/api/v1/auth/send-code": (1, 60),       # 发送验证码：1次/分钟
        
        # 支付相关 - 防刷单
        "/api/v1/payments": (5, 60),             # 支付：5次/分钟
        "/api/v1/payments/epay/create": (3, 60), # 创建订单：3次/分钟
        "/api/v1/payments/alipay/create": (3, 60),
        "/api/v1/payments/wechat/create": (3, 60),
        
        # 内容创建 - 防刷
        "/api/v1/comments": (10, 60),            # 评论：10次/分钟
        "/api/v1/videos/upload": (3, 300),       # 上传：3次/5分钟
        "/api/v1/posts": (5, 60),                # 发帖：5次/分钟
        
        # 互动操作 - 适度限制
        "/api/v1/videos/like": (30, 60),         # 点赞：30次/分钟
        "/api/v1/users/follow": (20, 60),        # 关注：20次/分钟
    }
    
    # 白名单路径（不限流）
    WHITELIST = [
        "/api/health",
        "/api/docs",
        "/api/openapi.json",
        "/uploads/",
        "/api/v1/payments/epay/notify",   # 支付回调不限流
        "/api/v1/payments/alipay/notify",
        "/api/v1/payments/wechat/notify",
    ]


class InMemoryRateLimiter:
    """内存限流器（Redis不可用时的备用方案）"""
    
    def __init__(self):
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, key: str, limit: int, window: int) -> Tuple[bool, int]:
        """检查是否允许请求"""
        async with self._lock:
            now = time.time()
            # 清理过期记录
            self._requests[key] = [t for t in self._requests[key] if now - t < window]
            
            current_count = len(self._requests[key])
            
            if current_count >= limit:
                # 计算重置时间
                oldest = min(self._requests[key]) if self._requests[key] else now
                retry_after = int(window - (now - oldest))
                return False, max(1, retry_after)
            
            # 记录请求
            self._requests[key].append(now)
            return True, 0


# 全局内存限流器实例
_memory_limiter = InMemoryRateLimiter()


async def check_rate_limit(request: Request) -> None:
    """检查请求是否超过限流"""
    if not settings.RATE_LIMIT_ENABLED:
        return
    
    path = request.url.path
    
    # 检查白名单
    for whitelist_path in RateLimitConfig.WHITELIST:
        if path.startswith(whitelist_path):
            return
    
    # 获取客户端标识（IP + 用户ID）
    client_ip = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    
    # 尝试获取用户ID
    user_id = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        from app.core.security import decode_token
        token = auth_header[7:]
        payload = decode_token(token)
        if payload:
            user_id = payload.get("sub")
    
    # 构建限流键
    identifier = f"{user_id or client_ip}"
    
    # 获取限流配置
    limit, window = RateLimitConfig.DEFAULT
    for config_path, config in RateLimitConfig.PATHS.items():
        if path.startswith(config_path):
            limit, window = config
            break
    
    rate_key = f"rate_limit:{path}:{identifier}"
    
    # 尝试使用 Redis 限流
    try:
        redis = await RedisCache.get_client()
        if redis:
            # 使用 Redis 滑动窗口限流
            current = await redis.incr(rate_key)
            if current == 1:
                await redis.expire(rate_key, window)
            
            if current > limit:
                ttl = await redis.ttl(rate_key)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"请求过于频繁，请 {ttl} 秒后重试",
                    headers={"Retry-After": str(ttl)}
                )
            return
    except HTTPException:
        raise
    except Exception:
        pass
    
    # Redis 不可用，使用内存限流
    allowed, retry_after = await _memory_limiter.is_allowed(rate_key, limit, window)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"请求过于频繁，请 {retry_after} 秒后重试",
            headers={"Retry-After": str(retry_after)}
        )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""
    
    async def dispatch(self, request: Request, call_next):
        await check_rate_limit(request)
        return await call_next(request)
