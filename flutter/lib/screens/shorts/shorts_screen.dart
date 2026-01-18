import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:cached_network_image/cached_network_image.dart';
import '../../app/theme.dart';
import '../../models/video.dart';
import '../../services/api_service.dart';

/// 短视频/禁区页面
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

  @override
  void initState() {
    super.initState();
    _fetchShorts();
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  Future<void> _fetchShorts() async {
    if (_isLoading) return;
    
    setState(() => _isLoading = true);
    
    try {
      final response = await ApiService.get('/shorts', params: {
        'page': 1,
        'page_size': 20,
      });
      
      final data = response.data;
      List<dynamic> items = [];
      if (data is Map) {
        items = data['items'] ?? data['videos'] ?? [];
      } else if (data is List) {
        items = data;
      }
      
      setState(() {
        _shorts = items.cast<Map<String, dynamic>>();
      });
    } catch (e) {
      debugPrint('获取短视频失败: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _onPageChanged(int index) {
    setState(() {
      _currentIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading && _shorts.isEmpty) {
      return Scaffold(
        backgroundColor: AppTheme.backgroundColor,
        body: const Center(
          child: CircularProgressIndicator(color: AppTheme.primaryColor),
        ),
      );
    }
    
    if (_shorts.isEmpty) {
      return Scaffold(
        backgroundColor: AppTheme.backgroundColor,
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.video_library_outlined, 
                color: Colors.white.withOpacity(0.3), 
                size: 64,
              ),
              const SizedBox(height: 16),
              Text(
                '暂无短视频',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.5),
                  fontSize: 16,
                ),
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: _fetchShorts,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primaryColor,
                ),
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
        itemBuilder: (context, index) {
          return _buildShortItem(index);
        },
      ),
    );
  }

  Widget _buildShortItem(int index) {
    final video = _shorts[index];
    final coverUrl = video['cover_url'] ?? video['cover'];
    final fullCoverUrl = coverUrl != null ? ApiService.getFullImageUrl(coverUrl) : null;
    
    return Stack(
      fit: StackFit.expand,
      children: [
        // 背景封面
        GestureDetector(
          onTap: () {
            if (kIsWeb) {
              Navigator.pushNamed(context, '/video/${video['id']}');
            }
          },
          child: fullCoverUrl != null
              ? CachedNetworkImage(
                  imageUrl: fullCoverUrl,
                  fit: BoxFit.cover,
                  placeholder: (_, __) => Container(
                    color: Colors.black,
                    child: const Center(
                      child: CircularProgressIndicator(color: Colors.white),
                    ),
                  ),
                  errorWidget: (_, __, ___) => Container(
                    color: AppTheme.surfaceColor,
                    child: Icon(
                      Icons.image_outlined,
                      color: Colors.white.withOpacity(0.3),
                      size: 64,
                    ),
                  ),
                )
              : Container(
                  color: AppTheme.surfaceColor,
                  child: Icon(
                    Icons.video_library_outlined,
                    color: Colors.white.withOpacity(0.3),
                    size: 64,
                  ),
                ),
        ),
        
        // 渐变遮罩
        Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                Colors.transparent,
                Colors.transparent,
                Colors.black.withOpacity(0.7),
              ],
              stops: const [0.0, 0.5, 1.0],
            ),
          ),
        ),
        
        // 播放按钮
        if (kIsWeb)
          Center(
            child: Container(
              width: 70,
              height: 70,
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.5),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.play_arrow,
                size: 45,
                color: Colors.white,
              ),
            ),
          ),
        
        // 右侧操作栏
        Positioned(
          right: 12,
          bottom: 150,
          child: _buildActionBar(video),
        ),
        
        // 底部信息
        Positioned(
          left: 16,
          right: 70,
          bottom: 40,
          child: _buildVideoInfo(video),
        ),
        
        // 顶部
        Positioned(
          top: 0,
          left: 0,
          right: 0,
          child: SafeArea(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    '禁区',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
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
        _buildActionButton(
          icon: Icons.favorite_border,
          label: _formatCount(video['like_count'] ?? 0),
        ),
        const SizedBox(height: 20),
        _buildActionButton(
          icon: Icons.chat_bubble_outline,
          label: _formatCount(video['comment_count'] ?? 0),
        ),
        const SizedBox(height: 20),
        _buildActionButton(
          icon: Icons.star_border,
          label: _formatCount(video['favorite_count'] ?? 0),
        ),
        const SizedBox(height: 20),
        _buildActionButton(
          icon: Icons.share,
          label: '分享',
        ),
      ],
    );
  }

  Widget _buildAvatar(Map<String, dynamic> video) {
    final avatarUrl = video['uploader_avatar'];
    final fullAvatarUrl = avatarUrl != null ? ApiService.getFullImageUrl(avatarUrl) : null;
    
    return Stack(
      clipBehavior: Clip.none,
      children: [
        Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(color: Colors.white, width: 2),
          ),
          child: ClipOval(
            child: fullAvatarUrl != null
                ? CachedNetworkImage(
                    imageUrl: fullAvatarUrl,
                    fit: BoxFit.cover,
                    errorWidget: (_, __, ___) => Container(
                      color: AppTheme.surfaceColor,
                      child: const Icon(Icons.person, color: Colors.white),
                    ),
                  )
                : Container(
                    color: AppTheme.surfaceColor,
                    child: const Icon(Icons.person, color: Colors.white),
                  ),
          ),
        ),
        Positioned(
          bottom: -8,
          left: 0,
          right: 0,
          child: Center(
            child: Container(
              width: 20,
              height: 20,
              decoration: const BoxDecoration(
                color: Colors.red,
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.add, color: Colors.white, size: 14),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildActionButton({
    required IconData icon,
    required String label,
    Color color = Colors.white,
    VoidCallback? onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 30),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(color: color, fontSize: 12),
          ),
        ],
      ),
    );
  }

  Widget _buildVideoInfo(Map<String, dynamic> video) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          '@${video['uploader_name'] ?? '用户'}',
          style: const TextStyle(
            color: Colors.white,
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          video['title'] ?? '',
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: TextStyle(
            color: Colors.white.withOpacity(0.9),
            fontSize: 14,
            height: 1.4,
          ),
        ),
      ],
    );
  }

  String _formatCount(int count) {
    if (count >= 10000) {
      return '${(count / 10000).toStringAsFixed(1)}w';
    } else if (count >= 1000) {
      return '${(count / 1000).toStringAsFixed(1)}k';
    }
    return count.toString();
  }
}
