"""
Windows 转码服务器上传服务
负责将视频直接上传到 Windows 转码服务器
"""
import os
import asyncio
import aiohttp
import logging
from typing import Optional

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.video import Video, VideoStatus
from sqlalchemy import select

logger = logging.getLogger(__name__)

# Windows 转码服务器配置
TRANSCODE_SERVER_HOST = os.getenv("TRANSCODE_SERVER_HOST", "198.176.60.121")
TRANSCODE_SERVER_PORT = os.getenv("TRANSCODE_SERVER_PORT", "5000")
TRANSCODE_API_KEY = os.getenv("TRANSCODE_API_KEY", "vYTWoms4FKOqySca1jCLtNHRVz3BAI6U")

# 是否启用直接上传到转码服务器
DIRECT_UPLOAD_ENABLED = os.getenv("DIRECT_UPLOAD_ENABLED", "true").lower() == "true"


class WindowsTranscodeService:
    """Windows 转码服务器上传服务"""
    
    @staticmethod
    def is_enabled() -> bool:
        """检查直接上传是否启用"""
        return DIRECT_UPLOAD_ENABLED
    
    @staticmethod
    def get_upload_url() -> str:
        """获取上传URL"""
        return f"http://{TRANSCODE_SERVER_HOST}:{TRANSCODE_SERVER_PORT}/upload"
    
    @staticmethod
    async def upload_to_transcode_server(video_id: int, file_content: bytes, filename: str) -> dict:
        """
        直接上传视频到转码服务器
        
        Args:
            video_id: 视频ID
            file_content: 文件内容
            filename: 原始文件名
            
        Returns:
            dict: 上传结果
        """
        if not DIRECT_UPLOAD_ENABLED:
            return {"success": False, "error": "Direct upload not enabled"}
        
        upload_url = f"http://{TRANSCODE_SERVER_HOST}:{TRANSCODE_SERVER_PORT}/upload"
        
        try:
            logger.info(f"[Transcode] 开始上传到转码服务器: video_id={video_id}, size={len(file_content)/1024/1024:.2f}MB")
            
            # 准备表单数据
            form_data = aiohttp.FormData()
            form_data.add_field('file', file_content, filename=filename, content_type='video/mp4')
            form_data.add_field('video_id', str(video_id))
            
            # 发送请求
            timeout = aiohttp.ClientTimeout(total=3600)  # 1小时超时（大文件）
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    upload_url,
                    data=form_data,
                    headers={"X-API-Key": TRANSCODE_API_KEY}
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200 and result.get("success"):
                        logger.info(f"[Transcode] 上传成功: video_id={video_id}")
                        return {
                            "success": True,
                            "filename": result.get("filename"),
                            "message": "视频已上传到转码服务器，等待处理"
                        }
                    else:
                        error = result.get("error", "Unknown error")
                        logger.error(f"[Transcode] 上传失败: {error}")
                        return {"success": False, "error": error}
                        
        except asyncio.TimeoutError:
            logger.error(f"[Transcode] 上传超时: video_id={video_id}")
            return {"success": False, "error": "Upload timeout"}
        except aiohttp.ClientError as e:
            logger.error(f"[Transcode] 网络错误: {e}")
            return {"success": False, "error": f"Network error: {str(e)}"}
        except Exception as e:
            logger.error(f"[Transcode] 上传异常: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def check_server_status() -> dict:
        """
        检查转码服务器状态
        
        Returns:
            dict: 服务器状态
        """
        try:
            url = f"http://{TRANSCODE_SERVER_HOST}:{TRANSCODE_SERVER_PORT}/status"
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "online": True,
                            "host": TRANSCODE_SERVER_HOST,
                            **data
                        }
                    else:
                        return {"online": False, "error": f"HTTP {response.status}"}
                        
        except Exception as e:
            return {"online": False, "error": str(e)}
    
    @staticmethod
    async def health_check() -> bool:
        """
        健康检查
        
        Returns:
            bool: 服务器是否在线
        """
        try:
            url = f"http://{TRANSCODE_SERVER_HOST}:{TRANSCODE_SERVER_PORT}/health"
            timeout = aiohttp.ClientTimeout(total=5)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    return response.status == 200
        except:
            return False
