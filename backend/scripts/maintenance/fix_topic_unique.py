"""
修复话题表的唯一约束问题
SQLite 不支持直接删除约束，需要重建表
"""
import sqlite3

conn = sqlite3.connect('app.db')
c = conn.cursor()

# 1. 创建新表（不带 name 唯一约束）
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
    FOREIGN KEY (parent_id) REFERENCES topics_new(id) ON DELETE CASCADE
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
c.execute("PRAGMA table_info(topics)")
print("话题表结构:")
for col in c.fetchall():
    print(f"  {col[1]}: {col[2]}")

c.execute("SELECT COUNT(*) FROM topics")
print(f"\n话题数: {c.fetchone()[0]}")

conn.close()
print("\n✓ 唯一约束已移除!")
