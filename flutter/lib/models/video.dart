class Video {
  final int id;
  final String title;
  final String? description;
  final String? thumbnailUrl;
  final String? coverUrl;
  final String? videoUrl;
  final String? hlsUrl;
  final int duration;
  final int viewCount;
  final int likeCount;
  final int favoriteCount;
  final int commentCount;
  final bool isVip;
  final int coinPrice;
  final int? categoryId;
  final String? categoryName;
  final int? creatorId;
  final String? creatorName;
  final String? creatorAvatar;
  final String status;
  final DateTime createdAt;
  final bool isLiked;
  final bool isFavorited;
  final bool isPurchased;
  
  Video({
    required this.id,
    required this.title,
    this.description,
    this.thumbnailUrl,
    this.coverUrl,
    this.videoUrl,
    this.hlsUrl,
    this.duration = 0,
    this.viewCount = 0,
    this.likeCount = 0,
    this.favoriteCount = 0,
    this.commentCount = 0,
    this.isVip = false,
    this.coinPrice = 0,
    this.categoryId,
    this.categoryName,
    this.creatorId,
    this.creatorName,
    this.creatorAvatar,
    this.status = 'active',
    required this.createdAt,
    this.isLiked = false,
    this.isFavorited = false,
    this.isPurchased = false,
  });
  
  static int _toInt(dynamic value) {
    if (value == null) return 0;
    if (value is int) return value;
    if (value is double) return value.toInt();
    if (value is String) return int.tryParse(value) ?? 0;
    return 0;
  }
  
  factory Video.fromJson(Map<String, dynamic> json) {
    return Video(
      id: _toInt(json['id']),
      title: json['title'] ?? '',
      description: json['description'],
      thumbnailUrl: json['thumbnail'] ?? json['thumbnail_url'],
      coverUrl: json['cover_url'],
      videoUrl: json['video_url'],
      hlsUrl: json['hls_url'],
      duration: _toInt(json['duration']),
      viewCount: _toInt(json['view_count']),
      likeCount: _toInt(json['like_count']),
      favoriteCount: _toInt(json['favorite_count']),
      commentCount: _toInt(json['comment_count']),
      isVip: json['is_vip'] ?? json['is_vip_only'] ?? json['needs_vip'] ?? false,
      coinPrice: _toInt(json['coin_price']),
      categoryId: json['category_id'] != null ? _toInt(json['category_id']) : null,
      categoryName: json['category_name'],
      creatorId: json['creator_id'] != null ? _toInt(json['creator_id']) : (json['user_id'] != null ? _toInt(json['user_id']) : null),
      creatorName: json['creator_name'] ?? json['username'],
      creatorAvatar: json['creator_avatar'] ?? json['avatar'],
      status: json['status'] ?? 'active',
      createdAt: _parseDateTime(json['created_at']),
      isLiked: json['is_liked'] ?? false,
      isFavorited: json['is_favorited'] ?? false,
      isPurchased: json['is_purchased'] ?? false,
    );
  }
  
  static DateTime _parseDateTime(dynamic value) {
    if (value == null) return DateTime.now();
    if (value is DateTime) return value;
    if (value is String) {
      try {
        return DateTime.parse(value);
      } catch (_) {
        return DateTime.now();
      }
    }
    return DateTime.now();
  }
  
  String get formattedDuration {
    final minutes = duration ~/ 60;
    final seconds = duration % 60;
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }
  
  String get formattedViewCount {
    if (viewCount >= 10000) {
      return '${(viewCount / 10000).toStringAsFixed(1)}万';
    }
    return viewCount.toString();
  }
  
  String? get cover => coverUrl ?? thumbnailUrl;
  String? get playUrl => hlsUrl ?? videoUrl;
}

class ShortVideo extends Video {
  ShortVideo({
    required super.id,
    required super.title,
    super.description,
    super.thumbnailUrl,
    super.coverUrl,
    super.videoUrl,
    super.hlsUrl,
    super.duration,
    super.viewCount,
    super.likeCount,
    super.favoriteCount,
    super.commentCount,
    super.isVip,
    super.coinPrice,
    super.categoryId,
    super.categoryName,
    super.creatorId,
    super.creatorName,
    super.creatorAvatar,
    super.status,
    required super.createdAt,
    super.isLiked,
    super.isFavorited,
    super.isPurchased,
  });
  
  factory ShortVideo.fromJson(Map<String, dynamic> json) {
    return ShortVideo(
      id: Video._toInt(json['id']),
      title: json['title'] ?? '',
      description: json['description'],
      thumbnailUrl: json['thumbnail'] ?? json['thumbnail_url'],
      coverUrl: json['cover_url'],
      videoUrl: json['video_url'],
      hlsUrl: json['hls_url'],
      duration: Video._toInt(json['duration']),
      viewCount: Video._toInt(json['view_count']),
      likeCount: Video._toInt(json['like_count']),
      favoriteCount: Video._toInt(json['favorite_count']),
      commentCount: Video._toInt(json['comment_count']),
      isVip: json['is_vip'] ?? false,
      coinPrice: Video._toInt(json['coin_price']),
      categoryId: json['category_id'] != null ? Video._toInt(json['category_id']) : null,
      categoryName: json['category_name'],
      creatorId: json['creator_id'] != null ? Video._toInt(json['creator_id']) : null,
      creatorName: json['creator_name'] ?? json['username'],
      creatorAvatar: json['creator_avatar'] ?? json['avatar'],
      status: json['status'] ?? 'active',
      createdAt: Video._parseDateTime(json['created_at']),
      isLiked: json['is_liked'] ?? false,
      isFavorited: json['is_favorited'] ?? false,
      isPurchased: json['is_purchased'] ?? false,
    );
  }
}
