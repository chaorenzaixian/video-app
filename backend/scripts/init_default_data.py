#!/usr/bin/env python
"""
初始化默认数据脚本
用法: python -m scripts.init_default_data
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from sqlalchemy import select, text


async def init_default_tasks():
    """初始化默认任务配置"""
    from app.models.points import Task
    
    default_tasks = [
        {"task_type": "checkin", "task_name": "签到任务", "task_desc": "每日签到 +5积分", "points_reward": 5, "daily_limit": 1, "icon": "○", "icon_bg": "linear-gradient(360deg, #9e52cf, #4d45bf)", "action_type": "claim", "sort_order": 1, "is_active": True},
        {"task_type": "post", "task_name": "每日发帖", "task_desc": "发布帖子 +5积分", "points_reward": 5, "daily_limit": 1, "icon": "📷", "icon_bg": "linear-gradient(360deg, #9e52cf, #4d45bf)", "action_type": "redirect", "action_url": "/user/post", "sort_order": 2, "is_active": True},
        {"task_type": "comment_post", "task_name": "帖子评论", "task_desc": "帖子评论十个字以上 获得5积分", "points_reward": 5, "daily_limit": 5, "icon": "✏️", "icon_bg": "linear-gradient(135deg, #22c55e, #10b981)", "action_type": "redirect", "sort_order": 3, "is_active": True},
        {"task_type": "comment_video", "task_name": "视频评论", "task_desc": "视频评论十个字以上 获得5积分", "points_reward": 5, "daily_limit": 5, "icon": "✏️", "icon_bg": "linear-gradient(135deg, #22c55e, #10b981)", "action_type": "redirect", "sort_order": 4, "is_active": True},
        {"task_type": "invite", "task_name": "每日邀请", "task_desc": "每日邀请用户+20积分", "points_reward": 20, "daily_limit": 10, "icon": "👥", "icon_bg": "linear-gradient(360deg, #9e52cf, #4d45bf)", "action_type": "redirect", "action_url": "/user/promotion", "sort_order": 5, "is_active": True},
        {"task_type": "buy_vip", "task_name": "购买VIP+100积分", "task_desc": "购买任意VIP 即可获得100积分", "points_reward": 100, "daily_limit": 0, "icon": "💎", "icon_bg": "linear-gradient(360deg, #9e52cf, #4d45bf)", "action_type": "redirect", "action_url": "/user/vip", "sort_order": 6, "is_active": True},
        {"task_type": "download", "task_name": "下载APP", "task_desc": "下载好色，即可获得20积分", "points_reward": 20, "daily_limit": 1, "icon": "⬇️", "icon_bg": "linear-gradient(360deg, #9e52cf, #4d45bf)", "action_type": "claim", "sort_order": 7, "is_active": True},
    ]
    
    async with AsyncSessionLocal() as db:
        added = 0
        for config in default_tasks:
            result = await db.execute(select(Task).where(Task.task_type == config["task_type"]))
            if not result.scalar_one_or_none():
                db.add(Task(**config))
                added += 1
                print(f"  [+] Task: {config['task_name']}")
        if added:
            await db.commit()
        print(f"[OK] Tasks: {added} added")


async def init_default_exchange_items():
    """初始化默认兑换商品"""
    from app.models.points import ExchangeItem
    
    default_items = [
        {"item_name": "VIP体验卡1天", "item_desc": "畅游全站VIP资源", "item_type": "vip_days", "item_value": 1, "points_cost": 100, "stock": -1, "daily_limit": 1, "is_active": True, "sort_order": 1},
        {"item_name": "情趣盲盒", "item_desc": "兑换后联系客服领取!", "item_type": "gift", "item_value": 1, "points_cost": 3000, "stock": -1, "daily_limit": 1, "is_active": True, "sort_order": 2},
        {"item_name": "VIP体验卡7天", "item_desc": "畅游全站VIP资源", "item_type": "vip_days", "item_value": 7, "points_cost": 200, "stock": -1, "daily_limit": 1, "is_active": True, "sort_order": 3},
        {"item_name": "VIP体验卡30天", "item_desc": "畅游全站VIP资源", "item_type": "vip_days", "item_value": 30, "points_cost": 600, "stock": -1, "daily_limit": 1, "is_active": True, "sort_order": 6},
    ]
    
    async with AsyncSessionLocal() as db:
        added = 0
        for config in default_items:
            result = await db.execute(select(ExchangeItem).where(ExchangeItem.item_name == config["item_name"], ExchangeItem.points_cost == config["points_cost"]))
            if not result.first():
                db.add(ExchangeItem(**config))
                added += 1
                print(f"  [+] Exchange: {config['item_name']}")
        if added:
            await db.commit()
        print(f"[OK] Exchange items: {added} added")


async def init_default_gifts():
    """初始化默认礼物"""
    from app.models.creator import Gift
    
    default_gifts = [
        {"name": "小心心", "icon": "❤️", "coins_price": 1, "sort_order": 1},
        {"name": "棒棒糖", "icon": "🍭", "coins_price": 5, "sort_order": 2},
        {"name": "玫瑰花", "icon": "🌹", "coins_price": 10, "sort_order": 3},
        {"name": "啤酒", "icon": "🍺", "coins_price": 20, "sort_order": 4},
        {"name": "蛋糕", "icon": "🎂", "coins_price": 50, "sort_order": 5},
        {"name": "钻戒", "icon": "💍", "coins_price": 100, "sort_order": 6},
        {"name": "皇冠", "icon": "👑", "coins_price": 200, "sort_order": 7},
        {"name": "火箭", "icon": "🚀", "coins_price": 500, "sort_order": 8},
        {"name": "城堡", "icon": "🏰", "coins_price": 1000, "sort_order": 9},
        {"name": "嘉年华", "icon": "🎪", "coins_price": 5000, "sort_order": 10},
    ]
    
    async with AsyncSessionLocal() as db:
        added = 0
        for config in default_gifts:
            result = await db.execute(select(Gift).where(Gift.name == config["name"]))
            if not result.first():
                db.add(Gift(**config, is_active=True))
                added += 1
        if added:
            await db.commit()
        print(f"[OK] Gifts: {added} added")


async def init_default_recharge_packages():
    """初始化默认充值套餐"""
    from app.models.coins import RechargePackage
    from decimal import Decimal
    
    default_packages = [
        {"name": "体验包", "coins": 60, "bonus_coins": 0, "price": Decimal("6.00"), "tag": "体验", "sort_order": 1, "is_active": True},
        {"name": "小额充值", "coins": 120, "bonus_coins": 10, "price": Decimal("12.00"), "sort_order": 2, "is_active": True},
        {"name": "超值套餐", "coins": 300, "bonus_coins": 50, "price": Decimal("30.00"), "tag": "热门", "is_hot": True, "sort_order": 3, "is_active": True},
        {"name": "畅享套餐", "coins": 680, "bonus_coins": 150, "price": Decimal("68.00"), "tag": "推荐", "sort_order": 4, "is_active": True},
        {"name": "至尊套餐", "coins": 1280, "bonus_coins": 400, "price": Decimal("128.00"), "tag": "超值", "sort_order": 5, "is_active": True},
        {"name": "首充礼包", "coins": 100, "bonus_coins": 100, "price": Decimal("6.00"), "original_price": Decimal("10.00"), "tag": "首充2倍", "is_first_charge": True, "sort_order": 0, "is_active": True},
    ]
    
    async with AsyncSessionLocal() as db:
        added = 0
        for config in default_packages:
            result = await db.execute(select(RechargePackage).where(RechargePackage.name == config["name"]))
            if not result.first():
                db.add(RechargePackage(**config))
                added += 1
        if added:
            await db.commit()
        print(f"[OK] Recharge packages: {added} added")


async def init_default_official_groups():
    """初始化默认官方群组"""
    from app.models.ad import OfficialGroup, OfficialGroupType
    
    default_groups = [
        {"name": "官方土豆群", "group_type": OfficialGroupType.COMMUNITY, "icon_type": "rocket", "icon_bg": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", "url": "https://t.me/example1", "sort_order": 1},
        {"name": "官方飞机群", "group_type": OfficialGroupType.COMMUNITY, "icon_type": "telegram", "icon_bg": "linear-gradient(135deg, #00b4db 0%, #0083b0 100%)", "url": "https://t.me/example2", "sort_order": 2},
        {"name": "官方商务", "group_type": OfficialGroupType.BUSINESS, "icon_type": "briefcase", "icon_bg": "linear-gradient(135deg, #00b4db 0%, #0083b0 100%)", "url": "https://t.me/business1", "sort_order": 1},
        {"name": "渠道合作", "group_type": OfficialGroupType.BUSINESS, "icon_type": "heart", "icon_bg": "linear-gradient(135deg, #00b4db 0%, #0083b0 100%)", "url": "https://t.me/business2", "sort_order": 2},
    ]
    
    async with AsyncSessionLocal() as db:
        added = 0
        for config in default_groups:
            result = await db.execute(select(OfficialGroup).where(OfficialGroup.name == config["name"]))
            if not result.first():
                db.add(OfficialGroup(**config, is_active=True))
                added += 1
        if added:
            await db.commit()
        print(f"[OK] Official groups: {added} added")


async def main():
    """运行所有初始化"""
    print("=" * 50)
    print("Initializing default data...")
    print("=" * 50)
    
    await init_default_tasks()
    await init_default_exchange_items()
    await init_default_gifts()
    await init_default_recharge_packages()
    await init_default_official_groups()
    
    print("=" * 50)
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
