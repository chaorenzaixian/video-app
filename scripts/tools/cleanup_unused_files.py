"""
清理服务器上数据库中不存在的孤立文件
- HLS视频目录
- 缩略图
- 预览视频
- 短视频

使用方法:
1. 先运行 --dry-run 模式查看将要删除的文件
2. 确认无误后运行 --delete 模式执行删除
"""
import os
import sys
import shutil
import asyncio
import argparse
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '/www/wwwroot/video-app/backend')

from sqlalchemy import select, text
from app.core.database import AsyncSessionLocal
from app.models.video import Video

# 配置
UPLOAD_DIR = "/www/wwwroot/video-app/backend/uploads"

# 需要检查的目录
DIRS_TO_CHECK = {
    "hls": {
        "path": os.path.join(UPLOAD_DIR, "hls"),
        "type": "directory",  # 每个视频是一个目录
        "db_field": "hls_url",
        "url_pattern": "/uploads/hls/"
    },
    "thumbnails": {
        "path": os.path.join(UPLOAD_DIR, "thumbnails"),
        "type": "file",
        "db_field": "cover_url",
        "url_pattern": "/uploads/thumbnails/"
    },
    "previews": {
        "path": os.path.join(UPLOAD_DIR, "previews"),
        "type": "file",
        "db_field": "preview_url",
        "url_pattern": "/uploads/previews/"
    },
    "shorts": {
        "path": os.path.join(UPLOAD_DIR, "shorts"),
        "type": "file",
        "db_field": "hls_url",
        "url_pattern": "/uploads/shorts/"
    }
}


async def get_db_video_files():
    """从数据库获取所有视频相关的文件路径"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Video.id, Video.hls_url, Video.cover_url, Video.preview_url)
        )
        videos = result.fetchall()
        
        db_files = {
            "hls_dirs": set(),      # HLS目录名
            "thumbnails": set(),    # 缩略图文件名
            "previews": set(),      # 预览视频文件名
            "shorts": set()         # 短视频文件名
        }
        
        for video in videos:
            video_id, hls_url, cover_url, preview_url = video
            
            # HLS目录
            if hls_url and "/hls/" in hls_url:
                # /uploads/hls/video_name/master.m3u8 -> video_name
                parts = hls_url.split("/")
                if len(parts) >= 4:
                    dir_name = parts[-2]
                    db_files["hls_dirs"].add(dir_name)
            
            # 短视频
            if hls_url and "/shorts/" in hls_url:
                filename = os.path.basename(hls_url)
                db_files["shorts"].add(filename)
            
            # 缩略图
            if cover_url and "/thumbnails/" in cover_url:
                filename = os.path.basename(cover_url)
                db_files["thumbnails"].add(filename)
            
            # 预览视频
            if preview_url and "/previews/" in preview_url:
                filename = os.path.basename(preview_url)
                db_files["previews"].add(filename)
        
        return db_files, len(videos)


def get_disk_files(dir_path, file_type):
    """获取磁盘上的文件/目录列表"""
    if not os.path.exists(dir_path):
        return set()
    
    items = set()
    for item in os.listdir(dir_path):
        item_path = os.path.join(dir_path, item)
        if file_type == "directory" and os.path.isdir(item_path):
            items.add(item)
        elif file_type == "file" and os.path.isfile(item_path):
            items.add(item)
    
    return items


def get_dir_size(path):
    """获取目录大小"""
    total = 0
    if os.path.isfile(path):
        return os.path.getsize(path)
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total += os.path.getsize(fp)
    return total


def format_size(size):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


async def main():
    parser = argparse.ArgumentParser(description='清理数据库中不存在的孤立文件')
    parser.add_argument('--dry-run', action='store_true', help='只显示将要删除的文件，不实际删除')
    parser.add_argument('--delete', action='store_true', help='执行删除操作')
    args = parser.parse_args()
    
    if not args.dry_run and not args.delete:
        print("请指定 --dry-run 或 --delete 参数")
        print("  --dry-run: 只显示将要删除的文件")
        print("  --delete: 执行删除操作")
        return
    
    print("=" * 60)
    print(f"孤立文件清理工具 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 获取数据库中的文件
    print("\n[1] 从数据库获取视频文件信息...")
    db_files, video_count = await get_db_video_files()
    print(f"    数据库中共有 {video_count} 个视频记录")
    print(f"    - HLS目录: {len(db_files['hls_dirs'])} 个")
    print(f"    - 缩略图: {len(db_files['thumbnails'])} 个")
    print(f"    - 预览视频: {len(db_files['previews'])} 个")
    print(f"    - 短视频: {len(db_files['shorts'])} 个")
    
    # 检查各目录
    orphan_files = {
        "hls": [],
        "thumbnails": [],
        "previews": [],
        "shorts": []
    }
    
    total_size = 0
    
    print("\n[2] 扫描磁盘文件...")
    
    # HLS目录
    hls_path = DIRS_TO_CHECK["hls"]["path"]
    if os.path.exists(hls_path):
        disk_hls = get_disk_files(hls_path, "directory")
        orphan_hls = disk_hls - db_files["hls_dirs"]
        for item in orphan_hls:
            item_path = os.path.join(hls_path, item)
            size = get_dir_size(item_path)
            orphan_files["hls"].append((item, item_path, size))
            total_size += size
        print(f"    HLS目录: 磁盘 {len(disk_hls)} 个, 孤立 {len(orphan_hls)} 个")
    
    # 缩略图
    thumb_path = DIRS_TO_CHECK["thumbnails"]["path"]
    if os.path.exists(thumb_path):
        disk_thumbs = get_disk_files(thumb_path, "file")
        orphan_thumbs = disk_thumbs - db_files["thumbnails"]
        for item in orphan_thumbs:
            item_path = os.path.join(thumb_path, item)
            size = get_dir_size(item_path)
            orphan_files["thumbnails"].append((item, item_path, size))
            total_size += size
        print(f"    缩略图: 磁盘 {len(disk_thumbs)} 个, 孤立 {len(orphan_thumbs)} 个")
    
    # 预览视频
    preview_path = DIRS_TO_CHECK["previews"]["path"]
    if os.path.exists(preview_path):
        disk_previews = get_disk_files(preview_path, "file")
        orphan_previews = disk_previews - db_files["previews"]
        for item in orphan_previews:
            item_path = os.path.join(preview_path, item)
            size = get_dir_size(item_path)
            orphan_files["previews"].append((item, item_path, size))
            total_size += size
        print(f"    预览视频: 磁盘 {len(disk_previews)} 个, 孤立 {len(orphan_previews)} 个")
    
    # 短视频
    shorts_path = DIRS_TO_CHECK["shorts"]["path"]
    if os.path.exists(shorts_path):
        disk_shorts = get_disk_files(shorts_path, "file")
        orphan_shorts = disk_shorts - db_files["shorts"]
        for item in orphan_shorts:
            item_path = os.path.join(shorts_path, item)
            size = get_dir_size(item_path)
            orphan_files["shorts"].append((item, item_path, size))
            total_size += size
        print(f"    短视频: 磁盘 {len(disk_shorts)} 个, 孤立 {len(orphan_shorts)} 个")
    
    # 统计
    total_orphan = sum(len(v) for v in orphan_files.values())
    print(f"\n[3] 统计结果:")
    print(f"    孤立文件总数: {total_orphan}")
    print(f"    占用空间: {format_size(total_size)}")
    
    if total_orphan == 0:
        print("\n✓ 没有发现孤立文件，无需清理")
        return
    
    # 显示详细列表
    print("\n[4] 孤立文件列表:")
    
    if orphan_files["hls"]:
        print(f"\n  HLS目录 ({len(orphan_files['hls'])} 个):")
        for name, path, size in sorted(orphan_files["hls"])[:20]:
            print(f"    - {name}/ ({format_size(size)})")
        if len(orphan_files["hls"]) > 20:
            print(f"    ... 还有 {len(orphan_files['hls']) - 20} 个")
    
    if orphan_files["thumbnails"]:
        print(f"\n  缩略图 ({len(orphan_files['thumbnails'])} 个):")
        for name, path, size in sorted(orphan_files["thumbnails"])[:20]:
            print(f"    - {name} ({format_size(size)})")
        if len(orphan_files["thumbnails"]) > 20:
            print(f"    ... 还有 {len(orphan_files['thumbnails']) - 20} 个")
    
    if orphan_files["previews"]:
        print(f"\n  预览视频 ({len(orphan_files['previews'])} 个):")
        for name, path, size in sorted(orphan_files["previews"])[:20]:
            print(f"    - {name} ({format_size(size)})")
        if len(orphan_files["previews"]) > 20:
            print(f"    ... 还有 {len(orphan_files['previews']) - 20} 个")
    
    if orphan_files["shorts"]:
        print(f"\n  短视频 ({len(orphan_files['shorts'])} 个):")
        for name, path, size in sorted(orphan_files["shorts"])[:20]:
            print(f"    - {name} ({format_size(size)})")
        if len(orphan_files["shorts"]) > 20:
            print(f"    ... 还有 {len(orphan_files['shorts']) - 20} 个")
    
    # 执行删除
    if args.delete:
        print("\n[5] 执行删除...")
        deleted_count = 0
        deleted_size = 0
        errors = []
        
        for category, items in orphan_files.items():
            for name, path, size in items:
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                    deleted_count += 1
                    deleted_size += size
                except Exception as e:
                    errors.append(f"{path}: {e}")
        
        print(f"\n✓ 删除完成!")
        print(f"  - 删除文件/目录: {deleted_count} 个")
        print(f"  - 释放空间: {format_size(deleted_size)}")
        
        if errors:
            print(f"\n⚠ 删除失败 ({len(errors)} 个):")
            for err in errors[:10]:
                print(f"  - {err}")
    else:
        print("\n[提示] 这是 dry-run 模式，未执行实际删除")
        print("       确认无误后，使用 --delete 参数执行删除")


if __name__ == "__main__":
    asyncio.run(main())
