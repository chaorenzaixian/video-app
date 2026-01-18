"""
API依赖项
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.database import get_db
from app.core.security import decode_token
from app.core.token_blacklist import TokenBlacklist
from app.models.user import User, UserRole

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户（优化版：并行检查黑名单）"""
    import asyncio
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌"
        )
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌类型"
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌内容"
        )
    
    # 并行检查：令牌黑名单 + 用户黑名单 + 查询用户
    async def check_token_blacklist():
        return await TokenBlacklist.is_blacklisted(token)
    
    async def check_user_blacklist():
        return await TokenBlacklist.is_user_blacklisted(int(user_id))
    
    async def get_user():
        result = await db.execute(select(User).where(User.id == int(user_id)))
        return result.scalar_one_or_none()
    
    token_blacklisted, user_blacklisted, user = await asyncio.gather(
        check_token_blacklist(),
        check_user_blacklist(),
        get_user()
    )
    
    if token_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌已失效，请重新登录"
        )
    
    if user_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号已在其他地方登出，请重新登录"
        )
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """获取当前用户（可选）"""
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        payload = decode_token(token)
        
        if payload is None or payload.get("type") != "access":
            return None
        
        user_id = payload.get("sub")
        if user_id is None:
            return None
        
        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        
        if user and user.is_active:
            return user
    except:
        pass
    
    return None


async def get_current_vip_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前VIP用户"""
    from datetime import datetime
    from app.models.user import UserVIP
    
    result = await db.execute(
        select(UserVIP).where(
            UserVIP.user_id == current_user.id,
            UserVIP.is_active == True,
            UserVIP.expire_date > datetime.utcnow()
        )
    )
    vip = result.scalar_one_or_none()
    
    if vip is None and current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要VIP权限"
        )
    
    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取管理员用户"""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def get_super_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取超级管理员用户"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )
    return current_user


# 别名，保持兼容性
get_current_admin = get_admin_user









