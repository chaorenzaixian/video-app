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
    // 获取状态栏高度
    final statusBarHeight = MediaQuery.of(context).padding.top;
    
    return Scaffold(
      backgroundColor: Colors.black,
      body: Column(
        children: [
          // 状态栏占位（黑色背景）
          Container(
            height: statusBarHeight,
            color: Colors.black,
          ),
          // WebView 全屏显示
          const Expanded(
            child: WebViewPage(
              url: 'http://38.47.218.137/',
              showAppBar: false,
              enableEdgeSwipeBack: true,
            ),
          ),
        ],
      ),
    );
  }
}
