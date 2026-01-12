"""
通知相关测试
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_notifications_without_auth(client: AsyncClient):
    """测试未登录获取通知列表"""
    response = await client.get("/api/v1/notifications")
    
    # 应该返回401
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_unread_count_without_auth(client: AsyncClient):
    """测试未登录获取未读数量"""
    response = await client.get("/api/v1/notifications/unread-count")
    
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_mark_notification_read_without_auth(client: AsyncClient):
    """测试未登录标记已读"""
    response = await client.put("/api/v1/notifications/1/read")
    
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_mark_all_read_without_auth(client: AsyncClient):
    """测试未登录标记全部已读"""
    response = await client.put("/api/v1/notifications/read-all")
    
    assert response.status_code in [401, 403]
