import 'package:flutter/material.dart';

/// 应用全局状态管理
class AppProvider extends ChangeNotifier {
  bool _isLoading = false;
  String? _error;
  int _currentTabIndex = 0;
  
  bool get isLoading => _isLoading;
  String? get error => _error;
  int get currentTabIndex => _currentTabIndex;
  
  void setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }
  
  void setError(String? error) {
    _error = error;
    notifyListeners();
  }
  
  void setCurrentTabIndex(int index) {
    _currentTabIndex = index;
    notifyListeners();
  }
  
  void clearError() {
    _error = null;
    notifyListeners();
  }
}
