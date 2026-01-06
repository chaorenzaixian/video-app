"""
后台视频批量操作API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List

from app.core.database import get_db
from app.models.user import User
from app.models.video import Video, VideoStatus
from app.api.deps import get_admin_user

router = APIRouter(prefix="/admin/videos")


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
    """批量删除视频"""
    await db.execute(
        update(Video)
        .where(Video.id.in_(video_ids))
        .values(status=VideoStatus.DELETED)
    )
    await db.commit()
    return {"message": f"已删除 {len(video_ids)} 个视频"}


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



