"""
功能开关/AB测试/灰度发布 API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_user_optional, get_admin_user
from app.models.user import User
from app.models.feature_flag import FeatureFlag, FeatureRule, ExperimentExposure, ExperimentEvent
from app.services.feature_flag_service import FeatureFlagService

router = APIRouter(prefix="/feature-flags", tags=["功能开关"])


# ========== Schemas ==========

class FlagEvaluateRequest(BaseModel):
    """评估请求"""
    flag_keys: List[str]


class FlagEvaluateResponse(BaseModel):
    """评估响应"""
    flags: dict


class TrackEventRequest(BaseModel):
    """追踪事件请求"""
    flag_key: str
    event_type: str
    event_value: Optional[float] = None
    event_data: Optional[dict] = None


class FlagCreateRequest(BaseModel):
    """创建功能开关请求"""
    key: str
    name: str
    description: Optional[str] = None
    flag_type: str = "boolean"
    is_enabled: bool = False
    default_value: Optional[str] = '{"enabled": false}'
    variants: Optional[str] = None
    rollout_percentage: int = 0
    whitelist_user_ids: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class FlagUpdateRequest(BaseModel):
    """更新功能开关请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    flag_type: Optional[str] = None
    is_enabled: Optional[bool] = None
    default_value: Optional[str] = None
    variants: Optional[str] = None
    rollout_percentage: Optional[int] = None
    whitelist_user_ids: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class RuleCreateRequest(BaseModel):
    """创建规则请求"""
    name: str
    conditions: str  # JSON
    value: str  # JSON
    priority: int = 100
    is_enabled: bool = True


# ========== 用户端 API ==========

@router.post("/evaluate", response_model=FlagEvaluateResponse)
async def evaluate_flags(
    request_data: FlagEvaluateRequest,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    批量评估功能开关
    
    前端启动时调用，获取所有需要的功能开关状态
    """
    service = FeatureFlagService(db)
    
    # 构建用户上下文
    user_context = {
        "user_id": current_user.id if current_user else None,
        "vip_level": 0,
        "is_guest": True,
        "device": request.headers.get("X-Device-Type", "web"),
        "app_version": request.headers.get("X-App-Version", "1.0.0"),
        "region": request.headers.get("X-Region", "unknown"),
    }
    
    if current_user:
        user_context["is_guest"] = current_user.is_guest
        user_context["role"] = current_user.role.value if current_user.role else "user"
        # TODO: 获取VIP等级
    
    results = await service.get_all_flags(user_context, request_data.flag_keys)
    
    return FlagEvaluateResponse(flags=results)


@router.post("/track-event")
async def track_event(
    event_data: TrackEventRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    追踪实验事件（转化数据）
    """
    service = FeatureFlagService(db)
    
    await service.track_event(
        flag_key=event_data.flag_key,
        user_id=current_user.id,
        event_type=event_data.event_type,
        event_value=event_data.event_value,
        event_data=event_data.event_data
    )
    
    return {"success": True}


# ========== 管理端 API ==========

@router.get("/admin/list")
async def list_flags(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取功能开关列表（管理员）"""
    query = select(FeatureFlag)
    
    if search:
        query = query.where(
            (FeatureFlag.key.ilike(f"%{search}%")) |
            (FeatureFlag.name.ilike(f"%{search}%"))
        )
    
    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()
    
    # 分页
    query = query.order_by(FeatureFlag.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    flags = result.scalars().all()
    
    return {
        "items": [
            {
                "id": f.id,
                "key": f.key,
                "name": f.name,
                "description": f.description,
                "flag_type": f.flag_type,
                "is_enabled": f.is_enabled,
                "rollout_percentage": f.rollout_percentage,
                "exposure_count": f.exposure_count,
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "updated_at": f.updated_at.isoformat() if f.updated_at else None,
            }
            for f in flags
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/admin/create")
async def create_flag(
    flag_data: FlagCreateRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """创建功能开关（管理员）"""
    # 检查key是否已存在
    result = await db.execute(
        select(FeatureFlag).where(FeatureFlag.key == flag_data.key)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="功能开关Key已存在"
        )
    
    flag = FeatureFlag(
        key=flag_data.key,
        name=flag_data.name,
        description=flag_data.description,
        flag_type=flag_data.flag_type,
        is_enabled=flag_data.is_enabled,
        default_value=flag_data.default_value,
        variants=flag_data.variants,
        rollout_percentage=flag_data.rollout_percentage,
        whitelist_user_ids=flag_data.whitelist_user_ids,
        start_time=flag_data.start_time,
        end_time=flag_data.end_time
    )
    
    db.add(flag)
    await db.commit()
    await db.refresh(flag)
    
    return {
        "id": flag.id,
        "key": flag.key,
        "message": "创建成功"
    }


@router.get("/admin/{flag_id}")
async def get_flag(
    flag_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取功能开关详情（管理员）"""
    result = await db.execute(
        select(FeatureFlag).where(FeatureFlag.id == flag_id)
    )
    flag = result.scalar_one_or_none()
    
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="功能开关不存在"
        )
    
    # 获取规则
    rules_result = await db.execute(
        select(FeatureRule)
        .where(FeatureRule.flag_id == flag_id)
        .order_by(FeatureRule.priority)
    )
    rules = rules_result.scalars().all()
    
    return {
        "id": flag.id,
        "key": flag.key,
        "name": flag.name,
        "description": flag.description,
        "flag_type": flag.flag_type,
        "is_enabled": flag.is_enabled,
        "default_value": flag.default_value,
        "variants": flag.variants,
        "rollout_percentage": flag.rollout_percentage,
        "whitelist_user_ids": flag.whitelist_user_ids,
        "start_time": flag.start_time.isoformat() if flag.start_time else None,
        "end_time": flag.end_time.isoformat() if flag.end_time else None,
        "exposure_count": flag.exposure_count,
        "created_at": flag.created_at.isoformat() if flag.created_at else None,
        "updated_at": flag.updated_at.isoformat() if flag.updated_at else None,
        "rules": [
            {
                "id": r.id,
                "name": r.name,
                "conditions": r.conditions,
                "value": r.value,
                "priority": r.priority,
                "is_enabled": r.is_enabled,
            }
            for r in rules
        ]
    }


@router.put("/admin/{flag_id}")
async def update_flag(
    flag_id: int,
    flag_data: FlagUpdateRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新功能开关（管理员）"""
    result = await db.execute(
        select(FeatureFlag).where(FeatureFlag.id == flag_id)
    )
    flag = result.scalar_one_or_none()
    
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="功能开关不存在"
        )
    
    # 更新字段
    update_data = flag_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(flag, key, value)
    
    await db.commit()
    
    # 使缓存失效
    await FeatureFlagService.invalidate_cache(flag.key)
    
    return {"message": "更新成功"}


@router.delete("/admin/{flag_id}")
async def delete_flag(
    flag_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """删除功能开关（管理员）"""
    result = await db.execute(
        select(FeatureFlag).where(FeatureFlag.id == flag_id)
    )
    flag = result.scalar_one_or_none()
    
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="功能开关不存在"
        )
    
    flag_key = flag.key
    await db.delete(flag)
    await db.commit()
    
    # 使缓存失效
    await FeatureFlagService.invalidate_cache(flag_key)
    
    return {"message": "删除成功"}


@router.post("/admin/{flag_id}/toggle")
async def toggle_flag(
    flag_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """快速切换功能开关状态（管理员）"""
    result = await db.execute(
        select(FeatureFlag).where(FeatureFlag.id == flag_id)
    )
    flag = result.scalar_one_or_none()
    
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="功能开关不存在"
        )
    
    flag.is_enabled = not flag.is_enabled
    await db.commit()
    
    # 使缓存失效
    await FeatureFlagService.invalidate_cache(flag.key)
    
    return {
        "message": "状态已切换",
        "is_enabled": flag.is_enabled
    }


@router.post("/admin/{flag_id}/rules")
async def create_rule(
    flag_id: int,
    rule_data: RuleCreateRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """添加规则（管理员）"""
    # 检查功能开关是否存在
    result = await db.execute(
        select(FeatureFlag).where(FeatureFlag.id == flag_id)
    )
    flag = result.scalar_one_or_none()
    
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="功能开关不存在"
        )
    
    rule = FeatureRule(
        flag_id=flag_id,
        name=rule_data.name,
        conditions=rule_data.conditions,
        value=rule_data.value,
        priority=rule_data.priority,
        is_enabled=rule_data.is_enabled
    )
    
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    
    # 使缓存失效
    await FeatureFlagService.invalidate_cache(flag.key)
    
    return {
        "id": rule.id,
        "message": "规则创建成功"
    }


@router.delete("/admin/rules/{rule_id}")
async def delete_rule(
    rule_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """删除规则（管理员）"""
    result = await db.execute(
        select(FeatureRule).where(FeatureRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="规则不存在"
        )
    
    # 获取关联的功能开关key用于清除缓存
    flag_result = await db.execute(
        select(FeatureFlag).where(FeatureFlag.id == rule.flag_id)
    )
    flag = flag_result.scalar_one_or_none()
    
    await db.delete(rule)
    await db.commit()
    
    if flag:
        await FeatureFlagService.invalidate_cache(flag.key)
    
    return {"message": "规则删除成功"}


# ========== 数据分析 API ==========

@router.get("/admin/{flag_id}/stats")
async def get_flag_stats(
    flag_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取功能开关统计数据（管理员）"""
    result = await db.execute(
        select(FeatureFlag).where(FeatureFlag.id == flag_id)
    )
    flag = result.scalar_one_or_none()
    
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="功能开关不存在"
        )
    
    # 曝光统计（按变体）
    exposure_stats = await db.execute(
        select(
            ExperimentExposure.variant_name,
            func.count(func.distinct(ExperimentExposure.user_id)).label("user_count")
        )
        .where(ExperimentExposure.flag_key == flag.key)
        .group_by(ExperimentExposure.variant_name)
    )
    exposure_data = {row.variant_name: row.user_count for row in exposure_stats}
    
    # 事件统计（按变体和事件类型）
    event_stats = await db.execute(
        select(
            ExperimentEvent.variant_name,
            ExperimentEvent.event_type,
            func.count(func.distinct(ExperimentEvent.user_id)).label("user_count"),
            func.sum(ExperimentEvent.event_value).label("total_value")
        )
        .where(ExperimentEvent.flag_key == flag.key)
        .group_by(ExperimentEvent.variant_name, ExperimentEvent.event_type)
    )
    
    event_data = {}
    for row in event_stats:
        if row.variant_name not in event_data:
            event_data[row.variant_name] = {}
        event_data[row.variant_name][row.event_type] = {
            "user_count": row.user_count,
            "total_value": float(row.total_value) if row.total_value else 0
        }
    
    # 计算转化率
    conversion_rates = {}
    for variant, events in event_data.items():
        exposed_users = exposure_data.get(variant, 0)
        if exposed_users > 0:
            conversion_rates[variant] = {}
            for event_type, data in events.items():
                conversion_rates[variant][event_type] = round(
                    data["user_count"] / exposed_users * 100, 2
                )
    
    return {
        "flag_key": flag.key,
        "exposure": exposure_data,
        "events": event_data,
        "conversion_rates": conversion_rates
    }


