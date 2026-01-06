"""
水印管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from pydantic import BaseModel
import os
import uuid

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_admin_user
from app.models.user import User
from app.models.watermark import WatermarkConfig

router = APIRouter(prefix="/watermark", tags=["水印管理"])


# ========== Schemas ==========

class WatermarkConfigCreate(BaseModel):
    """创建水印配置"""
    name: str
    watermark_type: str = "image"  # image/text/user_id
    
    # 图片水印
    image_url: Optional[str] = None
    image_opacity: float = 0.5
    image_scale: float = 0.1
    
    # 文字水印
    text_template: Optional[str] = None
    font_size: int = 24
    font_color: str = "white"
    text_opacity: float = 0.3
    
    # 位置
    position: str = "bottom_right"
    offset_x: int = 20
    offset_y: int = 20
    
    # 动态
    is_moving: bool = False
    move_speed_x: int = 30
    move_speed_y: int = 20
    
    # 应用范围
    apply_to: str = "all"
    priority: int = 0


class WatermarkConfigUpdate(BaseModel):
    """更新水印配置"""
    name: Optional[str] = None
    watermark_type: Optional[str] = None
    image_url: Optional[str] = None
    image_opacity: Optional[float] = None
    image_scale: Optional[float] = None
    text_template: Optional[str] = None
    font_size: Optional[int] = None
    font_color: Optional[str] = None
    text_opacity: Optional[float] = None
    position: Optional[str] = None
    offset_x: Optional[int] = None
    offset_y: Optional[int] = None
    is_moving: Optional[bool] = None
    move_speed_x: Optional[int] = None
    move_speed_y: Optional[int] = None
    apply_to: Optional[str] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class WatermarkConfigResponse(BaseModel):
    """水印配置响应"""
    id: int
    name: str
    watermark_type: str
    image_url: Optional[str]
    image_opacity: float
    image_scale: float
    text_template: Optional[str]
    font_size: int
    font_color: str
    text_opacity: float
    position: str
    offset_x: int
    offset_y: int
    is_moving: bool
    move_speed_x: int
    move_speed_y: int
    apply_to: str
    priority: int
    is_active: bool
    
    class Config:
        from_attributes = True


# ========== API Endpoints ==========

@router.get("/configs")
async def list_watermark_configs(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取所有水印配置（管理员）"""
    result = await db.execute(
        select(WatermarkConfig).order_by(WatermarkConfig.priority)
    )
    configs = result.scalars().all()
    
    return {
        "items": [
            {
                "id": c.id,
                "name": c.name,
                "watermark_type": c.watermark_type,
                "image_url": c.image_url,
                "image_opacity": c.image_opacity,
                "image_scale": c.image_scale,
                "text_template": c.text_template,
                "font_size": c.font_size,
                "font_color": c.font_color,
                "text_opacity": c.text_opacity,
                "position": c.position,
                "offset_x": c.offset_x,
                "offset_y": c.offset_y,
                "is_moving": c.is_moving,
                "move_speed_x": c.move_speed_x,
                "move_speed_y": c.move_speed_y,
                "apply_to": c.apply_to,
                "priority": c.priority,
                "is_active": c.is_active,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in configs
        ]
    }


@router.post("/configs")
async def create_watermark_config(
    config_data: WatermarkConfigCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """创建水印配置（管理员）"""
    config = WatermarkConfig(
        name=config_data.name,
        watermark_type=config_data.watermark_type,
        image_url=config_data.image_url,
        image_opacity=config_data.image_opacity,
        image_scale=config_data.image_scale,
        text_template=config_data.text_template,
        font_size=config_data.font_size,
        font_color=config_data.font_color,
        text_opacity=config_data.text_opacity,
        position=config_data.position,
        offset_x=config_data.offset_x,
        offset_y=config_data.offset_y,
        is_moving=config_data.is_moving,
        move_speed_x=config_data.move_speed_x,
        move_speed_y=config_data.move_speed_y,
        apply_to=config_data.apply_to,
        priority=config_data.priority,
        is_active=True
    )
    
    db.add(config)
    await db.commit()
    await db.refresh(config)
    
    return {
        "id": config.id,
        "message": "水印配置创建成功"
    }


@router.put("/configs/{config_id}")
async def update_watermark_config(
    config_id: int,
    config_data: WatermarkConfigUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新水印配置（管理员）"""
    result = await db.execute(
        select(WatermarkConfig).where(WatermarkConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="水印配置不存在"
        )
    
    update_data = config_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(config, key, value)
    
    await db.commit()
    
    return {"message": "水印配置更新成功"}


@router.delete("/configs/{config_id}")
async def delete_watermark_config(
    config_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """删除水印配置（管理员）"""
    result = await db.execute(
        select(WatermarkConfig).where(WatermarkConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="水印配置不存在"
        )
    
    await db.delete(config)
    await db.commit()
    
    return {"message": "水印配置删除成功"}


@router.post("/configs/{config_id}/toggle")
async def toggle_watermark_config(
    config_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """切换水印配置状态（管理员）"""
    result = await db.execute(
        select(WatermarkConfig).where(WatermarkConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="水印配置不存在"
        )
    
    config.is_active = not config.is_active
    await db.commit()
    
    return {
        "message": "状态已切换",
        "is_active": config.is_active
    }


@router.post("/upload-image")
async def upload_watermark_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_admin_user)
):
    """上传水印图片（管理员，自动转WebP优化）"""
    from app.services.image_service import ImageService
    
    # 检查文件类型
    if file.content_type not in ImageService.SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持 PNG、JPG、WebP、GIF、BMP 格式"
        )
    
    # 读取文件内容
    content = await file.read()
    
    # 验证图片
    valid, error = ImageService.validate_image(content, file.content_type)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    try:
        # 使用图片服务处理并保存
        result = await ImageService.save_image(
            content=content,
            subdir="site",
            filename=f"watermark_{uuid.uuid4().hex[:8]}",
            convert_webp=True
        )
        return {"url": result["url"], "message": "上传成功", "optimized": ImageService.is_available()}
    except Exception:
        # 降级处理
        watermark_dir = os.path.join(settings.UPLOAD_DIR, "site")
        os.makedirs(watermark_dir, exist_ok=True)
        file_ext = os.path.splitext(file.filename)[1].lower() or ".png"
        filename = f"watermark_{uuid.uuid4().hex[:8]}{file_ext}"
        file_path = os.path.join(watermark_dir, filename)
        with open(file_path, "wb") as f:
            f.write(content)
        return {"url": f"/uploads/site/{filename}", "message": "上传成功", "optimized": False}


@router.post("/preview")
async def preview_watermark(
    config_id: int,
    video_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    预览水印效果（生成带水印的预览帧）
    """
    from app.models.video import Video
    from app.services.watermark_service import WatermarkService, WatermarkConfig as WMConfig
    import subprocess
    import tempfile
    
    # 获取水印配置
    result = await db.execute(
        select(WatermarkConfig).where(WatermarkConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="水印配置不存在"
        )
    
    # 获取视频
    result = await db.execute(
        select(Video).where(Video.id == video_id)
    )
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频不存在"
        )
    
    # 获取视频文件路径
    video_path = video.original_url
    if not video_path or not os.path.exists(video_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="视频文件不存在"
        )
    
    # 创建水印配置对象
    wm_config = WMConfig(
        watermark_type=config.watermark_type,
        image_path=os.path.join(settings.UPLOAD_DIR, config.image_url.replace("/uploads/", "")) if config.image_url else None,
        image_opacity=config.image_opacity,
        image_scale=config.image_scale,
        text=config.text_template,
        font_size=config.font_size,
        font_color=config.font_color,
        text_opacity=config.text_opacity,
        position=config.position,
        offset_x=config.offset_x,
        offset_y=config.offset_y,
        is_moving=config.is_moving,
        move_speed_x=config.move_speed_x,
        move_speed_y=config.move_speed_y
    )
    
    # 生成预览帧
    preview_dir = os.path.join(settings.UPLOAD_DIR, "watermark_preview")
    os.makedirs(preview_dir, exist_ok=True)
    
    preview_filename = f"preview_{config_id}_{video_id}.jpg"
    preview_path = os.path.join(preview_dir, preview_filename)
    
    # 使用 FFmpeg 生成带水印的单帧
    try:
        # 先截取一帧
        temp_frame = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        subprocess.run([
            "ffmpeg", "-y",
            "-ss", "00:00:05",
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            temp_frame.name
        ], capture_output=True, timeout=30)
        
        # 应用水印
        success = await WatermarkService.apply_watermark(
            temp_frame.name,
            preview_path,
            wm_config
        )
        
        # 清理临时文件
        os.unlink(temp_frame.name)
        
        if success and os.path.exists(preview_path):
            return {
                "preview_url": f"/uploads/watermark_preview/{preview_filename}",
                "message": "预览生成成功"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="预览生成失败"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"预览生成失败: {str(e)}"
        )


