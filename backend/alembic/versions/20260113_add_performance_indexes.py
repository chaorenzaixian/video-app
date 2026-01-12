"""添加性能优化索引

Revision ID: 20260113_indexes
Revises: 
Create Date: 2026-01-13

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '20260113_indexes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """添加性能优化索引"""
    
    # 视频表索引
    # 状态+创建时间（首页查询）
    op.create_index(
        'idx_video_status_created',
        'videos',
        ['status', 'created_at'],
        if_not_exists=True
    )
    
    # 状态+是否精选+创建时间（精选视频查询）
    op.create_index(
        'idx_video_status_featured_created',
        'videos',
        ['status', 'is_featured', 'created_at'],
        if_not_exists=True
    )
    
    # 分类+状态（分类页查询）
    op.create_index(
        'idx_video_category_status',
        'videos',
        ['category_id', 'status'],
        if_not_exists=True
    )
    
    # 上传者+状态（用户视频列表）
    op.create_index(
        'idx_video_uploader_status',
        'videos',
        ['uploader_id', 'status'],
        if_not_exists=True
    )
    
    # 评论表索引
    # 视频+隐藏+创建时间（评论列表）
    op.create_index(
        'idx_comment_video_hidden_created',
        'comments',
        ['video_id', 'is_hidden', 'created_at'],
        if_not_exists=True
    )
    
    # 用户+创建时间（用户评论列表）
    op.create_index(
        'idx_comment_user_created',
        'comments',
        ['user_id', 'created_at'],
        if_not_exists=True
    )
    
    # 父评论ID（回复查询）
    op.create_index(
        'idx_comment_parent',
        'comments',
        ['parent_id'],
        if_not_exists=True
    )
    
    # VIP表索引
    # 用户+激活+过期时间（VIP查询）
    op.create_index(
        'idx_user_vip_active_expire',
        'user_vip',
        ['user_id', 'is_active', 'expire_date'],
        if_not_exists=True
    )
    
    # 关注表索引
    # 被关注者+创建时间（粉丝列表）
    op.create_index(
        'idx_follow_following_created',
        'user_follows',
        ['following_id', 'created_at'],
        if_not_exists=True
    )
    
    # 关注者+创建时间（关注列表）
    op.create_index(
        'idx_follow_follower_created',
        'user_follows',
        ['follower_id', 'created_at'],
        if_not_exists=True
    )
    
    # 支付订单表索引
    # 用户+状态+创建时间（订单列表）
    op.create_index(
        'idx_payment_order_user_status',
        'payment_orders',
        ['user_id', 'status', 'created_at'],
        if_not_exists=True
    )
    
    # 订单号（唯一查询）
    op.create_index(
        'idx_payment_order_no',
        'payment_orders',
        ['order_no'],
        unique=True,
        if_not_exists=True
    )
    
    # 通知表索引
    # 用户+已读+创建时间（通知列表）
    op.create_index(
        'idx_notification_user_read_created',
        'notifications',
        ['user_id', 'is_read', 'created_at'],
        if_not_exists=True
    )
    
    # 点赞表索引
    # 视频+用户（检查是否点赞）
    op.create_index(
        'idx_like_video_user',
        'video_likes',
        ['video_id', 'user_id'],
        if_not_exists=True
    )
    
    # 收藏表索引
    # 用户+创建时间（收藏列表）
    op.create_index(
        'idx_favorite_user_created',
        'video_favorites',
        ['user_id', 'created_at'],
        if_not_exists=True
    )
    
    # 视频+用户（检查是否收藏）
    op.create_index(
        'idx_favorite_video_user',
        'video_favorites',
        ['video_id', 'user_id'],
        if_not_exists=True
    )
    
    # 观看历史表索引
    # 用户+观看时间（历史列表）
    op.create_index(
        'idx_history_user_watched',
        'watch_history',
        ['user_id', 'watched_at'],
        if_not_exists=True
    )
    
    print("✅ 性能优化索引创建完成")


def downgrade():
    """删除索引"""
    # 视频表
    op.drop_index('idx_video_status_created', 'videos', if_exists=True)
    op.drop_index('idx_video_status_featured_created', 'videos', if_exists=True)
    op.drop_index('idx_video_category_status', 'videos', if_exists=True)
    op.drop_index('idx_video_uploader_status', 'videos', if_exists=True)
    
    # 评论表
    op.drop_index('idx_comment_video_hidden_created', 'comments', if_exists=True)
    op.drop_index('idx_comment_user_created', 'comments', if_exists=True)
    op.drop_index('idx_comment_parent', 'comments', if_exists=True)
    
    # VIP表
    op.drop_index('idx_user_vip_active_expire', 'user_vip', if_exists=True)
    
    # 关注表
    op.drop_index('idx_follow_following_created', 'user_follows', if_exists=True)
    op.drop_index('idx_follow_follower_created', 'user_follows', if_exists=True)
    
    # 支付订单表
    op.drop_index('idx_payment_order_user_status', 'payment_orders', if_exists=True)
    op.drop_index('idx_payment_order_no', 'payment_orders', if_exists=True)
    
    # 通知表
    op.drop_index('idx_notification_user_read_created', 'notifications', if_exists=True)
    
    # 点赞表
    op.drop_index('idx_like_video_user', 'video_likes', if_exists=True)
    
    # 收藏表
    op.drop_index('idx_favorite_user_created', 'video_favorites', if_exists=True)
    op.drop_index('idx_favorite_video_user', 'video_favorites', if_exists=True)
    
    # 观看历史表
    op.drop_index('idx_history_user_watched', 'watch_history', if_exists=True)
