"""
认证相关API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from datetime import datetime, timedelta
import uuid
import hashlib
import random

from app.core.database import get_db
from app.core.security import (
    verify_password, get_password_hash, 
    create_access_token, create_refresh_token, 
    decode_token, generate_invite_code
)
from app.api.deps import get_current_user, get_current_user_optional
from app.models.user import User, UserVIP
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, Token, TokenRefresh,
    GuestRegister, GuestLogin, BindPhone, BindEmail, UpgradeAccount
)
from app.core.config import settings

router = APIRouter()

# ========== 昵称词库 ==========

# 形容词库（30个）
NICKNAME_ADJECTIVES = [
    "快乐", "开心", "可爱", "温柔", "活泼", "呆萌", "软糯", "甜蜜", "元气", "阳光",
    "慵懒", "安静", "傲娇", "高冷", "佛系", "躺平", "摸鱼", "追梦", "暴富", "幸运",
    "神秘", "闪亮", "迷糊", "贪吃", "爱笑", "害羞", "勇敢", "机智", "淡定", "随缘",
]

# 名词库（40个）
NICKNAME_NOUNS = [
    # 动物
    "小猫", "小狗", "兔子", "熊猫", "考拉", "企鹅", "小鹿", "狐狸", "仓鼠", "柴犬",
    # 食物饮品
    "奶茶", "可乐", "柠檬", "草莓", "芒果", "蜜桃", "樱桃", "葡萄", "西瓜", "布丁",
    # 甜品零食
    "糖果", "饼干", "蛋糕", "冰淇淋", "棉花糖", "巧克力", "甜甜圈", "马卡龙",
    # 自然元素
    "星星", "月亮", "云朵", "晚风", "清茶", "甜橙", "阳光", "彩虹",
    # 角色
    "宝贝", "天使", "精灵", "公主",
]

# 固定短昵称库（作为补充）
SHORT_NICKNAMES = [
    "小白", "大神", "萌新", "大佬", "小透明", "路人甲", "咸鱼", "锦鲤", "欧皇", "非酋",
    "肝帝", "佛系", "社恐", "i人", "e人", "干饭人", "夜猫子", "早起鸟", "吃货", "宅宅",
]


def generate_guest_username():
    """生成8位数字用户名"""
    return str(random.randint(10000000, 99999999))


def generate_random_nickname():
    """生成随机昵称（形容词+名词+3位数字）
    
    格式示例：快乐小猫001、温柔兔子123、元气奶茶456
    总组合数：30×40×1000 + 20×1000 = 1,220,000（约122万）
    """
    # 80%概率使用组合昵称，20%概率使用固定短昵称
    if random.random() < 0.8:
        adj = random.choice(NICKNAME_ADJECTIVES)
        noun = random.choice(NICKNAME_NOUNS)
        nickname = f"{adj}{noun}"
    else:
        nickname = random.choice(SHORT_NICKNAMES)
    
    # 添加3位随机数后缀确保唯一性
    suffix = random.randint(0, 999)
    
    return f"{nickname}{suffix:03d}"


def generate_guest_password():
    """生成游客默认密码"""
    return uuid.uuid4().hex


def generate_default_avatar(user_id: int) -> str:
    """根据用户ID生成默认头像路径
    
    共52个预设头像，根据用户ID取模分配
    """
    total_avatars = 52
    index = user_id % total_avatars
    
    if index < 17:
        # icon_avatar_1.webp 到 icon_avatar_17.webp
        return f"/images/avatars/icon_avatar_{index + 1}.webp"
    elif index < 32:
        # DM_20251217202131_001.JPEG 到 DM_20251217202131_015.JPEG
        num = str(index - 17 + 1).zfill(3)
        return f"/images/avatars/DM_20251217202131_{num}.JPEG"
    else:
        # DM_20251217202341_001 到 DM_20251217202341_020
        num = str(index - 32 + 1).zfill(3)
        webp_files = ['002', '006', '015', '018']
        ext = 'webp' if num in webp_files else 'JPEG'
        return f"/images/avatars/DM_20251217202341_{num}.{ext}"


def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    # 尝试从X-Forwarded-For头获取（用于代理/负载均衡）
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    # 尝试从X-Real-IP头获取
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    # 直接获取客户端IP
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=UserResponse)
async def register(
    user_in: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """用户注册"""
    # 检查用户名是否存在
    result = await db.execute(
        select(User).where(
            or_(
                User.username == user_in.username,
                User.email == user_in.email
            )
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或邮箱已存在"
        )
    
    # 处理邀请码 - 支持新推广系统
    invited_by = None
    inviter_profile = None
    if user_in.invite_code:
        # 先在新的 UserProfile 表中查找
        from app.models.promotion import UserProfile, Invitation, Reward
        result = await db.execute(
            select(UserProfile).where(UserProfile.invite_code == user_in.invite_code)
        )
        inviter_profile = result.scalar_one_or_none()
        if inviter_profile:
            invited_by = inviter_profile.user_id
        else:
            # 兼容旧系统：在 User 表中查找
            result = await db.execute(
                select(User).where(User.invite_code == user_in.invite_code)
            )
            inviter = result.scalar_one_or_none()
            if inviter:
                invited_by = inviter.id
    
    # 创建用户
    user = User(
        username=user_in.username,
        email=user_in.email,
        phone=user_in.phone,
        hashed_password=get_password_hash(user_in.password),
        invite_code=generate_invite_code(),
        invited_by=invited_by
    )
    db.add(user)
    await db.flush()
    
    # 分配默认头像（基于用户ID）
    user.avatar = generate_default_avatar(user.id)
    
    # 创建VIP记录
    vip = UserVIP(user_id=user.id)
    db.add(vip)
    
    # 创建用户推广资料
    from app.models.promotion import UserProfile, Invitation, Reward
    from app.core.invite_code import encode_user_id
    
    # 基于用户ID生成唯一邀请码（无需检查重复）
    new_invite_code = encode_user_id(user.id)
    user_profile = UserProfile(
        user_id=user.id,
        invite_code=new_invite_code,
        inviter_id=invited_by
    )
    db.add(user_profile)
    
    # 处理邀请奖励
    if invited_by:
        # 获取客户端信息用于防作弊
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        device_fingerprint = request.headers.get("x-device-fingerprint", "")
        
        # 使用防作弊服务创建邀请记录
        from app.services.anti_fraud import AntiFraudService
        anti_fraud = AntiFraudService(db)
        is_valid, invalid_reason = await anti_fraud.check_invite_validity(
            inviter_id=invited_by,
            invitee_id=user.id,
            device_fingerprint=device_fingerprint,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        invitation = Invitation(
            inviter_id=invited_by,
            invitee_id=user.id,
            invite_code=user_in.invite_code,
            device_fingerprint=device_fingerprint,
            ip_address=client_ip,
            user_agent=user_agent,
            is_valid=is_valid,
            invalid_reason=invalid_reason
        )
        db.add(invitation)
        
        # 更新邀请人统计
        result = await db.execute(select(User).where(User.id == invited_by))
        inviter = result.scalar_one()
        inviter.invite_count += 1
        
        # 如果邀请人没有推广资料（旧系统用户），为其创建
        if not inviter_profile:
            inviter_profile = UserProfile(
                user_id=invited_by,
                invite_code=inviter.invite_code or gen_code(),
                total_invites=0,
                valid_invites=0
            )
            db.add(inviter_profile)
            await db.flush()
        
        # 更新邀请人推广资料统计
        inviter_profile.total_invites += 1
        # 注意：valid_invites 在被邀请人充值后才增加，由 payments.py 处理
        # 里程碑奖励也在充值后自动发放，基于 valid_invites 计算
    
    await db.commit()
    await db.refresh(user)
    
    return user


@router.post("/guest/register", response_model=Token)
async def guest_register(
    guest_in: GuestRegister,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """自动注册（优化版）
    
    根据设备指纹自动注册账号，如果设备已注册则直接登录
    优化：并行化Redis检查，优化用户名生成
    """
    from app.core.redis import RedisCache
    import asyncio
    
    client_ip = get_client_ip(request)
    device_id = guest_in.device_id
    
    # ========== 1. 并行检查：IP速率限制 + 设备锁 + 设备是否已注册 ==========
    rate_key = f"guest_register_rate:{client_ip}"
    lock_key = f"guest_register_lock:{device_id}"
    
    async def check_rate_limit():
        """检查IP速率限制"""
        try:
            rate_count = await RedisCache.get(rate_key)
            return int(rate_count) if rate_count else 0
        except:
            return 0
    
    async def check_device_lock():
        """检查设备锁"""
        try:
            return await RedisCache.get(lock_key)
        except:
            return None
    
    async def check_existing_user():
        """检查设备是否已注册"""
        result = await db.execute(
            select(User).where(User.device_id == device_id)
        )
        return result.scalar_one_or_none()
    
    # 并行执行三个检查
    rate_count, existing_lock, user = await asyncio.gather(
        check_rate_limit(),
        check_device_lock(),
        check_existing_user()
    )
    
    # 检查速率限制
    if rate_count >= 10:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁，请稍后再试"
        )
    
    # 检查设备锁
    if existing_lock:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="注册处理中，请稍后"
        )
    
    # ========== 2. 设备已注册，直接登录 ==========
    if user:
        user.last_login = datetime.utcnow()
        user.last_login_ip = client_ip
        await db.commit()
        
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token
        )
    
    # ========== 3. 新设备，设置锁并创建账号 ==========
    lock_acquired = False
    try:
        await RedisCache.set(lock_key, "1", expire=5)
        lock_acquired = True
        
        # 增加速率计数
        await RedisCache.incr(rate_key)
        if rate_count == 0:
            await RedisCache.expire(rate_key, 60)
    except:
        pass
    
    try:
        # 使用时间戳+随机数生成用户名，几乎不可能重复
        import time
        timestamp = int(time.time() * 1000) % 100000000  # 8位时间戳
        guest_username = str(timestamp)
        guest_nickname = generate_random_nickname()
        guest_password = generate_guest_password()
        
        user = User(
            username=guest_username,
            email=None,
            hashed_password=get_password_hash(guest_password),
            nickname=guest_nickname,
            register_ip=client_ip,
            last_login_ip=client_ip,
            device_id=device_id,
            is_guest=False,
            invite_code=generate_invite_code(),
            last_login=datetime.utcnow()
        )
        db.add(user)
        await db.flush()
        
        # 分配默认头像
        user.avatar = generate_default_avatar(user.id)
        
        # 创建VIP记录
        vip = UserVIP(user_id=user.id)
        db.add(vip)
        
        await db.commit()
        await db.refresh(user)
        
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token
        )
    finally:
        if lock_acquired:
            try:
                await RedisCache.delete(lock_key)
            except:
                pass


@router.post("/guest/login", response_model=Token)
async def guest_login(
    guest_in: GuestLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """游客登录
    
    根据设备指纹登录游客账号
    """
    client_ip = get_client_ip(request)
    
    result = await db.execute(
        select(User).where(User.device_id == guest_in.device_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备未注册，请先注册"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用"
        )
    
    # 更新最后登录时间和IP
    user.last_login = datetime.utcnow()
    user.last_login_ip = client_ip
    await db.commit()
    
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/bind/phone/send-code")
async def send_phone_bind_code(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """发送绑定手机的验证码到用户邮箱
    
    使用邮箱验证代替短信验证（免费方案）
    """
    from app.services.email_service import EmailService
    
    # 检查用户是否有邮箱
    if not current_user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先绑定邮箱才能使用邮箱验证"
        )
    
    # 发送验证码到邮箱
    result = await EmailService.send_verification_code(
        current_user.email, 
        "绑定手机", 
        "bind_phone"
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS if "频繁" in result["message"] else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )
    
    # 隐藏部分邮箱
    email = current_user.email
    at_index = email.index('@')
    masked_email = email[:2] + '***' + email[at_index-1:]
    
    return {
        "message": f"验证码已发送到 {masked_email}",
        "email": masked_email,
        "debug_code": result.get("code")  # 仅调试模式返回
    }


@router.post("/bind/phone")
async def bind_phone(
    bind_in: BindPhone,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """绑定手机号（使用邮箱验证码验证）
    
    游客账号绑定手机号后可通过手机号登录
    """
    from app.services.email_service import EmailService
    
    # 验证邮箱验证码
    if current_user.email:
        verify_result = await EmailService.verify_code(
            current_user.email,
            bind_in.code,
            "bind_phone"
        )
        
        if not verify_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=verify_result["message"]
            )
    
    # 检查手机号是否已被使用
    result = await db.execute(
        select(User).where(User.phone == bind_in.phone)
    )
    existing = result.scalar_one_or_none()
    if existing and existing.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号已被其他账号绑定"
        )
    
    current_user.phone = bind_in.phone
    await db.commit()
    
    return {"message": "手机号绑定成功"}


@router.post("/email/send-code")
async def send_email_code(
    email: str,
    code_type: str = "bind",  # bind, verify, reset
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    发送邮箱验证码
    
    code_type:
    - bind: 绑定邮箱
    - verify: 验证邮箱
    - reset: 重置密码
    """
    from app.services.email_service import EmailService
    
    # 验证邮箱格式
    import re
    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱格式不正确"
        )
    
    # 绑定操作需要登录
    if code_type == "bind" and not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录"
        )
    
    # 检查邮箱是否已被其他账号使用
    if code_type == "bind":
        result = await db.execute(
            select(User).where(User.email == email)
        )
        existing = result.scalar_one_or_none()
        if existing and existing.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被其他账号绑定"
            )
    
    # 密码重置/登录需要邮箱已注册
    if code_type in ["reset", "login"]:
        result = await db.execute(
            select(User).where(User.email == email)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="该邮箱未绑定任何账号"
            )
    
    # 发送验证码
    purpose_map = {
        "bind": "绑定",
        "verify": "验证",
        "reset": "重置密码",
        "login": "登录"
    }
    purpose = purpose_map.get(code_type, "验证")
    
    result = await EmailService.send_verification_code(email, purpose, code_type)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS if "频繁" in result["message"] else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )
    
    return result


@router.post("/email/verify-code")
async def verify_email_code(
    email: str,
    code: str,
    code_type: str = "verify"
):
    """验证邮箱验证码"""
    from app.services.email_service import EmailService
    
    result = await EmailService.verify_code(email, code, code_type)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return result


@router.post("/recovery/login")
async def login_with_email_code(
    email: str,
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """通过邮箱验证码直接登录"""
    from app.services.email_service import EmailService
    from app.core.security import create_access_token
    
    # 查找用户
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该邮箱未绑定任何账号"
        )
    
    # 验证验证码
    verify_result = await EmailService.verify_code(email, code, "login")
    
    if not verify_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=verify_result["message"]
        )
    
    # 生成token
    access_token = create_access_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "message": "登录成功"
    }


@router.post("/bind/email")
async def bind_email(
    bind_in: BindEmail,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """绑定邮箱（需要先获取验证码）
    
    游客账号绑定邮箱后可通过邮箱登录
    """
    from app.services.email_service import EmailService
    
    # 验证邮箱验证码
    code = getattr(bind_in, 'code', None)
    if code:
        verify_result = await EmailService.verify_code(bind_in.email, code, "bind")
        if not verify_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=verify_result["message"]
            )
    
    # 检查邮箱是否已被使用
    result = await db.execute(
        select(User).where(User.email == bind_in.email)
    )
    existing = result.scalar_one_or_none()
    if existing and existing.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被其他账号绑定"
        )
    
    current_user.email = bind_in.email
    current_user.is_verified = True  # 标记邮箱已验证
    await db.commit()
    
    return {"message": "邮箱绑定成功"}


@router.post("/upgrade", response_model=UserResponse)
async def upgrade_account(
    upgrade_in: UpgradeAccount,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """升级游客账号
    
    游客账号设置用户名和密码后升级为正式账号
    """
    if not current_user.is_guest:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前账号已是正式账号"
        )
    
    # 检查用户名是否已存在
    result = await db.execute(
        select(User).where(
            User.username == upgrade_in.username,
            User.id != current_user.id
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    if upgrade_in.email:
        result = await db.execute(
            select(User).where(
                User.email == upgrade_in.email,
                User.id != current_user.id
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )
    
    # 升级账号
    current_user.username = upgrade_in.username
    current_user.hashed_password = get_password_hash(upgrade_in.password)
    current_user.is_guest = False
    
    if upgrade_in.email:
        current_user.email = upgrade_in.email
    if upgrade_in.phone:
        current_user.phone = upgrade_in.phone
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.post("/login", response_model=Token)
async def login(
    user_in: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    client_ip = get_client_ip(request)
    
    # 支持用户名、邮箱、手机号登录
    result = await db.execute(
        select(User).where(
            or_(
                User.username == user_in.username,
                User.email == user_in.username,
                User.phone == user_in.username
            )
        )
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    # 更新最后登录时间和IP
    user.last_login = datetime.utcnow()
    user.last_login_ip = client_ip
    await db.commit()
    
    # 生成令牌
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_in: TokenRefresh,
    db: AsyncSession = Depends(get_db)
):
    """刷新令牌"""
    payload = decode_token(token_in.refresh_token)
    
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )
    
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用"
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


# ========== 二维码登录相关 ==========

@router.post("/generate-qr-token")
async def generate_qr_token(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """生成二维码登录令牌（永久有效，一次性使用）"""
    from app.models.user import LoginQRToken
    import secrets
    
    # 生成唯一令牌
    token = secrets.token_hex(32)  # 64字符
    
    # 创建令牌记录
    qr_token = LoginQRToken(
        user_id=current_user.id,
        token=token,
        is_used=False
    )
    db.add(qr_token)
    await db.commit()
    
    return {
        "token": token,
        "user_id": current_user.id,
        "message": "二维码令牌已生成，永久有效，只能使用一次"
    }


@router.get("/qr-token-status")
async def get_qr_token_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户的二维码令牌状态"""
    from app.models.user import LoginQRToken
    
    # 获取最新的未使用令牌
    result = await db.execute(
        select(LoginQRToken)
        .where(LoginQRToken.user_id == current_user.id)
        .where(LoginQRToken.is_used == False)
        .order_by(LoginQRToken.created_at.desc())
        .limit(1)
    )
    token_record = result.scalar_one_or_none()
    
    if token_record:
        return {
            "has_token": True,
            "token": token_record.token,
            "created_at": token_record.created_at.isoformat() if token_record.created_at else None
        }
    
    return {
        "has_token": False,
        "token": None
    }


@router.post("/qr-login")
async def qr_login(
    token: str,
    device_id: str = None,
    device_info: str = None,
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """扫码登录 - 使用二维码令牌登录"""
    from app.models.user import LoginQRToken, TrustedDevice, DeviceSwitchLog
    from datetime import timedelta
    import secrets
    
    # 配置
    MAX_TRUSTED_DEVICES = 2  # 最多可信设备数
    SWITCH_COOLDOWN_HOURS = 24  # 设备切换冷却期（小时）
    
    # 获取客户端IP
    client_ip = "unknown"
    if request:
        client_ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
    
    # 生成设备ID（如果未提供）
    if not device_id:
        device_id = hashlib.md5(f"{client_ip}-{device_info or 'unknown'}".encode()).hexdigest()
    
    # 查找令牌
    result = await db.execute(
        select(LoginQRToken).where(LoginQRToken.token == token)
    )
    token_record = result.scalar_one_or_none()
    
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="无效的登录令牌"
        )
    
    if token_record.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该令牌已被使用，请重新生成"
        )
    
    # 获取用户
    result = await db.execute(
        select(User).where(User.id == token_record.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户不存在或已被禁用"
        )
    
    # === 检查可信设备 ===
    result = await db.execute(
        select(TrustedDevice)
        .where(TrustedDevice.user_id == user.id)
        .where(TrustedDevice.device_id == device_id)
        .where(TrustedDevice.is_active == True)
    )
    current_device = result.scalar_one_or_none()
    
    if not current_device:
        # 新设备，检查是否超过最大设备数
        result = await db.execute(
            select(TrustedDevice)
            .where(TrustedDevice.user_id == user.id)
            .where(TrustedDevice.is_active == True)
        )
        active_devices = result.scalars().all()
        
        if len(active_devices) >= MAX_TRUSTED_DEVICES:
            # 检查设备切换冷却期
            cooldown_time = datetime.utcnow() - timedelta(hours=SWITCH_COOLDOWN_HOURS)
            result = await db.execute(
                select(DeviceSwitchLog)
                .where(DeviceSwitchLog.user_id == user.id)
                .where(DeviceSwitchLog.switched_at > cooldown_time)
                .order_by(DeviceSwitchLog.switched_at.desc())
            )
            recent_switches = result.scalars().all()
            
            if recent_switches:
                # 计算剩余冷却时间
                last_switch = recent_switches[0]
                next_available = last_switch.switched_at + timedelta(hours=SWITCH_COOLDOWN_HOURS)
                remaining = next_available - datetime.utcnow()
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"您的账号24小时内已切换设备，下次切换需等待 {hours}小时{minutes}分钟"
                )
            
            # 移除最旧的设备
            oldest_device = sorted(active_devices, key=lambda d: d.last_login_at or d.created_at)[0]
            oldest_device.is_active = False
            
            # 记录设备切换
            switch_log = DeviceSwitchLog(
                user_id=user.id,
                from_device_id=oldest_device.device_id,
                to_device_id=device_id,
                to_device_name=device_info,
                to_device_ip=client_ip
            )
            db.add(switch_log)
        
        # 添加新的可信设备
        new_device = TrustedDevice(
            user_id=user.id,
            device_id=device_id,
            device_name=device_info or "Unknown Device",
            device_info=device_info,
            is_active=True,
            last_login_at=datetime.utcnow(),
            last_login_ip=client_ip
        )
        db.add(new_device)
    else:
        # 已有可信设备，更新登录时间
        current_device.last_login_at = datetime.utcnow()
        current_device.last_login_ip = client_ip
    
    # 生成新的会话ID
    new_session_id = secrets.token_hex(32)
    
    # 更新用户的当前会话（使旧设备失效）
    user.current_session_id = new_session_id
    user.current_device_info = device_info or "Unknown Device"
    user.last_login = datetime.utcnow()
    user.last_login_ip = client_ip
    
    # 标记令牌为已使用
    token_record.is_used = True
    token_record.used_at = datetime.utcnow()
    token_record.used_device_info = device_info
    token_record.used_ip = client_ip
    
    await db.commit()
    
    # 生成访问令牌（包含session_id和device_id）
    access_token = create_access_token(
        data={"sub": str(user.id), "session_id": new_session_id, "device_id": device_id}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "session_id": new_session_id, "device_id": device_id}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "message": "登录成功，其他设备已自动登出"
    }


@router.get("/check-session")
async def check_session(
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """检查当前会话是否有效"""
    # 从请求头获取当前token
    auth_header = request.headers.get("Authorization", "") if request else ""
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        payload = decode_token(token)
        
        if payload:
            token_session_id = payload.get("session_id")
            
            # 如果token中有session_id，检查是否与用户当前session匹配
            if token_session_id and current_user.current_session_id:
                if token_session_id != current_user.current_session_id:
                    return {
                        "valid": False,
                        "reason": "session_expired",
                        "message": "您的账号已在其他设备登录"
                    }
    
    return {
        "valid": True,
        "user_id": current_user.id,
        "current_device": current_user.current_device_info
    }


@router.post("/regenerate-qr-token")
async def regenerate_qr_token(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """重新生成二维码令牌（使旧令牌失效）"""
    from app.models.user import LoginQRToken
    from sqlalchemy import update
    import secrets
    
    # 将该用户所有未使用的旧令牌标记为已使用
    await db.execute(
        update(LoginQRToken)
        .where(LoginQRToken.user_id == current_user.id)
        .where(LoginQRToken.is_used == False)
        .values(is_used=True, used_at=datetime.utcnow())
    )
    
    # 生成新令牌
    token = secrets.token_hex(32)
    qr_token = LoginQRToken(
        user_id=current_user.id,
        token=token,
        is_used=False
    )
    db.add(qr_token)
    await db.commit()
    
    return {
        "token": token,
        "user_id": current_user.id,
        "message": "新的二维码令牌已生成，旧令牌已失效"
    }


# ========== 设备管理相关 ==========

@router.get("/devices")
async def get_trusted_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的可信设备列表"""
    from app.models.user import TrustedDevice
    
    result = await db.execute(
        select(TrustedDevice)
        .where(TrustedDevice.user_id == current_user.id)
        .where(TrustedDevice.is_active == True)
        .order_by(TrustedDevice.last_login_at.desc())
    )
    devices = result.scalars().all()
    
    return {
        "devices": [
            {
                "id": d.id,
                "device_id": d.device_id[:8] + "****",  # 部分隐藏
                "device_name": d.device_name,
                "last_login_at": d.last_login_at.isoformat() if d.last_login_at else None,
                "last_login_ip": d.last_login_ip,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "is_current": d.device_id == current_user.current_session_id[:32] if current_user.current_session_id else False
            }
            for d in devices
        ],
        "max_devices": 2
    }


@router.delete("/devices/{device_id}")
async def remove_trusted_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """移除可信设备"""
    from app.models.user import TrustedDevice
    
    result = await db.execute(
        select(TrustedDevice)
        .where(TrustedDevice.id == device_id)
        .where(TrustedDevice.user_id == current_user.id)
    )
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在"
        )
    
    device.is_active = False
    await db.commit()
    
    return {"message": "设备已移除"}


@router.get("/device-switch-status")
async def get_device_switch_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取设备切换状态（冷却时间）"""
    from app.models.user import DeviceSwitchLog, TrustedDevice
    from datetime import timedelta
    
    SWITCH_COOLDOWN_HOURS = 24
    
    # 获取当前设备数
    result = await db.execute(
        select(TrustedDevice)
        .where(TrustedDevice.user_id == current_user.id)
        .where(TrustedDevice.is_active == True)
    )
    active_devices = result.scalars().all()
    
    # 检查最近的切换记录
    cooldown_time = datetime.utcnow() - timedelta(hours=SWITCH_COOLDOWN_HOURS)
    result = await db.execute(
        select(DeviceSwitchLog)
        .where(DeviceSwitchLog.user_id == current_user.id)
        .where(DeviceSwitchLog.switched_at > cooldown_time)
        .order_by(DeviceSwitchLog.switched_at.desc())
        .limit(1)
    )
    last_switch = result.scalar_one_or_none()
    
    can_switch = True
    remaining_seconds = 0
    
    if last_switch and len(active_devices) >= 2:
        next_available = last_switch.switched_at + timedelta(hours=SWITCH_COOLDOWN_HOURS)
        if datetime.utcnow() < next_available:
            can_switch = False
            remaining_seconds = int((next_available - datetime.utcnow()).total_seconds())
    
    return {
        "active_devices": len(active_devices),
        "max_devices": 2,
        "can_switch": can_switch,
        "remaining_seconds": remaining_seconds,
        "remaining_text": f"{remaining_seconds // 3600}小时{(remaining_seconds % 3600) // 60}分钟" if remaining_seconds > 0 else None,
        "last_switch_at": last_switch.switched_at.isoformat() if last_switch else None
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_in: TokenRefresh,
    db: AsyncSession = Depends(get_db)
):
    """刷新令牌"""
    payload = decode_token(token_in.refresh_token)
    
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )
    
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用"
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


# ========== 二维码登录相关 ==========

@router.post("/generate-qr-token")
async def generate_qr_token(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """生成二维码登录令牌（永久有效，一次性使用）"""
    from app.models.user import LoginQRToken
    import secrets
    
    # 生成唯一令牌
    token = secrets.token_hex(32)  # 64字符
    
    # 创建令牌记录
    qr_token = LoginQRToken(
        user_id=current_user.id,
        token=token,
        is_used=False
    )
    db.add(qr_token)
    await db.commit()
    
    return {
        "token": token,
        "user_id": current_user.id,
        "message": "二维码令牌已生成，永久有效，只能使用一次"
    }


@router.get("/qr-token-status")
async def get_qr_token_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户的二维码令牌状态"""
    from app.models.user import LoginQRToken
    
    # 获取最新的未使用令牌
    result = await db.execute(
        select(LoginQRToken)
        .where(LoginQRToken.user_id == current_user.id)
        .where(LoginQRToken.is_used == False)
        .order_by(LoginQRToken.created_at.desc())
        .limit(1)
    )
    token_record = result.scalar_one_or_none()
    
    if token_record:
        return {
            "has_token": True,
            "token": token_record.token,
            "created_at": token_record.created_at.isoformat() if token_record.created_at else None
        }
    
    return {
        "has_token": False,
        "token": None
    }


