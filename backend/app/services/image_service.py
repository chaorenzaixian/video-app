"""
图片处理服务 - 支持压缩、转WebP、生成缩略图
"""
import os
import uuid
from typing import Optional, Tuple, List
from io import BytesIO
import logging

try:
    from PIL import Image, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("Pillow 未安装，图片处理功能将受限。安装命令: pip install Pillow")

from app.core.config import settings

logger = logging.getLogger(__name__)


class ImageSize:
    """图片尺寸定义"""
    THUMBNAIL = (150, 150)    # 缩略图
    SMALL = (320, 320)        # 小图
    MEDIUM = (640, 640)       # 中图
    LARGE = (1280, 1280)      # 大图
    ORIGINAL = None           # 原图


class ImageService:
    """图片处理服务"""
    
    # 支持的输入格式
    SUPPORTED_FORMATS = {'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'}
    
    # WebP 压缩质量
    WEBP_QUALITY = 85
    
    # 最大文件大小 (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    @staticmethod
    def is_available() -> bool:
        """检查 Pillow 是否可用"""
        return PIL_AVAILABLE
    
    @staticmethod
    def validate_image(content: bytes, content_type: str) -> Tuple[bool, str]:
        """
        验证图片
        返回: (是否有效, 错误信息)
        """
        if content_type not in ImageService.SUPPORTED_FORMATS:
            return False, f"不支持的图片格式: {content_type}"
        
        if len(content) > ImageService.MAX_FILE_SIZE:
            return False, f"图片大小超过限制 ({ImageService.MAX_FILE_SIZE // 1024 // 1024}MB)"
        
        return True, ""
    
    @staticmethod
    def process_image(
        content: bytes,
        convert_webp: bool = True,
        quality: int = 85,
        max_size: Optional[Tuple[int, int]] = None,
        keep_animation: bool = True
    ) -> Tuple[bytes, str]:
        """
        处理图片
        
        Args:
            content: 原始图片字节
            convert_webp: 是否转换为 WebP
            quality: 压缩质量 (1-100)
            max_size: 最大尺寸 (width, height)，超过则等比缩放
            keep_animation: 是否保留动图
        
        Returns:
            (处理后的字节, 文件扩展名)
        """
        if not PIL_AVAILABLE:
            # Pillow 不可用，返回原图
            return content, ".jpg"
        
        try:
            img = Image.open(BytesIO(content))
            
            # 检查是否为动图
            is_animated = getattr(img, 'is_animated', False)
            
            # 动图且需要保留动画
            if is_animated and keep_animation:
                if convert_webp:
                    # 转换动图为 WebP
                    output = BytesIO()
                    img.save(
                        output, 
                        format='WEBP', 
                        save_all=True,
                        quality=quality,
                        method=4  # 压缩方法 (0-6, 6最慢但最小)
                    )
                    return output.getvalue(), ".webp"
                else:
                    return content, ".gif"
            
            # 处理不同图片模式
            if img.mode == 'RGBA' or (img.mode == 'P' and 'transparency' in img.info):
                # 保留透明通道
                if img.mode == 'P':
                    img = img.convert('RGBA')
                # RGBA模式直接保存为webp，保留透明度
            elif img.mode in ('LA', 'P'):
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB' and img.mode != 'RGBA':
                img = img.convert('RGB')
            
            # 自动旋转（根据 EXIF）
            img = ImageOps.exif_transpose(img)
            
            # 缩放
            if max_size:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 输出
            output = BytesIO()
            if convert_webp:
                img.save(output, format='WEBP', quality=quality, method=4, lossless=(img.mode == 'RGBA'))
                return output.getvalue(), ".webp"
            else:
                img.save(output, format='JPEG', quality=quality, optimize=True)
                return output.getvalue(), ".jpg"
                
        except Exception as e:
            logger.error(f"图片处理失败: {e}")
            return content, ".jpg"
    
    @staticmethod
    def generate_thumbnails(
        content: bytes,
        sizes: List[Tuple[int, int]] = None
    ) -> dict:
        """
        生成多尺寸缩略图
        
        Args:
            content: 原始图片字节
            sizes: 尺寸列表，默认生成 small/medium/large
        
        Returns:
            {
                "small": bytes,
                "medium": bytes,
                "large": bytes
            }
        """
        if not PIL_AVAILABLE:
            return {}
        
        if sizes is None:
            sizes = [
                ("small", ImageSize.SMALL),
                ("medium", ImageSize.MEDIUM),
                ("large", ImageSize.LARGE),
            ]
        
        result = {}
        
        try:
            img = Image.open(BytesIO(content))
            
            # 处理不同图片模式，保留透明通道
            has_alpha = False
            if img.mode == 'RGBA' or (img.mode == 'P' and 'transparency' in img.info):
                if img.mode == 'P':
                    img = img.convert('RGBA')
                has_alpha = True
            elif img.mode in ('LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB' and img.mode != 'RGBA':
                img = img.convert('RGB')
            
            # 自动旋转
            img = ImageOps.exif_transpose(img)
            
            for name, size in sizes:
                thumb = img.copy()
                thumb.thumbnail(size, Image.Resampling.LANCZOS)
                
                output = BytesIO()
                thumb.save(output, format='WEBP', quality=80, method=4, lossless=has_alpha)
                result[name] = output.getvalue()
                
        except Exception as e:
            logger.error(f"生成缩略图失败: {e}")
        
        return result
    
    @staticmethod
    async def save_image(
        content: bytes,
        subdir: str = "images",
        filename: str = None,
        convert_webp: bool = True,
        generate_thumbs: bool = False,
        max_size: Tuple[int, int] = None
    ) -> dict:
        """
        保存图片（完整流程）
        
        Args:
            content: 图片字节
            subdir: 子目录
            filename: 文件名（不含扩展名），为空则自动生成
            convert_webp: 是否转换为 WebP
            generate_thumbs: 是否生成缩略图
            max_size: 最大尺寸
        
        Returns:
            {
                "url": "/uploads/images/xxx.webp",
                "filename": "xxx.webp",
                "size": 12345,
                "thumbnails": {
                    "small": "/uploads/images/xxx_small.webp",
                    "medium": "/uploads/images/xxx_medium.webp"
                }
            }
        """
        # 生成文件名
        if not filename:
            filename = uuid.uuid4().hex
        
        # 处理图片
        processed, ext = ImageService.process_image(
            content,
            convert_webp=convert_webp,
            max_size=max_size
        )
        
        # 确保目录存在
        save_dir = os.path.join(settings.UPLOAD_DIR, subdir)
        os.makedirs(save_dir, exist_ok=True)
        
        # 保存主图
        full_filename = f"{filename}{ext}"
        filepath = os.path.join(save_dir, full_filename)
        
        with open(filepath, 'wb') as f:
            f.write(processed)
        
        result = {
            "url": f"/uploads/{subdir}/{full_filename}",
            "filename": full_filename,
            "size": len(processed),
            "thumbnails": {}
        }
        
        # 生成缩略图
        if generate_thumbs:
            thumbs = ImageService.generate_thumbnails(content)
            for size_name, thumb_content in thumbs.items():
                thumb_filename = f"{filename}_{size_name}.webp"
                thumb_path = os.path.join(save_dir, thumb_filename)
                
                with open(thumb_path, 'wb') as f:
                    f.write(thumb_content)
                
                result["thumbnails"][size_name] = f"/uploads/{subdir}/{thumb_filename}"
        
        return result
    
    @staticmethod
    def get_image_info(content: bytes) -> dict:
        """获取图片信息"""
        if not PIL_AVAILABLE:
            return {"size": len(content)}
        
        try:
            img = Image.open(BytesIO(content))
            return {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode,
                "size": len(content),
                "is_animated": getattr(img, 'is_animated', False)
            }
        except Exception as e:
            return {"size": len(content), "error": str(e)}


# 便捷函数
async def process_and_save_image(
    content: bytes,
    content_type: str,
    subdir: str = "images",
    convert_webp: bool = True
) -> dict:
    """
    处理并保存图片的便捷函数
    """
    # 验证
    valid, error = ImageService.validate_image(content, content_type)
    if not valid:
        raise ValueError(error)
    
    # 保存
    return await ImageService.save_image(
        content,
        subdir=subdir,
        convert_webp=convert_webp
    )
