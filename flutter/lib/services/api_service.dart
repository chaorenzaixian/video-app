import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/foundation.dart';

class ApiService {
  static late Dio _dio;
  static late SharedPreferences _prefs;
  static bool _initialized = false;
  
  // API 基础地址 - 使用真实服务器地址
  static const String baseUrl = 'http://38.47.218.137:8000/api/v1';
  static const String serverUrl = 'http://38.47.218.137:8000';
  
  static Future<void> init() async {
    if (_initialized) return;
    
    _prefs = await SharedPreferences.getInstance();
    
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 60),
      receiveTimeout: const Duration(seconds: 60),
      headers: {
        'Content-Type': 'application/json',
      },
    ));
    
    // 请求拦截器 - 添加 Token
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        final token = _prefs.getString('token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (error, handler) async {
        if (error.response?.statusCode == 401) {
          // Token过期，用 device_id 自动重新登录
          final deviceId = _prefs.getString('device_id');
          if (deviceId != null) {
            try {
              debugPrint('🔄 Token过期，自动重新登录...');
              final newDio = Dio(BaseOptions(baseUrl: baseUrl));
              final response = await newDio.post('/auth/guest/register', data: {
                'device_id': deviceId,
              });
              
              if (response.data['access_token'] != null) {
                // 保存新 Token
                await _prefs.setString('token', response.data['access_token']);
                debugPrint('✅ 自动重新登录成功');
                
                // 用新 Token 重试原请求
                final opts = error.requestOptions;
                opts.headers['Authorization'] = 'Bearer ${response.data['access_token']}';
                final retryResponse = await _dio.fetch(opts);
                return handler.resolve(retryResponse);
              }
            } catch (e) {
              debugPrint('❌ 自动重新登录失败: $e');
            }
          }
        }
        return handler.next(error);
      },
    ));
    
    _initialized = true;
  }
  
  static Future<void> _ensureInit() async {
    if (!_initialized) {
      await init();
    }
  }
  
  static Future<void> setToken(String token) async {
    await _ensureInit();
    await _prefs.setString('token', token);
  }
  
  static Future<void> clearToken() async {
    await _ensureInit();
    await _prefs.remove('token');
  }
  
  static String? getToken() {
    if (!_initialized) return null;
    return _prefs.getString('token');
  }
  
  static Future<void> setDeviceId(String deviceId) async {
    await _ensureInit();
    await _prefs.setString('device_id', deviceId);
  }
  
  static String? getDeviceId() {
    if (!_initialized) return null;
    return _prefs.getString('device_id');
  }
  
  // GET 请求
  static Future<Response> get(
    String path, {
    Map<String, dynamic>? params,
  }) async {
    await _ensureInit();
    debugPrint('📡 GET: $baseUrl$path params: $params');
    try {
      final response = await _dio.get(path, queryParameters: params);
      debugPrint('📡 响应状态: ${response.statusCode}');
      return response;
    } catch (e) {
      debugPrint('📡 请求失败: $e');
      rethrow;
    }
  }
  
  // POST 请求
  static Future<Response> post(
    String path, {
    dynamic data,
  }) async {
    await _ensureInit();
    debugPrint('📡 POST: $baseUrl$path data: $data');
    try {
      final response = await _dio.post(path, data: data);
      debugPrint('📡 响应状态: ${response.statusCode}');
      return response;
    } catch (e) {
      debugPrint('📡 POST 失败: $e');
      rethrow;
    }
  }
  
  // PUT 请求
  static Future<Response> put(
    String path, {
    dynamic data,
  }) async {
    await _ensureInit();
    return _dio.put(path, data: data);
  }
  
  // DELETE 请求
  static Future<Response> delete(String path) async {
    await _ensureInit();
    return _dio.delete(path);
  }
  
  // 上传文件
  static Future<Response> upload(
    String path,
    String filePath, {
    String fieldName = 'file',
    Map<String, dynamic>? data,
  }) async {
    await _ensureInit();
    final formData = FormData.fromMap({
      fieldName: await MultipartFile.fromFile(filePath),
      ...?data,
    });
    return _dio.post(path, data: formData);
  }
  
  /// 获取完整的图片URL
  static String getFullImageUrl(String? url) {
    if (url == null || url.isEmpty) return '';
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url;
    }
    if (url.startsWith('/')) {
      return '$serverUrl$url';
    }
    return '$serverUrl/$url';
  }
  
  /// 获取完整的视频URL
  static String getFullVideoUrl(String? url) {
    if (url == null || url.isEmpty) return '';
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url;
    }
    if (url.startsWith('/')) {
      return '$serverUrl$url';
    }
    return '$serverUrl/$url';
  }
}
