# 实现计划：下载页管理

## 概述

基于现有项目结构，在后端创建下载页配置 API，在前端创建管理页面，实现下载链接、Logo、二维码等配置的管理功能。

## 任务

- [x] 1. 后端 API 开发
  - [x] 1.1 创建下载页配置 API 文件 `backend/app/api/download_page.py`
    - 实现 `GET /api/v1/download-page/config` 公开接口获取配置
    - 实现 `PUT /api/v1/admin/download-page/config` 管理接口更新配置
    - 实现 `POST /api/v1/admin/download-page/upload` 图片上传接口
    - 实现 `POST /api/v1/admin/download-page/qrcode` 二维码生成接口
    - 复用 SystemConfig 模型，使用 `download_page` 分组
    - _需求: 1.1-1.6, 2.1-2.6, 3.1-3.5, 5.1-5.4_

  - [x] 1.2 添加 Pydantic 数据模型
    - 定义 AndroidLink、IOSLinks、QRCodeConfig 等模型
    - 定义请求/响应模型
    - _需求: 1.2, 1.3_

  - [x] 1.3 实现图片上传服务
    - 支持 PNG、JPG、WebP 格式验证
    - 实现 2MB 大小限制
    - 保存到指定目录并返回 URL
    - _需求: 2.1-2.6_

  - [x] 1.4 实现二维码生成服务
    - 使用 qrcode 库生成二维码
    - 支持自定义 Logo、颜色、尺寸
    - 返回 base64 编码图片
    - _需求: 3.1-3.5_

  - [x] 1.5 编写属性测试 - 配置 round-trip
    - **Property 1: 配置保存与读取一致性**
    - **验证: 需求 5.1, 5.2**

  - [x] 1.6 编写属性测试 - 链接状态过滤
    - **Property 2: 链接启用状态正确性**
    - **验证: 需求 1.4**

- [x] 2. 检查点 - 后端 API 完成
  - 确保所有测试通过，如有问题请询问用户。

- [x] 3. 前端页面开发
  - [x] 3.1 创建 `frontend/src/views/admin/DownloadPageManage.vue`
    - 页面布局：下载链接、Logo、二维码、背景图四个区域
    - 使用 Element Plus 组件
    - _需求: 1.1, 4.1-4.3_

  - [x] 3.2 实现下载链接管理功能
    - Android 链接表格（添加、编辑、删除、排序、启用/禁用）
    - iOS 链接表单（App Store、mobileconfig）
    - _需求: 1.1-1.6_

  - [x] 3.3 实现 Logo 管理功能
    - PC 端和移动端 Logo 上传组件
    - 图片预览功能
    - _需求: 2.1-2.4_

  - [x] 3.4 实现二维码生成功能
    - URL 输入框
    - 颜色选择器、尺寸调整
    - Logo 上传（可选）
    - 二维码预览和下载
    - _需求: 3.1-3.5_

  - [x] 3.5 实现背景图管理功能
    - V1/V2 两套背景配置
    - PC 端和移动端背景上传
    - 支持纯色背景设置
    - _需求: 6.1-6.4_

  - [x] 3.6 实现预览功能
    - 预览按钮打开新窗口
    - PC/移动端预览切换
    - _需求: 4.1-4.3_

- [x] 4. 路由与菜单配置
  - [x] 4.1 添加前端路由配置
    - 在 router 中添加 `/admin/download-page` 路由
    - _需求: 1.1_

  - [x] 4.2 添加后端路由注册
    - 在 `backend/app/api/__init__.py` 中注册 download_page router
    - _需求: 5.2_

- [x] 5. 检查点 - 前端页面完成
  - 确保所有测试通过，如有问题请询问用户。

- [x] 6. 数据库初始化
  - [x] 6.1 添加默认配置项
    - 在 SystemConfig 默认配置中添加 download_page 分组的配置项
    - _需求: 5.1_

- [x] 7. 最终检查点
  - 确保所有功能正常工作，如有问题请询问用户。

- [ ] 8. APK 上传功能
  - [ ] 8.1 后端 - 添加 APK 上传接口
    - 在 `backend/app/api/download_page.py` 添加 `POST /admin/upload-apk` 接口
    - 支持最大 200MB 文件上传
    - 验证 APK 文件格式
    - 保存到下载页服务器目录 `/www/wwwroot/app-download/`
    - 返回下载 URL
    - _需求: 7.1, 7.2, 7.5, 7.6_

  - [ ] 8.2 后端 - 添加 APK 删除接口
    - 添加 `DELETE /admin/apk/{filename}` 接口
    - 删除服务器上的 APK 文件
    - _需求: 7.7_

  - [ ] 8.3 前端 - 添加 APK 上传 UI
    - 在 Android 下载链接区域添加 APK 上传组件
    - 显示上传进度条
    - 上传成功后自动填充下载链接
    - _需求: 7.3, 7.4_

  - [ ] 8.4 部署与测试
    - 提交代码到 GitHub
    - 在服务器上拉取并构建
    - 测试 APK 上传功能
    - _需求: 7.1-7.7_

## 备注

- 所有任务均为必需任务
- 每个任务都引用了具体的需求编号以便追溯
- 检查点用于确保增量验证
- 属性测试确保核心功能的正确性
