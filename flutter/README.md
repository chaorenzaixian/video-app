# VOD 视频 - Flutter 移动端

## 项目结构

```
lib/
├── main.dart                 # 入口文件
├── app/
│   ├── app.dart             # App 根组件
│   ├── routes.dart          # 路由配置
│   └── theme.dart           # 主题配置
├── core/
│   ├── models/              # 数据模型
│   │   ├── user.dart
│   │   ├── video.dart
│   │   └── category.dart
│   ├── providers/           # 状态管理
│   │   ├── auth_provider.dart
│   │   ├── user_provider.dart
│   │   └── video_provider.dart
│   └── services/            # 服务层
│       ├── api_service.dart
│       └── storage_service.dart
└── features/
    ├── auth/                # 认证模块
    │   └── screens/
    │       ├── login_screen.dart
    │       └── register_screen.dart
    ├── home/                # 首页模块
    │   ├── screens/
    │   │   └── home_screen.dart
    │   └── widgets/
    │       ├── video_grid.dart
    │       └── category_tabs.dart
    ├── video/               # 视频模块
    │   └── screens/
    │       ├── video_player_screen.dart
    │       └── video_list_screen.dart
    ├── shorts/              # 短视频模块
    ├── profile/             # 个人中心
    ├── vip/                 # VIP 会员
    └── search/              # 搜索
```

## 开始开发

### 1. 环境准备

- Flutter SDK >= 3.0.0
- Dart SDK >= 3.0.0
- Android Studio / VS Code

### 2. 安装依赖

```bash
cd flutter
flutter pub get
```

### 3. 配置 API 地址

编辑 `lib/core/services/api_service.dart`：

```dart
static const String baseUrl = 'http://your-server-ip:8001/api/v1';
```

### 4. 运行项目

```bash
# 运行在模拟器
flutter run

# 运行在指定设备
flutter run -d <device_id>

# 构建 APK
flutter build apk --release

# 构建 iOS
flutter build ios --release
```

## 功能清单

### 已完成
- [x] 项目架构搭建
- [x] 登录/注册页面
- [x] 游客登录
- [x] 首页视频列表
- [x] 分类筛选
- [x] 视频详情页
- [x] VIP 购买页
- [x] 搜索页面
- [x] 个人中心

### 待完成
- [ ] 视频播放器集成
- [ ] 短视频滑动播放
- [ ] 评论功能
- [ ] 支付集成
- [ ] 下载功能
- [ ] 推送通知
- [ ] 分享功能

## 技术栈

- **状态管理**: Provider
- **网络请求**: Dio
- **本地存储**: SharedPreferences
- **视频播放**: video_player + chewie
- **图片缓存**: cached_network_image
- **下拉刷新**: pull_to_refresh
- **屏幕适配**: flutter_screenutil
