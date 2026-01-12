#!/usr/bin/env python3
"""
SQLite to PostgreSQL 数据迁移脚本
"""
import os
import sys
import sqlite3
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import psycopg2
    from psycopg2.extras import execute_batch
except ImportError:
    print("请安装 psycopg2: pip install psycopg2-binary")
    sys.exit(1)

# 配置
SQLITE_PATH = os.path.join(os.path.dirname(__file__), 'app.db')
POSTGRES_CONFIG = {
    'host': os.environ.get('PG_HOST', '127.0.0.1'),
    'port': int(os.environ.get('PG_PORT', 5432)),
    'user': os.environ.get('PG_USER', 'video_app'),
    'password': os.environ.get('PG_PASSWORD', 'VideoApp2026!'),
    'database': os.environ.get('PG_DATABASE', 'video_app')
}

def get_sqlite_tables(conn):
    """获取所有表名"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables

def get_table_info(conn, table_name):
    """获取表结构"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info('{table_name}')")
    columns = []
    for row in cursor.fetchall():
        columns.append({
            'cid': row[0],
            'name': row[1],
            'type': row[2].upper() if row[2] else 'TEXT',
            'notnull': row[3],
            'default': row[4],
            'pk': row[5]
        })
    cursor.close()
    return columns

def sqlite_to_postgres_type(sqlite_type, col_name):
    """SQLite类型转PostgreSQL类型"""
    sqlite_type = sqlite_type.upper() if sqlite_type else 'TEXT'
    
    # 根据列名推断类型
    if col_name == 'id':
        return 'SERIAL PRIMARY KEY'
    # device_id, session_id 等是字符串，不是整数
    if col_name in ['device_id', 'session_id', 'current_session_id', 'invite_code']:
        return 'VARCHAR(100)'
    
    # 优先使用SQLite声明的类型
    if 'VARCHAR' in sqlite_type:
        return sqlite_type
    if 'TEXT' in sqlite_type:
        return 'TEXT'
    if 'BOOLEAN' in sqlite_type:
        return 'BOOLEAN'
    if 'DATETIME' in sqlite_type or 'TIMESTAMP' in sqlite_type:
        return 'TIMESTAMP'
    
    if col_name.endswith('_id') and col_name not in ['device_id', 'session_id']:
        return 'INTEGER'
    if col_name in ['is_active', 'is_admin', 'is_vip', 'is_deleted', 'is_top', 'is_hot']:
        return 'BOOLEAN'
    if col_name.endswith('_at') or col_name in ['created_at', 'updated_at', 'expires_at', 'last_login']:
        return 'TIMESTAMP'
    if col_name in ['price', 'amount', 'balance', 'points']:
        return 'DECIMAL(10,2)'
    
    # 根据SQLite类型转换
    if 'INT' in sqlite_type:
        return 'INTEGER'
    elif 'CHAR' in sqlite_type or 'TEXT' in sqlite_type or 'CLOB' in sqlite_type:
        return 'TEXT'
    elif 'BLOB' in sqlite_type:
        return 'BYTEA'
    elif 'REAL' in sqlite_type or 'FLOA' in sqlite_type or 'DOUB' in sqlite_type:
        return 'DOUBLE PRECISION'
    elif 'BOOL' in sqlite_type:
        return 'BOOLEAN'
    elif 'DATE' in sqlite_type or 'TIME' in sqlite_type:
        return 'TIMESTAMP'
    elif 'NUMERIC' in sqlite_type or 'DECIMAL' in sqlite_type:
        return 'DECIMAL(10,2)'
    else:
        return 'TEXT'

def create_postgres_table(pg_conn, table_name, columns):
    """创建PostgreSQL表"""
    cursor = pg_conn.cursor()
    
    # 删除已存在的表
    cursor.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
    
    col_defs = []
    for col in columns:
        pg_type = sqlite_to_postgres_type(col['type'], col['name'])
        
        if 'PRIMARY KEY' in pg_type:
            col_defs.append(f'"{col["name"]}" {pg_type}')
        else:
            nullable = 'NOT NULL' if col['notnull'] and col['name'] != 'id' else ''
            col_defs.append(f'"{col["name"]}" {pg_type} {nullable}'.strip())
    
    create_sql = f'CREATE TABLE "{table_name}" (\n  ' + ',\n  '.join(col_defs) + '\n)'
    
    try:
        cursor.execute(create_sql)
        pg_conn.commit()
        print(f"  ✅ 创建表: {table_name}")
        return True
    except Exception as e:
        pg_conn.rollback()
        print(f"  ❌ 创建表失败 {table_name}: {e}")
        return False
    finally:
        cursor.close()

def convert_value(val, col_name, pg_type):
    """转换值类型"""
    if val is None:
        return None
    
    # 布尔值转换
    if 'BOOLEAN' in pg_type or col_name.startswith('is_'):
        if isinstance(val, str):
            return val.lower() in ('true', '1', 'yes')
        return bool(val)
    
    # 时间戳处理
    if 'TIMESTAMP' in pg_type:
        if isinstance(val, str) and val:
            # 修复无效的时间格式
            val = re.sub(r'\.(\d{5})$', r'.0\1', val)  # 5位微秒补0
            return val
        return val
    
    return val

def migrate_table_data(sqlite_conn, pg_conn, table_name, columns):
    """迁移表数据"""
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    col_names = [col['name'] for col in columns]
    quoted_cols = ', '.join(['"' + c + '"' for c in col_names])
    sqlite_cursor.execute(f'SELECT {quoted_cols} FROM "{table_name}"')
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"  ⚪ 表 {table_name} 无数据")
        return
    
    # 转换数据
    converted_rows = []
    for row in rows:
        converted_row = []
        for i, val in enumerate(row):
            col = columns[i]
            pg_type = sqlite_to_postgres_type(col['type'], col['name'])
            converted_row.append(convert_value(val, col['name'], pg_type))
        converted_rows.append(tuple(converted_row))
    
    # 插入数据
    pg_col_names = [f'"{c}"' for c in col_names]
    placeholders = ', '.join(['%s'] * len(columns))
    insert_sql = f'INSERT INTO "{table_name}" ({", ".join(pg_col_names)}) VALUES ({placeholders})'
    
    try:
        execute_batch(pg_cursor, insert_sql, converted_rows, page_size=100)
        pg_conn.commit()
        print(f"  ✅ 迁移数据: {table_name} ({len(rows)} 条)")
    except Exception as e:
        pg_conn.rollback()
        print(f"  ❌ 迁移数据失败 {table_name}: {e}")
    finally:
        sqlite_cursor.close()
        pg_cursor.close()

def reset_sequence(pg_conn, table_name):
    """重置序列"""
    cursor = pg_conn.cursor()
    try:
        cursor.execute(f'''
            SELECT setval(pg_get_serial_sequence('"{table_name}"', 'id'), 
                   COALESCE((SELECT MAX(id) FROM "{table_name}"), 1))
        ''')
        pg_conn.commit()
    except:
        pg_conn.rollback()
    finally:
        cursor.close()

def main():
    print("=" * 50)
    print("SQLite → PostgreSQL 数据迁移")
    print("=" * 50)
    print()
    
    # 检查SQLite文件
    if not os.path.exists(SQLITE_PATH):
        print(f"❌ SQLite文件不存在: {SQLITE_PATH}")
        return
    
    # 连接SQLite
    print("1. 连接 SQLite...")
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    print(f"   ✅ SQLite 连接成功: {SQLITE_PATH}")
    
    # 连接PostgreSQL
    print("2. 连接 PostgreSQL...")
    try:
        pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
        print(f"   ✅ PostgreSQL 连接成功: {POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}")
    except Exception as e:
        print(f"   ❌ PostgreSQL 连接失败: {e}")
        sqlite_conn.close()
        return
    
    # 获取表列表
    print("3. 获取表列表...")
    tables = get_sqlite_tables(sqlite_conn)
    print(f"   找到 {len(tables)} 个表: {', '.join(tables[:5])}...")
    
    # 创建表结构
    print("\n4. 创建表结构...")
    for table in tables:
        columns = get_table_info(sqlite_conn, table)
        create_postgres_table(pg_conn, table, columns)
    
    # 迁移数据
    print("\n5. 迁移数据...")
    for table in tables:
        columns = get_table_info(sqlite_conn, table)
        migrate_table_data(sqlite_conn, pg_conn, table, columns)
        reset_sequence(pg_conn, table)
    
    sqlite_conn.close()
    pg_conn.close()
    
    print("\n" + "=" * 50)
    print("✅ 迁移完成!")
    print("=" * 50)

if __name__ == '__main__':
    main()
