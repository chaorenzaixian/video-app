"""
GPU 转码服务
负责将视频推送到 GPU 服务器进行转码
"""
import os
import asyncio
import subprocess
import logging
from typing import Optional
from datetime import datetime

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.video import Video, VideoStatus
from sqlalchemy import select

logger = logging.getLogger(__name__)

# GPU 服务器配置
GPU_SERVER_HOST = os.getenv("GPU_SERVER_HOST", "149.36.0.246")
GPU_SERVER_USER = os.getenv("GPU_SERVER_USER", "ubuntu")
GPU_SERVER_WORK_DIR = os.getenv("GPU_SERVER_WORK_DIR", "/home/ubuntu/video-transcode")

# 是否启用 GPU 转码 (可通过环境变量控制)
GPU_TRANSCODE_ENABLED = os.getenv("GPU_TRANSCODE_ENABLED", "false").lower() == "true"


class GPUTranscodeService:
    """GPU 转码服务"""
    
    @staticmethod
    def is_enabled() -> bool:
        """检查 GPU 转码是否启用"""
        return GPU_TRANSCODE_ENABLED
    
    @staticmethod
    async def push_to_gpu(video_id: int, file_path: str) -> bool:
        """
        将视频推送到 GPU 服务器进行转码
        
        Args:
            video_id: 视频ID
            file_path: 本地视频文件路径
            
        Returns:
            bool: 是否成功推送
        """
        if not GPU_TRANSCODE_ENABLED:
            logger.info(f"GPU转码未启用，跳过: video_id={video_id}")
            return False
        
        try:
            logger.info(f"[GPU] 开始推送视频到GPU服务器: video_id={video_id}")
            
            # 1. 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"[GPU] 视频文件不存在: {file_path}")
                return False
            
            # 2. 获取文件名
            filename = os.path.basename(file_path)
            remote_path = f"{GPU_SERVER_WORK_DIR}/uploads/{video_id}_{filename}"
            
            # 3. 使用 rsync 推送文件到 GPU 服务器
            rsync_cmd = [
                "rsync", "-avz", "--progress",
                file_path,
                f"{GPU_SERVER_USER}@{GPU_SERVER_HOST}:{remote_path}"
            ]
            
            logger.info(f"[GPU] 执行: {' '.join(rsync_cmd)}")
            
            # 异步执行 rsync
            process = await asyncio.create_subprocess_exec(
                *rsync_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"[GPU] rsync 失败: {stderr.decode()}")
                return False
            
            logger.info(f"[GPU] 文件推送成功: {remote_path}")
            
            # 4. 触发 GPU 服务器开始转码
            ssh_cmd = [
                "ssh", f"{GPU_SERVER_USER}@{GPU_SERVER_HOST}",
                f"cd {GPU_SERVER_WORK_DIR} && nohup ./transcode.sh process {video_id} {remote_path} > logs/video_{video_id}.log 2>&1 &"
            ]
            
            logger.info(f"[GPU] 触发转码: video_id={video_id}")
            
            process = await asyncio.create_subprocess_exec(
                *ssh_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"[GPU] 触发转码失败: {stderr.decode()}")
                return False
            
            logger.info(f"[GPU] 转码任务已提交: video_id={video_id}")
            
            # 5. 更新视频状态为 GPU 处理中
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Video).where(Video.id == video_id)
                )
                video = result.scalar_one_or_none()
                if video:
                    video.status = VideoStatus.PROCESSING
                    await db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"[GPU] 推送失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    async def check_gpu_server() -> dict:
        """
        检查 GPU 服务器状态
        
        Returns:
            dict: 服务器状态信息
        """
        try:
            # 检查 SSH 连接
            ssh_cmd = [
                "ssh", "-o", "ConnectTimeout=5",
                f"{GPU_SERVER_USER}@{GPU_SERVER_HOST}",
                "nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *ssh_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return {
                    "status": "offline",
                    "error": stderr.decode()
                }
            
            # 解析 GPU 信息
            gpu_info = []
            for line in stdout.decode().strip().split('\n'):
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 4:
                    gpu_info.append({
                        "name": parts[0],
                        "memory_used": parts[1],
                        "memory_total": parts[2],
                        "utilization": parts[3]
                    })
            
            return {
                "status": "online",
                "host": GPU_SERVER_HOST,
                "gpus": gpu_info
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    @staticmethod
    async def get_transcode_queue() -> list:
        """
        获取 GPU 服务器上的转码队列
        
        Returns:
            list: 正在处理的视频列表
        """
        try:
            ssh_cmd = [
                "ssh", "-o", "ConnectTimeout=5",
                f"{GPU_SERVER_USER}@{GPU_SERVER_HOST}",
                f"ps aux | grep 'transcode.sh process' | grep -v grep | awk '{{print $NF}}'"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *ssh_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return []
            
            # 解析正在处理的视频ID
            processing = []
            for line in stdout.decode().strip().split('\n'):
                if line:
                    # 从路径中提取 video_id
                    parts = line.split('/')
                    for part in parts:
                        if part.startswith('video_') or part.isdigit():
                            processing.append(part)
                            break
            
            return processing
            
        except Exception as e:
            logger.error(f"获取转码队列失败: {e}")
            return []
