import sqlite3
from datetime import datetime

conn = sqlite3.connect('app.db')
c = conn.cursor()

# 查看有问题的用户
c.execute("SELECT id, username, invite_count, is_guest, created_at FROM users WHERE invite_count IS NULL OR is_guest IS NULL OR created_at IS NULL LIMIT 10")
print("有问题的用户:")
for row in c.fetchall():
    print(f"  ID: {row[0]}, Username: {row[1]}, invite_count: {row[2]}, is_guest: {row[3]}, created_at: {row[4]}")

# 修复 invite_count
c.execute("UPDATE users SET invite_count = 0 WHERE invite_count IS NULL")
print(f"修复 invite_count: {c.rowcount} 行")

# 修复 is_guest
c.execute("UPDATE users SET is_guest = 0 WHERE is_guest IS NULL")
print(f"修复 is_guest: {c.rowcount} 行")

# 修复 created_at
now = datetime.now().isoformat()
c.execute("UPDATE users SET created_at = ? WHERE created_at IS NULL", (now,))
print(f"修复 created_at: {c.rowcount} 行")

conn.commit()

# 验证
c.execute("SELECT COUNT(*) FROM users WHERE invite_count IS NULL OR is_guest IS NULL OR created_at IS NULL")
print(f"剩余问题用户数: {c.fetchone()[0]}")

conn.close()
print("完成!")
