class Video {
  final int id;
  final String title;
  final String? description;
  final String? coverUrl;
  final String? hlsUrl;
  final String? previewUrl;
  final double duration;
  final String status;
  final String quality;
  final bool isVipOnly;
  final bool isFeatured;
  final bool isShort;
  final int viewCount;
  final int likeCount;
  final int commentCount;
  final int favoriteCount;
  final String? aiSummary;
  final String? uploaderName;
  final String? uploaderAvatar;
  final List<String> tags;
  final DateTime createdAt;
  final DateTime? publishedAt;
  
  // 付费相关
  final String payType;
  final int coinPrice;
  final int vipCoinPrice;
  final int freePreviewSeconds;
  
  Video({
    required this.id,
    required this.title,
    this.description,
    this.coverUrl,
    this.hlsUrl,
    this.previewUrl,
    this.duration = 0,
    this.status = 'PUBLISHED',
    this.quality = '720p',
    this.isVipOnly = false,
    this.isFeatured = false,
    this.isShort = false,
    this.viewCount = 0,
    this.likeCount = 0,
    this.commentCount = 0,
    this.favoriteCount = 0,
    this.aiSummary,
    this.uploaderName,
    this.uploaderAvatar,
    this.tags = const [],
    required this.createdAt,
    this.publishedAt,
    this.payType = 'free',
    this.coinPrice = 0,
    this.vipCoinPrice = 0,
    this.freePreviewSeconds = 15,
  });
  
  factory Video.fromJson(Map<String, dynamic> json) {
    return Video(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      coverUrl: json['cover_url'],
      hlsUrl: json['hls_url'],
      previewUrl: json['preview_url'],
      duration: (json['duration'] ?? 0).toDouble(),
      status: json['status'] ?? 'PUBLISHED',
      quality: json['quality'] ?? '720p',
      isVipOnly: json['is_vip_only'] ?? false,
      isFeatured: json['is_featured'] ?? false,
      isShort: json['is_short'] ?? false,
      viewCount: json['view_count'] ?? 0,
      likeCount: json['like_count'] ?? 0,
      commentCount: json['comment_count'] ?? 0,
      favoriteCount: json['favorite_count'] ?? 0,
      aiSummary: json['ai_summary'],
      uploaderName: json['uploader_name'],
      uploaderAvatar: json['uploader_avatar'],
      tags: (json['tags'] as List?)?.cast<String>() ?? [],
      createdAt: DateTime.parse(json['created_at']),
      publishedAt: json['published_at'] != null 
          ? DateTime.parse(json['published_at']) 
          : null,
      payType: json['pay_type'] ?? 'free',
      coinPrice: json['coin_price'] ?? 0,
      vipCoinPrice: json['vip_coin_price'] ?? 0,
      freePreviewSeconds: json['free_preview_seconds'] ?? 15,
    );
  }
  
  String get durationText {
    final minutes = (duration / 60).floor();
    final seconds = (duration % 60).floor();
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }
  
  String get viewCountText {
    if (viewCount >= 10000) {
      return '${(viewCount / 10000).toStringAsFixed(1)}万';
    }
    return viewCount.toString();
  }
  
  bool get isFree => payType == 'free';
  bool get needsCoins => payType == 'coins' && coinPrice > 0;
}
