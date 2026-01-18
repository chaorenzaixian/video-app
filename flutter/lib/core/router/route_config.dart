import 'package:flutter/material.dart';

/// 路由类型枚举
enum RouteType {
  /// Flutter 原生页面
  native,
  /// WebView 页面
  webview,
}

/// 路由配置类
class RouteConfig {
  /// 路由类型
  final RouteType type;
  
  /// 原生页面构建器（仅 native 类型使用）
  final Widget Function(Map<String, dynamic> args)? builder;
  
  /// WebView 页面路径（仅 webview 类型使用）
  final String? webPath;
  
  /// 页面标题
  final String? title;

  RouteConfig({
    required this.type,
    this.builder,
    this.webPath,
    this.title,
  }) : assert(
    (type == RouteType.native && builder != null) ||
    (type == RouteType.webview && webPath != null),
    'Native routes must have a builder, WebView routes must have a webPath',
  );

  /// 是否为原生路由
  bool get isNative => type == RouteType.native;

  /// 是否为 WebView 路由
  bool get isWebView => type == RouteType.webview;
}
