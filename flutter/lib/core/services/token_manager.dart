import 'dart:async';
import 'package:vod_app/services/api_service.dart';

/// Token 管理器 - 负责 Flutter 和 WebView 之间的 Token 同步
class TokenManager {
  static final TokenManager _instance = TokenManager._internal();
  factory TokenManager() => _instance;
  TokenManager._internal();

  final _tokenController = StreamController<String?>.broadcast();
  
  /// Token 变化的 Stream，用于监听 Token 更新
  Stream<String?> get tokenStream => _tokenController.stream;

  /// 获取当前 Token
  String? get currentToken => ApiService.getToken();

  /// 设置 Token（同时通知所有监听者）
  Future<void> setToken(String token) async {
    await ApiService.setToken(token);
    _tokenController.add(token);
  }

  /// 清除 Token
  Future<void> clearToken() async {
    await ApiService.clearToken();
    _tokenController.add(null);
  }

  /// 生成注入 Token 的 JavaScript 代码
  /// 用于在 WebView 加载完成后注入 Token 到 localStorage
  String generateTokenInjectionScript() {
    final token = currentToken;
    if (token == null || token.isEmpty) return '';
    return '''
      (function() {
        try {
          // 保存token到localStorage
          localStorage.setItem('token', '$token');
          localStorage.setItem('access_token', '$token');
          
          // 检查是否需要刷新页面（如果当前在登录页）
          const path = window.location.pathname;
          if (path.includes('/login') || path.includes('/register')) {
            console.log('Token injected, redirecting to home...');
            window.location.href = '/';
          } else {
            console.log('Token injected from Flutter');
          }
        } catch(e) {
          console.error('Token injection error:', e);
        }
      })();
    ''';
  }

  /// 释放资源
  void dispose() {
    _tokenController.close();
  }
}
