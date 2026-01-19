import base64
from PIL import Image
import io

# 读取 webp 图片
img = Image.open(r'C:\Users\garry\Downloads\ic_launcher-Photoroom.webp')

# 转换为 PNG 并调整大小为 180x180 (iOS 推荐的 WebClip 图标尺寸)
img = img.convert('RGBA')
img = img.resize((180, 180), Image.LANCZOS)

# 保存为 PNG 到内存
png_buffer = io.BytesIO()
img.save(png_buffer, format='PNG')
png_data = png_buffer.getvalue()

# 转换为 base64
b64_data = base64.b64encode(png_data).decode('utf-8')

# 生成 mobileconfig 文件
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
            <data>{b64_data}</data>
            <key>IgnoreManifestScope</key>
            <true/>
            <key>IsRemovable</key>
            <true/>
            <key>Label</key>
            <string>Soul</string>
            <key>PayloadDescription</key>
            <string>添加Soul快捷方式到主屏幕</string>
            <key>PayloadDisplayName</key>
            <string>Soul WebClip</string>
            <key>PayloadIdentifier</key>
            <string>cc.ssoul.webclip</string>
            <key>PayloadType</key>
            <string>com.apple.webClip.managed</string>
            <key>PayloadUUID</key>
            <string>a1b2c3d4-e5f6-4890-abcd-ef1234567890</string>
            <key>PayloadVersion</key>
            <integer>1</integer>
            <key>Precomposed</key>
            <true/>
            <key>URL</key>
            <string>http://38.47.218.137/#/user</string>
        </dict>
    </array>
    <key>PayloadDescription</key>
    <string>安装Soul到您的主屏幕</string>
    <key>PayloadDisplayName</key>
    <string>Soul</string>
    <key>PayloadIdentifier</key>
    <string>cc.ssoul.profile</string>
    <key>PayloadOrganization</key>
    <string>Soul</string>
    <key>PayloadRemovalDisallowed</key>
    <false/>
    <key>PayloadType</key>
    <string>Configuration</string>
    <key>PayloadUUID</key>
    <string>b2c3d4e5-f678-4012-bcde-f12345678901</string>
    <key>PayloadVersion</key>
    <integer>1</integer>
</dict>
</plist>
'''

# 保存文件
with open('packages/Soul.mobileconfig', 'w', encoding='utf-8') as f:
    f.write(mobileconfig)

print('mobileconfig 文件已生成，包含图标')
