"""
GPU 转码回调 API
接收 GPU 服务器的转码完成通知，更新视频状态

架构说明:
转码服务器 (198.176.60.121) 完成以下工作后调用此接口:
1. 视频转码 (GPU加速)
2. 生成封面 (WebP格式)
3. 生成预览 (10秒短视频)
4. 上传全部文件到主服务器
5. 调用此回调更新数据库
"""
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging

from app.core.database import AsyncSessionLocal
from app.models.video import Video, VideoStatus
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter()

# 转码回调密钥 (从环境变量读取)
import os
TRANSCODE_SECRET_KEY = os.getenv("TRANSCODE_SECRET_KEY", "vYTWoms4FKOqySca1jCLtNHRVz3BAI6U")


class TranscodeCallbackRequest(BaseModel):
    """转码回调请求"""
    video_id: int
    status: str  # success / failed
    thumbnail_url: Optional[str] = None  # 封面图片URL (WebP)
    preview_url: Optional[str] = None    # 预览视频URL (MP4)
    hls_url: Optional[str] = None        # 转码后视频URL (MP4/HLS)
    duration: Optional[float] = None     # 视频时长（秒）
    error_message: Optional[str] = None


@router.post("/transcode-callback")
async def transcode_callback(
    request: TranscodeCallbackRequest,
    x_transcode_key: str = Header(None, alias="X-Transcode-Key")
):
    """
    GPU 转码完成回调
    
    由转码服务器在处理完成后调用，更新视频的：
    - cover_url (封面图片，WebP格式)
    - preview_url (预览视频，10秒MP4)
    - hls_url (转码后视频URL)
    - duration (视频时长)
    - status (发布状态)
    
    请求示例:
    {
        "video_id": 123,
        "status": "success",
        "thumbnail_url": "/uploads/thumbnails/123.webp",
        "preview_url": "/uploads/previews/123_preview.mp4",
        "hls_url": "/uploads/videos/123.mp4",
        "duration": 180.5
    }
    """
    # 验证密钥
    if x_transcode_key != TRANSCODE_SECRET_KEY:
        logger.warning(f"转码回调密钥验证失败: video_id={request.video_id}")
        raise HTTPException(status_code=403, detail="Invalid transcode key")
    
    logger.info(f"收到转码回调: video_id={request.video_id}, status={request.status}")
    logger.info(f"  封面: {request.thumbnail_url}")
    logger.info(f"  预览: {request.preview_url}")
    logger.info(f"  视频: {request.hls_url}")
    
    async with AsyncSessionLocal() as db:
        try:
            # 查找视频
            result = await db.execute(
                select(Video).where(Video.id == request.video_id)
            )
            video = result.scalar_one_or_none()
            
            if not video:
                logger.error(f"视频不存在: video_id={request.video_id}")
                raise HTTPException(status_code=404, detail="Video not found")
            
            if request.status == "success":
                # 更新视频信息
                if request.thumbnail_url:
                    video.cover_url = request.thumbnail_url
                    logger.info(f"  更新封面URL: {request.thumbnail_url}")
                    
                if request.preview_url:
                    video.preview_url = request.preview_url
                    logger.info(f"  更新预览URL: {request.preview_url}")
                    
                if request.hls_url:
                    video.hls_url = request.hls_url
                    logger.info(f"  更新视频URL: {request.hls_url}")
                
                if request.duration:
                    video.duration = request.duration
                    logger.info(f"  更新时长: {request.duration}秒")
                
                # 转码完成后设置为待审核状态（未发布），需要管理员手动发布
                video.status = VideoStatus.REVIEWING
                # 不设置 published_at，等管理员发布时再设置
                
                logger.info(f"视频转码成功，等待审核: video_id={request.video_id}")
            else:
                # 转码失败
                video.status = VideoStatus.FAILED
                logger.error(f"视频转码失败: video_id={request.video_id}, error={request.error_message}")
            
            await db.commit()
            
            return {
                "success": True,
                "video_id": request.video_id,
                "status": video.status.value,
                "cover_url": video.cover_url,
                "preview_url": video.preview_url,
                "hls_url": video.hls_url
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"处理转码回调失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/transcode-status/{video_id}")
async def get_transcode_status(video_id: int):
    """
    查询视频转码状态
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Video).where(Video.id == video_id)
        )
        video = result.scalar_one_or_none()
        
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        return {
            "video_id": video_id,
            "status": video.status.value,
            "cover_url": video.cover_url,
            "preview_url": video.preview_url,
            "hls_url": video.hls_url,
            "published_at": video.published_at.isoformat() if video.published_at else None
        }


@router.get("/gpu-status")
async def get_gpu_server_status():
    """
    获取 GPU 服务器状态
    """
    try:
        from app.services.gpu_transcode_service import GPUTranscodeService
        
        status = await GPUTranscodeService.check_gpu_server()
        queue = await GPUTranscodeService.get_transcode_queue()
        
        return {
            "enabled": GPUTranscodeService.is_enabled(),
            "server": status,
            "processing_queue": queue
        }
    except ImportError:
        return {
            "enabled": False,
            "error": "GPU transcode service not available"
        }
    except Exception as e:
        return {
            "enabled": False,
            "error": str(e)
        }
