"""
推广系统 API - 分享送VIP + 代理系统
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel
from decimal import Decimal
import random
import string

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User, UserVIP
from app.models.promotion import (
    UserProfile, Invitation, Commission, Withdrawal,
    Reward, AgentRelation, InviteMilestone, PromotionConfig
)

router = APIRouter(prefix="/promotion", tags=["推广系统"])


# ==================== Schemas ====================

class InviteCodeResponse(BaseModel):
    invite_code: str
    invite_url: str
    qr_code_url: str


class InviteStatsResponse(BaseModel):
    total_invites: int
    valid_invites: int
    total_reward_days: int
    pending_rewards: int


class InvitationRecord(BaseModel):
    id: int
    invitee_username: str
    invitee_avatar: Optional[str]
    is_valid: bool
    register_rewarded: bool
    recharge_rewarded: bool
    created_at: datetime


class RewardRecord(BaseModel):
    id: int
    reward_type: str
    reward_content: str
    reward_value: float
    reward_desc: Optional[str]
    claimed: bool
    created_at: datetime


class AgentInfoResponse(BaseModel):
    agent_level: int
    agent_level_name: str
    commission_rate: float
    total_commission: float
    available_balance: float
    frozen_balance: float
    total_withdrawn: float
    total_team_size: int
    agent_status: str
    # 新增统计数据
    month_commission: float = 0
    month_invites: int = 0
    today_commission: float = 0
    today_invites: int = 0
    direct_invites: int = 0
    direct_paid_users: int = 0


class CommissionRecord(BaseModel):
    id: int
    from_username: str
    order_amount: float
    commission_type: str
    commission_rate: float
    commission_amount: float
    status: str
    created_at: datetime


class WithdrawRequest(BaseModel):
    amount: float
    withdraw_type: str  # alipay/wechat/bank
    account_name: str
    account_number: str
    bank_name: Optional[str] = None


class WithdrawRecord(BaseModel):
    id: int
    amount: float
    fee: float
    actual_amount: float
    withdraw_type: str
    status: str
    reject_reason: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]


# ==================== Helper Functions ====================

def generate_invite_code(length: int = 8) -> str:
    """生成邀请码"""
    chars = string.ascii_uppercase + string.digits
    # 排除容易混淆的字符
    chars = chars.replace('O', '').replace('0', '').replace('I', '').replace('1', '').replace('L', '')
    return ''.join(random.choice(chars) for _ in range(length))


def get_agent_level_name(level: int) -> str:
    """获取代理等级名称"""
    level_names = {
        0: "普通用户",
        1: "推广达人",
        2: "普通代理",
        3: "高级代理",
        4: "超级代理"
    }
    return level_names.get(level, "普通用户")


def get_commission_rate(level: int) -> Decimal:
    """获取佣金比例"""
    rates = {
        0: Decimal("0"),
        1: Decimal("0.08"),   # 推广达人 8%
        2: Decimal("0.15"),   # 普通代理 15%
        3: Decimal("0.30"),   # 高级代理 30%
        4: Decimal("0.50"),   # 超级代理 50%
    }
    return rates.get(level, Decimal("0"))


async def get_or_create_profile(db: AsyncSession, user_id: int) -> UserProfile:
    """获取或创建用户推广资料"""
    try:
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            # 基于用户ID生成唯一邀请码（无需检查重复）
            from app.core.invite_code import encode_user_id
            code = encode_user_id(user_id)
            
            profile = UserProfile(
                user_id=user_id,
                invite_code=code,
                agent_level=0,
                commission_rate=Decimal("0"),
                agent_status="inactive",
                total_invites=0,
                valid_invites=0,
                total_team_size=0,
                total_commission=Decimal("0"),
                available_balance=Decimal("0"),
                frozen_balance=Decimal("0"),
                total_withdrawn=Decimal("0"),
                total_reward_days=0
            )
            db.add(profile)
            await db.commit()
            await db.refresh(profile)
        
        return profile
    except Exception as e:
        print(f"[ERROR] get_or_create_profile: {e}")
        await db.rollback()
        raise


async def auto_grant_milestone_rewards(db: AsyncSession, user_id: int, valid_invites: int):
    """
    自动发放里程碑奖励
    当用户有效邀请数增加时调用,自动检测并发放所有达到的里程碑奖励
    
    Args:
        db: 数据库会话
        user_id: 邀请人用户ID
        valid_invites: 当前有效邀请数
    
    Returns:
        (total_days_granted, milestones_granted): 发放的VIP天数和达成的里程碑列表
    """
    # 获取所有活跃的里程碑配置
    result = await db.execute(
        select(InviteMilestone).where(
            InviteMilestone.is_active == True
        ).order_by(InviteMilestone.invite_count)
    )
    milestones = result.scalars().all()
    
    # 获取已发放的里程碑奖励
    claimed_result = await db.execute(
        select(Reward.source_id).where(
            and_(
                Reward.user_id == user_id,
                Reward.source_type == "milestone"
            )
        )
    )
    claimed_ids = set(r[0] for r in claimed_result.all())
    
    total_days_granted = 0
    milestones_granted = []
    
    for milestone in milestones:
        # 检查是否达到此里程碑且未发放过
        if valid_invites >= milestone.invite_count and milestone.id not in claimed_ids:
            # 创建奖励记录（已自动领取）
            reward = Reward(
                user_id=user_id,
                reward_type="milestone",
                reward_content=milestone.reward_type,
                reward_value=milestone.reward_value,
                reward_desc=milestone.reward_desc or f"邀请{milestone.invite_count}人里程碑奖励",
                source_type="milestone",
                source_id=milestone.id,
                claimed=True,
                claimed_at=datetime.utcnow()
            )
            db.add(reward)
            
            # 如果是VIP天数奖励，直接发放
            if milestone.reward_type == "vip_days":
                vip_days = int(milestone.reward_value)
                total_days_granted += vip_days
                
                # 更新用户VIP
                vip_result = await db.execute(
                    select(UserVIP).where(UserVIP.user_id == user_id)
                )
                vip = vip_result.scalar_one_or_none()
                
                if vip:
                    if vip.expire_date and vip.expire_date > datetime.utcnow():
                        vip.expire_date += timedelta(days=vip_days)
                    else:
                        vip.expire_date = datetime.utcnow() + timedelta(days=vip_days)
                    vip.is_active = True
                    if vip.vip_level == 0:
                        vip.vip_level = 1
                else:
                    vip = UserVIP(
                        user_id=user_id,
                        vip_level=1,
                        is_active=True,
                        expire_date=datetime.utcnow() + timedelta(days=vip_days)
                    )
                    db.add(vip)
            
            milestones_granted.append({
                "invite_count": milestone.invite_count,
                "reward_type": milestone.reward_type,
                "reward_value": float(milestone.reward_value),
                "reward_desc": milestone.reward_desc
            })
            
            print(f"[Milestone] User {user_id} reached {milestone.invite_count} invites, granted {milestone.reward_value} {milestone.reward_type}")
    
    # 更新用户累计奖励天数
    if total_days_granted > 0:
        profile_result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()
        if profile:
            profile.total_reward_days = (profile.total_reward_days or 0) + total_days_granted
    
    return total_days_granted, milestones_granted


# ==================== 邀请码相关 API ====================

@router.get("/invite-code", response_model=InviteCodeResponse)
async def get_invite_code(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户邀请码和分享链接"""
    profile = await get_or_create_profile(db, current_user.id)
    
    # 构建邀请链接
    base_url = str(request.base_url).rstrip('/')
    invite_url = f"{base_url}/register?invite={profile.invite_code}"
    qr_code_url = f"{base_url}/api/v1/promotion/qrcode/{profile.invite_code}"
    
    return InviteCodeResponse(
        invite_code=profile.invite_code,
        invite_url=invite_url,
        qr_code_url=qr_code_url
    )


@router.get("/invite-stats", response_model=InviteStatsResponse)
async def get_invite_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取邀请统计"""
    profile = await get_or_create_profile(db, current_user.id)
    
    # 获取待领取奖励数量
    pending_result = await db.execute(
        select(func.count(Reward.id)).where(
            and_(
                Reward.user_id == current_user.id,
                Reward.claimed == False
            )
        )
    )
    pending_rewards = pending_result.scalar() or 0
    
    return InviteStatsResponse(
        total_invites=profile.total_invites or 0,
        valid_invites=profile.valid_invites or 0,
        total_reward_days=profile.total_reward_days or 0,
        pending_rewards=pending_rewards or 0
    )


@router.get("/invitations", response_model=List[InvitationRecord])
async def get_invitations(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取邀请记录列表"""
    offset = (page - 1) * page_size
    
    result = await db.execute(
        select(Invitation, User).join(
            User, Invitation.invitee_id == User.id
        ).where(
            Invitation.inviter_id == current_user.id
        ).order_by(
            Invitation.created_at.desc()
        ).offset(offset).limit(page_size)
    )
    
    records = []
    for invitation, invitee in result.all():
        records.append(InvitationRecord(
            id=invitation.id,
            invitee_username=invitee.username,
            invitee_avatar=invitee.avatar if hasattr(invitee, 'avatar') else None,
            is_valid=invitation.is_valid,
            register_rewarded=invitation.register_rewarded,
            recharge_rewarded=invitation.recharge_rewarded,
            created_at=invitation.created_at
        ))
    
    return records


# ==================== 奖励相关 API ====================

@router.get("/rewards", response_model=List[RewardRecord])
async def get_rewards(
    page: int = 1,
    page_size: int = 20,
    claimed: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取奖励记录"""
    offset = (page - 1) * page_size
    
    query = select(Reward).where(Reward.user_id == current_user.id)
    
    if claimed is not None:
        query = query.where(Reward.claimed == claimed)
    
    result = await db.execute(
        query.order_by(Reward.created_at.desc()).offset(offset).limit(page_size)
    )
    
    records = []
    for reward in result.scalars().all():
        records.append(RewardRecord(
            id=reward.id,
            reward_type=reward.reward_type,
            reward_content=reward.reward_content,
            reward_value=float(reward.reward_value),
            reward_desc=reward.reward_desc,
            claimed=reward.claimed,
            created_at=reward.created_at
        ))
    
    return records


@router.post("/rewards/{reward_id}/claim")
async def claim_reward(
    reward_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """领取奖励"""
    # 获取奖励
    result = await db.execute(
        select(Reward).where(
            and_(
                Reward.id == reward_id,
                Reward.user_id == current_user.id
            )
        )
    )
    reward = result.scalar_one_or_none()
    
    if not reward:
        raise HTTPException(status_code=404, detail="奖励不存在")
    
    if reward.claimed:
        raise HTTPException(status_code=400, detail="奖励已领取")
    
    if reward.expire_at and reward.expire_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="奖励已过期")
    
    # 发放奖励
    if reward.reward_content == "vip_days":
        # 增加VIP天数
        vip_result = await db.execute(
            select(UserVIP).where(UserVIP.user_id == current_user.id)
        )
        vip = vip_result.scalar_one_or_none()
        
        if vip:
            if vip.expire_date and vip.expire_date > datetime.utcnow():
                vip.expire_date += timedelta(days=int(reward.reward_value))
            else:
                vip.expire_date = datetime.utcnow() + timedelta(days=int(reward.reward_value))
            vip.is_active = True
            if vip.vip_level == 0:
                vip.vip_level = 1
        else:
            vip = UserVIP(
                user_id=current_user.id,
                vip_level=1,
                is_active=True,
                expire_date=datetime.utcnow() + timedelta(days=int(reward.reward_value))
            )
            db.add(vip)
    
    elif reward.reward_content == "cash":
        # 增加余额
        profile = await get_or_create_profile(db, current_user.id)
        profile.available_balance += Decimal(str(reward.reward_value))
    
    # 标记已领取
    reward.claimed = True
    reward.claimed_at = datetime.utcnow()
    
    await db.commit()
    
    return {"success": True, "message": "奖励领取成功"}


@router.post("/rewards/claim-all")
async def claim_all_rewards(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """一键领取所有奖励"""
    result = await db.execute(
        select(Reward).where(
            and_(
                Reward.user_id == current_user.id,
                Reward.claimed == False
            )
        )
    )
    rewards = result.scalars().all()
    
    if not rewards:
        raise HTTPException(status_code=400, detail="没有可领取的奖励")
    
    total_vip_days = 0
    total_cash = Decimal("0")
    
    for reward in rewards:
        if reward.expire_at and reward.expire_at < datetime.utcnow():
            continue
        
        if reward.reward_content == "vip_days":
            total_vip_days += int(reward.reward_value)
        elif reward.reward_content == "cash":
            total_cash += Decimal(str(reward.reward_value))
        
        reward.claimed = True
        reward.claimed_at = datetime.utcnow()
    
    # 批量发放VIP天数
    if total_vip_days > 0:
        vip_result = await db.execute(
            select(UserVIP).where(UserVIP.user_id == current_user.id)
        )
        vip = vip_result.scalar_one_or_none()
        
        if vip:
            if vip.expire_date and vip.expire_date > datetime.utcnow():
                vip.expire_date += timedelta(days=total_vip_days)
            else:
                vip.expire_date = datetime.utcnow() + timedelta(days=total_vip_days)
            vip.is_active = True
            if vip.vip_level == 0:
                vip.vip_level = 1
        else:
            vip = UserVIP(
                user_id=current_user.id,
                vip_level=1,
                is_active=True,
                expire_date=datetime.utcnow() + timedelta(days=total_vip_days)
            )
            db.add(vip)
    
    # 批量发放现金
    if total_cash > 0:
        profile = await get_or_create_profile(db, current_user.id)
        profile.available_balance += total_cash
    
    await db.commit()
    
    return {
        "success": True,
        "message": "奖励领取成功",
        "vip_days": total_vip_days,
        "cash": float(total_cash)
    }


# ==================== 代理相关 API ====================

@router.get("/agent/info", response_model=AgentInfoResponse)
async def get_agent_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取代理信息"""
    from datetime import datetime, timedelta
    from sqlalchemy import and_, extract
    
    profile = await get_or_create_profile(db, current_user.id)
    
    # 获取当前时间
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 计算当月佣金
    month_commission_result = await db.execute(
        select(func.sum(Commission.commission_amount))
        .where(
            and_(
                Commission.agent_id == current_user.id,
                Commission.created_at >= month_start
            )
        )
    )
    month_commission = float(month_commission_result.scalar() or 0)
    
    # 计算今日佣金
    today_commission_result = await db.execute(
        select(func.sum(Commission.commission_amount))
        .where(
            and_(
                Commission.agent_id == current_user.id,
                Commission.created_at >= today_start
            )
        )
    )
    today_commission = float(today_commission_result.scalar() or 0)
    
    # 计算当月邀请数
    month_invites_result = await db.execute(
        select(func.count(Invitation.id))
        .where(
            and_(
                Invitation.inviter_id == current_user.id,
                Invitation.created_at >= month_start
            )
        )
    )
    month_invites = month_invites_result.scalar() or 0
    
    # 计算今日邀请数
    today_invites_result = await db.execute(
        select(func.count(Invitation.id))
        .where(
            and_(
                Invitation.inviter_id == current_user.id,
                Invitation.created_at >= today_start
            )
        )
    )
    today_invites = today_invites_result.scalar() or 0
    
    # 直推用户数（总邀请）
    direct_invites = profile.total_invites or 0
    
    # 直推付费用户（有效邀请）
    direct_paid_users = profile.valid_invites or 0
    
    return AgentInfoResponse(
        agent_level=profile.agent_level or 0,
        agent_level_name=get_agent_level_name(profile.agent_level or 0),
        commission_rate=float(profile.commission_rate or 0),
        total_commission=float(profile.total_commission or 0),
        available_balance=float(profile.available_balance or 0),
        frozen_balance=float(profile.frozen_balance or 0),
        total_withdrawn=float(profile.total_withdrawn or 0),
        total_team_size=profile.total_team_size or 0,
        agent_status=profile.agent_status or "inactive",
        month_commission=month_commission,
        month_invites=month_invites,
        today_commission=today_commission,
        today_invites=today_invites,
        direct_invites=direct_invites,
        direct_paid_users=direct_paid_users
    )


@router.post("/agent/apply")
async def apply_agent(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """申请成为代理"""
    profile = await get_or_create_profile(db, current_user.id)
    
    if profile.agent_level > 0:
        raise HTTPException(status_code=400, detail="您已经是代理了")
    
    if profile.agent_status == "pending":
        raise HTTPException(status_code=400, detail="您的申请正在审核中")
    
    # 检查邀请人数是否满足条件
    if profile.valid_invites < 10:
        raise HTTPException(status_code=400, detail="需要邀请至少10人才能申请代理")
    
    profile.agent_status = "pending"
    profile.agent_applied_at = datetime.utcnow()
    
    await db.commit()
    
    return {"success": True, "message": "申请已提交，请等待审核"}


@router.get("/agent/commissions", response_model=List[CommissionRecord])
async def get_commissions(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取佣金记录"""
    profile = await get_or_create_profile(db, current_user.id)
    
    if profile.agent_level == 0:
        raise HTTPException(status_code=403, detail="您不是代理，无法查看佣金记录")
    
    offset = (page - 1) * page_size
    
    query = select(Commission, User).outerjoin(
        User, Commission.from_user_id == User.id
    ).where(Commission.agent_id == current_user.id)
    
    if status:
        query = query.where(Commission.status == status)
    
    result = await db.execute(
        query.order_by(Commission.created_at.desc()).offset(offset).limit(page_size)
    )
    
    records = []
    for commission, from_user in result.all():
        records.append(CommissionRecord(
            id=commission.id,
            from_username=from_user.username if from_user else "未知用户",
            order_amount=float(commission.order_amount),
            commission_type=commission.commission_type,
            commission_rate=float(commission.commission_rate),
            commission_amount=float(commission.commission_amount),
            status=commission.status,
            created_at=commission.created_at
        ))
    
    return records


# ==================== 提现相关 API ====================

@router.post("/withdraw/apply")
async def apply_withdraw(
    request: WithdrawRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """申请提现"""
    from app.models.system_config import SystemConfig
    
    profile = await get_or_create_profile(db, current_user.id)
    
    if profile.agent_level == 0:
        raise HTTPException(status_code=403, detail="您不是代理，无法提现")
    
    # 获取配置
    config_result = await db.execute(
        select(SystemConfig).where(SystemConfig.group_name == "withdraw")
    )
    configs = {c.key: c.value for c in config_result.scalars().all()}
    
    min_withdraw = float(configs.get("withdraw_min_amount", "250"))
    max_withdraw = float(configs.get("withdraw_max_amount", "10000"))
    fee_rate = float(configs.get("withdraw_fee_rate", "20")) / 100
    
    if request.amount < min_withdraw:
        raise HTTPException(status_code=400, detail=f"最低提现金额为{min_withdraw}元")
    
    if request.amount > max_withdraw:
        raise HTTPException(status_code=400, detail=f"单笔提现最大{max_withdraw}元")
    
    if Decimal(str(request.amount)) > profile.available_balance:
        raise HTTPException(status_code=400, detail="余额不足")
    
    # 计算手续费
    fee = Decimal(str(request.amount)) * Decimal(str(fee_rate))
    actual_amount = Decimal(str(request.amount)) - fee
    
    # 创建提现记录
    withdrawal = Withdrawal(
        user_id=current_user.id,
        amount=Decimal(str(request.amount)),
        fee=fee,
        actual_amount=actual_amount,
        withdraw_type=request.withdraw_type,
        account_name=request.account_name,
        account_number=request.account_number,
        bank_name=request.bank_name,
        status="pending"
    )
    db.add(withdrawal)
    
    # 冻结余额
    profile.available_balance -= Decimal(str(request.amount))
    profile.frozen_balance += Decimal(str(request.amount))
    
    await db.commit()
    
    return {
        "success": True,
        "message": "提现申请已提交",
        "amount": float(request.amount),
        "fee": float(fee),
        "actual_amount": float(actual_amount)
    }


@router.get("/withdraw/records", response_model=List[WithdrawRecord])
async def get_withdraw_records(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取提现记录"""
    offset = (page - 1) * page_size
    
    result = await db.execute(
        select(Withdrawal).where(
            Withdrawal.user_id == current_user.id
        ).order_by(
            Withdrawal.created_at.desc()
        ).offset(offset).limit(page_size)
    )
    
    records = []
    for withdrawal in result.scalars().all():
        records.append(WithdrawRecord(
            id=withdrawal.id,
            amount=float(withdrawal.amount),
            fee=float(withdrawal.fee),
            actual_amount=float(withdrawal.actual_amount),
            withdraw_type=withdrawal.withdraw_type,
            status=withdrawal.status,
            reject_reason=withdrawal.reject_reason,
            created_at=withdrawal.created_at,
            processed_at=withdrawal.processed_at
        ))
    
    return records


# ==================== 里程碑相关 API ====================

@router.get("/milestones")
async def get_milestones(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取里程碑奖励配置和完成状态"""
    profile = await get_or_create_profile(db, current_user.id)
    
    result = await db.execute(
        select(InviteMilestone).where(
            InviteMilestone.is_active == True
        ).order_by(InviteMilestone.invite_count)
    )
    milestones = result.scalars().all()
    
    # 获取已领取的里程碑奖励
    claimed_result = await db.execute(
        select(Reward.source_id).where(
            and_(
                Reward.user_id == current_user.id,
                Reward.source_type == "milestone",
                Reward.claimed == True
            )
        )
    )
    claimed_ids = [r[0] for r in claimed_result.all()]
    
    milestone_list = []
    for m in milestones:
        milestone_list.append({
            "id": m.id,
            "invite_count": m.invite_count,
            "reward_type": m.reward_type,
            "reward_value": float(m.reward_value),
            "reward_desc": m.reward_desc,
            "unlocked": profile.valid_invites >= m.invite_count,
            "claimed": m.id in claimed_ids
        })
    
    return {
        "current_invites": profile.valid_invites,
        "milestones": milestone_list
    }


@router.post("/milestones/{milestone_id}/claim")
async def claim_milestone(
    milestone_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """领取里程碑奖励"""
    profile = await get_or_create_profile(db, current_user.id)
    
    # 获取里程碑
    result = await db.execute(
        select(InviteMilestone).where(InviteMilestone.id == milestone_id)
    )
    milestone = result.scalar_one_or_none()
    
    if not milestone:
        raise HTTPException(status_code=404, detail="里程碑不存在")
    
    if profile.valid_invites < milestone.invite_count:
        raise HTTPException(status_code=400, detail="未达到邀请人数要求")
    
    # 检查是否已领取
    existing = await db.execute(
        select(Reward).where(
            and_(
                Reward.user_id == current_user.id,
                Reward.source_type == "milestone",
                Reward.source_id == milestone_id
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="已领取过该奖励")
    
    # 创建奖励记录
    reward = Reward(
        user_id=current_user.id,
        reward_type="milestone",
        reward_content=milestone.reward_type,
        reward_value=milestone.reward_value,
        reward_desc=milestone.reward_desc,
        source_type="milestone",
        source_id=milestone_id,
        claimed=False
    )
    db.add(reward)
    await db.commit()
    
    return {"success": True, "message": "奖励已创建，请前往领取"}
