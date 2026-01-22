"""
打包转码服务文件
"""
import os
import shutil
import zipfile
from datetime import datetime

# 转码服务文件列表
TRANSCODE_FILES = [
    "transcode_service/web_ui.py",
    "transcode_service/config.py",
    "transcode_service/transcoder.py",
    "transcode_service/uploader.py",
    "transcode_service/task_queue.py",
    "transcode_service/requirements.txt",
    "transcode_service/worker.py",
    "transcode_service/service.py",
    "transcode_service/callback.py",
    "transcode_service/templates/index.html",
]

# 部署脚本
DEPLOY_SCRIPTS = [
    "scripts/upload_and_restart.py",
    "scripts/check_publish_status.py",
    "scripts/guardian.ps1",
]

def package():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"transcode_service_package_{timestamp}"
    package_dir = f"packages/{package_name}"
    
    # 创建目录
    os.makedirs(f"{package_dir}/transcode_service/templates", exist_ok=True)
    os.makedirs(f"{package_dir}/scripts", exist_ok=True)
    
    # 复制转码服务文件
    print("打包转码服务文件...")
    for file in TRANSCODE_FILES:
        if os.path.exists(file):
            dest = f"{package_dir}/{file}"
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(file, dest)
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} (不存在)")
    
    # 复制部署脚本
    print("\n打包部署脚本...")
    for file in DEPLOY_SCRIPTS:
        if os.path.exists(file):
            dest = f"{package_dir}/{file}"
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(file, dest)
            print(f"  ✓ {file}")
    
    # 创建README
    readme = """# 转码服务部署包

## 文件说明

### transcode_service/ - 转码服务核心文件
- web_ui.py - Web管理界面和API
- config.py - 配置文件（需要修改服务器信息）
- transcoder.py - 转码核心逻辑
- uploader.py - 文件上传模块
- task_queue.py - 任务队列管理
- requirements.txt - Python依赖
- templates/index.html - Web界面模板

### scripts/ - 部署脚本
- upload_and_restart.py - 上传并重启服务
- check_publish_status.py - 检查发布状态
- guardian.ps1 - 服务守护进程

## 部署步骤

1. 在Windows服务器上创建目录:
   D:\\VideoTranscode\\service\\

2. 复制transcode_service/下所有文件到:
   D:\\VideoTranscode\\service\\

3. 安装Python依赖:
   pip install -r requirements.txt

4. 修改config.py中的服务器配置

5. 启动服务:
   python web_ui.py

6. 访问: http://服务器IP:8080

## 配置说明

修改 config.py 中的以下配置:
- MAIN_SERVER["host"] - 主服务器IP
- MAIN_SERVER["ssh_key"] - SSH密钥路径
- MAIN_SERVER["api_base"] - API地址
- MAIN_SERVER["transcode_key"] - 转码密钥
"""
    
    with open(f"{package_dir}/README.md", "w", encoding="utf-8") as f:
        f.write(readme)
    
    # 创建ZIP
    print(f"\n创建ZIP包...")
    zip_path = f"packages/{package_name}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, package_dir)
                zf.write(file_path, arc_name)
    
    # 清理临时目录
    shutil.rmtree(package_dir)
    
    print(f"\n✓ 打包完成: {zip_path}")
    print(f"  文件大小: {os.path.getsize(zip_path) / 1024:.1f} KB")

if __name__ == "__main__":
    package()
