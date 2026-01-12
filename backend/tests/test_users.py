"""
用户相关测试
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_current_user_without_auth(client: AsyncClient):
    """测试未登录获取当前用户"""
    response = await client.get("/api/v1/users/me")
    
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_update_profile_without_auth(client: AsyncClient):
    """测试未登录更新资料"""
    response = await client.put(
        "/api/v1/users/me",
        json={"nickname": "新昵称"}
    )
    
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_user_profile(client: AsyncClient):
    """测试获取用户公开资料"""
    response = await client.get("/api/v1/users/1/profile")
    
    # 用户可能不存在
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_get_user_videos(client: AsyncClient):
    """测试获取用户视频列表"""
    response = await client.get("/api/v1/users/1/videos")
    
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_follow_user_without_auth(client: AsyncClient):
    """测试未登录关注用户"""
    response = await client.post("/api/v1/users/1/follow")
    
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_followers(client: AsyncClient):
    """测试获取粉丝列表"""
    response = await client.get("/api/v1/users/1/followers")
    
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_get_following(client: AsyncClient):
    """测试获取关注列表"""
    response = await client.get("/api/v1/users/1/following")
    
    assert response.status_code in [200, 404]
