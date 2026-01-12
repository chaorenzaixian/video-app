"""
JWT令牌黑名单管理
用于实现令牌撤销功能（登出、踢出设备等）
"""
from typing import Optional
from app.core.redis import RedisCache


class TokenBlacklist:
    """令牌黑名单管理器"""
    
    PREFIX = "token_blacklist:"
    
    @staticmethod
    async def add(token: str, ttl: int) -> bool:
        """
        将令牌加入黑名单
        
        Args:
            token: JWT令牌
            ttl: 过期时间（秒），应设置为令牌剩余有效期
        
        Returns:
            是否成功
        """
        try:
            return await RedisCache.set(f"{TokenBlacklist.PREFIX}{token}", "1", ttl)
        except Exception:
            # Redis不可用时，降级处理（不阻塞登出操作）
            return False
    
    @staticmethod
    async def is_blacklisted(token: str) -> bool:
        """
        检查令牌是否在黑名单中
        
        Args:
            token: JWT令牌
        
        Returns:
            是否在黑名单中
        """
        try:
            result = await RedisCache.get(f"{TokenBlacklist.PREFIX}{token}")
            return result is not None
        except Exception:
            # Redis不可用时，默认不在黑名单（保证服务可用性）
            return False
    
    @staticmethod
    async def add_user_tokens(user_id: int, ttl: int = 86400) -> bool:
        """
        将用户的所有令牌加入黑名单（用于强制登出所有设备）
        
        Args:
            user_id: 用户ID
            ttl: 过期时间（秒）
        
        Returns:
            是否成功
        """
        try:
            # 使用用户ID作为黑名单键，所有该用户的令牌都会被拒绝
            return await RedisCache.set(f"{TokenBlacklist.PREFIX}user:{user_id}", "1", ttl)
        except Exception:
            return False
    
    @staticmethod
    async def is_user_blacklisted(user_id: int) -> bool:
        """
        检查用户是否被全局黑名单
        
        Args:
            user_id: 用户ID
        
        Returns:
            是否被黑名单
        """
        try:
            result = await RedisCache.get(f"{TokenBlacklist.PREFIX}user:{user_id}")
            return result is not None
        except Exception:
            return False
    
    @staticmethod
    async def remove_user_blacklist(user_id: int) -> bool:
        """
        移除用户的全局黑名单
        
        Args:
            user_id: 用户ID
        
        Returns:
            是否成功
        """
        try:
            return await RedisCache.delete(f"{TokenBlacklist.PREFIX}user:{user_id}")
        except Exception:
            return False
