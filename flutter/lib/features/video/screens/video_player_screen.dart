import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:provider/provider.dart';

import '../../../app/theme.dart';
import '../../../core/providers/video_provider.dart';
import '../../../core/models/video.dart';

class VideoPlayerScreen extends StatefulWidget {
  final int videoId;

  const VideoPlayerScreen({super.key, required this.videoId});

  @override
  State<VideoPlayerScreen> createState() => _VideoPlayerScreenState();
}

class _VideoPlayerScreenState extends State<VideoPlayerScreen> {
  Video? _video;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadVideo();
  }

  Future<void> _loadVideo() async {
    final provider = context.read<VideoProvider>();
    final video = await provider.getVideoDetail(widget.videoId);
    
    if (mounted) {
      setState(() {
        _video = video;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    if (_video == null) {
      return Scaffold(
        appBar: AppBar(),
        body: const Center(
          child: Text('视频不存在'),
        ),
      );
    }

    return Scaffold(
      backgroundColor: Colors.black,
      body: SafeArea(
        child: Column(
          children: [
            // 视频播放器区域
            AspectRatio(
              aspectRatio: 16 / 9,
              child: Container(
                color: Colors.black,
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    // 封面图
                    if (_video!.coverUrl != null)
                      Image.network(
                        _video!.coverUrl!,
                        fit: BoxFit.cover,
                        width: double.infinity,
                      ),
                    
                    // 播放按钮
                    Container(
                      width: 64.w,
                      height: 64.w,
                      decoration: BoxDecoration(
                        color: Colors.black54,
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        Icons.play_arrow,
                        size: 40.w,
                        color: Colors.white,
                      ),
                    ),
                    
                    // 返回按钮
                    Positioned(
                      top: 8.h,
                      left: 8.w,
                      child: IconButton(
                        icon: const Icon(Icons.arrow_back, color: Colors.white),
                        onPressed: () => Navigator.pop(context),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            
            // 视频信息
            Expanded(
              child: Container(
                color: AppTheme.backgroundColor,
                child: ListView(
                  padding: EdgeInsets.all(16.w),
                  children: [
                    // 标题
                    Text(
                      _video!.title,
                      style: TextStyle(
                        fontSize: 18.sp,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                    SizedBox(height: 8.h),
                    
                    // 统计信息
                    Row(
                      children: [
                        _buildStat(Icons.play_arrow, _video!.viewCountText),
                        SizedBox(width: 16.w),
                        _buildStat(Icons.thumb_up_outlined, '${_video!.likeCount}'),
                        SizedBox(width: 16.w),
                        _buildStat(Icons.comment_outlined, '${_video!.commentCount}'),
                      ],
                    ),
                    SizedBox(height: 16.h),
                    
                    // 操作按钮
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        _buildActionButton(Icons.thumb_up_outlined, '点赞'),
                        _buildActionButton(Icons.star_outline, '收藏'),
                        _buildActionButton(Icons.share_outlined, '分享'),
                        _buildActionButton(Icons.download_outlined, '下载'),
                      ],
                    ),
                    SizedBox(height: 16.h),
                    
                    // 描述
                    if (_video!.description != null) ...[
                      Text(
                        '简介',
                        style: TextStyle(
                          fontSize: 16.sp,
                          fontWeight: FontWeight.bold,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                      SizedBox(height: 8.h),
                      Text(
                        _video!.description!,
                        style: TextStyle(
                          fontSize: 14.sp,
                          color: AppTheme.textSecondary,
                        ),
                      ),
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
        Icon(icon, size: 16.w, color: AppTheme.textSecondary),
        SizedBox(width: 4.w),
        Text(
          value,
          style: TextStyle(
            fontSize: 12.sp,
            color: AppTheme.textSecondary,
          ),
        ),
      ],
    );
  }

  Widget _buildActionButton(IconData icon, String label) {
    return Column(
      children: [
        Icon(icon, size: 24.w, color: AppTheme.textPrimary),
        SizedBox(height: 4.h),
        Text(
          label,
          style: TextStyle(
            fontSize: 12.sp,
            color: AppTheme.textSecondary,
          ),
        ),
      ],
    );
  }
}
