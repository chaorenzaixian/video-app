"""
远程转码服务
将视频发送到媒体服务器进行转码
"""
import os
import aiohttp
import asyncio
import logging
import secrets
from typing import Optional
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

# 远程转码服务配置
TRANSCODE_SERVER_URL = "http://104.143.33.52:8001"
CALLBACK_TOKEN_PREFIX = "transcode_"


class RemoteTranscoder:
    """远程转码服务客户端"""
    
    # 存储回调令牌
    _pending_callbacks: dict = {}
    
    @staticmethod
    def generate_callback_token(video_id: int) -> str:
        """生成回调令牌"""
        token = f"{CALLBACK_TOKEN_PREFIX}{video_id}_{secrets.token_hex(16)}"
        RemoteTranscoder._pending_callbacks[video_id] = token
        return token
    
    @staticmethod
    def verify_callback_token(video_id: int, token: str) -> bool:
        """验证回调令牌"""
        expected_token = RemoteTranscoder._pending_callbacks.get(video_id)
        if expected_token and expected_token == token:
            del RemoteTranscoder._pending_callbacks[video_id]
            return True
        return False
    
    @staticmethod
    async def send_for_transcoding(video_id: int, file_path: str) -> dict:
        """
        发送视频到远程服务器进行转码
        
        Args:
            video_id: 视频ID
            file_path: 本地视频文件路径
            
        Returns:
            dict: {"success": bool, "message": str}
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.error(f"视频 {video_id} 文件不存在: {file_path}")
            return {"success": False, "message": "文件不存在"}
        
        # 生成回调令牌
        callback_token = RemoteTranscoder.generate_callback_token(video_id)
        
        try:
            logger.info(f"视频 {video_id} 开始上传到远程转码服务器...")
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            logger.info(f"视频 {video_id} 文件大小: {file_size_mb:.1f}MB")
            
            # 设置超时（根据文件大小动态调整）
            # 每100MB给10分钟上传时间
            timeout_minutes = max(10, int(file_size_mb / 100) * 10)
            timeout = aiohttp.ClientTimeout(total=timeout_minutes * 60)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # 准备表单数据
                data = aiohttp.FormData()
                data.add_field('video_id', str(video_id))
                data.add_field('callback_token', callback_token)
                
                # 添加视频文件
                data.add_field(
                    'video',
                    open(file_path, 'rb'),
                    filename=os.path.basename(file_path),
                    content_type='video/mp4'
                )
                
                # 发送请求
                async with session.post(
                    f"{TRANSCODE_SERVER_URL}/api/transcode",
                    data=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"视频 {video_id} 已提交到远程转码: {result}")
                        return {"success": True, "message": "视频已提交转码"}
                    else:
                        error_text = await response.text()
                        logger.error(f"视频 {video_id} 提交转码失败: {response.status} - {error_text}")
                        return {"success": False, "message": f"提交失败: {response.status}"}
                        
        except asyncio.TimeoutError:
            logger.error(f"视频 {video_id} 上传超时")
            return {"success": False, "message": "上传超时"}
        except Exception as e:
            logger.error(f"视频 {video_id} 上传异常: {e}")
            return {"success": False, "message": str(e)}
    
    @staticmethod
    async def check_server_status() -> bool:
        """检查远程转码服务器状态"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{TRANSCODE_SERVER_URL}/api/health",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return True
        except:
            pass
        return False


# 用于向后兼容的函数
async def send_to_remote_transcoder(video_id: int, file_path: str) -> dict:
    """发送视频到远程转码服务器"""
    return await RemoteTranscoder.send_for_transcoding(video_id, file_path)

