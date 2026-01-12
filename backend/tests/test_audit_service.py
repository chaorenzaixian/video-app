"""
审计服务测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestAuditAction:
    """审计操作类型测试"""
    
    def test_audit_actions_defined(self):
        """测试审计操作类型定义"""
        from app.models.audit_log import AuditAction
        
        # 认证相关
        assert AuditAction.LOGIN == "login"
        assert AuditAction.LOGOUT == "logout"
        assert AuditAction.REGISTER == "register"
        
        # 用户相关
        assert AuditAction.USER_CREATE == "user_create"
        assert AuditAction.USER_DELETE == "user_delete"
        
        # VIP相关
        assert AuditAction.VIP_PURCHASE == "vip_purchase"
        
        # 视频相关
        assert AuditAction.VIDEO_UPLOAD == "video_upload"
        assert AuditAction.VIDEO_DELETE == "video_delete"
        
        # 支付相关
        assert AuditAction.PAYMENT_SUCCESS == "payment_success"
        assert AuditAction.PAYMENT_FAILED == "payment_failed"


class TestAuditService:
    """审计服务测试"""
    
    @pytest.mark.asyncio
    async def test_log_basic(self):
        """测试基本日志记录"""
        from app.services.audit_service import AuditService
        from app.models.audit_log import AuditAction
        
        # Mock数据库会话
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        
        result = await AuditService.log(
            db=mock_db,
            action=AuditAction.LOGIN,
            user_id=1,
            username="testuser",
            ip_address="127.0.0.1"
        )
        
        # 验证add被调用
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_log_login(self):
        """测试登录日志"""
        from app.services.audit_service import AuditService
        
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        
        result = await AuditService.log_login(
            db=mock_db,
            user_id=1,
            username="testuser",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            success=True
        )
        
        mock_db.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_log_payment(self):
        """测试支付日志"""
        from app.services.audit_service import AuditService
        
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        
        result = await AuditService.log_payment(
            db=mock_db,
            user_id=1,
            order_id="ORDER123",
            amount=100,
            payment_type="alipay",
            success=True
        )
        
        mock_db.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_log_vip_purchase(self):
        """测试VIP购买日志"""
        from app.services.audit_service import AuditService
        
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        
        result = await AuditService.log_vip_purchase(
            db=mock_db,
            user_id=1,
            vip_level=2,
            duration_days=30,
            amount=99,
            order_id="VIP123"
        )
        
        mock_db.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_log_with_error(self):
        """测试日志记录失败处理"""
        from app.services.audit_service import AuditService
        from app.models.audit_log import AuditAction
        
        mock_db = AsyncMock()
        mock_db.add = MagicMock(side_effect=Exception("DB Error"))
        mock_db.commit = AsyncMock()
        
        # 应该不抛出异常，返回None
        result = await AuditService.log(
            db=mock_db,
            action=AuditAction.LOGIN,
            user_id=1
        )
        
        assert result is None


class TestAuditLogDecorator:
    """审计日志装饰器测试"""
    
    @pytest.mark.asyncio
    async def test_audit_log_decorator(self):
        """测试审计日志装饰器"""
        from app.services.audit_service import audit_log, AuditService
        from app.models.audit_log import AuditAction
        
        @audit_log(AuditAction.VIDEO_DELETE, "video")
        async def delete_video(video_id: int, db, current_user):
            return {"deleted": video_id}
        
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "admin"
        
        with patch.object(AuditService, 'log', new_callable=AsyncMock) as mock_log:
            result = await delete_video(
                video_id=123,
                db=mock_db,
                current_user=mock_user
            )
            
            assert result == {"deleted": 123}
            mock_log.assert_called_once()
