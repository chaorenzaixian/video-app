"""
评论相关API - 优化版（解决N+1查询问题）
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Set
from datetime import datetime
import os
import uuid
import aiofiles

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_user_optional
from app.models.user import User, UserVIP, UserRole
from app.models.video import Video
from app.models.comment import Comment, CommentLike
from app.schemas.comment import CommentCreate, CommentUpdate, CommentResponse, CommentListResponse
from app.services.image_service import ImageService

router = APIRouter()

# 图片上传目录
COMMENT_IMAGE_DIR = "uploads/comments"


# ========== 批量查询辅助函数 ==========

async def batch_get_user_vip_levels(db: AsyncSession, user_ids: List[int]) -> Dict[int, int]:
    """批量获取用户VIP等级"""
    if not user_ids:
        return {}
    
    result = await db.execute(
        select(UserVIP).where(UserVIP.user_id.in_(user_ids))
    )
    vips = result.scalars().all()
    
    vip_map = {}
    now = datetime.utcnow()
    for vip in vips:
        if vip.is_active and vip.expire_date and vip.expire_date > now:
            vip_map[vip.user_id] = getattr(vip, 'vip_level', 0) or 0
    
    # 未找到的用户VIP等级为0
    for uid in user_ids:
        if uid not in vip_map:
            vip_map[uid] = 0
    
    return vip_map


async def batch_get_liked_comment_ids(
    db: AsyncSession, 
    comment_ids: List[int], 
    user_id: int
) -> Set[int]:
    """批量获取用户点赞的评论ID"""
    if not comment_ids or not user_id:
        return set()
    
    result = await db.execute(
        select(CommentLike.comment_id).where(
            CommentLike.comment_id.in_(comment_ids),
            CommentLike.user_id == user_id
        )
    )
    return set(row[0] for row in result.all())


async def check_user_is_vip(db: AsyncSession, user_id: int) -> bool:
    """检查用户是否是VIP"""
    result = await db.execute(select(UserVIP).where(UserVIP.user_id == user_id))
    vip = result.scalar_one_or_none()
    if vip and vip.is_active and vip.expire_date and vip.expire_date > datetime.utcnow():
        return True
    return False


def build_comment_response(
    comment: Comment,
    user: User,
    vip_level: int,
    is_liked: bool,
    replies: List[CommentResponse] = None
) -> CommentResponse:
    """构建评论响应对象"""
    return CommentResponse(
        id=comment.id,
        content=comment.content,
        image_url=comment.image_url,
        video_id=comment.video_id,
        user_id=comment.user_id,
        user_name=user.nickname or user.username,
        user_avatar=user.avatar,
        user_vip_level=vip_level,
        parent_id=comment.parent_id,
        like_count=comment.like_count,
        reply_count=comment.reply_count,
        is_pinned=comment.is_pinned,
        is_official=getattr(comment, 'is_official', False),
        is_god=getattr(comment, 'is_god', False),
        is_liked=is_liked,
        created_at=comment.created_at,
        replies=replies or []
    )


# ========== API端点 ==========

@router.post("/upload-image")
async def upload_comment_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """上传评论图片（仅VIP可用，自动转WebP优化）"""
    is_vip = await check_user_is_vip(db, current_user.id)
    is_admin = current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
    
    if not is_vip and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅VIP会员可以上传图片"
        )
    
    if file.content_type not in ImageService.SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能上传图片文件"
        )
    
    contents = await file.read()
    valid, error = ImageService.validate_image(contents, file.content_type)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    try:
        result = await ImageService.save_image(
            content=contents,
            subdir="comments",
            convert_webp=True
        )
        return {"url": result["url"], "optimized": ImageService.is_available()}
    except Exception:
        os.makedirs(COMMENT_IMAGE_DIR, exist_ok=True)
        ext = os.path.splitext(file.filename)[1] or '.jpg'
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(COMMENT_IMAGE_DIR, filename)
        async with aiofiles.open(filepath, 'wb') as f:
            await f.write(contents)
        return {"url": f"/{filepath}", "optimized": False}


@router.post("", response_model=CommentResponse)
async def create_comment(
    comment_in: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建评论（仅VIP可评论）"""
    is_admin = current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
    
    if not is_admin:
        is_vip = await check_user_is_vip(db, current_user.id)
        if not is_vip:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="仅VIP会员可以发表评论"
            )
    
    if not comment_in.content.strip() and not comment_in.image_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="评论内容不能为空"
        )
    
    # 检查视频
    result = await db.execute(select(Video).where(Video.id == comment_in.video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="视频不存在")
    
    # 检查父评论
    if comment_in.parent_id:
        result = await db.execute(select(Comment).where(Comment.id == comment_in.parent_id))
        parent = result.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="回复的评论不存在")
        parent.reply_count += 1
    
    # 创建评论
    comment = Comment(
        content=comment_in.content,
        image_url=comment_in.image_url,
        video_id=comment_in.video_id,
        user_id=current_user.id,
        parent_id=comment_in.parent_id,
        is_official=is_admin
    )
    db.add(comment)
    video.comment_count += 1
    
    await db.commit()
    await db.refresh(comment)
    
    # 获取VIP等级
    vip_map = await batch_get_user_vip_levels(db, [current_user.id])
    
    return build_comment_response(
        comment=comment,
        user=current_user,
        vip_level=vip_map.get(current_user.id, 0),
        is_liked=False
    )


@router.get("/video/{video_id}", response_model=CommentListResponse)
async def list_video_comments(
    video_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("newest", description="排序方式: newest(最新), hottest(最热)"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """获取视频评论列表（优化版 - 批量查询）"""
    # 基础查询：只获取顶级评论，预加载用户关系
    query = select(Comment).where(
        Comment.video_id == video_id,
        Comment.parent_id == None,
        Comment.is_hidden == False
    ).options(selectinload(Comment.user))
    
    # 统计总数
    count_query = select(func.count()).select_from(
        select(Comment.id).where(
            Comment.video_id == video_id,
            Comment.parent_id == None,
            Comment.is_hidden == False
        ).subquery()
    )
    result = await db.execute(count_query)
    total = result.scalar()
    
    # 排序
    if sort_by == "hottest":
        query = query.order_by(desc(Comment.is_pinned), desc(Comment.like_count), desc(Comment.created_at))
    else:
        query = query.order_by(desc(Comment.is_pinned), desc(Comment.created_at))
    
    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    comments = result.scalars().all()
    
    if not comments:
        return CommentListResponse(items=[], total=total, page=page, page_size=page_size)
    
    # 收集所有需要查询的用户ID和评论ID
    user_ids = set(c.user_id for c in comments)
    comment_ids = [c.id for c in comments]
    
    # 获取有回复的评论的回复（限制3条）
    comments_with_replies = [c for c in comments if c.reply_count > 0]
    reply_map: Dict[int, List[Comment]] = {}
    
    if comments_with_replies:
        parent_ids = [c.id for c in comments_with_replies]
        # 批量查询回复（每个父评论最多3条）
        for parent_id in parent_ids:
            reply_result = await db.execute(
                select(Comment)
                .where(Comment.parent_id == parent_id, Comment.is_hidden == False)
                .options(selectinload(Comment.user))
                .order_by(Comment.created_at)
                .limit(3)
            )
            replies = reply_result.scalars().all()
            reply_map[parent_id] = replies
            # 收集回复的用户ID和评论ID
            for r in replies:
                user_ids.add(r.user_id)
                comment_ids.append(r.id)
    
    # 批量查询VIP等级
    vip_map = await batch_get_user_vip_levels(db, list(user_ids))
    
    # 批量查询点赞状态
    liked_ids = set()
    if current_user:
        liked_ids = await batch_get_liked_comment_ids(db, comment_ids, current_user.id)
    
    # 构建响应
    items = []
    for comment in comments:
        # 构建回复列表
        replies_response = []
        if comment.id in reply_map:
            for reply in reply_map[comment.id]:
                replies_response.append(build_comment_response(
                    comment=reply,
                    user=reply.user,
                    vip_level=vip_map.get(reply.user_id, 0),
                    is_liked=reply.id in liked_ids
                ))
        
        items.append(build_comment_response(
            comment=comment,
            user=comment.user,
            vip_level=vip_map.get(comment.user_id, 0),
            is_liked=comment.id in liked_ids,
            replies=replies_response
        ))
    
    return CommentListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/replies/{parent_id}", response_model=CommentListResponse)
async def list_comment_replies(
    parent_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """获取评论的回复列表（优化版）"""
    # 检查父评论
    parent_result = await db.execute(select(Comment).where(Comment.id == parent_id))
    if not parent_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评论不存在")
    
    # 查询回复，预加载用户
    query = select(Comment).where(
        Comment.parent_id == parent_id,
        Comment.is_hidden == False
    ).options(selectinload(Comment.user))
    
    # 统计总数
    count_query = select(func.count()).select_from(
        select(Comment.id).where(
            Comment.parent_id == parent_id,
            Comment.is_hidden == False
        ).subquery()
    )
    result = await db.execute(count_query)
    total = result.scalar()
    
    # 分页
    query = query.order_by(Comment.created_at).offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    replies = result.scalars().all()
    
    if not replies:
        return CommentListResponse(items=[], total=total, page=page, page_size=page_size)
    
    # 批量查询
    user_ids = [r.user_id for r in replies]
    comment_ids = [r.id for r in replies]
    
    vip_map = await batch_get_user_vip_levels(db, user_ids)
    liked_ids = set()
    if current_user:
        liked_ids = await batch_get_liked_comment_ids(db, comment_ids, current_user.id)
    
    items = [
        build_comment_response(
            comment=reply,
            user=reply.user,
            vip_level=vip_map.get(reply.user_id, 0),
            is_liked=reply.id in liked_ids
        )
        for reply in replies
    ]
    
    return CommentListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/{comment_id}/like")
async def like_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """点赞/取消点赞评论"""
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评论不存在")
    
    # 检查是否已点赞
    like_result = await db.execute(
        select(CommentLike).where(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == current_user.id
        )
    )
    existing_like = like_result.scalar_one_or_none()
    
    if existing_like:
        await db.delete(existing_like)
        comment.like_count = max(0, comment.like_count - 1)
        message = "已取消点赞"
    else:
        like = CommentLike(comment_id=comment_id, user_id=current_user.id)
        db.add(like)
        comment.like_count += 1
        message = "点赞成功"
    
    await db.commit()
    return {"message": message, "like_count": comment.like_count}


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除评论（仅管理员）"""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可以删除评论")
    
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评论不存在")
    
    # 软删除
    comment.is_hidden = True
    
    # 更新视频评论数
    video_result = await db.execute(select(Video).where(Video.id == comment.video_id))
    video = video_result.scalar_one_or_none()
    if video:
        video.comment_count = max(0, video.comment_count - 1)
    
    await db.commit()
    return {"message": "删除成功"}
