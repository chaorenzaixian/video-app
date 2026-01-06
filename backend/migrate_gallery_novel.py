"""
迁移脚本：创建图集和小说相关表
"""
import sqlite3

conn = sqlite3.connect('app.db')
c = conn.cursor()

# 图集分类表
c.execute("""
CREATE TABLE IF NOT EXISTS gallery_categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME
)
""")
print("✓ gallery_categories 表已创建")

# 图集表
c.execute("""
CREATE TABLE IF NOT EXISTS galleries (
    id INTEGER PRIMARY KEY,
    category_id INTEGER,
    title VARCHAR(200) NOT NULL,
    cover VARCHAR(500) NOT NULL,
    images TEXT DEFAULT '[]',
    description TEXT,
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    image_count INTEGER DEFAULT 0,
    chapter_count INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'ongoing',
    is_hot BOOLEAN DEFAULT 0,
    is_recommended BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (category_id) REFERENCES gallery_categories(id)
)
""")
print("✓ galleries 表已创建")

# 小说分类表
c.execute("""
CREATE TABLE IF NOT EXISTS novel_categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    novel_type VARCHAR(20) DEFAULT 'text',
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME
)
""")
print("✓ novel_categories 表已创建")

# 小说表
c.execute("""
CREATE TABLE IF NOT EXISTS novels (
    id INTEGER PRIMARY KEY,
    category_id INTEGER,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(100),
    cover VARCHAR(500) NOT NULL,
    description TEXT,
    novel_type VARCHAR(20) DEFAULT 'text',
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    chapter_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'ongoing',
    is_hot BOOLEAN DEFAULT 0,
    is_recommended BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (category_id) REFERENCES novel_categories(id)
)
""")
print("✓ novels 表已创建")

# 小说章节表
c.execute("""
CREATE TABLE IF NOT EXISTS novel_chapters (
    id INTEGER PRIMARY KEY,
    novel_id INTEGER NOT NULL,
    chapter_num INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    audio_url VARCHAR(500),
    is_free BOOLEAN DEFAULT 1,
    created_at DATETIME,
    FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE
)
""")
print("✓ novel_chapters 表已创建")

# 创建索引
c.execute("CREATE INDEX IF NOT EXISTS ix_galleries_category ON galleries(category_id)")
c.execute("CREATE INDEX IF NOT EXISTS ix_novels_category ON novels(category_id)")
c.execute("CREATE INDEX IF NOT EXISTS ix_novel_chapters_novel ON novel_chapters(novel_id)")

conn.commit()
conn.close()
print("\n✓ 所有表创建完成!")
