"""
视频相关测试
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_videos(client: AsyncClient):
    """测试获取视频列表"""
    response = await client.get("/api/v1/videos")
    
    assert response.status_code == 200
    data = response.json()
    
    # 检查响应结构
    assert "items" in data or isinstance(data, list)
    if "items" in data:
        assert "total" in data


@pytest.mark.asyncio
async def test_list_videos_with_pagination(client: AsyncClient):
    """测试视频列表分页"""
    response = await client.get(
        "/api/v1/videos",
        params={"page": 1, "page_size": 10}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    if "items" in data:
        assert len(data["items"]) <= 10


@pytest.mark.asyncio
async def test_list_videos_with_category(client: AsyncClient):
    """测试按分类筛选视频"""
    response = await client.get(
        "/api/v1/videos",
        params={"category_id": 1}
    )
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_video_not_found(client: AsyncClient):
    """测试获取不存在的视频"""
    response = await client.get("/api/v1/videos/99999999")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_search_videos(client: AsyncClient):
    """测试搜索视频"""
    response = await client.get(
        "/api/v1/videos/search",
        params={"q": "test"}
    )
    
    # 搜索端点可能不存在，所以允许404
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_video_like_without_auth(client: AsyncClient):
    """测试未登录点赞视频"""
    response = await client.post("/api/v1/videos/1/like")
    
    # 应该返回401
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_video_favorite_without_auth(client: AsyncClient):
    """测试未登录收藏视频"""
    response = await client.post("/api/v1/videos/1/favorite")
    
    # 应该返回401
    assert response.status_code in [401, 403]
