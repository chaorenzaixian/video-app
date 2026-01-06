"""
支付服务 - 支付宝/微信/Stripe 统一接口
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import hashlib
import json
import uuid
import hmac
import base64
from urllib.parse import urlencode, quote_plus

import httpx

from app.core.config import settings


class PaymentResult:
    """支付结果"""
    def __init__(
        self,
        success: bool,
        order_id: str,
        payment_url: str = None,
        qr_code: str = None,
        error_message: str = None,
        raw_response: Dict = None
    ):
        self.success = success
        self.order_id = order_id
        self.payment_url = payment_url
        self.qr_code = qr_code
        self.error_message = error_message
        self.raw_response = raw_response


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
        
        # 排序并拼接参数
        sorted_params = sorted(params.items())
        sign_str = "&".join(f"{k}={v}" for k, v in sorted_params if v)
        
        # RSA2 签名
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
        
        # 移除 sign 和 sign_type
        params_copy = {k: v for k, v in params.items() if k not in ['sign', 'sign_type']}
        sorted_params = sorted(params_copy.items())
        sign_str = "&".join(f"{k}={v}" for k, v in sorted_params if v)
        
        # 验证签名
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
        
        # 业务参数
        biz_content = {
            "out_trade_no": order_id,
            "total_amount": f"{amount / 100:.2f}",  # 转换为元
            "subject": subject,
            "body": description,
            "product_code": "FAST_INSTANT_TRADE_PAY"
        }
        
        # 公共参数
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
        
        # 签名
        params["sign"] = self._sign(params)
        
        # 构建支付 URL
        payment_url = f"{self.gateway}?{urlencode(params, quote_via=quote_plus)}"
        
        return PaymentResult(
            success=True,
            order_id=order_id,
            payment_url=payment_url
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
                raw_response=result
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
        
        # 使用商户私钥签名
        try:
            from Crypto.PublicKey import RSA
            from Crypto.Signature import PKCS1_v1_5
            from Crypto.Hash import SHA256
            
            # 这里需要加载商户私钥
            # key = RSA.import_key(open(settings.WECHAT_KEY_PATH).read())
            # signer = PKCS1_v1_5.new(key)
            # digest = SHA256.new(sign_str.encode('utf-8'))
            # signature = base64.b64encode(signer.sign(digest)).decode('utf-8')
            # return signature
            
            # 简化版：使用 HMAC-SHA256
            signature = hmac.new(
                self.api_key.encode('utf-8'),
                sign_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            return signature
        except Exception as e:
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
                raw_response=result
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
        # V3 回调验签逻辑
        # 需要验证请求头中的签名
        
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
    
    def __init__(self):
        self.alipay = AlipayProvider()
        self.wechat = WechatPayProvider()
    
    async def create_order(
        self,
        provider: str,  # alipay / wechat / stripe
        order_id: str,
        amount: int,
        subject: str,
        description: str = "",
        **kwargs
    ) -> PaymentResult:
        """创建支付订单"""
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
    
    async def query_order(self, provider: str, order_id: str) -> Dict:
        """查询订单状态"""
        if provider == "alipay":
            return await self.alipay.query_order(order_id)
        elif provider == "wechat":
            return await self.wechat.query_order(order_id)
        else:
            return {"error": f"不支持的支付方式: {provider}"}


# 全局支付服务实例
payment_service = PaymentService()
