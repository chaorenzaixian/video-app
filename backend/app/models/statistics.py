"""
数据统计系统数据模型
"""
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Numeric, Text, JSON, Float
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserBehaviorLog(Base):
    """用户行为日志"""
    __tablename__ = "user_behavior_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    action_type = Column(String(50), nullable=False)       # view/click/search/purchase/like/share
    target_type = Column(String(50))                       # video/collection/page/user
    target_id = Column(Integer)
    
    extra_data = Column(JSON)                              # 额外数据
    
    device_type = Column(String(20))                       # mobile/tablet/desktop
    platform = Column(String(20))                          # ios/android/web
    ip_address = Column(String(50))
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class VideoDailyStats(Base):
    """视频每日统计"""
    __tablename__ = "video_daily_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    stat_date = Column(Date, nullable=False)
    
    view_count = Column(Integer, default=0)
    unique_viewers = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    purchase_count = Column(Integer, default=0)
    
    revenue_coins = Column(Integer, default=0)             # 收益(金币)
    tip_coins = Column(Integer, default=0)                 # 打赏(金币)
    
    avg_watch_duration = Column(Integer, default=0)        # 平均观看时长(秒)
    completion_rate = Column(Float)                        # 完播率
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 复合唯一约束
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class DailyRevenueReport(Base):
    """每日收入报表"""
    __tablename__ = "daily_revenue_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_date = Column(Date, unique=True, nullable=False)
    
    # 充值数据
    total_recharge = Column(Numeric(12, 2), default=0)     # 总充值金额
    recharge_orders = Column(Integer, default=0)           # 充值订单数
    recharge_users = Column(Integer, default=0)            # 充值用户数
    
    # 消费数据
    total_video_sales = Column(Integer, default=0)         # 视频销售(金币)
    total_tips = Column(Integer, default=0)                # 打赏(金币)
    total_vip_sales = Column(Numeric(12, 2), default=0)    # VIP销售金额
    
    # 提现数据
    total_withdrawals = Column(Numeric(12, 2), default=0)  # 总提现金额
    
    # 用户数据
    new_users = Column(Integer, default=0)                 # 新增用户
    active_users = Column(Integer, default=0)              # 活跃用户
    paying_users = Column(Integer, default=0)              # 付费用户
    
    # 关键指标
    arpu = Column(Numeric(10, 2))                          # 人均收入
    arppu = Column(Numeric(10, 2))                         # 付费用户人均收入
    pay_rate = Column(Float)                               # 付费率
    
    created_at = Column(DateTime, default=datetime.utcnow)


class UserRetentionStats(Base):
    """用户留存统计"""
    __tablename__ = "user_retention_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    cohort_date = Column(Date, nullable=False)             # 用户注册日期(群组)
    day_n = Column(Integer, nullable=False)                # 第N天
    
    total_users = Column(Integer, default=0)               # 该群组总用户数
    retained_users = Column(Integer, default=0)            # 留存用户数
    retention_rate = Column(Float)                         # 留存率
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class CreatorDailyStats(Base):
    """创作者每日统计"""
    __tablename__ = "creator_daily_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=False)
    stat_date = Column(Date, nullable=False)
    
    view_count = Column(Integer, default=0)
    new_followers = Column(Integer, default=0)
    video_sales = Column(Integer, default=0)
    tips_received = Column(Integer, default=0)
    
    total_income = Column(Integer, default=0)              # 总收入(金币)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class PlatformDailyStats(Base):
    """平台每日统计汇总"""
    __tablename__ = "platform_daily_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    stat_date = Column(Date, unique=True, nullable=False)
    
    # 用户指标
    total_users = Column(Integer, default=0)
    new_users = Column(Integer, default=0)
    dau = Column(Integer, default=0)                       # 日活跃用户
    mau = Column(Integer, default=0)                       # 月活跃用户
    
    # 内容指标
    total_videos = Column(Integer, default=0)
    new_videos = Column(Integer, default=0)
    total_views = Column(Integer, default=0)
    total_comments = Column(Integer, default=0)
    
    # 收入指标
    total_recharge = Column(Numeric(12, 2), default=0)
    total_consumption = Column(Integer, default=0)         # 消费(金币)
    platform_revenue = Column(Numeric(12, 2), default=0)   # 平台收入
    
    # 创作者指标
    total_creators = Column(Integer, default=0)
    active_creators = Column(Integer, default=0)
    creator_payouts = Column(Integer, default=0)           # 创作者提现(金币)
    
    created_at = Column(DateTime, default=datetime.utcnow)

