import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:pull_to_refresh/pull_to_refresh.dart';

import '../../../app/routes.dart';
import '../../../app/theme.dart';
import '../../../core/models/video.dart';

class VideoGrid extends StatefulWidget {
  final List<Video> videos;
  final bool isLoading;
  final bool hasMore;
  final VoidCallback onRefresh;
  final VoidCallback onLoadMore;

  const VideoGrid({
    super.key,
    required this.videos,
    required this.isLoading,
    required this.hasMore,
    required this.onRefresh,
    required this.onLoadMore,
  });

  @override
  State<VideoGrid> createState() => _VideoGridState();
}

class _VideoGridState extends State<VideoGrid> {
  final RefreshController _refreshController = RefreshController();

  @override
  void dispose() {
    _refreshController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (widget.videos.isEmpty && widget.isLoading) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    if (widget.videos.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.video_library_outlined,
              size: 64.w,
              color: AppTheme.textSecondary,
            ),
            SizedBox(height: 16.h),
            Text(
              '暂无视频',
              style: TextStyle(
                fontSize: 16.sp,
                color: AppTheme.textSecondary,
              ),
            ),
          ],
        ),
      );
    }

    return SmartRefresher(
      controller: _refreshController,
      enablePullDown: true,
      enablePullUp: widget.hasMore,
      onRefresh: () async {
        widget.onRefresh();
        _refreshController.refreshCompleted();
      },
      onLoading: () async {
        widget.onLoadMore();
        _refreshController.loadComplete();
      },
      child: GridView.builder(
        padding: EdgeInsets.all(12.w),
        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          mainAxisSpacing: 12.h,
          crossAxisSpacing: 12.w,
          childAspectRatio: 0.75,
        ),
        itemCount: widget.videos.length,
        itemBuilder: (context, index) {
          return VideoCard(video: widget.videos[index]);
        },
      ),
    );
  }
}

class VideoCard extends StatelessWidget {
  final Video video;

  const VideoCard({super.key, required this.video});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () {
        Navigator.pushNamed(
          context,
          AppRoutes.videoPlayer,
          arguments: {'videoId': video.id},
        );
      },
      child: Container(
        decoration: BoxDecoration(
          color: AppTheme.cardColor,
          borderRadius: BorderRadius.circular(8.r),
        ),
        clipBehavior: Clip.antiAlias,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 封面
            Expanded(
              child: Stack(
                fit: StackFit.expand,
                children: [
                  // 封面图
                  video.coverUrl != null
                      ? CachedNetworkImage(
                          imageUrl: video.coverUrl!,
                          fit: BoxFit.cover,
                          placeholder: (context, url) => Container(
                            color: AppTheme.surfaceColor,
                            child: const Center(
                              child: CircularProgressIndicator(strokeWidth: 2),
                            ),
                          ),
                          errorWidget: (context, url, error) => Container(
                            color: AppTheme.surfaceColor,
                            child: const Icon(Icons.error),
                          ),
                        )
                      : Container(
                          color: AppTheme.surfaceColor,
                          child: const Icon(Icons.video_library),
                        ),
                  
                  // 时长标签
                  Positioned(
                    right: 4.w,
                    bottom: 4.h,
                    child: Container(
                      padding: EdgeInsets.symmetric(
                        horizontal: 4.w,
                        vertical: 2.h,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.black54,
                        borderRadius: BorderRadius.circular(4.r),
                      ),
                      child: Text(
                        video.durationText,
                        style: TextStyle(
                          fontSize: 10.sp,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ),
                  
                  // VIP 标签
                  if (video.isVipOnly)
                    Positioned(
                      left: 4.w,
                      top: 4.h,
                      child: Container(
                        padding: EdgeInsets.symmetric(
                          horizontal: 6.w,
                          vertical: 2.h,
                        ),
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(
                            colors: [Color(0xFFFFD700), Color(0xFFFFA500)],
                          ),
                          borderRadius: BorderRadius.circular(4.r),
                        ),
                        child: Text(
                          'VIP',
                          style: TextStyle(
                            fontSize: 10.sp,
                            color: Colors.black,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ),
            
            // 标题和信息
            Padding(
              padding: EdgeInsets.all(8.w),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    video.title,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 13.sp,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  SizedBox(height: 4.h),
                  Row(
                    children: [
                      Icon(
                        Icons.play_arrow,
                        size: 14.w,
                        color: AppTheme.textSecondary,
                      ),
                      SizedBox(width: 2.w),
                      Text(
                        video.viewCountText,
                        style: TextStyle(
                          fontSize: 11.sp,
                          color: AppTheme.textSecondary,
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
}
