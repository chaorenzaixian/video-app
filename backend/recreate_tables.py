#!/usr/bin/env python3
"""重新创建PostgreSQL表结构（包含正确的枚举类型）"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, Base
from app.models import *

async def recreate():
    print("正在重新创建表结构...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 表结构创建完成")

if __name__ == "__main__":
    asyncio.run(recreate())
