import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/video.dart';
import '../models/category.dart';

class VideoProvider extends ChangeNotifier {
  final ApiService _api = ApiService();
  
  List<Video> _videos = [];
  List<Video> _shorts = [];
  List<Category> _categories = [];
  bool _isLoading = false;
  bool _hasMore = true;
  int _currentPage = 1;
  
  List<Video> get videos => _videos;
  List<Video> get shorts => _shorts;
  List<Category> get categories => _categories;
  bool get isLoading => _isLoading;
  bool get hasMore => _hasMore;
  
  Future<void> loadCategories() async {
    try {
      final response = await _api.getCategories();
      if (response.statusCode == 200) {
        _categories = (response.data as List)
            .map((e) => Category.fromJson(e))
            .toList();
        notifyListeners();
      }
    } catch (e) {
      debugPrint('加载分类失败: $e');
    }
  }
  
  Future<void> loadVideos({
    int? categoryId,
    String? search,
    String? sortBy,
    bool refresh = false,
  }) async {
    if (_isLoading) return;
    
    if (refresh) {
      _currentPage = 1;
      _hasMore = true;
    }
    
    if (!_hasMore && !refresh) return;
    
    _isLoading = true;
    notifyListeners();
    
    try {
      final response = await _api.getVideos(
        page: _currentPage,
        categoryId: categoryId,
        search: search,
        sortBy: sortBy,
      );
      
      if (response.statusCode == 200) {
        final data = response.data;
        final items = (data['items'] as List)
            .map((e) => Video.fromJson(e))
            .toList();
        
        if (refresh) {
          _videos = items;
        } else {
          _videos.addAll(items);
        }
        
        _hasMore = items.length >= 20;
        _currentPage++;
      }
    } catch (e) {
      debugPrint('加载视频失败: $e');
    }
    
    _isLoading = false;
    notifyListeners();
  }
  
  Future<void> loadShorts({bool refresh = false}) async {
    if (_isLoading) return;
    
    _isLoading = true;
    notifyListeners();
    
    try {
      final response = await _api.getShorts(page: refresh ? 1 : _currentPage);
      
      if (response.statusCode == 200) {
        final data = response.data;
        final items = (data['items'] as List)
            .map((e) => Video.fromJson(e))
            .toList();
        
        if (refresh) {
          _shorts = items;
        } else {
          _shorts.addAll(items);
        }
      }
    } catch (e) {
      debugPrint('加载短视频失败: $e');
    }
    
    _isLoading = false;
    notifyListeners();
  }
  
  Future<Video?> getVideoDetail(int videoId) async {
    try {
      final response = await _api.getVideoDetail(videoId);
      if (response.statusCode == 200) {
        return Video.fromJson(response.data);
      }
    } catch (e) {
      debugPrint('获取视频详情失败: $e');
    }
    return null;
  }
  
  Future<bool> likeVideo(int videoId) async {
    try {
      final response = await _api.likeVideo(videoId);
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
  
  Future<bool> favoriteVideo(int videoId) async {
    try {
      final response = await _api.favoriteVideo(videoId);
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
