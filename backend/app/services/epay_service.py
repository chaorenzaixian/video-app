"""
彩虹易支付 SDK Python版
支持：支付宝、微信支付、QQ钱包
"""
import hashlib
import httpx
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlencode
from dataclasses import dataclass
from app.core.config import settings


@dataclass
class PaymentResult:
    """支付结果"""
    success: bool
    payment_url: Optional[str] = None
    qr_code: Optional[str] = None
    trade_no: Optional[str] = None
    error_message: Optional[str] = None


class EpayService:
    """易支付服务"""
    
    def __init__(self):
        self.pid = settings.EPAY_PID
        self.key = settings.EPAY_KEY
        api_url = settings.EPAY_URL.rstrip('/') if settings.EPAY_URL else ''
        self.api_url = api_url
        self.submit_url = f"{api_url}/submit.php" if api_url else ''
        self.mapi_url = f"{api_url}/mapi.php" if api_url else ''
        self.query_url = f"{api_url}/api.php" if api_url else ''
        self.sign_type = "MD5"
        
        # 回调地址
        self.notify_url = settings.EPAY_NOTIFY_URL or ''
        self.return_url = settings.EPAY_RETURN_URL or ''
    
    def _get_sign(self, params: Dict[str, Any]) -> str:
        """计算MD5签名"""
        # 按key排序
        sorted_params = sorted(params.items())
        # 拼接字符串（排除sign和sign_type，排除空值）
        sign_str = '&'.join([
            f"{k}={v}" for k, v in sorted_params 
            if k not in ('sign', 'sign_type') and v != '' and v is not None
        ])
        # 拼接密钥
        sign_str += self.key
        # MD5签名
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest()
    
    def _build_request_param(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """构建请求参数（添加签名）"""
        # 过滤空值
        params = {k: v for k, v in params.items() if v is not None and v != ''}
        sign = self._get_sign(params)
        params['sign'] = sign
        params['sign_type'] = self.sign_type
        return params
    
    def get_pay_url(
        self,
        out_trade_no: str,
        pay_type: str,
        name: str,
        money: float,
        notify_url: str = None,
        return_url: str = None,
        param: str = "",
        clientip: str = ""
    ) -> str:
        """
        获取支付跳转链接（页面跳转方式）
        
        Args:
            out_trade_no: 商户订单号
            pay_type: 支付方式 (alipay/wxpay/qqpay)
            name: 商品名称
            money: 支付金额（元）
            notify_url: 异步通知地址
            return_url: 同步跳转地址
            param: 自定义参数（回调时原样返回）
            clientip: 用户IP
        
        Returns:
            支付跳转URL
        """
        params = {
            'pid': self.pid,
            'type': pay_type,
            'out_trade_no': out_trade_no,
            'notify_url': notify_url or self.notify_url,
            'return_url': return_url or self.return_url,
            'name': name,
            'money': str(money),
            'param': param,
            'clientip': clientip or ''
        }
        params = self._build_request_param(params)
        return f"{self.submit_url}?{urlencode(params)}"
    
    async def create_order(
        self,
        order_id: str,
        amount: float,
        subject: str,
        pay_type: str = "alipay",
        client_ip: str = None,
        notify_url: str = None,
        return_url: str = None
    ) -> PaymentResult:
        """
        创建支付订单（页面跳转方式）
        
        Returns:
            PaymentResult 包含 payment_url
        """
        try:
            payment_url = self.get_pay_url(
                out_trade_no=order_id,
                pay_type=pay_type,
                name=subject,
                money=amount,
                notify_url=notify_url,
                return_url=return_url,
                clientip=client_ip or ''
            )
            
            return PaymentResult(
                success=True,
                payment_url=payment_url
            )
        except Exception as e:
            return PaymentResult(
                success=False,
                error_message=str(e)
            )
    
    async def create_qr_order(
        self,
        order_id: str,
        amount: float,
        subject: str,
        pay_type: str = "alipay",
        client_ip: str = None,
        notify_url: str = None,
        return_url: str = None
    ) -> PaymentResult:
        """
        创建支付订单（API方式，获取二维码）
        
        Returns:
            PaymentResult 包含 qr_code 和 payment_url
        """
        params = {
            'pid': self.pid,
            'type': pay_type,
            'out_trade_no': order_id,
            'notify_url': notify_url or self.notify_url,
            'return_url': return_url or self.return_url,
            'name': subject,
            'money': str(amount),
            'clientip': client_ip or ''
        }
        params = self._build_request_param(params)
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(self.mapi_url, data=params)
                result = response.json()
            
            if result.get('code') == 1:
                return PaymentResult(
                    success=True,
                    payment_url=result.get('payurl'),
                    qr_code=result.get('qrcode'),
                    trade_no=result.get('trade_no')
                )
            else:
                return PaymentResult(
                    success=False,
                    error_message=result.get('msg', '创建订单失败')
                )
        except Exception as e:
            return PaymentResult(
                success=False,
                error_message=str(e)
            )
    
    def verify_sign(self, params: Dict[str, Any]) -> bool:
        """
        验证签名
        
        Args:
            params: 回调参数（包含sign）
        
        Returns:
            签名是否有效
        """
        if 'sign' not in params:
            return False
        
        received_sign = params.get('sign', '')
        calculated_sign = self._get_sign(params)
        
        return received_sign == calculated_sign
    
    def verify_notify(self, params: Dict[str, Any]) -> bool:
        """验证异步回调签名"""
        return self.verify_sign(params)
    
    def verify_return(self, params: Dict[str, Any]) -> bool:
        """验证同步回调签名"""
        return self.verify_sign(params)
    
    def parse_callback(self, params: Dict[str, Any]) -> Tuple[bool, str, str, float, str]:
        """
        解析并验证回调参数
        
        Returns:
            (is_success, order_no, trade_no, amount, trade_status)
        """
        # 验证签名
        if not self.verify_sign(params):
            return (False, '', '', 0, 'sign_error')
        
        trade_status = params.get('trade_status', '')
        order_no = params.get('out_trade_no', '')
        trade_no = params.get('trade_no', '')
        
        try:
            amount = float(params.get('money', 0))
        except:
            amount = 0
        
        is_success = trade_status == 'TRADE_SUCCESS'
        
        return (is_success, order_no, trade_no, amount, trade_status)
    
    async def query_order(self, trade_no: str) -> Dict[str, Any]:
        """
        查询订单状态
        
        Args:
            trade_no: 平台订单号或商户订单号
        
        Returns:
            {
                "code": 1,
                "msg": "success",
                "trade_no": "平台订单号",
                "out_trade_no": "商户订单号",
                "type": "支付方式",
                "pid": "商户ID",
                "money": "金额",
                "status": 1,  # 0未支付 1已支付
                ...
            }
        """
        url = f"{self.query_url}?act=order&pid={self.pid}&key={self.key}&trade_no={trade_no}"
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url)
                return response.json()
        except Exception as e:
            return {"code": 0, "msg": str(e), "status": 0}
    
    async def order_status(self, trade_no: str) -> bool:
        """检查订单是否已支付"""
        result = await self.query_order(trade_no)
        return result.get('status') == 1
    
    async def refund(self, trade_no: str, money: float) -> Dict[str, Any]:
        """
        订单退款
        
        Args:
            trade_no: 平台订单号
            money: 退款金额
        
        Returns:
            退款结果
        """
        url = self.query_url
        params = {
            'act': 'refund',
            'pid': self.pid,
            'key': self.key,
            'trade_no': trade_no,
            'money': str(money)
        }
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(url, data=params)
                return response.json()
        except Exception as e:
            return {"code": 0, "msg": str(e)}


# 单例
epay_service = EpayService()
