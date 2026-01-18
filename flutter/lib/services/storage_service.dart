import 'package:shared_preferences/shared_preferences.dart';

/// 本地存储服务
class StorageService {
  static late SharedPreferences _prefs;
  static bool _initialized = false;

  /// 初始化存储服务
  static Future<void> init() async {
    if (_initialized) return;
    _prefs = await SharedPreferences.getInstance();
    _initialized = true;
  }

  /// 获取字符串
  static String? getString(String key) {
    if (!_initialized) return null;
    return _prefs.getString(key);
  }

  /// 设置字符串
  static Future<bool> setString(String key, String value) async {
    if (!_initialized) await init();
    return _prefs.setString(key, value);
  }

  /// 获取布尔值
  static bool? getBool(String key) {
    if (!_initialized) return null;
    return _prefs.getBool(key);
  }

  /// 设置布尔值
  static Future<bool> setBool(String key, bool value) async {
    if (!_initialized) await init();
    return _prefs.setBool(key, value);
  }

  /// 获取整数
  static int? getInt(String key) {
    if (!_initialized) return null;
    return _prefs.getInt(key);
  }

  /// 设置整数
  static Future<bool> setInt(String key, int value) async {
    if (!_initialized) await init();
    return _prefs.setInt(key, value);
  }

  /// 删除键
  static Future<bool> remove(String key) async {
    if (!_initialized) await init();
    return _prefs.remove(key);
  }

  /// 清除所有数据
  static Future<bool> clear() async {
    if (!_initialized) await init();
    return _prefs.clear();
  }
}
