"""
下载页管理 API
管理 App 下载页面的配置，包括下载链接、Logo、二维码等
"""
import json
import uuid
import base64
import io
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.api.deps import get_current_user, get_admin_user
from app.models.user import User
from app.models.system_config import SystemConfig

router = APIRouter()


# ========== Pydantic 数据模型 ==========

class AndroidLink(BaseModel):
    """Android 下载链接"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "主下载"
    url: str
    is_primary: bool = False
    is_active: bool = True
    sort_order: int = 0


class IOSLinks(BaseModel):
    """iOS 下载链接"""
    appstore: str = ""
    mobileconfig: str = ""
    appstore_active: bool = True
    mobileconfig_active: bool = True


class QRCodeConfig(BaseModel):
    """二维码配置"""
    url: str = ""
    logo: Optional[str] = None
    color: str = "#000000"
    size: int = 300


class BackgroundConfig(BaseModel):
    """背景配置"""
    pc: str = ""
    mobile: str = ""


class LogoConfig(BaseModel):
    """Logo 配置"""
    pc: str = ""
    mobile: str = ""


class DownloadPageConfig(BaseModel):
    """完整下载页配置"""
    android_links: List[AndroidLink] = []
    ios_links: IOSLinks = IOSLinks()
    logos: LogoConfig = LogoConfig()
    backgrounds_v1: BackgroundConfig = BackgroundConfig()
    backgrounds_v2: BackgroundConfig = BackgroundConfig()
    qrcode: QRCodeConfig = QRCodeConfig()
    active_bg_version: str = "v1"


class DownloadPageConfigUpdate(BaseModel):
    """更新下载页配置请求"""
    android_links: Optional[List[AndroidLink]] = None
    ios_links: Optional[IOSLinks] = None
    logos: Optional[LogoConfig] = None
    backgrounds_v1: Optional[BackgroundConfig] = None
    backgrounds_v2: Optional[BackgroundConfig] = None
    qrcode: Optional[QRCodeConfig] = None
    active_bg_version: Optional[str] = None


class QRCodeRequest(BaseModel):
    """二维码生成请求"""
    url: str
    logo: Optional[str] = None
    color: str = "#000000"
    size: int = 300


# ========== 辅助函数 ==========

async def get_config_value(db: AsyncSession, key: str, default: str = "") -> str:
    """获取配置值"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == key)
    )
    config = result.scalar_one_or_none()
    return config.value if config else default


async def set_config_value(db: AsyncSession, key: str, value: str, group: str = "download_page", description: str = ""):
    """设置配置值"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == key)
    )
    config = result.scalar_one_or_none()
    
    if config:
        config.value = value
        config.updated_at = datetime.utcnow()
    else:
        config = SystemConfig(
            key=key,
            value=value,
            group_name=group,
            description=description
        )
        db.add(config)


async def load_download_config(db: AsyncSession) -> DownloadPageConfig:
    """从数据库加载完整配置"""
    config = DownloadPageConfig()
    
    # Android 链接
    android_json = await get_config_value(db, "download_android_links", "[]")
    try:
        android_data = json.loads(android_json)
        config.android_links = [AndroidLink(**item) for item in android_data]
    except:
        config.android_links = []
    
    # iOS 链接
    ios_appstore = await get_config_value(db, "download_ios_appstore", "")
    ios_mobileconfig = await get_config_value(db, "download_ios_mobileconfig", "")
    ios_appstore_active = await get_config_value(db, "download_ios_appstore_active", "true")
    ios_mobileconfig_active = await get_config_value(db, "download_ios_mobileconfig_active", "true")
    config.ios_links = IOSLinks(
        appstore=ios_appstore,
        mobileconfig=ios_mobileconfig,
        appstore_active=ios_appstore_active.lower() == "true",
        mobileconfig_active=ios_mobileconfig_active.lower() == "true"
    )
    
    # Logo
    config.logos = LogoConfig(
        pc=await get_config_value(db, "download_logo_pc", ""),
        mobile=await get_config_value(db, "download_logo_mobile", "")
    )
    
    # 背景 V1
    config.backgrounds_v1 = BackgroundConfig(
        pc=await get_config_value(db, "download_bg_v1_pc", ""),
        mobile=await get_config_value(db, "download_bg_v1_mobile", "")
    )
    
    # 背景 V2
    config.backgrounds_v2 = BackgroundConfig(
        pc=await get_config_value(db, "download_bg_v2_pc", ""),
        mobile=await get_config_value(db, "download_bg_v2_mobile", "")
    )
    
    # 二维码配置
    config.qrcode = QRCodeConfig(
        url=await get_config_value(db, "download_qrcode_url", ""),
        logo=await get_config_value(db, "download_qrcode_logo", "") or None,
        color=await get_config_value(db, "download_qrcode_color", "#000000"),
        size=int(await get_config_value(db, "download_qrcode_size", "300"))
    )
    
    # 当前背景版本
    config.active_bg_version = await get_config_value(db, "download_active_bg_version", "v1")
    
    return config


async def save_download_config(db: AsyncSession, update: DownloadPageConfigUpdate):
    """保存配置到数据库"""
    if update.android_links is not None:
        # 按 sort_order 排序，主链接优先
        sorted_links = sorted(
            update.android_links,
            key=lambda x: (not x.is_primary, x.sort_order)
        )
        await set_config_value(
            db, "download_android_links",
            json.dumps([link.dict() for link in sorted_links]),
            description="Android 下载链接列表"
        )
    
    if update.ios_links is not None:
        await set_config_value(db, "download_ios_appstore", update.ios_links.appstore, description="iOS App Store 链接")
        await set_config_value(db, "download_ios_mobileconfig", update.ios_links.mobileconfig, description="iOS mobileconfig 链接")
        await set_config_value(db, "download_ios_appstore_active", str(update.ios_links.appstore_active).lower(), description="App Store 链接启用状态")
        await set_config_value(db, "download_ios_mobileconfig_active", str(update.ios_links.mobileconfig_active).lower(), description="mobileconfig 链接启用状态")
    
    if update.logos is not None:
        await set_config_value(db, "download_logo_pc", update.logos.pc, description="PC 端 Logo")
        await set_config_value(db, "download_logo_mobile", update.logos.mobile, description="移动端 Logo")
    
    if update.backgrounds_v1 is not None:
        await set_config_value(db, "download_bg_v1_pc", update.backgrounds_v1.pc, description="V1 背景 PC 端")
        await set_config_value(db, "download_bg_v1_mobile", update.backgrounds_v1.mobile, description="V1 背景移动端")
    
    if update.backgrounds_v2 is not None:
        await set_config_value(db, "download_bg_v2_pc", update.backgrounds_v2.pc, description="V2 背景 PC 端")
        await set_config_value(db, "download_bg_v2_mobile", update.backgrounds_v2.mobile, description="V2 背景移动端")
    
    if update.qrcode is not None:
        await set_config_value(db, "download_qrcode_url", update.qrcode.url, description="二维码目标 URL")
        await set_config_value(db, "download_qrcode_logo", update.qrcode.logo or "", description="二维码中心 Logo")
        await set_config_value(db, "download_qrcode_color", update.qrcode.color, description="二维码颜色")
        await set_config_value(db, "download_qrcode_size", str(update.qrcode.size), description="二维码尺寸")
    
    if update.active_bg_version is not None:
        await set_config_value(db, "download_active_bg_version", update.active_bg_version, description="当前背景版本")
    
    await db.commit()


# ========== 公开 API ==========

@router.get("/config")
async def get_download_config(db: AsyncSession = Depends(get_db)):
    """获取下载页配置（公开接口，供下载页使用）"""
    config = await load_download_config(db)
    
    # 过滤掉未启用的链接
    active_android_links = [
        link for link in config.android_links if link.is_active
    ]
    
    # 构建前端友好的响应格式
    response = {
        "download": {
            "android": active_android_links,
            "ios": {
                "appstore": config.ios_links.appstore if config.ios_links.appstore_active else "",
                "mobileconfig": config.ios_links.mobileconfig if config.ios_links.mobileconfig_active else ""
            }
        },
        "logos": config.logos.dict(),
        "backgrounds": {
            "v1": config.backgrounds_v1.dict(),
            "v2": config.backgrounds_v2.dict()
        },
        "active_bg_version": config.active_bg_version,
        "qrcode": config.qrcode.dict()
    }
    
    return response


# ========== 管理 API ==========

@router.get("/admin/config")
async def get_admin_download_config(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取完整下载页配置（管理员接口）"""
    config = await load_download_config(db)
    return config.dict()


@router.put("/admin/config")
async def update_download_config(
    update: DownloadPageConfigUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新下载页配置"""
    try:
        await save_download_config(db, update)
        return {"message": "配置更新成功"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"配置保存失败: {str(e)}")



@router.post("/admin/upload")
async def upload_download_image(
    file: UploadFile = File(...),
    type: str = Form(...),  # logo_pc, logo_mobile, bg_v1_pc, bg_v1_mobile, bg_v2_pc, bg_v2_mobile, qrcode_logo
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """上传下载页图片（Logo/背景）"""
    import os
    import aiofiles
    
    # 验证文件类型
    allowed_types = ["image/png", "image/jpeg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="不支持的图片格式，请上传 PNG、JPG 或 WebP 格式"
        )
    
    # 验证文件大小 (2MB)
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="图片大小不能超过 2MB"
        )
    
    # 验证类型参数
    valid_types = ["logo_pc", "logo_mobile", "bg_v1_pc", "bg_v1_mobile", "bg_v2_pc", "bg_v2_mobile", "qrcode_logo"]
    if type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"无效的类型参数，有效值: {', '.join(valid_types)}"
        )
    
    # 生成文件名
    ext = file.filename.split(".")[-1] if "." in file.filename else "png"
    filename = f"download_{type}_{uuid.uuid4().hex[:8]}.{ext}"
    
    # 保存到 static/download 目录
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "download")
    os.makedirs(upload_dir, exist_ok=True)
    
    filepath = os.path.join(upload_dir, filename)
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)
    
    # 返回 URL
    url = f"/static/download/{filename}"
    
    return {"url": url, "filename": filename}


@router.post("/admin/qrcode")
async def generate_qrcode(
    request: QRCodeRequest,
    current_user: User = Depends(get_admin_user)
):
    """生成二维码"""
    try:
        import qrcode
        from PIL import Image
        import requests
        
        # 创建二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=2,
        )
        qr.add_data(request.url)
        qr.make(fit=True)
        
        # 解析颜色
        fill_color = request.color if request.color else "#000000"
        
        # 生成二维码图片
        qr_img = qr.make_image(fill_color=fill_color, back_color="white")
        qr_img = qr_img.convert("RGBA")
        
        # 调整尺寸
        qr_img = qr_img.resize((request.size, request.size), Image.Resampling.LANCZOS)
        
        # 如果有 Logo，嵌入到中心
        if request.logo:
            try:
                # 支持 URL 或 base64
                if request.logo.startswith("http"):
                    logo_response = requests.get(request.logo, timeout=5)
                    logo_img = Image.open(io.BytesIO(logo_response.content))
                elif request.logo.startswith("data:"):
                    # base64 格式
                    logo_data = request.logo.split(",")[1]
                    logo_img = Image.open(io.BytesIO(base64.b64decode(logo_data)))
                else:
                    # 本地路径
                    import os
                    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), request.logo.lstrip("/"))
                    logo_img = Image.open(logo_path)
                
                # 调整 Logo 大小（二维码的 1/4）
                logo_size = request.size // 4
                logo_img = logo_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                
                # 计算位置（居中）
                pos = ((request.size - logo_size) // 2, (request.size - logo_size) // 2)
                
                # 创建白色背景
                logo_bg = Image.new("RGBA", (logo_size + 10, logo_size + 10), "white")
                qr_img.paste(logo_bg, (pos[0] - 5, pos[1] - 5))
                
                # 粘贴 Logo
                if logo_img.mode == "RGBA":
                    qr_img.paste(logo_img, pos, logo_img)
                else:
                    qr_img.paste(logo_img, pos)
            except Exception as e:
                # Logo 处理失败，继续生成不带 Logo 的二维码
                print(f"Logo 处理失败: {e}")
        
        # 转换为 base64
        buffer = io.BytesIO()
        qr_img.save(buffer, format="PNG")
        buffer.seek(0)
        
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            "image": f"data:image/png;base64,{image_base64}",
            "size": request.size
        }
        
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="二维码生成库未安装，请安装 qrcode 和 Pillow"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"二维码生成失败: {str(e)}"
        )


@router.delete("/admin/android-link/{link_id}")
async def delete_android_link(
    link_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """删除 Android 下载链接"""
    config = await load_download_config(db)
    
    # 过滤掉要删除的链接
    new_links = [link for link in config.android_links if link.id != link_id]
    
    if len(new_links) == len(config.android_links):
        raise HTTPException(status_code=404, detail="链接不存在")
    
    # 保存更新
    update = DownloadPageConfigUpdate(android_links=new_links)
    await save_download_config(db, update)
    
    return {"message": "删除成功"}
