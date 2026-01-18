# Requirements Document

## Introduction

本文档定义了 Flutter + WebView 混合方案移动端 App 的需求。该 App 将结合 Flutter 原生页面（用于性能关键功能）和 WebView 页面（用于复用现有 Vue 网页功能），为用户提供流畅的视频观看体验。

核心目标：
- 性能关键页面使用 Flutter 原生实现，确保流畅体验
- 复杂功能页面使用 WebView 加载现有 Vue 网页，保证功能一致性
- Flutter 和 WebView 之间共享登录状态（Token）
- 页面外观与 Vue 网页保持一致

## Glossary

- **App**: Flutter 移动端应用程序
- **WebView_Container**: 用于加载和显示 Vue 网页的 WebView 组件
- **Token_Manager**: 负责管理和同步 Flutter 与 WebView 之间登录状态的模块
- **Native_Page**: 使用 Flutter 原生组件实现的页面
- **Hybrid_Router**: 负责在原生页面和 WebView 页面之间进行路由导航的模块
- **JS_Bridge**: Flutter 与 WebView 之间的 JavaScript 通信桥接层
- **Video_Player**: Flutter 原生视频播放器组件，支持 HLS 流媒体
- **Shorts_Player**: 短视频播放器，支持上下滑动切换
- **Bottom_Navigation**: 底部导航栏组件
- **API_Service**: 与后端 API 通信的服务层

## Requirements

### Requirement 1: 底部导航栏

**User Story:** As a 用户, I want 通过底部导航栏快速切换主要功能页面, so that 我可以方便地访问首页、短视频、VIP、社区和个人中心。

#### Acceptance Criteria

1. THE Bottom_Navigation SHALL 显示五个导航项：首页、短视频、VIP、社区、我的
2. WHEN 用户点击导航项 THEN THE Bottom_Navigation SHALL 切换到对应页面并高亮当前选中项
3. THE Bottom_Navigation SHALL 在所有主要页面底部保持可见
4. WHEN 用户切换页面 THEN THE App SHALL 保持之前页面的状态不丢失

### Requirement 2: 首页（Flutter 原生）

**User Story:** As a 用户, I want 在首页浏览视频列表和分类, so that 我可以快速找到感兴趣的视频内容。

#### Acceptance Criteria

1. WHEN 首页加载 THEN THE App SHALL 从 API 获取视频分类列表并显示为可滑动的标签栏
2. WHEN 首页加载 THEN THE App SHALL 从 API 获取视频列表并以网格形式展示
3. WHEN 用户选择分类标签 THEN THE App SHALL 加载该分类下的视频列表
4. WHEN 用户下拉刷新 THEN THE App SHALL 重新获取最新视频数据
5. WHEN 用户滚动到列表底部 THEN THE App SHALL 自动加载更多视频
6. WHEN 用户点击视频卡片 THEN THE App SHALL 导航到视频播放页面
7. THE App SHALL 使用 cached_network_image 缓存视频封面图片
8. WHEN 用户点击搜索图标 THEN THE App SHALL 导航到搜索页面

### Requirement 3: 短视频页面（Flutter 原生）

**User Story:** As a 用户, I want 上下滑动浏览短视频, so that 我可以像使用抖音一样流畅地观看短视频内容。

#### Acceptance Criteria

1. WHEN 短视频页面加载 THEN THE Shorts_Player SHALL 从 API 获取短视频列表
2. THE Shorts_Player SHALL 支持上下滑动切换视频
3. WHEN 用户滑动到新视频 THEN THE Shorts_Player SHALL 自动播放当前视频并暂停上一个视频
4. THE Shorts_Player SHALL 预加载当前视频前后各一个视频以确保流畅切换
5. WHEN 用户点击视频画面 THEN THE Shorts_Player SHALL 切换播放/暂停状态
6. THE Shorts_Player SHALL 显示视频标题、上传者信息、点赞数、评论数
7. THE Shorts_Player SHALL 在右侧显示操作栏：头像、点赞、评论、收藏、分享
8. WHEN 用户点击点赞按钮 THEN THE App SHALL 调用 API 进行点赞操作并更新 UI 状态
9. THE Shorts_Player SHALL 释放距离当前视频超过2个位置的视频控制器以节省内存

### Requirement 4: 视频播放器（Flutter 原生）

**User Story:** As a 用户, I want 流畅地播放视频并控制播放, so that 我可以获得良好的视频观看体验。

#### Acceptance Criteria

1. WHEN 视频播放页面加载 THEN THE Video_Player SHALL 从 API 获取视频详情
2. THE Video_Player SHALL 支持 HLS 流媒体播放
3. THE Video_Player SHALL 显示播放控制栏：播放/暂停、进度条、全屏、音量
4. WHEN 视频加载中 THEN THE Video_Player SHALL 显示封面图片和加载指示器
5. IF 视频加载失败 THEN THE Video_Player SHALL 显示错误信息和重试按钮
6. THE Video_Player SHALL 显示视频标题、播放量、点赞数、评论数
7. THE Video_Player SHALL 提供点赞、收藏、分享、下载操作按钮
8. WHEN 用户点击点赞或收藏按钮 THEN THE App SHALL 调用 API 并更新 UI 状态
9. THE Video_Player SHALL 在视频下方显示视频简介

### Requirement 5: WebView 容器

**User Story:** As a 开发者, I want 一个通用的 WebView 容器组件, so that 可以复用现有 Vue 网页功能而无需重新开发。

#### Acceptance Criteria

1. THE WebView_Container SHALL 使用 webview_flutter 包加载网页
2. WHEN WebView 加载页面 THEN THE WebView_Container SHALL 显示加载进度指示器
3. IF WebView 加载失败 THEN THE WebView_Container SHALL 显示错误页面和重试按钮
4. THE WebView_Container SHALL 支持页面内导航（前进、后退）
5. THE WebView_Container SHALL 在加载前自动注入用户 Token 到页面
6. WHEN 网页请求打开新页面 THEN THE WebView_Container SHALL 在当前容器内导航或根据配置打开新页面
7. THE WebView_Container SHALL 支持下拉刷新当前页面

### Requirement 6: Token 同步机制

**User Story:** As a 用户, I want 在 Flutter 原生页面和 WebView 页面之间保持登录状态一致, so that 我不需要重复登录。

#### Acceptance Criteria

1. THE Token_Manager SHALL 在 SharedPreferences 中存储用户 Token
2. WHEN WebView 加载页面 THEN THE Token_Manager SHALL 通过 JavaScript 将 Token 注入到网页 localStorage
3. WHEN 用户在 Flutter 原生页面登录 THEN THE Token_Manager SHALL 更新存储的 Token 并同步到所有 WebView 实例
4. WHEN 用户在 WebView 页面登录 THEN THE JS_Bridge SHALL 将新 Token 传递给 Flutter 并更新本地存储
5. WHEN 用户登出 THEN THE Token_Manager SHALL 清除 Flutter 和 WebView 中的所有 Token
6. WHEN Token 过期或无效 THEN THE App SHALL 自动跳转到登录页面

### Requirement 7: JavaScript 桥接通信

**User Story:** As a 开发者, I want Flutter 和 WebView 之间能够双向通信, so that 可以实现原生功能调用和状态同步。

#### Acceptance Criteria

1. THE JS_Bridge SHALL 支持 Flutter 调用 WebView 中的 JavaScript 方法
2. THE JS_Bridge SHALL 支持 WebView 中的 JavaScript 调用 Flutter 原生方法
3. WHEN 网页需要打开原生页面 THEN THE JS_Bridge SHALL 接收导航请求并调用 Hybrid_Router
4. WHEN 网页需要获取设备信息 THEN THE JS_Bridge SHALL 返回设备 ID、平台类型等信息
5. WHEN 网页需要分享内容 THEN THE JS_Bridge SHALL 调用 Flutter 原生分享功能
6. THE JS_Bridge SHALL 使用 JSON 格式进行数据传输
7. IF JS_Bridge 调用失败 THEN THE App SHALL 记录错误日志并返回错误信息给调用方

### Requirement 8: 混合路由导航

**User Story:** As a 用户, I want 在原生页面和 WebView 页面之间无缝切换, so that 我感受不到两种技术实现的差异。

#### Acceptance Criteria

1. THE Hybrid_Router SHALL 维护原生页面和 WebView 页面的路由映射表
2. WHEN 导航到原生页面路由 THEN THE Hybrid_Router SHALL 使用 Flutter Navigator 进行导航
3. WHEN 导航到 WebView 页面路由 THEN THE Hybrid_Router SHALL 打开 WebView_Container 并加载对应 URL
4. THE Hybrid_Router SHALL 支持传递参数到目标页面
5. WHEN 用户按返回键 THEN THE Hybrid_Router SHALL 正确处理原生页面和 WebView 页面的返回逻辑
6. THE Hybrid_Router SHALL 支持页面结果回传

### Requirement 9: VIP 会员页面（WebView）

**User Story:** As a 用户, I want 查看和购买 VIP 会员, so that 我可以享受会员专属内容和特权。

#### Acceptance Criteria

1. WHEN 用户进入 VIP 页面 THEN THE WebView_Container SHALL 加载 VIP 网页：http://38.47.218.137/user/vip
2. THE WebView_Container SHALL 正确显示 VIP 等级、价格、特权信息
3. WHEN 用户点击购买 THEN THE WebView_Container SHALL 正常处理支付流程
4. WHEN VIP 购买成功 THEN THE JS_Bridge SHALL 通知 Flutter 刷新用户信息

### Requirement 10: 个人中心页面（WebView）

**User Story:** As a 用户, I want 管理我的个人信息和账户设置, so that 我可以自定义我的账户。

#### Acceptance Criteria

1. WHEN 用户进入个人中心 THEN THE WebView_Container SHALL 加载个人中心网页：http://38.47.218.137/user/profile
2. THE WebView_Container SHALL 正确显示用户头像、昵称、VIP 状态、金币余额
3. WHEN 用户修改个人信息 THEN THE JS_Bridge SHALL 通知 Flutter 刷新用户数据
4. THE WebView_Container SHALL 正确显示功能入口：观看历史、我的收藏、我的下载等

### Requirement 11: 社区页面（WebView）

**User Story:** As a 用户, I want 浏览和参与社区互动, so that 我可以与其他用户交流。

#### Acceptance Criteria

1. WHEN 用户进入社区页面 THEN THE WebView_Container SHALL 加载社区网页：http://38.47.218.137/user/community
2. THE WebView_Container SHALL 正确显示帖子列表、话题分类
3. WHEN 用户点击帖子 THEN THE WebView_Container SHALL 导航到帖子详情页
4. WHEN 用户发布内容 THEN THE WebView_Container SHALL 正常处理发布流程

### Requirement 12: 其他 WebView 页面

**User Story:** As a 用户, I want 访问其他功能页面, so that 我可以使用完整的平台功能。

#### Acceptance Criteria

1. WHEN 用户进入设置页面 THEN THE WebView_Container SHALL 加载：http://38.47.218.137/user/settings
2. WHEN 用户进入观看历史 THEN THE WebView_Container SHALL 加载：http://38.47.218.137/user/history
3. WHEN 用户进入我的收藏 THEN THE WebView_Container SHALL 加载：http://38.47.218.137/user/favorites
4. WHEN 用户进入充值页面 THEN THE WebView_Container SHALL 加载：http://38.47.218.137/user/recharge
5. WHEN 用户进入邀请页面 THEN THE WebView_Container SHALL 加载：http://38.47.218.137/user/invite
6. WHEN 用户进入客服页面 THEN THE WebView_Container SHALL 加载：http://38.47.218.137/user/service

### Requirement 13: 用户认证

**User Story:** As a 用户, I want 登录和注册账户, so that 我可以使用个性化功能和保存我的数据。

#### Acceptance Criteria

1. WHEN App 首次启动且无 Token THEN THE App SHALL 自动进行游客注册
2. WHEN 用户选择登录 THEN THE App SHALL 显示登录页面
3. WHEN 用户输入正确的用户名和密码 THEN THE App SHALL 调用登录 API 并保存 Token
4. IF 登录失败 THEN THE App SHALL 显示错误提示信息
5. WHEN 用户登出 THEN THE App SHALL 清除 Token 并重新进行游客注册
6. THE App SHALL 在 API 请求头中自动携带 Authorization Token

### Requirement 14: 网络错误处理

**User Story:** As a 用户, I want 在网络异常时获得友好的提示, so that 我知道发生了什么并可以采取行动。

#### Acceptance Criteria

1. IF 网络请求超时 THEN THE App SHALL 显示超时提示并提供重试选项
2. IF 网络不可用 THEN THE App SHALL 显示无网络提示
3. IF API 返回 401 错误 THEN THE App SHALL 清除 Token 并跳转到登录页面
4. IF API 返回其他错误 THEN THE App SHALL 显示对应的错误信息
5. THE App SHALL 设置合理的请求超时时间（60秒）

### Requirement 15: 平台兼容性

**User Story:** As a 用户, I want App 在 Android 和 iOS 上都能正常运行, so that 我可以在不同设备上使用。

#### Acceptance Criteria

1. THE App SHALL 支持 Android 5.0 (API 21) 及以上版本
2. THE App SHALL 支持 iOS 12.0 及以上版本
3. THE App SHALL 正确处理 Android 和 iOS 的状态栏和安全区域
4. THE WebView_Container SHALL 在 Android 上使用 Android WebView，在 iOS 上使用 WKWebView
5. THE App SHALL 正确处理 Android 返回键行为
