"""添加图集评论点赞表"""
import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(
        host='127.0.0.1',
        port=5432,
        user='video_app',
        password='VideoApp2026!',
        database='video_app'
    )
    
    try:
        # 创建评论点赞表
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS gallery_comment_likes (
                id SERIAL PRIMARY KEY,
                comment_id INTEGER NOT NULL REFERENCES gallery_comments(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("[OK] gallery_comment_likes 表创建成功")
        
        # 创建唯一索引
        try:
            await conn.execute('''
                CREATE UNIQUE INDEX IF NOT EXISTS idx_gallery_comment_like_unique 
                ON gallery_comment_likes(comment_id, user_id)
            ''')
            print("[OK] 唯一索引创建成功")
        except Exception as e:
            print(f"[!] 索引可能已存在: {e}")
            
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
