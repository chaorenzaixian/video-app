import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/foundation.dart';

class ApiService {
  static late Dio _dio;
  static late SharedPreferences _prefs;
  static bool _initialized = false;
  
  // API 基础地址 - 通过 ADB reverse 端口转发
  // 模拟器和 Chrome 都可以用 localhost
  static const String baseUrl = 'http://localhost:8000/api/v1';
  static const String serverUrl = 'http://localhost:8000';  // 用于图片URL
  
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
      onError: (error, handler) {
        // 处理401错误 - 登录过期
        if (error.response?.statusCode == 401) {
          // 不要直接删除token，让UserProvider处理
        }
        return handler.next(error);
      },
    ));
    
    _initialized = true;
  }
  
  // 确保初始化
  static Future<void> _ensureInit() async {
    if (!_initialized) {
      await init();
    }
  }
  
  // 设置 Token
  static Future<void> setToken(String token) async {
    await _ensureInit();
    await _prefs.setString('token', token);
  }
  
  // 清除 Token
  static Future<void> clearToken() async {
    await _ensureInit();
    await _prefs.remove('token');
  }
  
  // 获取 Token
  static String? getToken() {
    if (!_initialized) return null;
    return _prefs.getString('token');
  }
  
  // 设置设备ID
  static Future<void> setDeviceId(String deviceId) async {
    await _ensureInit();
    await _prefs.setString('device_id', deviceId);
  }
  
  // 获取设备ID
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
  /// 处理相对路径和绝对路径
  static String getFullImageUrl(String? url) {
    if (url == null || url.isEmpty) return '';
    
    // 如果已经是完整URL，直接返回
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url;
    }
    
    // 相对路径，拼接服务器地址
    if (url.startsWith('/')) {
      return '$serverUrl$url';
    }
    
    return '$serverUrl/$url';
  }
}



import 'package:flutter/foundation.dart';

class ApiService {
  static late Dio _dio;
  static late SharedPreferences _prefs;
  static bool _initialized = false;
  
  // API 基础地址 - 通过 ADB reverse 端口转发
  // 模拟器和 Chrome 都可以用 localhost
  static const String baseUrl = 'http://localhost:8000/api/v1';
  static const String serverUrl = 'http://localhost:8000';  // 用于图片URL
  
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
      onError: (error, handler) {
        // 处理401错误 - 登录过期
        if (error.response?.statusCode == 401) {
          // 不要直接删除token，让UserProvider处理
        }
        return handler.next(error);
      },
    ));
    
    _initialized = true;
  }
  
  // 确保初始化
  static Future<void> _ensureInit() async {
    if (!_initialized) {
      await init();
    }
  }
  
  // 设置 Token
  static Future<void> setToken(String token) async {
    await _ensureInit();
    await _prefs.setString('token', token);
  }
  
  // 清除 Token
  static Future<void> clearToken() async {
    await _ensureInit();
    await _prefs.remove('token');
  }
  
  // 获取 Token
  static String? getToken() {
    if (!_initialized) return null;
    return _prefs.getString('token');
  }
  
  // 设置设备ID
  static Future<void> setDeviceId(String deviceId) async {
    await _ensureInit();
    await _prefs.setString('device_id', deviceId);
  }
  
  // 获取设备ID
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
  /// 处理相对路径和绝对路径
  static String getFullImageUrl(String? url) {
    if (url == null || url.isEmpty) return '';
    
    // 如果已经是完整URL，直接返回
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url;
    }
    
    // 相对路径，拼接服务器地址
    if (url.startsWith('/')) {
      return '$serverUrl$url';
    }
    
    return '$serverUrl/$url';
  }
}