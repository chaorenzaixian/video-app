"""添加性能优化索引

Revision ID: 20260113_perf_idx
Revises: 20260113_soft_delete
Create Date: 2026-01-13

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '20260113_perf_idx'
down_revision = '20260113_soft_delete'
branch_labels = None
depends_on = None


def upgrade():
    """添加性能优化索引"""
    
    # 视频表：状态+创建时间（首页查询优化）
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_video_status_created 
        ON videos (status, created_at DESC)
    """)
    
    # 评论表：视频+隐藏+创建时间（评论列表优化）
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_comment_video_hidden_created 
        ON comments (video_id, is_hidden, created_at DESC)
    """)
    
    # VIP表：用户+激活+过期时间（VIP查询优化）
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_vip_active_expire 
        ON user_vips (user_id, is_active, expire_date)
    """)
    
    # 关注表：被关注者+创建时间（粉丝列表优化）
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_follow_following_created 
        ON user_follows (following_id, created_at DESC)
    """)
    
    # 支付订单表：用户+状态+创建时间（订单列表优化）
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_payment_order_user_status 
        ON payment_orders (user_id, status, created_at DESC)
    """)
    
    # 支付订单表：订单号唯一索引（回调查询优化）
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_payment_order_no 
        ON payment_orders (order_no)
    """)
    
    # 通知表：用户+已读+创建时间（通知列表优化）
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_notification_user_read_created 
        ON user_notifications (user_id, is_read, created_at DESC)
    """)
    
    print("✅ 性能优化索引添加完成")


def downgrade():
    """删除索引"""
    op.execute("DROP INDEX IF EXISTS idx_video_status_created")
    op.execute("DROP INDEX IF EXISTS idx_comment_video_hidden_created")
    op.execute("DROP INDEX IF EXISTS idx_user_vip_active_expire")
    op.execute("DROP INDEX IF EXISTS idx_follow_following_created")
    op.execute("DROP INDEX IF EXISTS idx_payment_order_user_status")
    op.execute("DROP INDEX IF EXISTS idx_payment_order_no")
    op.execute("DROP INDEX IF EXISTS idx_notification_user_read_created")
