"""
审计日志模型
记录系统关键操作
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Index
from app.core.database import Base


class AuditLog(Base):
    """审计日志表"""
    __tablename__ = "audit_logs"
    
    __table_args__ = (
        Index('idx_audit_user_id', 'user_id'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_created_at', 'created_at'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 操作者信息
    user_id = Column(Integer, nullable=True, comment="操作用户ID，系统操作为空")
    username = Column(String(100), nullable=True, comment="操作用户名")
    
    # 操作信息
    action = Column(String(50), nullable=False, comment="操作类型")
    resource_type = Column(String(50), nullable=True, comment="资源类型")
    resource_id = Column(Integer, nullable=True, comment="资源ID")
    
    # 请求信息
    ip_address = Column(String(50), nullable=True, comment="IP地址")
    user_agent = Column(String(500), nullable=True, comment="User-Agent")
    request_method = Column(String(10), nullable=True, comment="请求方法")
    request_path = Column(String(500), nullable=True, comment="请求路径")
    
    # 详细信息
    details = Column(JSON, nullable=True, comment="操作详情")
    old_value = Column(JSON, nullable=True, comment="修改前的值")
    new_value = Column(JSON, nullable=True, comment="修改后的值")
    
    # 结果
    status = Column(String(20), default="success", comment="操作状态: success/failed")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")


class AuditAction:
    """审计操作类型常量"""
    # 认证相关
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    PASSWORD_CHANGE = "password_change"
    
    # 用户相关
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_BAN = "user_ban"
    USER_UNBAN = "user_unban"
    
    # VIP相关
    VIP_PURCHASE = "vip_purchase"
    VIP_UPGRADE = "vip_upgrade"
    VIP_EXPIRE = "vip_expire"
    
    # 视频相关
    VIDEO_UPLOAD = "video_upload"
    VIDEO_UPDATE = "video_update"
    VIDEO_DELETE = "video_delete"
    VIDEO_PUBLISH = "video_publish"
    VIDEO_UNPUBLISH = "video_unpublish"
    
    # 评论相关
    COMMENT_CREATE = "comment_create"
    COMMENT_DELETE = "comment_delete"
    COMMENT_PIN = "comment_pin"
    
    # 支付相关
    PAYMENT_CREATE = "payment_create"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    REFUND = "refund"
    
    # 金币相关
    COINS_PURCHASE = "coins_purchase"
    COINS_CONSUME = "coins_consume"
    COINS_REWARD = "coins_reward"
    
    # 提现相关
    WITHDRAW_REQUEST = "withdraw_request"
    WITHDRAW_APPROVE = "withdraw_approve"
    WITHDRAW_REJECT = "withdraw_reject"
    
    # 管理操作
    ADMIN_CONFIG_UPDATE = "admin_config_update"
    ADMIN_CATEGORY_UPDATE = "admin_category_update"
    ADMIN_BANNER_UPDATE = "admin_banner_update"
