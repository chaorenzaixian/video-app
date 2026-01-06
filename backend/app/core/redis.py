"""
Redis 连接管理 - 带容错处理和内存备用缓存
"""
import redis.asyncio as redis
from app.core.config import settings
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import asyncio

logger = logging.getLogger(__name__)

# Redis 连接池
redis_pool = None
redis_available = True  # Redis可用性标志

# 内存缓存（Redis不可用时的备用方案）
_memory_cache: Dict[str, Dict[str, Any]] = {}
_cache_lock = asyncio.Lock()


async def _cleanup_expired_memory_cache():
    """清理过期的内存缓存"""
    now = datetime.utcnow()
    expired_keys = [
        key for key, data in _memory_cache.items()
        if data.get('expire_at') and data['expire_at'] < now
    ]
    for key in expired_keys:
        del _memory_cache[key]


async def get_redis():
    """获取Redis连接"""
    global redis_pool, redis_available
    
    if not redis_available:
        return None
        
    if redis_pool is None:
        try:
            redis_pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2,  # 连接超时2秒
                socket_timeout=2  # 操作超时2秒
            )
        except Exception as e:
            logger.warning(f"Redis连接池创建失败: {e}")
            redis_available = False
            return None
    
    try:
        r = redis.Redis(connection_pool=redis_pool)
        # 测试连接
        await r.ping()
        return r
    except Exception as e:
        logger.warning(f"Redis连接失败: {e}")
        redis_available = False
        return None


async def close_redis():
    """关闭Redis连接"""
    global redis_pool, redis_available
    if redis_pool:
        try:
            await redis_pool.disconnect()
        except:
            pass
        redis_pool = None
    redis_available = True  # 重置标志，允许下次重试


class RedisCache:
    """Redis缓存工具类 - 带容错处理，Redis不可用时使用内存缓存"""
    
    @staticmethod
    async def get(key: str) -> Optional[str]:
        """获取缓存"""
        try:
            r = await get_redis()
            if r is not None:
                return await r.get(key)
        except Exception as e:
            logger.debug(f"Redis get失败: {e}")
        
        # Redis不可用，使用内存缓存
        async with _cache_lock:
            await _cleanup_expired_memory_cache()
            data = _memory_cache.get(key)
            if data:
                if data.get('expire_at') and data['expire_at'] < datetime.utcnow():
                    del _memory_cache[key]
                    return None
                return data.get('value')
        return None
    
    @staticmethod
    async def set(key: str, value: str, expire: int = 3600) -> bool:
        """设置缓存"""
        try:
            r = await get_redis()
            if r is not None:
                await r.set(key, value, ex=expire)
                return True
        except Exception as e:
            logger.debug(f"Redis set失败: {e}")
        
        # Redis不可用，使用内存缓存
        async with _cache_lock:
            expire_at = datetime.utcnow() + timedelta(seconds=expire) if expire else None
            _memory_cache[key] = {
                'value': value,
                'expire_at': expire_at
            }
            print(f"[MemoryCache] 存储: {key} = {value}, 过期时间: {expire}秒")
        return True
    
    @staticmethod
    async def delete(key: str) -> bool:
        """删除缓存"""
        try:
            r = await get_redis()
            if r is not None:
                await r.delete(key)
                return True
        except Exception as e:
            logger.debug(f"Redis delete失败: {e}")
        
        # Redis不可用，从内存缓存删除
        async with _cache_lock:
            if key in _memory_cache:
                del _memory_cache[key]
        return True
    
    @staticmethod
    async def incr(key: str) -> int:
        """自增"""
        try:
            r = await get_redis()
            if r is not None:
                return await r.incr(key)
        except Exception as e:
            logger.debug(f"Redis incr失败: {e}")
        
        # Redis不可用，使用内存缓存
        async with _cache_lock:
            data = _memory_cache.get(key, {'value': '0'})
            new_value = int(data.get('value', 0)) + 1
            _memory_cache[key] = {'value': str(new_value), 'expire_at': data.get('expire_at')}
            return new_value
    
    @staticmethod
    async def expire(key: str, seconds: int) -> bool:
        """设置过期时间"""
        try:
            r = await get_redis()
            if r is not None:
                await r.expire(key, seconds)
                return True
        except Exception as e:
            logger.debug(f"Redis expire失败: {e}")
        
        # Redis不可用，更新内存缓存过期时间
        async with _cache_lock:
            if key in _memory_cache:
                _memory_cache[key]['expire_at'] = datetime.utcnow() + timedelta(seconds=seconds)
        return True