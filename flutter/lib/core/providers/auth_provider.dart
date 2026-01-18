import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/storage_service.dart';
import '../models/user.dart';

class AuthProvider extends ChangeNotifier {
  final ApiService _api = ApiService();
  
  User? _user;
  bool _isLoading = false;
  String? _error;
  bool _initialized = false;
  
  User? get user => _user;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isLoggedIn {
    try {
      return StorageService.getToken() != null;
    } catch (e) {
      return false;
    }
  }
  bool get isVip => _user?.isVip ?? false;
  
  // 延迟初始化，避免构造函数中调用异步方法
  Future<void> init() async {
    if (_initialized) return;
    _initialized = true;
    
    if (isLoggedIn) {
      await _loadUser();
    }
  }
  
  Future<void> _loadUser() async {
    try {
      final response = await _api.getCurrentUser();
      if (response.statusCode == 200) {
        _user = User.fromJson(response.data);
        notifyListeners();
      }
    } catch (e) {
      debugPrint('加载用户信息失败: $e');
    }
  }
  
  Future<bool> login(String username, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      final response = await _api.login(username, password);
      
      if (response.statusCode == 200) {
        final data = response.data;
        await StorageService.saveToken(data['access_token']);
        await StorageService.saveRefreshToken(data['refresh_token']);
        await _loadUser();
        _isLoading = false;
        notifyListeners();
        return true;
      }
    } catch (e) {
      _error = _parseError(e);
    }
    
    _isLoading = false;
    notifyListeners();
    return false;
  }
  
  Future<bool> register(String username, String email, String password, {String? inviteCode}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      final response = await _api.register(username, email, password, inviteCode: inviteCode);
      if (response.statusCode == 200) {
        return await login(username, password);
      }
    } catch (e) {
      _error = _parseError(e);
    }
    
    _isLoading = false;
    notifyListeners();
    return false;
  }
  
  Future<bool> guestLogin() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      final deviceId = StorageService.getDeviceId();
      if (deviceId == null) {
        _error = '设备ID获取失败';
        _isLoading = false;
        notifyListeners();
        return false;
      }
      
      final response = await _api.guestRegister(deviceId);
      
      if (response.statusCode == 200) {
        final data = response.data;
        await StorageService.saveToken(data['access_token']);
        await StorageService.saveRefreshToken(data['refresh_token']);
        await _loadUser();
        _isLoading = false;
        notifyListeners();
        return true;
      }
    } catch (e) {
      _error = _parseError(e);
    }
    
    _isLoading = false;
    notifyListeners();
    return false;
  }
  
  Future<void> logout() async {
    await StorageService.clearAuth();
    _user = null;
    notifyListeners();
  }
  
  Future<void> refreshUser() async {
    await _loadUser();
  }
  
  String _parseError(dynamic e) {
    if (e is Exception) {
      return e.toString().replaceAll('Exception: ', '');
    }
    return '操作失败，请重试';
  }
}
