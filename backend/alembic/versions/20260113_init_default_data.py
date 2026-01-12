"""init default data

Revision ID: init_default_data
Revises: baseline_initial
Create Date: 2026-01-13

初始化默认数据：任务、礼物、充值套餐等
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from decimal import Decimal


revision: str = 'init_default_data'
down_revision: Union[str, Sequence[str], None] = 'baseline_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """插入默认数据"""
    conn = op.get_bind()
    
    # 1. 默认任务
    tasks = [
        ("checkin", "签到任务", "每日签到 +5积分", 5, 1, "○", "linear-gradient(360deg, #9e52cf, #4d45bf)", "claim", None, 1),
        ("post", "每日发帖", "发布帖子 +5积分", 5, 1, "📷", "linear-gradient(360deg, #9e52cf, #4d45bf)", "redirect", "/user/post", 2),
        ("comment_post", "帖子评论", "帖子评论十个字以上 获得5积分", 5, 5, "✏️", "linear-gradient(135deg, #22c55e, #10b981)", "redirect", None, 3),
        ("comment_video", "视频评论", "视频评论十个字以上 获得5积分", 5, 5, "✏️", "linear-gradient(135deg, #22c55e, #10b981)", "redirect", None, 4),
        ("invite", "每日邀请", "每日邀请用户+20积分", 20, 10, "👥", "linear-gradient(360deg, #9e52cf, #4d45bf)", "redirect", "/user/promotion", 5),
        ("buy_vip", "购买VIP+100积分", "购买任意VIP 即可获得100积分", 100, 0, "💎", "linear-gradient(360deg, #9e52cf, #4d45bf)", "redirect", "/user/vip", 6),
        ("download", "下载APP", "下载好色，即可获得20积分", 20, 1, "⬇️", "linear-gradient(360deg, #9e52cf, #4d45bf)", "claim", None, 7),
    ]
    
    for task in tasks:
        result = conn.execute(text("SELECT id FROM tasks WHERE task_type = :task_type"), {"task_type": task[0]})
        if not result.fetchone():
            conn.execute(text("""
                INSERT INTO tasks (task_type, task_name, task_desc, points_reward, daily_limit, icon, icon_bg, action_type, action_url, sort_order, is_active)
                VALUES (:task_type, :task_name, :task_desc, :points_reward, :daily_limit, :icon, :icon_bg, :action_type, :action_url, :sort_order, true)
            """), {
                "task_type": task[0], "task_name": task[1], "task_desc": task[2],
                "points_reward": task[3], "daily_limit": task[4], "icon": task[5],
                "icon_bg": task[6], "action_type": task[7], "action_url": task[8], "sort_order": task[9]
            })
    
    # 2. 默认礼物
    gifts = [
        ("小心心", "❤️", 1, 1),
        ("棒棒糖", "🍭", 5, 2),
        ("玫瑰花", "🌹", 10, 3),
        ("啤酒", "🍺", 20, 4),
        ("蛋糕", "🎂", 50, 5),
        ("钻戒", "💍", 100, 6),
        ("皇冠", "👑", 200, 7),
        ("火箭", "🚀", 500, 8),
        ("城堡", "🏰", 1000, 9),
        ("嘉年华", "🎪", 5000, 10),
    ]
    
    for gift in gifts:
        result = conn.execute(text("SELECT id FROM gifts WHERE name = :name"), {"name": gift[0]})
        if not result.fetchone():
            conn.execute(text("""
                INSERT INTO gifts (name, icon, coins_price, sort_order, is_active)
                VALUES (:name, :icon, :coins_price, :sort_order, true)
            """), {"name": gift[0], "icon": gift[1], "coins_price": gift[2], "sort_order": gift[3]})
    
    # 3. 默认充值套餐
    packages = [
        ("体验包", 60, 0, 6.00, "体验", False, False, 1),
        ("小额充值", 120, 10, 12.00, None, False, False, 2),
        ("超值套餐", 300, 50, 30.00, "热门", True, False, 3),
        ("畅享套餐", 680, 150, 68.00, "推荐", False, False, 4),
        ("至尊套餐", 1280, 400, 128.00, "超值", False, False, 5),
        ("首充礼包", 100, 100, 6.00, "首充2倍", False, True, 0),
    ]
    
    for pkg in packages:
        result = conn.execute(text("SELECT id FROM recharge_packages WHERE name = :name"), {"name": pkg[0]})
        if not result.fetchone():
            conn.execute(text("""
                INSERT INTO recharge_packages (name, coins, bonus_coins, price, tag, is_hot, is_first_charge, sort_order, is_active)
                VALUES (:name, :coins, :bonus_coins, :price, :tag, :is_hot, :is_first_charge, :sort_order, true)
            """), {
                "name": pkg[0], "coins": pkg[1], "bonus_coins": pkg[2], "price": pkg[3],
                "tag": pkg[4], "is_hot": pkg[5], "is_first_charge": pkg[6], "sort_order": pkg[7]
            })
    
    print("[OK] Default data initialized")


def downgrade() -> None:
    """删除默认数据（谨慎操作）"""
    # 通常不删除初始数据
    pass
