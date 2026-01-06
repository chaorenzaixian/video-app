class User {
  final int id;
  final String username;
  final String? email;
  final String? phone;
  final String? nickname;
  final String? avatar;
  final String? bio;
  final bool isGuest;
  final bool isVip;
  final int vipLevel;
  final DateTime? vipExpireDate;
  final String? inviteCode;
  final int inviteCount;
  final int coins;
  final int points;
  final DateTime createdAt;
  
  User({
    required this.id,
    required this.username,
    this.email,
    this.phone,
    this.nickname,
    this.avatar,
    this.bio,
    this.isGuest = false,
    this.isVip = false,
    this.vipLevel = 0,
    this.vipExpireDate,
    this.inviteCode,
    this.inviteCount = 0,
    this.coins = 0,
    this.points = 0,
    required this.createdAt,
  });
  
  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      username: json['username'],
      email: json['email'],
      phone: json['phone'],
      nickname: json['nickname'],
      avatar: json['avatar'],
      bio: json['bio'],
      isGuest: json['is_guest'] ?? false,
      isVip: json['is_vip'] ?? false,
      vipLevel: json['vip_level'] ?? 0,
      vipExpireDate: json['vip_expire_date'] != null 
          ? DateTime.parse(json['vip_expire_date']) 
          : null,
      inviteCode: json['invite_code'],
      inviteCount: json['invite_count'] ?? 0,
      coins: json['coins'] ?? 0,
      points: json['points'] ?? 0,
      createdAt: DateTime.parse(json['created_at']),
    );
  }
  
  String get displayName => nickname ?? username;
  
  String get vipLevelName {
    switch (vipLevel) {
      case 1: return '月度会员';
      case 2: return '季度会员';
      case 3: return '年度会员';
      case 4: return 'VIP3';
      case 5: return '黄金至尊';
      case 6: return '紫色限定至尊';
      default: return '普通用户';
    }
  }
}
