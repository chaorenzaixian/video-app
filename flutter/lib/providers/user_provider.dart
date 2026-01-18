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
  
  String _generateDeviceId() {
    final random = Random();
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    final randomPart = List.generate(16, (i) => random.nextInt(16).toRadixString(16)).join('');
    return 'flutter_$timestamp$randomPart';
  }
  
  Future<void> init() async {
    final token = ApiService.getToken();
    if (token != null) {
      await fetchUser();
    } else {
      await guestRegister();
    }
  }
  
  Future<bool> guestRegister() async {
    try {
      _isLoading = true;
      notifyListeners();
      
      String deviceId = ApiService.getDeviceId() ?? _generateDeviceId();
      await ApiService.setDeviceId(deviceId);
      
      final response = await ApiService.post('/auth/guest/register', data: {
        'device_id': deviceId,
      });
      final data = response.data;
      
      if (data['access_token'] != null) {
        await ApiService.setToken(data['access_token']);
        await fetchUser();
        return true;
      }
    } catch (e) {
      debugPrint('游客注册失败: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
    return false;
  }
  
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
  
  Future<void> fetchUser() async {
    try {
      final response = await ApiService.get('/users/me');
      _user = User.fromJson(response.data);
      _isLoggedIn = true;
      notifyListeners();
    } catch (e) {
      debugPrint('获取用户信息失败: $e');
      _isLoggedIn = false;
      notifyListeners();
    }
  }
  
  Future<void> logout() async {
    await ApiService.clearToken();
    _user = null;
    _isLoggedIn = false;
    notifyListeners();
    await guestRegister();
  }
  
  Future<bool> updateProfile({String? nickname, String? avatar}) async {
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
  
  Future<void> refreshCoins() async {
    await fetchUser();
  }
}
