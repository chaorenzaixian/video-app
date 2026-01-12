import sqlite3

conn = sqlite3.connect('app.db')
c = conn.cursor()

# 修复角色值为大写
c.execute("UPDATE users SET role = 'SUPER_ADMIN' WHERE role = 'super_admin'")
c.execute("UPDATE users SET role = 'ADMIN' WHERE role = 'admin'")
c.execute("UPDATE users SET role = 'USER' WHERE role = 'user'")
c.execute("UPDATE users SET role = 'VIP' WHERE role = 'vip'")

conn.commit()
print("角色值已修复为大写格式")

# 验证
c.execute("SELECT id, username, role FROM users WHERE role IN ('ADMIN', 'SUPER_ADMIN') LIMIT 5")
for row in c.fetchall():
    print(f"ID: {row[0]}, 用户名: {row[1]}, 角色: {row[2]}")

conn.close()
