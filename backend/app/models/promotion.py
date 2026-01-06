"""
推广系统模型 - 分享送VIP + 代理系统
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum, Numeric, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class AgentLevel(int, enum.Enum):
    """代理等级"""
    NORMAL = 0          # 普通用户
    PROMOTER = 1        # 推广达人 (邀请50人+)
    AGENT = 2           # 普通代理 (业绩1万+)
    SENIOR_AGENT = 3    # 高级代理 (业绩10万+)
    SUPER_AGENT = 4     # 超级代理 (签约)


class CommissionType(str, enum.Enum):
    """佣金类型"""
    DIRECT = "direct"       # 直推佣金
    TEAM = "team"           # 团队佣金
    LEVEL = "level"         # 平级奖励


class CommissionStatus(str, enum.Enum):
    """佣金状态"""
    PENDING = "pending"         # 待结算
    SETTLED = "settled"         # 已结算
    CANCELLED = "cancelled"     # 已取消


class WithdrawStatus(str, enum.Enum):
    """提现状态"""
    PENDING = "pending"         # 待审核
    PROCESSING = "processing"   # 处理中
    SUCCESS = "success"         # 成功
    FAILED = "failed"           # 失败
    REJECTED = "rejected"       # 拒绝


class WithdrawType(str, enum.Enum):
    """提现方式"""
    ALIPAY = "alipay"           # 支付宝
    WECHAT = "wechat"           # 微信
    BANK = "bank"               # 银行卡


class RewardType(str, enum.Enum):
    """奖励类型"""
    INVITE_REGISTER = "invite_register"     # 邀请注册
    INVITE_RECHARGE = "invite_recharge"     # 邀请充值
    MILESTONE = "milestone"                  # 里程碑奖励
    ACTIVITY = "activity"                    # 活动奖励


class RewardContent(str, enum.Enum):
    """奖励内容类型"""
    VIP_DAYS = "vip_days"       # VIP天数
    CASH = "cash"               # 现金
    COUPON = "coupon"           # 优惠券


class UserProfile(Base):
    """用户推广资料表"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # 邀请关系
    invite_code = Column(String(20), unique=True, index=True, nullable=False)  # 邀请码
    inviter_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # 邀请人ID
    
    # 代理信息
    agent_level = Column(Integer, default=0)  # 代理等级
    commission_rate = Column(Numeric(5, 4), default=0)  # 佣金比例 (0.0000 - 0.9999)
    agent_status = Column(String(20), default="inactive")  # inactive/pending/active/frozen
    agent_applied_at = Column(DateTime, nullable=True)  # 申请代理时间
    agent_approved_at = Column(DateTime, nullable=True)  # 审核通过时间
    
    # 统计数据
    total_invites = Column(Integer, default=0)  # 总邀请数
    valid_invites = Column(Integer, default=0)  # 有效邀请数
    total_team_size = Column(Integer, default=0)  # 团队总人数
    total_commission = Column(Numeric(12, 2), default=0)  # 累计佣金
    available_balance = Column(Numeric(12, 2), default=0)  # 可提现余额
    frozen_balance = Column(Numeric(12, 2), default=0)  # 冻结余额
    total_withdrawn = Column(Numeric(12, 2), default=0)  # 累计提现
    
    # 奖励统计
    total_reward_days = Column(Integer, default=0)  # 累计获得VIP天数
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", foreign_keys=[user_id], backref="profile")
    inviter = relationship("User", foreign_keys=[inviter_id])
    
    __table_args__ = (
        Index('idx_user_profile_inviter', 'inviter_id'),
        Index('idx_user_profile_agent_level', 'agent_level'),
    )


class Invitation(Base):
    """邀请记录表"""
    __tablename__ = "invitations"
    
    id = Column(Integer, primary_key=True, index=True)
    inviter_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # 邀请人
    invitee_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # 被邀请人
    invite_code = Column(String(20), nullable=False)  # 使用的邀请码
    
    # 风控信息
    device_fingerprint = Column(String(255), nullable=True)  # 设备指纹
    ip_address = Column(String(50), nullable=True)  # IP地址
    user_agent = Column(Text, nullable=True)  # 浏览器信息
    
    # 状态
    is_valid = Column(Boolean, default=False)  # 是否有效邀请
    invalid_reason = Column(String(100), nullable=True)  # 无效原因
    
    # 奖励状态
    register_rewarded = Column(Boolean, default=False)  # 注册奖励是否已发放
    recharge_rewarded = Column(Boolean, default=False)  # 充值奖励是否已发放
    
    created_at = Column(DateTime, default=datetime.utcnow)
    validated_at = Column(DateTime, nullable=True)  # 验证通过时间
    
    # 关系
    inviter = relationship("User", foreign_keys=[inviter_id])
    invitee = relationship("User", foreign_keys=[invitee_id])
    
    __table_args__ = (
        Index('idx_invitation_inviter', 'inviter_id'),
        Index('idx_invitation_invitee', 'invitee_id'),
        Index('idx_invitation_code', 'invite_code'),
        Index('idx_invitation_device', 'device_fingerprint'),
    )


class Commission(Base):
    """佣金记录表"""
    __tablename__ = "commissions"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # 获得佣金的代理
    from_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # 来源用户
    order_id = Column(Integer, nullable=True)  # 关联订单ID
    
    # 佣金信息
    order_amount = Column(Numeric(12, 2), nullable=False)  # 订单金额
    commission_type = Column(String(20), nullable=False)  # direct/team/level
    commission_rate = Column(Numeric(5, 4), nullable=False)  # 佣金比例
    commission_amount = Column(Numeric(12, 2), nullable=False)  # 佣金金额
    level_diff = Column(Integer, default=1)  # 层级差 (1=直推, 2=二级...)
    
    # 状态
    status = Column(String(20), default="pending")  # pending/settled/cancelled
    
    settled_at = Column(DateTime, nullable=True)  # 结算时间
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    agent = relationship("User", foreign_keys=[agent_id])
    from_user = relationship("User", foreign_keys=[from_user_id])
    
    __table_args__ = (
        Index('idx_commission_agent', 'agent_id'),
        Index('idx_commission_status', 'status'),
        Index('idx_commission_created', 'created_at'),
    )


class Withdrawal(Base):
    """提现记录表"""
    __tablename__ = "withdrawals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 提现信息
    amount = Column(Numeric(12, 2), nullable=False)  # 提现金额
    fee = Column(Numeric(12, 2), default=0)  # 手续费
    actual_amount = Column(Numeric(12, 2), nullable=False)  # 实际到账
    
    # 收款信息
    withdraw_type = Column(String(20), nullable=False)  # alipay/wechat/bank
    account_name = Column(String(50), nullable=True)  # 账户名
    account_number = Column(String(100), nullable=True)  # 账号(加密存储)
    bank_name = Column(String(50), nullable=True)  # 银行名称
    
    # 状态
    status = Column(String(20), default="pending")  # pending/processing/success/failed/rejected
    reject_reason = Column(String(255), nullable=True)  # 拒绝原因
    
    # 处理信息
    operator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # 处理人
    processed_at = Column(DateTime, nullable=True)  # 处理时间
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User", foreign_keys=[user_id])
    operator = relationship("User", foreign_keys=[operator_id])
    
    __table_args__ = (
        Index('idx_withdrawal_user', 'user_id'),
        Index('idx_withdrawal_status', 'status'),
        Index('idx_withdrawal_created', 'created_at'),
    )


class Reward(Base):
    """奖励记录表"""
    __tablename__ = "rewards"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 奖励信息
    reward_type = Column(String(30), nullable=False)  # invite_register/invite_recharge/milestone/activity
    reward_content = Column(String(20), nullable=False)  # vip_days/cash/coupon
    reward_value = Column(Numeric(12, 2), nullable=False)  # 奖励数值（VIP天数或金额）
    reward_desc = Column(String(255), nullable=True)  # 奖励描述
    
    # 来源
    source_type = Column(String(30), nullable=True)  # invitation/milestone/activity
    source_id = Column(Integer, nullable=True)  # 来源ID
    
    # 状态
    claimed = Column(Boolean, default=False)  # 是否已领取
    claimed_at = Column(DateTime, nullable=True)  # 领取时间
    expire_at = Column(DateTime, nullable=True)  # 过期时间
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User", foreign_keys=[user_id])
    
    __table_args__ = (
        Index('idx_reward_user', 'user_id'),
        Index('idx_reward_type', 'reward_type'),
        Index('idx_reward_claimed', 'claimed'),
    )


class AgentRelation(Base):
    """代理层级关系表(闭包表,用于快速查询上下级)"""
    __tablename__ = "agent_relations"
    
    id = Column(Integer, primary_key=True, index=True)
    ancestor_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # 上级ID
    descendant_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # 下级ID
    level_depth = Column(Integer, nullable=False)  # 层级深度 (1=直接下级, 2=二级...)
    path = Column(String(500), nullable=True)  # 完整路径 如: 1/5/23/89
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_relation_ancestor', 'ancestor_id'),
        Index('idx_relation_descendant', 'descendant_id'),
        Index('idx_relation_depth', 'level_depth'),
    )


class InviteMilestone(Base):
    """邀请里程碑配置表"""
    __tablename__ = "invite_milestones"
    
    id = Column(Integer, primary_key=True, index=True)
    invite_count = Column(Integer, nullable=False, unique=True)  # 邀请人数要求
    reward_type = Column(String(20), nullable=False)  # vip_days/cash/agent_upgrade
    reward_value = Column(Numeric(12, 2), nullable=False)  # 奖励值
    reward_desc = Column(String(255), nullable=True)  # 奖励描述
    is_active = Column(Boolean, default=True)  # 是否启用
    
    created_at = Column(DateTime, default=datetime.utcnow)


class PromotionConfig(Base):
    """推广配置表"""
    __tablename__ = "promotion_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(50), unique=True, nullable=False)  # 配置键
    config_value = Column(Text, nullable=False)  # 配置值(JSON)
    config_desc = Column(String(255), nullable=True)  # 配置描述
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

