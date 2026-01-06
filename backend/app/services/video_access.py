"""
视频访问权限服务 - 统一的权限检查逻辑
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.video import Video
from app.models.user import User, UserVIP
from app.models.coins import VideoPurchase, UserCoins
from app.core.vip_config import (
    VIPLevel,
    get_vip_discount,
    calculate_discounted_price,
    can_watch_free,
    can_download,
    get_daily_download_limit,
    get_vip_level_name,
)


class VideoAccessResult:
    """视频访问权限检查结果"""
    def __init__(
        self,
        can_watch: bool,
        can_download: bool = False,
        is_free: bool = False,
        is_purchased: bool = False,
        is_vip_free: bool = False,
        coin_price: int = 0,
        original_price: int = 0,
        discount_rate: Optional[float] = None,
        free_preview_seconds: int = 0,
        reason: str = "",
        user_coins: int = 0,
        vip_level: int = 0,
        vip_name: str = "",
    ):
        self.can_watch = can_watch
        self.can_download = can_download
        self.is_free = is_free
        self.is_purchased = is_purchased
        self.is_vip_free = is_vip_free
        self.coin_price = coin_price
        self.original_price = original_price
        self.discount_rate = discount_rate
        self.free_preview_seconds = free_preview_seconds
        self.reason = reason
        self.user_coins = user_coins
        self.vip_level = vip_level
        self.vip_name = vip_name
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "can_watch": self.can_watch,
            "can_download": self.can_download,
            "is_free": self.is_free,
            "is_purchased": self.is_purchased,
            "is_vip_free": self.is_vip_free,
            "coin_price": self.coin_price,
            "free_preview_seconds": self.free_preview_seconds,
            "user_coins": self.user_coins,
            "vip_level": self.vip_level,
            "vip_name": self.vip_name,
        }
        if self.original_price > 0 and self.original_price != self.coin_price:
            result["original_price"] = self.original_price
        if self.discount_rate is not None and self.discount_rate < 1:
            result["discount_rate"] = self.discount_rate
        if self.reason:
            result["reason"] = self.reason
        return result


async def get_user_vip_level(db: AsyncSession, user_id: int) -> int:
    """获取用户VIP等级"""
    result = await db.execute(
        select(UserVIP).where(UserVIP.user_id == user_id)
    )
    user_vip = result.scalar_one_or_none()
    
    if not user_vip:
        return 0
    
    if not user_vip.is_active:
        return 0
    
    if user_vip.expire_date and user_vip.expire_date < datetime.utcnow():
        return 0
    
    return user_vip.vip_level or 0


async def get_user_coins(db: AsyncSession, user_id: int) -> int:
    """获取用户金币余额"""
    result = await db.execute(
        select(UserCoins).where(UserCoins.user_id == user_id)
    )
    user_coins = result.scalar_one_or_none()
    return user_coins.balance if user_coins else 0


async def check_video_purchased(db: AsyncSession, user_id: int, video_id: int) -> bool:
    """检查视频是否已购买"""
    result = await db.execute(
        select(VideoPurchase).where(
            VideoPurchase.user_id == user_id,
            VideoPurchase.video_id == video_id
        )
    )
    return result.scalar_one_or_none() is not None


async def check_video_access(
    db: AsyncSession,
    video: Video,
    user: Optional[User] = None,
) -> VideoAccessResult:
    """
    统一检查用户对视频的访问权限
    
    Args:
        db: 数据库会话
        video: 视频对象
        user: 用户对象（可选，未登录时为None）
    
    Returns:
        VideoAccessResult: 访问权限结果
    """
    pay_type = getattr(video, 'pay_type', 'free') or 'free'
    coin_price = getattr(video, 'coin_price', 0) or 0
    vip_coin_price = getattr(video, 'vip_coin_price', None)  # VIP会员价格
    vip_free_level = getattr(video, 'vip_free_level', 0) or 0
    free_preview_seconds = getattr(video, 'free_preview_seconds', 15) or 15
    
    # 免费视频
    if pay_type == 'free' or coin_price <= 0:
        return VideoAccessResult(
            can_watch=True,
            can_download=user is not None,
            is_free=True,
            reason="免费视频"
        )
    
    # 未登录用户
    if user is None:
        return VideoAccessResult(
            can_watch=False,
            is_free=False,
            coin_price=coin_price,
            original_price=coin_price,
            free_preview_seconds=free_preview_seconds,
            reason="请登录后观看"
        )
    
    user_id = user.id
    
    # 获取用户VIP信息
    vip_level = await get_user_vip_level(db, user_id)
    vip_name = get_vip_level_name(vip_level)
    user_coins = await get_user_coins(db, user_id)
    user_can_download = can_download(vip_level)
    
    # 检查是否已购买
    is_purchased = await check_video_purchased(db, user_id, video.id)
    if is_purchased:
        return VideoAccessResult(
            can_watch=True,
            can_download=user_can_download,
            is_purchased=True,
            user_coins=user_coins,
            vip_level=vip_level,
            vip_name=vip_name,
            reason="已购买"
        )
    
    # 黄金至尊(5)及以上全免费
    if vip_level >= VIPLevel.GOLD:
        return VideoAccessResult(
            can_watch=True,
            can_download=user_can_download,
            is_vip_free=True,
            user_coins=user_coins,
            vip_level=vip_level,
            vip_name=vip_name,
            reason=f"{vip_name}会员免费"
        )
    
    # VIP免费类型视频
    if pay_type == 'vip_free' and vip_level > 0 and vip_level >= vip_free_level:
        return VideoAccessResult(
            can_watch=True,
            can_download=user_can_download,
            is_vip_free=True,
            user_coins=user_coins,
            vip_level=vip_level,
            vip_name=vip_name,
            reason=f"{vip_name}会员免费"
        )
    
    # 计算最终价格
    # 优先使用vip_coin_price，如果未设置则使用折扣计算
    if vip_level > 0 and vip_coin_price is not None:
        # VIP会员使用专门设置的VIP价格
        final_price = vip_coin_price
        if final_price == 0:
            # VIP会员价格为0，表示VIP免费
            return VideoAccessResult(
                can_watch=True,
                can_download=user_can_download,
                is_vip_free=True,
                user_coins=user_coins,
                vip_level=vip_level,
                vip_name=vip_name,
                reason=f"{vip_name}会员免费"
            )
        discount_rate = final_price / coin_price if coin_price > 0 else 1.0
    else:
        # 非VIP或未设置VIP价格，使用等级折扣计算
        discount_rate = get_vip_discount(vip_level)
        final_price = calculate_discounted_price(coin_price, vip_level)
    
    return VideoAccessResult(
        can_watch=False,
        can_download=False,
        is_free=False,
        coin_price=final_price,
        original_price=coin_price,
        discount_rate=discount_rate if discount_rate < 1 else None,
        free_preview_seconds=free_preview_seconds,
        user_coins=user_coins,
        vip_level=vip_level,
        vip_name=vip_name,
        reason="需要购买"
    )


async def check_video_access_by_id(
    db: AsyncSession,
    video_id: int,
    user: Optional[User] = None,
) -> Optional[VideoAccessResult]:
    """
    通过视频ID检查访问权限
    
    Returns:
        VideoAccessResult 或 None（视频不存在时）
    """
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        return None
    
    return await check_video_access(db, video, user)



















