"""
数据库模型
"""
from app.models.user import User, UserVIP, LoginQRToken, TrustedDevice, DeviceSwitchLog
from app.models.video import Video, VideoCategory, ShortVideoCategory, VideoTag, VideoView
from app.models.comment import Comment, CommentLike
from app.models.payment import Payment, PaymentOrder
from app.models.ad import Advertisement, AdClick, Announcement, OfficialGroup, OfficialGroupType, CustomerService
from app.models.promotion import (
    UserProfile, Invitation, Commission, Withdrawal, 
    Reward, AgentRelation, InviteMilestone, PromotionConfig
)
from app.models.system_config import SystemConfig
from app.models.points import (
    UserPoints, Task, TaskRecord, PointLog, ExchangeItem, ExchangeRecord
)
from app.models.coins import (
    UserCoins, CoinTransaction, RechargePackage, RechargeOrder, 
    VideoPurchase, CollectionPurchase
)
from app.models.creator import (
    CreatorApplication, Creator, CreatorEarning, CreatorWithdrawal,
    VideoTip, Gift, VideoReview, VideoCollection, CollectionVideo,
    UserFollow, TipRanking
)
from app.models.social import (
    PrivateMessage, MessageConversation, VideoDanmaku,
    Playlist, PlaylistVideo, UserNotification, VideoLike, VideoFavorite
)
from app.models.community import (
    Post, PostComment, PostLike, PostCommentLike, Topic, TopicFollow
)
from app.models.coupon import (
    CouponTemplate, UserCoupon, NewUserPackage, NewUserPackageClaim, PromotionalEvent
)
from app.models.referral import (
    ReferralLevel, RechargeCommission, PromoLink, PromoClickLog, ReferralChain
)
from app.models.statistics import (
    UserBehaviorLog, VideoDailyStats, DailyRevenueReport, 
    UserRetentionStats, CreatorDailyStats, PlatformDailyStats
)
from app.models.report import Report, ReportCategory
from app.models.watermark import WatermarkConfig as WatermarkConfigModel
from app.models.feature_flag import FeatureFlag, FeatureRule, ExperimentExposure, ExperimentEvent
from app.models.admin_log import AdminLog
from app.models.content import Banner, Notice, NoticeRead
from app.models.vip import VipCard, VipPrivilege, VipPurchaseRecord
from app.models.chat import ChatSession, ChatMessage, QuickReply

__all__ = [
    "User", "UserVIP", "LoginQRToken", "TrustedDevice", "DeviceSwitchLog",
    "Video", "VideoCategory", "ShortVideoCategory", "VideoTag", "VideoView",
    "Comment", "CommentLike",
    "Payment", "PaymentOrder",
    "Advertisement", "AdClick", "Announcement", "OfficialGroup", "OfficialGroupType",
    "CustomerService",
    # 推广系统
    "UserProfile", "Invitation", "Commission", "Withdrawal",
    "Reward", "AgentRelation", "InviteMilestone", "PromotionConfig",
    # 系统配置
    "SystemConfig",
    # 积分任务系统
    "UserPoints", "Task", "TaskRecord", "PointLog", "ExchangeItem", "ExchangeRecord",
    # 金币系统
    "UserCoins", "CoinTransaction", "RechargePackage", "RechargeOrder",
    "VideoPurchase", "CollectionPurchase",
    # 创作者系统
    "CreatorApplication", "Creator", "CreatorEarning", "CreatorWithdrawal",
    "VideoTip", "Gift", "VideoReview", "VideoCollection", "CollectionVideo",
    "UserFollow", "TipRanking",
    # 举报系统
    "Report", "ReportCategory",
    # 管理后台
    "AdminLog", "Banner", "Notice", "NoticeRead",
    # 社交功能
    "VideoLike", "VideoFavorite",
    # 社区功能
    "Post", "PostComment", "PostLike", "PostCommentLike", "Topic", "TopicFollow",
    # 客服聊天
    "ChatSession", "ChatMessage", "QuickReply"
]