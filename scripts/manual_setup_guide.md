# 手动配置上传功能指南

由于自动部署遇到问题，请按以下步骤手动配置：

## 方法1：通过远程桌面配置（推荐）

### 步骤1：连接到转码服务器
1. 打开远程桌面连接
2. 输入：`198.176.60.121`
3. 用户名：`Administrator`
4. 密码：`jCkMIjNlnSd7f6GM`

### 步骤2：创建 SSH 密钥文件
在转码服务器上打开 PowerShell，执行：

```powershell
# 创建密钥文件
@"
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACBE9vQLi1nGfWBVacAymJd/B6TeSVq6KeYxZBCd57L9gAAAAJDvzGZC78xm
QgAAAAtzc2gtZWQyNTUxOQAAACBE9vQLi1nGfWBVacAymJd/B6TeSVq6KeYxZBCd57L9gA
AAAECtAxcJq0SjnZjz4DYebdKR/2BX09k3EOCZniP9JI0SwkT29AuLWcZ9YFVpwDKYl38H
pN5JWrop5jFkEJ3nsv2AAAAADXJvb3RASEIxMzExMDM=
-----END OPENSSH PRIVATE KEY-----
"@ | Out-File -FilePath C:\server_key -Encoding ASCII

# 验证文件
Get-Content C:\server_key
```

### 步骤3：下载脚本文件
在转码服务器上，下载以下两个文件到 `D:\VideoTranscode\scripts\`：

1. **upload_to_main.ps1** - 从本地项目的 `scripts\upload_to_main.ps1`
2. **watcher.ps1** - 从本地项目的 `scripts\watcher_with_upload.ps1`（重命名为 watcher.ps1）

可以通过以下方式传输：
- 复制粘贴文件内容
- 使用 U 盘
- 通过远程桌面的文件共享

### 步骤4：测试上传功能

```powershell
# 测试上传脚本
powershell -ExecutionPolicy Bypass -File D:\VideoTranscode\scripts\upload_to_main.ps1 -VideoFile D:\VideoTranscode\completed\test_out.mp4
```

### 步骤5：启动监控服务

```powershell
# 启动带上传功能的监控服务
powershell -ExecutionPolicy Bypass -NoExit -File D:\VideoTranscode\scripts\watcher.ps1
```

## 方法2：使用密码认证的上传脚本（备选）

如果 SSH 密钥认证有问题，可以使用密码认证版本。

创建 `D:\VideoTranscode\scripts\upload_with_password.ps1`：

```powershell
# upload_with_password.ps1
param(
    [Parameter(Mandatory=$true)]
    [string]$VideoFile
)

$mainServer = "38.47.218.137"
$mainUser = "root"
$mainPass = "YOUR_MAIN_SERVER_PASSWORD"  # 需要主服务器密码
$uploadPath = "/www/wwwroot/video-app/backend/uploads/videos/"

# 使用 WinSCP 或其他支持密码的工具上传
# 或者使用 sshpass (需要安装)
```

## 验证清单

- [ ] SSH 密钥文件已创建：`C:\server_key`
- [ ] 上传脚本已部署：`D:\VideoTranscode\scripts\upload_to_main.ps1`
- [ ] 监控脚本已更新：`D:\VideoTranscode\scripts\watcher.ps1`
- [ ] 测试上传成功
- [ ] 监控服务正常运行

## 测试完整流程

1. 将测试视频放入：`D:\VideoTranscode\downloads\test.mp4`
2. 监控服务会自动：
   - 转码视频
   - 上传到主服务器
   - 记录日志
3. 检查主服务器：`/www/wwwroot/video-app/backend/uploads/videos/`
4. 查看日志：`D:\VideoTranscode\logs\upload.log`

## 故障排查

### 上传失败
- 检查 SSH 密钥文件是否正确
- 检查主服务器是否可访问
- 查看日志：`D:\VideoTranscode\logs\upload.log`

### 权限问题
- 确保 SSH 密钥文件权限正确
- 在 Windows 上不需要特殊权限设置

### 网络问题
- 测试连接：`ping 38.47.218.137`
- 测试 SSH：`ssh -i C:\server_key root@38.47.218.137`

## 下一步

配置完成后，系统将自动：
1. 监控 `D:\VideoTranscode\downloads\` 目录
2. 自动转码新视频
3. 自动上传到主服务器
4. 记录所有操作日志

每天可处理 300+ 个视频！
