#!/usr/bin/env python3
import json
import os
import shutil

UPLOADS_DIR = '/www/wwwroot/video-app/backend/uploads'
BACKUP_DIR = '/www/wwwroot/video-app/backend/uploads_unused_backup'

with open('/tmp/unused_files_report.json') as f:
    data = json.load(f)

files = data['files']
print(f'Moving {len(files)} files to backup...')
os.makedirs(BACKUP_DIR, exist_ok=True)

moved = 0
for rel_path in files:
    src = os.path.join(UPLOADS_DIR, rel_path)
    dst = os.path.join(BACKUP_DIR, rel_path)
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        try:
            shutil.move(src, dst)
            moved += 1
        except Exception as e:
            print(f'Failed: {rel_path} - {e}')

print(f'Done! Moved {moved} files')
print(f'Backup location: {BACKUP_DIR}')
print(f'To delete backup: rm -rf {BACKUP_DIR}')
