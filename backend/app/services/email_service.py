"""
邮件服务 - 支持SMTP和第三方邮件API
"""
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import Optional
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings
from app.core.redis import RedisCache

_executor = ThreadPoolExecutor(max_workers=2)


class EmailConfig:
    """邮件配置"""
    # SMTP配置（从环境变量读取）
    SMTP_HOST: str = getattr(settings, 'SMTP_HOST', 'smtp.qq.com')
    SMTP_PORT: int = getattr(settings, 'SMTP_PORT', 465)
    SMTP_USER: str = getattr(settings, 'SMTP_USER', '')
    SMTP_PASSWORD: str = getattr(settings, 'SMTP_PASSWORD', '')
    SMTP_USE_SSL: bool = getattr(settings, 'SMTP_USE_SSL', True)
    
    # 发件人信息
    FROM_NAME: str = getattr(settings, 'EMAIL_FROM_NAME', 'VOD平台')
    FROM_EMAIL: str = getattr(settings, 'EMAIL_FROM_EMAIL', '')
    
    # 验证码设置
    CODE_LENGTH: int = 6
    CODE_EXPIRE_MINUTES: int = 10
    CODE_RESEND_SECONDS: int = 60  # 重发间隔


class EmailService:
    """邮件服务"""
    
    @staticmethod
    def generate_code(length: int = 6) -> str:
        """生成数字验证码"""
        return ''.join(random.choices(string.digits, k=length))
    
    @staticmethod
    def _send_smtp_email(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str = None
    ) -> bool:
        """
        通过SMTP发送邮件（同步方法，在线程池中执行）
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{EmailConfig.FROM_NAME} <{EmailConfig.FROM_EMAIL or EmailConfig.SMTP_USER}>"
            msg['To'] = to_email
            msg['Subject'] = Header(subject, 'utf-8')
            
            # 添加纯文本版本
            if text_content:
                part1 = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(part1)
            
            # 添加HTML版本
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part2)
            
            # 发送邮件
            if EmailConfig.SMTP_USE_SSL:
                server = smtplib.SMTP_SSL(EmailConfig.SMTP_HOST, EmailConfig.SMTP_PORT)
            else:
                server = smtplib.SMTP(EmailConfig.SMTP_HOST, EmailConfig.SMTP_PORT)
                server.starttls()
            
            server.login(EmailConfig.SMTP_USER, EmailConfig.SMTP_PASSWORD)
            server.sendmail(
                EmailConfig.FROM_EMAIL or EmailConfig.SMTP_USER,
                [to_email],
                msg.as_string()
            )
            server.quit()
            
            print(f"[Email] 邮件发送成功: {to_email}")
            return True
            
        except Exception as e:
            print(f"[Email] 邮件发送失败: {e}")
            return False
    
    @staticmethod
    async def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str = None
    ) -> bool:
        """异步发送邮件"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor,
            EmailService._send_smtp_email,
            to_email, subject, html_content, text_content
        )
    
    @staticmethod
    def _build_verification_email(code: str, purpose: str = "验证") -> tuple:
        """构建验证码邮件内容"""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
                .container {{ max-width: 500px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; }}
                .header h1 {{ color: #fff; margin: 0; font-size: 24px; }}
                .content {{ padding: 40px 30px; text-align: center; }}
                .code-box {{ background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%); border-radius: 10px; padding: 25px; margin: 25px 0; }}
                .code {{ font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #667eea; font-family: 'Courier New', monospace; }}
                .tips {{ color: #666; font-size: 14px; line-height: 1.8; margin-top: 20px; }}
                .warning {{ color: #e74c3c; font-size: 13px; margin-top: 15px; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #999; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📧 邮箱{purpose}</h1>
                </div>
                <div class="content">
                    <p style="color: #333; font-size: 16px;">您正在进行邮箱{purpose}操作，验证码为：</p>
                    <div class="code-box">
                        <div class="code">{code}</div>
                    </div>
                    <div class="tips">
                        <p>⏰ 验证码有效期为 <strong>{EmailConfig.CODE_EXPIRE_MINUTES} 分钟</strong></p>
                        <p>🔒 请勿将验证码告知他人，以保障账户安全</p>
                    </div>
                    <p class="warning">如果这不是您本人的操作，请忽略此邮件</p>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿直接回复</p>
                    <p>© {datetime.now().year} VOD Platform. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        您正在进行邮箱{purpose}操作
        
        验证码: {code}
        
        有效期: {EmailConfig.CODE_EXPIRE_MINUTES} 分钟
        
        请勿将验证码告知他人，以保障账户安全。
        如果这不是您本人的操作，请忽略此邮件。
        """
        
        return html_content, text_content
    
    @staticmethod
    async def send_verification_code(
        email: str,
        purpose: str = "验证",
        code_type: str = "verify"  # verify, bind, reset
    ) -> dict:
        """
        发送验证码邮件
        
        返回:
        {
            "success": True/False,
            "message": "...",
            "code": "123456" (仅调试模式返回)
        }
        """
        # 检查发送频率限制
        rate_key = f"email_rate:{email}"
        last_sent = await RedisCache.get(rate_key)
        
        if last_sent:
            remaining = EmailConfig.CODE_RESEND_SECONDS - (datetime.utcnow().timestamp() - float(last_sent))
            if remaining > 0:
                return {
                    "success": False,
                    "message": f"发送过于频繁，请 {int(remaining)} 秒后重试",
                    "retry_after": int(remaining)
                }
        
        # 生成验证码
        code = EmailService.generate_code(EmailConfig.CODE_LENGTH)
        
        # 存储验证码到 Redis
        code_key = f"email_code:{code_type}:{email}"
        await RedisCache.set(code_key, code, expire=EmailConfig.CODE_EXPIRE_MINUTES * 60)
        
        # 记录发送时间（用于频率限制）
        await RedisCache.set(rate_key, str(datetime.utcnow().timestamp()), expire=EmailConfig.CODE_RESEND_SECONDS)
        
        # 构建邮件内容
        html_content, text_content = EmailService._build_verification_email(code, purpose)
        
        # 发送邮件
        subject = f"【VOD平台】邮箱{purpose}验证码"
        
        # 检查是否配置了SMTP
        if not EmailConfig.SMTP_USER or not EmailConfig.SMTP_PASSWORD:
            # 未配置SMTP，调试模式直接返回验证码
            print(f"[Email Debug] 验证码: {code} -> {email}")
            return {
                "success": True,
                "message": "验证码已发送（调试模式）",
                "code": code,  # 调试模式返回验证码
                "debug": True
            }
        
        success = await EmailService.send_email(email, subject, html_content, text_content)
        
        if success:
            return {
                "success": True,
                "message": "验证码已发送到您的邮箱，请注意查收"
            }
        else:
            # 发送失败，清除验证码
            await RedisCache.delete(code_key)
            return {
                "success": False,
                "message": "邮件发送失败，请稍后重试"
            }
    
    @staticmethod
    async def verify_code(
        email: str,
        code: str,
        code_type: str = "verify"
    ) -> dict:
        """
        验证邮箱验证码
        
        返回:
        {
            "success": True/False,
            "message": "..."
        }
        """
        code_key = f"email_code:{code_type}:{email}"
        stored_code = await RedisCache.get(code_key)
        
        if not stored_code:
            return {
                "success": False,
                "message": "验证码已过期或不存在"
            }
        
        if stored_code != code:
            return {
                "success": False,
                "message": "验证码错误"
            }
        
        # 验证成功，删除验证码（一次性使用）
        await RedisCache.delete(code_key)
        
        return {
            "success": True,
            "message": "验证成功"
        }
    
    @staticmethod
    async def send_welcome_email(email: str, username: str) -> bool:
        """发送欢迎邮件"""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
                .container {{ max-width: 500px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; text-align: center; }}
                .header h1 {{ color: #fff; margin: 0; font-size: 28px; }}
                .header p {{ color: rgba(255,255,255,0.9); margin: 10px 0 0; }}
                .content {{ padding: 40px 30px; }}
                .feature {{ display: flex; align-items: center; margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
                .feature-icon {{ font-size: 24px; margin-right: 15px; }}
                .feature-text {{ color: #333; }}
                .cta {{ text-align: center; margin: 30px 0; }}
                .cta a {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; padding: 15px 40px; border-radius: 30px; text-decoration: none; font-weight: bold; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #999; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 欢迎加入</h1>
                    <p>Hi {username}，感谢您的注册！</p>
                </div>
                <div class="content">
                    <p style="color: #333; font-size: 16px; line-height: 1.8;">
                        您的账号已创建成功，现在可以开始探索平台的精彩内容了！
                    </p>
                    
                    <div class="feature">
                        <span class="feature-icon">🎬</span>
                        <span class="feature-text">海量高清视频，随心观看</span>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">👑</span>
                        <span class="feature-text">升级VIP，解锁更多特权</span>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">🎁</span>
                        <span class="feature-text">每日签到，领取积分好礼</span>
                    </div>
                    
                    <div class="cta">
                        <a href="#">立即开始探索</a>
                    </div>
                </div>
                <div class="footer">
                    <p>© {datetime.now().year} VOD Platform. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        subject = "🎉 欢迎加入 VOD平台"
        return await EmailService.send_email(email, subject, html_content)
    
    @staticmethod
    async def send_password_reset_email(email: str, reset_token: str) -> bool:
        """发送密码重置邮件"""
        
        reset_link = f"https://your-domain.com/reset-password?token={reset_token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
                .container {{ max-width: 500px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); padding: 30px; text-align: center; }}
                .header h1 {{ color: #fff; margin: 0; font-size: 24px; }}
                .content {{ padding: 40px 30px; text-align: center; }}
                .cta {{ margin: 30px 0; }}
                .cta a {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; padding: 15px 40px; border-radius: 30px; text-decoration: none; font-weight: bold; }}
                .tips {{ color: #666; font-size: 14px; line-height: 1.8; margin-top: 20px; }}
                .warning {{ color: #e74c3c; font-size: 13px; margin-top: 15px; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #999; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔑 密码重置</h1>
                </div>
                <div class="content">
                    <p style="color: #333; font-size: 16px;">您正在申请重置密码，请点击下方按钮完成操作：</p>
                    
                    <div class="cta">
                        <a href="{reset_link}">重置密码</a>
                    </div>
                    
                    <div class="tips">
                        <p>⏰ 链接有效期为 <strong>30 分钟</strong></p>
                        <p>🔒 如果按钮无法点击，请复制以下链接到浏览器：</p>
                        <p style="word-break: break-all; font-size: 12px; color: #999;">{reset_link}</p>
                    </div>
                    
                    <p class="warning">如果这不是您本人的操作，请忽略此邮件并确保账户安全</p>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿直接回复</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        subject = "【VOD平台】密码重置"
        return await EmailService.send_email(email, subject, html_content)


