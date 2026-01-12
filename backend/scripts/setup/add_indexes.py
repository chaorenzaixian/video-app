#!/usr/bin/env python3
"""添加数据库索引优化查询性能"""
import sqlite3
import os

def add_indexes():
    db_path = 'app.db'
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    indexes = [
        # Post 表索引
        ("idx_post_visibility_created", "posts", "visibility, created_at"),
        ("idx_post_is_hot_created", "posts", "is_hot, created_at"),
        ("idx_post_like_count", "posts", "like_count"),
        ("idx_post_view_count", "posts", "view_count"),
        ("idx_post_is_top_created", "posts", "is_top, created_at"),
        
        # PostComment 表索引
        ("idx_comment_post_created", "post_comments", "post_id, created_at"),
        ("idx_comment_user_created", "post_comments", "user_id, created_at"),
        ("idx_comment_parent_id", "post_comments", "parent_id"),
        ("idx_comment_status", "post_comments", "status"),
        
        # Video 表索引
        ("idx_video_category_created", "videos", "category_id, created_at"),
        ("idx_video_status_created", "videos", "status, created_at"),
        ("idx_video_view_count", "videos", "view_count"),
        ("idx_video_like_count", "videos", "like_count"),
        
        # UserFollow 表索引
        ("idx_follow_follower_created", "user_follows", "follower_id, created_at"),
        ("idx_follow_following_created", "user_follows", "following_id, created_at"),
    ]
    
    created = 0
    skipped = 0
    
    for idx_name, table, columns in indexes:
        try:
            # 检查索引是否已存在
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND name='{idx_name}'")
            if cursor.fetchone():
                print(f"⏭️ 索引已存在: {idx_name}")
                skipped += 1
                continue
            
            # 检查表是否存在
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                print(f"⚠️ 表不存在: {table}")
                skipped += 1
                continue
            
            # 创建索引
            sql = f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({columns})"
            cursor.execute(sql)
            print(f"✅ 创建索引: {idx_name} ON {table}({columns})")
            created += 1
        except Exception as e:
            print(f"❌ 创建索引失败 {idx_name}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n完成: 创建 {created} 个索引, 跳过 {skipped} 个")

if __name__ == "__main__":
    add_indexes()
