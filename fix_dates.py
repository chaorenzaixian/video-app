import sqlite3
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# 查找并修复所有表中的日期格式问题
tables = ['videos', 'users', 'comments', 'posts', 'banners', 'func_entries']
date_columns = ['created_at', 'updated_at', 'last_login']

fixed = 0
for table in tables:
    try:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        
        for col in date_columns:
            if col in columns:
                # 修复5位毫秒的日期
                cursor.execute(f"UPDATE {table} SET {col} = {col} || '0' WHERE length({col}) = 25 AND {col} LIKE '%.%'")
                if cursor.rowcount > 0:
                    print(f"Fixed {cursor.rowcount} records in {table}.{col}")
                    fixed += cursor.rowcount
    except Exception as e:
        print(f"Error with {table}: {e}")

conn.commit()
print(f"Total fixed: {fixed}")
conn.close()
