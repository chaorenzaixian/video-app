import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(
        user='video_app',
        password='VideoApp2026!',
        database='video_app',
        host='127.0.0.1',
        port=5432
    )
    
    # 查看user_vips表中管理员的VIP信息
    vip_info = await conn.fetchrow("SELECT * FROM user_vips WHERE user_id = 55")
    if vip_info:
        print(f"管理员VIP信息: {dict(vip_info)}")
    else:
        print("管理员在user_vips表中没有记录")
    
    # 查看vip_privileges表
    try:
        privileges = await conn.fetch("SELECT * FROM vip_privileges ORDER BY level")
        print("\nVIP特权等级表:")
        for p in privileges:
            print(f"Level {p['level']}: {p.get('name', 'N/A')}")
    except Exception as e:
        print(f"查询失败: {e}")
    
    await conn.close()

asyncio.run(main())
