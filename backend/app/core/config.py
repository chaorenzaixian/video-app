"""
应用配置管理 - 安全增强版
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional, List
import os
import secrets

# 获取项目根目录（backend目录）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "VOD Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"  # development / staging / production
    
    # 安全配置 - 生产环境必须从环境变量读取
    SECRET_KEY: str = ""
    JWT_SECRET_KEY: str = ""
    
    # CORS 配置（逗号分隔的域名列表，* 表示允许所有）
    # 生产环境建议设置具体域名：https://ssoul.cc,https://www.ssoul.cc
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000"
    
    # 数据库配置 - 默认使用 SQLite（本地开发）
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = True
    
    # JWT配置
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # API 限流配置
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REGISTER: str = "3/minute"
    RATE_LIMIT_DEFAULT: str = "60/minute"
    
    # 视频存储配置（使用绝对路径）
    UPLOAD_DIR: str = os.path.join(BASE_DIR, "uploads")
    VIDEO_DIR: str = os.path.join(BASE_DIR, "uploads/videos")
    THUMBNAIL_DIR: str = os.path.join(BASE_DIR, "uploads/thumbnails")
    HLS_DIR: str = os.path.join(BASE_DIR, "uploads/hls")
    MAX_VIDEO_SIZE: int = 5 * 1024 * 1024 * 1024  # 5GB
    
    # FFmpeg配置
    FFMPEG_PATH: str = "ffmpeg"
    
    # AI配置 (OpenAI)
    OPENAI_API_KEY: Optional[str] = None
    
    # 支付配置 - Stripe
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    
    # 支付配置 - 支付宝
    ALIPAY_APP_ID: Optional[str] = None
    ALIPAY_PRIVATE_KEY: Optional[str] = None
    ALIPAY_PUBLIC_KEY: Optional[str] = None
    ALIPAY_NOTIFY_URL: Optional[str] = None
    ALIPAY_RETURN_URL: Optional[str] = None
    ALIPAY_SANDBOX: bool = True  # 沙箱模式
    
    # 支付配置 - 微信支付
    WECHAT_APP_ID: Optional[str] = None
    WECHAT_MCH_ID: Optional[str] = None
    WECHAT_API_KEY: Optional[str] = None
    WECHAT_CERT_PATH: Optional[str] = None
    WECHAT_KEY_PATH: Optional[str] = None
    WECHAT_NOTIFY_URL: Optional[str] = None
    
    # 支付配置 - 易支付（彩虹易支付/通用易支付）
    EPAY_URL: str = ""  # 易支付网关地址，如 https://pay.example.com
    EPAY_PID: str = ""  # 商户ID
    EPAY_KEY: str = ""  # 商户密钥
    EPAY_NOTIFY_URL: Optional[str] = None  # 异步通知地址
    EPAY_RETURN_URL: Optional[str] = None  # 同步跳转地址
    
    # 会员价格 (分)
    VIP_PRICE_MONTHLY: int = 2900  # 29元
    VIP_PRICE_QUARTERLY: int = 7900  # 79元
    VIP_PRICE_YEARLY: int = 19900  # 199元
    VIP_PRICE_LIFETIME: int = 49900  # 499元
    
    # 邀请奖励
    INVITE_REWARD_DAYS: int = 7  # 邀请一人送7天VIP
    
    # 监控配置
    PROMETHEUS_PORT: int = 9090
    
    # 邮件配置 (SMTP)
    SMTP_HOST: str = "smtp.qq.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_SSL: bool = True
    EMAIL_FROM_NAME: str = "VOD平台"
    EMAIL_FROM_EMAIL: str = ""

    @field_validator('SECRET_KEY', 'JWT_SECRET_KEY', mode='before')
    @classmethod
    def validate_or_generate_secrets(cls, v, info):
        """验证密钥，开发环境自动生成，生产环境必须配置"""
        dangerous_defaults = [
            'your-super-secret-key-change-in-production',
            'jwt-secret-key-change-in-production',
            'secret', 'password', '123456', ''
        ]
        
        env = os.getenv('ENVIRONMENT', 'development')
        
        if v in dangerous_defaults or not v:
            if env == 'production':
                raise ValueError(
                    f"生产环境必须设置安全的 {info.field_name}！"
                    f"请在 .env 文件中配置，可使用: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
                )
            # 开发环境自动生成
            return secrets.token_urlsafe(32)
        
        if len(v) < 32 and env == 'production':
            raise ValueError(f"{info.field_name} 长度至少需要32个字符")
        
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        """解析 CORS 域名列表"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()

# 创建必要的目录
for dir_path in [settings.UPLOAD_DIR, settings.VIDEO_DIR, settings.THUMBNAIL_DIR, settings.HLS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# 打印启动信息
if settings.DEBUG:
    print(f"[CONFIG] Environment: {settings.ENVIRONMENT}")
    print(f"[CONFIG] Debug: {settings.DEBUG}")
    print(f"[CONFIG] CORS Origins: {settings.cors_origins_list}")

# 创建必要的目录
for dir_path in [settings.UPLOAD_DIR, settings.VIDEO_DIR, settings.THUMBNAIL_DIR, settings.HLS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

