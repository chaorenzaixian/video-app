import base64
import os
from PIL import Image
import io

# 读取图标并转换为 PNG
icon_path = r'C:\Users\garry\OneDrive\Desktop\img2\ic_launcher.webp'
img = Image.open(icon_path)
# 调整为 180x180 (iOS 推荐尺寸)
img = img.resize((180, 180), Image.Resampling.LANCZOS)
# 转换为 PNG
png_buffer = io.BytesIO()
img.save(png_buffer, format='PNG')
icon_data = png_buffer.getvalue()
icon_b64 = base64.b64encode(icon_data).decode('utf-8')
print(f'Icon PNG base64 length: {len(icon_b64)}')

# 读取开屏图
splash_path = r'C:\Users\garry\OneDrive\Desktop\img2\ic_splash_bg.webp'
with open(splash_path, 'rb') as f:
    splash_data = f.read()
splash_b64 = base64.b64encode(splash_data).decode('utf-8')
print(f'Splash base64 length: {len(splash_b64)}')

# 创建开屏页面
splash_html = f'''<!DOCTYPE html>
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
        function goHome() {{ clearInterval(timer); window.location.href = 'https://ssoul.cc/#/user'; }}
    </script>
</body>
</html>'''

with open(r'C:\Users\garry\OneDrive\Desktop\video-app\packages\splash.html', 'w', encoding='utf-8') as f:
    f.write(splash_html)
print('splash.html created')

# 创建 app.html - 直接跳转页面
app_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Soul">
    <title>Soul</title>
    <style>
        * {{ margin: 0; padding: 0; }}
        html, body {{ width: 100%; height: 100%; background: #0d0d1a; }}
        .loading {{ position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: #fff; }}
        .spinner {{ width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.2); border-top-color: #6366f1; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 15px; }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    </style>
</head>
<body>
    <div class="loading">
        <div class="spinner"></div>
        <p>加载中...</p>
    </div>
    <script>
        // 立即跳转到首页
        window.location.replace('/#/user');
    </script>
</body>
</html>'''

with open(r'C:\Users\garry\OneDrive\Desktop\video-app\packages\app.html', 'w', encoding='utf-8') as f:
    f.write(app_html)
print('app.html created')

# 创建 mobileconfig
mobileconfig = f'''<?xml version="1.0" encoding="UTF-8"?>
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
            <string>https://ssoul.cc/#/user</string>
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

with open(r'C:\Users\garry\OneDrive\Desktop\video-app\packages\Soul.mobileconfig', 'w', encoding='utf-8') as f:
    f.write(mobileconfig)
print('Soul.mobileconfig created')
print('Done!')




from PIL import Image
import io

# 读取图标并转换为 PNG
icon_path = r'C:\Users\garry\OneDrive\Desktop\img2\ic_launcher.webp'
img = Image.open(icon_path)
# 调整为 180x180 (iOS 推荐尺寸)
img = img.resize((180, 180), Image.Resampling.LANCZOS)
# 转换为 PNG
png_buffer = io.BytesIO()
img.save(png_buffer, format='PNG')
icon_data = png_buffer.getvalue()
icon_b64 = base64.b64encode(icon_data).decode('utf-8')
print(f'Icon PNG base64 length: {len(icon_b64)}')

# 读取开屏图
splash_path = r'C:\Users\garry\OneDrive\Desktop\img2\ic_splash_bg.webp'
with open(splash_path, 'rb') as f:
    splash_data = f.read()
splash_b64 = base64.b64encode(splash_data).decode('utf-8')
print(f'Splash base64 length: {len(splash_b64)}')

# 创建开屏页面
splash_html = f'''<!DOCTYPE html>
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
        function goHome() {{ clearInterval(timer); window.location.href = 'https://ssoul.cc/#/user'; }}
    </script>
</body>
</html>'''

with open(r'C:\Users\garry\OneDrive\Desktop\video-app\packages\splash.html', 'w', encoding='utf-8') as f:
    f.write(splash_html)
print('splash.html created')

# 创建 app.html - 直接跳转页面
app_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Soul">
    <title>Soul</title>
    <style>
        * {{ margin: 0; padding: 0; }}
        html, body {{ width: 100%; height: 100%; background: #0d0d1a; }}
        .loading {{ position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: #fff; }}
        .spinner {{ width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.2); border-top-color: #6366f1; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 15px; }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    </style>
</head>
<body>
    <div class="loading">
        <div class="spinner"></div>
        <p>加载中...</p>
    </div>
    <script>
        // 立即跳转到首页
        window.location.replace('/#/user');
    </script>
</body>
</html>'''

with open(r'C:\Users\garry\OneDrive\Desktop\video-app\packages\app.html', 'w', encoding='utf-8') as f:
    f.write(app_html)
print('app.html created')

# 创建 mobileconfig
mobileconfig = f'''<?xml version="1.0" encoding="UTF-8"?>
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
            <string>https://ssoul.cc/#/user</string>
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

with open(r'C:\Users\garry\OneDrive\Desktop\video-app\packages\Soul.mobileconfig', 'w', encoding='utf-8') as f:
    f.write(mobileconfig)
print('Soul.mobileconfig created')
print('Done!')
