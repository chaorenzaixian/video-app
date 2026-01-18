import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:vod_app/services/api_service.dart';
import 'package:vod_app/core/models/js_bridge_message.dart';

/// JavaScript 桥接 - 处理 Flutter 和 WebView 之间的双向通信
class JSBridge {
  final WebViewController controller;
  final Function(String route, Map<String, dynamic>? params)? onNavigate;
  final Function(String token)? onTokenUpdate;
  final Function(Map<String, dynamic> data)? onShare;

  JSBridge({
    required this.controller,
    this.onNavigate,
    this.onTokenUpdate,
    this.onShare,
  });

  /// 初始化 JS Bridge
  Future<void> init() async {
    await controller.addJavaScriptChannel(
      'FlutterBridge',
      onMessageReceived: _handleMessage,
    );
  }

  /// 处理来自 WebView 的消息
  void _handleMessage(JavaScriptMessage message) {
    try {
      final data = jsonDecode(message.message) as Map<String, dynamic>;
      final bridgeMessage = JSBridgeMessage.fromJson(data);
      
      debugPrint('📱 JSBridge 收到消息: ${bridgeMessage.action}');

      switch (bridgeMessage.action) {
        case 'navigate':
          final route = bridgeMessage.data?['route'] as String?;
          final params = bridgeMessage.data?['params'] as Map<String, dynamic>?;
          if (route != null) {
            onNavigate?.call(route, params);
          }
          break;
        case 'updateToken':
          final token = bridgeMessage.data?['token'] as String?;
          if (token != null) {
            onTokenUpdate?.call(token);
          }
          break;
        case 'share':
          final shareData = bridgeMessage.data;
          if (shareData != null) {
            onShare?.call(shareData);
          }
          break;
        case 'getDeviceInfo':
          _sendDeviceInfo();
          break;
        default:
          debugPrint('📱 JSBridge 未知消息类型: ${bridgeMessage.action}');
      }
    } catch (e) {
      debugPrint('📱 JSBridge 消息解析失败: $e');
      _sendError('MESSAGE_PARSE_ERROR', e.toString());
    }
  }

  /// 调用 WebView 中的 JavaScript 方法
  Future<void> callJS(String method, [Map<String, dynamic>? params]) async {
    final paramsJson = params != null ? jsonEncode(params) : '{}';
    final script = 'window.$method && window.$method($paramsJson)';
    try {
      await controller.runJavaScript(script);
    } catch (e) {
      debugPrint('📱 JSBridge 调用 JS 失败: $e');
    }
  }

  /// 发送设备信息到 WebView
  Future<void> _sendDeviceInfo() async {
    final deviceInfo = {
      'platform': Platform.isIOS ? 'ios' : 'android',
      'deviceId': ApiService.getDeviceId() ?? '',
      'appVersion': '1.0.0',
    };
    await callJS('onDeviceInfo', deviceInfo);
  }

  /// 发送错误信息到 WebView
  Future<void> _sendError(String code, String message) async {
    await callJS('onError', {
      'code': code,
      'message': message,
    });
  }
}
