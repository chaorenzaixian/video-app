import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/user.dart';

class UserProvider extends ChangeNotifier {
  final ApiService _api = ApiService();
  
  User? _user;
  bool _isLoading = false;
  
  User? get user => _user;
  bool get isLoading => _isLoading;
  bool get isVip => _user?.isVip ?? false;
  int get vipLevel => _user?.vipLevel ?? 0;
  
  Future<void> loadUser() async {
    _isLoading = true;
    notifyListeners();
    
    try {
      final response = await _api.getCurrentUser();
      if (response.statusCode == 200) {
        _user = User.fromJson(response.data);
      }
    } catch (e) {
      debugPrint('加载用户信息失败: $e');
    }
    
    _isLoading = false;
    notifyListeners();
  }
  
  Future<bool> updateProfile(Map<String, dynamic> data) async {
    try {
      final response = await _api.updateProfile(data);
      if (response.statusCode == 200) {
        await loadUser();
        return true;
      }
    } catch (e) {
      debugPrint('更新资料失败: $e');
    }
    return false;
  }
  
  void clearUser() {
    _user = null;
    notifyListeners();
  }
}
