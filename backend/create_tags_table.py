"""创建缺失的 video_tag 表"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'app.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查表是否存在
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='video_tag'")
if cursor.fetchone():
    print("video_tag 表已存在")
else:
    print("创建 video_tag 表...")
    cursor.execute('''
        CREATE TABLE video_tag (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(30) UNIQUE NOT NULL,
            use_count INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_tag_name ON video_tag(name)')
    conn.commit()
    print("video_tag 表创建成功!")

# 添加一些默认标签
default_tags = ['国产', '日本', '欧美', '韩国', '动漫', '制服', '学生', '熟女', '网红', '直播']
for tag in default_tags:
    try:
        cursor.execute("INSERT INTO video_tag (name, use_count) VALUES (?, 0)", (tag,))
    except sqlite3.IntegrityError:
        pass  # 已存在

conn.commit()

# 验证
cursor.execute("SELECT * FROM video_tag")
print("\n当前标签:")
for row in cursor.fetchall():
    print(f"  {row}")

conn.close()
print("\n完成!")
