import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/app_provider.dart';
import '../../providers/user_provider.dart';
import '../../app/theme.dart';
import '../../utils/assets.dart';
import '../home/home_screen.dart';
import '../shorts/shorts_screen.dart';
import '../profile/profile_screen.dart';

/// 主布局 - 精确复刻 Vue.js 底部导航
class MainLayout extends StatefulWidget {
  const MainLayout({super.key});

  @override
  State<MainLayout> createState() => _MainLayoutState();
}

class _MainLayoutState extends State<MainLayout> {
  final List<Widget> _screens = [
    const HomeScreen(),
    const ShortsScreen(),
    const Center(child: Text('Soul', style: TextStyle(color: Colors.white))), // 占位
    const Center(child: Text('广场', style: TextStyle(color: Colors.white))), // 占位
    const ProfileScreen(),
  ];

  // 底部导航标签 - 与 Vue 完全一致
  final List<String> _labels = ['首页', '禁区', 'Soul', '广场', '自己'];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<UserProvider>().init();
      context.read<AppProvider>().initAppData();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AppProvider>(
      builder: (context, appProvider, child) {
        return Scaffold(
          backgroundColor: const Color(0xFF0A0A0A),
          body: IndexedStack(
            index: appProvider.currentTabIndex,
            children: _screens,
          ),
          bottomNavigationBar: _buildBottomNav(appProvider),
        );
      },
    );
  }

  /// 底部导航 - 精确复刻 Vue bottom-nav 样式
  Widget _buildBottomNav(AppProvider appProvider) {
    return Container(
      decoration: BoxDecoration(
        // Vue: background: linear-gradient(to top, #0a0a0a 0%, rgba(10, 10, 10, 0.98) 100%)
        gradient: LinearGradient(
          begin: Alignment.bottomCenter,
          end: Alignment.topCenter,
          colors: [
            const Color(0xFF0A0A0A),
            const Color(0xFF0A0A0A).withOpacity(0.98),
          ],
        ),
        // Vue: border-top: 1px solid rgba(255, 255, 255, 0.06)
        border: Border(
          top: BorderSide(
            color: Colors.white.withOpacity(0.06),
            width: 1,
          ),
        ),
      ),
      child: SafeArea(
        top: false,
        child: Padding(
          // Vue: padding-bottom: calc(clamp(2px, 0.8vw, 5px) + env(safe-area-inset-bottom))
          padding: const EdgeInsets.only(top: 6, bottom: 4),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: List.generate(5, (index) {
              // 中间的 Soul 按钮特殊处理
              if (index == 2) {
                return _buildSoulButton(appProvider);
              }
              return _buildNavItem(index, appProvider);
            }),
          ),
        ),
      ),
    );
  }

  /// 普通导航项 - 对应 Vue nav-item
  Widget _buildNavItem(int index, AppProvider appProvider) {
    final isActive = appProvider.currentTabIndex == index;

    return GestureDetector(
      onTap: () => appProvider.setTabIndex(index),
      behavior: HitTestBehavior.opaque,
      child: Container(
        // Vue: padding: clamp(3px, 1vw, 6px) clamp(8px, 3vw, 16px)
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // 图标容器 - Vue: nav-icon-img
            Container(
              // Vue: width: clamp(24px, 7vw, 32px), height: clamp(24px, 7vw, 32px)
              width: 28,
              height: 28,
              alignment: Alignment.center,
              child: Image.asset(
                AppAssets.getNavIcon(index, isActive),
                width: 28,
                height: 28,
                fit: BoxFit.contain,
                errorBuilder: (context, error, stackTrace) {
                  return Icon(
                    _getDefaultIcon(index),
                    color: isActive ? AppTheme.primaryColor : Colors.white.withOpacity(0.45),
                    size: 24,
                  );
                },
              ),
            ),
            // Vue: gap: clamp(1px, 0.5vw, 3px)
            const SizedBox(height: 2),
            // 标签文字 - Vue: nav-label
            isActive
                ? ShaderMask(
                    // Vue: background: linear-gradient(135deg, #c084fc, #818cf8)
                    shaderCallback: (bounds) => const LinearGradient(
                      colors: [Color(0xFFC084FC), Color(0xFF818CF8)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ).createShader(bounds),
                    child: Text(
                      _labels[index],
                      style: const TextStyle(
                        // Vue: font-size: clamp(11px, 3vw, 13px)
                        fontSize: 11,
                        color: Colors.white,
                        // Vue: letter-spacing: 0.5px
                        letterSpacing: 0.5,
                      ),
                    ),
                  )
                : Text(
                    _labels[index],
                    style: TextStyle(
                      fontSize: 11,
                      // Vue: color: rgba(255, 255, 255, 0.45)
                      color: Colors.white.withOpacity(0.45),
                      letterSpacing: 0.5,
                    ),
                  ),
          ],
        ),
      ),
    );
  }

  IconData _getDefaultIcon(int index) {
    switch (index) {
      case 0:
        return Icons.home_outlined;
      case 1:
        return Icons.play_circle_outline;
      case 3:
        return Icons.explore_outlined;
      case 4:
        return Icons.person_outline;
      default:
        return Icons.circle_outlined;
    }
  }

  /// Soul 中间按钮 - 特殊样式
  Widget _buildSoulButton(AppProvider appProvider) {
    final isActive = appProvider.currentTabIndex == 2;

    return GestureDetector(
      onTap: () => _showPublishOptions(),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Soul 图标
            Container(
              width: 28,
              height: 28,
              alignment: Alignment.center,
              child: Image.asset(
                AppAssets.getNavIcon(2, isActive),
                width: 28,
                height: 28,
                fit: BoxFit.contain,
                errorBuilder: (context, error, stackTrace) {
                  return Container(
                    width: 28,
                    height: 28,
                    decoration: BoxDecoration(
                      gradient: AppTheme.primaryGradient,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.add, color: Colors.white, size: 20),
                  );
                },
              ),
            ),
            const SizedBox(height: 2),
            Text(
              _labels[2],
              style: TextStyle(
                fontSize: 11,
                color: isActive
                    ? AppTheme.primaryColor
                    : Colors.white.withOpacity(0.45),
                letterSpacing: 0.5,
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// 发布选项弹窗
  void _showPublishOptions() {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF1A1A1A),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // 拖动条
                Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
                const SizedBox(height: 24),
                // 发布选项
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    _buildPublishOption(
                      AppAssets.publishVideo,
                      '发布视频',
                      Icons.videocam,
                      () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/publish/video');
                      },
                    ),
                    _buildPublishOption(
                      AppAssets.publishImg,
                      '发布短视频',
                      Icons.short_text,
                      () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/publish/short');
                      },
                    ),
                    _buildPublishOption(
                      AppAssets.publishImgText,
                      '发布图文',
                      Icons.image,
                      () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/publish/image');
                      },
                    ),
                  ],
                ),
                const SizedBox(height: 20),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildPublishOption(
    String asset,
    String label,
    IconData fallbackIcon,
    VoidCallback onTap,
  ) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              color: AppTheme.primaryColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(16),
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: Image.asset(
                asset,
                fit: BoxFit.cover,
                errorBuilder: (context, error, stackTrace) {
                  return Icon(
                    fallbackIcon,
                    color: AppTheme.primaryColor,
                    size: 32,
                  );
                },
              ),
            ),
          ),
          const SizedBox(height: 10),
          Text(
            label,
            style: TextStyle(
              fontSize: 13,
              color: Colors.white.withOpacity(0.8),
            ),
          ),
        ],
      ),
    );
  }
}



import '../../providers/app_provider.dart';
import '../../providers/user_provider.dart';
import '../../app/theme.dart';
import '../../utils/assets.dart';
import '../home/home_screen.dart';
import '../shorts/shorts_screen.dart';
import '../profile/profile_screen.dart';

/// 主布局 - 精确复刻 Vue.js 底部导航
class MainLayout extends StatefulWidget {
  const MainLayout({super.key});

  @override
  State<MainLayout> createState() => _MainLayoutState();
}

class _MainLayoutState extends State<MainLayout> {
  final List<Widget> _screens = [
    const HomeScreen(),
    const ShortsScreen(),
    const Center(child: Text('Soul', style: TextStyle(color: Colors.white))), // 占位
    const Center(child: Text('广场', style: TextStyle(color: Colors.white))), // 占位
    const ProfileScreen(),
  ];

  // 底部导航标签 - 与 Vue 完全一致
  final List<String> _labels = ['首页', '禁区', 'Soul', '广场', '自己'];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<UserProvider>().init();
      context.read<AppProvider>().initAppData();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AppProvider>(
      builder: (context, appProvider, child) {
        return Scaffold(
          backgroundColor: const Color(0xFF0A0A0A),
          body: IndexedStack(
            index: appProvider.currentTabIndex,
            children: _screens,
          ),
          bottomNavigationBar: _buildBottomNav(appProvider),
        );
      },
    );
  }

  /// 底部导航 - 精确复刻 Vue bottom-nav 样式
  Widget _buildBottomNav(AppProvider appProvider) {
    return Container(
      decoration: BoxDecoration(
        // Vue: background: linear-gradient(to top, #0a0a0a 0%, rgba(10, 10, 10, 0.98) 100%)
        gradient: LinearGradient(
          begin: Alignment.bottomCenter,
          end: Alignment.topCenter,
          colors: [
            const Color(0xFF0A0A0A),
            const Color(0xFF0A0A0A).withOpacity(0.98),
          ],
        ),
        // Vue: border-top: 1px solid rgba(255, 255, 255, 0.06)
        border: Border(
          top: BorderSide(
            color: Colors.white.withOpacity(0.06),
            width: 1,
          ),
        ),
      ),
      child: SafeArea(
        top: false,
        child: Padding(
          // Vue: padding-bottom: calc(clamp(2px, 0.8vw, 5px) + env(safe-area-inset-bottom))
          padding: const EdgeInsets.only(top: 6, bottom: 4),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: List.generate(5, (index) {
              // 中间的 Soul 按钮特殊处理
              if (index == 2) {
                return _buildSoulButton(appProvider);
              }
              return _buildNavItem(index, appProvider);
            }),
          ),
        ),
      ),
    );
  }

  /// 普通导航项 - 对应 Vue nav-item
  Widget _buildNavItem(int index, AppProvider appProvider) {
    final isActive = appProvider.currentTabIndex == index;

    return GestureDetector(
      onTap: () => appProvider.setTabIndex(index),
      behavior: HitTestBehavior.opaque,
      child: Container(
        // Vue: padding: clamp(3px, 1vw, 6px) clamp(8px, 3vw, 16px)
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // 图标容器 - Vue: nav-icon-img
            Container(
              // Vue: width: clamp(24px, 7vw, 32px), height: clamp(24px, 7vw, 32px)
              width: 28,
              height: 28,
              alignment: Alignment.center,
              child: Image.asset(
                AppAssets.getNavIcon(index, isActive),
                width: 28,
                height: 28,
                fit: BoxFit.contain,
                errorBuilder: (context, error, stackTrace) {
                  return Icon(
                    _getDefaultIcon(index),
                    color: isActive ? AppTheme.primaryColor : Colors.white.withOpacity(0.45),
                    size: 24,
                  );
                },
              ),
            ),
            // Vue: gap: clamp(1px, 0.5vw, 3px)
            const SizedBox(height: 2),
            // 标签文字 - Vue: nav-label
            isActive
                ? ShaderMask(
                    // Vue: background: linear-gradient(135deg, #c084fc, #818cf8)
                    shaderCallback: (bounds) => const LinearGradient(
                      colors: [Color(0xFFC084FC), Color(0xFF818CF8)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ).createShader(bounds),
                    child: Text(
                      _labels[index],
                      style: const TextStyle(
                        // Vue: font-size: clamp(11px, 3vw, 13px)
                        fontSize: 11,
                        color: Colors.white,
                        // Vue: letter-spacing: 0.5px
                        letterSpacing: 0.5,
                      ),
                    ),
                  )
                : Text(
                    _labels[index],
                    style: TextStyle(
                      fontSize: 11,
                      // Vue: color: rgba(255, 255, 255, 0.45)
                      color: Colors.white.withOpacity(0.45),
                      letterSpacing: 0.5,
                    ),
                  ),
          ],
        ),
      ),
    );
  }

  IconData _getDefaultIcon(int index) {
    switch (index) {
      case 0:
        return Icons.home_outlined;
      case 1:
        return Icons.play_circle_outline;
      case 3:
        return Icons.explore_outlined;
      case 4:
        return Icons.person_outline;
      default:
        return Icons.circle_outlined;
    }
  }

  /// Soul 中间按钮 - 特殊样式
  Widget _buildSoulButton(AppProvider appProvider) {
    final isActive = appProvider.currentTabIndex == 2;

    return GestureDetector(
      onTap: () => _showPublishOptions(),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Soul 图标
            Container(
              width: 28,
              height: 28,
              alignment: Alignment.center,
              child: Image.asset(
                AppAssets.getNavIcon(2, isActive),
                width: 28,
                height: 28,
                fit: BoxFit.contain,
                errorBuilder: (context, error, stackTrace) {
                  return Container(
                    width: 28,
                    height: 28,
                    decoration: BoxDecoration(
                      gradient: AppTheme.primaryGradient,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.add, color: Colors.white, size: 20),
                  );
                },
              ),
            ),
            const SizedBox(height: 2),
            Text(
              _labels[2],
              style: TextStyle(
                fontSize: 11,
                color: isActive
                    ? AppTheme.primaryColor
                    : Colors.white.withOpacity(0.45),
                letterSpacing: 0.5,
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// 发布选项弹窗
  void _showPublishOptions() {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF1A1A1A),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // 拖动条
                Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
                const SizedBox(height: 24),
                // 发布选项
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    _buildPublishOption(
                      AppAssets.publishVideo,
                      '发布视频',
                      Icons.videocam,
                      () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/publish/video');
                      },
                    ),
                    _buildPublishOption(
                      AppAssets.publishImg,
                      '发布短视频',
                      Icons.short_text,
                      () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/publish/short');
                      },
                    ),
                    _buildPublishOption(
                      AppAssets.publishImgText,
                      '发布图文',
                      Icons.image,
                      () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/publish/image');
                      },
                    ),
                  ],
                ),
                const SizedBox(height: 20),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildPublishOption(
    String asset,
    String label,
    IconData fallbackIcon,
    VoidCallback onTap,
  ) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              color: AppTheme.primaryColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(16),
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: Image.asset(
                asset,
                fit: BoxFit.cover,
                errorBuilder: (context, error, stackTrace) {
                  return Icon(
                    fallbackIcon,
                    color: AppTheme.primaryColor,
                    size: 32,
                  );
                },
              ),
            ),
          ),
          const SizedBox(height: 10),
          Text(
            label,
            style: TextStyle(
              fontSize: 13,
              color: Colors.white.withOpacity(0.8),
            ),
          ),
        ],
      ),
    );
  }
}