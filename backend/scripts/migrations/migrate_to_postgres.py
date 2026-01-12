#!/usr/bin/env python3
"""
MySQL to PostgreSQL 数据迁移脚本
"""
import os
import sys
import asyncio
from datetime import datetime

# 设置路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pymysql
import psycopg2
from psycopg2.extras import execute_values

# 数据库配置
MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'video_app',
    'password': 'RmYtmssLzZMXjbbM',
    'database': 'video_app',
    'charset': 'utf8mb4'
}

POSTGRES_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'user': 'video_app',
    'password': 'RmYtmssLzZMXjbbM',
    'database': 'video_app'
}

def get_mysql_tables(mysql_conn):
    """获取所有表名"""
    cursor = mysql_conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables

def get_table_columns(mysql_conn, table_name):
    """获取表的列信息"""
    cursor = mysql_conn.cursor()
    cursor.execute(f"DESCRIBE `{table_name}`")
    columns = []
    for row in cursor.fetchall():
        col_name = row[0]
        col_type = row[1].upper()
        is_nullable = row[2] == 'YES'
        is_primary = row[3] == 'PRI'
        default = row[4]
        extra = row[5]
        columns.append({
            'name': col_name,
            'type': col_type,
            'nullable': is_nullable,
            'primary': is_primary,
            'default': default,
            'extra': extra
        })
    cursor.close()
    return columns

def mysql_to_postgres_type(mysql_type):
    """将 MySQL 类型转换为 PostgreSQL 类型"""
    mysql_type = mysql_type.upper()
    
    if 'INT' in mysql_type:
        if 'BIGINT' in mysql_type:
            return 'BIGINT'
        elif 'TINYINT(1)' in mysql_type:
            return 'BOOLEAN'
        elif 'TINYINT' in mysql_type or 'SMALLINT' in mysql_type:
            return 'SMALLINT'
        else:
            return 'INTEGER'
    elif 'VARCHAR' in mysql_type:
        # 提取长度
        import re
        match = re.search(r'\((\d+)\)', mysql_type)
        if match:
            return f'VARCHAR({match.group(1)})'
        return 'VARCHAR(255)'
    elif 'TEXT' in mysql_type:
        return 'TEXT'
    elif 'DATETIME' in mysql_type or 'TIMESTAMP' in mysql_type:
        return 'TIMESTAMP'
    elif 'DATE' in mysql_type:
        return 'DATE'
    elif 'FLOAT' in mysql_type:
        return 'REAL'
    elif 'DOUBLE' in mysql_type or 'DECIMAL' in mysql_type:
        return 'DOUBLE PRECISION'
    elif 'BLOB' in mysql_type:
        return 'BYTEA'
    elif 'ENUM' in mysql_type:
        return 'VARCHAR(50)'
    elif 'JSON' in mysql_type:
        return 'TEXT'  # PostgreSQL 9.2 doesn't have JSON type
    else:
        return 'TEXT'

def create_postgres_table(pg_conn, table_name, columns):
    """在 PostgreSQL 中创建表"""
    cursor = pg_conn.cursor()
    
    # 删除已存在的表
    cursor.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
    
    # 构建 CREATE TABLE 语句
    col_defs = []
    primary_keys = []
    
    for col in columns:
        pg_type = mysql_to_postgres_type(col['type'])
        
        # 处理自增主键
        if 'AUTO_INCREMENT' in col['extra'].upper():
            pg_type = 'SERIAL'
        
        nullable = '' if col['nullable'] else 'NOT NULL'
        
        if col['primary']:
            primary_keys.append(f'"{col["name"]}"')
        
        if pg_type == 'SERIAL':
            col_defs.append(f'"{col["name"]}" {pg_type}')
        else:
            col_defs.append(f'"{col["name"]}" {pg_type} {nullable}'.strip())
    
    # 添加主键
    if primary_keys:
        col_defs.append(f'PRIMARY KEY ({", ".join(primary_keys)})')
    
    create_sql = f'CREATE TABLE "{table_name}" (\n  ' + ',\n  '.join(col_defs) + '\n)'
    
    try:
        cursor.execute(create_sql)
        pg_conn.commit()
        print(f"  ✅ 创建表: {table_name}")
    except Exception as e:
        pg_conn.rollback()
        print(f"  ❌ 创建表失败 {table_name}: {e}")
        print(f"     SQL: {create_sql[:200]}...")
    
    cursor.close()

def migrate_table_data(mysql_conn, pg_conn, table_name, columns):
    """迁移表数据"""
    mysql_cursor = mysql_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    # 获取数据
    col_names = [f'`{col["name"]}`' for col in columns]
    mysql_cursor.execute(f"SELECT {', '.join(col_names)} FROM `{table_name}`")
    rows = mysql_cursor.fetchall()
    
    if not rows:
        print(f"  ⚪ 表 {table_name} 无数据")
        mysql_cursor.close()
        pg_cursor.close()
        return
    
    # 构建 INSERT 语句
    pg_col_names = [f'"{col["name"]}"' for col in columns]
    
    # 转换数据类型
    converted_rows = []
    for row in rows:
        converted_row = []
        for i, val in enumerate(row):
            col = columns[i]
            pg_type = mysql_to_postgres_type(col['type'])
            
            # 处理布尔值
            if pg_type == 'BOOLEAN':
                if val is None:
                    converted_row.append(None)
                else:
                    converted_row.append(bool(val))
            else:
                converted_row.append(val)
        converted_rows.append(tuple(converted_row))
    
    # 插入数据
    try:
        placeholders = ', '.join(['%s'] * len(columns))
        insert_sql = f'INSERT INTO "{table_name}" ({", ".join(pg_col_names)}) VALUES ({placeholders})'
        
        pg_cursor.executemany(insert_sql, converted_rows)
        pg_conn.commit()
        print(f"  ✅ 迁移数据: {table_name} ({len(rows)} 条)")
    except Exception as e:
        pg_conn.rollback()
        print(f"  ❌ 迁移数据失败 {table_name}: {e}")
    
    mysql_cursor.close()
    pg_cursor.close()

def reset_sequences(pg_conn, table_name, columns):
    """重置序列值"""
    cursor = pg_conn.cursor()
    
    for col in columns:
        if 'AUTO_INCREMENT' in col.get('extra', '').upper():
            seq_name = f"{table_name}_{col['name']}_seq"
            try:
                cursor.execute(f'''
                    SELECT setval('"{seq_name}"', COALESCE((SELECT MAX("{col['name']}") FROM "{table_name}"), 1))
                ''')
                pg_conn.commit()
            except:
                pg_conn.rollback()
    
    cursor.close()

def main():
    print("=" * 50)
    print("MySQL → PostgreSQL 数据迁移")
    print("=" * 50)
    print()
    
    # 连接 MySQL
    print("1. 连接 MySQL...")
    try:
        mysql_conn = pymysql.connect(**MYSQL_CONFIG)
        print("   ✅ MySQL 连接成功")
    except Exception as e:
        print(f"   ❌ MySQL 连接失败: {e}")
        return
    
    # 连接 PostgreSQL
    print("2. 连接 PostgreSQL...")
    try:
        pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
        print("   ✅ PostgreSQL 连接成功")
    except Exception as e:
        print(f"   ❌ PostgreSQL 连接失败: {e}")
        mysql_conn.close()
        return
    
    # 获取所有表
    print("3. 获取表列表...")
    tables = get_mysql_tables(mysql_conn)
    print(f"   找到 {len(tables)} 个表")
    
    # 迁移每个表
    print("\n4. 创建表结构...")
    for table in tables:
        columns = get_table_columns(mysql_conn, table)
        create_postgres_table(pg_conn, table, columns)
    
    # 迁移数据
    print("\n5. 迁移数据...")
    for table in tables:
        columns = get_table_columns(mysql_conn, table)
        migrate_table_data(mysql_conn, pg_conn, table, columns)
        reset_sequences(pg_conn, table, columns)
    
    # 关闭连接
    mysql_conn.close()
    pg_conn.close()
    
    print("\n" + "=" * 50)
    print("✅ 迁移完成!")
    print("=" * 50)

if __name__ == '__main__':
    main()

