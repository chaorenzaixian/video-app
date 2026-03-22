"""
Cleanup orphan files on server that don't exist in database
"""
import os
import sys
import shutil
import asyncio
import argparse
from datetime import datetime

sys.path.insert(0, '/www/wwwroot/video-app/backend')

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.video import Video

UPLOAD_DIR = "/www/wwwroot/video-app/backend/uploads"

async def get_db_video_files():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Video.id, Video.hls_url, Video.cover_url, Video.preview_url)
        )
        videos = result.fetchall()
        
        db_files = {
            "hls_dirs": set(),
            "thumbnails": set(),
            "previews": set(),
            "shorts": set()
        }
        
        for video in videos:
            video_id, hls_url, cover_url, preview_url = video
            
            if hls_url and "/hls/" in hls_url:
                parts = hls_url.split("/")
                if len(parts) >= 4:
                    dir_name = parts[-2]
                    db_files["hls_dirs"].add(dir_name)
            
            if hls_url and "/shorts/" in hls_url:
                filename = os.path.basename(hls_url)
                db_files["shorts"].add(filename)
            
            if cover_url and "/thumbnails/" in cover_url:
                filename = os.path.basename(cover_url)
                db_files["thumbnails"].add(filename)
            
            if preview_url and "/previews/" in preview_url:
                filename = os.path.basename(preview_url)
                db_files["previews"].add(filename)
        
        return db_files, len(videos)

def get_disk_files(dir_path, file_type):
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
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--delete', action='store_true')
    args = parser.parse_args()
    
    if not args.dry_run and not args.delete:
        print("Use --dry-run or --delete")
        return
    
    print("=" * 60)
    print(f"Orphan File Cleanup - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    print("\n[1] Getting DB video files...")
    db_files, video_count = await get_db_video_files()
    print(f"    DB has {video_count} videos")
    print(f"    - HLS dirs: {len(db_files['hls_dirs'])}")
    print(f"    - Thumbnails: {len(db_files['thumbnails'])}")
    print(f"    - Previews: {len(db_files['previews'])}")
    print(f"    - Shorts: {len(db_files['shorts'])}")
    
    orphan_files = {"hls": [], "thumbnails": [], "previews": [], "shorts": []}
    total_size = 0
    
    print("\n[2] Scanning disk files...")
    
    hls_path = os.path.join(UPLOAD_DIR, "hls")
    if os.path.exists(hls_path):
        disk_hls = get_disk_files(hls_path, "directory")
        orphan_hls = disk_hls - db_files["hls_dirs"]
        for item in orphan_hls:
            item_path = os.path.join(hls_path, item)
            size = get_dir_size(item_path)
            orphan_files["hls"].append((item, item_path, size))
            total_size += size
        print(f"    HLS: disk {len(disk_hls)}, orphan {len(orphan_hls)}")
    
    thumb_path = os.path.join(UPLOAD_DIR, "thumbnails")
    if os.path.exists(thumb_path):
        disk_thumbs = get_disk_files(thumb_path, "file")
        orphan_thumbs = disk_thumbs - db_files["thumbnails"]
        for item in orphan_thumbs:
            item_path = os.path.join(thumb_path, item)
            size = get_dir_size(item_path)
            orphan_files["thumbnails"].append((item, item_path, size))
            total_size += size
        print(f"    Thumbnails: disk {len(disk_thumbs)}, orphan {len(orphan_thumbs)}")
    
    preview_path = os.path.join(UPLOAD_DIR, "previews")
    if os.path.exists(preview_path):
        disk_previews = get_disk_files(preview_path, "file")
        orphan_previews = disk_previews - db_files["previews"]
        for item in orphan_previews:
            item_path = os.path.join(preview_path, item)
            size = get_dir_size(item_path)
            orphan_files["previews"].append((item, item_path, size))
            total_size += size
        print(f"    Previews: disk {len(disk_previews)}, orphan {len(orphan_previews)}")
    
    shorts_path = os.path.join(UPLOAD_DIR, "shorts")
    if os.path.exists(shorts_path):
        disk_shorts = get_disk_files(shorts_path, "file")
        orphan_shorts = disk_shorts - db_files["shorts"]
        for item in orphan_shorts:
            item_path = os.path.join(shorts_path, item)
            size = get_dir_size(item_path)
            orphan_files["shorts"].append((item, item_path, size))
            total_size += size
        print(f"    Shorts: disk {len(disk_shorts)}, orphan {len(orphan_shorts)}")
    
    total_orphan = sum(len(v) for v in orphan_files.values())
    print(f"\n[3] Summary:")
    print(f"    Total orphan: {total_orphan}")
    print(f"    Total size: {format_size(total_size)}")
    
    if total_orphan == 0:
        print("\nNo orphan files found!")
        return
    
    print("\n[4] Orphan file list:")
    
    if orphan_files["hls"]:
        print(f"\n  HLS dirs ({len(orphan_files['hls'])}):")
        for name, path, size in sorted(orphan_files["hls"])[:30]:
            print(f"    - {name}/ ({format_size(size)})")
        if len(orphan_files["hls"]) > 30:
            print(f"    ... and {len(orphan_files['hls']) - 30} more")
    
    if orphan_files["thumbnails"]:
        print(f"\n  Thumbnails ({len(orphan_files['thumbnails'])}):")
        for name, path, size in sorted(orphan_files["thumbnails"])[:30]:
            print(f"    - {name} ({format_size(size)})")
        if len(orphan_files["thumbnails"]) > 30:
            print(f"    ... and {len(orphan_files['thumbnails']) - 30} more")
    
    if orphan_files["previews"]:
        print(f"\n  Previews ({len(orphan_files['previews'])}):")
        for name, path, size in sorted(orphan_files["previews"])[:30]:
            print(f"    - {name} ({format_size(size)})")
        if len(orphan_files["previews"]) > 30:
            print(f"    ... and {len(orphan_files['previews']) - 30} more")
    
    if orphan_files["shorts"]:
        print(f"\n  Shorts ({len(orphan_files['shorts'])}):")
        for name, path, size in sorted(orphan_files["shorts"])[:30]:
            print(f"    - {name} ({format_size(size)})")
        if len(orphan_files["shorts"]) > 30:
            print(f"    ... and {len(orphan_files['shorts']) - 30} more")
    
    if args.delete:
        print("\n[5] Deleting...")
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
        
        print(f"\nDone!")
        print(f"  - Deleted: {deleted_count}")
        print(f"  - Freed: {format_size(deleted_size)}")
        
        if errors:
            print(f"\nErrors ({len(errors)}):")
            for err in errors[:10]:
                print(f"  - {err}")
    else:
        print("\n[Note] This is dry-run mode. Use --delete to actually delete.")

if __name__ == "__main__":
    asyncio.run(main())