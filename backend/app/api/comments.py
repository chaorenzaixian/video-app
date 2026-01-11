"""
评论相关API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
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


async def get_user_vip_level(db: AsyncSession, user_id: int) -> int:
    """获取用户VIP等级"""
    result = await db.execute(select(UserVIP).where(UserVIP.user_id == user_id))
    vip = result.scalar_one_or_none()
    if vip and vip.is_active and vip.expire_date and vip.expire_date > datetime.utcnow():
        return getattr(vip, 'vip_level', 0) or 0
    return 0


async def check_user_is_vip(db: AsyncSession, user_id: int) -> bool:
    """检查用户是否是VIP"""
    result = await db.execute(select(UserVIP).where(UserVIP.user_id == user_id))
    vip = result.scalar_one_or_none()
    if vip and vip.is_active and vip.expire_date and vip.expire_date > datetime.utcnow():
        return True
    return False


@router.post("/upload-image")
async def upload_comment_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """上传评论图片（仅VIP可用，自动转WebP优化）"""
    # 检查VIP权限
    is_vip = await check_user_is_vip(db, current_user.id)
    is_admin = current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
    
    if not is_vip and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅VIP会员可以上传图片"
        )
    
    # 检查文件类型
    if file.content_type not in ImageService.SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能上传图片文件"
        )
    
    # 读取文件内容
    contents = await file.read()
    
    # 验证图片
    valid, error = ImageService.validate_image(contents, file.content_type)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    try:
        # 使用图片服务处理并保存（自动转WebP）
        result = await ImageService.save_image(
            content=contents,
            subdir="comments",
            convert_webp=True
        )
        return {"url": result["url"], "optimized": ImageService.is_available()}
    except Exception as e:
        # 降级处理
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
    # 检查是否是管理员
    is_admin = current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
    
    # 非管理员需要检查VIP权限
    if not is_admin:
        is_vip = await check_user_is_vip(db, current_user.id)
        if not is_vip:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="仅VIP会员可以发表评论"
            )
    
    # 检查内容（必须有内容或图片）
    if not comment_in.content.strip() and not comment_in.image_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="评论内容不能为空"
        )
    
    # 检查视频是否存在
    result = await db.execute(select(Video).where(Video.id == comment_in.video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频不存在"
        )
    
    # 检查父评论
    if comment_in.parent_id:
        result = await db.execute(
            select(Comment).where(Comment.id == comment_in.parent_id)
        )
        parent = result.scalar_one_or_none()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="回复的评论不存在"
            )
        # 更新父评论的回复数
        parent.reply_count += 1
    
    # 创建评论
    comment = Comment(
        content=comment_in.content,
        image_url=comment_in.image_url,
        video_id=comment_in.video_id,
        user_id=current_user.id,
        parent_id=comment_in.parent_id,
        is_official=is_admin  # 管理员评论标记为官方
    )
    db.add(comment)
    
    # 更新视频评论数
    video.comment_count += 1
    
    await db.commit()
    await db.refresh(comment)
    
    # 获取当前用户VIP等级
    user_vip_level = await get_user_vip_level(db, current_user.id)
    
    return CommentResponse(
        id=comment.id,
        content=comment.content,
        image_url=comment.image_url,
        video_id=comment.video_id,
        user_id=comment.user_id,
        user_name=current_user.nickname or current_user.username,
        user_avatar=current_user.avatar,
        user_vip_level=user_vip_level,
        parent_id=comment.parent_id,
        like_count=comment.like_count,
        reply_count=comment.reply_count,
        is_pinned=comment.is_pinned,
        is_official=comment.is_official,
        created_at=comment.created_at
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
    """获取视频评论列表"""
    # 只获取顶级评论
    query = select(Comment).where(
        Comment.video_id == video_id,
        Comment.parent_id == None,
        Comment.is_hidden == False
    )
    
    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()
    
    # 排序和分页
    if sort_by == "hottest":
        # 最热：按点赞数排序
        query = query.order_by(desc(Comment.is_pinned), desc(Comment.like_count), desc(Comment.created_at))
    else:
        # 默认最新
        query = query.order_by(desc(Comment.is_pinned), desc(Comment.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    comments = result.scalars().all()
    
    items = []
    for comment in comments:
        # 获取用户信息
        user_result = await db.execute(select(User).where(User.id == comment.user_id))
        user = user_result.scalar_one()
        
        # 获取用户VIP等级
        user_vip_level = await get_user_vip_level(db, comment.user_id)
        
        # 检查当前用户是否点赞
        is_liked = False
        if current_user:
            like_result = await db.execute(
                select(CommentLike).where(
                    CommentLike.comment_id == comment.id,
                    CommentLike.user_id == current_user.id
                )
            )
            is_liked = like_result.scalar_one_or_none() is not None
        
        # 获取回复
        replies = []
        if comment.reply_count > 0:
            reply_result = await db.execute(
                select(Comment)
                .where(Comment.parent_id == comment.id, Comment.is_hidden == False)
                .order_by(Comment.created_at)
                .limit(3)  # 默认显示3条回复
            )
            reply_comments = reply_result.scalars().all()
            
            for reply in reply_comments:
                reply_user_result = await db.execute(select(User).where(User.id == reply.user_id))
                reply_user = reply_user_result.scalar_one()
                
                # 获取回复者VIP等级
                reply_user_vip_level = await get_user_vip_level(db, reply.user_id)
                
                reply_is_liked = False
                if current_user:
                    reply_like_result = await db.execute(
                        select(CommentLike).where(
                            CommentLike.comment_id == reply.id,
                            CommentLike.user_id == current_user.id
                        )
                    )
                    reply_is_liked = reply_like_result.scalar_one_or_none() is not None
                
                replies.append(CommentResponse(
                    id=reply.id,
                    content=reply.content,
                    image_url=reply.image_url,
                    video_id=reply.video_id,
                    user_id=reply.user_id,
                    user_name=reply_user.nickname or reply_user.username,
                    user_avatar=reply_user.avatar,
                    user_vip_level=reply_user_vip_level,
                    parent_id=reply.parent_id,
                    like_count=reply.like_count,
                    reply_count=reply.reply_count,
                    is_pinned=reply.is_pinned,
                    is_official=reply.is_official if hasattr(reply, 'is_official') else False,
                    is_liked=reply_is_liked,
                    created_at=reply.created_at
                ))
        
        items.append(CommentResponse(
            id=comment.id,
            content=comment.content,
            image_url=comment.image_url,
            video_id=comment.video_id,
            user_id=comment.user_id,
            user_name=user.nickname or user.username,
            user_avatar=user.avatar,
            user_vip_level=user_vip_level,
            parent_id=comment.parent_id,
            like_count=comment.like_count,
            reply_count=comment.reply_count,
            is_pinned=comment.is_pinned,
            is_official=comment.is_official if hasattr(comment, 'is_official') else False,
            is_liked=is_liked,
            created_at=comment.created_at,
            replies=replies
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
    """获取评论的回复列表"""
    # 检查父评论是否存在
    parent_result = await db.execute(select(Comment).where(Comment.id == parent_id))
    parent_comment = parent_result.scalar_one_or_none()
    
    if not parent_comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评论不存在"
        )
    
    # 获取回复
    query = select(Comment).where(
        Comment.parent_id == parent_id,
        Comment.is_hidden == False
    )
    
    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()
    
    # 排序和分页
    query = query.order_by(Comment.created_at).offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    replies = result.scalars().all()
    
    items = []
    for reply in replies:
        # 获取用户信息
        user_result = await db.execute(select(User).where(User.id == reply.user_id))
        user = user_result.scalar_one()
        
        # 获取用户VIP等级
        user_vip_level = await get_user_vip_level(db, reply.user_id)
        
        # 检查当前用户是否点赞
        is_liked = False
        if current_user:
            like_result = await db.execute(
                select(CommentLike).where(
                    CommentLike.comment_id == reply.id,
                    CommentLike.user_id == current_user.id
                )
            )
            is_liked = like_result.scalar_one_or_none() is not None
        
        items.append(CommentResponse(
            id=reply.id,
            content=reply.content,
            image_url=reply.image_url,
            video_id=reply.video_id,
            user_id=reply.user_id,
            user_name=user.nickname or user.username,
            user_nickname=user.nickname or user.username,
            user_avatar=user.avatar,
            user_vip_level=user_vip_level,
            parent_id=reply.parent_id,
            like_count=reply.like_count,
            reply_count=reply.reply_count,
            is_pinned=reply.is_pinned,
            is_official=reply.is_official if hasattr(reply, 'is_official') else False,
            is_liked=is_liked,
            created_at=reply.created_at
        ))
    
    return CommentListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/{comment_id}/like")
async def like_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """点赞评论"""
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评论不存在"
        )
    
    # 检查是否已点赞
    like_result = await db.execute(
        select(CommentLike).where(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == current_user.id
        )
    )
    existing_like = like_result.scalar_one_or_none()
    
    if existing_like:
        # 取消点赞
        await db.delete(existing_like)
        comment.like_count -= 1
        message = "已取消点赞"
    else:
        # 添加点赞
        like = CommentLike(
            comment_id=comment_id,
            user_id=current_user.id
        )
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
    from app.models.user import UserRole
    
    # 只有管理员可以删除评论
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可以删除评论"
        )
    
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评论不存在"
        )
    
    # 软删除（隐藏）
    comment.is_hidden = True
    
    # 更新视频评论数
    video_result = await db.execute(select(Video).where(Video.id == comment.video_id))
    video = video_result.scalar_one()
    video.comment_count = max(0, video.comment_count - 1)
    
    await db.commit()
    
    return {"message": "删除成功"}






