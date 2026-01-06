import 'package:shared_preferences/shared_preferences.dart';
import 'dart:math';

class StorageService {
  static late SharedPreferences _prefs;
  
  static const String _tokenKey = 'access_token';
  static const String _refreshTokenKey = 'refresh_token';
  static const String _deviceIdKey = 'device_id';
  static const String _userKey = 'user_data';
  
  static Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
    
    // 确保有设备 ID
    if (getDeviceId() == null) {
      await _generateDeviceId();
    }
  }
  
  static Future<void> _generateDeviceId() async {
    final random = Random.secure();
    final values = List<int>.generate(32, (i) => random.nextInt(256));
    final deviceId = values.map((e) => e.toRadixString(16).padLeft(2, '0')).join();
    await _prefs.setString(_deviceIdKey, deviceId);
  }
  
  // ========== Token 管理 ==========
  
  static String? getToken() {
    return _prefs.getString(_tokenKey);
  }
  
  static Future<void> saveToken(String token) async {
    await _prefs.setString(_tokenKey, token);
  }
  
  static String? getRefreshToken() {
    return _prefs.getString(_refreshTokenKey);
  }
  
  static Future<void> saveRefreshToken(String token) async {
    await _prefs.setString(_refreshTokenKey, token);
  }
  
  static String? getDeviceId() {
    return _prefs.getString(_deviceIdKey);
  }
  
  static Future<void> clearAuth() async {
    await _prefs.remove(_tokenKey);
    await _prefs.remove(_refreshTokenKey);
    await _prefs.remove(_userKey);
  }
  
  // ========== 用户数据 ==========
  
  static String? getUserData() {
    return _prefs.getString(_userKey);
  }
  
  static Future<void> saveUserData(String userData) async {
    await _prefs.setString(_userKey, userData);
  }
  
  // ========== 通用方法 ==========
  
  static Future<void> setString(String key, String value) async {
    await _prefs.setString(key, value);
  }
  
  static String? getString(String key) {
    return _prefs.getString(key);
  }
  
  static Future<void> setBool(String key, bool value) async {
    await _prefs.setBool(key, value);
  }
  
  static bool? getBool(String key) {
    return _prefs.getBool(key);
  }
  
  static Future<void> remove(String key) async {
    await _prefs.remove(key);
  }
}
