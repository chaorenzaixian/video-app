import 'package:flutter/material.dart';
import 'package:vod_app/core/router/route_config.dart';
import 'package:vod_app/features/webview/screens/webview_page.dart';
import 'package:vod_app/screens/home/home_screen.dart';
import 'package:vod_app/screens/shorts/shorts_screen.dart';
import 'package:vod_app/screens/video/video_player_screen.dart';
import 'package:vod_app/screens/search/search_screen.dart';
import 'package:vod_app/screens/auth/login_screen.dart';

/// 路由未找到异常
class RouteNotFoundException implements Exception {
  final String route;
  RouteNotFoundException(this.route);
  
  @override
  String toString() => 'Route not found: $route';
}

/// 混合路由器 - 管理原生页面和 WebView 页面的导航
class HybridRouter {
  /// Web 基础 URL
  static const String webBaseUrl = 'http://38.47.218.137';

  /// 路由映射表
  static final Map<String, RouteConfig> routes = {
    // 原生页面
    '/home': RouteConfig(
      type: RouteType.native,
      builder: (_) => const HomeScreen(),
      title: '首页',
    ),
    '/shorts': RouteConfig(
      type: RouteType.native,
      builder: (_) => const ShortsScreen(),
      title: '短视频',
    ),
    '/video': RouteConfig(
      type: RouteType.native,
      builder: (args) => VideoPlayerScreen(
        videoId: args['videoId'] as int? ?? 0,
      ),
      title: '视频播放',
    ),
    '/search': RouteConfig(
      type: RouteType.native,
      builder: (_) => const SearchScreen(),
      title: '搜索',
    ),
    '/login': RouteConfig(
      type: RouteType.native,
      builder: (_) => const LoginScreen(),
      title: '登录',
    ),

    // WebView 页面
    '/vip': RouteConfig(
      type: RouteType.webview,
      webPath: '/user/vip',
      title: 'VIP',
    ),
    '/profile': RouteConfig(
      type: RouteType.webview,
      webPath: '/user/profile',
      title: '个人中心',
    ),
    '/community': RouteConfig(
      type: RouteType.webview,
      webPath: '/user/community',
      title: '社区',
    ),
    '/settings': RouteConfig(
      type: RouteType.webview,
      webPath: '/user/settings',
      title: '设置',
    ),
    '/history': RouteConfig(
      type: RouteType.webview,
      webPath: '/user/history',
      title: '观看历史',
    ),
    '/favorites': RouteConfig(
      type: RouteType.webview,
      webPath: '/user/favorites',
      title: '我的收藏',
    ),
    '/recharge': RouteConfig(
      type: RouteType.webview,
      webPath: '/user/recharge',
      title: '充值',
    ),
    '/invite': RouteConfig(
      type: RouteType.webview,
      webPath: '/user/invite',
      title: '邀请好友',
    ),
    '/service': RouteConfig(
      type: RouteType.webview,
      webPath: '/user/service',
      title: '客服',
    ),
  };

  /// 获取 WebView 页面完整 URL
  static String getWebPageUrl(String path) {
    if (path.startsWith('http')) return path;
    return '$webBaseUrl$path';
  }

  /// 判断路由类型
  static RouteType? getRouteType(String route) {
    return routes[route]?.type;
  }

  /// 判断是否为原生路由
  static bool isNativeRoute(String route) {
    return routes[route]?.type == RouteType.native;
  }

  /// 判断是否为 WebView 路由
  static bool isWebViewRoute(String route) {
    return routes[route]?.type == RouteType.webview;
  }

  /// 导航到指定路由
  static Future<T?> navigateTo<T>(
    BuildContext context,
    String route, {
    Map<String, dynamic>? params,
  }) async {
    final config = routes[route];
    if (config == null) {
      throw RouteNotFoundException(route);
    }

    if (config.type == RouteType.native) {
      return Navigator.push<T>(
        context,
        MaterialPageRoute(
          builder: (_) => config.builder!(params ?? {}),
        ),
      );
    } else {
      return Navigator.push<T>(
        context,
        MaterialPageRoute(
          builder: (_) => WebViewPage(
            url: getWebPageUrl(config.webPath!),
            title: config.title,
          ),
        ),
      );
    }
  }

  /// 替换当前路由
  static Future<T?> replaceTo<T>(
    BuildContext context,
    String route, {
    Map<String, dynamic>? params,
  }) async {
    final config = routes[route];
    if (config == null) {
      throw RouteNotFoundException(route);
    }

    if (config.type == RouteType.native) {
      return Navigator.pushReplacement<T, dynamic>(
        context,
        MaterialPageRoute(
          builder: (_) => config.builder!(params ?? {}),
        ),
      );
    } else {
      return Navigator.pushReplacement<T, dynamic>(
        context,
        MaterialPageRoute(
          builder: (_) => WebViewPage(
            url: getWebPageUrl(config.webPath!),
            title: config.title,
          ),
        ),
      );
    }
  }
}
