"""
Cloudflare R2 对象存储服务
免流量费，适合视频/图片等静态资源托管
"""
import boto3
from botocore.config import Config
import os
import uuid
from datetime import datetime
from typing import Optional

class R2Service:
    """Cloudflare R2 存储服务"""
    
    def __init__(self):
        self.account_id = os.getenv('R2_ACCOUNT_ID')
        self.access_key = os.getenv('R2_ACCESS_KEY_ID')
        self.secret_key = os.getenv('R2_SECRET_ACCESS_KEY')
        self.bucket_name = os.getenv('R2_BUCKET_NAME', 'video-app-assets')
        self.public_url = os.getenv('R2_PUBLIC_URL', '')  # 如 https://cdn.yourdomain.com
        
        self._client = None
    
    @property
    def is_configured(self) -> bool:
        """检查是否已配置R2"""
        return all([self.account_id, self.access_key, self.secret_key])
    
    @property
    def client(self):
        """获取S3客户端（R2兼容S3 API）"""
        if not self._client and self.is_configured:
            self._client = boto3.client(
                's3',
                endpoint_url=f'https://{self.account_id}.r2.cloudflarestorage.com',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=Config(signature_version='s3v4'),
                region_name='auto'
            )
        return self._client
    
    def generate_key(self, subdir: str, filename: str) -> str:
        """生成存储路径"""
        ext = os.path.splitext(filename)[1] or ''
        date_prefix = datetime.now().strftime('%Y/%m/%d')
        unique_name = f"{uuid.uuid4().hex[:12]}{ext}"
        return f"{subdir}/{date_prefix}/{unique_name}"
    
    async def upload_file(
        self,
        content: bytes,
        filename: str,
        subdir: str = "uploads",
        content_type: Optional[str] = None
    ) -> dict:
        """
        上传文件到R2
        
        Args:
            content: 文件内容
            filename: 原始文件名
            subdir: 子目录 (videos/images/community等)
            content_type: MIME类型
        
        Returns:
            {"key": "存储路径", "url": "公开访问URL"}
        """
        if not self.is_configured:
            raise Exception("R2未配置，请设置环境变量")
        
        key = self.generate_key(subdir, filename)
        
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        
        # 上传到R2
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=content,
            **extra_args
        )
        
        # 生成公开URL
        if self.public_url:
            url = f"{self.public_url.rstrip('/')}/{key}"
        else:
            url = f"https://{self.bucket_name}.{self.account_id}.r2.cloudflarestorage.com/{key}"
        
        return {"key": key, "url": url}
    
    async def delete_file(self, key: str) -> bool:
        """删除文件"""
        if not self.is_configured:
            return False
        
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception:
            return False
    
    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """获取预签名URL（用于私有文件临时访问）"""
        if not self.is_configured:
            return ""
        
        return self.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket_name, 'Key': key},
            ExpiresIn=expires_in
        )


# 全局实例
r2_service = R2Service()
