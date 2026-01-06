import sqlite3
conn = sqlite3.connect('app.db')
c = conn.cursor()
c.execute("SELECT id, username, role FROM users WHERE role IN ('admin', 'super_admin') LIMIT 5")
for row in c.fetchall():
    print(f"ID: {row[0]}, 用户名: {row[1]}, 角色: {row[2]}")
conn.close()
