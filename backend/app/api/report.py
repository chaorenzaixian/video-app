"""
举报系统API
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user, get_admin_user
from app.models.user import User
from app.models.report import Report, ReportCategory

router = APIRouter(prefix="/reports", tags=["举报系统"])


# ==================== Schemas ====================

class ReportCreate(BaseModel):
    target_type: str  # video, comment, user, message
    target_id: int
    reason_type: str  # spam, porn, violence, fraud, other
    reason_detail: Optional[str] = None
    screenshots: Optional[List[str]] = None


class ReportResponse(BaseModel):
    id: int
    target_type: str
    target_id: int
    reason_type: str
    reason_detail: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 用户举报 ====================

@router.get("/categories")
async def get_report_categories(
    target_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取举报分类列表"""
    query = select(ReportCategory).where(ReportCategory.is_active == True)
    
    result = await db.execute(query.order_by(ReportCategory.sort_order))
    categories = result.scalars().all()
    
    # 过滤适用类型
    filtered = []
    for cat in categories:
        if target_type and cat.target_types:
            if target_type not in cat.target_types:
                continue
        filtered.append({
            "code": cat.code,
            "name": cat.name,
            "description": cat.description
        })
    
    # 如果没有自定义分类，返回默认分类
    if not filtered:
        return [
            {"code": "spam", "name": "垃圾广告", "description": "包含垃圾广告、恶意推广等"},
            {"code": "porn", "name": "色情低俗", "description": "包含色情、低俗内容"},
            {"code": "violence", "name": "暴力血腥", "description": "包含暴力、血腥内容"},
            {"code": "fraud", "name": "欺诈骗钱", "description": "存在欺诈、诈骗行为"},
            {"code": "copyright", "name": "侵权盗版", "description": "侵犯版权或盗用他人内容"},
            {"code": "other", "name": "其他问题", "description": "其他违规行为"}
        ]
    
    return filtered


@router.post("", response_model=ReportResponse)
async def create_report(
    data: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """提交举报"""
    # 检查是否重复举报
    existing = await db.execute(
        select(Report).where(
            Report.reporter_id == current_user.id,
            Report.target_type == data.target_type,
            Report.target_id == data.target_id,
            Report.status.in_(["pending", "processing"])
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="您已举报过此内容，请等待处理")
    
    # 验证举报对象存在
    if data.target_type == "video":
        from app.models.video import Video
        result = await db.execute(select(Video).where(Video.id == data.target_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="视频不存在")
    elif data.target_type == "comment":
        from app.models.comment import Comment
        result = await db.execute(select(Comment).where(Comment.id == data.target_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="评论不存在")
    elif data.target_type == "user":
        result = await db.execute(select(User).where(User.id == data.target_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="用户不存在")
    
    # 创建举报记录
    report = Report(
        reporter_id=current_user.id,
        target_type=data.target_type,
        target_id=data.target_id,
        reason_type=data.reason_type,
        reason_detail=data.reason_detail,
        screenshots=data.screenshots
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    return report


@router.get("/my", response_model=List[ReportResponse])
async def get_my_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取我的举报记录"""
    query = select(Report).where(
        Report.reporter_id == current_user.id
    ).order_by(Report.created_at.desc())
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    
    return result.scalars().all()


# ==================== 管理后台 ====================

@router.get("/admin/list")
async def admin_get_reports(
    status: Optional[str] = None,
    target_type: Optional[str] = None,
    reason_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """管理后台获取举报列表"""
    query = select(Report, User).join(User, Report.reporter_id == User.id)
    
    if status:
        query = query.where(Report.status == status)
    if target_type:
        query = query.where(Report.target_type == target_type)
    if reason_type:
        query = query.where(Report.reason_type == reason_type)
    
    query = query.order_by(Report.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    
    reports = []
    for report, reporter in result.all():
        reports.append({
            "id": report.id,
            "reporter": {
                "id": reporter.id,
                "nickname": reporter.nickname
            },
            "target_type": report.target_type,
            "target_id": report.target_id,
            "reason_type": report.reason_type,
            "reason_detail": report.reason_detail,
            "screenshots": report.screenshots,
            "status": report.status,
            "created_at": report.created_at,
            "handled_at": report.handled_at,
            "handle_result": report.handle_result
        })
    
    # 获取总数
    count_query = select(func.count(Report.id))
    if status:
        count_query = count_query.where(Report.status == status)
    if target_type:
        count_query = count_query.where(Report.target_type == target_type)
    total = await db.execute(count_query)
    
    return {
        "items": reports,
        "total": total.scalar() or 0
    }


class HandleReportRequest(BaseModel):
    result: str  # warn, delete, ban, dismiss
    note: Optional[str] = None


@router.post("/admin/{report_id}/handle")
async def handle_report(
    report_id: int,
    data: HandleReportRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """处理举报"""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="举报不存在")
    
    if report.status in ["resolved", "rejected"]:
        raise HTTPException(status_code=400, detail="该举报已处理")
    
    # 执行处理动作
    if data.result == "delete":
        # 删除被举报内容
        if report.target_type == "video":
            from app.models.video import Video
            video_result = await db.execute(select(Video).where(Video.id == report.target_id))
            video = video_result.scalar_one_or_none()
            if video:
                video.status = "deleted"
        elif report.target_type == "comment":
            from app.models.comment import Comment
            comment_result = await db.execute(select(Comment).where(Comment.id == report.target_id))
            comment = comment_result.scalar_one_or_none()
            if comment:
                await db.delete(comment)
    
    elif data.result == "ban":
        # 封禁用户
        if report.target_type == "user":
            user_result = await db.execute(select(User).where(User.id == report.target_id))
            target_user = user_result.scalar_one_or_none()
            if target_user:
                target_user.is_active = False
    
    # 更新举报状态
    report.status = "resolved" if data.result != "dismiss" else "rejected"
    report.handler_id = admin.id
    report.handled_at = datetime.utcnow()
    report.handle_result = data.result
    report.handle_note = data.note
    
    await db.commit()
    
    return {"message": "处理成功"}


@router.get("/admin/stats")
async def get_report_stats(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取举报统计"""
    # 各状态数量
    status_stats = {}
    for status in ["pending", "processing", "resolved", "rejected"]:
        count = await db.execute(
            select(func.count(Report.id)).where(Report.status == status)
        )
        status_stats[status] = count.scalar() or 0
    
    # 各类型数量
    type_stats = {}
    for target_type in ["video", "comment", "user", "message"]:
        count = await db.execute(
            select(func.count(Report.id)).where(Report.target_type == target_type)
        )
        type_stats[target_type] = count.scalar() or 0
    
    # 今日举报数
    from datetime import timedelta
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = await db.execute(
        select(func.count(Report.id)).where(Report.created_at >= today)
    )
    
    return {
        "by_status": status_stats,
        "by_type": type_stats,
        "today_count": today_count.scalar() or 0,
        "pending_count": status_stats.get("pending", 0)
    }

