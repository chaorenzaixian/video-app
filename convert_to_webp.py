"""
批量转换图片为 WebP 格式
- 转换 PNG, JPG, JPEG, GIF 为 WebP
- 自动更新代码中的引用
- 保留原文件备份（可选删除）
"""
import os
import re
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import shutil

# 需要转换的目录
CONVERT_DIRS = [
    "frontend/public/images",
    "flutter/assets/images",
    "flutter/assets/icon",
    "backend/uploads/images",
    "backend/uploads/thumbnails",
    "backend/uploads/site",
    "backend/uploads/community",
    "backend/uploads/gallery",
    "backend/uploads/vip",
    "backend/uploads/comments",
    "backend/uploads/novel",
    "backend/uploads/func",
]

# 需要更新引用的代码目录
CODE_DIRS = [
    "frontend/src",
    "flutter/lib",
]

# 数据库图片路径需要更新（运行后手动执行SQL）
DB_UPDATE_NEEDED = True

# 支持的图片格式
SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.gif'}

# 转换质量 (0-100)
WEBP_QUALITY = 85

# 是否删除原文件
DELETE_ORIGINAL = True

# 统计
stats = {
    'converted': 0,
    'skipped': 0,
    'failed': 0,
    'size_before': 0,
    'size_after': 0,
    'references_updated': 0
}


def check_cwebp():
    """检查 cwebp 是否安装"""
    try:
        subprocess.run(['cwebp', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def convert_with_pillow(input_path: str, output_path: str) -> bool:
    """使用 Pillow 转换图片（支持动态 GIF）"""
    try:
        from PIL import Image
        
        with Image.open(input_path) as img:
            # 处理动态 GIF -> 动态 WebP
            if img.format == 'GIF' and getattr(img, 'is_animated', False):
                return convert_animated_gif(input_path, output_path)
            
            # 转换为 RGB（如果有透明通道则保留 RGBA）
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img = img.convert('RGBA')
            else:
                img = img.convert('RGB')
            
            img.save(output_path, 'WEBP', quality=WEBP_QUALITY, method=6)
        return True
    except Exception as e:
        print(f"  ❌ Pillow 转换失败: {e}")
        return False


def convert_animated_gif(input_path: str, output_path: str) -> bool:
    """转换动态 GIF 为动态 WebP"""
    try:
        from PIL import Image
        
        with Image.open(input_path) as img:
            frames = []
            durations = []
            
            # 提取所有帧
            try:
                while True:
                    # 获取帧持续时间
                    duration = img.info.get('duration', 100)
                    durations.append(duration)
                    
                    # 转换帧为 RGBA
                    frame = img.convert('RGBA')
                    frames.append(frame.copy())
                    
                    img.seek(img.tell() + 1)
            except EOFError:
                pass
            
            if not frames:
                return False
            
            # 保存为动态 WebP
            frames[0].save(
                output_path,
                'WEBP',
                save_all=True,
                append_images=frames[1:],
                duration=durations,
                loop=0,  # 无限循环
                quality=WEBP_QUALITY,
                method=4  # 动图用较快的方法
            )
            
            print(f" 🎬 动图({len(frames)}帧)", end="")
            return True
            
    except Exception as e:
        print(f"  ❌ 动图转换失败: {e}")
        return False


def convert_with_cwebp(input_path: str, output_path: str) -> bool:
    """使用 cwebp 命令行工具转换"""
    try:
        cmd = ['cwebp', '-q', str(WEBP_QUALITY), input_path, '-o', output_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"  ❌ cwebp 转换失败: {e}")
        return False


def convert_image(file_path: Path, use_cwebp: bool = False) -> tuple:
    """转换单个图片"""
    if file_path.suffix.lower() not in SUPPORTED_FORMATS:
        return None, None, 'skip'
    
    if file_path.suffix.lower() == '.webp':
        return None, None, 'skip'
    
    output_path = file_path.with_suffix('.webp')
    
    # 如果 webp 已存在，跳过
    if output_path.exists():
        return None, None, 'skip'
    
    original_size = file_path.stat().st_size
    
    # 转换
    if use_cwebp:
        success = convert_with_cwebp(str(file_path), str(output_path))
    else:
        success = convert_with_pillow(str(file_path), str(output_path))
    
    if success and output_path.exists():
        new_size = output_path.stat().st_size
        
        # 如果新文件更大，保留原文件
        if new_size > original_size:
            print(f"  ⚠️ WebP 更大，保留原文件: {file_path.name}")
            output_path.unlink()
            return None, None, 'skip'
        
        return original_size, new_size, 'success'
    
    return None, None, 'fail'


def find_images(directory: str) -> list:
    """查找所有需要转换的图片"""
    images = []
    for root, dirs, files in os.walk(directory):
        # 跳过 node_modules 等目录
        dirs[:] = [d for d in dirs if d not in {'node_modules', '.git', 'venv', '__pycache__'}]
        
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in SUPPORTED_FORMATS:
                images.append(file_path)
    return images


def update_code_references(old_ext: str, code_dirs: list):
    """更新代码中的图片引用"""
    extensions_to_check = ['.vue', '.js', '.ts', '.dart', '.html', '.css', '.scss']
    
    for code_dir in code_dirs:
        if not os.path.exists(code_dir):
            continue
            
        for root, dirs, files in os.walk(code_dir):
            dirs[:] = [d for d in dirs if d not in {'node_modules', '.git', 'build'}]
            
            for file in files:
                if not any(file.endswith(ext) for ext in extensions_to_check):
                    continue
                
                file_path = Path(root) / file
                try:
                    content = file_path.read_text(encoding='utf-8')
                    original_content = content
                    
                    # 替换图片引用 (.png -> .webp, .jpg -> .webp, etc.)
                    # 匹配各种引用方式
                    patterns = [
                        (rf'(["\'/])([^"\']*){re.escape(old_ext)}(["\'/])', rf'\1\2.webp\3'),
                        (rf'(src=")([^"]*){re.escape(old_ext)}(")', rf'\1\2.webp\3'),
                        (rf"(src=')([^']*){re.escape(old_ext)}(')", rf"\1\2.webp\3"),
                    ]
                    
                    for pattern, replacement in patterns:
                        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                    
                    if content != original_content:
                        file_path.write_text(content, encoding='utf-8')
                        stats['references_updated'] += 1
                        print(f"  📝 更新引用: {file_path}")
                        
                except Exception as e:
                    print(f"  ⚠️ 无法处理文件 {file_path}: {e}")


def main():
    print("=" * 60)
    print("🖼️  批量转换图片为 WebP 格式")
    print("=" * 60)
    
    # 检查转换工具
    use_cwebp = check_cwebp()
    if use_cwebp:
        print("✅ 使用 cwebp 进行转换")
    else:
        try:
            from PIL import Image
            print("✅ 使用 Pillow 进行转换")
        except ImportError:
            print("❌ 请安装 Pillow: pip install Pillow")
            return
    
    # 收集所有图片
    all_images = []
    for dir_path in CONVERT_DIRS:
        if os.path.exists(dir_path):
            images = find_images(dir_path)
            all_images.extend(images)
            print(f"📁 {dir_path}: 找到 {len(images)} 个图片")
    
    if not all_images:
        print("没有找到需要转换的图片")
        return
    
    print(f"\n总计: {len(all_images)} 个图片待转换\n")
    
    # 转换图片
    converted_files = []
    for img_path in all_images:
        print(f"🔄 转换: {img_path.name}", end="")
        
        original_size, new_size, status = convert_image(img_path, use_cwebp)
        
        if status == 'success':
            stats['converted'] += 1
            stats['size_before'] += original_size
            stats['size_after'] += new_size
            
            savings = (1 - new_size / original_size) * 100
            print(f" ✅ 节省 {savings:.1f}%")
            
            converted_files.append(img_path)
            
            # 删除原文件
            if DELETE_ORIGINAL:
                img_path.unlink()
        elif status == 'skip':
            stats['skipped'] += 1
            print(" ⏭️ 跳过")
        else:
            stats['failed'] += 1
            print(" ❌ 失败")
    
    # 更新代码引用
    if converted_files:
        print("\n📝 更新代码中的图片引用...")
        for ext in SUPPORTED_FORMATS:
            update_code_references(ext, CODE_DIRS)
    
    # 打印统计
    print("\n" + "=" * 60)
    print("📊 转换统计")
    print("=" * 60)
    print(f"✅ 成功转换: {stats['converted']} 个")
    print(f"⏭️ 跳过: {stats['skipped']} 个")
    print(f"❌ 失败: {stats['failed']} 个")
    print(f"📝 更新引用: {stats['references_updated']} 处")
    
    if stats['size_before'] > 0:
        saved = stats['size_before'] - stats['size_after']
        saved_percent = (saved / stats['size_before']) * 100
        print(f"\n💾 空间节省:")
        print(f"   转换前: {stats['size_before'] / 1024 / 1024:.2f} MB")
        print(f"   转换后: {stats['size_after'] / 1024 / 1024:.2f} MB")
        print(f"   节省: {saved / 1024 / 1024:.2f} MB ({saved_percent:.1f}%)")


if __name__ == "__main__":
    main()
