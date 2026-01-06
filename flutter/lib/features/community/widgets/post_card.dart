import 'package:flutter/material.dart';

class PostCard extends StatelessWidget {
  final Map<String, dynamic> post;
  final VoidCallback? onLike;
  final VoidCallback? onFollow;
  final VoidCallback? onTap;

  const PostCard({
    super.key,
    required this.post,
    this.onLike,
    this.onFollow,
    this.onTap,
  });

  String _formatTime(String? time) {
    if (time == null) return '';
    final d = DateTime.tryParse(time);
    if (d == null) return '';
    final now = DateTime.now();
    final diff = now.difference(d).inSeconds;
    if (diff < 60) return '刚刚';
    if (diff < 3600) return '${diff ~/ 60}分钟前';
    if (diff < 86400) return '${diff ~/ 3600}小时前';
    return '${d.month}/${d.day}';
  }

  @override
  Widget build(BuildContext context) {
    final user = post['user'] ?? {};
    final images = (post['images'] as List?)?.cast<String>() ?? [];
    final isLiked = post['is_liked'] == true;
    final isFollowed = post['is_followed'] == true;

    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFF151515),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 用户信息
            Row(
              children: [
                CircleAvatar(
                  radius: 22,
                  backgroundImage: NetworkImage(
                    user['avatar'] ?? 'https://via.placeholder.com/44',
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        user['nickname'] ?? user['username'] ?? '用户',
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      Text(
                        _formatTime(post['created_at']),
                        style: const TextStyle(color: Colors.grey, fontSize: 12),
                      ),
                    ],
                  ),
                ),
                if (!isFollowed)
                  TextButton(
                    onPressed: onFollow,
                    style: TextButton.styleFrom(
                      backgroundColor: const Color(0xFFFF4757),
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(20),
                      ),
                    ),
                    child: const Text('+关注', style: TextStyle(color: Colors.white, fontSize: 13)),
                  ),
              ],
            ),
            const SizedBox(height: 12),
            // 内容
            if (post['content'] != null && post['content'].toString().isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Text(
                  post['content'],
                  style: const TextStyle(color: Color(0xFFDDDDDD), height: 1.6),
                ),
              ),
            // 图片
            if (images.isNotEmpty) _buildImagesGrid(images),
            // 互动栏
            const SizedBox(height: 12),
            Row(
              children: [
                _buildAction(
                  icon: isLiked ? Icons.favorite : Icons.favorite_border,
                  color: isLiked ? Colors.red : Colors.grey,
                  count: post['like_count'],
                  onTap: onLike,
                ),
                const SizedBox(width: 30),
                _buildAction(
                  icon: Icons.chat_bubble_outline,
                  color: Colors.grey,
                  count: post['comment_count'],
                ),
                const SizedBox(width: 30),
                _buildAction(
                  icon: Icons.share_outlined,
                  color: Colors.grey,
                  count: post['share_count'],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildImagesGrid(List<String> images) {
    final count = images.length;
    int crossAxisCount = count == 1 ? 1 : (count <= 4 ? 2 : 3);
    
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: crossAxisCount,
        crossAxisSpacing: 4,
        mainAxisSpacing: 4,
      ),
      itemCount: images.length > 9 ? 9 : images.length,
      itemBuilder: (ctx, i) => ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: Image.network(
          images[i],
          fit: BoxFit.cover,
          errorBuilder: (_, __, ___) => Container(color: Colors.grey[800]),
        ),
      ),
    );
  }

  Widget _buildAction({
    required IconData icon,
    required Color color,
    int? count,
    VoidCallback? onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Row(
        children: [
          Icon(icon, color: color, size: 20),
          if (count != null && count > 0) ...[
            const SizedBox(width: 4),
            Text('$count', style: TextStyle(color: color, fontSize: 13)),
          ],
        ],
      ),
    );
  }
}
