"""
网站设置API
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from pydantic import BaseModel
import os
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_admin_user
from app.models.user import User

router = APIRouter()


class SiteSettingsResponse(BaseModel):
    """网站设置响应"""
    site_name: str = "Soul"
    logo: Optional[str] = None
    favicon: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[str] = None
    contact_email: Optional[str] = None
    contact_qq: Optional[str] = None
    contact_telegram: Optional[str] = None
    footer_text: Optional[str] = None
    icp_number: Optional[str] = None


class SiteSettingsUpdate(BaseModel):
    """更新网站设置"""
    site_name: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[str] = None
    contact_email: Optional[str] = None
    contact_qq: Optional[str] = None
    contact_telegram: Optional[str] = None
    footer_text: Optional[str] = None
    icp_number: Optional[str] = None


# 简单的文件存储（实际可以用数据库）
SETTINGS_FILE = os.path.join(settings.UPLOAD_DIR, "site_settings.json")


def load_settings() -> dict:
    """加载设置"""
    import json
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        "site_name": "Soul",
        "logo": "",
        "favicon": "",
        "description": "精彩视频平台",
        "keywords": "视频,VIP,会员",
        "contact_email": "",
        "contact_qq": "",
        "contact_telegram": "",
        "footer_text": "",
        "icp_number": ""
    }


def save_settings(data: dict):
    """保存设置"""
    import json
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@router.get("/site", response_model=SiteSettingsResponse)
async def get_site_settings():
    """获取网站设置（公开接口）"""
    data = load_settings()
    return SiteSettingsResponse(**data)


@router.put("/site", response_model=SiteSettingsResponse)
async def update_site_settings(
    settings_in: SiteSettingsUpdate,
    current_user: User = Depends(get_admin_user)
):
    """更新网站设置（管理员）"""
    data = load_settings()
    
    # 更新非空字段
    for field, value in settings_in.dict(exclude_unset=True).items():
        if value is not None:
            data[field] = value
    
    save_settings(data)
    return SiteSettingsResponse(**data)


@router.post("/site/logo")
async def upload_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_admin_user)
):
    """上传Logo（管理员，自动转WebP优化）"""
    from app.services.image_service import ImageService
    
    # SVG不转换，其他格式转WebP
    is_svg = file.content_type == 'image/svg+xml'
    
    # 验证文件类型
    allowed_types = list(ImageService.SUPPORTED_FORMATS) + ['image/svg+xml']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="不支持的图片格式")
    
    # 读取文件内容
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小不能超过2MB")
    
    # 删除旧Logo
    data = load_settings()
    if data.get("logo"):
        old_path = os.path.join(settings.UPLOAD_DIR, data["logo"].lstrip("/uploads/"))
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except:
                pass
    
    if is_svg:
        # SVG直接保存
        ext = '.svg'
        filename = f"logo_{uuid.uuid4().hex[:8]}{ext}"
        logo_dir = os.path.join(settings.UPLOAD_DIR, "site")
        os.makedirs(logo_dir, exist_ok=True)
        filepath = os.path.join(logo_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(content)
        logo_url = f"/uploads/site/{filename}"
    else:
        # 其他格式使用图片服务处理
        try:
            result = await ImageService.save_image(
                content=content,
                subdir="site",
                filename=f"logo_{uuid.uuid4().hex[:8]}",
                convert_webp=True
            )
            logo_url = result["url"]
        except Exception:
            # 降级处理
            ext = os.path.splitext(file.filename)[1] or '.png'
            filename = f"logo_{uuid.uuid4().hex[:8]}{ext}"
            logo_dir = os.path.join(settings.UPLOAD_DIR, "site")
            os.makedirs(logo_dir, exist_ok=True)
            filepath = os.path.join(logo_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(content)
            logo_url = f"/uploads/site/{filename}"
    
    data["logo"] = logo_url
    save_settings(data)
    
    return {"logo": logo_url, "message": "上传成功"}


@router.delete("/site/logo")
async def delete_logo(
    current_user: User = Depends(get_admin_user)
):
    """删除Logo（管理员）"""
    data = load_settings()
    
    if data.get("logo"):
        # 删除文件
        old_path = os.path.join(settings.UPLOAD_DIR, data["logo"].lstrip("/uploads/"))
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except:
                pass
        
        data["logo"] = ""
        save_settings(data)
    
    return {"message": "删除成功"}


# ========== 评论区公告设置 ==========

ANNOUNCEMENT_FILE = os.path.join(settings.UPLOAD_DIR, "comment_announcement.json")

class CommentAnnouncementResponse(BaseModel):
    """评论区公告响应"""
    enabled: bool = True
    name: str = "Soul官方"
    avatar: Optional[str] = None
    content: str = ""
    updated_at: Optional[str] = None

class CommentAnnouncementUpdate(BaseModel):
    """更新评论区公告"""
    enabled: Optional[bool] = None
    name: Optional[str] = None
    avatar: Optional[str] = None
    content: Optional[str] = None


def load_announcement() -> dict:
    """加载公告设置"""
    import json
    if os.path.exists(ANNOUNCEMENT_FILE):
        try:
            with open(ANNOUNCEMENT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        "enabled": True,
        "name": "Soul官方",
        "avatar": "/images/avatars/icon_avatar_1.png",
        "content": "🔥限时\"新人永久卡\"🔥100元特惠,VIP视频💕永久免费看,消费一次终身受益,还送3次AI脱衣👇女神秒变母狗👉点击抢购👉👉👉",
        "updated_at": datetime.now().isoformat()
    }


def save_announcement(data: dict):
    """保存公告设置"""
    import json
    os.makedirs(os.path.dirname(ANNOUNCEMENT_FILE), exist_ok=True)
    data["updated_at"] = datetime.now().isoformat()
    with open(ANNOUNCEMENT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@router.get("/comment-announcement", response_model=CommentAnnouncementResponse)
async def get_comment_announcement():
    """获取评论区公告（公开接口）"""
    data = load_announcement()
    return CommentAnnouncementResponse(**data)


@router.put("/comment-announcement", response_model=CommentAnnouncementResponse)
async def update_comment_announcement(
    announcement_in: CommentAnnouncementUpdate,
    current_user: User = Depends(get_admin_user)
):
    """更新评论区公告（管理员）"""
    data = load_announcement()
    
    for field, value in announcement_in.dict(exclude_unset=True).items():
        if value is not None:
            data[field] = value
    
    save_announcement(data)
    return CommentAnnouncementResponse(**data)


@router.post("/comment-announcement/avatar")
async def upload_announcement_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_admin_user)
):
    """上传公告头像（管理员，自动转WebP优化）"""
    from app.services.image_service import ImageService
    
    if file.content_type not in ImageService.SUPPORTED_FORMATS:
        raise HTTPException(status_code=400, detail="不支持的图片格式")
    
    content = await file.read()
    if len(content) > 1 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小不能超过1MB")
    
    try:
        result = await ImageService.save_image(
            content=content,
            subdir="site",
            filename=f"announcement_avatar_{uuid.uuid4().hex[:8]}",
            convert_webp=True
        )
        avatar_url = result["url"]
    except Exception:
        # 降级处理
        ext = os.path.splitext(file.filename)[1] or '.png'
        filename = f"announcement_avatar_{uuid.uuid4().hex[:8]}{ext}"
        avatar_dir = os.path.join(settings.UPLOAD_DIR, "site")
        os.makedirs(avatar_dir, exist_ok=True)
        filepath = os.path.join(avatar_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(content)
        avatar_url = f"/uploads/site/{filename}"
    
    data = load_announcement()
    data["avatar"] = avatar_url
    save_announcement(data)
    
    return {"avatar": avatar_url, "message": "上传成功"}


