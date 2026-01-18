========================================
转码服务器部署文件包
========================================

这个文件夹包含需要复制到转码服务器的文件。

文件清单：
---------
1. upload_to_main.ps1  - 上传脚本
2. watcher.ps1         - 监控脚本（带自动上传）

部署步骤：
---------

步骤1：SSH 密钥已创建 ✓
你已经在转码服务器上创建了 C:\server_key

步骤2：复制这两个文件到转码服务器
方法：通过远程桌面的复制粘贴功能

目标位置：
- upload_to_main.ps1 -> D:\VideoTranscode\scripts\upload_to_main.ps1
- watcher.ps1 -> D:\VideoTranscode\scripts\watcher.ps1

步骤3：测试上传功能
在转码服务器 PowerShell 中执行：

powershell -ExecutionPolicy Bypass -File D:\VideoTranscode\scripts\upload_to_main.ps1 -VideoFile D:\VideoTranscode\completed\test_out.mp4

步骤4：启动监控服务
powershell -ExecutionPolicy Bypass -NoExit -File D:\VideoTranscode\scripts\watcher.ps1

完成！
---------
系统将自动：
1. 监控 D:\VideoTranscode\downloads\ 目录
2. 自动转码新视频
3. 自动上传到主服务器 (38.47.218.137)
4. 记录日志

查看日志：
- D:\VideoTranscode\logs\watcher.log
- D:\VideoTranscode\logs\upload.log
