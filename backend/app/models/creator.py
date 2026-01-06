"""
创作者系统数据模型
"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric, Text, JSON, Float
from sqlalchemy.orm import relationship

from app.core.database import Base


class CreatorApplication(Base):
    """创作者申请表"""
    __tablename__ = "creator_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 申请信息
    real_name = Column(String(50))
    id_card = Column(String(30))                           # 身份证号(加密存储)
    phone = Column(String(20))
    email = Column(String(100))
    introduction = Column(Text)                            # 个人介绍
    expertise = Column(String(255))                        # 擅长领域
    sample_works = Column(JSON)                            # 作品样例URLs
    
    # 审核信息
    status = Column(String(20), default="pending")         # pending/approved/rejected
    reject_reason = Column(Text)
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    reviewed_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", foreign_keys=[user_id], backref="creator_applications")


class Creator(Base):
    """创作者信息表"""
    __tablename__ = "creators"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # 创作者信息
    display_name = Column(String(100))                     # 展示名称
    avatar = Column(String(255))                           # 创作者头像
    cover_image = Column(String(255))                      # 主页封面
    bio = Column(Text)                                     # 个人简介
    tags = Column(String(255))                             # 标签
    
    # 等级认证
    creator_level = Column(Integer, default=1)             # 创作者等级 1-10
    is_verified = Column(Boolean, default=False)           # 是否认证
    verification_type = Column(String(20))                 # personal/company/official
    verification_note = Column(String(100))                # 认证说明
    
    # 统计数据
    total_videos = Column(Integer, default=0)
    total_views = Column(Integer, default=0)
    total_likes = Column(Integer, default=0)
    total_comments = Column(Integer, default=0)
    total_followers = Column(Integer, default=0)
    
    # 收益统计
    total_coins_earned = Column(Integer, default=0)        # 总收益(金币)
    total_tips_received = Column(Integer, default=0)       # 总打赏(金币)
    available_coins = Column(Integer, default=0)           # 可提现金币
    frozen_coins = Column(Integer, default=0)              # 冻结金币
    
    # 分成设置
    platform_share_ratio = Column(Float, default=0.30)     # 平台抽成比例(默认30%)
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)
    ban_reason = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", backref="creator_profile")


class CreatorEarning(Base):
    """创作者收益记录"""
    __tablename__ = "creator_earnings"
    
    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=False)
    
    # 收益类型
    earning_type = Column(String(30), nullable=False)      # video_sale/tip/bonus/referral
    source_type = Column(String(30))                       # video/live/system
    source_id = Column(Integer)                            # 关联ID(视频ID等)
    
    # 金额
    gross_amount = Column(Integer, nullable=False)         # 总金额(金币)
    platform_fee = Column(Integer, default=0)              # 平台费用(金币)
    net_amount = Column(Integer, nullable=False)           # 净收入(金币)
    
    # 来源用户
    from_user_id = Column(Integer, ForeignKey("users.id"))
    
    # 状态
    status = Column(String(20), default="pending")         # pending/settled/withdrawn
    settled_at = Column(DateTime)
    
    description = Column(String(255))
    extra_data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    creator = relationship("Creator", backref="earnings")


class CreatorWithdrawal(Base):
    """创作者提现记录"""
    __tablename__ = "creator_withdrawals"
    
    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=False)
    
    # 提现信息
    coins_amount = Column(Integer, nullable=False)         # 提现金币数
    cash_amount = Column(Numeric(10, 2), nullable=False)   # 折合现金(元)
    exchange_rate = Column(Float, default=0.01)            # 兑换率(1金币=0.01元)
    
    # 收款信息
    payment_method = Column(String(30))                    # alipay/wechat/bank
    payment_account = Column(String(100))                  # 收款账号
    payment_name = Column(String(50))                      # 收款人姓名
    
    # 状态
    status = Column(String(20), default="pending")         # pending/processing/completed/rejected
    reject_reason = Column(Text)
    processed_by = Column(Integer, ForeignKey("users.id"))
    processed_at = Column(DateTime)
    
    # 流水号
    transaction_no = Column(String(100))                   # 平台流水号
    external_no = Column(String(100))                      # 第三方流水号
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = relationship("Creator", backref="withdrawals")


class VideoTip(Base):
    """视频打赏记录"""
    __tablename__ = "video_tips"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=False)
    
    # 打赏信息
    coins_amount = Column(Integer, nullable=False)         # 打赏金币数
    gift_id = Column(Integer, ForeignKey("gifts.id"))      # 礼物ID(可选)
    message = Column(String(200))                          # 打赏留言
    
    # 分成
    platform_fee = Column(Integer, default=0)              # 平台抽成
    creator_income = Column(Integer, default=0)            # 创作者收入
    
    is_anonymous = Column(Boolean, default=False)          # 是否匿名
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    video = relationship("Video", backref="tips")
    user = relationship("User", backref="tips_given")
    creator = relationship("Creator", backref="tips_received")


class Gift(Base):
    """礼物配置表"""
    __tablename__ = "gifts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)              # 礼物名称
    icon = Column(String(255))                             # 礼物图标
    animation_url = Column(String(255))                    # 特效动画URL
    
    coins_price = Column(Integer, nullable=False)          # 金币价格
    
    category = Column(String(30))                          # 分类
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class VideoReview(Base):
    """视频审核表"""
    __tablename__ = "video_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), unique=True, nullable=False)
    
    # 审核状态
    status = Column(String(20), default="pending")         # pending/approved/rejected/revision
    priority = Column(Integer, default=0)                  # 审核优先级
    
    # 审核信息
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    review_note = Column(Text)                             # 审核备注
    reject_reasons = Column(JSON)                          # 拒绝原因列表
    
    # AI审核
    ai_score = Column(Float)                               # AI审核分数
    ai_labels = Column(JSON)                               # AI识别标签
    ai_reviewed = Column(Boolean, default=False)
    
    reviewed_at = Column(DateTime)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    video = relationship("Video", backref="review")


class VideoCollection(Base):
    """视频合集表"""
    __tablename__ = "video_collections"
    
    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=False)
    
    # 基本信息
    title = Column(String(200), nullable=False)
    description = Column(Text)
    cover_image = Column(String(255))
    
    # 统计
    total_videos = Column(Integer, default=0)
    total_duration = Column(Integer, default=0)            # 总时长(秒)
    view_count = Column(Integer, default=0)
    subscribe_count = Column(Integer, default=0)
    
    # 付费设置
    pay_type = Column(String(20), default="free")          # free/coins
    collection_price = Column(Integer, default=0)          # 合集价格
    single_video_price = Column(Integer, default=0)        # 单集价格
    discount_percent = Column(Integer, default=20)         # 合集折扣(%)
    
    # 状态
    is_completed = Column(Boolean, default=False)          # 是否完结
    status = Column(String(20), default="draft")           # draft/published/hidden
    sort_order = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = relationship("Creator", backref="collections")


class CollectionVideo(Base):
    """合集-视频关联表"""
    __tablename__ = "collection_videos"
    
    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(Integer, ForeignKey("video_collections.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    
    episode_number = Column(Integer)                       # 集数
    episode_title = Column(String(200))                    # 单集标题
    sort_order = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    collection = relationship("VideoCollection", backref="videos")
    video = relationship("Video", backref="in_collections")


class UserFollow(Base):
    """用户关注关系表"""
    __tablename__ = "user_follows"
    
    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False)   # 粉丝
    following_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 被关注者
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 唯一约束在数据库层面处理


class TipRanking(Base):
    """打赏排行榜(缓存表)"""
    __tablename__ = "tip_rankings"
    
    id = Column(Integer, primary_key=True, index=True)
    ranking_type = Column(String(20), nullable=False)      # weekly/monthly/total
    period = Column(String(20))                            # 2024-01/2024-W01
    
    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=False)
    total_tips = Column(Integer, default=0)
    tip_count = Column(Integer, default=0)
    rank = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = relationship("Creator")

