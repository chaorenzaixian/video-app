"""
支付服务测试
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock

from app.services.payment_service import (
    OrderStatus,
    OrderStateMachine,
    PaymentService,
    PaymentResult
)


class TestOrderStatus:
    """订单状态测试"""
    
    def test_status_values(self):
        """测试状态值"""
        assert OrderStatus.PENDING.value == "pending"
        assert OrderStatus.PAID.value == "paid"
        assert OrderStatus.FAILED.value == "failed"
        assert OrderStatus.EXPIRED.value == "expired"
        assert OrderStatus.REFUNDED.value == "refunded"
        assert OrderStatus.CANCELLED.value == "cancelled"


class TestOrderStateMachine:
    """订单状态机测试"""
    
    def test_can_transition_pending_to_paid(self):
        """测试待支付->已支付转换"""
        assert OrderStateMachine.can_transition(
            OrderStatus.PENDING, 
            OrderStatus.PAID
        ) is True
    
    def test_can_transition_pending_to_failed(self):
        """测试待支付->失败转换"""
        assert OrderStateMachine.can_transition(
            OrderStatus.PENDING, 
            OrderStatus.FAILED
        ) is True
    
    def test_can_transition_pending_to_expired(self):
        """测试待支付->过期转换"""
        assert OrderStateMachine.can_transition(
            OrderStatus.PENDING, 
            OrderStatus.EXPIRED
        ) is True
    
    def test_cannot_transition_paid_to_pending(self):
        """测试已支付不能转回待支付"""
        assert OrderStateMachine.can_transition(
            OrderStatus.PAID, 
            OrderStatus.PENDING
        ) is False
    
    def test_can_transition_paid_to_refunded(self):
        """测试已支付->已退款转换"""
        assert OrderStateMachine.can_transition(
            OrderStatus.PAID, 
            OrderStatus.REFUNDED
        ) is True
    
    def test_cannot_transition_expired(self):
        """测试过期订单不能转换"""
        assert OrderStateMachine.can_transition(
            OrderStatus.EXPIRED, 
            OrderStatus.PAID
        ) is False
    
    def test_can_transition_failed_to_pending(self):
        """测试失败->待支付（重试）"""
        assert OrderStateMachine.can_transition(
            OrderStatus.FAILED, 
            OrderStatus.PENDING
        ) is True
    
    def test_transition_success(self):
        """测试状态转换成功"""
        order = MagicMock()
        order.status = OrderStatus.PENDING.value
        order.id = "test_order_1"
        
        result = OrderStateMachine.transition(order, OrderStatus.PAID)
        
        assert result is True
        assert order.status == OrderStatus.PAID.value
    
    def test_transition_failure(self):
        """测试状态转换失败"""
        order = MagicMock()
        order.status = OrderStatus.EXPIRED.value
        order.id = "test_order_2"
        
        result = OrderStateMachine.transition(order, OrderStatus.PAID)
        
        assert result is False
        assert order.status == OrderStatus.EXPIRED.value
    
    def test_get_allowed_transitions(self):
        """测试获取允许的转换"""
        allowed = OrderStateMachine.get_allowed_transitions(OrderStatus.PENDING)
        
        assert OrderStatus.PAID in allowed
        assert OrderStatus.FAILED in allowed
        assert OrderStatus.EXPIRED in allowed
        assert OrderStatus.CANCELLED in allowed


class TestPaymentService:
    """支付服务测试"""
    
    def test_generate_order_id(self):
        """测试生成订单号"""
        service = PaymentService()
        
        order_id1 = service.generate_order_id()
        order_id2 = service.generate_order_id()
        
        # 订单号应该唯一
        assert order_id1 != order_id2
        # 订单号应该以PAY开头
        assert order_id1.startswith("PAY")
        assert order_id2.startswith("PAY")
    
    def test_generate_order_id_with_prefix(self):
        """测试自定义前缀生成订单号"""
        service = PaymentService()
        
        order_id = service.generate_order_id(prefix="VIP")
        
        assert order_id.startswith("VIP")
    
    def test_is_order_expired_true(self):
        """测试订单已过期"""
        service = PaymentService()
        
        # 31分钟前创建的订单
        created_at = datetime.utcnow() - timedelta(minutes=31)
        
        assert service.is_order_expired(created_at) is True
    
    def test_is_order_expired_false(self):
        """测试订单未过期"""
        service = PaymentService()
        
        # 10分钟前创建的订单
        created_at = datetime.utcnow() - timedelta(minutes=10)
        
        assert service.is_order_expired(created_at) is False
    
    def test_is_order_expired_none(self):
        """测试空创建时间"""
        service = PaymentService()
        
        assert service.is_order_expired(None) is True


class TestPaymentResult:
    """支付结果测试"""
    
    def test_success_result(self):
        """测试成功结果"""
        result = PaymentResult(
            success=True,
            order_id="test_order",
            payment_url="https://pay.example.com/order/123"
        )
        
        assert result.success is True
        assert result.order_id == "test_order"
        assert result.payment_url is not None
        assert result.error_message is None
    
    def test_failure_result(self):
        """测试失败结果"""
        result = PaymentResult(
            success=False,
            order_id="test_order",
            error_message="支付配置不完整"
        )
        
        assert result.success is False
        assert result.error_message == "支付配置不完整"
    
    def test_qr_code_result(self):
        """测试二维码支付结果"""
        result = PaymentResult(
            success=True,
            order_id="test_order",
            qr_code="weixin://wxpay/bizpayurl?pr=xxx"
        )
        
        assert result.success is True
        assert result.qr_code is not None
        assert result.payment_url is None
