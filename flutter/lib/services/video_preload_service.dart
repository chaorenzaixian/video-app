import 'package:flutter_cache_manager/flutter_cache_manager.dart';
import '../core/services/api_service.dart';

/// 视频预加载服务
class VideoPreloadService {
  static final VideoPreloadService _instance = VideoPreloadService._internal();
  factory VideoPreloadService() => _instance;
  VideoPreloadService._internal();

  // 自定义缓存管理器
  static final CacheManager _cacheManager = CacheManager(
    Config(
      'video_cache',
      stalePeriod: const Duration(days: 7),
      maxNrOfCacheObjects: 50,
      repo: JsonCacheInfoRepository(databaseName: 'video_cache'),
      fileService: HttpFileService(),
    ),
  );

  // 预加载队列
  final List<String> _preloadQueue = [];
  bool _isPreloading = false;

  /// 预加载视频封面
  Future<void> preloadCovers(List<String?> coverUrls) async {
    for (final url in coverUrls) {
      if (url != null && url.isNotEmpty) {
        final fullUrl = ApiService.getFullImageUrl(url);
        try {
          await _cacheManager.downloadFile(fullUrl);
        } catch (e) {
          // 忽略预加载错误
        }
      }
    }
  }

  /// 预加载视频（仅预加载前几秒）
  Future<void> preloadVideo(String? videoUrl) async {
    if (videoUrl == null || videoUr