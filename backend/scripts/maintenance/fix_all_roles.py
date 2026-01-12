import sqlite3

conn = sqlite3.connect('app.db')
c = conn.cursor()

# 查看所有不同的角色值
c.execute("SELECT DISTINCT role FROM users")
print("当前角色值:", [r[0] for r in c.fetchall()])

# 修复所有角色值为大写
c.execute("UPDATE users SET role = 'SUPER_ADMIN' WHERE LOWER(role) = 'super_admin'")
c.execute("UPDATE users SET role = 'ADMIN' WHERE LOWER(role) = 'admin'")
c.execute("UPDATE users SET role = 'USER' WHERE LOWER(role) = 'user' OR role IS NULL OR role = ''")
c.execute("UPDATE users SET role = 'VIP' WHERE LOWER(role) = 'vip'")

conn.commit()

# 验证
c.execute("SELECT DISTINCT role FROM users")
print("修复后角色值:", [r[0] for r in c.fetchall()])

c.execute("SELECT COUNT(*) FROM users")
print("总用户数:", c.fetchone()[0])

conn.close()
print("完成!")
