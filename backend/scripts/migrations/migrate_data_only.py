#!/usr/bin/env python3
"""只迁移数据（表结构已由SQLAlchemy创建）"""
import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import psycopg2
    from psycopg2.extras import execute_batch
except ImportError:
    print("请安装 psycopg2: pip install psycopg2-binary")
    sys.exit(1)

SQLITE_PATH = os.path.join(os.path.dirname(__file__), 'app.db')
POSTGRES_CONFIG = {
    'host': os.environ.get('PG_HOST', '127.0.0.1'),
    'port': int(os.environ.get('PG_PORT', 5432)),
    'user': os.environ.get('PG_USER', 'video_app'),
    'password': os.environ.get('PG_PASSWORD', 'VideoApp2026!'),
    'database': os.environ.get('PG_DATABASE', 'video_app')
}

def get_sqlite_tables(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    return [row[0] for row in cursor.fetchall()]

def get_pg_tables(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
    return [row[0] for row in cursor.fetchall()]

def get_table_columns(conn, table_name, is_pg=False):
    cursor = conn.cursor()
    if is_pg:
        cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position")
        return [row[0] for row in cursor.fetchall()]
    else:
        cursor.execute(f"PRAGMA table_info('{table_name}')")
        return [row[1] for row in cursor.fetchall()]

def get_pg_column_types(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = '{table_name}'
    """)
    return {row[0]: row[1] for row in cursor.fetchall()}

def convert_row(row, cols, col_types):
    result = []
    for i, val in enumerate(row):
        col = cols[i]
        col_type = col_types.get(col, '')
        if val is None:
            result.append(None)
        elif col_type == 'boolean':
            result.append(bool(val))
        else:
            result.append(val)
    return tuple(result)

def migrate_table(sqlite_conn, pg_conn, table_name):
    sqlite_cols = get_table_columns(sqlite_conn, table_name, False)
    pg_cols = get_table_columns(pg_conn, table_name, True)
    pg_col_types = get_pg_column_types(pg_conn, table_name)
    
    common_cols = [c for c in sqlite_cols if c in pg_cols]
    if not common_cols:
        print(f"  ⚠️ 表 {table_name} 无共同列")
        return
    
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    quoted_cols = ', '.join([f'"{c}"' for c in common_cols])
    sqlite_cursor.execute(f'SELECT {quoted_cols} FROM "{table_name}"')
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"  ⚪ 表 {table_name} 无数据")
        return
    
    # 转换数据类型
    converted = [convert_row(row, common_cols, pg_col_types) for row in rows]
    
    placeholders = ', '.join(['%s'] * len(common_cols))
    insert_sql = f'INSERT INTO "{table_name}" ({quoted_cols}) VALUES ({placeholders})'
    
    try:
        execute_batch(pg_cursor, insert_sql, converted, page_size=100)
        pg_conn.commit()
        print(f"  ✅ {table_name} ({len(rows)} 条)")
    except Exception as e:
        pg_conn.rollback()
        print(f"  ❌ {table_name}: {str(e)[:80]}")

def reset_sequences(pg_conn):
    cursor = pg_conn.cursor()
    cursor.execute("""
        SELECT tablename FROM pg_tables WHERE schemaname = 'public'
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    for table in tables:
        try:
            cursor.execute(f"""
                SELECT setval(pg_get_serial_sequence('"{table}"', 'id'), 
                       COALESCE((SELECT MAX(id) FROM "{table}"), 1), true)
            """)
            pg_conn.commit()
        except:
            pg_conn.rollback()

def main():
    print("=" * 50)
    print("SQLite → PostgreSQL 数据迁移 (仅数据)")
    print("=" * 50)
    
    if not os.path.exists(SQLITE_PATH):
        print(f"❌ SQLite文件不存在: {SQLITE_PATH}")
        return
    
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    print(f"✅ SQLite: {SQLITE_PATH}")
    
    try:
        pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
        print(f"✅ PostgreSQL: {POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}")
    except Exception as e:
        print(f"❌ PostgreSQL连接失败: {e}")
        return
    
    # 禁用触发器（包括外键检查）
    pg_cursor = pg_conn.cursor()
    
    pg_tables = get_pg_tables(pg_conn)
    sqlite_tables = get_sqlite_tables(sqlite_conn)
    
    common_tables = [t for t in sqlite_tables if t in pg_tables]
    print(f"\n迁移 {len(common_tables)} 个表...")
    
    # 先清空所有表
    for table in common_tables:
        try:
            pg_cursor.execute(f'TRUNCATE TABLE "{table}" CASCADE')
            pg_conn.commit()
        except:
            pg_conn.rollback()
    
    for table in common_tables:
        migrate_table(sqlite_conn, pg_conn, table)
    
    print("\n重置序列...")
    reset_sequences(pg_conn)
    
    sqlite_conn.close()
    pg_conn.close()
    print("\n✅ 迁移完成!")

if __name__ == '__main__':
    main()
