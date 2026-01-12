"""
Pytest 配置和 fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# 设置测试环境
import os
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from app.main import app
from app.core.database import Base, get_db


# 测试数据库引擎
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
    future=True
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    创建测试数据库会话
    每个测试函数使用独立的数据库
    """
    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 创建会话
    async with TestSessionLocal() as session:
        yield session
    
    # 清理所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    创建测试客户端
    """
    # 覆盖依赖
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    # 清理覆盖
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """测试用户数据"""
    return {
        "username": "testuser",
        "password": "Test123456",
        "email": "test@example.com",
        "nickname": "测试用户"
    }


@pytest.fixture
def test_video_data():
    """测试视频数据"""
    return {
        "title": "测试视频",
        "description": "这是一个测试视频",
        "duration": 120,
        "cover_url": "/uploads/covers/test.webp",
        "hls_url": "/uploads/videos/test/index.m3u8"
    }


@pytest.fixture
def auth_headers():
    """
    生成认证头
    用于需要登录的测试
    """
    # 这里可以生成一个测试用的JWT token
    # 实际使用时需要根据项目的认证方式调整
    return {"Authorization": "Bearer test_token"}
