import sqlite3
conn = sqlite3.connect('backend/app.db')
c = conn.cursor()

# 查看所有表
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
print("Tables:", [t[0] for t in tables if 'vip' in t[0].lower()])

# 查看user_vips表
try:
    c.execute("SELECT * FROM user_vips LIMIT 5")
    rows = c.fetchall()
    print("user_vips:", rows)
except Exception as e:
    print("Error:", e)
