"""
上传 APK 和 mobileconfig 文件到服务器并更新下载页配置
"""
import os
import sys
import requests

# 服务器配置
API_BASE = "http://38.47.218.230:8000/api/v1"
# 需要管理员 token
TOKEN = None

def get_token():
    """获取管理员 token"""
    global TOKEN
    if TOKEN:
        return TOKEN
    
    # 尝试从环境变量获取
    TOKEN = os.environ.get("ADMIN_TOKEN")
    if TOKEN:
        return TOKEN
    
    # 尝试登录获取
    print("请输入管理员账号信息：")
    username = input("用户名: ").strip()
    password = input("密码: ").strip()
    
    try:
        resp = requests.post(f"{API_BASE}/auth/login", json={
            "username": username,
            "password": password
        })
        if resp.status_code == 200:
            data = resp.json()
            TOKEN = data.get("access_token")
            print("登录成功！")
            return TOKEN
        else:
            print(f"登录失败: {resp.text}")
            return None
    except Exception as e:
        print(f"登录错误: {e}")
        return None

def upload_apk(filepath):
    """上传 APK 文件"""
    token = get_token()
    if not token:
        return None
    
    print(f"正在上传 APK: {filepath}")
    file_size = os.path.getsize(filepath)
    print(f"文件大小: {file_size / 1024 / 1024:.2f} MB")
    
    with open(filepath, 'rb') as f:
        files = {'file': ('Soul.apk', f, 'application/vnd.android.package-archive')}
        headers = {'Authorization': f'Bearer {token}'}
        
        resp = requests.post(
            f"{API_BASE}/download-page/admin/upload-apk",
            files=files,
            headers=headers,
            timeout=300  # 5分钟超时
        )
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"APK 上传成功！")
        print(f"  下载地址: {data.get('url')}")
        print(f"  文件大小: {data.get('size_mb')} MB")
        return data
    else:
        print(f"APK 上传失败: {resp.status_code} - {resp.text}")
        return None

def upload_mobileconfig(filepath):
    """上传 mobileconfig 文件"""
    token = get_token()
    if not token:
        return None
    
    print(f"正在上传 mobileconfig: {filepath}")
    
    with open(filepath, 'rb') as f:
        files = {'file': ('Soul.mobileconfig', f, 'application/x-apple-aspen-config')}
        headers = {'Authorization': f'Bearer {token}'}
        
        resp = requests.post(
            f"{API_BASE}/download-page/admin/upload-mobileconfig",
            files=files,
            headers=headers,
            timeout=60
        )
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"Mobileconfig 上传成功！")
        print(f"  下载地址: {data.get('url')}")
        print(f"  文件大小: {data.get('size_kb')} KB")
        return data
    else:
        print(f"Mobileconfig 上传失败: {resp.status_code} - {resp.text}")
        return None

def update_download_config(apk_url=None, mobileconfig_url=None):
    """更新下载页配置"""
    token = get_token()
    if not token:
        return False
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # 先获取当前配置
    resp = requests.get(f"{API_BASE}/download-page/admin/config", headers=headers)
    if resp.status_code != 200:
        print(f"获取配置失败: {resp.text}")
        return False
    
    config = resp.json()
    print("\n当前配置:")
    print(f"  Android 链接数: {len(config.get('android_links', []))}")
    print(f"  iOS mobileconfig: {config.get('ios_links', {}).get('mobileconfig', '未设置')}")
    
    # 构建更新数据
    update_data = {}
    
    if apk_url:
        # 更新或添加 Android 主下载链接
        android_links = config.get('android_links', [])
        found = False
        for link in android_links:
            if link.get('is_primary'):
                link['url'] = apk_url
                found = True
                break
        
        if not found:
            android_links.insert(0, {
                'name': '主下载',
                'url': apk_url,
                'is_primary': True,
                'is_active': True,
                'sort_order': 0
            })
        
        update_data['android_links'] = android_links
    
    if mobileconfig_url:
        ios_links = config.get('ios_links', {})
        ios_links['mobileconfig'] = mobileconfig_url
        ios_links['mobileconfig_active'] = True
        update_data['ios_links'] = ios_links
    
    if not update_data:
        print("没有需要更新的配置")
        return True
    
    # 发送更新请求
    resp = requests.put(
        f"{API_BASE}/download-page/admin/config",
        json=update_data,
        headers=headers
    )
    
    if resp.status_code == 200:
        print("\n下载页配置更新成功！")
        return True
    else:
        print(f"配置更新失败: {resp.status_code} - {resp.text}")
        return False

def main():
    print("=" * 50)
    print("App 文件上传工具")
    print("=" * 50)
    
    # 文件路径
    apk_path = "flutter/build/app/outputs/flutter-apk/app-release.apk"
    mobileconfig_path = "packages/Soul.mobileconfig"
    
    apk_url = None
    mobileconfig_url = None
    
    # 上传 APK
    if os.path.exists(apk_path):
        result = upload_apk(apk_path)
        if result:
            apk_url = result.get('url')
    else:
        print(f"APK 文件不存在: {apk_path}")
    
    print()
    
    # 上传 mobileconfig
    if os.path.exists(mobileconfig_path):
        result = upload_mobileconfig(mobileconfig_path)
        if result:
            mobileconfig_url = result.get('url')
    else:
        print(f"Mobileconfig 文件不存在: {mobileconfig_path}")
    
    print()
    
    # 更新下载页配置
    if apk_url or mobileconfig_url:
        update_download_config(apk_url, mobileconfig_url)
    
    print("\n" + "=" * 50)
    print("完成！")
    print("=" * 50)

if __name__ == "__main__":
    main()
