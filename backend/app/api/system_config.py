"""
系统配置API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List, Dict
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user, get_admin_user
from app.models.user import User
from app.models.system_config import SystemConfig

router = APIRouter()


class ConfigUpdate(BaseModel):
    value: str


class ConfigItem(BaseModel):
    key: str
    value: Optional[str]
    description: Optional[str]
    group_name: Optional[str]


# ========== 公开API（前端使用） ==========

@router.get("/public/{key}")
async def get_public_config(
    key: str,
    db: AsyncSession = Depends(get_db)
):
    """获取单个公开配置"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == key)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        return {"key": key, "value": None}
    
    return {"key": config.key, "value": config.value}


@router.get("/public/group/{group_name}")
async def get_public_config_group(
    group_name: str,
    db: AsyncSession = Depends(get_db)
):
    """获取配置组的所有配置"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.group_name == group_name)
    )
    configs = result.scalars().all()
    
    return {c.key: c.value for c in configs}


@router.get("/credential")
async def get_credential_config(
    db: AsyncSession = Depends(get_db)
):
    """获取账号凭证页配置(公开接口)"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.group_name == "credential")
    )
    configs = result.scalars().all()
    
    config_dict = {c.key: c.value for c in configs}
    
    return {
        "site_name": config_dict.get("credential_site_name", "Soul成人版"),
        "site_url": config_dict.get("credential_site_url", "https://soul9.fm"),
        "tip": config_dict.get("credential_tip", "提示*扫码可直接登录，仅限一台设备使用")
    }


@router.get("/withdraw")
async def get_withdraw_config(
    db: AsyncSession = Depends(get_db)
):
    """获取提现配置(公开接口)"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.group_name == "withdraw")
    )
    configs = result.scalars().all()
    
    config_dict = {c.key: c.value for c in configs}
    
    return {
        "fee_rate": float(config_dict.get("withdraw_fee_rate", "20")),
        "min_amount": float(config_dict.get("withdraw_min_amount", "250")),
        "max_amount": float(config_dict.get("withdraw_max_amount", "10000")),
        "rules": [
            config_dict.get("withdraw_rule_1", "每次提现金额最低250元起，单笔提现最大10000元，且为整数。"),
            config_dict.get("withdraw_rule_2", "每次提现收取20%手续费。"),
            config_dict.get("withdraw_rule_3", "支持银行卡或USDT提现，收款账户卡号与姓名一致，到账时间不超72小时内"),
            config_dict.get("withdraw_rule_4", "申请提现后请随时关注收款账户进款通知，长时间未到账，请及时联系客服")
        ]
    }


@router.get("/agent-levels")
async def get_agent_levels_config(
    db: AsyncSession = Depends(get_db)
):
    """获取代理等级配置(公开接口)"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.group_name == "agent_levels")
    )
    configs = result.scalars().all()
    
    config_dict = {c.key: c.value for c in configs}
    
    # 解析等级配置（从高到低排序显示）
    levels = []
    for i in range(6, 0, -1):
        name = config_dict.get(f"agent_level_{i}_name")
        if name:
            levels.append({
                "level": i,
                "name": name,
                "rate": config_dict.get(f"agent_level_{i}_rate", "0"),
                "condition": config_dict.get(f"agent_level_{i}_condition", "无"),
                "min_users": int(config_dict.get(f"agent_level_{i}_min_users", "0")),
                "min_sub_agents": int(config_dict.get(f"agent_level_{i}_min_sub_agents", "0")),
                "min_sub_level": int(config_dict.get(f"agent_level_{i}_min_sub_level", "0"))
            })
    
    return {"levels": levels}


# ========== 管理API（后台使用） ==========

@router.get("/")
async def get_all_configs(
    group_name: Optional[str] = None,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取所有配置"""
    query = select(SystemConfig)
    if group_name:
        query = query.where(SystemConfig.group_name == group_name)
    query = query.order_by(SystemConfig.group_name, SystemConfig.key)
    
    result = await db.execute(query)
    configs = result.scalars().all()
    
    return [
        {
            "id": c.id,
            "key": c.key,
            "value": c.value,
            "description": c.description,
            "group_name": c.group_name,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        }
        for c in configs
    ]


@router.put("/{key}")
async def update_config(
    key: str,
    data: ConfigUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新配置"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == key)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    config.value = data.value
    await db.commit()
    
    return {"message": "更新成功", "key": key, "value": data.value}


@router.post("/batch")
async def batch_update_configs(
    configs: Dict[str, str],
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """批量更新配置"""
    updated = 0
    for key, value in configs.items():
        result = await db.execute(
            select(SystemConfig).where(SystemConfig.key == key)
        )
        config = result.scalar_one_or_none()
        
        if config:
            config.value = value
            updated += 1
    
    await db.commit()
    return {"message": f"更新了 {updated} 项配置"}


@router.get("/groups")
async def get_config_groups(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取所有配置分组"""
    result = await db.execute(
        select(SystemConfig.group_name).distinct()
    )
    groups = [row[0] for row in result.fetchall()]
    
    group_names = {
        "basic": "基础配置",
        "credential": "账号凭证",
        "share": "分享配置",
        "general": "通用配置",
        "withdraw": "提现配置",
        "agent_levels": "代理等级"
    }
    
    return [
        {"key": g, "name": group_names.get(g, g)}
        for g in groups
    ]
