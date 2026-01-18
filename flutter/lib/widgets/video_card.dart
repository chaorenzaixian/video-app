import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../app/theme.dart';
import '../models/video.dart';
import '../services/api_service.dart';

/// 视频卡片 - 精确匹配 Web .video-card 样式
class VideoCard extends StatelessWidget {
  final Video video;
  final int gridMode; // 1=单列, 2=双列
  
  const VideoCard({
    super.key, 
    required this.video,
    this.gridMode = 2,
  });

  @override
  Widget build(BuildContext context) {
    final coverUrl = video.cover != null ? ApiService.getFullImageUrl(video.cover!) : '';
    
    return GestureDetector(
      onTap: () {
        Navigator.pushNamed(context, '/video/${video.id}');
      },
      child: Container(
        decoration: BoxDecoration(
          color: Colors.transparent,
          borderRadius: BorderRadius.circular(6),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 封面区域 - 16:9 比例
            AspectRatio(
              aspectRatio: 16 / 9,
              child: Container(
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(gridMode == 1 ? 8 : 6),
                ),
                clipBehavior: Clip.antiAlias,
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    // 封面图片
                    coverUrl.isNotEmpty
                        ? CachedNetworkImage(
                            imageUrl: coverUrl,
                            fit: BoxFit.cover,
                            placeholder: (_, __) => Container(
                              color: const Color(0xFF1A1A1A),
                              child: const Center(
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: AppTheme.primaryColor,
                                ),
                              ),
                            ),
                            errorWidget: (_, __, ___) => Container(
                              color: const Color(0xFF1A1A1A),
                              child: Icon(
                                Icons.image_outlined,
                                color: Colors.white.withOpacity(0.2),
                                size: 40,
                              ),
                            ),
                          )
                        : Container(
                            color: const Color(0xFF1A1A1A),
                            child: Icon(
                              Icons.image_outlined,
                              color: Colors.white.withOpacity(0.2),
                              size: 40,
                            ),
                          ),
                    
                    // 左下角播放量 - .cover-views
                    Positioned(
                      bottom: 8,
                      left: 8,
                      child: Row(
                        children: [
                          const Text(
                            '�?,
                            style: TextStyle(
                              fontSize: 10,
                              color: Colors.white,
                              shadows: [
                                Shadow(
                                  blurRadius: 3,
                                  color: Color(0xCC000000),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 3),
                          Text(
                            _formatCount(video.viewCount),
                            style: const TextStyle(
                              fontSize: 12,
                              color: Colors.white,
                              shadows: [
                                Shadow(
                                  blurRadius: 3,
                                  color: Color(0xCC000000),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    
                    // 右下角时�?- .video-duration
                    Positioned(
                      bottom: 8,
                      right: 8,
                      child: Text(
                        video.formattedDuration,
                        style: const TextStyle(
                          fontSize: 12,
                          color: Colors.white,
                          shadows: [
                            Shadow(
                              blurRadius: 3,
                              color: Color(0xCC000000),
                            ),
                          ],
                        ),
                      ),
                    ),
                    
                    // VIP 标签 - .vip-tag
                    if (video.isVip)
                      Positioned(
                        top: 8,
                        left: 8,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(
                              colors: [Color(0xFFFFCC00), Color(0xFFFF9500)],
                            ),
                            borderRadius: BorderRadius.circular(4),
                            boxShadow: [
                              BoxShadow(
                                color: const Color(0xFFFFCC00).withOpacity(0.3),
                                blurRadius: 8,
                              ),
                            ],
                          ),
                          child: const Text(
                            'VIP',
                            style: TextStyle(
                              color: Colors.black,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
            
            // 视频信息�?- .video-info
            Padding(
              padding: EdgeInsets.symmetric(
                horizontal: 2,
                vertical: gridMode == 1 ? 6 : 4,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 标题 - .video-title (固定两行)
                  SizedBox(
                    height: gridMode == 1 ? 44 : 38, // 固定两行高度
                    child: Text(
                      video.title,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.92),
                        fontSize: gridMode == 1 ? 15 : 13,
                        height: 1.5,
                        letterSpacing: 0.5,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                  
                  const SizedBox(height: 4),
                  
                  // 底部标签和评�?- .video-meta
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      // 标签 - .video-tag
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(
                            colors: [Color(0xFFA855F7), Color(0xFF7C3AED)],
                          ),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          video.categoryName ?? '精�?,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 11,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                      
                      // 评论�?- .video-comments
                      Text(
                        '评论 ${video.commentCount}',
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.5),
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  // 格式化播放量
  String _formatCount(int count) {
    if (count >= 10000) {
      return '${(count / 10000).toStringAsFixed(1)}W';
    }
    return count.toString();
  }
}

