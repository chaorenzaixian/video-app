"""add soft delete columns to key tables

Revision ID: 20260113_soft_delete
Revises: 20260113_audit
Create Date: 2026-01-13

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '20260113_soft_delete'
down_revision = '20260113_audit'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """为关键表添加软删除字段"""
    
    # 视频表添加软删除字段
    op.execute("""
        ALTER TABLE videos 
        ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE;
    """)
    op.execute("""
        ALTER TABLE videos 
        ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;
    """)
    op.execute("""
        ALTER TABLE videos 
        ADD COLUMN IF NOT EXISTS deleted_by INTEGER;
    """)
    
    # 创建索引
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_videos_is_deleted 
        ON videos (is_deleted);
    """)
    
    # 用户表添加软删除字段
    op.execute("""
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE;
    """)
    op.execute("""
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;
    """)
    op.execute("""
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS deleted_by INTEGER;
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_is_deleted 
        ON users (is_deleted);
    """)
    
    # 社区帖子表添加软删除字段（如果表存在）
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'community_posts') THEN
                ALTER TABLE community_posts 
                ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE;
                ALTER TABLE community_posts 
                ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;
                ALTER TABLE community_posts 
                ADD COLUMN IF NOT EXISTS deleted_by INTEGER;
                CREATE INDEX IF NOT EXISTS idx_community_posts_is_deleted 
                ON community_posts (is_deleted);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """移除软删除字段"""
    # 删除索引
    op.execute("DROP INDEX IF EXISTS idx_videos_is_deleted")
    op.execute("DROP INDEX IF EXISTS idx_users_is_deleted")
    op.execute("DROP INDEX IF EXISTS idx_community_posts_is_deleted")
    
    # 删除列
    op.execute("ALTER TABLE videos DROP COLUMN IF EXISTS is_deleted")
    op.execute("ALTER TABLE videos DROP COLUMN IF EXISTS deleted_at")
    op.execute("ALTER TABLE videos DROP COLUMN IF EXISTS deleted_by")
    
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS is_deleted")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS deleted_at")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS deleted_by")
    
    # 社区帖子表（如果存在）
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'community_posts') THEN
                ALTER TABLE community_posts DROP COLUMN IF EXISTS is_deleted;
                ALTER TABLE community_posts DROP COLUMN IF EXISTS deleted_at;
                ALTER TABLE community_posts DROP COLUMN IF EXISTS deleted_by;
            END IF;
        END $$;
    """)
