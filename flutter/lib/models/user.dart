class User {
  final int id;
  final String? username;
  final String? nickname;
  final String? email;
  final String? phone;
  final String? avatar;
  final int coins;
  final int points;
  final bool isVip;
  final int vipLevel;
  final DateTime? vipExpireTime;
  final bool isCreator;
  final String role;
  final DateTime? createdAt;
  
  User({
    required this.id,
    this.username,
    this.nickname,
    this.email,
    this.phone,
    this.avatar,
    this.coins = 0,
    this.points = 0,
    this.isVip = false,
    this.vipLevel = 0,
    this.vipExpireTime,
    this.isCreator = false,
    this.role = 'user',
    this.createdAt,
  });
  
  /// 安全转换为 int
  static int _toInt(dynamic value) {
    if (value == null) return 0;
    if (value is int) return value;
    if (value is double) return value.toInt();
    if (value is String) return int.tryParse(value) ?? 0;
    return 0;
  }
  
  /// 安全解析日期时间
  static DateTime? _parseDateTime(dynamic value) {
    if (value == null) return null;
    if (value is DateTime) return value;
    if (value is String) {
      try {
        return DateTime.parse(value);
      } catch (_) {
        return null;
      }
    }
    return null;
  }
  
  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: _toInt(json['id']),
      username: json['username'],
      nickname: json['nickname'],
      email: json['email'],
      phone: json['phone'],
      avatar: json['avatar'],
      coins: _toInt(json['coins']),
      points: _toInt(json['points']),
      isVip: json['is_vip'] ?? false,
      vipLevel: _toInt(json['vip_level']),
      vipExpireTime: _parseDateTime(json['vip_expire_time']),
      isCreator: json['is_creator'] ?? false,
      role: json['role'] ?? 'user',
      createdAt: _parseDateTime(json['created_at']),
    );
  }
  
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'username': username,
      'nickname': nickname,
      'email': email,
      'phone': phone,
      'avatar': avatar,
      'coins': coins,
      'points': points,
      'is_vip': isVip,
      'vip_level': vipLevel,
      'vip_expire_time': vipExpireTime?.toIso8601String(),
      'is_creator': isCreator,
      'role': role,
      'created_at': createdAt?.toIso8601String(),
    };
  }
  
  // 显示名称
  String get displayName => nickname ?? username ?? '用户$id';
  
  // VIP等级名称
  String get vipLevelName {
    switch (vipLevel) {
      case 1: return '普通VIP';
      case 2: return 'VIP 1';
      case 3: return 'VIP 2';
      case 4: return 'VIP 3';
      case 5: return '黄金至尊';
      case 6: return '紫色限定至尊';
      default: return '普通用户';
    }
  }
  
  // VIP到期时间格式化
  String? get vipExpireDate {
    if (vipExpireTime == null) return null;
    return '${vipExpireTime!.year}-${vipExpireTime!.month.toString().padLeft(2, '0')}-${vipExpireTime!.day.toString().padLeft(2, '0')}';
  }
}
