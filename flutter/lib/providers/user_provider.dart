import 'dart:math';
import 'package:flutter/material.dart';
import '../models/user.dart';
import '../services/api_service.dart';

class UserProvider with ChangeNotifier {
  User? _user;
  bool _isLoading = false;
  bool _isLoggedIn = false;
  
  User? get user => _user;
  bool get isLoading => _isLoading;
  bool get isLoggedIn => _isLoggedIn;
  bool get isVip => _user?.isVip ?? false;
  int get coins => _user?.coins ?? 0;
  int get points => _user?.points ?? 0;
  
  // 生成设备ID (模拟)
  String _generateDeviceId() {
    final random = Random();
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    final randomPart = List.generate(16, (i) => random.nextInt(16).toRadixString(16)).join('');
    return 'flutter_web_$timestamp$randomPart';
  }
  
  // 初始化 - 检查登录状态
  Future<void> init() async {
    final token = ApiService.getToken();
    if (token != null) {
      await fetchUser();
    } else {
      // 自动游客注册
      await guestRegister();
    }
  }
  
  // 游客注册 - 对应 stores/user.js 的 autoRegisterGuest
  Future<bool> guestRegister() async {
    try {
      _isLoading = true;
      notifyListeners();
      
      // 生成或获取设备ID
      String deviceId = ApiService.getDeviceId() ?? _generateDeviceId();
      await ApiService.setDeviceId(deviceId);
      
      final response = await ApiService.post('/auth/guest/register', data: {
        'device_id': deviceId,
      });
      final data = response.data;
      
      if (data['access_token'] != null) {
        await ApiService.setToken(data['access_token']);
        
        // 立即获取用户信息
        await fetchUser();
        return true;
      }
    } catch (e) {
      debugPrint('游客注册失败: $e');
      // 即使注册失败，也可以作为游客使用一些功能
    } finally {
      _isLoading = false;
      notifyListeners();
    }
    return false;
  }
  
  // 登录
  Future<bool> login(String username, String password) async {
    try {
      _isLoading = true;
      notifyListeners();
      
      final response = await ApiService.post('/auth/login', data: {
        'username': username,
        'password': password,
      });
      
      final data = response.data;
      if (data['access_token'] != null) {
        await ApiService.setToken(data['access_token']);
        _user = User.fromJson(data['user']);
        _isLoggedIn = true;
        notifyListeners();
        return true;
      }
    } catch (e) {
      debugPrint('登录失败: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
    return false;
  }
  
  // 获取用户信息
  Future<void> fetchUser() async {
    try {
      final response = await ApiService.get('/users/me');
      _user = User.fromJson(response.data);
      _isLoggedIn = true;
      notifyListeners();
    } catch (e) {
      debugPrint('获取用户信息失败: $e');
      // 不要清除token，可能只是暂时的网络问题
      _isLoggedIn = false;
      notifyListeners();
    }
  }
  
  // 退出登录
  Future<void> logout() async {
    await ApiService.clearToken();
    _user = null;
    _isLoggedIn = false;
    notifyListeners();
    
    // 重新游客注册
    await guestRegister();
  }
  
  // 更新用户信息
  Future<bool> updateProfile({
    String? nickname,
    String? avatar,
  }) async {
    try {
      final response = await ApiService.put('/users/me', data: {
        if (nickname != null) 'nickname': nickname,
        if (avatar != null) 'avatar': avatar,
      });
      _user = User.fromJson(response.data);
      notifyListeners();
      return true;
    } catch (e) {
      debugPrint('更新用户信息失败: $e');
      return false;
    }
  }
  
  // 刷新金币
  Future<void> refreshCoins() async {
    await fetchUser();
  }
}



import '../models/user.dart';
import '../services/api_service.dart';

class UserProvider with ChangeNotifier {
  User? _user;
  bool _isLoading = false;
  bool _isLoggedIn = false;
  
  User? get user => _user;
  bool get isLoading => _isLoading;
  bool get isLoggedIn => _isLoggedIn;
  bool get isVip => _user?.isVip ?? false;
  int get coins => _user?.coins ?? 0;
  int get points => _user?.points ?? 0;
  
  // 生成设备ID (模拟)
  String _generateDeviceId() {
    final random = Random();
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    final randomPart = List.generate(16, (i) => random.nextInt(16).toRadixString(16)).join('');
    return 'flutter_web_$timestamp$randomPart';
  }
  
  // 初始化 - 检查登录状态
  Future<void> init() async {
    final token = ApiService.getToken();
    if (token != null) {
      await fetchUser();
    } else {
      // 自动游客注册
      await guestRegister();
    }
  }
  
  // 游客注册 - 对应 stores/user.js 的 autoRegisterGuest
  Future<bool> guestRegister() async {
    try {
      _isLoading = true;
      notifyListeners();
      
      // 生成或获取设备ID
      String deviceId = ApiService.getDeviceId() ?? _generateDeviceId();
      await ApiService.setDeviceId(deviceId);
      
      final response = await ApiService.post('/auth/guest/register', data: {
        'device_id': deviceId,
      });
      final data = response.data;
      
      if (data['access_token'] != null) {
        await ApiService.setToken(data['access_token']);
        
        // 立即获取用户信息
        await fetchUser();
        return true;
      }
    } catch (e) {
      debugPrint('游客注册失败: $e');
      // 即使注册失败，也可以作为游客使用一些功能
    } finally {
      _isLoading = false;
      notifyListeners();
    }
    return false;
  }
  
  // 登录
  Future<bool> login(String username, String password) async {
    try {
      _isLoading = true;
      notifyListeners();
      
      final response = await ApiService.post('/auth/login', data: {
        'username': username,
        'password': password,
      });
      
      final data = response.data;
      if (data['access_token'] != null) {
        await ApiService.setToken(data['access_token']);
        _user = User.fromJson(data['user']);
        _isLoggedIn = true;
        notifyListeners();
        return true;
      }
    } catch (e) {
      debugPrint('登录失败: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
    return false;
  }
  
  // 获取用户信息
  Future<void> fetchUser() async {
    try {
      final response = await ApiService.get('/users/me');
      _user = User.fromJson(response.data);
      _isLoggedIn = true;
      notifyListeners();
    } catch (e) {
      debugPrint('获取用户信息失败: $e');
      // 不要清除token，可能只是暂时的网络问题
      _isLoggedIn = false;
      notifyListeners();
    }
  }
  
  // 退出登录
  Future<void> logout() async {
    await ApiService.clearToken();
    _user = null;
    _isLoggedIn = false;
    notifyListeners();
    
    // 重新游客注册
    await guestRegister();
  }
  
  // 更新用户信息
  Future<bool> updateProfile({
    String? nickname,
    String? avatar,
  }) async {
    try {
      final response = await ApiService.put('/users/me', data: {
        if (nickname != null) 'nickname': nickname,
        if (avatar != null) 'avatar': avatar,
      });
      _user = User.fromJson(response.data);
      notifyListeners();
      return true;
    } catch (e) {
      debugPrint('更新用户信息失败: $e');
      return false;
    }
  }
  
  // 刷新金币
  Future<void> refreshCoins() async {
    await fetchUser();
  }
}