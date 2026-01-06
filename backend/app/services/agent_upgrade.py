"""
代理自动升级服务
当用户邀请的人成功充值后，自动检查并升级代理等级
"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.promotion import UserProfile
from app.models.system_config import SystemConfig


async def get_level_configs(db: AsyncSession) -> dict:
    """
    从数据库获取所有代理等级配置
    返回: {level: {name, rate, min_users, min_sub_agents, min_sub_level}, ...}
    """
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.group_name == "agent_levels")
    )
    configs = result.scalars().all()
    
    config_dict = {c.key: c.value for c in configs}
    
    level_configs = {}
    for i in range(1, 7):  # 等级1-6
        name = config_dict.get(f"agent_level_{i}_name")
        if name:
            level_configs[i] = {
                "name": name,
                "rate": Decimal(str(int(config_dict.get(f"agent_level_{i}_rate", "40")) / 100)),
                "min_users": int(config_dict.get(f"agent_level_{i}_min_users", "0")),
                "min_sub_agents": int(config_dict.get(f"agent_level_{i}_min_sub_agents", "0")),
                "min_sub_level": int(config_dict.get(f"agent_level_{i}_min_sub_level", "0"))
            }
    
    return level_configs


async def count_sub_agents(db: AsyncSession, user_id: int, min_level: int) -> int:
    """
    统计直属代理数量（达到指定等级以上的）
    """
    result = await db.execute(
        select(func.count(UserProfile.id))
        .where(UserProfile.inviter_id == user_id)
        .where(UserProfile.agent_level >= min_level)
    )
    return result.scalar() or 0


async def get_or_create_profile(db: AsyncSession, user_id: int) -> UserProfile:
    """获取或创建用户推广资料"""
    import random
    
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        # 基于用户ID生成唯一邀请码
        from app.core.invite_code import encode_user_id
        code = encode_user_id(user_id)
        
        profile = UserProfile(
            user_id=user_id,
            invite_code=code
        )
        db.add(profile)
        await db.flush()
    
    return profile


async def auto_upgrade_agent(db: AsyncSession, user_id: int) -> tuple:
    """
    自动检查并升级代理等级
    
    Args:
        db: 数据库会话
        user_id: 邀请人的用户ID
        
    Returns:
        (upgraded: bool, new_level: int, level_name: str)
    """
    # 获取用户推广资料
    profile = await get_or_create_profile(db, user_id)
    valid_invites = profile.valid_invites or 0  # 有效邀请数（已充值）
    
    # 获取等级配置
    level_configs = await get_level_configs(db)
    
    if not level_configs:
        # 使用默认配置
        level_configs = {
            1: {"name": "普通级", "rate": Decimal("0.40"), "min_users": 1, "min_sub_agents": 0, "min_sub_level": 0},
            2: {"name": "青铜级", "rate": Decimal("0.46"), "min_users": 5, "min_sub_agents": 0, "min_sub_level": 0},
            3: {"name": "白银级", "rate": Decimal("0.52"), "min_users": 20, "min_sub_agents": 2, "min_sub_level": 2},
            4: {"name": "黄金级", "rate": Decimal("0.58"), "min_users": 50, "min_sub_agents": 2, "min_sub_level": 3},
            5: {"name": "铂金级", "rate": Decimal("0.64"), "min_users": 100, "min_sub_agents": 2, "min_sub_level": 4},
            6: {"name": "钻石级", "rate": Decimal("0.70"), "min_users": 400, "min_sub_agents": 2, "min_sub_level": 5},
        }
    
    # 从高到低检查，找到符合条件的最高等级
    new_level = 0
    new_rate = Decimal("0")
    level_name = ""
    
    for level in sorted(level_configs.keys(), reverse=True):
        config = level_configs[level]
        min_users = config["min_users"]
        min_sub_agents = config["min_sub_agents"]
        min_sub_level = config["min_sub_level"]
        
        # 检查有效邀请数
        if valid_invites < min_users:
            continue
        
        # 检查直属代理条件（如果有要求）
        if min_sub_agents > 0:
            sub_count = await count_sub_agents(db, user_id, min_sub_level)
            if sub_count < min_sub_agents:
                continue
        
        # 符合条件
        new_level = level
        new_rate = config["rate"]
        level_name = config["name"]
        break
    
    # 只升不降（防止误降级）
    if new_level > profile.agent_level:
        old_level = profile.agent_level
        
        profile.agent_level = new_level
        profile.commission_rate = new_rate
        
        # 如果之前不是代理，设置申请和激活时间
        if old_level == 0:
            profile.agent_applied_at = datetime.utcnow()  # 设置申请时间（用于列表排序）
        
        if profile.agent_status != "active":
            profile.agent_status = "active"
            profile.agent_approved_at = datetime.utcnow()
        
        await db.commit()
        
        print(f"[Agent Upgrade] User {user_id}: Level {old_level} -> {new_level} ({level_name})")
        
        return True, new_level, level_name
    
    return False, profile.agent_level, ""


async def update_valid_invites(db: AsyncSession, inviter_id: int):
    """
    更新邀请人的有效邀请数 +1
    """
    profile = await get_or_create_profile(db, inviter_id)
    profile.valid_invites = (profile.valid_invites or 0) + 1
    profile.total_invites = (profile.total_invites or 0) + 1
    await db.commit()


当用户邀请的人成功充值后，自动检查并升级代理等级
"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.promotion import UserProfile
from app.models.system_config import SystemConfig


async def get_level_configs(db: AsyncSession) -> dict:
    """
    从数据库获取所有代理等级配置
    返回: {level: {name, rate, min_users, min_sub_agents, min_sub_level}, ...}
    """
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.group_name == "agent_levels")
    )
    configs = result.scalars().all()
    
    config_dict = {c.key: c.value for c in configs}
    
    level_configs = {}
    for i in range(1, 7):  # 等级1-6
        name = config_dict.get(f"agent_level_{i}_name")
        if name:
            level_configs[i] = {
                "name": name,
                "rate": Decimal(str(int(config_dict.get(f"agent_level_{i}_rate", "40")) / 100)),
                "min_users": int(config_dict.get(f"agent_level_{i}_min_users", "0")),
                "min_sub_agents": int(config_dict.get(f"agent_level_{i}_min_sub_agents", "0")),
                "min_sub_level": int(config_dict.get(f"agent_level_{i}_min_sub_level", "0"))
            }
    
    return level_configs


async def count_sub_agents(db: AsyncSession, user_id: int, min_level: int) -> int:
    """
    统计直属代理数量（达到指定等级以上的）
    """
    result = await db.execute(
        select(func.count(UserProfile.id))
        .where(UserProfile.inviter_id == user_id)
        .where(UserProfile.agent_level >= min_level)
    )
    return result.scalar() or 0


async def get_or_create_profile(db: AsyncSession, user_id: int) -> UserProfile:
    """获取或创建用户推广资料"""
    import random
    
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        # 基于用户ID生成唯一邀请码
        from app.core.invite_code import encode_user_id
        code = encode_user_id(user_id)
        
        profile = UserProfile(
            user_id=user_id,
            invite_code=code
        )
        db.add(profile)
        await db.flush()
    
    return profile


async def auto_upgrade_agent(db: AsyncSession, user_id: int) -> tuple:
    """
    自动检查并升级代理等级
    
    Args:
        db: 数据库会话
        user_id: 邀请人的用户ID
        
    Returns:
        (upgraded: bool, new_level: int, level_name: str)
    """
    # 获取用户推广资料
    profile = await get_or_create_profile(db, user_id)
    valid_invites = profile.valid_invites or 0  # 有效邀请数（已充值）
    
    # 获取等级配置
    level_configs = await get_level_configs(db)
    
    if not level_configs:
        # 使用默认配置
        level_configs = {
            1: {"name": "普通级", "rate": Decimal("0.40"), "min_users": 1, "min_sub_agents": 0, "min_sub_level": 0},
            2: {"name": "青铜级", "rate": Decimal("0.46"), "min_users": 5, "min_sub_agents": 0, "min_sub_level": 0},
            3: {"name": "白银级", "rate": Decimal("0.52"), "min_users": 20, "min_sub_agents": 2, "min_sub_level": 2},
            4: {"name": "黄金级", "rate": Decimal("0.58"), "min_users": 50, "min_sub_agents": 2, "min_sub_level": 3},
            5: {"name": "铂金级", "rate": Decimal("0.64"), "min_users": 100, "min_sub_agents": 2, "min_sub_level": 4},
            6: {"name": "钻石级", "rate": Decimal("0.70"), "min_users": 400, "min_sub_agents": 2, "min_sub_level": 5},
        }
    
    # 从高到低检查，找到符合条件的最高等级
    new_level = 0
    new_rate = Decimal("0")
    level_name = ""
    
    for level in sorted(level_configs.keys(), reverse=True):
        config = level_configs[level]
        min_users = config["min_users"]
        min_sub_agents = config["min_sub_agents"]
        min_sub_level = config["min_sub_level"]
        
        # 检查有效邀请数
        if valid_invites < min_users:
            continue
        
        # 检查直属代理条件（如果有要求）
        if min_sub_agents > 0:
            sub_count = await count_sub_agents(db, user_id, min_sub_level)
            if sub_count < min_sub_agents:
                continue
        
        # 符合条件
        new_level = level
        new_rate = config["rate"]
        level_name = config["name"]
        break
    
    # 只升不降（防止误降级）
    if new_level > profile.agent_level:
        old_level = profile.agent_level
        
        profile.agent_level = new_level
        profile.commission_rate = new_rate
        
        # 如果之前不是代理，设置申请和激活时间
        if old_level == 0:
            profile.agent_applied_at = datetime.utcnow()  # 设置申请时间（用于列表排序）
        
        if profile.agent_status != "active":
            profile.agent_status = "active"
            profile.agent_approved_at = datetime.utcnow()
        
        await db.commit()
        
        print(f"[Agent Upgrade] User {user_id}: Level {old_level} -> {new_level} ({level_name})")
        
        return True, new_level, level_name
    
    return False, profile.agent_level, ""


async def update_valid_invites(db: AsyncSession, inviter_id: int):
    """
    更新邀请人的有效邀请数 +1
    """
    profile = await get_or_create_profile(db, inviter_id)
    profile.valid_invites = (profile.valid_invites or 0) + 1
    profile.total_invites = (profile.total_invites or 0) + 1
    await db.commit()

