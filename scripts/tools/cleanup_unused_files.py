#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cleanup unused upload files
"""
import os
import json
import shutil
from datetime import datetime

# Database connection
DB_HOST = "127.0.0.1"
DB_USER = "video_app"
DB_PASS = "VideoApp2024!"
DB_NAME = "video_app"

UPLOADS_DIR = "/www/wwwroot/video-app/backend/uploads"
BACKUP_DIR = "/www/wwwroot/video-app/backend/uploads_backup"

def get_db_referenced_files():
    """Get all file paths referenced in database"""
    import psycopg2
    
    conn = psycopg2.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    referenced = set()
    
    # Query all fields containing file paths
    queries = [
        "SELECT cover_url FROM videos WHERE cover_url IS NOT NULL AND cover_url != ''",
        "SELECT preview_url FROM videos WHERE preview_url IS NOT NULL AND preview_url != ''",
        "SELECT avatar FROM users WHERE avatar IS NOT NULL AND avatar != ''",
        "SELECT image_url FROM banners WHERE image_url IS NOT NULL AND image_url != ''",
        "SELECT cover FROM novels WHERE cover IS NOT NULL AND cover != ''",
        "SELECT cover FROM galleries WHERE cover IS NOT NULL AND cover != ''",
        "SELECT avatar FROM dating_hosts WHERE avatar IS NOT NULL AND avatar != ''",
        "SELECT profile_url FROM dating_hosts WHERE profile_url IS NOT NULL AND profile_url != ''",
        "SELECT image FROM advertisements WHERE image IS NOT NULL AND image != ''",
        "SELECT image FROM gifts WHERE image IS NOT NULL AND image != ''",
        "SELECT cover FROM posts WHERE cover IS NOT NULL AND cover != ''",
        "SELECT video_url FROM posts WHERE video_url IS NOT NULL AND video_url != ''",
        "SELECT background_image FROM vip_cards WHERE background_image IS NOT NULL AND background_image != ''",
        "SELECT icon FROM vip_privileges WHERE icon IS NOT NULL AND icon != ''",
    ]
    
    for query in queries:
        try:
            cur.execute(query)
            for row in cur.fetchall():
                if row[0]:
                    path = row[0]
                    if path.startswith('/uploads/'):
                        referenced.add(path[9:])  # Remove /uploads/ prefix
        except Exception as e:
            pass  # Silently skip failed queries
    
    # Query JSON field (posts.images)
    try:
        cur.execute("SELECT images FROM posts WHERE images IS NOT NULL")
        for row in cur.fetchall():
            if row[0]:
                try:
                    images = row[0] if isinstance(row[0], list) else json.loads(str(row[0])) if row[0] else []
                    for img in images:
                        if img and isinstance(img, str) and img.startswith('/uploads/'):
                            referenced.add(img[9:])
                except:
                    pass
    except:
        pass
    
    conn.close()
    return referenced

def get_actual_files(directories):
    """Get all files in specified directories"""
    files = {}
    for subdir in directories:
        dir_path = os.path.join(UPLOADS_DIR, subdir)
        if not os.path.exists(dir_path):
            continue
        for root, _, filenames in os.walk(dir_path):
            for filename in filenames:
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, UPLOADS_DIR)
                try:
                    size = os.path.getsize(full_path)
                    files[rel_path] = size
                except:
                    pass
    return files

def format_size(size_bytes):
    """Format file size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"

def main():
    print("=" * 60)
    print("Unused Files Cleanup Tool")
    print("=" * 60)
    print()
    
    # Directories to check (exclude hls and videos)
    check_dirs = ['images', 'thumbnails', 'previews', 'novel', 'gallery', 'dating', 
                  'community', 'comments', 'site', 'vip', 'func']
    
    print("1. Getting database referenced files...")
    referenced = get_db_referenced_files()
    print(f"   Referenced files: {len(referenced)}")
    
    print("\n2. Scanning actual files...")
    actual_files = get_actual_files(check_dirs)
    print(f"   Actual files: {len(actual_files)}")
    
    print("\n3. Analyzing unused files...")
    unused_files = {}
    for rel_path, size in actual_files.items():
        if rel_path not in referenced:
            unused_files[rel_path] = size
    
    # Group by directory
    by_dir = {}
    for rel_path, size in unused_files.items():
        dir_name = rel_path.split('/')[0] if '/' in rel_path else 'root'
        if dir_name not in by_dir:
            by_dir[dir_name] = {'count': 0, 'size': 0, 'files': []}
        by_dir[dir_name]['count'] += 1
        by_dir[dir_name]['size'] += size
        by_dir[dir_name]['files'].append((rel_path, size))
    
    print("\n" + "=" * 60)
    print("UNUSED FILES SUMMARY")
    print("=" * 60)
    
    total_count = 0
    total_size = 0
    
    for dir_name, info in sorted(by_dir.items()):
        print(f"\n[{dir_name}]")
        print(f"  Files: {info['count']}")
        print(f"  Size: {format_size(info['size'])}")
        total_count += info['count']
        total_size += info['size']
        
        # Show top 5 files by size
        print("  Top files:")
        for f, s in sorted(info['files'], key=lambda x: -x[1])[:5]:
            print(f"    - {f} ({format_size(s)})")
        if len(info['files']) > 5:
            print(f"    ... and {len(info['files']) - 5} more files")
    
    print("\n" + "=" * 60)
    print(f"TOTAL: {total_count} unused files")
    print(f"Space to free: {format_size(total_size)}")
    print("=" * 60)
    
    # Save report
    report_file = "/tmp/unused_files_report.json"
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'total_count': total_count,
        'total_size': total_size,
        'total_size_human': format_size(total_size),
        'by_directory': {k: {'count': v['count'], 'size': v['size'], 'size_human': format_size(v['size'])} for k, v in by_dir.items()},
        'files': list(unused_files.keys())
    }
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    print(f"\nReport saved to: {report_file}")
    
    return report_data

if __name__ == "__main__":
    main()
