#!/usr/bin/env python3
"""
Telegram 视频下载器
用法:
  python tg_downloader.py login          # 首次登录
  python tg_downloader.py list           # 列出最近的频道/群组
  python tg_downloader.py download <频道> [数量]  # 下载视频
"""
import os
import sys
import asyncio
from pathlib import Path

# 配置
DOWNLOAD_DIR = Path.home() / "video-transcode" / "downloads"
SESSION_FILE = Path.home() / "video-transcode" / "tg_session"

# Telegram API 配置 (从 https://my.telegram.org 获取)
API_ID = os.getenv("TG_API_ID", "")
API_HASH = os.getenv("TG_API_HASH", "")

async def login():
    """登录 Telegram"""
    from telethon import TelegramClient
    
    if not API_ID or not API_HASH:
        print("=" * 50)
        print("首次使用需要配置 Telegram API")
        print("1. 访问 https://my.telegram.org")
        print("2. 登录后点击 'API development tools'")
        print("3. 创建应用，获取 api_id 和 api_hash")
        print("=" * 50)
        
        api_id = input("请输入 API ID: ").strip()
        api_hash = input("请输入 API Hash: ").strip()
        
        # 保存到环境变量文件
        env_file = Path.home() / "video-transcode" / ".tg_env"
        with open(env_file, "w") as f:
            f.write(f"export TG_API_ID={api_id}\n")
            f.write(f"export TG_API_HASH={api_hash}\n")
        print(f"配置已保存到 {env_file}")
        print("请运行: source ~/.video-transcode/.tg_env")
    else:
        api_id = int(API_ID)
        api_hash = API_HASH
    
    client = TelegramClient(str(SESSION_FILE), int(api_id), api_hash)
    await client.start()
    
    me = await client.get_me()
    print(f"登录成功: {me.first_name} (@{me.username})")
    
    await client.disconnect()

async def list_dialogs():
    """列出频道和群组"""
    from telethon import TelegramClient
    
    if not API_ID or not API_HASH:
        print("请先运行: python tg_downloader.py login")
        return
    
    client = TelegramClient(str(SESSION_FILE), int(API_ID), API_HASH)
    await client.start()
    
    print("\n最近的对话:")
    print("-" * 60)
    
    async for dialog in client.iter_dialogs(limit=20):
        entity_type = "频道" if dialog.is_channel else "群组" if dialog.is_group else "私聊"
        print(f"[{entity_type}] {dialog.name} (ID: {dialog.id})")
    
    await client.disconnect()

async def download_videos(channel, limit=10):
    """从频道下载视频"""
    from telethon import TelegramClient
    from telethon.tl.types import MessageMediaDocument
    
    if not API_ID or not API_HASH:
        print("请先运行: python tg_downloader.py login")
        return
    
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    client = TelegramClient(str(SESSION_FILE), int(API_ID), API_HASH)
    await client.start()
    
    print(f"正在从 {channel} 获取视频...")
    
    downloaded = 0
    async for message in client.iter_messages(channel, limit=100):
        if downloaded >= limit:
            break
            
        if message.media and isinstance(message.media, MessageMediaDocument):
            mime = message.media.document.mime_type
            if mime and mime.startswith("video"):
                # 生成文件名
                filename = f"tg_{message.id}_{message.date.strftime('%Y%m%d')}.mp4"
                filepath = DOWNLOAD_DIR / filename
                
                if filepath.exists():
                    print(f"跳过已存在: {filename}")
                    continue
                
                size_mb = message.media.document.size / 1024 / 1024
                print(f"下载中: {filename} ({size_mb:.1f} MB)")
                
                await client.download_media(message, filepath)
                downloaded += 1
                print(f"完成: {filename}")
    
    print(f"\n下载完成，共 {downloaded} 个视频")
    print(f"保存位置: {DOWNLOAD_DIR}")
    
    await client.disconnect()

async def download_by_link(link):
    """通过消息链接下载"""
    from telethon import TelegramClient
    import re
    
    if not API_ID or not API_HASH:
        print("请先运行: python tg_downloader.py login")
        return
    
    # 解析链接 https://t.me/channel/123
    match = re.match(r'https?://t\.me/([^/]+)/(\d+)', link)
    if not match:
        print("无效的链接格式，应为: https://t.me/channel/123")
        return
    
    channel = match.group(1)
    msg_id = int(match.group(2))
    
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    client = TelegramClient(str(SESSION_FILE), int(API_ID), API_HASH)
    await client.start()
    
    print(f"获取消息: {channel}/{msg_id}")
    
    try:
        message = await client.get_messages(channel, ids=msg_id)
        if message and message.media:
            filename = f"tg_{channel}_{msg_id}.mp4"
            filepath = DOWNLOAD_DIR / filename
            
            print(f"下载中: {filename}")
            await client.download_media(message, filepath)
            print(f"完成: {filepath}")
        else:
            print("消息不包含媒体文件")
    except Exception as e:
        print(f"下载失败: {e}")
    
    await client.disconnect()

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1]
    
    if cmd == "login":
        asyncio.run(login())
    elif cmd == "list":
        asyncio.run(list_dialogs())
    elif cmd == "download":
        if len(sys.argv) < 3:
            print("用法: python tg_downloader.py download <频道名/链接> [数量]")
            return
        target = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        
        if target.startswith("http"):
            asyncio.run(download_by_link(target))
        else:
            asyncio.run(download_videos(target, limit))
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
