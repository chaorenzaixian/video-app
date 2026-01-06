"""
管理后台 - 创作者管理API
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_admin_user
from app.models.user import User
from app.models.video import Video
from app.models.creator import (
    CreatorApplication, Creator, VideoReview, VideoTip,
    CreatorWithdrawal
)

router = APIRouter(prefix="/admin", tags=["管理后台-创作者"])


# ==================== 创作者申请审核 ====================

@router.get("/creator-applications")
async def get_creator_applications(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取创作者申请列表"""
    query = select(CreatorApplication, User).join(
        User, CreatorApplication.user_id == User.id
    )
    
    if status:
        query = query.where(CreatorApplication.status == status)
    
    query = query.order_by(CreatorApplication.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    
    applications = []
    for app, user in result.all():
        applications.append({
            "id": app.id,
            "user_id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "real_name": app.real_name,
            "phone": app.phone,
            "introduction": app.introduction,
            "status": app.status,
            "created_at": app.created_at
        })
    
    # 获取总数
    count_query = select(func.count(CreatorApplication.id))
    if status:
        count_query = count_query.where(CreatorApplication.status == status)
    total = await db.execute(count_query)
    
    return {
        "items": applications,
        "total": total.scalar() or 0
    }


@router.post("/creator-applications/{app_id}/approve")
async def approve_creator_application(
    app_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """通过创作者申请"""
    result = await db.execute(
        select(CreatorApplication).where(CreatorApplication.id == app_id)
    )
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(status_code=404, detail="申请不存在")
    
    if application.status != "pending":
        raise HTTPException(status_code=400, detail="申请状态异常")
    
    # 更新申请状态
    application.status = "approved"
    application.reviewed_by = admin.id
    application.reviewed_at = datetime.utcnow()
    
    # 创建创作者记录
    creator = Creator(
        user_id=application.user_id,
        display_name=application.real_name
    )
    db.add(creator)
    
    await db.commit()
    
    return {"message": "已通过申请"}


@router.post("/creator-applications/{app_id}/reject")
async def reject_creator_application(
    app_id: int,
    reason: str = "",
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """拒绝创作者申请"""
    result = await db.execute(
        select(CreatorApplication).where(CreatorApplication.id == app_id)
    )
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(status_code=404, detail="申请不存在")
    
    if application.status != "pending":
        raise HTTPException(status_code=400, detail="申请状态异常")
    
    application.status = "rejected"
    application.reject_reason = reason
    application.reviewed_by = admin.id
    application.reviewed_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "已拒绝申请"}


# ==================== 视频审核 ====================

@router.get("/video-reviews")
async def get_video_reviews(
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取视频审核列表"""
    query = select(VideoReview, Video, User).join(
        Video, VideoReview.video_id == Video.id
    ).join(
        User, Video.uploader_id == User.id
    )
    
    if status:
        query = query.where(VideoReview.status == status)
    
    if keyword:
        query = query.where(Video.title.ilike(f"%{keyword}%"))
    
    query = query.order_by(VideoReview.submitted_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    
    reviews = []
    for review, video, user in result.all():
        reviews.append({
            "id": review.id,
            "video_id": video.id,
            "video": {
                "id": video.id,
                "title": video.title,
                "cover_url": video.cover_url,
                "original_url": video.original_url,
                "pay_type": video.pay_type,
                "coin_price": video.coin_price,
                "uploader": {
                    "id": user.id,
                    "nickname": user.nickname
                }
            },
            "status": review.status,
            "ai_reviewed": review.ai_reviewed,
            "ai_score": review.ai_score,
            "review_note": review.review_note,
            "submitted_at": review.submitted_at
        })
    
    # 获取总数
    count_query = select(func.count(VideoReview.id))
    if status:
        count_query = count_query.where(VideoReview.status == status)
    total = await db.execute(count_query)
    
    return {
        "items": reviews,
        "total": total.scalar() or 0
    }


class RejectRequest(BaseModel):
    reasons: List[str]
    note: Optional[str] = None


@router.post("/video-reviews/{review_id}/approve")
async def approve_video(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """通过视频审核"""
    result = await db.execute(
        select(VideoReview).where(VideoReview.id == review_id)
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=404, detail="审核记录不存在")
    
    if review.status != "pending":
        raise HTTPException(status_code=400, detail="该视频已审核")
    
    review.status = "approved"
    review.reviewer_id = admin.id
    review.reviewed_at = datetime.utcnow()
    
    # 更新视频状态为已发布
    video_result = await db.execute(
        select(Video).where(Video.id == review.video_id)
    )
    video = video_result.scalar_one_or_none()
    if video:
        video.status = "published"
        video.published_at = datetime.utcnow()
        
        # 更新创作者视频数
        if video.creator_id:
            creator_result = await db.execute(
                select(Creator).where(Creator.id == video.creator_id)
            )
            creator = creator_result.scalar_one_or_none()
            if creator:
                creator.total_videos += 1
    
    await db.commit()
    
    return {"message": "审核通过"}


@router.post("/video-reviews/{review_id}/reject")
async def reject_video(
    review_id: int,
    data: RejectRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """拒绝视频"""
    result = await db.execute(
        select(VideoReview).where(VideoReview.id == review_id)
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=404, detail="审核记录不存在")
    
    if review.status != "pending":
        raise HTTPException(status_code=400, detail="该视频已审核")
    
    review.status = "rejected"
    review.reject_reasons = data.reasons
    review.review_note = data.note
    review.reviewer_id = admin.id
    review.reviewed_at = datetime.utcnow()
    
    # 更新视频状态
    video_result = await db.execute(
        select(Video).where(Video.id == review.video_id)
    )
    video = video_result.scalar_one_or_none()
    if video:
        video.status = "rejected"
    
    await db.commit()
    
    return {"message": "已拒绝"}


# ==================== 提现审核 ====================

@router.get("/creator-withdrawals")
async def get_withdrawals(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取提现申请列表"""
    query = select(CreatorWithdrawal, Creator, User).join(
        Creator, CreatorWithdrawal.creator_id == Creator.id
    ).join(
        User, Creator.user_id == User.id
    )
    
    if status:
        query = query.where(CreatorWithdrawal.status == status)
    
    query = query.order_by(CreatorWithdrawal.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    
    withdrawals = []
    for w, creator, user in result.all():
        withdrawals.append({
            "id": w.id,
            "creator_id": creator.id,
            "user": {
                "id": user.id,
                "nickname": user.nickname
            },
            "coins_amount": w.coins_amount,
            "cash_amount": float(w.cash_amount),
            "payment_method": w.payment_method,
            "payment_account": w.payment_account,
            "payment_name": w.payment_name,
            "status": w.status,
            "created_at": w.created_at
        })
    
    return {"items": withdrawals}


@router.post("/creator-withdrawals/{withdrawal_id}/approve")
async def approve_withdrawal(
    withdrawal_id: int,
    transaction_no: str = "",
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """通过提现申请"""
    result = await db.execute(
        select(CreatorWithdrawal).where(CreatorWithdrawal.id == withdrawal_id)
    )
    withdrawal = result.scalar_one_or_none()
    
    if not withdrawal:
        raise HTTPException(status_code=404, detail="提现记录不存在")
    
    if withdrawal.status != "pending":
        raise HTTPException(status_code=400, detail="状态异常")
    
    withdrawal.status = "completed"
    withdrawal.transaction_no = transaction_no
    withdrawal.processed_by = admin.id
    withdrawal.processed_at = datetime.utcnow()
    
    # 解冻并扣除创作者金币
    creator_result = await db.execute(
        select(Creator).where(Creator.id == withdrawal.creator_id)
    )
    creator = creator_result.scalar_one_or_none()
    if creator:
        creator.frozen_coins -= withdrawal.coins_amount
    
    await db.commit()
    
    return {"message": "提现已完成"}


@router.post("/creator-withdrawals/{withdrawal_id}/reject")
async def reject_withdrawal(
    withdrawal_id: int,
    reason: str = "",
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """拒绝提现申请"""
    result = await db.execute(
        select(CreatorWithdrawal).where(CreatorWithdrawal.id == withdrawal_id)
    )
    withdrawal = result.scalar_one_or_none()
    
    if not withdrawal:
        raise HTTPException(status_code=404, detail="提现记录不存在")
    
    if withdrawal.status != "pending":
        raise HTTPException(status_code=400, detail="状态异常")
    
    withdrawal.status = "rejected"
    withdrawal.reject_reason = reason
    withdrawal.processed_by = admin.id
    withdrawal.processed_at = datetime.utcnow()
    
    # 解冻金币，退回可用余额
    creator_result = await db.execute(
        select(Creator).where(Creator.id == withdrawal.creator_id)
    )
    creator = creator_result.scalar_one_or_none()
    if creator:
        creator.frozen_coins -= withdrawal.coins_amount
        creator.available_coins += withdrawal.coins_amount
    
    await db.commit()
    
    return {"message": "已拒绝提现"}

