import sqlite3
conn = sqlite3.connect('app.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(users)')
print("Users表结构:")
for col in cursor.fetchall():
    print(f"  {col[1]}: {col[2]}")

cursor.execute('SELECT * FROM users LIMIT 1')
row = cursor.fetchone()
if row:
    cursor.execute('PRAGMA table_info(users)')
    cols = [c[1] for c in cursor.fetchall()]
    print("\n第一行数据:")
    for i, val in enumerate(row):
        print(f"  {cols[i]}: {repr(val)[:50]}")
