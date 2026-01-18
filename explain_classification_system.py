#!/usr/bin/env python3
import paramiko
import sys

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

def run_command(ssh, command, description):
    """执行远程命令"""
    print(f"\n📋 {description}...")
    try:
        stdin, stdout, stderr = ssh.exec_command(command, timeout=60)
        output = stdout.read().decode('utf-8', errors='ignore').strip()
        error = stderr.read().decode('utf-8', errors='ignore').strip()
        exit_code = stdout.channel.recv_exit_status()
        
        if exit_code == 0:
            print(f"✅ 成功")
            if output:
                print(f"   输出: {output}")
        else:
            print(f"❌ 失败 (退出码: {exit_code})")
            if error:
                print(f"   错误: {error}")
        
        return output, error, exit_code
    except Exception as e:
        print(f"❌ 异常: {e}")
        return "", str(e), -1

print("📖 长短视频分类系统详细说明")
print("=" * 60)

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"🔐 连接到 {TRANSCODE_SERVER}...")
    ssh.connect(
        hostname=TRANSCODE_SERVER,
        port=22,
        username=TRANSCODE_USER,
        password=TRANSCODE_PASSWORD,
        timeout=30
    )
    print("✅ 连接成功!")
    
    # 1. 查看当前的 watcher 脚本逻辑
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 当前 Watcher 脚本内容 ===\'; Get-Content D:\\VideoTranscode\\scripts\\watcher.ps1"',
        "查看当前 watcher 脚本")
    
    # 2. 查看配置文件
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 配置文件内容 ===\'; if (Test-Path D:\\VideoTranscode\\config.ini) { Get-Content D:\\VideoTranscode\\config.ini } else { Write-Host \'配置文件不存在\' }"',
        "查看配置文件")
    
    # 3. 查看目录结构
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 完整目录结构 ===\'; Write-Host \'Downloads目录:\'; Get-ChildItem D:\\VideoTranscode\\downloads -Recurse | Select-Object FullName, PSIsContainer; Write-Host \'\\nCompleted目录:\'; Get-ChildItem D:\\VideoTranscode\\completed -Recurse | Select-Object FullName, PSIsContainer"',
        "查看完整目录结构")
    
    # 4. 演示 FFprobe 时长检测
    run_command(ssh,
        'powershell -Command "Write-Host \'=== FFprobe 时长检测演示 ===\'; if (Test-Path D:\\VideoTranscode\\completed\\*.mp4) { $testFile = Get-ChildItem D:\\VideoTranscode\\completed -Filter \'*.mp4\' | Select-Object -First 1; Write-Host \'测试文件:\' $testFile.Name; $duration = & ffprobe -v quiet -show_entries format=duration -of csv=p=0 $testFile.FullName 2>$null; Write-Host \'检测到的时长:\' $duration \'秒\'; $threshold = 60; if ([double]$duration -le $threshold) { Write-Host \'分类结果: 短视频 (≤60秒)\' } else { Write-Host \'分类结果: 长视频 (>60秒)\' } } else { Write-Host \'没有可测试的视频文件\' }"',
        "演示时长检测")
    
    print("\n" + "=" * 60)
    print("📖 长短视频分类系统详细说明")
    print("=" * 60)
    
    print("\n🔍 **分类原理**")
    print("系统使用 FFprobe 工具检测视频的实际播放时长，然后根据预设的阈值进行分类。")
    
    print("\n⚙️ **技术实现**")
    print("1. **时长检测**: 使用 `ffprobe -v quiet -show_entries format=duration -of csv=p=0 视频文件`")
    print("2. **分类逻辑**: 比较检测到的时长与配置的阈值")
    print("3. **自动处理**: Watcher 服务自动扫描、检测、分类、转码")
    
    print("\n📁 **目录结构和工作流程**")
    print("""
D:\\VideoTranscode\\
├── downloads\\                    # 上传目录
│   ├── (根目录)                   # 🔄 自动分类区域
│   ├── short\\                    # 📱 手动短视频区域  
│   └── long\\                     # 🎬 手动长视频区域
├── processing\\                   # ⚙️ 临时处理目录
├── completed\\                    # 📤 输出目录
│   ├── short\\                    # 📱 短视频输出
│   └── long\\                     # 🎬 长视频输出
├── logs\\                         # 📝 日志目录
└── config.ini                    # ⚙️ 配置文件
""")
    
    print("\n🔄 **自动分类流程** (推荐方式)")
    print("1. **上传**: 将视频文件放入 `downloads\\` 根目录")
    print("2. **检测**: Watcher 每10秒扫描一次，发现新文件")
    print("3. **分析**: 使用 FFprobe 检测视频实际时长")
    print("4. **分类**: 根据时长与阈值比较")
    print("   - ≤ 60秒 → 标记为 'short'")
    print("   - > 60秒 → 标记为 'long'")
    print("5. **移动**: 文件移动到 `processing\\` 目录")
    print("6. **转码**: 调用转码脚本，传递视频类型参数")
    print("7. **输出**: 转码完成后保存到对应的 `completed\\short\\` 或 `completed\\long\\`")
    
    print("\n👤 **手动分类流程**")
    print("**短视频手动分类**:")
    print("1. 上传到: `downloads\\short\\`")
    print("2. 系统跳过时长检测，直接标记为 'short'")
    print("3. 输出到: `completed\\short\\`")
    print("")
    print("**长视频手动分类**:")
    print("1. 上传到: `downloads\\long\\`")
    print("2. 系统跳过时长检测，直接标记为 'long'")
    print("3. 输出到: `completed\\long\\`")
    
    print("\n⚙️ **配置文件详解** (`config.ini`)")
    print("```ini")
    print("# 视频分类配置")
    print("SHORT_VIDEO_THRESHOLD=60    # 短视频阈值（秒）")
    print("LONG_VIDEO_THRESHOLD=60     # 长视频阈值（秒，目前未使用）")
    print("```")
    print("- 修改 `SHORT_VIDEO_THRESHOLD` 可以调整分类标准")
    print("- 例如设置为 30，则30秒以下为短视频")
    
    print("\n🔧 **Watcher 服务工作机制**")
    print("1. **循环扫描**: 每10秒检查一次 downloads 目录")
    print("2. **文件过滤**: 只处理 .mp4 文件且大小 > 1000字节")
    print("3. **多目录支持**: 同时扫描根目录、short、long 子目录")
    print("4. **时长检测**: 对根目录的文件进行 FFprobe 检测")
    print("5. **类型传递**: 将视频类型参数传递给转码脚本")
    print("6. **日志记录**: 记录处理过程和统计信息")
    
    print("\n📊 **分类示例**")
    print("| 视频时长 | 上传位置 | 分类结果 | 输出位置 |")
    print("|---------|---------|---------|---------|")
    print("| 30秒 | downloads\\ | 自动→short | completed\\short\\ |")
    print("| 90秒 | downloads\\ | 自动→long | completed\\long\\ |")
    print("| 任意 | downloads\\short\\ | 强制→short | completed\\short\\ |")
    print("| 任意 | downloads\\long\\ | 强制→long | completed\\long\\ |")
    
    print("\n🎯 **使用建议**")
    print("✅ **推荐**: 使用自动分类（上传到 downloads 根目录）")
    print("✅ **灵活**: 需要强制分类时使用手动分类")
    print("✅ **可调**: 根据需要修改 config.ini 中的阈值")
    print("✅ **监控**: 查看 logs\\watcher.log 了解处理状态")
    
    print("\n⚠️ **注意事项**")
    print("1. FFprobe 检测需要视频文件完整且格式正确")
    print("2. 损坏的视频文件可能导致检测失败")
    print("3. 非常短的视频（<1秒）可能检测不准确")
    print("4. 手动分类会跳过时长检测，直接按目录分类")
    
except Exception as e:
    print(f"❌ 说明生成失败: {e}")
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()