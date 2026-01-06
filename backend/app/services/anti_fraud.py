"""
防作弊服务
用于检测和防止推广系统中的作弊行为
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.promotion import Invitation, UserProfile
from app.models.user import User
import hashlib
import re


class AntiFraudService:
    """防作弊服务"""
    
    # 配置
    MAX_INVITES_PER_IP_PER_DAY = 5  # 每个IP每天最多邀请数
    MAX_INVITES_PER_DEVICE_PER_DAY = 3  # 每个设备每天最多邀请数
    MIN_ACCOUNT_AGE_FOR_REWARD = 3600  # 账号最短存活时间（秒）才能算有效邀请
    SUSPICIOUS_PATTERNS = [
        r'^test\d+$',  # test123 等测试账号
        r'^user\d+$',  # user123 等批量账号
        r'^temp\d+$',  # temp123 等临时账号
    ]
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def check_invite_validity(
        self,
        inviter_id: int,
        invitee_id: int,
        device_fingerprint: Optional[str],
        ip_address: Optional[str],
        user_agent: Optional[str]
    ) -> Tuple[bool, Optional[str]]:
        """
        检查邀请是否有效
        返回: (is_valid, invalid_reason)
        """
        
        # 1. 检查是否自己邀请自己
        if inviter_id == invitee_id:
            return False, "自邀无效"
        
        # 2. 检查是否重复邀请
        existing = await self.db.execute(
            select(Invitation).where(
                and_(
                    Invitation.inviter_id == inviter_id,
                    Invitation.invitee_id == invitee_id
                )
            )
        )
        if existing.scalar_one_or_none():
            return False, "重复邀请"
        
        # 3. 检查IP限制
        if ip_address:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ip_count = await self.db.execute(
                select(func.count(Invitation.id)).where(
                    and_(
                        Invitation.ip_address == ip_address,
                        Invitation.created_at >= today_start
                    )
                )
            )
            if (ip_count.scalar() or 0) >= self.MAX_INVITES_PER_IP_PER_DAY:
                return False, f"IP {ip_address} 今日邀请过多"
        
        # 4. 检查设备指纹限制
        if device_fingerprint:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            device_count = await self.db.execute(
                select(func.count(Invitation.id)).where(
                    and_(
                        Invitation.device_fingerprint == device_fingerprint,
                        Invitation.created_at >= today_start
                    )
                )
            )
            if (device_count.scalar() or 0) >= self.MAX_INVITES_PER_DEVICE_PER_DAY:
                return False, "设备今日邀请过多"
        
        # 5. 检查是否循环邀请
        invitee_profile = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == invitee_id)
        )
        invitee_profile = invitee_profile.scalar_one_or_none()
        if invitee_profile and invitee_profile.inviter_id == inviter_id:
            # 被邀请人已经是邀请人的下级，无需重复
            pass
        
        # 检查是否形成循环
        if await self._check_circular_invite(inviter_id, invitee_id):
            return False, "循环邀请无效"
        
        return True, None
    
    async def _check_circular_invite(self, inviter_id: int, invitee_id: int) -> bool:
        """检查是否形成循环邀请链"""
        # 获取邀请人的上级链
        current_id = inviter_id
        visited = set()
        
        for _ in range(10):  # 最多检查10层
            if current_id in visited:
                return True
            visited.add(current_id)
            
            profile = await self.db.execute(
                select(UserProfile).where(UserProfile.user_id == current_id)
            )
            profile = profile.scalar_one_or_none()
            
            if not profile or not profile.inviter_id:
                break
            
            if profile.inviter_id == invitee_id:
                return True
            
            current_id = profile.inviter_id
        
        return False
    
    async def check_username_suspicious(self, username: str) -> bool:
        """检查用户名是否可疑"""
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.match(pattern, username, re.IGNORECASE):
                return True
        return False
    
    async def check_account_age(self, user_id: int) -> bool:
        """检查账号是否存活足够长时间"""
        user = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user.scalar_one_or_none()
        
        if not user:
            return False
        
        account_age = (datetime.utcnow() - user.created_at).total_seconds()
        return account_age >= self.MIN_ACCOUNT_AGE_FOR_REWARD
    
    async def validate_invite_for_reward(
        self,
        invitation_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        验证邀请是否可以发放奖励
        返回: (can_reward, reason)
        """
        invitation = await self.db.execute(
            select(Invitation).where(Invitation.id == invitation_id)
        )
        invitation = invitation.scalar_one_or_none()
        
        if not invitation:
            return False, "邀请记录不存在"
        
        if not invitation.is_valid:
            return False, invitation.invalid_reason or "邀请无效"
        
        if invitation.register_rewarded:
            return False, "已发放过注册奖励"
        
        # 检查被邀请人账号年龄
        if not await self.check_account_age(invitation.invitee_id):
            return False, "被邀请人账号存活时间不足"
        
        # 检查被邀请人是否有活跃行为（可扩展）
        # TODO: 添加更多活跃度检测
        
        return True, None
    
    @staticmethod
    def generate_device_fingerprint(
        user_agent: str,
        screen_resolution: str = "",
        timezone: str = "",
        language: str = "",
        platform: str = ""
    ) -> str:
        """生成设备指纹"""
        fingerprint_data = f"{user_agent}|{screen_resolution}|{timezone}|{language}|{platform}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:32]
    
    async def get_fraud_statistics(self) -> dict:
        """获取欺诈统计数据"""
        # 今日无效邀请数
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        invalid_today = await self.db.execute(
            select(func.count(Invitation.id)).where(
                and_(
                    Invitation.is_valid == False,
                    Invitation.created_at >= today_start
                )
            )
        )
        
        # 本周无效邀请数
        week_start = today_start - timedelta(days=today_start.weekday())
        invalid_week = await self.db.execute(
            select(func.count(Invitation.id)).where(
                and_(
                    Invitation.is_valid == False,
                    Invitation.created_at >= week_start
                )
            )
        )
        
        # 按原因分组
        invalid_reasons = await self.db.execute(
            select(
                Invitation.invalid_reason,
                func.count(Invitation.id)
            ).where(
                Invitation.is_valid == False
            ).group_by(Invitation.invalid_reason)
        )
        
        reasons_dict = {}
        for reason, count in invalid_reasons.all():
            reasons_dict[reason or "未知"] = count
        
        return {
            "invalid_today": invalid_today.scalar() or 0,
            "invalid_week": invalid_week.scalar() or 0,
            "invalid_by_reason": reasons_dict
        }


async def validate_and_create_invitation(
    db: AsyncSession,
    inviter_id: int,
    invitee_id: int,
    invite_code: str,
    device_fingerprint: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Invitation:
    """
    验证并创建邀请记录
    """
    anti_fraud = AntiFraudService(db)
    
    is_valid, invalid_reason = await anti_fraud.check_invite_validity(
        inviter_id=inviter_id,
        invitee_id=invitee_id,
        device_fingerprint=device_fingerprint,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    invitation = Invitation(
        inviter_id=inviter_id,
        invitee_id=invitee_id,
        invite_code=invite_code,
        device_fingerprint=device_fingerprint,
        ip_address=ip_address,
        user_agent=user_agent,
        is_valid=is_valid,
        invalid_reason=invalid_reason,
        validated_at=datetime.utcnow() if is_valid else None
    )
    
    db.add(invitation)
    
    return invitation

防作弊服务
用于检测和防止推广系统中的作弊行为
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.promotion import Invitation, UserProfile
from app.models.user import User
import hashlib
import re


class AntiFraudService:
    """防作弊服务"""
    
    # 配置
    MAX_INVITES_PER_IP_PER_DAY = 5  # 每个IP每天最多邀请数
    MAX_INVITES_PER_DEVICE_PER_DAY = 3  # 每个设备每天最多邀请数
    MIN_ACCOUNT_AGE_FOR_REWARD = 3600  # 账号最短存活时间（秒）才能算有效邀请
    SUSPICIOUS_PATTERNS = [
        r'^test\d+$',  # test123 等测试账号
        r'^user\d+$',  # user123 等批量账号
        r'^temp\d+$',  # temp123 等临时账号
    ]
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def check_invite_validity(
        self,
        inviter_id: int,
        invitee_id: int,
        device_fingerprint: Optional[str],
        ip_address: Optional[str],
        user_agent: Optional[str]
    ) -> Tuple[bool, Optional[str]]:
        """
        检查邀请是否有效
        返回: (is_valid, invalid_reason)
        """
        
        # 1. 检查是否自己邀请自己
        if inviter_id == invitee_id:
            return False, "自邀无效"
        
        # 2. 检查是否重复邀请
        existing = await self.db.execute(
            select(Invitation).where(
                and_(
                    Invitation.inviter_id == inviter_id,
                    Invitation.invitee_id == invitee_id
                )
            )
        )
        if existing.scalar_one_or_none():
            return False, "重复邀请"
        
        # 3. 检查IP限制
        if ip_address:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ip_count = await self.db.execute(
                select(func.count(Invitation.id)).where(
                    and_(
                        Invitation.ip_address == ip_address,
                        Invitation.created_at >= today_start
                    )
                )
            )
            if (ip_count.scalar() or 0) >= self.MAX_INVITES_PER_IP_PER_DAY:
                return False, f"IP {ip_address} 今日邀请过多"
        
        # 4. 检查设备指纹限制
        if device_fingerprint:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            device_count = await self.db.execute(
                select(func.count(Invitation.id)).where(
                    and_(
                        Invitation.device_fingerprint == device_fingerprint,
                        Invitation.created_at >= today_start
                    )
                )
            )
            if (device_count.scalar() or 0) >= self.MAX_INVITES_PER_DEVICE_PER_DAY:
                return False, "设备今日邀请过多"
        
        # 5. 检查是否循环邀请
        invitee_profile = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == invitee_id)
        )
        invitee_profile = invitee_profile.scalar_one_or_none()
        if invitee_profile and invitee_profile.inviter_id == inviter_id:
            # 被邀请人已经是邀请人的下级，无需重复
            pass
        
        # 检查是否形成循环
        if await self._check_circular_invite(inviter_id, invitee_id):
            return False, "循环邀请无效"
        
        return True, None
    
    async def _check_circular_invite(self, inviter_id: int, invitee_id: int) -> bool:
        """检查是否形成循环邀请链"""
        # 获取邀请人的上级链
        current_id = inviter_id
        visited = set()
        
        for _ in range(10):  # 最多检查10层
            if current_id in visited:
                return True
            visited.add(current_id)
            
            profile = await self.db.execute(
                select(UserProfile).where(UserProfile.user_id == current_id)
            )
            profile = profile.scalar_one_or_none()
            
            if not profile or not profile.inviter_id:
                break
            
            if profile.inviter_id == invitee_id:
                return True
            
            current_id = profile.inviter_id
        
        return False
    
    async def check_username_suspicious(self, username: str) -> bool:
        """检查用户名是否可疑"""
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.match(pattern, username, re.IGNORECASE):
                return True
        return False
    
    async def check_account_age(self, user_id: int) -> bool:
        """检查账号是否存活足够长时间"""
        user = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user.scalar_one_or_none()
        
        if not user:
            return False
        
        account_age = (datetime.utcnow() - user.created_at).total_seconds()
        return account_age >= self.MIN_ACCOUNT_AGE_FOR_REWARD
    
    async def validate_invite_for_reward(
        self,
        invitation_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        验证邀请是否可以发放奖励
        返回: (can_reward, reason)
        """
        invitation = await self.db.execute(
            select(Invitation).where(Invitation.id == invitation_id)
        )
        invitation = invitation.scalar_one_or_none()
        
        if not invitation:
            return False, "邀请记录不存在"
        
        if not invitation.is_valid:
            return False, invitation.invalid_reason or "邀请无效"
        
        if invitation.register_rewarded:
            return False, "已发放过注册奖励"
        
        # 检查被邀请人账号年龄
        if not await self.check_account_age(invitation.invitee_id):
            return False, "被邀请人账号存活时间不足"
        
        # 检查被邀请人是否有活跃行为（可扩展）
        # TODO: 添加更多活跃度检测
        
        return True, None
    
    @staticmethod
    def generate_device_fingerprint(
        user_agent: str,
        screen_resolution: str = "",
        timezone: str = "",
        language: str = "",
        platform: str = ""
    ) -> str:
        """生成设备指纹"""
        fingerprint_data = f"{user_agent}|{screen_resolution}|{timezone}|{language}|{platform}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:32]
    
    async def get_fraud_statistics(self) -> dict:
        """获取欺诈统计数据"""
        # 今日无效邀请数
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        invalid_today = await self.db.execute(
            select(func.count(Invitation.id)).where(
                and_(
                    Invitation.is_valid == False,
                    Invitation.created_at >= today_start
                )
            )
        )
        
        # 本周无效邀请数
        week_start = today_start - timedelta(days=today_start.weekday())
        invalid_week = await self.db.execute(
            select(func.count(Invitation.id)).where(
                and_(
                    Invitation.is_valid == False,
                    Invitation.created_at >= week_start
                )
            )
        )
        
        # 按原因分组
        invalid_reasons = await self.db.execute(
            select(
                Invitation.invalid_reason,
                func.count(Invitation.id)
            ).where(
                Invitation.is_valid == False
            ).group_by(Invitation.invalid_reason)
        )
        
        reasons_dict = {}
        for reason, count in invalid_reasons.all():
            reasons_dict[reason or "未知"] = count
        
        return {
            "invalid_today": invalid_today.scalar() or 0,
            "invalid_week": invalid_week.scalar() or 0,
            "invalid_by_reason": reasons_dict
        }


async def validate_and_create_invitation(
    db: AsyncSession,
    inviter_id: int,
    invitee_id: int,
    invite_code: str,
    device_fingerprint: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Invitation:
    """
    验证并创建邀请记录
    """
    anti_fraud = AntiFraudService(db)
    
    is_valid, invalid_reason = await anti_fraud.check_invite_validity(
        inviter_id=inviter_id,
        invitee_id=invitee_id,
        device_fingerprint=device_fingerprint,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    invitation = Invitation(
        inviter_id=inviter_id,
        invitee_id=invitee_id,
        invite_code=invite_code,
        device_fingerprint=device_fingerprint,
        ip_address=ip_address,
        user_agent=user_agent,
        is_valid=is_valid,
        invalid_reason=invalid_reason,
        validated_at=datetime.utcnow() if is_valid else None
    )
    
    db.add(invitation)
    
    return invitation

