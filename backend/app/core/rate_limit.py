"""
API 限流模块
防止暴力破解和滥用
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Callable
import time
from collections import defaultdict
import asyncio

from app.core.config import settings


class RateLimiter:
    """简单的内存限流器（生产环境建议使用 Redis）"""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self._lock = asyncio.Lock()
    
    def _parse_limit(self, limit_str: str) -> tuple:
        """解析限流配置，如 '5/minute' -> (5, 60)"""
        parts = limit_str.split('/')
        count = int(parts[0])
        period = parts[1].lower()
        
        period_seconds = {
            'second': 1,
            'minute': 60,
            'hour': 3600,
            'day': 86400
        }
        
        return count, period_seconds.get(period, 60)
    
    async def is_allowed(self, key: str, limit_str: str) -> tuple:
        """
        检查是否允许请求
        返回: (是否允许, 剩余次数, 重置时间)
        """
        if not settings.RATE_LIMIT_ENABLED:
            return True, -1, 0
        
        max_requests, period = self._parse_limit(limit_str)
        now = time.time()
        
        async with self._lock:
            # 清理过期记录
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if now - req_time < period
            ]
            
            current_count = len(self.requests[key])
            
            if current_count >= max_requests:
                # 计算重置时间
                oldest = min(self.requests[key]) if self.requests[key] else now
                reset_time = int(oldest + period - now)
                return False, 0, reset_time
            
            # 记录本次请求
            self.requests[key].append(now)
            remaining = max_requests - current_count - 1
            
            return True, remaining, period


# 全局限流器实例
rate_limiter = RateLimiter()


def get_client_ip(request: Request) -> str:
    """获取客户端真实 IP"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


def rate_limit(limit: str = None):
    """
    限流装饰器
    用法: @rate_limit("5/minute")
    """
    def decorator(func: Callable):
        async def wrapper(request: Request, *args, **kwargs):
            limit_str = limit or settings.RATE_LIMIT_DEFAULT
            client_ip = get_client_ip(request)
            key = f"{client_ip}:{request.url.path}"
            
            allowed, remaining, reset_time = await rate_limiter.is_allowed(key, limit_str)
            
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": f"请求过于频繁，请 {reset_time} 秒后重试",
                        "retry_after": reset_time
                    },
                    headers={
                        "Retry-After": str(reset_time),
                        "X-RateLimit-Remaining": "0"
                    }
                )
            
            response = await func(request, *args, **kwargs)
            return response
        
        # 保留原函数信息
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    return decorator


async def check_rate_limit(request: Request, limit: str = None) -> bool:
    """
    检查限流（用于在路由函数内部调用）
    返回 True 表示允许，抛出异常表示被限流
    """
    from fastapi import HTTPException
    
    limit_str = limit or settings.RATE_LIMIT_DEFAULT
    client_ip = get_client_ip(request)
    key = f"{client_ip}:{request.url.path}"
    
    allowed, remaining, reset_time = await rate_limiter.is_allowed(key, limit_str)
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"请求过于频繁，请 {reset_time} 秒后重试",
            headers={"Retry-After": str(reset_time)}
        )
    
    return True
