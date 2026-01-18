========================================
转码服务器配置文件包
========================================

这个文件夹包含配置转码服务器自动上传功能所需的所有文件。

文件清单：
---------
1. upload_to_main.ps1       - 上传脚本
2. watcher_with_upload.ps1  - 监控脚本（带自动上传）
3. SETUP_INSTRUCTIONS.txt   - 快速配置说明
4. README_DEPLOY.txt        - 本文件

部署方法：
---------

方法1：远程桌面（推荐）
1. 使用远程桌面连接到 198.176.60.121
2. 将这个文件夹复制到转码服务器桌面
3. 按照 SETUP_INSTRUCTIONS.txt 的说明操作

方法2：U盘传输
1. 将这个文件夹复制到 U 盘
2. 在转码服务器上插入 U 盘
3. 复制文件到相应位置

配置步骤（简要）：
-----------------

步骤1：创建 SSH 密钥
在转码服务器 PowerShell 中执行：

$keyContent = @"
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACBE9vQLi1nGfWBVacAymJd/B6TeSVq6KeYxZBCd57L9gAAAAJDvzGZC78xm
QgAAAAtzc2gtZWQyNTUxOQAAACBE9vQLi1nGfWBVacAymJd/B6TeSVq6KeYxZBCd57L9gA
AAAECtAxcJq0SjnZjz4DYebdKR/2BX09k3EOCZniP9JI0SwkT29AuLWcZ9YFVpwDKYl38H
pN5JWrop5jFkEJ3nsv2AAAAADXJvb3RASEIxMzExMDM=
-----END OPENSSH PRIVATE KEY-----
"@
$keyContent | Out-File -FilePath C:\server_key -Encoding ASCII -NoNewline

步骤2：复制脚本文件
- upload_to_main.ps1 -> D:\VideoTranscode\scripts\upload_to_main.ps1
- watcher_with_upload.ps1 -> D:\VideoTranscode\scripts\watcher.ps1

步骤3：测试上传
powershell -ExecutionPolicy Bypass -File D:\VideoTranscode\scripts\upload_to_main.ps1 -VideoFile D:\VideoTranscode\completed\test_out.mp4

步骤4：启动监控
powershell -ExecutionPolicy Bypass -NoExit -File D:\VideoTranscode\scripts\watcher.ps1

完成！
------
详细说明请查看：转码服务器上传配置完成指南.md

技术支持：
---------
- 主服务器：38.47.218.137
- 转码服务器：198.176.60.121
- 上传目录：/www/wwwroot/video-app/backend/uploads/videos/
- 可用空间：412 GB
