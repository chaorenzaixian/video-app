"""
暗网视频专区数据库迁移脚本
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine, AsyncSessionLocal

async def migrate():
    async with engine.begin() as conn:
        # 创建暗网分类表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS darkweb_categories (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                description TEXT,
                icon VARCHAR(200),
                sort_order INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                parent_id INTEGER REFERENCES darkweb_categories(id),
                level INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("✓ 创建 darkweb_categories 表")
        
        # 创建暗网标签表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS darkweb_tags (
                id SERIAL PRIMARY KEY,
                name VARCHAR(30) NOT NULL UNIQUE,
                use_count INTEGER DEFAULT 0
            )
        """))
        print("✓ 创建 darkweb_tags 表")
        
        # 创建暗网视频表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS darkweb_videos (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                cover_url VARCHAR(500),
                original_url VARCHAR(500),
                hls_url VARCHAR(500),
                preview_url VARCHAR(500),
                duration FLOAT DEFAULT 0,
                file_size INTEGER DEFAULT 0,
                status VARCHAR(20) DEFAULT 'UPLOADING',
                quality VARCHAR(20) DEFAULT '720p',
                is_featured BOOLEAN DEFAULT FALSE,
                view_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                favorite_count INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                category_id INTEGER REFERENCES darkweb_categories(id),
                uploader_id INTEGER NOT NULL REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                published_at TIMESTAMP
            )
        """))
        print("✓ 创建 darkweb_videos 表")
        
        # 创建视频-标签关联表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS darkweb_video_tags_association (
                video_id INTEGER REFERENCES darkweb_videos(id) ON DELETE CASCADE,
                tag_id INTEGER REFERENCES darkweb_tags(id) ON DELETE CASCADE,
                PRIMARY KEY (video_id, tag_id)
            )
        """))
        print("✓ 创建 darkweb_video_tags_association 表")
        
        # 创建观看记录表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS darkweb_views (
                id SERIAL PRIMARY KEY,
                video_id INTEGER NOT NULL REFERENCES darkweb_videos(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id),
                ip_address VARCHAR(50),
                watch_duration FLOAT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("✓ 创建 darkweb_views 表")
        
        # 创建索引
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_darkweb_status_created ON darkweb_videos(status, created_at)
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_darkweb_category_status ON darkweb_videos(category_id, status)
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_darkweb_view_video ON darkweb_views(video_id, created_at)
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_darkweb_view_user ON darkweb_views(user_id, created_at)
        """))
        print("✓ 创建索引")
        
        # 添加系统配置
        await conn.execute(text("""
            INSERT INTO system_configs (key, value, description)
            VALUES ('darkweb_min_vip_level', '5', '暗网专区最低VIP等级要求')
            ON CONFLICT (key) DO NOTHING
        """))
        print("✓ 添加系统配置")
        
        # 添加默认分类
        await conn.execute(text("""
            INSERT INTO darkweb_categories (name, description, sort_order, level)
            VALUES 
                ('暴力血腥', '暴力血腥类视频', 1, 1),
                ('猎奇恐怖', '猎奇恐怖类视频', 2, 1),
                ('禁忌内容', '禁忌类视频', 3, 1)
            ON CONFLICT DO NOTHING
        """))
        print("✓ 添加默认分类")
        
    print("\n✅ 暗网视频专区数据库迁移完成!")

if __name__ == "__main__":
    asyncio.run(migrate())
