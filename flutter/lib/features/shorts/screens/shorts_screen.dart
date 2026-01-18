import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';
import 'package:cached_network_image/cached_network_image.dart';

import '../../../app/theme.dart';
import '../../../core/services/api_service.dart';

/// 短视频页面 - 抖音风格上下滑动
class ShortsScreen extends StatefulWidget {
  const ShortsScreen({super.key});

  @override
  State<ShortsScreen> createState() => _ShortsScreenState();
}

class _ShortsScreenState extends State<ShortsScreen> {
  final PageController _pageController = PageController();
  List<Map<String, dynamic>> _shorts = [];
  int _currentIndex = 0;
  bool _isLoading = false;
  
  // 预加载的播放器控制器
  final Map<int, VideoPlayerController> _controllers = {};
  final Map<int, bool> _isPlaying = {};

  @override
  void initState() {
    super.initState();
    _fetchShorts();
  }

  @override
  void dispose() {
    _pageController.dispose();
    for (final controller in _controllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> _fetchShorts() async {
    if (_isLoading) return;
    setState(() => _isLoading = true);
    
    try {
      final response = await ApiService.get('/shorts', params: {'page': 1, 'page_size': 20});
      final data = response.data;
      List<dynamic> items = [];
      
      if (data is Map) {
        items = data['items'] ?? data['videos'] ?? [];
      } else if (data is List) {
        items = data;
      }
      
      setState(() => _shorts = items.cast<Map<String, dynamic>>());
      _preloadVideos(0);
    } catch (e) {
      debugPrint('获取短视频失败: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _preloadVideos(int currentIndex) {
    // 预加载当前和前后各1个视频
    for (int i = currentIndex - 1; i <= currentIndex + 1; i++) {
      if (i >= 0 && i < _shorts.length && !_controllers.containsKey(i)) {
        _createController(i);
      }
    }
    
    // 释放距离太远的控制器
    final keysToRemove = <int>[];
    for (final key in _controllers.keys) {
      if ((key - currentIndex).abs() > 2) keysToRemove.add(key);
    }
    for (final key in keysToRemove) {
      _controllers[key]?.dispose();
      _controllers.remove(key);
      _isPlaying.remove(key);
    }
  }

  Future<void> _createController(int index) async {
    if (index < 0 || index >= _shorts.length) return;
    
    final video = _shorts[index];
    final hlsUrl = video['hls_url'] ?? video['video_url'];
    if (hlsUrl == null || hlsUrl.isEmpty) return;
    
    final fullUrl = ApiService.getFullVideoUrl(hlsUrl);
    final controller = VideoPlayerController.networkUrl(Uri.parse(fullUrl));
    _controllers[index] = controller;
    _isPlaying[index] = false;
    
    try {
      await controller.initialize();
      controller.setLooping(true);
      
      if (index == _currentIndex && mounted) {
        controller.play();
        _isPlaying[index] = true;
      }
      if (mounted) setState(() {});
    } catch (e) {
      debugPrint('视频初始化失败: $e');
    }
  }

  void _onPageChanged(int index) {
    // 暂停旧视频
    _controllers[_currentIndex]?.pause();
    _isPlaying[_currentIndex] = false;
    
    setState(() => _currentIndex = index);
    
    // 播放新视频
    final controller = _controllers[index];
    if (controller != null && controller.value.isInitialized) {
      controller.play();
      _isPlaying[index] = true;
    }
    
    _preloadVideos(index);
  }

  void _togglePlay(int index) {
    final controller = _controllers[index];
    if (controller == null || !controller.value.isInitialized) return;
    
    if (controller.value.isPlaying) {
      controller.pause();
      _isPlaying[index] = false;
    } else {
      controller.play();
      _isPlaying[index] = true;
    }
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading && _shorts.isEmpty) {
      return Scaffold(
        backgroundColor: Colors.black,
        body: const Center(child: CircularProgressIndicator(color: AppTheme.primaryColor)),
      );
    }
    
    if (_shorts.isEmpty) {
      return Scaffold(
        backgroundColor: Colors.black,
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.video_library_outlined, color: Colors.white.withOpacity(0.3), size: 64),
              const SizedBox(height: 16),
              Text('暂无短视频', style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 16)),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: _fetchShorts,
                style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryColor),
                child: const Text('刷新'),
              ),
            ],
          ),
        ),
      );
    }
    
    return Scaffold(
      backgroundColor: Colors.black,
      body: PageView.builder(
        controller: _pageController,
        scrollDirection: Axis.vertical,
        onPageChanged: _onPageChanged,
        itemCount: _shorts.length,
        itemBuilder: (context, index) => _buildShortItem(index),
      ),
    );
  }

  Widget _buildShortItem(int index) {
    final video = _shorts[index];
    final coverUrl = video['cover_url'];
    final controller = _controllers[index];
    final isPlaying = _isPlaying[index] ?? false;
    final isInitialized = controller?.value.isInitialized ?? false;
    
    return Stack(
      fit: StackFit.expand,
      children: [
        // 视频播放器或封面
        GestureDetector(
          onTap: () => _togglePlay(index),
          child: isInitialized
              ? AspectRatio(
                  aspectRatio: controller!.value.aspectRatio,
                  child: VideoPlayer(controller),
                )
              : (coverUrl != null
                  ? CachedNetworkImage(
                      imageUrl: ApiService.getFullImageUrl(coverUrl),
                      fit: BoxFit.cover,
                      placeholder: (_, __) => Container(color: Colors.black),
                      errorWidget: (_, __, ___) => Container(color: Colors.black),
                    )
                  : Container(color: Colors.black)),
        ),
        
        // 渐变遮罩
        Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [Colors.transparent, Colors.transparent, Colors.black.withOpacity(0.7)],
              stops: const [0.0, 0.5, 1.0],
            ),
          ),
        ),
        
        // 暂停时显示播放按钮
        if (!isPlaying)
          Center(
            child: Container(
              width: 70, height: 70,
              decoration: BoxDecoration(color: Colors.black.withOpacity(0.5), shape: BoxShape.circle),
              child: const Icon(Icons.play_arrow, size: 45, color: Colors.white),
            ),
          ),
        
        // 加载指示器
        if (!isInitialized && index == _currentIndex)
          const Center(child: CircularProgressIndicator(color: Colors.white)),
        
        // 右侧操作栏
        Positioned(right: 12, bottom: 150, child: _buildActionBar(video)),
        
        // 底部信息
        Positioned(left: 16, right: 70, bottom: 40, child: _buildVideoInfo(video)),
        
        // 顶部
        Positioned(
          top: 0, left: 0, right: 0,
          child: SafeArea(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  GestureDetector(
                    onTap: () => Navigator.pop(context),
                    child: const Icon(Icons.arrow_back, color: Colors.white, size: 26),
                  ),
                  const Text('短视频', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                  GestureDetector(
                    onTap: () => Navigator.pushNamed(context, '/search'),
                    child: const Icon(Icons.search, color: Colors.white, size: 26),
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildActionBar(Map<String, dynamic> video) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        _buildAvatar(video),
        const SizedBox(height: 24),
        _buildActionButton(icon: Icons.favorite_border, label: _formatCount(video['like_count'] ?? 0)),
        const SizedBox(height: 20),
        _buildActionButton(icon: Icons.chat_bubble_outline, label: _formatCount(video['comment_count'] ?? 0)),
        const SizedBox(height: 20),
        _buildActionButton(icon: Icons.star_border, label: _formatCount(video['favorite_count'] ?? 0)),
        const SizedBox(height: 20),
        _buildActionButton(icon: Icons.share, label: '分享'),
      ],
    );
  }

  Widget _buildAvatar(Map<String, dynamic> video) {
    final avatarUrl = video['uploader_avatar'];
    return Stack(
      clipBehavior: Clip.none,
      children: [
        Container(
          width: 48, height: 48,
          decoration: BoxDecoration(shape: BoxShape.circle, border: Border.all(color: Colors.white, width: 2)),
          child: ClipOval(
            child: avatarUrl != null
                ? CachedNetworkImage(
                    imageUrl: ApiService.getFullImageUrl(avatarUrl),
                    fit: BoxFit.cover,
                    errorWidget: (_, __, ___) => Container(color: AppTheme.surfaceColor, child: const Icon(Icons.person, color: Colors.white)),
                  )
                : Container(color: AppTheme.surfaceColor, child: const Icon(Icons.person, color: Colors.white)),
          ),
        ),
        Positioned(
          bottom: -8, left: 0, right: 0,
          child: Center(
            child: Container(
              width: 20, height: 20,
              decoration: const BoxDecoration(color: Colors.red, shape: BoxShape.circle),
              child: const Icon(Icons.add, color: Colors.white, size: 14),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildActionButton({required IconData icon, required String label, Color color = Colors.white, VoidCallback? onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 30),
          const SizedBox(height: 4),
          Text(label, style: TextStyle(color: color, fontSize: 12)),
        ],
      ),
    );
  }

  Widget _buildVideoInfo(Map<String, dynamic> video) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text('@${video['uploader_name'] ?? '用户'}', style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        Text(video['title'] ?? '', maxLines: 2, overflow: TextOverflow.ellipsis, style: TextStyle(color: Colors.white.withOpacity(0.9), fontSize: 14, height: 1.4)),
      ],
    );
  }

  String _formatCount(int count) {
    if (count >= 10000) return '${(count / 10000).toStringAsFixed(1)}w';
    if (count >= 1000) return '${(count / 1000).toStringAsFixed(1)}k';
    return count.toString();
  }
}
