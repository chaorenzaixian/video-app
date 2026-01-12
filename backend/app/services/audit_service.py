"""
审计日志服务
提供审计日志记录功能
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from functools import wraps

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request

from app.models.audit_log import AuditLog, AuditAction

logger = logging.getLogger(__name__)


class AuditService:
    """审计日志服务"""
    
    @staticmethod
    async def log(
        db: AsyncSession,
        action: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        details: Optional[Dict] = None,
        old_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> Optional[AuditLog]:
        """
        记录审计日志
        
        Args:
            db: 数据库会话
            action: 操作类型（使用 AuditAction 常量）
            user_id: 操作用户ID
            username: 操作用户名
            resource_type: 资源类型（如 video, user, comment）
            resource_id: 资源ID
            details: 操作详情
            old_value: 修改前的值
            new_value: 修改后的值
            ip_address: IP地址
            user_agent: User-Agent
            request_method: 请求方法
            request_path: 请求路径
            status: 操作状态（success/failed）
            error_message: 错误信息
        """
        try:
            audit_log = AuditLog(
                user_id=user_id,
                username=username,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                old_value=old_value,
                new_value=new_value,
                ip_address=ip_address,
                user_agent=user_agent,
                request_method=request_method,
                request_path=request_path,
                status=status,
                error_message=error_message,
                created_at=datetime.utcnow()
            )
            
            db.add(audit_log)
            await db.commit()
            
            logger.info(
                f"Audit: {action} by user {user_id} on {resource_type}:{resource_id} - {status}"
            )
            
            return audit_log
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            return None
    
    @staticmethod
    async def log_from_request(
        db: AsyncSession,
        request: Request,
        action: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        details: Optional[Dict] = None,
        old_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> Optional[AuditLog]:
        """
        从请求对象记录审计日志
        自动提取IP、User-Agent等信息
        """
        # 获取真实IP（考虑代理）
        ip_address = request.headers.get("X-Forwarded-For")
        if ip_address:
            ip_address = ip_address.split(",")[0].strip()
        else:
            ip_address = request.client.host if request.client else None
        
        user_agent = request.headers.get("User-Agent", "")[:500]
        
        return await AuditService.log(
            db=db,
            action=action,
            user_id=user_id,
            username=username,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request.method,
            request_path=str(request.url.path),
            status=status,
            error_message=error_message
        )
    
    @staticmethod
    async def log_login(
        db: AsyncSession,
        user_id: int,
        username: str,
        ip_address: str,
        user_agent: str,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> Optional[AuditLog]:
        """记录登录日志"""
        return await AuditService.log(
            db=db,
            action=AuditAction.LOGIN,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            status="success" if success else "failed",
            error_message=error_message
        )
    
    @staticmethod
    async def log_logout(
        db: AsyncSession,
        user_id: int,
        username: str,
        ip_address: Optional[str] = None
    ) -> Optional[AuditLog]:
        """记录登出日志"""
        return await AuditService.log(
            db=db,
            action=AuditAction.LOGOUT,
            user_id=user_id,
            username=username,
            ip_address=ip_address
        )
    
    @staticmethod
    async def log_payment(
        db: AsyncSession,
        user_id: int,
        order_id: str,
        amount: int,
        payment_type: str,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> Optional[AuditLog]:
        """记录支付日志"""
        action = AuditAction.PAYMENT_SUCCESS if success else AuditAction.PAYMENT_FAILED
        return await AuditService.log(
            db=db,
            action=action,
            user_id=user_id,
            resource_type="payment",
            details={
                "order_id": order_id,
                "amount": amount,
                "payment_type": payment_type
            },
            status="success" if success else "failed",
            error_message=error_message
        )
    
    @staticmethod
    async def log_vip_purchase(
        db: AsyncSession,
        user_id: int,
        vip_level: int,
        duration_days: int,
        amount: int,
        order_id: str
    ) -> Optional[AuditLog]:
        """记录VIP购买日志"""
        return await AuditService.log(
            db=db,
            action=AuditAction.VIP_PURCHASE,
            user_id=user_id,
            resource_type="vip",
            details={
                "vip_level": vip_level,
                "duration_days": duration_days,
                "amount": amount,
                "order_id": order_id
            }
        )
    
    @staticmethod
    async def log_video_action(
        db: AsyncSession,
        action: str,
        user_id: int,
        video_id: int,
        video_title: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> Optional[AuditLog]:
        """记录视频操作日志"""
        return await AuditService.log(
            db=db,
            action=action,
            user_id=user_id,
            resource_type="video",
            resource_id=video_id,
            details={
                "title": video_title,
                **(details or {})
            }
        )
    
    @staticmethod
    async def log_admin_action(
        db: AsyncSession,
        user_id: int,
        username: str,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        old_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
        details: Optional[Dict] = None
    ) -> Optional[AuditLog]:
        """记录管理员操作日志"""
        return await AuditService.log(
            db=db,
            action=action,
            user_id=user_id,
            username=username,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value,
            details=details
        )


def audit_log(action: str, resource_type: Optional[str] = None):
    """
    审计日志装饰器
    
    用法:
    @audit_log(AuditAction.VIDEO_DELETE, "video")
    async def delete_video(video_id: int, db: AsyncSession, current_user: User):
        ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 尝试从参数中获取db和current_user
            db = kwargs.get('db')
            current_user = kwargs.get('current_user')
            request = kwargs.get('request')
            
            result = None
            error = None
            
            try:
                result = await func(*args, **kwargs)
                status = "success"
            except Exception as e:
                error = str(e)
                status = "failed"
                raise
            finally:
                # 记录审计日志
                if db:
                    user_id = getattr(current_user, 'id', None) if current_user else None
                    username = getattr(current_user, 'username', None) if current_user else None
                    
                    # 尝试获取资源ID
                    resource_id = kwargs.get('video_id') or kwargs.get('user_id') or kwargs.get('id')
                    
                    await AuditService.log(
                        db=db,
                        action=action,
                        user_id=user_id,
                        username=username,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        status=status,
                        error_message=error
                    )
            
            return result
        return wrapper
    return decorator
