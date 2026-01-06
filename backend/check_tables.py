import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'app.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查看所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("=== 所有表 ===")
for t in sorted(tables):
    print(f"  {t}")

# 检查tags表是否存在
if 'tags' in tables:
    print("\n=== tags表存在 ===")
    cursor.execute("SELECT * FROM tags LIMIT 5")
    print(cursor.fetchall())
else:
    print("\n=== tags表不存在! ===")

conn.close()
