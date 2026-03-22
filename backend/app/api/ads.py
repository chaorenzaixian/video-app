"""
广告相关API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
import os
import uuid
import json

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user_optional, get_admin_user
from app.models.user import User, UserVIP
from app.models.ad import Advertisement, AdClick, AdPosition, AdType, IconAd, FuncEntry, Announcement, OfficialGroup, OfficialGroupType, CustomerService
from app.services.image_service import ImageService, process_and_save_image

router = APIRouter()


@router.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    convert_webp: bool = Query(True, description="是否转换为WebP格式"),
    generate_thumbs: bool = Query(False, description="是否生成缩略图"),
    current_user: User = Depends(get_admin_user)
):
    """
    上传图片（通用）- 支持自动WebP转换和缩略图生成
    
    - convert_webp: 是否转换为WebP格式（默认开启，可减少50-70%体积）
    - generate_thumbs: 是否生成多尺寸缩略图（small/medium/large）
    """
    # 验证文件类型
    valid, error = ImageService.validate_image(b"", file.content_type or "")
    if file.content_type not in ImageService.SUPPORTED_FORMATS:
        raise HTTPException(status_code=400, detail="不支持的图片格式，请上传PNG/JPG/GIF/WEBP/BMP")
    
    # 读取文件内容
    content = await file.read()
    
    # 验证文件大小
    valid, error = ImageService.validate_image(content, file.content_type)
    if not valid:
        raise HTTPException(status_code=400, detail=error)
    
    try:
        # 使用图片服务处理并保存
        result = await ImageService.save_image(
            content=content,
            subdir="images",
            convert_webp=convert_webp,
            generate_thumbs=generate_thumbs
        )
        
        return {
            "url": result["url"],
            "filename": result["filename"],
            "size": result["size"],
            "thumbnails": result.get("thumbnails", {}),
            "optimized": convert_webp and ImageService.is_available()
        }
    except Exception as e:
        # 降级处理：如果图片处理失败，使用原始方式保存
        upload_dir = os.path.join(settings.UPLOAD_DIR, "images")
        os.makedirs(upload_dir, exist_ok=True)
        
        ext = os.path.splitext(file.filename)[1] or '.png'
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(upload_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(content)
        
        return {
            "url": f"/uploads/images/{filename}",
            "filename": filename,
            "size": len(content),
            "thumbnails": {},
            "optimized": False
        }


class AdResponse(BaseModel):
    id: int
    title: str
    ad_type: str
    media_url: Optional[str] = None
    html_content: Optional[str] = None
    target_url: Optional[str] = None
    position: str
    duration: int
    
    class Config:
        from_attributes = True


class SplashAdResponse(BaseModel):
    """开屏广告响应"""
    id: Optional[int] = None
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    duration: int = 5
    title: Optional[str] = None


class PopupAdResponse(BaseModel):
    """弹窗广告响应"""
    id: Optional[int] = None
    image_url: Optional[str] = None
    images: List[str] = []  # 所有图片列表
    target_url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None


@router.get("/popup")
async def get_popup_ad(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """获取首页弹窗广告"""
    # VIP用户不展示广告
    if current_user:
        result = await db.execute(
            select(UserVIP).where(
                UserVIP.user_id == current_user.id,
                UserVIP.is_active == True,
                UserVIP.expire_date > datetime.utcnow()
            )
        )
        if result.scalar_one_or_none():
            return None
    
    now = datetime.utcnow()
    
    query = select(Advertisement).where(
        and_(
            Advertisement.position == AdPosition.HOME_POPUP,
            Advertisement.is_active == True,
            (Advertisement.start_date == None) | (Advertisement.start_date <= now),
            (Advertisement.end_date == None) | (Advertisement.end_date >= now)
        )
    ).order_by(Advertisement.priority.desc()).limit(1)
    
    result = await db.execute(query)
    ad = result.scalar_one_or_none()
    
    if ad:
        ad.impression_count = (ad.impression_count or 0) + 1
        await db.commit()
        
        # 构建图片列表
        images = []
        if ad.media_url:
            images.append(ad.media_url)
        if ad.extra_images:
            try:
                extra = json.loads(ad.extra_images)
                if isinstance(extra, list):
                    images.extend(extra)
            except:
                pass
        
        return PopupAdResponse(
            id=ad.id,
            image_url=ad.media_url,
            images=images,
            target_url=ad.target_url,
            title=ad.title,
            description=ad.description
        )
    
    return None


@router.get("/splash", response_model=SplashAdResponse)
async def get_splash_ad(
    db: AsyncSession = Depends(get_db)
):
    """获取开屏广告"""
    now = datetime.utcnow()
    
    # 查询开屏广告 (position = splash)
    query = select(Advertisement).where(
        and_(
            Advertisement.position == AdPosition.SPLASH,
            Advertisement.is_active == True,
            (Advertisement.start_date == None) | (Advertisement.start_date <= now),
            (Advertisement.end_date == None) | (Advertisement.end_date >= now)
        )
    ).order_by(Advertisement.priority.desc()).limit(1)
    
    result = await db.execute(query)
    ad = result.scalar_one_or_none()
    
    if ad:
        # 更新展示次数
        ad.impression_count = (ad.impression_count or 0) + 1
        await db.commit()
        
        return SplashAdResponse(
            id=ad.id,
            image_url=ad.media_url,
            link_url=ad.target_url,
            duration=ad.duration or 5,
            title=ad.title
        )
    
    # 没有开屏广告时返回空
    return SplashAdResponse(duration=3)


@router.get("", response_model=List[AdResponse])
async def get_ads(
    position: str = Query(...),
    limit: int = Query(5, ge=1, le=20),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """获取广告列表"""
    # 检查用户是否是VIP（VIP不展示广告）
    if current_user:
        result = await db.execute(
            select(UserVIP).where(
                UserVIP.user_id == current_user.id,
                UserVIP.is_active == True,
                UserVIP.expire_date > datetime.utcnow()
            )
        )
        if result.scalar_one_or_none():
            return []  # VIP用户不展示广告
    
    now = datetime.utcnow()
    
    # 查询有效广告（日期为NULL时视为有效）
    query = select(Advertisement).where(
        and_(
            Advertisement.position == position,
            Advertisement.is_active == True,
            (Advertisement.start_date == None) | (Advertisement.start_date <= now),
            (Advertisement.end_date == None) | (Advertisement.end_date >= now)
        )
    ).order_by(Advertisement.priority.desc()).limit(limit)
    
    result = await db.execute(query)
    ads = result.scalars().all()
    
    # 更新展示次数
    for ad in ads:
        ad.impression_count = (ad.impression_count or 0) + 1
    await db.commit()
    
    return [
        AdResponse(
            id=ad.id,
            title=ad.title,
            ad_type=ad.ad_type,
            media_url=ad.media_url,
            html_content=ad.html_content,
            target_url=ad.target_url,
            position=ad.position,
            duration=ad.duration
        )
        for ad in ads
    ]


class IconAdResponse(BaseModel):
    """图标广告位响应"""
    id: int
    name: str
    icon: Optional[str] = None
    image: Optional[str] = None
    link: Optional[str] = None


class IconAdAdminResponse(BaseModel):
    """图标广告位管理响应（含统计）"""
    id: int
    name: str
    icon: Optional[str] = None
    image: Optional[str] = None
    link: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    click_count: int = 0
    impression_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class IconAdCreate(BaseModel):
    """创建图标广告位"""
    name: str
    icon: Optional[str] = None
    image: Optional[str] = None
    link: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class IconAdUpdate(BaseModel):
    """更新图标广告位"""
    name: Optional[str] = None
    icon: Optional[str] = None
    image: Optional[str] = None
    link: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class IconAdSortItem(BaseModel):
    """排序项"""
    id: int
    sort_order: int


class IconAdSortRequest(BaseModel):
    """批量排序请求"""
    items: List[IconAdSortItem]


class IconAdStatsResponse(BaseModel):
    """图标广告统计响应"""
    total_ads: int
    active_ads: int
    total_clicks: int
    total_impressions: int
    avg_ctr: float  # 平均点击率
    ads_stats: List[dict]  # 各广告详细统计


# 默认广告位数据（前5个为固定位，后面为滚动位）
DEFAULT_ICON_ADS = [
    # 第一行固定5个
    {"name": "同城约炮", "icon": "🔥", "image": "", "link": "https://example.com/1", "sort_order": 1},
    {"name": "色色春药", "icon": "💊", "image": "", "link": "https://example.com/2", "sort_order": 2},
    {"name": "新葡京", "icon": "🎰", "image": "", "link": "https://example.com/3", "sort_order": 3},
    {"name": "海角乱伦", "icon": "🌊", "image": "", "link": "https://example.com/4", "sort_order": 4},
    {"name": "P站中文版", "icon": "🅿", "image": "", "link": "https://example.com/5", "sort_order": 5},
    # 第二行滚动（数量不限）
    {"name": "萝莉岛", "icon": "🏝", "image": "", "link": "https://example.com/6", "sort_order": 6},
    {"name": "XVideos", "icon": "❌", "image": "", "link": "https://example.com/7", "sort_order": 7},
    {"name": "快手视频", "icon": "⚡", "image": "", "link": "https://example.com/8", "sort_order": 8},
    {"name": "萝丽塔", "icon": "🎀", "image": "", "link": "https://example.com/9", "sort_order": 9},
    {"name": "oio禁", "icon": "🔒", "image": "", "link": "https://example.com/10", "sort_order": 10},
    {"name": "黑料网", "icon": "📰", "image": "", "link": "https://example.com/11", "sort_order": 11},
    {"name": "色花堂", "icon": "🌸", "image": "", "link": "https://example.com/12", "sort_order": 12},
    {"name": "Pornhub", "icon": "🔶", "image": "", "link": "https://example.com/13", "sort_order": 13}
]


@router.get("/icons", response_model=List[IconAdResponse])
async def get_icon_ads(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """获取图标广告位（前5个固定位 + 后续滚动位，数量不限）"""
    # 从数据库获取
    result = await db.execute(
        select(IconAd)
        .where(IconAd.is_active == True)
        .order_by(IconAd.sort_order, IconAd.id)
    )
    ads = result.scalars().all()
    
    # 如果数据库没有，返回默认数据
    if not ads:
        return [
            IconAdResponse(
                id=i+1,
                name=ad["name"],
                icon=ad["icon"],
                image=ad.get("image"),
                link=ad["link"]
            )
            for i, ad in enumerate(DEFAULT_ICON_ADS)
        ]
    
    # 更新展示次数
    for ad in ads:
        ad.impression_count = (ad.impression_count or 0) + 1
    await db.commit()
    
    return [
        IconAdResponse(
            id=ad.id,
            name=ad.name,
            icon=ad.icon,
            image=ad.image,
            link=ad.link
        )
        for ad in ads
    ]


# ========== 管理后台API ==========

@router.get("/icons/admin", response_model=List[IconAdAdminResponse])
async def get_all_icon_ads(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：获取所有图标广告位（含统计）"""
    result = await db.execute(
        select(IconAd).order_by(IconAd.sort_order, IconAd.id)
    )
    ads = result.scalars().all()
    
    return [
        IconAdAdminResponse(
            id=ad.id,
            name=ad.name,
            icon=ad.icon,
            image=ad.image,
            link=ad.link,
            sort_order=ad.sort_order or 0,
            is_active=ad.is_active,
            click_count=ad.click_count or 0,
            impression_count=ad.impression_count or 0,
            created_at=ad.created_at,
            updated_at=ad.updated_at
        )
        for ad in ads
    ]


@router.post("/icons", response_model=IconAdResponse)
async def create_icon_ad(
    ad_in: IconAdCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：创建图标广告位"""
    ad = IconAd(
        name=ad_in.name,
        icon=ad_in.icon,
        image=ad_in.image,
        bg="",  # 保留字段但不使用
        link=ad_in.link,
        sort_order=ad_in.sort_order,
        is_active=ad_in.is_active
    )
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    
    return IconAdResponse(
        id=ad.id,
        name=ad.name,
        icon=ad.icon,
        image=ad.image,
        link=ad.link
    )


@router.put("/icons/sort")
async def update_icon_ads_sort(
    sort_data: IconAdSortRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：批量更新图标广告排序"""
    for item in sort_data.items:
        result = await db.execute(select(IconAd).where(IconAd.id == item.id))
        ad = result.scalar_one_or_none()
        if ad:
            ad.sort_order = item.sort_order
    
    await db.commit()
    return {"message": "排序更新成功", "count": len(sort_data.items)}


@router.put("/icons/{ad_id}", response_model=IconAdResponse)
async def update_icon_ad(
    ad_id: int,
    ad_in: IconAdUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：更新图标广告位"""
    result = await db.execute(select(IconAd).where(IconAd.id == ad_id))
    ad = result.scalar_one_or_none()
    
    if not ad:
        raise HTTPException(status_code=404, detail="广告位不存在")
    
    # 更新字段
    if ad_in.name is not None:
        ad.name = ad_in.name
    if ad_in.icon is not None:
        ad.icon = ad_in.icon
    if ad_in.image is not None:
        ad.image = ad_in.image
    if ad_in.link is not None:
        ad.link = ad_in.link
    if ad_in.sort_order is not None:
        ad.sort_order = ad_in.sort_order
    if ad_in.is_active is not None:
        ad.is_active = ad_in.is_active
    
    await db.commit()
    await db.refresh(ad)
    
    return IconAdResponse(
        id=ad.id,
        name=ad.name,
        icon=ad.icon,
        image=ad.image,
        link=ad.link
    )


@router.delete("/icons/{ad_id}")
async def delete_icon_ad(
    ad_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：删除图标广告位（包括服务器文件）"""
    result = await db.execute(select(IconAd).where(IconAd.id == ad_id))
    ad = result.scalar_one_or_none()
    
    if not ad:
        raise HTTPException(status_code=404, detail="广告位不存在")
    
    # 保存图片路径
    image_url = ad.image
    
    await db.delete(ad)
    await db.commit()
    
    # 删除服务器上的图片文件
    deleted_files = []
    try:
        if image_url and image_url.startswith("/uploads/"):
            img_path = image_url.replace("/uploads/", "")
            img_file = os.path.join(settings.UPLOAD_DIR, img_path)
            if os.path.exists(img_file):
                os.remove(img_file)
                deleted_files.append(img_path)
    except Exception as e:
        print(f"删除图标广告图片时出错: {e}")
    
    return {"message": "删除成功", "deleted_files": deleted_files}


@router.post("/icons/init")
async def init_icon_ads(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：初始化默认广告位数据"""
    # 检查是否已有数据
    result = await db.execute(select(IconAd).limit(1))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="已存在广告位数据")
    
    # 创建默认数据
    for ad_data in DEFAULT_ICON_ADS:
        ad = IconAd(**ad_data, is_active=True)
        db.add(ad)
    
    await db.commit()
    
    return {"message": "初始化成功", "count": len(DEFAULT_ICON_ADS)}


@router.post("/icons/{ad_id}/click")
async def record_icon_ad_click(
    ad_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """记录图标广告点击"""
    result = await db.execute(select(IconAd).where(IconAd.id == ad_id))
    ad = result.scalar_one_or_none()
    
    if not ad:
        raise HTTPException(status_code=404, detail="广告位不存在")
    
    # 更新点击次数
    ad.click_count = (ad.click_count or 0) + 1
    await db.commit()
    
    return {"success": True, "link": ad.link}


@router.post("/icons/{ad_id}/copy", response_model=IconAdAdminResponse)
async def copy_icon_ad(
    ad_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：复制图标广告位"""
    result = await db.execute(select(IconAd).where(IconAd.id == ad_id))
    ad = result.scalar_one_or_none()
    
    if not ad:
        raise HTTPException(status_code=404, detail="广告位不存在")
    
    # 获取最大排序值
    max_result = await db.execute(
        select(IconAd.sort_order).order_by(IconAd.sort_order.desc()).limit(1)
    )
    max_sort = max_result.scalar() or 0
    
    # 创建副本
    new_ad = IconAd(
        name=f"{ad.name}(副本)",
        icon=ad.icon,
        image=ad.image,
        bg=ad.bg or "",
        link=ad.link,
        sort_order=max_sort + 1,
        is_active=False,  # 默认禁用
        click_count=0,
        impression_count=0
    )
    db.add(new_ad)
    await db.commit()
    await db.refresh(new_ad)
    
    return IconAdAdminResponse(
        id=new_ad.id,
        name=new_ad.name,
        icon=new_ad.icon,
        image=new_ad.image,
        link=new_ad.link,
        sort_order=new_ad.sort_order,
        is_active=new_ad.is_active,
        click_count=new_ad.click_count or 0,
        impression_count=new_ad.impression_count or 0,
        created_at=new_ad.created_at,
        updated_at=new_ad.updated_at
    )


@router.get("/icons/stats", response_model=IconAdStatsResponse)
async def get_icon_ads_stats(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：获取图标广告统计数据"""
    result = await db.execute(select(IconAd).order_by(IconAd.sort_order, IconAd.id))
    ads = result.scalars().all()
    
    total_ads = len(ads)
    active_ads = sum(1 for ad in ads if ad.is_active)
    total_clicks = sum(ad.click_count or 0 for ad in ads)
    total_impressions = sum(ad.impression_count or 0 for ad in ads)
    
    # 计算平均点击率
    avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    
    # 各广告详细统计
    ads_stats = []
    for ad in ads:
        clicks = ad.click_count or 0
        impressions = ad.impression_count or 0
        ctr = (clicks / impressions * 100) if impressions > 0 else 0
        ads_stats.append({
            "id": ad.id,
            "name": ad.name,
            "clicks": clicks,
            "impressions": impressions,
            "ctr": round(ctr, 2),
            "is_active": ad.is_active
        })
    
    return IconAdStatsResponse(
        total_ads=total_ads,
        active_ads=active_ads,
        total_clicks=total_clicks,
        total_impressions=total_impressions,
        avg_ctr=round(avg_ctr, 2),
        ads_stats=ads_stats
    )


@router.post("/{ad_id}/click")
async def record_click(
    ad_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """记录广告点击"""
    result = await db.execute(select(Advertisement).where(Advertisement.id == ad_id))
    ad = result.scalar_one_or_none()
    
    if not ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="广告不存在"
        )
    
    # 创建点击记录
    click = AdClick(
        ad_id=ad_id,
        user_id=current_user.id if current_user else None
    )
    db.add(click)
    
    # 更新点击次数
    ad.click_count += 1
    
    await db.commit()
    
    return {"target_url": ad.target_url}


# ========== 功能入口管理 ==========

class FuncEntryResponse(BaseModel):
    """功能入口响应"""
    id: int
    name: str
    image: Optional[str] = None
    link: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class FuncEntryCreate(BaseModel):
    """创建功能入口"""
    name: str
    image: Optional[str] = None
    link: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class FuncEntryUpdate(BaseModel):
    """更新功能入口"""
    name: Optional[str] = None
    image: Optional[str] = None
    link: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


# 默认功能入口数据
DEFAULT_FUNC_ENTRIES = [
    {"name": "AI广场", "image": "/uploads/func/ai.png", "link": "/user/ai", "sort_order": 1},
    {"name": "签到福利", "image": "/uploads/func/gift.png", "link": "/user/checkin", "sort_order": 2},
    {"name": "会员中心", "image": "/uploads/func/vip.png", "link": "/user/vip", "sort_order": 3},
    {"name": "排行榜", "image": "/uploads/func/trophy.png", "link": "/user/rank", "sort_order": 4},
    {"name": "分享邀请", "image": "/uploads/func/heart.png", "link": "/user/share", "sort_order": 5},
]


@router.get("/func-entries", response_model=List[FuncEntryResponse])
async def get_func_entries(
    db: AsyncSession = Depends(get_db)
):
    """获取功能入口列表"""
    result = await db.execute(
        select(FuncEntry)
        .where(FuncEntry.is_active == True)
        .order_by(FuncEntry.sort_order)
    )
    entries = result.scalars().all()
    
    # 如果数据库没有，返回默认数据
    if not entries:
        return [
            FuncEntryResponse(
                id=i+1,
                name=entry["name"],
                image=entry["image"],
                link=entry["link"],
                sort_order=entry["sort_order"],
                is_active=True
            )
            for i, entry in enumerate(DEFAULT_FUNC_ENTRIES)
        ]
    
    return [
        FuncEntryResponse(
            id=entry.id,
            name=entry.name,
            image=entry.image,
            link=entry.link,
            sort_order=entry.sort_order,
            is_active=entry.is_active
        )
        for entry in entries
    ]


@router.get("/func-entries/admin", response_model=List[FuncEntryResponse])
async def get_all_func_entries(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：获取所有功能入口"""
    result = await db.execute(
        select(FuncEntry).order_by(FuncEntry.sort_order)
    )
    entries = result.scalars().all()
    
    return [
        FuncEntryResponse(
            id=entry.id,
            name=entry.name,
            image=entry.image,
            link=entry.link,
            sort_order=entry.sort_order,
            is_active=entry.is_active
        )
        for entry in entries
    ]


@router.post("/func-entries", response_model=FuncEntryResponse)
async def create_func_entry(
    entry_in: FuncEntryCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：创建功能入口"""
    entry = FuncEntry(
        name=entry_in.name,
        image=entry_in.image,
        link=entry_in.link,
        sort_order=entry_in.sort_order,
        is_active=entry_in.is_active
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    
    return FuncEntryResponse(
        id=entry.id,
        name=entry.name,
        image=entry.image,
        link=entry.link,
        sort_order=entry.sort_order,
        is_active=entry.is_active
    )


@router.put("/func-entries/{entry_id}", response_model=FuncEntryResponse)
async def update_func_entry(
    entry_id: int,
    entry_in: FuncEntryUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：更新功能入口"""
    result = await db.execute(select(FuncEntry).where(FuncEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=404, detail="功能入口不存在")
    
    if entry_in.name is not None:
        entry.name = entry_in.name
    if entry_in.image is not None:
        entry.image = entry_in.image
    if entry_in.link is not None:
        entry.link = entry_in.link
    if entry_in.sort_order is not None:
        entry.sort_order = entry_in.sort_order
    if entry_in.is_active is not None:
        entry.is_active = entry_in.is_active
    
    await db.commit()
    await db.refresh(entry)
    
    return FuncEntryResponse(
        id=entry.id,
        name=entry.name,
        image=entry.image,
        link=entry.link,
        sort_order=entry.sort_order,
        is_active=entry.is_active
    )


@router.delete("/func-entries/{entry_id}")
async def delete_func_entry(
    entry_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：删除功能入口（包括服务器文件）"""
    result = await db.execute(select(FuncEntry).where(FuncEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=404, detail="功能入口不存在")
    
    # 保存图片路径
    image_url = entry.image
    
    await db.delete(entry)
    await db.commit()
    
    # 删除服务器上的图片文件
    deleted_files = []
    try:
        if image_url and image_url.startswith("/uploads/"):
            img_path = image_url.replace("/uploads/", "")
            img_file = os.path.join(settings.UPLOAD_DIR, img_path)
            if os.path.exists(img_file):
                os.remove(img_file)
                deleted_files.append(img_path)
    except Exception as e:
        print(f"删除功能入口图片时出错: {e}")
    
    return {"message": "删除成功", "deleted_files": deleted_files}


@router.post("/func-entries/init")
async def init_func_entries(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：初始化默认功能入口数据"""
    result = await db.execute(select(FuncEntry).limit(1))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="已存在功能入口数据")
    
    for entry_data in DEFAULT_FUNC_ENTRIES:
        entry = FuncEntry(**entry_data, is_active=True)
        db.add(entry)
    
    await db.commit()
    
    return {"message": "初始化成功", "count": len(DEFAULT_FUNC_ENTRIES)}


# ========== 公告管理 ==========

class AnnouncementResponse(BaseModel):
    """公告响应"""
    id: int
    content: str
    link: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: Optional[datetime] = None


class AnnouncementCreate(BaseModel):
    """创建公告"""
    content: str
    link: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class AnnouncementUpdate(BaseModel):
    """更新公告"""
    content: Optional[str] = None
    link: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@router.get("/announcements", response_model=List[AnnouncementResponse])
async def get_announcements(
    db: AsyncSession = Depends(get_db)
):
    """获取有效公告列表（前台使用）"""
    now = datetime.utcnow()
    
    query = select(Announcement).where(
        and_(
            Announcement.is_active == True,
            (Announcement.start_date == None) | (Announcement.start_date <= now),
            (Announcement.end_date == None) | (Announcement.end_date >= now)
        )
    ).order_by(Announcement.sort_order.desc(), Announcement.created_at.desc())
    
    result = await db.execute(query)
    announcements = result.scalars().all()
    
    return [
        AnnouncementResponse(
            id=ann.id,
            content=ann.content,
            link=ann.link,
            sort_order=ann.sort_order,
            is_active=ann.is_active,
            start_date=ann.start_date,
            end_date=ann.end_date,
            created_at=ann.created_at
        )
        for ann in announcements
    ]


@router.get("/announcements/admin", response_model=List[AnnouncementResponse])
async def get_all_announcements(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：获取所有公告"""
    result = await db.execute(
        select(Announcement).order_by(Announcement.sort_order.desc(), Announcement.created_at.desc())
    )
    announcements = result.scalars().all()
    
    return [
        AnnouncementResponse(
            id=ann.id,
            content=ann.content,
            link=ann.link,
            sort_order=ann.sort_order,
            is_active=ann.is_active,
            start_date=ann.start_date,
            end_date=ann.end_date,
            created_at=ann.created_at
        )
        for ann in announcements
    ]


@router.post("/announcements", response_model=AnnouncementResponse)
async def create_announcement(
    ann_in: AnnouncementCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：创建公告"""
    announcement = Announcement(
        content=ann_in.content,
        link=ann_in.link,
        sort_order=ann_in.sort_order,
        is_active=ann_in.is_active,
        start_date=ann_in.start_date,
        end_date=ann_in.end_date
    )
    db.add(announcement)
    await db.commit()
    await db.refresh(announcement)
    
    return AnnouncementResponse(
        id=announcement.id,
        content=announcement.content,
        link=announcement.link,
        sort_order=announcement.sort_order,
        is_active=announcement.is_active,
        start_date=announcement.start_date,
        end_date=announcement.end_date,
        created_at=announcement.created_at
    )


@router.put("/announcements/{ann_id}", response_model=AnnouncementResponse)
async def update_announcement(
    ann_id: int,
    ann_in: AnnouncementUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：更新公告"""
    result = await db.execute(select(Announcement).where(Announcement.id == ann_id))
    announcement = result.scalar_one_or_none()
    
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")
    
    if ann_in.content is not None:
        announcement.content = ann_in.content
    if ann_in.link is not None:
        announcement.link = ann_in.link
    if ann_in.sort_order is not None:
        announcement.sort_order = ann_in.sort_order
    if ann_in.is_active is not None:
        announcement.is_active = ann_in.is_active
    if ann_in.start_date is not None:
        announcement.start_date = ann_in.start_date
    if ann_in.end_date is not None:
        announcement.end_date = ann_in.end_date
    
    await db.commit()
    await db.refresh(announcement)
    
    return AnnouncementResponse(
        id=announcement.id,
        content=announcement.content,
        link=announcement.link,
        sort_order=announcement.sort_order,
        is_active=announcement.is_active,
        start_date=announcement.start_date,
        end_date=announcement.end_date,
        created_at=announcement.created_at
    )


@router.delete("/announcements/{ann_id}")
async def delete_announcement(
    ann_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：删除公告"""
    result = await db.execute(select(Announcement).where(Announcement.id == ann_id))
    announcement = result.scalar_one_or_none()
    
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")
    
    await db.delete(announcement)
    await db.commit()
    
    return {"message": "删除成功"}


# ========== 视频广告管理 ==========

class AdvertisementAdminResponse(BaseModel):
    """视频广告管理响应"""
    id: int
    title: str
    description: Optional[str] = None
    ad_type: str
    media_url: Optional[str] = None
    extra_images: List[str] = []  # 额外图片列表
    html_content: Optional[str] = None
    target_url: Optional[str] = None
    position: str
    priority: int = 0
    duration: int = 5
    is_active: bool = True
    impression_count: int = 0
    click_count: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: Optional[datetime] = None


class AdvertisementCreate(BaseModel):
    """创建视频广告"""
    title: str
    description: Optional[str] = None
    ad_type: str = "video"
    media_url: Optional[str] = None
    extra_images: List[str] = []  # 额外图片列表
    html_content: Optional[str] = None
    target_url: Optional[str] = None
    position: str = "video_pre"
    priority: int = 0
    duration: int = 5
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class AdvertisementUpdate(BaseModel):
    """更新视频广告"""
    title: Optional[str] = None
    description: Optional[str] = None
    ad_type: Optional[str] = None
    media_url: Optional[str] = None
    extra_images: Optional[List[str]] = None  # 额外图片列表
    html_content: Optional[str] = None
    target_url: Optional[str] = None
    position: Optional[str] = None
    priority: Optional[int] = None
    duration: Optional[int] = None
    is_active: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


def parse_extra_images(extra_images_str: Optional[str]) -> List[str]:
    """解析额外图片JSON字符串为列表"""
    if not extra_images_str:
        return []
    try:
        result = json.loads(extra_images_str)
        return result if isinstance(result, list) else []
    except:
        return []


@router.get("/admin/{ad_id}", response_model=AdvertisementAdminResponse)
async def get_advertisement_by_id(
    ad_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：获取单个广告详情"""
    result = await db.execute(select(Advertisement).where(Advertisement.id == ad_id))
    ad = result.scalar_one_or_none()
    
    if not ad:
        raise HTTPException(status_code=404, detail="广告不存在")
    
    return AdvertisementAdminResponse(
        id=ad.id,
        title=ad.title,
        description=ad.description,
        ad_type=ad.ad_type.value if hasattr(ad.ad_type, 'value') else ad.ad_type,
        media_url=ad.media_url,
        extra_images=parse_extra_images(ad.extra_images),
        html_content=ad.html_content,
        target_url=ad.target_url,
        position=ad.position.value if hasattr(ad.position, 'value') else ad.position,
        priority=ad.priority,
        duration=ad.duration,
        is_active=ad.is_active,
        impression_count=ad.impression_count,
        click_count=ad.click_count,
        start_date=ad.start_date,
        end_date=ad.end_date,
        created_at=ad.created_at
    )


@router.get("/admin", response_model=List[AdvertisementAdminResponse])
async def get_all_advertisements(
    position: Optional[str] = None,
    ad_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：获取所有视频广告"""
    query = select(Advertisement)
    
    if position:
        try:
            pos_enum = AdPosition(position)
            query = query.where(Advertisement.position == pos_enum)
        except ValueError:
            pass  # Invalid position, ignore filter
    if ad_type:
        try:
            type_enum = AdType(ad_type)
            query = query.where(Advertisement.ad_type == type_enum)
        except ValueError:
            pass  # Invalid type, ignore filter
    
    query = query.order_by(Advertisement.priority.desc(), Advertisement.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    ads = result.scalars().all()
    
    return [
        AdvertisementAdminResponse(
            id=ad.id,
            title=ad.title,
            description=ad.description,
            ad_type=ad.ad_type.value if hasattr(ad.ad_type, 'value') else ad.ad_type,
            media_url=ad.media_url,
            extra_images=parse_extra_images(ad.extra_images),
            html_content=ad.html_content,
            target_url=ad.target_url,
            position=ad.position.value if hasattr(ad.position, 'value') else ad.position,
            priority=ad.priority,
            duration=ad.duration,
            is_active=ad.is_active,
            impression_count=ad.impression_count,
            click_count=ad.click_count,
            start_date=ad.start_date,
            end_date=ad.end_date,
            created_at=ad.created_at
        )
        for ad in ads
    ]


@router.post("/admin", response_model=AdvertisementAdminResponse)
async def create_advertisement(
    ad_in: AdvertisementCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：创建视频广告"""
    ad = Advertisement(
        title=ad_in.title,
        description=ad_in.description,
        ad_type=AdType(ad_in.ad_type) if ad_in.ad_type else AdType.VIDEO,
        media_url=ad_in.media_url,
        extra_images=json.dumps(ad_in.extra_images) if ad_in.extra_images else None,
        html_content=ad_in.html_content,
        target_url=ad_in.target_url,
        position=AdPosition(ad_in.position) if ad_in.position else AdPosition.VIDEO_PRE,
        priority=ad_in.priority,
        duration=ad_in.duration,
        start_date=ad_in.start_date,
        end_date=ad_in.end_date,
        is_active=True
    )
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    
    return AdvertisementAdminResponse(
        id=ad.id,
        title=ad.title,
        description=ad.description,
        ad_type=ad.ad_type.value if hasattr(ad.ad_type, 'value') else ad.ad_type,
        media_url=ad.media_url,
        extra_images=parse_extra_images(ad.extra_images),
        html_content=ad.html_content,
        target_url=ad.target_url,
        position=ad.position.value if hasattr(ad.position, 'value') else ad.position,
        priority=ad.priority,
        duration=ad.duration,
        is_active=ad.is_active,
        impression_count=ad.impression_count,
        click_count=ad.click_count,
        start_date=ad.start_date,
        end_date=ad.end_date,
        created_at=ad.created_at
    )


@router.put("/admin/{ad_id}", response_model=AdvertisementAdminResponse)
async def update_advertisement(
    ad_id: int,
    ad_in: AdvertisementUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：更新视频广告"""
    result = await db.execute(select(Advertisement).where(Advertisement.id == ad_id))
    ad = result.scalar_one_or_none()
    
    if not ad:
        raise HTTPException(status_code=404, detail="广告不存在")
    
    if ad_in.title is not None:
        ad.title = ad_in.title
    if ad_in.description is not None:
        ad.description = ad_in.description
    if ad_in.ad_type is not None:
        ad.ad_type = AdType(ad_in.ad_type)
    if ad_in.media_url is not None:
        ad.media_url = ad_in.media_url
    if ad_in.extra_images is not None:
        ad.extra_images = json.dumps(ad_in.extra_images) if ad_in.extra_images else None
    if ad_in.html_content is not None:
        ad.html_content = ad_in.html_content
    if ad_in.target_url is not None:
        ad.target_url = ad_in.target_url
    if ad_in.position is not None:
        ad.position = AdPosition(ad_in.position)
    if ad_in.priority is not None:
        ad.priority = ad_in.priority
    if ad_in.duration is not None:
        ad.duration = ad_in.duration
    if ad_in.is_active is not None:
        ad.is_active = ad_in.is_active
    if ad_in.start_date is not None:
        ad.start_date = ad_in.start_date
    if ad_in.end_date is not None:
        ad.end_date = ad_in.end_date
    
    await db.commit()
    await db.refresh(ad)
    
    return AdvertisementAdminResponse(
        id=ad.id,
        title=ad.title,
        description=ad.description,
        ad_type=ad.ad_type.value if hasattr(ad.ad_type, 'value') else ad.ad_type,
        media_url=ad.media_url,
        extra_images=parse_extra_images(ad.extra_images),
        html_content=ad.html_content,
        target_url=ad.target_url,
        position=ad.position.value if hasattr(ad.position, 'value') else ad.position,
        priority=ad.priority,
        duration=ad.duration,
        is_active=ad.is_active,
        impression_count=ad.impression_count,
        click_count=ad.click_count,
        start_date=ad.start_date,
        end_date=ad.end_date,
        created_at=ad.created_at
    )


@router.delete("/admin/{ad_id}")
async def delete_advertisement(
    ad_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：删除视频广告（包括服务器文件）"""
    result = await db.execute(select(Advertisement).where(Advertisement.id == ad_id))
    ad = result.scalar_one_or_none()
    
    if not ad:
        raise HTTPException(status_code=404, detail="广告不存在")
    
    # 保存媒体文件路径
    media_url = ad.media_url
    extra_images = parse_extra_images(ad.extra_images)
    
    await db.delete(ad)
    await db.commit()
    
    # 删除服务器上的文件
    deleted_files = []
    try:
        # 删除主媒体文件
        if media_url and media_url.startswith("/uploads/"):
            media_path = media_url.replace("/uploads/", "")
            media_file = os.path.join(settings.UPLOAD_DIR, media_path)
            if os.path.exists(media_file):
                os.remove(media_file)
                deleted_files.append(media_path)
        
        # 删除额外图片
        for img_url in extra_images:
            if img_url and img_url.startswith("/uploads/"):
                img_path = img_url.replace("/uploads/", "")
                img_file = os.path.join(settings.UPLOAD_DIR, img_path)
                if os.path.exists(img_file):
                    os.remove(img_file)
                    deleted_files.append(img_path)
    except Exception as e:
        print(f"删除广告文件时出错: {e}")
    
    return {"message": "删除成功", "deleted_files": deleted_files}



# ================== 官方群组API ==================

from app.models.ad import OfficialGroup, OfficialGroupType


class OfficialGroupResponse(BaseModel):
    """官方群组响应"""
    id: int
    name: str
    group_type: str
    icon_type: str
    icon_image: Optional[str] = None
    icon_bg: str
    url: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    click_count: int = 0
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class OfficialGroupCreate(BaseModel):
    """创建官方群组"""
    name: str
    group_type: str = "community"
    icon_type: str = "rocket"
    icon_image: Optional[str] = None
    icon_bg: str = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    url: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class OfficialGroupUpdate(BaseModel):
    """更新官方群组"""
    name: Optional[str] = None
    group_type: Optional[str] = None
    icon_type: Optional[str] = None
    icon_image: Optional[str] = None
    icon_bg: Optional[str] = None
    url: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


@router.get("/groups")
async def get_official_groups(
    group_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取官方群组列表（前端用）"""
    query = select(OfficialGroup).where(OfficialGroup.is_active == True)
    
    if group_type:
        query = query.where(OfficialGroup.group_type == group_type)
    
    query = query.order_by(OfficialGroup.sort_order.asc(), OfficialGroup.id.asc())
    
    result = await db.execute(query)
    groups = result.scalars().all()
    
    return [
        {
            "id": g.id,
            "name": g.name,
            "group_type": g.group_type.value if hasattr(g.group_type, 'value') else g.group_type,
            "icon_type": g.icon_type,
            "icon_bg": g.icon_bg,
            "url": g.url,
            "sort_order": g.sort_order,
            "is_active": g.is_active,
            "created_at": g.created_at
        }
        for g in groups
    ]


@router.get("/groups/admin", response_model=List[OfficialGroupResponse])
async def get_all_official_groups_admin(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：获取所有官方群组"""
    query = select(OfficialGroup).order_by(OfficialGroup.group_type.asc(), OfficialGroup.sort_order.asc())
    result = await db.execute(query)
    groups = result.scalars().all()
    
    return [
        OfficialGroupResponse(
            id=g.id,
            name=g.name,
            group_type=g.group_type.value if hasattr(g.group_type, 'value') else g.group_type,
            icon_type=g.icon_type,
            icon_bg=g.icon_bg,
            url=g.url,
            sort_order=g.sort_order,
            is_active=g.is_active,
            created_at=g.created_at
        )
        for g in groups
    ]


@router.post("/groups", response_model=OfficialGroupResponse)
async def create_official_group(
    group_in: OfficialGroupCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：创建官方群组"""
    group_type_enum = OfficialGroupType.COMMUNITY
    if group_in.group_type == "business":
        group_type_enum = OfficialGroupType.BUSINESS
    
    group = OfficialGroup(
        name=group_in.name,
        group_type=group_type_enum,
        icon_type=group_in.icon_type,
        icon_image=group_in.icon_image,
        icon_bg=group_in.icon_bg,
        url=group_in.url,
        sort_order=group_in.sort_order,
        is_active=group_in.is_active
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    
    return OfficialGroupResponse(
        id=group.id,
        name=group.name,
        group_type=group.group_type.value if hasattr(group.group_type, 'value') else group.group_type,
        icon_type=group.icon_type,
        icon_image=group.icon_image,
        icon_bg=group.icon_bg,
        url=group.url,
        sort_order=group.sort_order,
        is_active=group.is_active,
        click_count=group.click_count,
        created_at=group.created_at
    )


@router.put("/groups/{group_id}", response_model=OfficialGroupResponse)
async def update_official_group(
    group_id: int,
    group_in: OfficialGroupUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：更新官方群组"""
    result = await db.execute(select(OfficialGroup).where(OfficialGroup.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(status_code=404, detail="群组不存在")
    
    if group_in.name is not None:
        group.name = group_in.name
    if group_in.group_type is not None:
        group.group_type = OfficialGroupType.BUSINESS if group_in.group_type == "business" else OfficialGroupType.COMMUNITY
    if group_in.icon_type is not None:
        group.icon_type = group_in.icon_type
    if group_in.icon_image is not None:
        group.icon_image = group_in.icon_image
    if group_in.icon_bg is not None:
        group.icon_bg = group_in.icon_bg
    if group_in.url is not None:
        group.url = group_in.url
    if group_in.sort_order is not None:
        group.sort_order = group_in.sort_order
    if group_in.is_active is not None:
        group.is_active = group_in.is_active
    
    await db.commit()
    await db.refresh(group)
    
    return OfficialGroupResponse(
        id=group.id,
        name=group.name,
        group_type=group.group_type.value if hasattr(group.group_type, 'value') else group.group_type,
        icon_type=group.icon_type,
        icon_image=group.icon_image,
        icon_bg=group.icon_bg,
        url=group.url,
        sort_order=group.sort_order,
        is_active=group.is_active,
        click_count=group.click_count,
        created_at=group.created_at
    )


@router.delete("/groups/{group_id}")
async def delete_official_group(
    group_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：删除官方群组（包括服务器文件）"""
    result = await db.execute(select(OfficialGroup).where(OfficialGroup.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(status_code=404, detail="群组不存在")
    
    # 保存图片路径
    icon_image = group.icon_image
    
    await db.delete(group)
    await db.commit()
    
    # 删除服务器上的图片文件
    deleted_files = []
    try:
        if icon_image and icon_image.startswith("/uploads/"):
            img_path = icon_image.replace("/uploads/", "")
            img_file = os.path.join(settings.UPLOAD_DIR, img_path)
            if os.path.exists(img_file):
                os.remove(img_file)
                deleted_files.append(img_path)
    except Exception as e:
        print(f"删除群组图片时出错: {e}")
    
    return {"message": "删除成功", "deleted_files": deleted_files}


@router.post("/groups/{group_id}/click")
async def record_group_click(
    group_id: int,
    db: AsyncSession = Depends(get_db)
):
    """记录群组点击"""
    result = await db.execute(select(OfficialGroup).where(OfficialGroup.id == group_id))
    group = result.scalar_one_or_none()
    
    if group:
        group.click_count += 1
        await db.commit()
    
    return {"message": "ok"}


# ============== 客服管理 ==============

from app.models.ad import CustomerService


class CustomerServiceResponse(BaseModel):
    """客服响应"""
    id: int
    name: str
    service_type: str
    icon_type: str
    icon_image: Optional[str] = None
    icon_bg: str
    contact: Optional[str] = None
    description: Optional[str] = None
    work_time: Optional[str] = None
    sort_order: int
    is_active: bool
    click_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CustomerServiceCreate(BaseModel):
    """创建客服"""
    name: str
    service_type: str = "online"
    icon_type: str = "headset"
    icon_image: Optional[str] = None
    icon_bg: str = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    contact: Optional[str] = None
    description: Optional[str] = None
    work_time: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class CustomerServiceUpdate(BaseModel):
    """更新客服"""
    name: Optional[str] = None
    service_type: Optional[str] = None
    icon_type: Optional[str] = None
    icon_image: Optional[str] = None
    icon_bg: Optional[str] = None
    contact: Optional[str] = None
    description: Optional[str] = None
    work_time: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


@router.get("/customer-service")
async def get_customer_services(
    db: AsyncSession = Depends(get_db)
):
    """获取客服列表（前端用）"""
    query = select(CustomerService).where(CustomerService.is_active == True)
    query = query.order_by(CustomerService.sort_order.asc(), CustomerService.id.asc())
    
    result = await db.execute(query)
    services = result.scalars().all()
    
    return [
        CustomerServiceResponse(
            id=s.id,
            name=s.name,
            service_type=s.service_type.value if hasattr(s.service_type, 'value') else s.service_type,
            icon_type=s.icon_type,
            icon_image=s.icon_image,
            icon_bg=s.icon_bg,
            contact=s.contact,
            description=s.description,
            work_time=s.work_time,
            sort_order=s.sort_order,
            is_active=s.is_active,
            click_count=s.click_count,
            created_at=s.created_at
        )
        for s in services
    ]


@router.get("/customer-service/admin")
async def get_all_customer_services_admin(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：获取所有客服"""
    query = select(CustomerService).order_by(CustomerService.sort_order.asc())
    result = await db.execute(query)
    services = result.scalars().all()
    
    return [
        CustomerServiceResponse(
            id=s.id,
            name=s.name,
            service_type=s.service_type.value if hasattr(s.service_type, 'value') else s.service_type,
            icon_type=s.icon_type,
            icon_image=s.icon_image,
            icon_bg=s.icon_bg,
            contact=s.contact,
            description=s.description,
            work_time=s.work_time,
            sort_order=s.sort_order,
            is_active=s.is_active,
            click_count=s.click_count,
            created_at=s.created_at
        )
        for s in services
    ]


@router.post("/customer-service")
async def create_customer_service(
    service_in: CustomerServiceCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：创建客服"""
    service = CustomerService(
        name=service_in.name,
        service_type=service_in.service_type or "online",
        icon_type=service_in.icon_type,
        icon_image=service_in.icon_image,
        icon_bg=service_in.icon_bg,
        contact=service_in.contact,
        description=service_in.description,
        work_time=service_in.work_time,
        sort_order=service_in.sort_order,
        is_active=service_in.is_active
    )
    db.add(service)
    await db.commit()
    await db.refresh(service)
    
    return CustomerServiceResponse(
        id=service.id,
        name=service.name,
        service_type=service.service_type.value if hasattr(service.service_type, 'value') else service.service_type,
        icon_type=service.icon_type,
        icon_image=service.icon_image,
        icon_bg=service.icon_bg,
        contact=service.contact,
        description=service.description,
        work_time=service.work_time,
        sort_order=service.sort_order,
        is_active=service.is_active,
        click_count=service.click_count,
        created_at=service.created_at
    )


@router.put("/customer-service/{service_id}")
async def update_customer_service(
    service_id: int,
    service_in: CustomerServiceUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：更新客服"""
    result = await db.execute(select(CustomerService).where(CustomerService.id == service_id))
    service = result.scalar_one_or_none()
    
    if not service:
        raise HTTPException(status_code=404, detail="客服不存在")
    
    if service_in.name is not None:
        service.name = service_in.name
    if service_in.service_type is not None:
        service.service_type = service_in.service_type
    if service_in.icon_type is not None:
        service.icon_type = service_in.icon_type
    if service_in.icon_image is not None:
        service.icon_image = service_in.icon_image
    if service_in.icon_bg is not None:
        service.icon_bg = service_in.icon_bg
    if service_in.contact is not None:
        service.contact = service_in.contact
    if service_in.description is not None:
        service.description = service_in.description
    if service_in.work_time is not None:
        service.work_time = service_in.work_time
    if service_in.sort_order is not None:
        service.sort_order = service_in.sort_order
    if service_in.is_active is not None:
        service.is_active = service_in.is_active
    
    await db.commit()
    await db.refresh(service)
    
    return CustomerServiceResponse(
        id=service.id,
        name=service.name,
        service_type=service.service_type.value if hasattr(service.service_type, 'value') else service.service_type,
        icon_type=service.icon_type,
        icon_image=service.icon_image,
        icon_bg=service.icon_bg,
        contact=service.contact,
        description=service.description,
        work_time=service.work_time,
        sort_order=service.sort_order,
        is_active=service.is_active,
        click_count=service.click_count,
        created_at=service.created_at
    )


@router.delete("/customer-service/{service_id}")
async def delete_customer_service(
    service_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理后台：删除客服（包括服务器文件）"""
    result = await db.execute(select(CustomerService).where(CustomerService.id == service_id))
    service = result.scalar_one_or_none()
    
    if not service:
        raise HTTPException(status_code=404, detail="客服不存在")
    
    # 保存图片路径
    icon_image = service.icon_image
    
    await db.delete(service)
    await db.commit()
    
    # 删除服务器上的图片文件
    deleted_files = []
    try:
        if icon_image and icon_image.startswith("/uploads/"):
            img_path = icon_image.replace("/uploads/", "")
            img_file = os.path.join(settings.UPLOAD_DIR, img_path)
            if os.path.exists(img_file):
                os.remove(img_file)
                deleted_files.append(img_path)
    except Exception as e:
        print(f"删除客服图片时出错: {e}")
    
    return {"message": "删除成功", "deleted_files": deleted_files}


@router.post("/customer-service/{service_id}/click")
async def record_service_click(
    service_id: int,
    db: AsyncSession = Depends(get_db)
):
    """记录客服点击"""
    result = await db.execute(select(CustomerService).where(CustomerService.id == service_id))
    service = result.scalar_one_or_none()
    
    if service:
        service.click_count += 1
        await db.commit()
    
    return {"message": "ok"}

