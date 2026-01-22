"""创建暗网视频相关的数据库表"""
import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# 使用密钥连接
key = paramiko.Ed25519Key.from_private_key_file('server_key_main')
client.connect('38.47.218.137', username='root', pkey=key)

# 创建表的SQL
sql = '''
-- 暗网视频分类表
CREATE TABLE IF NOT EXISTS darkweb_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    icon VARCHAR(200),
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    parent_id INTEGER REFERENCES darkweb_categories(id),
    level INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 暗网视频标签表
CREATE TABLE IF NOT EXISTS darkweb_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(30) UNIQUE NOT NULL,
    use_count INTEGER DEFAULT 0
);

-- 暗网视频表
CREATE TABLE IF NOT EXISTS darkweb_videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    cover_url VARCHAR(500),
    original_url VARCHAR(500),
    hls_url VARCHAR(500),
    preview_url VARCHAR(500),
    duration FLOAT DEFAULT 0,
    file_size INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'UPLOADING',
    quality VARCHAR(20) DEFAULT 'HD',
    is_featured BOOLEAN DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    favorite_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    category_id INTEGER REFERENCES darkweb_categories(id),
    uploader_id INTEGER NOT NULL REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    published_at DATETIME
);

-- 暗网视频-标签关联表
CREATE TABLE IF NOT EXISTS darkweb_video_tags_association (
    video_id INTEGER NOT NULL REFERENCES darkweb_videos(id),
    tag_id INTEGER NOT NULL REFERENCES darkweb_tags(id),
    PRIMARY KEY (video_id, tag_id)
);

-- 暗网视频观看记录表
CREATE TABLE IF NOT EXISTS darkweb_views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL REFERENCES darkweb_videos(id),
    user_id INTEGER REFERENCES users(id),
    ip_address VARCHAR(50),
    watch_duration FLOAT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_darkweb_status_created ON darkweb_videos(status, created_at);
CREATE INDEX IF NOT EXISTS idx_darkweb_category_status ON darkweb_videos(category_id, status);
CREATE INDEX IF NOT EXISTS idx_darkweb_view_video ON darkweb_views(video_id, created_at);
CREATE INDEX IF NOT EXISTS idx_darkweb_view_user ON darkweb_views(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_darkweb_videos_title ON darkweb_videos(title);

-- 插入一些默认分类
INSERT OR IGNORE INTO darkweb_categories (id, name, description, sort_order, level) VALUES 
(1, '热门推荐', '热门暗网视频', 1, 1),
(2, '最新上传', '最新上传的视频', 2, 1),
(3, '精选收藏', '精选优质内容', 3, 1);
'''

# 执行SQL
cmd = f'''sqlite3 /www/wwwroot/video-app/backend/app.db "{sql}"'''
stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')

if out:
    print("Output:", out)
if err:
    print("Error:", err)
else:
    print("Tables created successfully!")

# 验证
cmd2 = '''sqlite3 /www/wwwroot/video-app/backend/app.db ".tables" | grep dark'''
stdin, stdout, stderr = client.exec_command(cmd2, timeout=30)
print("Darkweb tables:", stdout.read().decode('utf-8'))

client.close()
