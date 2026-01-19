"""
后台视频批量操作API
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os

from app.core.database import get_db
from app.models.user import User
from app.models.video import Video, VideoStatus
from app.api.deps import get_admin_user

router = APIRouter(prefix="/admin/videos")

# 转码回调密钥
TRANSCODE_SECRET_KEY = os.getenv("TRANSCODE_SECRET_KEY", "vYTWoms4FKOqySca1jCLtNHRVz3BAI6U")


@router.post("/batch-approve")
async def batch_approve_videos(
    video_ids: List[int],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """批量审核通过视频"""
    await db.execute(
        update(Video)
        .where(Video.id.in_(video_ids))
        .values(status=VideoStatus.PUBLISHED)
    )
    await db.commit()
    return {"message": f"已审核通过 {len(video_ids)} 个视频"}


@router.post("/batch-reject")
async def batch_reject_videos(
    video_ids: List[int],
    reason: str = "内容不符合规范",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """批量拒绝视频"""
    await db.execute(
        update(Video)
        .where(Video.id.in_(video_ids))
        .values(status=VideoStatus.REJECTED)
    )
    await db.commit()
    return {"message": f"已拒绝 {len(video_ids)} 个视频"}


@router.post("/batch-delete")
async def batch_delete_videos(
    video_ids: List[int],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """批量删除视频（真删除，包括数据库记录和服务器文件）"""
    import shutil
    from sqlalchemy import text
    
    # 先获取所有视频信息
    result = await db.execute(select(Video).where(Video.id.in_(video_ids)))
    videos = result.scalars().all()
    
    if not videos:
        raise HTTPException(status_code=404, detail="未找到视频")
    
    UPLOAD_BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
    deleted_count = 0
    deleted_files = []
    
    for video in videos:
        try:
            video_id = video.id
            hls_url = video.hls_url
            cover_url = video.cover_url
            preview_url = video.preview_url
            
            # 删除数据库关联数据
            await db.execute(text("""
                DELETE FROM comment_likes 
                WHERE comment_id IN (SELECT id FROM comments WHERE video_id = :video_id)
            """), {"video_id": video_id})
            await db.execute(text("DELETE FROM comments WHERE video_id = :video_id"), {"video_id": video_id})
            await db.execute(text("DELETE FROM video_views WHERE video_id = :video_id"), {"video_id": video_id})
            await db.execute(text("DELETE FROM video_tags_association WHERE video_id = :video_id"), {"video_id": video_id})
            await db.execute(text("DELETE FROM videos WHERE id = :video_id"), {"video_id": video_id})
            
            # 删除服务器文件
            if hls_url:
                if "/hls/" in hls_url:
                    parts = hls_url.split("/")
                    if len(parts) >= 4:
                        video_name = parts[-2]
                        hls_dir = os.path.join(UPLOAD_BASE, "hls", video_name)
                        if os.path.exists(hls_dir):
                            shutil.rmtree(hls_dir, ignore_errors=True)
                            deleted_files.append(f"hls/{video_name}/")
                elif "/shorts/" in hls_url:
                    filename = os.path.basename(hls_url)
                    short_file = os.path.join(UPLOAD_BASE, "shorts", filename)
                    if os.path.exists(short_file):
                        os.remove(short_file)
                        deleted_files.append(f"shorts/{filename}")
            
            if cover_url and cover_url.startswith("/uploads/"):
                cover_path = cover_url[9:]  # 去掉 /uploads/
                cover_file = os.path.join(UPLOAD_BASE, cover_path)
                if os.path.exists(cover_file):
                    os.remove(cover_file)
            
            if preview_url and preview_url.startswith("/uploads/"):
                preview_path = preview_url[9:]
                preview_file = os.path.join(UPLOAD_BASE, preview_path)
                if os.path.exists(preview_file):
                    os.remove(preview_file)
            
            deleted_count += 1
            
        except Exception as e:
            print(f"删除视频 {video.id} 失败: {e}")
            continue
    
    await db.commit()
    return {
        "message": f"已删除 {deleted_count} 个视频",
        "deleted_files": deleted_files
    }


@router.post("/batch-feature")
async def batch_feature_videos(
    video_ids: List[int],
    is_featured: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """批量设置精选视频"""
    await db.execute(
        update(Video)
        .where(Video.id.in_(video_ids))
        .values(is_featured=is_featured)
    )
    await db.commit()
    action = "设为精选" if is_featured else "取消精选"
    return {"message": f"已{action} {len(video_ids)} 个视频"}





class ImportVideoRequest(BaseModel):
    """导入视频请求"""
    filename: str  # 视频文件名（不含扩展名）
    title: Optional[str] = None  # 标题，默认使用文件名
    is_short: bool = False  # 是否短视频
    hls_url: Optional[str] = None  # HLS URL (长视频)
    video_url: Optional[str] = None  # 视频 URL (短视频)
    cover_url: Optional[str] = None  # 封面 URL
    preview_url: Optional[str] = None  # 预览 URL
    duration: Optional[float] = None  # 时长


async def get_unique_title(db: AsyncSession, base_title: str) -> str:
    """
    获取唯一的视频标题
    如果标题已存在，自动添加后缀 (2), (3), ...
    """
    import re
    
    # 检查原标题是否存在
    result = await db.execute(
        select(Video).where(Video.title == base_title)
    )
    if not result.scalar_one_or_none():
        return base_title
    
    # 标题已存在，查找最大后缀
    # 匹配 "标题 (数字)" 格式
    pattern = re.escape(base_title) + r' \((\d+)\)$'
    
    # 查询所有相关标题
    result = await db.execute(
        select(Video.title).where(
            Video.title.like(f"{base_title}%")
        )
    )
    existing_titles = [row[0] for row in result.fetchall()]
    
    max_num = 1
    for title in existing_titles:
        if title == base_title:
            continue
        match = re.match(pattern, title)
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num
    
    return f"{base_title} ({max_num + 1})"


@router.post("/import-from-transcode")
async def import_video_from_transcode(
    request: ImportVideoRequest,
    x_transcode_key: str = Header(None, alias="X-Transcode-Key"),
    db: AsyncSession = Depends(get_db)
):
    """
    从转码服务器导入视频
    
    转码服务器完成处理后调用此接口创建视频记录
    视频状态设置为 REVIEWING（待审核），需要管理员手动发布
    如果 hls_url 已存在，跳过导入（防止重复）
    如果标题已存在，自动添加后缀 (2), (3), ...
    """
    # 验证密钥
    if x_transcode_key != TRANSCODE_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid transcode key")
    
    # 检查 hls_url 是否已存在（防止重复导入）
    check_url = request.hls_url or request.video_url
    if check_url:
        result = await db.execute(
            select(Video).where(Video.hls_url == check_url)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return {
                "success": True,
                "video_id": existing.id,
                "action": "skipped",
                "title": existing.title,
                "renamed": False,
                "message": f"视频已存在，跳过导入: {existing.title}"
            }
    
    # 获取唯一标题（自动重命名）
    base_title = request.title or request.filename
    unique_title = await get_unique_title(db, base_title)
    
    # 创建新视频记录
    video = Video(
        title=unique_title,
        description="",
        is_short=request.is_short,
        hls_url=request.hls_url or request.video_url,
        cover_url=request.cover_url,
        preview_url=request.preview_url,
        duration=request.duration or 0,
        status=VideoStatus.REVIEWING,  # 待审核状态
        uploader_id=1,  # 默认管理员上传
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)
    
    # 返回信息
    renamed = unique_title != base_title
    return {
        "success": True,
        "video_id": video.id,
        "action": "created",
        "title": unique_title,
        "renamed": renamed,
        "message": f"视频已导入: {unique_title}" + (" (已自动重命名)" if renamed else "")
    }


@router.post("/batch-publish")
async def batch_publish_videos(
    video_ids: List[int],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """批量发布视频（从待审核状态发布）"""
    await db.execute(
        update(Video)
        .where(Video.id.in_(video_ids))
        .values(
            status=VideoStatus.PUBLISHED,
            published_at=datetime.utcnow()
        )
    )
    await db.commit()
    return {"message": f"已发布 {len(video_ids)} 个视频"}


# ============ 待处理视频管理 API ============

class PendingVideoListResponse(BaseModel):
    """待处理视频列表响应"""
    items: List[dict]
    total: int
    page: int
    page_size: int


class UpdateAndPublishRequest(BaseModel):
    """更新并发布视频请求"""
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    cover_url: Optional[str] = None
    coin_price: Optional[int] = 0
    is_vip_only: Optional[bool] = False
    vip_coin_price: Optional[int] = 0
    is_featured: Optional[bool] = False
    publish: bool = True  # 是否同时发布


@router.get("/pending")
async def get_pending_videos(
    page: int = 1,
    page_size: int = 20,
    video_type: Optional[str] = None,  # short/long/all
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """获取待处理视频列表（REVIEWING状态）"""
    from sqlalchemy import func
    
    # 基础查询
    query = select(Video).where(Video.status == VideoStatus.REVIEWING)
    count_query = select(func.count(Video.id)).where(Video.status == VideoStatus.REVIEWING)
    
    # 视频类型筛选
    if video_type == "short":
        query = query.where(Video.is_short == True)
        count_query = count_query.where(Video.is_short == True)
    elif video_type == "long":
        query = query.where(Video.is_short == False)
        count_query = count_query.where(Video.is_short == False)
    
    # 搜索
    if search:
        query = query.where(Video.title.ilike(f"%{search}%"))
        count_query = count_query.where(Video.title.ilike(f"%{search}%"))
    
    # 总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页
    query = query.order_by(Video.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    videos = result.scalars().all()
    
    # 构建响应
    items = []
    for v in videos:
        items.append({
            "id": v.id,
            "title": v.title,
            "description": v.description,
            "cover_url": v.cover_url,
            "hls_url": v.hls_url,
            "preview_url": v.preview_url,
            "duration": v.duration,
            "is_short": v.is_short,
            "category_id": v.category_id,
            "coin_price": v.coin_price,
            "is_vip_only": v.is_vip_only,
            "vip_coin_price": v.vip_coin_price,
            "is_featured": v.is_featured,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{video_id}/covers")
async def get_video_covers(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """获取视频的候选封面列表"""
    import glob
    
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 上传目录基础路径
    UPLOAD_BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
    
    covers = []
    
    if video.is_short:
        # 短视频：从 hls_url 提取文件名
        # hls_url 格式: /uploads/shorts/{filename}.mp4
        if video.hls_url:
            parts = video.hls_url.split('/')
            if len(parts) >= 3:
                filename = parts[-1].replace('.mp4', '').replace('_transcoded', '')
                
                # 首先检查 shorts/thumbnails/{filename}/ 目录（新格式）
                thumb_dir = os.path.join(UPLOAD_BASE, "shorts", "thumbnails", filename)
                if os.path.exists(thumb_dir):
                    # 查找 cover_*.webp 文件
                    pattern = os.path.join(thumb_dir, "cover_*.webp")
                    found_covers = sorted(glob.glob(pattern), key=lambda x: int(os.path.basename(x).replace('cover_', '').replace('.webp', '')))
                    
                    for cover_path in found_covers:
                        cover_name = os.path.basename(cover_path)
                        # 提取封面编号
                        try:
                            idx = int(cover_name.replace('cover_', '').replace('.webp', ''))
                        except:
                            idx = len(covers) + 1
                        rel_path = f"/uploads/shorts/thumbnails/{filename}/{cover_name}"
                        covers.append({
                            "index": idx,
                            "url": rel_path,
                            "is_current": video.cover_url == rel_path
                        })
                
                # 如果没找到，尝试旧格式 shorts/thumbnails/{filename}_cover_*.jpg
                if not covers:
                    thumb_dir2 = os.path.join(UPLOAD_BASE, "shorts", "thumbnails")
                    if os.path.exists(thumb_dir2):
                        pattern = os.path.join(thumb_dir2, f"{filename}_cover_*.jpg")
                        found_covers = sorted(glob.glob(pattern))
                        
                        for i, cover_path in enumerate(found_covers, 1):
                            rel_path = f"/uploads/shorts/thumbnails/{os.path.basename(cover_path)}"
                            covers.append({
                                "index": i,
                                "url": rel_path,
                                "is_current": video.cover_url == rel_path
                            })
                
                # 如果还没找到，尝试 thumbnails 目录
                if not covers:
                    thumb_dir3 = os.path.join(UPLOAD_BASE, "thumbnails")
                    if os.path.exists(thumb_dir3):
                        pattern = os.path.join(thumb_dir3, f"{filename}_cover_*.jpg")
                        found_covers = sorted(glob.glob(pattern))
                        
                        for i, cover_path in enumerate(found_covers, 1):
                            rel_path = f"/uploads/thumbnails/{os.path.basename(cover_path)}"
                            covers.append({
                                "index": i,
                                "url": rel_path,
                                "is_current": video.cover_url == rel_path
                            })
    else:
        # 长视频封面在 hls/{video_name}/covers/ 目录
        if video.hls_url:
            # 从 hls_url 提取视频名称
            # hls_url 格式: /uploads/hls/{video_name}/master.m3u8
            parts = video.hls_url.split('/')
            if len(parts) >= 4:
                video_name = parts[-2]
                
                # 首先检查 hls/{video_name}/covers/ 目录（新格式）
                covers_dir = os.path.join(UPLOAD_BASE, "hls", video_name, "covers")
                if os.path.exists(covers_dir):
                    # 查找 cover_*.webp 文件
                    for ext in ['webp', 'jpg', 'png']:
                        pattern = os.path.join(covers_dir, f"cover_*.{ext}")
                        try:
                            found_covers = sorted(glob.glob(pattern), key=lambda x: int(os.path.basename(x).split('_')[1].split('.')[0]))
                        except:
                            found_covers = sorted(glob.glob(pattern))
                        
                        for cover_path in found_covers:
                            cover_name = os.path.basename(cover_path)
                            try:
                                idx = int(cover_name.split('_')[1].split('.')[0])
                            except:
                                idx = len(covers) + 1
                            rel_path = f"/uploads/hls/{video_name}/covers/{cover_name}"
                            covers.append({
                                "index": idx,
                                "url": rel_path,
                                "is_current": video.cover_url == rel_path
                            })
                        if covers:
                            break
                
                # 如果没找到，尝试旧格式 hls/{video_name}/cover_*.jpg
                if not covers:
                    hls_dir = os.path.join(UPLOAD_BASE, "hls", video_name)
                    if os.path.exists(hls_dir):
                        for ext in ['webp', 'jpg', 'png']:
                            pattern = os.path.join(hls_dir, f"cover_*.{ext}")
                            found_covers = sorted(glob.glob(pattern))
                            
                            for i, cover_path in enumerate(found_covers, 1):
                                rel_path = f"/uploads/hls/{video_name}/{os.path.basename(cover_path)}"
                                covers.append({
                                    "index": i,
                                    "url": rel_path,
                                    "is_current": video.cover_url == rel_path
                                })
                            if covers:
                                break
    
    # 如果没有找到任何封面，返回当前封面（如果有）
    if not covers and video.cover_url:
        covers.append({
            "index": 1,
            "url": video.cover_url,
            "is_current": True
        })
    
    return {
        "video_id": video_id,
        "current_cover": video.cover_url,
        "covers": covers,
        "message": "未找到候选封面" if not covers else None
    }


@router.put("/{video_id}/update-and-publish")
async def update_and_publish_video(
    video_id: int,
    request: UpdateAndPublishRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """更新视频信息并发布"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 更新字段
    if request.title is not None:
        video.title = request.title
    if request.description is not None:
        video.description = request.description
    if request.category_id is not None:
        video.category_id = request.category_id
    if request.cover_url is not None:
        video.cover_url = request.cover_url
    if request.coin_price is not None:
        video.coin_price = request.coin_price
    if request.is_vip_only is not None:
        video.is_vip_only = request.is_vip_only
    if request.vip_coin_price is not None:
        video.vip_coin_price = request.vip_coin_price
    if request.is_featured is not None:
        video.is_featured = request.is_featured
    
    # 发布
    if request.publish:
        video.status = VideoStatus.PUBLISHED
        video.published_at = datetime.utcnow()
        
        # 清理未使用的候选封面
        await cleanup_unused_covers(video)
    
    await db.commit()
    
    return {
        "success": True,
        "video_id": video_id,
        "published": request.publish,
        "message": "视频已更新" + ("并发布" if request.publish else "")
    }


async def cleanup_unused_covers(video):
    """清理未使用的候选封面，只保留选中的封面"""
    import shutil
    
    UPLOAD_BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
    
    if not video.cover_url:
        return
    
    try:
        if video.is_short:
            # 短视频：清理 shorts/thumbnails/{filename}/ 目录
            if video.hls_url:
                parts = video.hls_url.split('/')
                if len(parts) >= 3:
                    filename = parts[-1].replace('.mp4', '').replace('_transcoded', '')
                    covers_dir = os.path.join(UPLOAD_BASE, "shorts", "thumbnails", filename)
                    if os.path.exists(covers_dir):
                        # 获取选中封面的文件名
                        selected_cover_name = os.path.basename(video.cover_url)
                        # 删除其他封面
                        for f in os.listdir(covers_dir):
                            if f != selected_cover_name and f.startswith('cover_'):
                                try:
                                    os.remove(os.path.join(covers_dir, f))
                                except:
                                    pass
        else:
            # 长视频：清理 hls/{video_name}/covers/ 目录
            if video.hls_url:
                parts = video.hls_url.split('/')
                if len(parts) >= 4:
                    video_name = parts[-2]
                    covers_dir = os.path.join(UPLOAD_BASE, "hls", video_name, "covers")
                    if os.path.exists(covers_dir):
                        # 获取选中封面的文件名
                        selected_cover_name = os.path.basename(video.cover_url)
                        # 删除其他封面
                        for f in os.listdir(covers_dir):
                            if f != selected_cover_name and f.startswith('cover_'):
                                try:
                                    os.remove(os.path.join(covers_dir, f))
                                except:
                                    pass
                        # 如果目录为空或只剩选中的封面，可以删除整个 covers 目录
                        remaining = os.listdir(covers_dir)
                        if len(remaining) == 0:
                            try:
                                os.rmdir(covers_dir)
                            except:
                                pass
    except Exception as e:
        # 清理失败不影响发布
        print(f"清理封面失败: {e}")


@router.put("/{video_id}/cover")
async def update_video_cover(
    video_id: int,
    cover_url: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """更新视频封面"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    video.cover_url = cover_url
    await db.commit()
    
    return {
        "success": True,
        "video_id": video_id,
        "cover_url": cover_url
    }
