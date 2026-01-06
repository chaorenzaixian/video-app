"""
迁移脚本：为话题表添加分级支持
"""
import sqlite3

conn = sqlite3.connect('app.db')
c = conn.cursor()

# 检查并添加新字段
def add_column_if_not_exists(table, column, column_type, default=None):
    c.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in c.fetchall()]
    if column not in columns:
        if default is not None:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type} DEFAULT {default}")
        else:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        print(f"✓ 添加字段: {table}.{column}")
    else:
        print(f"- 字段已存在: {table}.{column}")

# 添加新字段
add_column_if_not_exists('topics', 'parent_id', 'INTEGER', 'NULL')
add_column_if_not_exists('topics', 'level', 'INTEGER', '1')
add_column_if_not_exists('topics', 'icon', 'VARCHAR(500)', 'NULL')
add_column_if_not_exists('topics', 'children_count', 'INTEGER', '0')

# 移除 unique 约束（SQLite 不支持直接移除，需要重建表，这里跳过）
# 现有数据默认为顶级分类
c.execute("UPDATE topics SET level = 1 WHERE level IS NULL")
c.execute("UPDATE topics SET parent_id = NULL WHERE parent_id IS NULL")

conn.commit()

# 验证
c.execute("PRAGMA table_info(topics)")
print("\n话题表结构:")
for col in c.fetchall():
    print(f"  {col[1]}: {col[2]}")

c.execute("SELECT COUNT(*) FROM topics")
print(f"\n现有话题数: {c.fetchone()[0]}")

conn.close()
print("\n✓ 迁移完成!")
