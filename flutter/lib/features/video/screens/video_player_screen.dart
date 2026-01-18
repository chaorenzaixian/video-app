import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:video_player/video_player.dart';
import 'package:chewie/chewie.dart';
import 'package:cached_network_image/cached_network_image.dart';

import '../../../app/theme.dart';
import '../../../core/services/api_service.dart';

class VideoPlayerScreen extends StatefulWidget {
  final int videoId;

  const VideoPlayerScreen({super.key, required this.videoId});

  @override
  State<VideoPlayerScreen> createState() => _VideoPlayerScreenState();
}

class _VideoPlayerScreenState extends State<VideoPlayerScreen> {
  Map<String, dynamic>? _video;
  bool _isLoading = true;
  String? _error;
  VideoPlayerController? _videoController;
  ChewieController? _chewieController;
  bool _isLiked = false;
  bool _isFavorited = false;

  @override
  void initState() {
    super.initState();
    _loadVideo();
  }

  Future<void> _loadVideo() async {
    try {
      final response = await ApiService.get('/videos/${widget.videoId}');
      final data = response.data;
      
      if (mounted) {
        setState(() {
          _video = data;
          _isLoading = false;
          _isLiked = data['is_liked'] ?? false;
          _isFavorited = data['is_favorited'] ?? false;
        });
        _initPlayer();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = '加载失败: $e';
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _initPlayer() async {
    if (_video == null) return;
    
    final hlsUrl = _video!['hls_url'];
    if (hlsUrl == null || hlsUrl.isEmpty) {
      setState(() => _error = '视频地址不存在');
      return;
    }

    final fullUrl = ApiService.getFullVideoUrl(hlsUrl);
    
    // video_player 原生支持 HLS
    _videoController = VideoPlayerController.networkUrl(Uri.parse(fullUrl));
    
    try {
      await _videoController!.initialize();
      
      _chewieController = ChewieController(
        videoPlayerController: _videoController!,
        autoPlay: true,
        looping: false,
        aspectRatio: _videoController!.value.aspectRatio,
        allowFullScreen: true,
        allowMuting: true,
        showControls: true,
        materialProgressColors: ChewieProgressColors(
          playedColor: AppTheme.primaryColor,
          handleColor: AppTheme.primaryColor,
          bufferedColor: Colors.white24,
          backgroundColor: Colors.white12,
        ),
        placeholder: _buildPlaceholder(),
        errorBuilder: (context, errorMessage) {
          return Center(
            child: Text(
              '播放失败: $errorMessage',
              style: const TextStyle(color: Colors.white),
            ),
          );
        },
      );
      
      if (mounted) setState(() {});
    } catch (e) {
      if (mounted) {
        setState(() => _error = '播放器初始化失败: $e');
      }
    }
  }

  Widget _buildPlaceholder() {
    final coverUrl = _video?['cover_url'];
    if (coverUrl == null) return Container(color: Colors.black);
    
    return CachedNetworkImage(
      imageUrl: ApiService.getFullImageUrl(coverUrl),
      fit: BoxFit.cover,
      errorWidget: (_, __, ___) => Container(color: Colors.black),
    );
  }

  @override
  void dispose() {
    _chewieController?.dispose();
    _videoController?.dispose();
    super.dispose();
  }

  Future<void> _toggleLike() async {
    try {
      await ApiService.post('/social/videos/${widget.videoId}/like');
      setState(() => _isLiked = !_isLiked);
    } catch (e) {
      debugPrint('点赞失败: $e');
    }
  }

  Future<void> _toggleFavorite() async {
    try {
      await ApiService.post('/social/videos/${widget.videoId}/favorite');
      setState(() => _isFavorited = !_isFavorited);
    } catch (e) {
      debugPrint('收藏失败: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        backgroundColor: Colors.black,
        body: const Center(
          child: CircularProgressIndicator(color: AppTheme.primaryColor),
        ),
      );
    }

    if (_error != null || _video == null) {
      return Scaffold(
        backgroundColor: AppTheme.backgroundColor,
        appBar: AppBar(backgroundColor: Colors.transparent, elevation: 0),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.error_outline, size: 64, color: Colors.red.withOpacity(0.5)),
              SizedBox(height: 16.h),
              Text(_error ?? '视频不存在',
                style: TextStyle(color: Colors.white70, fontSize: 16.sp)),
              SizedBox(height: 24.h),
              ElevatedButton(
                onPressed: () {
                  setState(() { _isLoading = true; _error = null; });
                  _loadVideo();
                },
                child: const Text('重试'),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: Colors.black,
      body: SafeArea(
        child: Column(
          children: [
            // 视频播放器
            AspectRatio(
              aspectRatio: 16 / 9,
              child: Stack(
                children: [
                  if (_chewieController != null)
                    Chewie(controller: _chewieController!)
                  else
                    Container(
                      color: Colors.black,
                      child: const Center(
                        child: CircularProgressIndicator(color: Colors.white),
                      ),
                    ),
                  // 返回按钮
                  Positioned(
                    top: 8, left: 8,
                    child: IconButton(
                      icon: const Icon(Icons.arrow_back, color: Colors.white),
                      onPressed: () => Navigator.pop(context),
                    ),
                  ),
                ],
              ),
            ),
            
            // 视频信息
            Expanded(
              child: Container(
                color: AppTheme.backgroundColor,
                child: ListView(
                  padding: EdgeInsets.all(16.w),
                  children: [
                    Text(_video!['title'] ?? '无标题',
                      style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.bold, color: Colors.white)),
                    SizedBox(height: 12.h),
                    
                    Row(
                      children: [
                        _buildStat(Icons.play_arrow, _formatCount(_video!['view_count'] ?? 0)),
                        SizedBox(width: 16.w),
                        _buildStat(Icons.thumb_up_outlined, _formatCount(_video!['like_count'] ?? 0)),
                        SizedBox(width: 16.w),
                        _buildStat(Icons.comment_outlined, _formatCount(_video!['comment_count'] ?? 0)),
                        const Spacer(),
                        if (_video!['is_vip_only'] == true)
                          Container(
                            padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 2.h),
                            decoration: BoxDecoration(
                              gradient: const LinearGradient(colors: [Color(0xFFFFD700), Color(0xFFFFA500)]),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text('VIP', style: TextStyle(fontSize: 10.sp, fontWeight: FontWeight.bold, color: Colors.black)),
                          ),
                      ],
                    ),
                    SizedBox(height: 20.h),
                    
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        _buildActionButton(_isLiked ? Icons.thumb_up : Icons.thumb_up_outlined, '点赞', isActive: _isLiked, onTap: _toggleLike),
                        _buildActionButton(_isFavorited ? Icons.star : Icons.star_outline, '收藏', isActive: _isFavorited, onTap: _toggleFavorite),
                        _buildActionButton(Icons.share_outlined, '分享', onTap: () {}),
                        _buildActionButton(Icons.download_outlined, '下载', onTap: () {}),
                      ],
                    ),
                    SizedBox(height: 20.h),
                    Divider(color: Colors.white.withOpacity(0.1)),
                    SizedBox(height: 12.h),
                    
                    if (_video!['description'] != null && _video!['description'].isNotEmpty) ...[
                      Text('简介', style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.bold, color: Colors.white)),
                      SizedBox(height: 8.h),
                      Text(_video!['description'], style: TextStyle(fontSize: 14.sp, color: Colors.white70, height: 1.5)),
                    ],
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStat(IconData icon, String value) {
    return Row(
      children: [
        Icon(icon, size: 16.w, color: Colors.white54),
        SizedBox(width: 4.w),
        Text(value, style: TextStyle(fontSize: 12.sp, color: Colors.white54)),
      ],
    );
  }

  Widget _buildActionButton(IconData icon, String label, {bool isActive = false, VoidCallback? onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Icon(icon, size: 26.w, color: isActive ? AppTheme.primaryColor : Colors.white),
          SizedBox(height: 4.h),
          Text(label, style: TextStyle(fontSize: 12.sp, color: isActive ? AppTheme.primaryColor : Colors.white70)),
        ],
      ),
    );
  }

  String _formatCount(int count) {
    if (count >= 10000) return '${(count / 10000).toStringAsFixed(1)}万';
    if (count >= 1000) return '${(count / 1000).toStringAsFixed(1)}千';
    return count.toString();
  }
}
