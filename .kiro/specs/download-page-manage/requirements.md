# 需求文档

## 简介

下载页管理功能允许管理员在后台配置和管理 App 下载页面的各项设置，包括下载链接、Logo 图片、二维码生成等，实现下载页内容的动态管理。

## 术语表

- **Download_Page_Manager**: 下载页管理系统，负责管理下载页配置的核心模块
- **Download_Link**: 下载链接，包含 Android 和 iOS 平台的应用下载地址
- **Logo_Manager**: Logo 管理器，负责上传和管理下载页的 Logo 图片
- **QRCode_Generator**: 二维码生成器，根据下载页 URL 生成可下载的二维码图片
- **Config_Sync_Service**: 配置同步服务，负责将后台配置同步到下载页
- **APK_Upload_Manager**: APK 上传管理器，负责上传和管理 Android 安装包文件

## 需求

### 需求 1：下载链接管理

**用户故事：** 作为管理员，我想管理 Android 和 iOS 的下载链接，以便用户能够从正确的地址下载应用。

#### 验收标准

1. WHEN 管理员访问下载页管理页面 THEN Download_Page_Manager SHALL 显示当前所有下载链接配置
2. WHEN 管理员添加 Android 下载链接 THEN Download_Page_Manager SHALL 保存链接并支持设置为主链接或备用链接
3. WHEN 管理员添加 iOS 下载链接 THEN Download_Page_Manager SHALL 支持 App Store 链接和 mobileconfig 链接两种类型
4. WHEN 管理员切换链接启用状态 THEN Download_Page_Manager SHALL 立即更新链接的可用性
5. WHEN 管理员删除下载链接 THEN Download_Page_Manager SHALL 移除该链接并更新配置
6. WHEN 管理员调整链接优先级 THEN Download_Page_Manager SHALL 按优先级顺序展示链接

### 需求 2：Logo 管理

**用户故事：** 作为管理员，我想上传和管理下载页的 Logo 图片，以便展示品牌形象。

#### 验收标准

1. WHEN 管理员上传 PC 端 Logo THEN Logo_Manager SHALL 保存图片并返回可访问的 URL
2. WHEN 管理员上传移动端 Logo THEN Logo_Manager SHALL 保存图片并返回可访问的 URL
3. WHEN 管理员预览 Logo THEN Logo_Manager SHALL 显示当前配置的 Logo 图片
4. WHEN 管理员更换 Logo THEN Logo_Manager SHALL 替换旧图片并更新配置
5. IF 上传的图片格式不支持 THEN Logo_Manager SHALL 拒绝上传并提示支持的格式（PNG、JPG、WebP）
6. IF 上传的图片超过大小限制 THEN Logo_Manager SHALL 拒绝上传并提示大小限制

### 需求 3：二维码生成

**用户故事：** 作为管理员，我想根据下载页 URL 生成二维码，以便用户可以扫码访问下载页。

#### 验收标准

1. WHEN 管理员输入下载页 URL THEN QRCode_Generator SHALL 实时生成对应的二维码预览
2. WHEN 管理员点击下载二维码 THEN QRCode_Generator SHALL 生成 PNG 格式的二维码图片供下载
3. WHEN 管理员自定义二维码 Logo THEN QRCode_Generator SHALL 在二维码中心嵌入指定的 Logo
4. WHEN 管理员自定义二维码颜色 THEN QRCode_Generator SHALL 使用指定颜色生成二维码
5. WHEN 管理员调整二维码尺寸 THEN QRCode_Generator SHALL 按指定尺寸生成二维码

### 需求 4：下载页预览

**用户故事：** 作为管理员，我想实时预览下载页效果，以便确认配置是否正确。

#### 验收标准

1. WHEN 管理员点击预览按钮 THEN Download_Page_Manager SHALL 在新窗口打开下载页预览
2. WHEN 管理员修改配置后预览 THEN Download_Page_Manager SHALL 显示最新配置的效果
3. WHEN 管理员切换 PC/移动端预览 THEN Download_Page_Manager SHALL 显示对应端的预览效果

### 需求 5：配置持久化与同步

**用户故事：** 作为管理员，我想保存配置并同步到下载页，以便用户访问时看到最新内容。

#### 验收标准

1. WHEN 管理员保存配置 THEN Config_Sync_Service SHALL 将配置持久化到数据库
2. WHEN 下载页加载时 THEN Config_Sync_Service SHALL 提供 API 返回最新配置
3. WHEN 配置更新成功 THEN Config_Sync_Service SHALL 返回成功提示
4. IF 配置保存失败 THEN Config_Sync_Service SHALL 返回错误信息并保持原配置不变

### 需求 6：背景图管理

**用户故事：** 作为管理员，我想管理下载页的背景图，以便自定义页面外观。

#### 验收标准

1. WHEN 管理员上传 PC 端背景图 THEN Download_Page_Manager SHALL 保存图片并更新配置
2. WHEN 管理员上传移动端背景图 THEN Download_Page_Manager SHALL 保存图片并更新配置
3. WHEN 管理员设置纯色背景 THEN Download_Page_Manager SHALL 支持使用颜色值替代图片
4. WHEN 管理员切换背景版本 THEN Download_Page_Manager SHALL 支持多套背景配置切换

### 需求 7：APK 安装包上传

**用户故事：** 作为管理员，我想直接上传 APK 安装包到服务器，以便用户可以直接下载应用而无需手动配置外部链接。

#### 验收标准

1. WHEN 管理员上传 APK 文件 THEN APK_Upload_Manager SHALL 保存文件到下载页服务器目录
2. WHEN APK 上传成功 THEN APK_Upload_Manager SHALL 返回可访问的下载 URL
3. WHEN 管理员上传 APK THEN APK_Upload_Manager SHALL 显示上传进度
4. WHEN APK 上传完成 THEN APK_Upload_Manager SHALL 自动填充到 Android 下载链接
5. IF 上传的文件不是 APK 格式 THEN APK_Upload_Manager SHALL 拒绝上传并提示错误
6. IF 上传的 APK 超过大小限制（200MB）THEN APK_Upload_Manager SHALL 拒绝上传并提示大小限制
7. WHEN 管理员删除已上传的 APK THEN APK_Upload_Manager SHALL 移除服务器上的文件
