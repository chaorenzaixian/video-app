import sqlite3
import os

conn = sqlite3.connect('app.db')
cursor = conn.cursor()

print('=== func_entries ===')
cursor.execute('SELECT id, name, image FROM func_entries')
for row in cursor.fetchall():
    image = row[2]
    if image:
        local_path = image.lstrip('/')
        exists = os.path.exists(local_path)
        status = 'OK' if exists else 'MISSING'
        print(f'{row[1]}: {image} [{status}]')

print('\n=== videos (first 5) ===')
cursor.execute('SELECT id, cover_url FROM videos WHERE cover_url IS NOT NULL LIMIT 5')
for row in cursor.fetchall():
    cover = row[1]
    if cover:
        local_path = cover.lstrip('/')
        exists = os.path.exists(local_path)
        status = 'OK' if exists else 'MISSING'
        print(f'Video {row[0]}: {cover} [{status}]')

conn.close()
