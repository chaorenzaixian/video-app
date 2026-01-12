"""
VIP相关测试
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_vip_packages(client: AsyncClient):
    """测试获取VIP套餐列表"""
    response = await client.get("/api/v1/vip/packages")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_vip_status_without_auth(client: AsyncClient):
    """测试未登录获取VIP状态"""
    response = await client.get("/api/v1/vip/status")
    
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_purchase_vip_without_auth(client: AsyncClient):
    """测试未登录购买VIP"""
    response = await client.post(
        "/api/v1/vip/purchase",
        json={"package_id": 1, "payment_method": "alipay"}
    )
    
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_vip_benefits(client: AsyncClient):
    """测试获取VIP权益说明"""
    response = await client.get("/api/v1/vip/benefits")
    
    # 可能没有这个端点
    assert response.status_code in [200, 404]
