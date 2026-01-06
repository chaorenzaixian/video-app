"""
修复话题表：添加 parent_id + name 组合唯一约束
"""
import sqlite3

conn = sqlite3.connect('app.db')
c = conn.cursor()

# 1. 创建新表（带组合唯一约束）
c.execute("""
CREATE TABLE IF NOT EXISTS topics_new (
    id INTEGER PRIMARY KEY,
    parent_id INTEGER,
    name VARCHAR(50) NOT NULL,
    level INTEGER DEFAULT 1,
    icon VARCHAR(500),
    cover VARCHAR(500),
    description TEXT,
    post_count INTEGER DEFAULT 0,
    follow_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    children_count INTEGER DEFAULT 0,
    is_hot BOOLEAN DEFAULT 0,
    is_recommended BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME,
    FOREIGN KEY (parent_id) REFERENCES topics_new(id) ON DELETE CASCADE,
    UNIQUE (parent_id, name)
)
""")

# 2. 复制数据
c.execute("""
INSERT INTO topics_new (id, parent_id, name, level, icon, cover, description, 
    post_count, follow_count, view_count, children_count, is_hot, is_recommended, 
    is_active, sort_order, created_at)
SELECT id, parent_id, name, level, icon, cover, description,
    post_count, follow_count, view_count, children_count, is_hot, is_recommended,
    is_active, sort_order, created_at
FROM topics
""")

# 3. 删除旧表
c.execute("DROP TABLE topics")

# 4. 重命名新表
c.execute("ALTER TABLE topics_new RENAME TO topics")

# 5. 创建索引
c.execute("CREATE INDEX IF NOT EXISTS ix_topics_id ON topics (id)")
c.execute("CREATE INDEX IF NOT EXISTS ix_topics_name ON topics (name)")
c.execute("CREATE INDEX IF NOT EXISTS ix_topics_parent_id ON topics (parent_id)")

conn.commit()

# 验证
c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='topics'")
print("表结构:")
print(c.fetchone()[0])

c.execute("SELECT COUNT(*) FROM topics")
print(f"\n话题数: {c.fetchone()[0]}")

conn.close()
print("\n✓ 组合唯一约束已添加 (parent_id + name)!")
