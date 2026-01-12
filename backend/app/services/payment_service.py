"""
支付服务 - 支付宝/微信/Stripe 统一接口
包含订单状态机和幂等性处理
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import hashlib
import json
import uuid
import hmac
import base64
import logging
from urllib.parse import urlencode, quote_plus

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


# ========== 订单状态机 ==========

class OrderStatus(str, Enum):
    """订单状态"""
    PENDING = "pending"      # 待支付
    PAID = "paid"            # 已支付
    FAILED = "failed"        # 支付失败
    EXPIRED = "expired"      # 已过期
    REFUNDED = "refunded"    # 已退款
    CANCELLED = "cancelled"  # 已取消


class OrderStateMachine:
    """订单状态机 - 管理订单状态转换"""
    
    # 允许的状态转换
    TRANSITIONS = {
        OrderStatus.PENDING: [
            OrderStatus.PAID, 
            OrderStatus.FAILED, 
            OrderStatus.EXPIRED,
            OrderStatus.CANCELLED
        ],
        OrderStatus.PAID: [OrderStatus.REFUNDED],
        OrderStatus.FAILED: [OrderStatus.PENDING],  # 允许重试
        OrderStatus.EXPIRED: [],
        OrderStatus.REFUNDED: [],
        OrderStatus.CANCELLED: [],
    }
    
    @classmethod
    def can_transition(cls, from_status: OrderStatus, to_status: OrderStatus) -> bool:
        """检查是否可以进行状态转换"""
        if isinstance(from_status, str):
            from_status = OrderStatus(from_status)
        if isinstance(to_status, str):
            to_status = OrderStatus(to_status)
        return to_status in cls.TRANSITIONS.get(from_status, [])
    
    @classmethod
    def transition(cls, order, to_status: OrderStatus) -> bool:
        """
        执行状态转换
        返回是否成功转换
        """
        if isinstance(to_status, str):
            to_status = OrderStatus(to_status)
        
        current_status = order.status
        if isinstance(current_status, str):
            current_status = OrderStatus(current_status)
        
        if not cls.can_transition(current_status, to_status):
            logger.warning(
                f"Invalid state transition: {current_status} -> {to_status} "
                f"for order {order.id}"
            )
            return False
        
        order.status = to_status.value
        order.updated_at = datetime.utcnow()
        
        # 记录状态变更历史
        if hasattr(order, 'status_history'):
            if order.status_history is None:
                order.status_history = []
            order.status_history.append({
                'from': current_status.value,
                'to': to_status.value,
                'at': datetime.utcnow().isoformat()
            })
        
        logger.info(f"Order {order.id} status changed: {current_status} -> {to_status}")
        return True
    
    @classmethod
    def get_allowed_transitions(cls, status: OrderStatus) -> List[OrderStatus]:
        """获取允许的下一状态列表"""
        if isinstance(status, str):
            status = OrderStatus(status)
        return cls.TRANSITIONS.get(status, [])


class PaymentResult:
    """支付结果"""
    def __init__(
        self,
        success: bool,
        order_id: str,
        payment_url: str = None,
        qr_code: str = None,
        error_message: str = None,
        raw_response: Dict = None,
        idempotency_key: str = None
    ):
        self.success = success
        self.order_id = order_id
        self.payment_url = payment_url
        self.qr_code = qr_code
        self.error_message = error_message
        self.raw_response = raw_response
        self.idempotency_key = idempotency_key


class PaymentProvider(ABC):
    """支付提供商基类"""
    
    @abstractmethod
    async def create_order(
        self,
        order_id: str,
        amount: int,  # 金额（分）
        subject: str,
        description: str = "",
        **kwargs
    ) -> PaymentResult:
        """创建支付订单"""
        pass
    
    @abstractmethod
    async def verify_callback(self, data: Dict) -> tuple:
        """验证回调签名，返回 (是否有效, 订单号, 金额)"""
        pass
    
    @abstractmethod
    async def query_order(self, order_id: str) -> Dict:
        """查询订单状态"""
        pass


class AlipayProvider(PaymentProvider):
    """支付宝支付"""
    
    GATEWAY_URL = "https://openapi.alipay.com/gateway.do"
    SANDBOX_URL = "https://openapi-sandbox.dl.alipaydev.com/gateway.do"
    
    def __init__(self):
        self.app_id = settings.ALIPAY_APP_ID
        self.private_key = settings.ALIPAY_PRIVATE_KEY
        self.public_key = settings.ALIPAY_PUBLIC_KEY
        self.notify_url = settings.ALIPAY_NOTIFY_URL
        self.return_url = settings.ALIPAY_RETURN_URL
        self.sandbox = settings.ALIPAY_SANDBOX
        
        self.gateway = self.SANDBOX_URL if self.sandbox else self.GATEWAY_URL
    
    def _sign(self, params: Dict) -> str:
        """RSA2 签名"""
        try:
            from Crypto.PublicKey import RSA
            from Crypto.Signature import PKCS1_v1_5
            from Crypto.Hash import SHA256
        except ImportError:
            raise ImportError("请安装 pycryptodome: pip install pycryptodome")
        
        sorted_params = sorted(params.items())
        sign_str = "&".join(f"{k}={v}" for k, v in sorted_params if v)
        
        key = RSA.import_key(self.private_key)
        signer = PKCS1_v1_5.new(key)
        digest = SHA256.new(sign_str.encode('utf-8'))
        signature = base64.b64encode(signer.sign(digest)).decode('utf-8')
        
        return signature
    
    def _verify_sign(self, params: Dict, sign: str) -> bool:
        """验证签名"""
        try:
            from Crypto.PublicKey import RSA
            from Crypto.Signature import PKCS1_v1_5
            from Crypto.Hash import SHA256
        except ImportError:
            return False
        
        params_copy = {k: v for k, v in params.items() if k not in ['sign', 'sign_type']}
        sorted_params = sorted(params_copy.items())
        sign_str = "&".join(f"{k}={v}" for k, v in sorted_params if v)
        
        key = RSA.import_key(self.public_key)
        verifier = PKCS1_v1_5.new(key)
        digest = SHA256.new(sign_str.encode('utf-8'))
        
        try:
            verifier.verify(digest, base64.b64decode(sign))
            return True
        except:
            return False
    
    async def create_order(
        self,
        order_id: str,
        amount: int,
        subject: str,
        description: str = "",
        **kwargs
    ) -> PaymentResult:
        """创建支付宝订单（网页支付）"""
        if not self.app_id or not self.private_key:
            return PaymentResult(
                success=False,
                order_id=order_id,
                error_message="支付宝配置不完整"
            )
        
        biz_content = {
            "out_trade_no": order_id,
            "total_amount": f"{amount / 100:.2f}",
            "subject": subject,
            "body": description,
            "product_code": "FAST_INSTANT_TRADE_PAY"
        }
        
        params = {
            "app_id": self.app_id,
            "method": "alipay.trade.page.pay",
            "format": "JSON",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "notify_url": self.notify_url,
            "return_url": self.return_url,
            "biz_content": json.dumps(biz_content)
        }
        
        params["sign"] = self._sign(params)
        payment_url = f"{self.gateway}?{urlencode(params, quote_via=quote_plus)}"
        
        return PaymentResult(
            success=True,
            order_id=order_id,
            payment_url=payment_url,
            idempotency_key=order_id
        )
    
    async def create_qr_order(
        self,
        order_id: str,
        amount: int,
        subject: str,
        description: str = ""
    ) -> PaymentResult:
        """创建支付宝订单（扫码支付）"""
        if not self.app_id or not self.private_key:
            return PaymentResult(
                success=False,
                order_id=order_id,
                error_message="支付宝配置不完整"
            )
        
        biz_content = {
            "out_trade_no": order_id,
            "total_amount": f"{amount / 100:.2f}",
            "subject": subject,
            "body": description
        }
        
        params = {
            "app_id": self.app_id,
            "method": "alipay.trade.precreate",
            "format": "JSON",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "notify_url": self.notify_url,
            "biz_content": json.dumps(biz_content)
        }
        
        params["sign"] = self._sign(params)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.gateway, data=params)
            result = response.json()
        
        resp_data = result.get("alipay_trade_precreate_response", {})
        
        if resp_data.get("code") == "10000":
            return PaymentResult(
                success=True,
                order_id=order_id,
                qr_code=resp_data.get("qr_code"),
                raw_response=result,
                idempotency_key=order_id
            )
        else:
            return PaymentResult(
                success=False,
                order_id=order_id,
                error_message=resp_data.get("sub_msg", "创建订单失败"),
                raw_response=result
            )
    
    async def verify_callback(self, data: Dict) -> tuple:
        """验证支付宝回调"""
        sign = data.get("sign", "")
        
        if not self._verify_sign(data, sign):
            return False, None, 0
        
        order_id = data.get("out_trade_no")
        amount = int(float(data.get("total_amount", 0)) * 100)
        trade_status = data.get("trade_status")
        
        if trade_status in ["TRADE_SUCCESS", "TRADE_FINISHED"]:
            return True, order_id, amount
        
        return False, order_id, amount
    
    async def query_order(self, order_id: str) -> Dict:
        """查询订单状态"""
        biz_content = {"out_trade_no": order_id}
        
        params = {
            "app_id": self.app_id,
            "method": "alipay.trade.query",
            "format": "JSON",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "biz_content": json.dumps(biz_content)
        }
        
        params["sign"] = self._sign(params)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.gateway, data=params)
            return response.json()


class WechatPayProvider(PaymentProvider):
    """微信支付（V3 API）"""
    
    API_BASE = "https://api.mch.weixin.qq.com"
    
    def __init__(self):
        self.app_id = settings.WECHAT_APP_ID
        self.mch_id = settings.WECHAT_MCH_ID
        self.api_key = settings.WECHAT_API_KEY
        self.notify_url = settings.WECHAT_NOTIFY_URL
    
    def _sign_v3(self, method: str, url: str, timestamp: str, nonce: str, body: str) -> str:
        """V3 签名"""
        sign_str = f"{method}\n{url}\n{timestamp}\n{nonce}\n{body}\n"
        
        try:
            signature = hmac.new(
                self.api_key.encode('utf-8'),
                sign_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            return signature
        except Exception as e:
            logger.error(f"WeChat sign error: {e}")
            return ""
    
    async def create_order(
        self,
        order_id: str,
        amount: int,
        subject: str,
        description: str = "",
        **kwargs
    ) -> PaymentResult:
        """创建微信支付订单（Native 扫码支付）"""
        if not self.app_id or not self.mch_id:
            return PaymentResult(
                success=False,
                order_id=order_id,
                error_message="微信支付配置不完整"
            )
        
        url = "/v3/pay/transactions/native"
        timestamp = str(int(datetime.now().timestamp()))
        nonce = uuid.uuid4().hex
        
        body = {
            "appid": self.app_id,
            "mchid": self.mch_id,
            "description": subject,
            "out_trade_no": order_id,
            "notify_url": self.notify_url,
            "amount": {
                "total": amount,
                "currency": "CNY"
            }
        }
        
        body_str = json.dumps(body)
        signature = self._sign_v3("POST", url, timestamp, nonce, body_str)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f'WECHATPAY2-SHA256-RSA2048 mchid="{self.mch_id}",nonce_str="{nonce}",signature="{signature}",timestamp="{timestamp}",serial_no="YOUR_SERIAL_NO"'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.API_BASE}{url}",
                headers=headers,
                content=body_str
            )
            result = response.json()
        
        if "code_url" in result:
            return PaymentResult(
                success=True,
                order_id=order_id,
                qr_code=result["code_url"],
                raw_response=result,
                idempotency_key=order_id
            )
        else:
            return PaymentResult(
                success=False,
                order_id=order_id,
                error_message=result.get("message", "创建订单失败"),
                raw_response=result
            )
    
    async def verify_callback(self, data: Dict) -> tuple:
        """验证微信支付回调"""
        resource = data.get("resource", {})
        order_id = resource.get("out_trade_no")
        amount = resource.get("amount", {}).get("total", 0)
        trade_state = resource.get("trade_state")
        
        if trade_state == "SUCCESS":
            return True, order_id, amount
        
        return False, order_id, amount
    
    async def query_order(self, order_id: str) -> Dict:
        """查询订单状态"""
        url = f"/v3/pay/transactions/out-trade-no/{order_id}?mchid={self.mch_id}"
        
        timestamp = str(int(datetime.now().timestamp()))
        nonce = uuid.uuid4().hex
        signature = self._sign_v3("GET", url, timestamp, nonce, "")
        
        headers = {
            "Authorization": f'WECHATPAY2-SHA256-RSA2048 mchid="{self.mch_id}",nonce_str="{nonce}",signature="{signature}",timestamp="{timestamp}",serial_no="YOUR_SERIAL_NO"'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.API_BASE}{url}", headers=headers)
            return response.json()


class PaymentService:
    """统一支付服务"""
    
    # 订单过期时间（分钟）
    ORDER_EXPIRE_MINUTES = 30
    
    def __init__(self):
        self.alipay = AlipayProvider()
        self.wechat = WechatPayProvider()
        self._processed_callbacks = {}  # 幂等性缓存
    
    def generate_order_id(self, prefix: str = "PAY") -> str:
        """生成唯一订单号"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_part = uuid.uuid4().hex[:8].upper()
        return f"{prefix}{timestamp}{random_part}"
    
    async def create_order(
        self,
        provider: str,
        order_id: str,
        amount: int,
        subject: str,
        description: str = "",
        **kwargs
    ) -> PaymentResult:
        """创建支付订单"""
        logger.info(f"Creating order: {order_id}, provider: {provider}, amount: {amount}")
        
        if provider == "alipay":
            return await self.alipay.create_order(order_id, amount, subject, description, **kwargs)
        elif provider == "alipay_qr":
            return await self.alipay.create_qr_order(order_id, amount, subject, description)
        elif provider == "wechat":
            return await self.wechat.create_order(order_id, amount, subject, description, **kwargs)
        else:
            return PaymentResult(
                success=False,
                order_id=order_id,
                error_message=f"不支持的支付方式: {provider}"
            )
    
    async def verify_callback(self, provider: str, data: Dict) -> tuple:
        """验证支付回调"""
        if provider == "alipay":
            return await self.alipay.verify_callback(data)
        elif provider == "wechat":
            return await self.wechat.verify_callback(data)
        else:
            return False, None, 0
    
    async def process_callback_idempotent(
        self, 
        provider: str, 
        data: Dict,
        process_func
    ) -> Dict:
        """
        幂等处理支付回调
        process_func: async def(order_id, amount) -> bool
        """
        # 验证回调
        is_valid, order_id, amount = await self.verify_callback(provider, data)
        
        if not is_valid:
            logger.warning(f"Invalid callback for provider {provider}")
            return {"success": False, "message": "签名验证失败"}
        
        if not order_id:
            return {"success": False, "message": "订单号为空"}
        
        # 幂等性检查
        callback_key = f"{provider}:{order_id}"
        if callback_key in self._processed_callbacks:
            logger.info(f"Duplicate callback ignored: {callback_key}")
            return {"success": True, "message": "订单已处理"}
        
        try:
            # 处理订单
            result = await process_func(order_id, amount)
            
            if result:
                # 标记为已处理
                self._processed_callbacks[callback_key] = datetime.utcnow()
                # 清理过期的缓存（保留24小时）
                self._cleanup_processed_cache()
                
            return {"success": result, "order_id": order_id}
        except Exception as e:
            logger.error(f"Process callback error: {e}")
            return {"success": False, "message": str(e)}
    
    def _cleanup_processed_cache(self):
        """清理过期的幂等性缓存"""
        cutoff = datetime.utcnow() - timedelta(hours=24)
        expired_keys = [
            k for k, v in self._processed_callbacks.items() 
            if v < cutoff
        ]
        for k in expired_keys:
            del self._processed_callbacks[k]
    
    async def query_order(self, provider: str, order_id: str) -> Dict:
        """查询订单状态"""
        if provider == "alipay":
            return await self.alipay.query_order(order_id)
        elif provider == "wechat":
            return await self.wechat.query_order(order_id)
        else:
            return {"error": f"不支持的支付方式: {provider}"}
    
    def is_order_expired(self, created_at: datetime) -> bool:
        """检查订单是否过期"""
        if not created_at:
            return True
        expire_time = created_at + timedelta(minutes=self.ORDER_EXPIRE_MINUTES)
        return datetime.utcnow() > expire_time


# 全局支付服务实例
payment_service = PaymentService()
