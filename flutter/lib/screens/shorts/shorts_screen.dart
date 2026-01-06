import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:cached_network_image/cached_network_image.dart';
import '../../app/theme.dart';
import '../../models/video.dart';
import '../../services/api_service.dart';

/// 短视频/禁区页面 - 精确匹配 Web 版本
/// 在 Web 上显示封面图，在移动端播放视频
class ShortsScreen extends StatefulWidget {
  const ShortsScreen({super.key});

  @override
  State<ShortsScreen> createState() => _ShortsScreenState();
}

class _ShortsScreenState extends State<ShortsScreen> {
  final PageController _pageController = PageController();
  List<ShortVideo> _shorts = [];
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
      final shorts = (data['items'] ?? data['videos'] ?? [])
          .map<ShortVideo>((json) => ShortVideo.fromJson(json))
          .toList();
      
      setState(() {
        _shorts = shorts;
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
    final coverUrl = video.cover != null ? ApiService.getFullImageUrl(video.cover!) : null;
    
    return Stack(
      fit: StackFit.expand,
      children: [
        // 背景 - 封面图（Web 用封面代替视频）
        GestureDetector(
          onTap: () {
            // 在 Web 上点击跳转到视频详情
            if (kIsWeb) {
              Navigator.pushNamed(context, '/video/${video.id}');
            }
          },
          child: coverUrl != null
              ? CachedNetworkImage(
                  imageUrl: coverUrl,
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
        
        // 播放按钮（Web 模式显示）
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
        
        // 顶部安全区域
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

  Widget _buildActionBar(ShortVideo video) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // 头像
        _buildAvatar(video),
        const SizedBox(height: 24),
        
        // 点赞
        _buildActionButton(
          icon: video.isLiked ? Icons.favorite : Icons.favorite_border,
          label: _formatCount(video.likeCount),
          color: video.isLiked ? Colors.red : Colors.white,
          onTap: () {},
        ),
        const SizedBox(height: 20),
        
        // 评论
        _buildActionButton(
          icon: Icons.chat_bubble_outline,
          label: _formatCount(video.commentCount),
          onTap: () {},
        ),
        const SizedBox(height: 20),
        
        // 收藏
        _buildActionButton(
          icon: video.isFavorited ? Icons.star : Icons.star_border,
          label: _formatCount(video.favoriteCount),
          color: video.isFavorited ? AppTheme.vipGold : Colors.white,
          onTap: () {},
        ),
        const SizedBox(height: 20),
        
        // 分享
        _buildActionButton(
          icon: Icons.share,
          label: '分享',
          onTap: () {},
        ),
      ],
    );
  }

  Widget _buildAvatar(ShortVideo video) {
    final avatarUrl = video.creatorAvatar != null 
        ? ApiService.getFullImageUrl(video.creatorAvatar!) 
        : null;
    
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
            child: avatarUrl != null
                ? CachedNetworkImage(
                    imageUrl: avatarUrl,
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
        // 关注按钮
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

  Widget _buildVideoInfo(ShortVideo video) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        // 作者名
        Row(
          children: [
            Text(
              '@${video.creatorName ?? '用户'}',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        
        // 标题
        Text(
          video.title,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: TextStyle(
            color: Colors.white.withOpacity(0.9),
            fontSize: 14,
            height: 1.4,
          ),
        ),
        
        // 音乐信息（如果有）
        if (video.description != null && video.description!.isNotEmpty) ...[
          const SizedBox(height: 10),
          Row(
            children: [
              const Icon(Icons.music_note, color: Colors.white, size: 14),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  video.description!,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.7),
                    fontSize: 13,
                  ),
                ),
              ),
            ],
          ),
        ],
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



import 'package:cached_network_image/cached_network_image.dart';
import '../../app/theme.dart';
import '../../models/video.dart';
import '../../services/api_service.dart';

/// 短视频/禁区页面 - 精确匹配 Web 版本
/// 在 Web 上显示封面图，在移动端播放视频
class ShortsScreen extends StatefulWidget {
  const ShortsScreen({super.key});

  @override
  State<ShortsScreen> createState() => _ShortsScreenState();
}

class _ShortsScreenState extends State<ShortsScreen> {
  final PageController _pageController = PageController();
  List<ShortVideo> _shorts = [];
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
      final shorts = (data['items'] ?? data['videos'] ?? [])
          .map<ShortVideo>((json) => ShortVideo.fromJson(json))
          .toList();
      
      setState(() {
        _shorts = shorts;
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
    final coverUrl = video.cover != null ? ApiService.getFullImageUrl(video.cover!) : null;
    
    return Stack(
      fit: StackFit.expand,
      children: [
        // 背景 - 封面图（Web 用封面代替视频）
        GestureDetector(
          onTap: () {
            // 在 Web 上点击跳转到视频详情
            if (kIsWeb) {
              Navigator.pushNamed(context, '/video/${video.id}');
            }
          },
          child: coverUrl != null
              ? CachedNetworkImage(
                  imageUrl: coverUrl,
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
        
        // 播放按钮（Web 模式显示）
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
        
        // 顶部安全区域
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

  Widget _buildActionBar(ShortVideo video) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // 头像
        _buildAvatar(video),
        const SizedBox(height: 24),
        
        // 点赞
        _buildActionButton(
          icon: video.isLiked ? Icons.favorite : Icons.favorite_border,
          label: _formatCount(video.likeCount),
          color: video.isLiked ? Colors.red : Colors.white,
          onTap: () {},
        ),
        const SizedBox(height: 20),
        
        // 评论
        _buildActionButton(
          icon: Icons.chat_bubble_outline,
          label: _formatCount(video.commentCount),
          onTap: () {},
        ),
        const SizedBox(height: 20),
        
        // 收藏
        _buildActionButton(
          icon: video.isFavorited ? Icons.star : Icons.star_border,
          label: _formatCount(video.favoriteCount),
          color: video.isFavorited ? AppTheme.vipGold : Colors.white,
          onTap: () {},
        ),
        const SizedBox(height: 20),
        
        // 分享
        _buildActionButton(
          icon: Icons.share,
          label: '分享',
          onTap: () {},
        ),
      ],
    );
  }

  Widget _buildAvatar(ShortVideo video) {
    final avatarUrl = video.creatorAvatar != null 
        ? ApiService.getFullImageUrl(video.creatorAvatar!) 
        : null;
    
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
            child: avatarUrl != null
                ? CachedNetworkImage(
                    imageUrl: avatarUrl,
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
        // 关注按钮
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

  Widget _buildVideoInfo(ShortVideo video) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        // 作者名
        Row(
          children: [
            Text(
              '@${video.creatorName ?? '用户'}',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        
        // 标题
        Text(
          video.title,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: TextStyle(
            color: Colors.white.withOpacity(0.9),
            fontSize: 14,
            height: 1.4,
          ),
        ),
        
        // 音乐信息（如果有）
        if (video.description != null && video.description!.isNotEmpty) ...[
          const SizedBox(height: 10),
          Row(
            children: [
              const Icon(Icons.music_note, color: Colors.white, size: 14),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  video.description!,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.7),
                    fontSize: 13,
                  ),
                ),
              ),
            ],
          ),
        ],
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