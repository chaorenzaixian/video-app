# Implementation Plan: Flutter + WebView 混合方案

## Overview

本实现计划将 Flutter + WebView 混合方案分解为可执行的编码任务。任务按照依赖关系排序，确保每个任务都能在前置任务完成后顺利执行。

## Tasks

- [x] 1. 添加依赖和项目配置
  - [x] 1.1 更新 pubspec.yaml 添加 webview_flutter 依赖
    - 添加 webview_flutter: ^4.4.2
    - 添加 webview_flutter_android 和 webview_flutter_wkwebview
    - 运行 flutter pub get
    - _Requirements: 5.1, 15.4_
  
  - [x] 1.2 配置 Android 权限和设置
    - 在 AndroidManifest.xml 添加 INTERNET 权限
    - 配置 android:usesCleartextTraffic="true" 支持 HTTP
    - 设置 minSdkVersion 为 21
    - _Requirements: 15.1, 15.4_
  
  - [x] 1.3 配置 iOS 设置
    - 在 Info.plist 添加 NSAppTransportSecurity 配置
    - 设置 iOS 最低版本为 12.0
    - _Requirements: 15.2, 15.4_

- [x] 2. 实现 Token 管理器
  - [x] 2.1 创建 TokenManager 类
    - 创建 flutter/lib/core/services/token_manager.dart
    - 实现 Token 存储、读取、清除方法
    - 实现 Token 变化的 Stream 通知
    - 实现 generateTokenInjectionScript 方法
    - _Requirements: 6.1, 6.2, 6.5_
  
  - [ ]* 2.2 编写 TokenManager 属性测试
    - **Property 9: Token Storage and Injection Round-Trip**
    - **Property 10: Token Clear Correctness**
    - **Validates: Requirements 6.1, 6.2, 6.5**

- [x] 3. 实现 JS Bridge 通信层
  - [x] 3.1 创建 JSBridgeMessage 数据模型
    - 创建 flutter/lib/core/models/js_bridge_message.dart
    - 实现 fromJson 和 toJson 方法
    - _Requirements: 7.6_
  
  - [ ]* 3.2 编写 JSBridgeMessage 属性测试
    - **Property 11: JS Bridge Message Serialization Round-Trip**
    - **Validates: Requirements 7.6**
  
  - [x] 3.3 创建 JSBridge 类
    - 创建 flutter/lib/core/services/js_bridge.dart
    - 实现 JavaScript Channel 注册
    - 实现消息处理（navigate、updateToken、share、getDeviceInfo）
    - 实现 callJS 方法调用 WebView JavaScript
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.7_

- [x] 4. 实现混合路由系统
  - [x] 4.1 创建路由配置模型
    - 创建 flutter/lib/core/router/route_config.dart
    - 定义 RouteType 枚举（native, webview）
    - 定义 RouteConfig 类
    - _Requirements: 8.1_
  
  - [x] 4.2 创建 HybridRouter 类
    - 创建 flutter/lib/core/router/hybrid_router.dart
    - 定义路由映射表（原生页面和 WebView 页面）
    - 实现 navigateTo 方法
    - 实现参数传递
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.6_
  
  - [ ]* 4.3 编写 HybridRouter 属性测试
    - **Property 12: Route Type Determination Correctness**
    - **Property 13: WebView URL Mapping Correctness**
    - **Validates: Requirements 8.2, 8.3, 12.1-12.6**

- [ ] 5. Checkpoint - 核心服务层完成
  - 确保所有测试通过，如有问题请询问用户。

- [x] 6. 实现 WebView 容器组件
  - [x] 6.1 创建 WebViewPage Widget
    - 创建 flutter/lib/features/webview/screens/webview_page.dart
    - 实现 WebViewController 初始化
    - 实现加载进度指示器
    - 实现错误页面和重试按钮
    - 集成 JSBridge
    - 实现 Token 注入
    - _Requirements: 5.1, 5.2, 5.3, 5.5, 5.7_
  
  - [x] 6.2 实现 WebView 导航处理
    - 实现页面内导航（前进、后退）
    - 实现新页面打开策略
    - 实现返回键处理
    - _Requirements: 5.4, 5.6, 8.5_

- [x] 7. 实现主界面和底部导航
  - [x] 7.1 创建 MainScreen Widget
    - 创建 flutter/lib/features/main/screens/main_screen.dart
    - 实现 BottomNavigationBar（5个Tab）
    - 使用 IndexedStack 保持页面状态
    - 集成原生页面和 WebView 页面
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  
  - [ ]* 7.2 编写导航属性测试
    - **Property 1: Navigation Index Consistency**
    - **Property 2: Page State Preservation**
    - **Validates: Requirements 1.2, 1.4**

- [ ] 8. 优化首页实现
  - [ ] 8.1 更新 HomePage 分类筛选
    - 确保分类选择时 API 请求包含正确的 categoryId
    - 优化分类标签栏 UI
    - _Requirements: 2.1, 2.3_
  
  - [ ]* 8.2 编写分类筛选属性测试
    - **Property 3: Category Filter Parameter Correctness**
    - **Validates: Requirements 2.3**
  
  - [ ] 8.3 更新视频卡片导航
    - 确保点击视频卡片导航到正确的播放页面
    - 使用 HybridRouter 进行导航
    - _Requirements: 2.6_
  
  - [ ]* 8.4 编写视频卡片导航属性测试
    - **Property 4: Video Card Navigation Correctness**
    - **Validates: Requirements 2.6**

- [ ] 9. 优化短视频播放器
  - [ ] 9.1 更新 ShortsScreen 播放状态管理
    - 确保切换视频时正确管理播放状态
    - 当前视频播放，其他视频暂停
    - _Requirements: 3.3_
  
  - [ ]* 9.2 编写播放状态管理属性测试
    - **Property 5: Shorts Playback State Management**
    - **Validates: Requirements 3.3**
  
  - [ ] 9.3 优化预加载和内存管理
    - 预加载当前视频前后各1个
    - 释放距离超过2的视频控制器
    - _Requirements: 3.4, 3.9_
  
  - [ ]* 9.4 编写预加载和内存管理属性测试
    - **Property 6: Shorts Preload and Memory Management**
    - **Validates: Requirements 3.4, 3.9**
  
  - [ ] 9.5 实现播放/暂停切换
    - 点击视频画面切换播放状态
    - _Requirements: 3.5_
  
  - [ ]* 9.6 编写播放/暂停切换属性测试
    - **Property 7: Play/Pause Toggle Correctness**
    - **Validates: Requirements 3.5**

- [ ] 10. Checkpoint - 原生页面优化完成
  - 确保所有测试通过，如有问题请询问用户。

- [ ] 11. 优化视频播放器
  - [ ] 11.1 确保视频信息显示完整
    - 显示标题、播放量、点赞数、评论数
    - 显示视频简介
    - _Requirements: 4.6, 4.9_
  
  - [ ]* 11.2 编写视频信息显示属性测试
    - **Property 8: Video Information Display Completeness**
    - **Validates: Requirements 3.6, 4.6**
  
  - [ ] 11.3 优化加载和错误状态
    - 加载中显示封面和指示器
    - 加载失败显示错误信息和重试按钮
    - _Requirements: 4.4, 4.5_

- [ ] 12. 优化 API 服务
  - [ ] 12.1 更新 ApiService Token 处理
    - 确保请求头自动携带 Authorization Token
    - 添加 getWebPageUrl 方法
    - _Requirements: 13.6_
  
  - [ ]* 12.2 编写 API Token 携带属性测试
    - **Property 14: API Request Token Header**
    - **Validates: Requirements 13.6**
  
  - [ ] 12.3 优化错误处理
    - 处理超时错误
    - 处理 401 错误（清除 Token，跳转登录）
    - 处理其他错误
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

- [x] 13. 集成 WebView 页面
  - [x] 13.1 配置 VIP 页面
    - 在 HybridRouter 中配置 /vip 路由
    - URL: http://38.47.218.137/user/vip
    - _Requirements: 9.1_
  
  - [x] 13.2 配置个人中心页面
    - 在 HybridRouter 中配置 /profile 路由
    - URL: http://38.47.218.137/user/profile
    - _Requirements: 10.1_
  
  - [x] 13.3 配置社区页面
    - 在 HybridRouter 中配置 /community 路由
    - URL: http://38.47.218.137/user/community
    - _Requirements: 11.1_
  
  - [x] 13.4 配置其他 WebView 页面
    - 设置页面: /user/settings
    - 观看历史: /user/history
    - 我的收藏: /user/favorites
    - 充值页面: /user/recharge
    - 邀请页面: /user/invite
    - 客服页面: /user/service
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

- [ ] 14. 实现用户认证流程
  - [ ] 14.1 更新登录流程
    - 登录成功后通过 TokenManager 设置 Token
    - 同步 Token 到 WebView
    - _Requirements: 13.3, 6.3_
  
  - [ ] 14.2 更新登出流程
    - 通过 TokenManager 清除 Token
    - 清除 WebView 中的 Token
    - 重新进行游客注册
    - _Requirements: 13.5, 6.5_
  
  - [ ] 14.3 实现 WebView 登录同步
    - 通过 JSBridge 接收 WebView 登录事件
    - 更新 Flutter 端 Token
    - _Requirements: 6.4_

- [ ] 15. 更新应用入口和路由
  - [ ] 15.1 更新 main.dart
    - 初始化 TokenManager
    - 设置 MainScreen 为首页
    - _Requirements: 13.1_
  
  - [ ] 15.2 更新 routes.dart
    - 集成 HybridRouter
    - 更新路由生成逻辑
    - _Requirements: 8.1_

- [ ] 16. Final Checkpoint - 功能集成完成
  - 确保所有测试通过，如有问题请询问用户。
  - 验证原生页面和 WebView 页面切换流畅
  - 验证 Token 同步正常工作

## Notes

- 任务标记 `*` 的为可选测试任务，可跳过以加快 MVP 开发
- 每个任务都引用了具体的需求编号以确保可追溯性
- Checkpoint 任务用于阶段性验证
- 属性测试验证通用正确性属性，每个测试至少运行 100 次迭代
