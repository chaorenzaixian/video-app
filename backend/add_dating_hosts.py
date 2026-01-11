"""
批量添加裸聊主播数据
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

# 分类: 学生萝莉, 人妻少妇, 主播御姐, 模特兼职
hosts_data = [
    # 学生萝莉
    ("小爱爱", 19, 160, 45, "C罩杯", "学生萝莉", 9),
    ("草莓萝莉", 22, 165, 49, "C罩杯", "学生萝莉", 2),
    ("艺校校花", 22, 165, 47, "C罩杯", "学生萝莉", 5),
    ("芒果萝莉", 20, 162, 49, "C罩杯", "学生萝莉", 2),
    ("母狗薯塔", 19, 168, 47, "D罩杯", "学生萝莉", 0),
    ("蜜桃臀-靓靓", 18, 167, 52, "D罩杯", "学生萝莉", 0),
    ("反差长安", 17, 163, 50, "C罩杯", "学生萝莉", 2),
    ("花花", 19, 160, 48, "E罩杯", "学生萝莉", 0),
    ("柠檬萝莉", 17, 158, 50, "B罩杯", "学生萝莉", 2),
    ("罗绮萝莉", 19, 169, 47, "C罩杯", "学生萝莉", 0),
    ("小恶魔", 20, 168, 45, "C罩杯", "学生萝莉", 4),
    ("小樱", 19, 168, 46, "C罩杯", "学生萝莉", 0),
    
    # 人妻少妇
    ("小尤物", 25, 166, 17, "C罩杯", "人妻少妇", 2),
    ("巨乳御姐", 28, 162, 55, "E罩杯", "人妻少妇", 0),
    ("波霸少妇", 25, 160, 52, "C罩杯", "人妻少妇", 0),
    ("苏苏", 24, 172, 47, "C罩杯", "人妻少妇", 0),
    ("大魔王", 20, 173, 50, "D罩杯", "人妻少妇", 4),
    ("兔兔", 25, 173, 50, "B罩杯", "人妻少妇", 0),
    ("初恋", 24, 168, 50, "D罩杯", "人妻少妇", 2),
    ("成都兼职前台", 22, 165, 47, "C罩杯", "人妻少妇", 2),
    ("江苏人妻", 28, 160, 50, "C罩杯", "人妻少妇", 1),
    ("贵州良家素人", 19, 168, 48, "C罩杯", "人妻少妇", 2),
    ("黑龙江大奶少妇", 29, 160, 50, "D罩杯", "人妻少妇", 2),
    
    # 主播御姐
    ("成都萝莉", 21, 160, 46, "C罩杯", "主播御姐", 1),
    ("杭州喜儿", 23, 164, 45, "C罩杯", "主播御姐", 1),
    ("玉玉", 23, 167, 46, "B罩杯", "主播御姐", 1),
    ("小柚", 24, 165, 49, "B罩杯", "主播御姐", 1),
    ("梦梦", 21, 168, 49, "C罩杯", "主播御姐", 10),
    ("觅觅", 24, 173, 47, "B罩杯", "主播御姐", 1),
    ("胡桃", 22, 168, 50, "C罩杯", "主播御姐", 5),
    ("林弯弯", 20, 170, 48, "B罩杯", "主播御姐", 1),
]

async def add_hosts():
    async with engine.begin() as conn:
        # 先清空现有数据
        await conn.execute(text("DELETE FROM dating_hosts"))
        
        # 批量插入
        for i, (name, age, height, weight, cup, sub_category, chat_count) in enumerate(hosts_data):
            await conn.execute(text("""
                INSERT INTO dating_hosts (nickname, age, height, weight, cup, category, sub_category, chat_count, sort_order, is_active)
                VALUES (:nickname, :age, :height, :weight, :cup, 'chat', :sub_category, :chat_count, :sort_order, TRUE)
            """), {
                "nickname": name,
                "age": age,
                "height": height,
                "weight": weight,
                "cup": cup,
                "sub_category": sub_category,
                "chat_count": chat_count,
                "sort_order": i
            })
        
        print(f"成功添加 {len(hosts_data)} 个主播!")

if __name__ == "__main__":
    asyncio.run(add_hosts())
