"""
iOS 描述文件（mobileconfig）生成API
用于生成Web Clip快捷方式，让用户可以将应用添加到主屏幕
"""
from fastapi import APIRouter, Request, Query
from fastapi.responses import Response
import uuid
import base64
from typing import Optional
from app.core.config import settings

router = APIRouter(prefix="/ios", tags=["iOS Profile"])

# 默认应用图标 (Base64编码的PNG)
DEFAULT_ICON = """iVBORw0KGgoAAAANSUhEUgAAALQAAAC0CAYAAAA9zQYyAAABhGlDQ1BJQ0MgcHJvZmlsZQAAKJF9
kT1Iw0AcxV9TpSIVB4uIOGSoThZERRy1CkWoEGqFVh1MLv2CJg1Jiouj4Fpw8GOx6uDirKuDqyAI
foC4uTkpukiJ/0sKLWI8OO7Hu3uPu3eAUC8zzeoYBzTdNlOJuJjJropdrwhCQB8mEJWZZc5JUhK+
4+seAb7exXmW/7k/R4+asxgQEIlnmWHaxBvE05u2wXmfOMKKsop8Tjxm0gWJH7muePzGueCywDMj
ZjrVIx4hFostLLcwKxoqcTxxWNV0yheyHqucdnLVJjXXz+cvFOb15DK/CqLMK0hwHI1yMuRQ1IQN
GjMoE0/QNlPqwlHOY47zK/lCIZfB3gJJzPWBj2NwhN0/4pvB7G4rBxfNlE0lIHoBLrcI0AWNcvAN
BjrtSNxN18c5d4NODn0LRLX0cNQwhHZfvekv8HAIDJy5dOapr7lzPwP8FJXhHBdwJIWvCn4D394H
wnqavF4YG+cVmfpGy+sAci6T6c9T2wJiH0DfjE3rXTrHuQHw77Qkf5APhoHQXdXpNwZA9w7Qa7Xw
rtiY70xvE7stfwy0wz0gvLQ7C6DAEWxW8c3C6o9E+p58v3X2/hbIOoS+b5oAAAAJcEhZcwAALiMA
AC4jAXilP3YAAABJSURBVHic7cExAQAAAMKg9U9tDB+gAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB4Nha9AAE0rFzaAAAAAElFTkSuQmCC"""

# 应用配置
APP_CONFIG = {
    "name": "Soul",
    "display_name": "Soul",
    "description": "Soul视频App - 精彩内容尽在掌握",
    "organization": "Soul Entertainment",
    "identifier": "cc.ssoul",
    "base_url": "https://ssoul.cc"
}


def generate_uuid() -> str:
    """生成UUID"""
    return str(uuid.uuid4()).upper()


def create_webclip_payload(
    url: str,
    label: str,
    icon_data: str,
    fullscreen: bool = True,
    is_removable: bool = True
) -> str:
    """创建Web Clip配置载荷"""
    return f"""
        <dict>
            <key>FullScreen</key>
            <{str(fullscreen).lower()}/>
            <key>IgnoreManifestScope</key>
            <true/>
            <key>Icon</key>
            <data>{icon_data}</data>
            <key>IsRemovable</key>
            <{str(is_removable).lower()}/>
            <key>Label</key>
            <string>{label}</string>
            <key>PayloadDescription</key>
            <string>{APP_CONFIG['description']}</string>
            <key>PayloadDisplayName</key>
            <string>{label}</string>
            <key>PayloadIdentifier</key>
            <string>{APP_CONFIG['identifier']}.webclip.{label.lower()}</string>
            <key>PayloadType</key>
            <string>com.apple.webClip.managed</string>
            <key>PayloadUUID</key>
            <string>{generate_uuid()}</string>
            <key>PayloadVersion</key>
            <integer>1</integer>
            <key>Precomposed</key>
            <true/>
            <key>URL</key>
            <string>{url}</string>
        </dict>"""


def create_mobileconfig(
    app_name: str,
    app_url: str,
    icon_base64: str,
    description: str = None,
    organization: str = None,
    consent_text: str = None
) -> str:
    """
    生成完整的mobileconfig XML
    
    Args:
        app_name: 应用名称
        app_url: 应用URL
        icon_base64: Base64编码的图标数据
        description: 描述文本
        organization: 组织名称
        consent_text: 安装同意文本
    """
    if description is None:
        description = APP_CONFIG['description']
    if organization is None:
        organization = APP_CONFIG['organization']
    
    profile_uuid = generate_uuid()
    webclip_payload = create_webclip_payload(
        url=app_url,
        label=app_name,
        icon_data=icon_base64,
        fullscreen=True,
        is_removable=True
    )
    
    consent_section = ""
    if consent_text:
        consent_section = f"""
    <key>ConsentText</key>
    <dict>
        <key>default</key>
        <string>{consent_text}</string>
        <key>zh-Hans</key>
        <string>{consent_text}</string>
    </dict>"""
    
    mobileconfig = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>PayloadContent</key>
    <array>
        {webclip_payload}
    </array>{consent_section}
    <key>PayloadDescription</key>
    <string>{description}</string>
    <key>PayloadDisplayName</key>
    <string>{app_name}</string>
    <key>PayloadIdentifier</key>
    <string>{APP_CONFIG['identifier']}.profile</string>
    <key>PayloadOrganization</key>
    <string>{organization}</string>
    <key>PayloadRemovalDisallowed</key>
    <false/>
    <key>PayloadType</key>
    <string>Configuration</string>
    <key>PayloadUUID</key>
    <string>{profile_uuid}</string>
    <key>PayloadVersion</key>
    <integer>1</integer>
</dict>
</plist>"""
    
    return mobileconfig.strip()


@router.get("/profile.mobileconfig")
async def download_mobileconfig(
    request: Request,
    name: Optional[str] = Query(default=None, description="应用名称"),
    url: Optional[str] = Query(default=None, description="应用URL")
):
    """
    下载iOS描述文件
    
    用户访问此链接后，iOS设备会提示安装描述文件
    安装后会在主屏幕添加应用图标
    """
    app_name = name or APP_CONFIG['name']
    app_url = url or f"{APP_CONFIG['base_url']}/#/user"
    
    # 尝试加载自定义图标，否则使用默认图标
    try:
        import os
        icon_path = os.path.join(settings.UPLOAD_DIR, "app_icon.png")
        if os.path.exists(icon_path):
            with open(icon_path, "rb") as f:
                icon_base64 = base64.b64encode(f.read()).decode('utf-8')
        else:
            icon_base64 = DEFAULT_ICON
    except:
        icon_base64 = DEFAULT_ICON
    
    # 生成mobileconfig
    mobileconfig_content = create_mobileconfig(
        app_name=app_name,
        app_url=app_url,
        icon_base64=icon_base64,
        description=f"安装{app_name}到您的主屏幕，享受原生App般的体验",
        consent_text=f"此配置描述文件将在您的设备主屏幕添加{app_name}快捷方式。"
    )
    
    return Response(
        content=mobileconfig_content,
        media_type="application/x-apple-aspen-config",
        headers={
            "Content-Disposition": f'attachment; filename="{app_name}.mobileconfig"',
            "Cache-Control": "no-cache, no-store, must-revalidate"
        }
    )


@router.get("/install")
async def ios_install_page(request: Request):
    """
    iOS安装引导页面（简单HTML）
    实际项目中应该使用前端页面
    """
    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <title>{APP_CONFIG['name']} - iOS安装</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }}
        .container {{ max-width: 400px; margin: 0 auto; padding: 40px 20px; }}
        .logo {{ 
            width: 100px; height: 100px; 
            border-radius: 22px; 
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            margin: 0 auto 30px;
            display: flex; align-items: center; justify-content: center;
            font-size: 40px; font-weight: bold;
            box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
        }}
        h1 {{ text-align: center; font-size: 28px; margin-bottom: 15px; }}
        .subtitle {{ text-align: center; color: rgba(255,255,255,0.7); margin-bottom: 40px; }}
        .install-btn {{
            display: block; width: 100%; padding: 18px;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            border: none; border-radius: 14px;
            color: #fff; font-size: 18px; font-weight: 600;
            text-decoration: none; text-align: center;
            box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .install-btn:active {{ transform: scale(0.98); }}
        .steps {{ margin-top: 50px; }}
        .step {{ 
            display: flex; align-items: flex-start; gap: 15px;
            padding: 15px 0; border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .step-num {{
            width: 32px; height: 32px; border-radius: 50%;
            background: rgba(99, 102, 241, 0.3);
            display: flex; align-items: center; justify-content: center;
            font-weight: bold; flex-shrink: 0;
        }}
        .step-text {{ font-size: 15px; line-height: 1.5; color: rgba(255,255,255,0.9); }}
        .note {{ 
            margin-top: 30px; padding: 15px; 
            background: rgba(255,255,255,0.1); 
            border-radius: 10px; font-size: 13px;
            color: rgba(255,255,255,0.7);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">S</div>
        <h1>{APP_CONFIG['name']}</h1>
        <p class="subtitle">{APP_CONFIG['description']}</p>
        
        <a href="/api/v1/ios/profile.mobileconfig" class="install-btn">
            📲 安装到主屏幕
        </a>
        
        <div class="steps">
            <div class="step">
                <span class="step-num">1</span>
                <span class="step-text">点击上方按钮下载描述文件</span>
            </div>
            <div class="step">
                <span class="step-num">2</span>
                <span class="step-text">打开 <strong>设置</strong> → 顶部会显示"已下载描述文件"</span>
            </div>
            <div class="step">
                <span class="step-num">3</span>
                <span class="step-text">点击 <strong>安装</strong>，按提示完成安装</span>
            </div>
            <div class="step">
                <span class="step-num">4</span>
                <span class="step-text">返回主屏幕，即可看到 {APP_CONFIG['name']} 图标</span>
            </div>
        </div>
        
        <div class="note">
            💡 提示：描述文件仅添加主屏幕快捷方式，不会收集任何个人信息。
            如需卸载，在设置 → 通用 → VPN与设备管理中删除即可。
        </div>
    </div>
</body>
</html>
"""
    return Response(content=html, media_type="text/html")


@router.get("/config")
async def get_ios_config():
    """
    获取iOS配置信息
    前端可用此接口获取配置后自定义展示
    """
    return {
        "app_name": APP_CONFIG['name'],
        "display_name": APP_CONFIG['display_name'],
        "description": APP_CONFIG['description'],
        "organization": APP_CONFIG['organization'],
        "base_url": APP_CONFIG['base_url'],
        "profile_url": f"{APP_CONFIG['base_url']}/api/v1/ios/profile.mobileconfig",
        "install_guide_url": f"{APP_CONFIG['base_url']}/api/v1/ios/install"
    }






