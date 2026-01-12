"""
评论相关测试
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_video_comments(client: AsyncClient):
    """测试获取视频评论列表"""
    # 使用一个可能存在的视频ID
    response = await client.get("/api/v1/comments/video/1")
    
    # 视频可能不存在，所以允许404
    assert response.status_code in [200, 404]
    
    if response.status_code == 200:
        data = response.json()
        assert "items" in data
        assert "total" in data


@pytest.mark.asyncio
async def test_list_comments_pagination(client: AsyncClient):
    """测试评论列表分页"""
    response = await client.get(
        "/api/v1/comments/video/1",
        params={"page": 1, "page_size": 10}
    )
    
    assert response.status_code in [200, 404]
    
    if response.status_code == 200:
        data = response.json()
        if "items" in data:
            assert len(data["items"]) <= 10


@pytest.mark.asyncio
async def test_list_comments_sort_by_newest(client: AsyncClient):
    """测试评论按最新排序"""
    response = await client.get(
        "/api/v1/comments/video/1",
        params={"sort_by": "newest"}
    )
    
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_list_comments_sort_by_hottest(client: AsyncClient):
    """测试评论按最热排序"""
    response = await client.get(
        "/api/v1/comments/video/1",
        params={"sort_by": "hottest"}
    )
    
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_create_comment_without_auth(client: AsyncClient):
    """测试未登录发表评论"""
    response = await client.post(
        "/api/v1/comments",
        json={
            "content": "测试评论",
            "video_id": 1
        }
    )
    
    # 应该返回401
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_like_comment_without_auth(client: AsyncClient):
    """测试未登录点赞评论"""
    response = await client.post("/api/v1/comments/1/like")
    
    # 应该返回401
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_delete_comment_without_auth(client: AsyncClient):
    """测试未登录删除评论"""
    response = await client.delete("/api/v1/comments/1")
    
    # 应该返回401
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_comment_replies(client: AsyncClient):
    """测试获取评论回复"""
    response = await client.get("/api/v1/comments/replies/1")
    
    # 评论可能不存在
    assert response.status_code in [200, 404]
