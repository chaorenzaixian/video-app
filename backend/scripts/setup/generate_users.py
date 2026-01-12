"""生成测试用户账号"""
import asyncio
import random
import sys
sys.path.insert(0, '.')

from app.core.database import get_db, engine
from app.models.user import User, UserVIP
from app.core.security import get_password_hash, generate_invite_code
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# 互联网梗昵称库
INTERNET_NICKNAMES = [
    "404号宇航员", "404小可爱", "404追梦人", "404摸鱼侠", "404躺平族",
    "人间加载中", "幸福加载中", "暴富加载中", "脱单加载中", "好运加载中",
    "佛系青年在线", "社恐患者在线", "熬夜冠军在线", "干饭达人在线", "摸鱼高手在线",
    "已读不回专家", "已读乱回大师", "消息必秒回", "在线隐身中",
    "官方认证小可爱", "野生程序猿", "退役熬夜选手", "资深摸鱼专家", "持证躺平师",
    "职业躺平家", "全职摸鱼人", "兼职做梦师", "业余暴富中", "实习锦鲤",
    "一只小可爱", "迷路的小猫", "冒泡的小鱼", "打盹的考拉", "装睡的猪猪",
    "暴富倒计时", "脱单进行中", "好运临门中", "锦鲤本鲤", "欧皇附体",
    "今天不想上班", "周一综合症", "起床困难户", "睡眠爱好者", "奶茶续命中",
    "快乐小天才", "开心果本果", "人间小太阳", "行走的表情包", "芜湖起飞",
]

def generate_username():
    """生成8位数字用户名"""
    return str(random.randint(10000000, 99999999))

def generate_nickname():
    """生成随机昵称"""
    nickname = random.choice(INTERNET_NICKNAMES)
    suffix = random.randint(1000, 9999)
    return f"{nickname}{suffix}"

async def generate_users(count: int = 10):
    """生成测试用户"""
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.core.database import async_session
    
    async with async_session() as db:
        created_users = []
        
        for i in range(count):
            # 生成唯一用户名
            username = generate_username()
            while True:
                result = await db.execute(select(User).where(User.username == username))
                if not result.scalar_one_or_none():
                    break
                username = generate_username()
            
            # 生成昵称
            nickname = generate_nickname()
            
            # 创建用户
            user = User(
                username=username,
                nickname=nickname,
                email=None,
                hashed_password=get_password_hash("123456"),  # 默认密码
                device_id=f"test_device_{random.randint(100000, 999999)}",
                is_guest=True,
                invite_code=generate_invite_code(),
                register_ip=f"192.168.1.{random.randint(1, 254)}",
                last_login_ip=f"192.168.1.{random.randint(1, 254)}",
            )
            db.add(user)
            await db.flush()
            
            # 创建VIP记录
            vip = UserVIP(user_id=user.id)
            db.add(vip)
            
            created_users.append({
                'id': user.id,
                'username': username,
                'nickname': nickname,
                'password': '123456'
            })
            
            print(f"✓ 已创建用户 {i+1}/{count}: {username} ({nickname})")
        
        await db.commit()
        
        print("\n" + "="*50)
        print(f"成功创建 {count} 个用户账号！")
        print("="*50)
        print("\n账号列表：")
        print("-"*50)
        for u in created_users:
            print(f"账号: {u['username']}  昵称: {u['nickname']}  密码: {u['password']}")
        print("-"*50)

if __name__ == "__main__":
    asyncio.run(generate_users(10))





