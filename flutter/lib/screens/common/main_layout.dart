import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../features/webview/screens/webview_page.dart';

/// 主布局 - 全屏 WebView（无底部导航）
class MainLayout extends StatefulWidget {
  const MainLayout({super.key});

  @override
  State<MainLayout> createState() => _MainLayoutState();
}

class _MainLayoutState extends State<MainLayout> {
  @override
  void initState() {
    super.initState();
    // 设置状态栏为黑色背景，白色图标
    SystemChrome.setSystemUIOverlayStyle(
      const SystemUiOverlayStyle(
        statusBarColor: Colors.black,
        statusBarIconBrightness: Brightness.light,
        statusBarBrightness: Brightness.dark,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    // 获取底部安全区域高度
    final bottomPadding = MediaQuery.of(context).padding.bottom;
    
    return Scaffold(
      backgroundColor: Colors.black,
      // 使用SafeArea只处理顶部，底部由网页的底部导航处理
      body: SafeArea(
        top: true,
        bottom: false, // 底部不使用SafeArea，让网页自己处理
        child: const WebViewPage(
          url: 'http://38.47.218.137/',
          showAppBar: false,
          enableEdgeSwipeBack: true,
        ),
      ),
    );
  }
}
