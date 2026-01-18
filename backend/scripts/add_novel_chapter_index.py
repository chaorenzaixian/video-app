"""
添加小说章节表和评论表索引
"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import text
from app.core.database import async_engine

async def add_indexes():
    """添加索引"""
    async with async_engine.begin() as conn:
        # 小说章节索引
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_novel_chapters_chapter_num 
                ON novel_chapters (chapter_num)
            """))
            print("✓ 添加 chapter_num 索引成功")
        except Exception as e:
            print(f"chapter_num 索引: {e}")
        
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_novel_chapters_novel_chapter 
                ON novel_chapters (novel_id, chapter_num)
            """))
            print("✓ 添加章节复合索引成功")
        except Exception as e:
            print(f"章节复合索引: {e}")
        
        # 图集评论索引
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_gallery_comments_gallery_created 
                ON gallery_comments (gallery_id, created_at DESC)
            """))
            print("✓ 添加图集评论索引成功")
        except Exception as e:
            print(f"图集评论索引: {e}")
        
        # 小说评论索引
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_novel_comments_novel_created 
                ON novel_comments (novel_id, created_at DESC)
            """))
            print("✓ 添加小说评论索引成功")
        except Exception as e:
            print(f"小说评论索引: {e}")
        
        # 评论点赞索引
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_gallery_comment_likes_comment 
                ON gallery_comment_likes (comment_id)
            """))
            print("✓ 添加图集评论点赞索引成功")
        except Exception as e:
            print(f"图集评论点赞索引: {e}")
        
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_novel_comment_likes_comment 
                ON novel_comment_likes (comment_id)
            """))
            print("✓ 添加小说评论点赞索引成功")
        except Exception as e:
            print(f"小说评论点赞索引: {e}")
        
        # 分析表以更新统计信息
        try:
            await conn.execute(text("ANALYZE novel_chapters"))
            await conn.execute(text("ANALYZE gallery_comments"))
            await conn.execute(text("ANALYZE novel_comments"))
            await conn.execute(text("ANALYZE gallery_comment_likes"))
            await conn.execute(text("ANALYZE novel_comment_likes"))
            print("✓ 更新表统计信息成功")
        except Exception as e:
            print(f"ANALYZE: {e}")

if __name__ == "__main__":
    asyncio.run(add_indexes())
    print("\n索引添加完成！")
