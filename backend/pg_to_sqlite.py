#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PostgreSQL to SQLite 数据迁移脚本
将 PostgreSQL 导出的 SQL 文件转换并导入到 SQLite
"""
import re
import sqlite3
import os
import sys

# SQL 文件路径
SQL_FILE = "../video_app_full_inserts_20260104_175243.sql"
SQLITE_DB = "app.db"


def convert_pg_to_sqlite(sql_content: str) -> list:
    """
    将 PostgreSQL INSERT 语句转换为 SQLite 兼容格式
    """
    inserts = []
    
    # 提取所有 INSERT 语句
    pattern = r"INSERT INTO public\.(\w+)\s*\(([^)]+)\)\s*VALUES\s*\(([^;]+)\);"
    
    for match in re.finditer(pattern, sql_content, re.IGNORECASE | re.DOTALL):
        table_name = match.group(1)
        columns = match.group(2).strip()
        values = match.group(3).strip()
        
        # 转换 PostgreSQL 特有语法
        # 1. 布尔值: true/false -> 1/0
        values = re.sub(r'\btrue\b', '1', values, flags=re.IGNORECASE)
        values = re.sub(r'\bfalse\b', '0', values, flags=re.IGNORECASE)
        
        # 2. 移除 public. 前缀
        # 3. 处理时间戳格式（SQLite 兼容）
        
        insert_sql = f"INSERT OR IGNORE INTO {table_name} ({columns}) VALUES ({values});"
        inserts.append(insert_sql)
    
    return inserts


def extract_inserts_simple(sql_content: str) -> list:
    """
    简单提取 INSERT 语句并转换
    """
    inserts = []
    lines = sql_content.split('\n')
    current_insert = ""
    in_insert = False
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('INSERT INTO public.'):
            in_insert = True
            current_insert = line
        elif in_insert:
            current_insert += " " + line
        
        if in_insert and line.endswith(';'):
            # 转换语句
            stmt = current_insert
            # 移除 public. 前缀
            stmt = stmt.replace('INSERT INTO public.', 'INSERT OR IGNORE INTO ')
            # 布尔值转换
            stmt = re.sub(r'\btrue\b', '1', stmt, flags=re.IGNORECASE)
            stmt = re.sub(r'\bfalse\b', '0', stmt, flags=re.IGNORECASE)
            
            inserts.append(stmt)
            current_insert = ""
            in_insert = False
    
    return inserts


def main():
    print(f"[*] 读取 SQL 文件: {SQL_FILE}")
    
    if not os.path.exists(SQL_FILE):
        print(f"[ERROR] 文件不存在: {SQL_FILE}")
        sys.exit(1)
    
    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"[*] 文件大小: {len(sql_content) / 1024:.2f} KB")
    
    # 提取 INSERT 语句
    print("[*] 提取并转换 INSERT 语句...")
    inserts = extract_inserts_simple(sql_content)
    print(f"[*] 找到 {len(inserts)} 条 INSERT 语句")
    
    if len(inserts) == 0:
        print("[WARNING] 没有找到 INSERT 语句")
        return
    
    # 备份现有数据库
    if os.path.exists(SQLITE_DB):
        backup_name = SQLITE_DB + ".backup"
        print(f"[*] 备份现有数据库到: {backup_name}")
        import shutil
        shutil.copy(SQLITE_DB, backup_name)
    
    # 连接 SQLite 数据库
    print(f"[*] 连接 SQLite 数据库: {SQLITE_DB}")
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    
    # 执行 INSERT 语句
    success_count = 0
    error_count = 0
    errors = []
    
    print("[*] 开始导入数据...")
    
    for i, stmt in enumerate(inserts):
        try:
            cursor.execute(stmt)
            success_count += 1
        except Exception as e:
            error_count += 1
            if error_count <= 10:  # 只记录前10个错误
                errors.append(f"  - {str(e)[:100]}")
        
        # 进度显示
        if (i + 1) % 100 == 0:
            print(f"  进度: {i + 1}/{len(inserts)}")
    
    conn.commit()
    conn.close()
    
    print(f"\n[完成] 导入结果:")
    print(f"  - 成功: {success_count}")
    print(f"  - 失败: {error_count}")
    
    if errors:
        print(f"\n[错误示例]:")
        for err in errors[:5]:
            print(err)


if __name__ == "__main__":
    main()
