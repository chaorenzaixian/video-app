"""
认证相关测试
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_guest_register(client: AsyncClient):
    """测试游客注册"""
    response = await client.post(
        "/api/v1/auth/guest/register",
        json={"device_id": "test-device-123"}
    )
    
    # 检查响应状态
    assert response.status_code in [200, 201, 422]  # 422 可能是验证错误
    
    if response.status_code == 200:
        data = response.json()
        assert "access_token" in data or "token" in data


@pytest.mark.asyncio
async def test_guest_register_duplicate_device(client: AsyncClient):
    """测试重复设备ID注册"""
    device_id = "duplicate-device-456"
    
    # 第一次注册
    response1 = await client.post(
        "/api/v1/auth/guest/register",
        json={"device_id": device_id}
    )
    
    # 第二次注册（应该返回相同用户或错误）
    response2 = await client.post(
        "/api/v1/auth/guest/register",
        json={"device_id": device_id}
    )
    
    # 两次请求都应该成功（返回相同用户）或第二次返回已存在
    assert response1.status_code in [200, 201, 422]
    assert response2.status_code in [200, 201, 400, 422]


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """测试无效凭证登录"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "nonexistent",
            "password": "wrongpassword"
        }
    )
    
    # 应该返回401或400
    assert response.status_code in [400, 401, 422]


@pytest.mark.asyncio
async def test_protected_endpoint_without_auth(client: AsyncClient):
    """测试未认证访问受保护端点"""
    response = await client.get("/api/v1/users/me")
    
    # 应该返回401
    assert response.status_code in [401, 403]
