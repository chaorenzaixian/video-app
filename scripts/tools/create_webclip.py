"""
iOS WebClip 配置文件生成工具
用于生成 mobileconfig 和开屏页面
"""
import base64
import os
from PIL import Image
import io

# 配置 - 当前使用IP访问
BASE_URL = 'http://38.47.218.137'
APP_URL = f'{BASE_URL}/#/user'

# 图标路径（相对于项目根目录）
ICON_PATH = 'backend/ic_launcher.webp'
SPLASH_PATH = 'backend/ic_splash_bg.webp'
OUTPUT_DIR = 'packages'


def load_icon(icon_path: str, size: tuple = (180, 180)) -> str:
    """加载并转换图标为Base64 PNG"""
    img = Image.open(icon_path)
    img = img.resize(size, Image.Resampling.LANCZOS)
    png_buffer = io.BytesIO()
    img.save(png_buffer, format='PNG')
    return base64.b64encode(png_buffer.getvalue()).decode('utf-8')


def load_splash(splash_path: str) -> str:
    """加载开屏图为Base64"""
    with open(splash_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def create_splash_html(splash_b64: str) -> str:
    """创建开屏页面HTML"""
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Soul">
    <title>Soul</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{ width: 100%; height: 100%; overflow: hidden; background: #000; }}
        .splash {{ width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; position: relative; }}
        .splash img {{ width: 100%; height: 100%; object-fit: cover; }}
        .skip-btn {{ position: absolute; top: 50px; right: 20px; padding: 8px 16px; background: rgba(0,0,0,0.5); color: #fff; border: 1px solid rgba(255,255,255,0.3); border-radius: 20px; font-size: 14px; cursor: pointer; z-index: 10; }}
    </style>
</head>
<body>
    <div class="splash">
        <img src="data:image/webp;base64,{splash_b64}" alt="Soul">
        <button class="skip-btn" onclick="goHome()">跳过 <span id="countdown">3</span>s</button>
    </div>
    <script>
        let count = 3;
        const countdownEl = document.getElementById('countdown');
        const timer = setInterval(function() {{
            count--;
            countdownEl.textContent = count;
            if (count <= 0) {{ clearInterval(timer); goHome(); }}
        }}, 1000);
        function goHome() {{ clearInterval(timer); window.location.href = '{APP_URL}'; }}
    </script>
</body>
</html>'''


def create_app_html() -> str:
    """创建加载页面HTML"""
    return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Soul">
    <title>Soul</title>
    <style>
        * { margin: 0; padding: 0; }
        html, body { width: 100%; height: 100%; background: #0d0d1a; }
        .loading { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: #fff; }
        .spinner { width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.2); border-top-color: #6366f1; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 15px; }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="loading">
        <div class="spinner"></div>
        <p>加载中...</p>
    </div>
    <script>
        window.location.replace('/#/user');
    </script>
</body>
</html>'''


def create_mobileconfig(icon_b64: str) -> str:
    """创建iOS描述文件"""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>PayloadContent</key>
    <array>
        <dict>
            <key>FullScreen</key>
            <true/>
            <key>Icon</key>
            <data>{icon_b64}</data>
            <key>IsRemovable</key>
            <true/>
            <key>Label</key>
            <string>Soul</string>
            <key>PayloadDescription</key>
            <string>Soul App</string>
            <key>PayloadDisplayName</key>
            <string>Soul</string>
            <key>PayloadIdentifier</key>
            <string>com.ssoul.webclip</string>
            <key>PayloadType</key>
            <string>com.apple.webClip.managed</string>
            <key>PayloadUUID</key>
            <string>A1B2C3D4-E5F6-7890-ABCD-EF1234567890</string>
            <key>PayloadVersion</key>
            <integer>1</integer>
            <key>Precomposed</key>
            <true/>
            <key>URL</key>
            <string>{APP_URL}</string>
        </dict>
    </array>
    <key>PayloadDescription</key>
    <string>Install Soul App</string>
    <key>PayloadDisplayName</key>
    <string>Soul</string>
    <key>PayloadIdentifier</key>
    <string>com.ssoul.profile</string>
    <key>PayloadOrganization</key>
    <string>Soul</string>
    <key>PayloadRemovalDisallowed</key>
    <false/>
    <key>PayloadType</key>
    <string>Configuration</string>
    <key>PayloadUUID</key>
    <string>B2C3D4E5-F678-9012-BCDE-F12345678901</string>
    <key>PayloadVersion</key>
    <integer>1</integer>
</dict>
</plist>'''


def main():
    """主函数"""
    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 加载资源
    print('Loading icon...')
    icon_b64 = load_icon(ICON_PATH)
    print(f'Icon base64 length: {len(icon_b64)}')
    
    print('Loading splash...')
    splash_b64 = load_splash(SPLASH_PATH)
    print(f'Splash base64 length: {len(splash_b64)}')
    
    # 生成文件
    print('Creating splash.html...')
    with open(os.path.join(OUTPUT_DIR, 'splash.html'), 'w', encoding='utf-8') as f:
        f.write(create_splash_html(splash_b64))
    
    print('Creating app.html...')
    with open(os.path.join(OUTPUT_DIR, 'app.html'), 'w', encoding='utf-8') as f:
        f.write(create_app_html())
    
    print('Creating Soul.mobileconfig...')
    with open(os.path.join(OUTPUT_DIR, 'Soul.mobileconfig'), 'w', encoding='utf-8') as f:
        f.write(create_mobileconfig(icon_b64))
    
    print('Done!')


if __name__ == '__main__':
    main()
