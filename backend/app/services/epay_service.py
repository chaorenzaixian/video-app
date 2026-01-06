"""
易支付服务 - 支持彩虹易支付/通用易支付接口
"""
import hashlib
import time
from typing import Optional, Dict, Any
from urllib.parse import urlencode, quote_plus
import httpx

from app.core.config import settings


class EpayResult:
    """易支付结果"""
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


class EpayService:
    """
    易支付服务
    
    支持的支付方式:
    - alipay: 支付宝
    - wxpay: 微信支付
    - qqpay: QQ钱包
    - bank: 网银支付
    """
    
    def __init__(self):
        self.api_url = settings.EPAY_URL.rstrip('/')
        self.pid = settings.EPAY_PID
        self.key = settings.EPAY_KEY
        self.notify_url = settings.EPAY_NOTIFY_URL
        self.return_url = settings.EPAY_RETURN_URL
    
    def _sign(self, params: Dict) -> str:
        """
        生成签名（MD5）
        签名规则：按参数名ASCII码排序，拼接后加上密钥，MD5加密
        """
        # 过滤空值和签名字段
        filtered = {k: v for k, v in params.items() if v and k not in ['sign', 'sign_type']}
        # 按键名排序
        sorted_params = sorted(filtered.items())
        # 拼接字符串
        sign_str = '&'.join(f'{k}={v}' for k, v in sorted_params)
        # 加上密钥
        sign_str += self.key
        # MD5 加密
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest()
    
    def verify_sign(self, params: Dict) -> bool:
        """验证签名"""
        sign = params.get('sign', '')
        if not sign:
            return False
        
        expected_sign = self._sign(params)
        return sign.lower() == expected_sign.lower()
    
    async def create_order(
        self,
        order_id: str,
        amount: float,  # 金额（元）
        subject: str,
        pay_type: str = 'alipay',  # alipay/wxpay/qqpay/bank
        client_ip: str = None,
        **kwargs
    ) -> EpayResult:
        """
        创建支付订单（页面跳转方式）
        
        Args:
            order_id: 商户订单号
            amount: 金额（元）
            subject: 商品名称
            pay_type: 支付方式 alipay/wxpay/qqpay/bank
            client_ip: 客户端IP
        
        Returns:
            EpayResult: 包含支付跳转URL
        """
        if not self.api_url or not self.pid or not self.key:
            return EpayResult(
                success=False,
                order_id=order_id,
                error_message="易支付配置不完整，请检查 EPAY_URL、EPAY_PID、EPAY_KEY"
            )
        
        # 构建参数
        params = {
            'pid': self.pid,
            'type': pay_type,
            'out_trade_no': order_id,
            'notify_url': self.notify_url or f"{settings.EPAY_URL}/api/v1/payments/epay/notify",
            'return_url': self.return_url or f"{settings.EPAY_URL}/payment/success",
            'name': subject,
            'money': f"{amount:.2f}",
            'clientip': client_ip or '',
            'sign_type': 'MD5',
        }
        
        # 生成签名
        params['sign'] = self._sign(params)
        
        # 构建跳转URL
        payment_url = f"{self.api_url}/submit.php?{urlencode(params)}"
        
        return EpayResult(
            success=True,
            order_id=order_id,
            payment_url=payment_url
        )
    
    async def create_qr_order(
        self,
        order_id: str,
        amount: float,
        subject: str,
        pay_type: str = 'alipay',
        client_ip: str = None,
    ) -> EpayResult:
        """
        创建支付订单（获取二维码/支付链接）
        使用 API 接口获取支付二维码
        """
        if not self.api_url or not self.pid or not self.key:
            return EpayResult(
                success=False,
                order_id=order_id,
                error_message="易支付配置不完整"
            )
        
        params = {
            'pid': self.pid,
            'type': pay_type,
            'out_trade_no': order_id,
            'notify_url': self.notify_url,
            'name': subject,
            'money': f"{amount:.2f}",
            'clientip': client_ip or '',
            'sign_type': 'MD5',
        }
        
        params['sign'] = self._sign(params)
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # 调用 API 接口
                response = await client.get(
                    f"{self.api_url}/mapi.php",
                    params=params
                )
                result = response.json()
            
            if result.get('code') == 1:
                return EpayResult(
                    success=True,
                    order_id=order_id,
                    qr_code=result.get('qrcode') or result.get('payurl'),
                    payment_url=result.get('payurl'),
                    raw_response=result
                )
            else:
                return EpayResult(
                    success=False,
                    order_id=order_id,
                    error_message=result.get('msg', '创建订单失败'),
                    raw_response=result
                )
        except Exception as e:
            return EpayResult(
                success=False,
                order_id=order_id,
                error_message=f"请求易支付接口失败: {str(e)}"
            )
    
    async def query_order(self, order_id: str) -> Dict:
        """
        查询订单状态
        """
        params = {
            'act': 'order',
            'pid': self.pid,
            'out_trade_no': order_id,
            'sign_type': 'MD5',
        }
        
        params['sign'] = self._sign(params)
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.api_url}/api.php",
                    params=params
                )
                return response.json()
        except Exception as e:
            return {'error': str(e)}
    
    def parse_callback(self, params: Dict) -> tuple:
        """
        解析回调参数
        
        Returns:
            (is_valid, order_id, trade_no, amount, trade_status)
        """
        # 验证签名
        if not self.verify_sign(params):
            return False, None, None, 0, None
        
        order_id = params.get('out_trade_no')
        trade_no = params.get('trade_no')
        amount = float(params.get('money', 0))
        trade_status = params.get('trade_status')
        
        # trade_status: TRADE_SUCCESS 表示支付成功
        is_success = trade_status == 'TRADE_SUCCESS'
        
        return is_success, order_id, trade_no, amount, trade_status


# 全局实例
epay_service = EpayService()
