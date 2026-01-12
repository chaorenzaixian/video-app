# -*- coding: utf-8 -*-
"""
Alembic 迁移环境配置
支持异步数据库和自动生成迁移
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 添加项目路径
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入配置和模型
from app.core.config import settings
from app.core.database import Base

# 导入所有模型以便 Alembic 能检测到它们
from app.models.user import User, UserVIP, UserRole
from app.models.video import Video, VideoCategory, VideoTag
from app.models.comment import Comment, CommentLike
from app.models.payment import PaymentOrder
from app.models.ad import Advertisement
from app.models.community import (
    Post, PostComment, PostLike, PostCollect, PostCommentLike,
    Gallery, GalleryCategory, GalleryComment, GalleryLike, GalleryCollect, GalleryCommentLike,
    Novel, NovelChapter, NovelComment, NovelLike, NovelCollect, NovelCommentLike,
    Topic, TopicFollow
)

# Alembic Config 对象
config = context.config

# 设置数据库 URL（从环境配置获取）
# 将 asyncpg 替换为 psycopg2 用于同步迁移
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql+asyncpg"):
    db_url = db_url.replace("postgresql+asyncpg", "postgresql")
elif db_url.startswith("sqlite+aiosqlite"):
    db_url = db_url.replace("sqlite+aiosqlite", "sqlite")

config.set_main_option("sqlalchemy.url", db_url)

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置目标元数据（用于自动生成迁移）
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式运行迁移（只生成 SQL，不执行）"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """执行迁移"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """异步模式运行迁移"""
    from sqlalchemy.ext.asyncio import create_async_engine
    
    connectable = create_async_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在线模式运行迁移"""
    # 检查是否使用异步驱动
    if settings.DATABASE_URL.startswith(("postgresql+asyncpg", "sqlite+aiosqlite")):
        asyncio.run(run_async_migrations())
    else:
        from sqlalchemy import engine_from_config
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
