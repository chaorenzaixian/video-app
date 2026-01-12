"""添加评论表索引

Revision ID: add_comment_indexes
Revises: init_default_data
Create Date: 2026-01-13

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_comment_indexes'
down_revision = 'init_default_data'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """添加评论表索引以优化查询性能"""
    # 创建索引（如果不存在）
    # 使用 IF NOT EXISTS 避免重复创建错误
    
    # 评论表索引
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_comment_video_created 
        ON comments (video_id, created_at)
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_comment_video_hidden 
        ON comments (video_id, is_hidden)
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_comment_user_created 
        ON comments (user_id, created_at)
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_comment_parent_id 
        ON comments (parent_id)
    """)
    
    # 评论点赞表索引
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_comment_like_comment_user 
        ON comment_likes (comment_id, user_id)
    """)
    
    # 用户表索引
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_created_at 
        ON users (created_at)
    """)


def downgrade() -> None:
    """删除索引"""
    op.execute("DROP INDEX IF EXISTS idx_comment_video_created")
    op.execute("DROP INDEX IF EXISTS idx_comment_video_hidden")
    op.execute("DROP INDEX IF EXISTS idx_comment_user_created")
    op.execute("DROP INDEX IF EXISTS idx_comment_parent_id")
    op.execute("DROP INDEX IF EXISTS idx_comment_like_comment_user")
    op.execute("DROP INDEX IF EXISTS idx_user_created_at")
