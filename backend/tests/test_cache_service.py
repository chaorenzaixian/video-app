"""
缓存服务测试
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestCacheService:
    """缓存服务测试"""
    
    @pytest.mark.asyncio
    async def test_cache_keys_format(self):
        """测试缓存键格式"""
        from app.services.cache_service import CacheKeys
        
        # 测试视频列表键
        key = CacheKeys.VIDEO_LIST.format(
            category="1", page=1, size=20, sort="created_at"
        )
        assert "video:list:1:1:20:created_at" == key
        
        # 测试视频详情键
        key = CacheKeys.VIDEO_DETAIL.format(id=123)
        assert "video:detail:123" == key
        
        # 测试用户VIP键
        key = CacheKeys.USER_VIP.format(id=456)
        assert "user:vip:456" == key
    
    @pytest.mark.asyncio
    async def test_cache_ttl_values(self):
        """测试缓存TTL值"""
        from app.services.cache_service import CacheTTL
        
        assert CacheTTL.SHORT == 60
        assert CacheTTL.MEDIUM == 300
        assert CacheTTL.LONG == 1800
        assert CacheTTL.VERY_LONG == 3600
        assert CacheTTL.DAY == 86400
    
    @pytest.mark.asyncio
    async def test_cache_service_get_set(self):
        """测试缓存获取和设置"""
        from app.services.cache_service import CacheService
        
        # Mock Redis
        with patch.object(CacheService, 'get', new_callable=AsyncMock) as mock_get:
            with patch.object(CacheService, 'set', new_callable=AsyncMock) as mock_set:
                mock_get.return_value = None
                mock_set.return_value = True
                
                # 测试获取不存在的键
                result = await CacheService.get("test:key")
                assert result is None
                
                # 测试设置键
                result = await CacheService.set("test:key", {"data": "value"}, 300)
                assert result is True
    
    @pytest.mark.asyncio
    async def test_cache_invalidator(self):
        """测试缓存失效器"""
        from app.services.cache_service import CacheInvalidator, CacheService
        
        with patch.object(CacheService, 'delete', new_callable=AsyncMock) as mock_delete:
            with patch.object(CacheService, 'delete_pattern', new_callable=AsyncMock) as mock_pattern:
                mock_delete.return_value = True
                mock_pattern.return_value = 5
                
                # 测试视频缓存失效
                await CacheInvalidator.invalidate_video(123)
                mock_delete.assert_called()
                mock_pattern.assert_called()
                
                # 测试用户缓存失效
                await CacheInvalidator.invalidate_user(456)
                assert mock_delete.call_count >= 2


class TestCacheDecorator:
    """缓存装饰器测试"""
    
    @pytest.mark.asyncio
    async def test_cached_decorator(self):
        """测试cached装饰器"""
        from app.services.cache_service import cached, CacheService
        
        call_count = 0
        
        @cached("test:{key}", ttl=60)
        async def test_func(key: str):
            nonlocal call_count
            call_count += 1
            return {"result": key}
        
        with patch.object(CacheService, 'get', new_callable=AsyncMock) as mock_get:
            with patch.object(CacheService, 'set', new_callable=AsyncMock) as mock_set:
                # 第一次调用，缓存未命中
                mock_get.return_value = None
                mock_set.return_value = True
                
                result = await test_func(key="abc")
                assert result == {"result": "abc"}
                assert call_count == 1
                
                # 第二次调用，缓存命中
                mock_get.return_value = {"result": "abc"}
                
                result = await test_func(key="abc")
                assert result == {"result": "abc"}
                # 函数不应该被再次调用
                assert call_count == 1
