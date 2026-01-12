"""
视频处理异步任务
"""
import os
import logging
import subprocess
from typing import Optional
from celery import shared_task

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_video_task(
    self,
    video_id: int,
    input_path: str,
    output_path: str,
    resolution: str = "720p"
) -> dict:
    """
    异步处理视频转码
    
    Args:
        video_id: 视频ID
        input_path: 输入文件路径
        output_path: 输出文件路径
        resolution: 目标分辨率
        
    Returns:
        处理结果
    """
    try:
        logger.info(f"开始处理视频 {video_id}: {input_path} -> {output_path}")
        
        # 分辨率配置
        resolution_map = {
            "480p": "-vf scale=-2:480",
            "720p": "-vf scale=-2:720",
            "1080p": "-vf scale=-2:1080",
        }
        
        scale_filter = resolution_map.get(resolution, resolution_map["720p"])
        
        # FFmpeg 命令
        cmd = [
            "ffmpeg", "-i", input_path,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            scale_filter,
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            "-y",
            output_path
        ]
        
        # 执行转码
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1小时超时
        )
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")
        
        # 获取输出文件大小
        file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        
        logger.info(f"视频 {video_id} 处理完成，文件大小: {file_size}")
        
        return {
            "success": True,
            "video_id": video_id,
            "output_path": output_path,
            "file_size": file_size
        }
        
    except subprocess.TimeoutExpired:
        logger.error(f"视频 {video_id} 处理超时")
        raise self.retry(exc=Exception("处理超时"))
        
    except Exception as e:
        logger.error(f"视频 {video_id} 处理失败: {e}")
        raise self.retry(exc=e)


@celery_app.task(bind=True, max_retries=3)
def generate_thumbnail_task(
    self,
    video_id: int,
    video_path: str,
    output_path: str,
    timestamp: str = "00:00:05"
) -> dict:
    """
    异步生成视频缩略图
    
    Args:
        video_id: 视频ID
        video_path: 视频文件路径
        output_path: 缩略图输出路径
        timestamp: 截取时间点
    """
    try:
        logger.info(f"生成视频 {video_id} 缩略图")
        
        cmd = [
            "ffmpeg", "-i", video_path,
            "-ss", timestamp,
            "-vframes", "1",
            "-vf", "scale=320:-1",
            "-y",
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")
        
        return {
            "success": True,
            "video_id": video_id,
            "thumbnail_path": output_path
        }
        
    except Exception as e:
        logger.error(f"缩略图生成失败: {e}")
        raise self.retry(exc=e)


@celery_app.task(bind=True, max_retries=2)
def extract_video_info_task(self, video_path: str) -> dict:
    """
    异步提取视频信息
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        视频信息（时长、分辨率等）
    """
    try:
        import json
        
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            raise Exception(f"FFprobe error: {result.stderr}")
        
        info = json.loads(result.stdout)
        
        # 提取关键信息
        duration = float(info.get("format", {}).get("duration", 0))
        
        video_stream = next(
            (s for s in info.get("streams", []) if s.get("codec_type") == "video"),
            {}
        )
        
        return {
            "success": True,
            "duration": duration,
            "width": video_stream.get("width", 0),
            "height": video_stream.get("height", 0),
            "codec": video_stream.get("codec_name", ""),
            "bitrate": int(info.get("format", {}).get("bit_rate", 0))
        }
        
    except Exception as e:
        logger.error(f"提取视频信息失败: {e}")
        raise self.retry(exc=e)
