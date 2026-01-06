import sqlite3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

conn = sqlite3.connect('app.db')
c = conn.cursor()

# 检查是否已存在admin用户
c.execute("SELECT id FROM users WHERE username = 'admin'")
if c.fetchone():
    # 更新为管理员
    c.execute("UPDATE users SET role = 'super_admin' WHERE username = 'admin'")
    print("已将 admin 用户升级为超级管理员")
else:
    # 创建新管理员
    hashed = pwd_context.hash("admin123")
    c.execute("""
        INSERT INTO users (username, hashed_password, role, is_active, nickname)
        VALUES ('admin', ?, 'super_admin', 1, '管理员')
    """, (hashed,))
    print("已创建管理员账号: admin / admin123")

conn.commit()
conn.close()
