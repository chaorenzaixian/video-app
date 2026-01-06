import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../../app/theme.dart';
import '../../providers/user_provider.dart';
import '../../services/api_service.dart';
import '../../utils/assets.dart';

/// 个人中心页面 - 精确复刻 Vue.js Profile.vue
class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  List<dynamic> _iconAds = [];
  int _unreadCount = 0;
  bool _signingIn = false;

  @override
  void initState() {
    super.initState();
    _fetchData();
  }

  Future<void> _fetchData() async {
    await Future.wait([
      _fetchIconAds(),
      _fetchUnreadCount(),
    ]);
  }

  Future<void> _fetchIconAds() async {
    try {
      final response = await ApiService.get('/ads/icons');
      setState(() {
        _iconAds = response.data ?? [];
      });
    } catch (e) {
      debugPrint('获取图标广告失败: $e');
    }
  }

  Future<void> _fetchUnreadCount() async {
    try {
      final response = await ApiService.get('/notifications/unread-count');
      setState(() {
        _unreadCount = response.data['count'] ?? 0;
      });
    } catch (e) {
      debugPrint('获取未读数失败: $e');
    }
  }

  Future<void> _handleSign() async {
    if (_signingIn) return;
    setState(() => _signingIn = true);

    try {
      await ApiService.post('/users/sign');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('签到成功！'), backgroundColor: Colors.green),
        );
        context.read<UserProvider>().fetchUser();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('签到失败'), backgroundColor: Colors.red),
        );
      }
    } finally {
      setState(() => _signingIn = false);
    }
  }

  void _copyId(String? id) {
    if (id == null) return;
    Clipboard.setData(ClipboardData(text: id));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('已复制'), duration: Duration(seconds: 1)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A), // Vue: #0a0a0a
      body: Consumer<UserProvider>(
        builder: (context, userProvider, child) {
          final user = userProvider.user;

          return SingleChildScrollView(
            child: Column(
              children: [
                // 顶部头部
                _buildHeader(),

                // 用户信息区域
                _buildUserSection(user),

                // VIP推广条
                _buildVipBanner(user),

                // 三卡片入口
                _buildCardGrid(),

                // 快捷功能
                _buildQuickMenu(),

                // 图标广告位
                _buildAdSection(),

                // 菜单列表
                _buildMenuList(),

                // 底部间距
                const SizedBox(height: 100),
              ],
            ),
          );
        },
      ),
    );
  }

  /// 顶部头部 - 对应 Vue page-header
  Widget _buildHeader() {
    return SafeArea(
      bottom: false,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            // 左侧通知图标
            GestureDetector(
              onTap: () => Navigator.pushNamed(context, '/messages'),
              child: Stack(
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1A1A1A),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Image.asset(
                      AppAssets.mineNotification,
                      color: Colors.white.withOpacity(0.7),
                      errorBuilder: (_, __, ___) => Icon(
                        Icons.notifications_outlined,
                        color: Colors.white.withOpacity(0.7),
                        size: 22,
                      ),
                    ),
                  ),
                  if (_unreadCount > 0)
                    Positioned(
                      right: 0,
                      top: 0,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                        decoration: BoxDecoration(
                          color: Colors.red,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        constraints: const BoxConstraints(minWidth: 16, minHeight: 16),
                        child: Text(
                          _unreadCount > 99 ? '99+' : '$_unreadCount',
                          style: const TextStyle(color: Colors.white, fontSize: 10),
                          textAlign: TextAlign.center,
                        ),
                      ),
                    ),
                ],
              ),
            ),

            // 右侧客服和设置
            Row(
              children: [
                GestureDetector(
                  onTap: () => Navigator.pushNamed(context, '/customer-service'),
                  child: Container(
                    width: 36,
                    height: 36,
                    padding: const EdgeInsets.all(6),
                    margin: const EdgeInsets.only(right: 12),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1A1A1A),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Image.asset(
                      AppAssets.icService,
                      errorBuilder: (_, __, ___) => Icon(
                        Icons.headset_mic_outlined,
                        color: Colors.white.withOpacity(0.7),
                        size: 22,
                      ),
                    ),
                  ),
                ),
                GestureDetector(
                  onTap: () => Navigator.pushNamed(context, '/settings'),
                  child: Container(
                    width: 36,
                    height: 36,
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1A1A1A),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Image.asset(
                      AppAssets.icSetting,
                      errorBuilder: (_, __, ___) => Icon(
                        Icons.settings_outlined,
                        color: Colors.white.withOpacity(0.7),
                        size: 22,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  /// 用户信息区域 - 对应 Vue user-section
  Widget _buildUserSection(user) {
    final isVip = user?.isVip ?? false;
    final vipLevel = user?.vipLevel ?? 0;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            const Color(0xFF1A1A1A),
            const Color(0xFF1A1A1A).withOpacity(0.8),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: [
          // 用户行 - user-row
          Row(
            children: [
              // 头像
              Stack(
                children: [
                  Container(
                    width: 70,
                    height: 70,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: isVip ? AppTheme.vipGradient : AppTheme.primaryGradient,
                      border: Border.all(
                        color: isVip ? AppTheme.vipGold : AppTheme.primaryColor,
                        width: 2,
                      ),
                    ),
                    child: ClipOval(
                      child: user?.avatar != null
                          ? CachedNetworkImage(
                              imageUrl: ApiService.getFullImageUrl(user!.avatar!),
                              fit: BoxFit.cover,
                            )
                          : const Icon(Icons.person, color: Colors.white, size: 35),
                    ),
                  ),
                  // VIP皇冠
                  if (isVip)
                    Positioned(
                      bottom: 0,
                      right: 0,
                      child: Container(
                        width: 22,
                        height: 22,
                        decoration: const BoxDecoration(
                          shape: BoxShape.circle,
                          gradient: AppTheme.vipGradient,
                        ),
                        child: const Icon(Icons.workspace_premium, color: Colors.black, size: 14),
                      ),
                    ),
                  // 性别图标
                  Positioned(
                    top: 0,
                    right: 0,
                    child: Container(
                      width: 18,
                      height: 18,
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        color: Color(0xFF4A90E2),
                      ),
                      child: const Center(
                        child: Text('♂', style: TextStyle(color: Colors.white, fontSize: 12)),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(width: 16),

              // 用户信息
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // 昵称行
                    Row(
                      children: [
                        Text(
                          user?.displayName ?? '未登录',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        if (vipLevel > 0) ...[
                          const SizedBox(width: 8),
                          Image.asset(
                            AppAssets.getVipIcon(vipLevel),
                            width: 50,
                            height: 20,
                            fit: BoxFit.contain,
                            errorBuilder: (_, __, ___) => _buildVipBadge(vipLevel),
                          ),
                        ],
                      ],
                    ),
                    const SizedBox(height: 6),
                    // 用户ID行
                    Row(
                      children: [
                        Text(
                          user?.username ?? '--------',
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.5),
                            fontSize: 13,
                          ),
                        ),
                        if (user?.username != null) ...[
                          const SizedBox(width: 8),
                          GestureDetector(
                            onTap: () => _copyId(user?.username),
                            child: Icon(
                              Icons.copy,
                              color: Colors.white.withOpacity(0.5),
                              size: 14,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ],
                ),
              ),

              // 签到按钮
              GestureDetector(
                onTap: _handleSign,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    gradient: AppTheme.primaryGradient,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Image.asset(
                        AppAssets.icSign,
                        width: 18,
                        height: 18,
                        errorBuilder: (_, __, ___) => const Icon(
                          Icons.calendar_today,
                          color: Colors.white,
                          size: 16,
                        ),
                      ),
                      const SizedBox(width: 4),
                      Text(
                        _signingIn ? '签到中...' : '签到',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),

          // 统计行 - stats-row
          Row(
            children: [
              Expanded(
                child: _buildStatItem(user?.coins ?? 0, '缓存视频'),
              ),
              Container(
                width: 1,
                height: 30,
                color: Colors.white.withOpacity(0.1),
              ),
              Expanded(
                child: _buildStatItem(0, '剩余AI脱衣次数'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildVipBadge(int level) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        gradient: AppTheme.vipGradient,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Text(
        'VIP$level',
        style: const TextStyle(
          color: Colors.black,
          fontSize: 11,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _buildStatItem(int value, String label) {
    return Column(
      children: [
        Text(
          '$value',
          style: const TextStyle(
            color: Colors.white,
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: TextStyle(
            color: Colors.white.withOpacity(0.5),
            fontSize: 12,
          ),
        ),
      ],
    );
  }

  /// VIP推广条 - 对应 Vue vip-banner
  Widget _buildVipBanner(user) {
    final isVip = user?.isVip ?? false;
    final vipLevel = user?.vipLevel ?? 0;

    return GestureDetector(
      onTap: () => Navigator.pushNamed(context, '/vip'),
      child: Container(
        margin: const EdgeInsets.all(16),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF2D1F3D), Color(0xFF1A1225)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: const Color(0xFFFFD700).withOpacity(0.3),
            width: 1,
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            // 左侧文字
            isVip
                ? Row(
                    children: [
                      Image.asset(
                        AppAssets.getVipIcon(vipLevel),
                        width: 60,
                        height: 24,
                        fit: BoxFit.contain,
                        errorBuilder: (_, __, ___) => _buildVipBadge(vipLevel),
                      ),
                      const SizedBox(width: 12),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          ShaderMask(
                            shaderCallback: (bounds) => const LinearGradient(
                              colors: [Color(0xFFFFE066), Color(0xFFFFAA00)],
                            ).createShader(bounds),
                            child: Text(
                              '到期时间：${user?.vipExpireTime != null ? _formatDate(user!.vipExpireTime!) : "永久"}',
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 12,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  )
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      ShaderMask(
                        shaderCallback: (bounds) => const LinearGradient(
                          colors: [Color(0xFFFFE066), Color(0xFFFFAA00)],
                        ).createShader(bounds),
                        child: const Text(
                          '开通会员',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '享专属特权',
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.6),
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),

            // 右侧按钮
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                gradient: AppTheme.vipGradient,
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    isVip ? '升级会员' : '开通会员',
                    style: const TextStyle(
                      color: Colors.black,
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(width: 4),
                  Container(
                    width: 18,
                    height: 18,
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.2),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.chevron_right,
                      color: Colors.black,
                      size: 14,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatDate(DateTime date) {
    return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
  }

  /// 三卡片入口 - 对应 Vue card-grid
  Widget _buildCardGrid() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        children: [
          Expanded(child: _buildFeatureCard('VIP特权', AppAssets.vipCenter, '/vip')),
          const SizedBox(width: 10),
          Expanded(child: _buildFeatureCard('我的钱包', AppAssets.myWallet, '/wallet')),
          const SizedBox(width: 10),
          Expanded(child: _buildFeatureCard('代理赚钱', AppAssets.agent, '/agent')),
        ],
      ),
    );
  }

  Widget _buildFeatureCard(String title, String asset, String route) {
    return GestureDetector(
      onTap: () => Navigator.pushNamed(context, route),
      child: Container(
        height: 70,
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF1E1E2E), Color(0xFF151520)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: AppTheme.primaryColor.withOpacity(0.2),
            width: 1,
          ),
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(12),
          child: Image.asset(
            asset,
            fit: BoxFit.cover,
            errorBuilder: (_, __, ___) => Center(
              child: Text(
                title,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  /// 快捷功能 - 对应 Vue quick-menu
  Widget _buildQuickMenu() {
    final menuItems = [
      {'icon': AppAssets.icHistory, 'label': '观看记录', 'route': '/history'},
      {'icon': AppAssets.icCollect, 'label': '我的收藏', 'route': '/favorites'},
      {'icon': AppAssets.icBuy, 'label': '我的购买', 'route': '/purchases'},
      {'icon': AppAssets.icAi, 'label': 'AI女友', 'route': '/ai'},
    ];

    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A1A),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: menuItems.map((item) {
          return GestureDetector(
            onTap: () => Navigator.pushNamed(context, item['route'] as String),
            child: Column(
              children: [
                Container(
                  width: 44,
                  height: 44,
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: const Color(0xFF252525),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Image.asset(
                    item['icon'] as String,
                    errorBuilder: (_, __, ___) => const Icon(
                      Icons.folder_outlined,
                      color: Colors.white54,
                      size: 20,
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  item['label'] as String,
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.8),
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  /// 图标广告位 - 对应 Vue ad-section
  Widget _buildAdSection() {
    if (_iconAds.isEmpty) return const SizedBox();

    final row1 = _iconAds.take(5).toList();
    final row2 = _iconAds.length > 5 ? _iconAds.skip(5).toList() : [];

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        children: [
          // 第一行固定
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: row1.map((ad) => _buildAdItem(ad)).toList(),
          ),

          // 第二行滚动
          if (row2.isNotEmpty) ...[
            const SizedBox(height: 12),
            SizedBox(
              height: 80,
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                itemCount: row2.length,
                itemBuilder: (context, index) {
                  return Padding(
                    padding: const EdgeInsets.only(right: 16),
                    child: _buildAdItem(row2[index]),
                  );
                },
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildAdItem(dynamic ad) {
    return GestureDetector(
      onTap: () {},
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  AppTheme.primaryColor.withOpacity(0.2),
                  AppTheme.secondaryColor.withOpacity(0.2),
                ],
              ),
              borderRadius: BorderRadius.circular(14),
            ),
            child: ad['image'] != null
                ? ClipRRect(
                    borderRadius: BorderRadius.circular(14),
                    child: CachedNetworkImage(
                      imageUrl: ApiService.getFullImageUrl(ad['image']),
                      fit: BoxFit.cover,
                      errorWidget: (_, __, ___) => Center(
                        child: Text(
                          ad['icon'] ?? '📦',
                          style: const TextStyle(fontSize: 24),
                        ),
                      ),
                    ),
                  )
                : Center(
                    child: Text(
                      ad['icon'] ?? '📦',
                      style: const TextStyle(fontSize: 24),
                    ),
                  ),
          ),
          const SizedBox(height: 6),
          Text(
            ad['name'] ?? '',
            style: TextStyle(
              fontSize: 11,
              color: Colors.white.withOpacity(0.7),
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }

  /// 菜单列表 - 对应 Vue menu-section
  Widget _buildMenuList() {
    final menuItems = [
      {'icon': Icons.dashboard_outlined, 'label': '创作中心', 'route': '/creator-center'},
      {'icon': Icons.share_outlined, 'label': '分享邀请', 'route': '/invite-share'},
      {'icon': Icons.apps_outlined, 'label': '应用推荐', 'route': '/app-recommend'},
      {'icon': Icons.group_outlined, 'label': '官方群组', 'route': '/groups'},
      {'icon': Icons.headset_mic_outlined, 'label': '联系客服', 'route': '/customer-service'},
    ];

    return Container(
      margin: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A1A),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: menuItems.asMap().entries.map((entry) {
          final index = entry.key;
          final item = entry.value;
          final isLast = index == menuItems.length - 1;

          return Column(
            children: [
              _buildMenuItem(
                item['icon'] as IconData,
                item['label'] as String,
                item['route'] as String,
              ),
              if (!isLast)
                Divider(
                  height: 1,
                  color: Colors.white.withOpacity(0.06),
                  indent: 52,
                ),
            ],
          );
        }).toList(),
      ),
    );
  }

  Widget _buildMenuItem(IconData icon, String label, String route) {
    return GestureDetector(
      onTap: () => Navigator.pushNamed(context, route),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(
          children: [
            Icon(
              icon,
              color: Colors.white.withOpacity(0.7),
              size: 22,
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Text(
                label,
                style: TextStyle(
                  color: Colors.white.withOpacity(0.9),
                  fontSize: 15,
                ),
              ),
            ),
            Icon(
              Icons.chevron_right,
              color: Colors.white.withOpacity(0.3),
              size: 20,
            ),
          ],
        ),
      ),
    );
  }
}



import 'package:provider/provider.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../../app/theme.dart';
import '../../providers/user_provider.dart';
import '../../services/api_service.dart';
import '../../utils/assets.dart';

/// 个人中心页面 - 精确复刻 Vue.js Profile.vue
class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  List<dynamic> _iconAds = [];
  int _unreadCount = 0;
  bool _signingIn = false;

  @override
  void initState() {
    super.initState();
    _fetchData();
  }

  Future<void> _fetchData() async {
    await Future.wait([
      _fetchIconAds(),
      _fetchUnreadCount(),
    ]);
  }

  Future<void> _fetchIconAds() async {
    try {
      final response = await ApiService.get('/ads/icons');
      setState(() {
        _iconAds = response.data ?? [];
      });
    } catch (e) {
      debugPrint('获取图标广告失败: $e');
    }
  }

  Future<void> _fetchUnreadCount() async {
    try {
      final response = await ApiService.get('/notifications/unread-count');
      setState(() {
        _unreadCount = response.data['count'] ?? 0;
      });
    } catch (e) {
      debugPrint('获取未读数失败: $e');
    }
  }

  Future<void> _handleSign() async {
    if (_signingIn) return;
    setState(() => _signingIn = true);

    try {
      await ApiService.post('/users/sign');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('签到成功！'), backgroundColor: Colors.green),
        );
        context.read<UserProvider>().fetchUser();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('签到失败'), backgroundColor: Colors.red),
        );
      }
    } finally {
      setState(() => _signingIn = false);
    }
  }

  void _copyId(String? id) {
    if (id == null) return;
    Clipboard.setData(ClipboardData(text: id));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('已复制'), duration: Duration(seconds: 1)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A), // Vue: #0a0a0a
      body: Consumer<UserProvider>(
        builder: (context, userProvider, child) {
          final user = userProvider.user;

          return SingleChildScrollView(
            child: Column(
              children: [
                // 顶部头部
                _buildHeader(),

                // 用户信息区域
                _buildUserSection(user),

                // VIP推广条
                _buildVipBanner(user),

                // 三卡片入口
                _buildCardGrid(),

                // 快捷功能
                _buildQuickMenu(),

                // 图标广告位
                _buildAdSection(),

                // 菜单列表
                _buildMenuList(),

                // 底部间距
                const SizedBox(height: 100),
              ],
            ),
          );
        },
      ),
    );
  }

  /// 顶部头部 - 对应 Vue page-header
  Widget _buildHeader() {
    return SafeArea(
      bottom: false,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            // 左侧通知图标
            GestureDetector(
              onTap: () => Navigator.pushNamed(context, '/messages'),
              child: Stack(
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1A1A1A),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Image.asset(
                      AppAssets.mineNotification,
                      color: Colors.white.withOpacity(0.7),
                      errorBuilder: (_, __, ___) => Icon(
                        Icons.notifications_outlined,
                        color: Colors.white.withOpacity(0.7),
                        size: 22,
                      ),
                    ),
                  ),
                  if (_unreadCount > 0)
                    Positioned(
                      right: 0,
                      top: 0,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                        decoration: BoxDecoration(
                          color: Colors.red,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        constraints: const BoxConstraints(minWidth: 16, minHeight: 16),
                        child: Text(
                          _unreadCount > 99 ? '99+' : '$_unreadCount',
                          style: const TextStyle(color: Colors.white, fontSize: 10),
                          textAlign: TextAlign.center,
                        ),
                      ),
                    ),
                ],
              ),
            ),

            // 右侧客服和设置
            Row(
              children: [
                GestureDetector(
                  onTap: () => Navigator.pushNamed(context, '/customer-service'),
                  child: Container(
                    width: 36,
                    height: 36,
                    padding: const EdgeInsets.all(6),
                    margin: const EdgeInsets.only(right: 12),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1A1A1A),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Image.asset(
                      AppAssets.icService,
                      errorBuilder: (_, __, ___) => Icon(
                        Icons.headset_mic_outlined,
                        color: Colors.white.withOpacity(0.7),
                        size: 22,
                      ),
                    ),
                  ),
                ),
                GestureDetector(
                  onTap: () => Navigator.pushNamed(context, '/settings'),
                  child: Container(
                    width: 36,
                    height: 36,
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1A1A1A),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Image.asset(
                      AppAssets.icSetting,
                      errorBuilder: (_, __, ___) => Icon(
                        Icons.settings_outlined,
                        color: Colors.white.withOpacity(0.7),
                        size: 22,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  /// 用户信息区域 - 对应 Vue user-section
  Widget _buildUserSection(user) {
    final isVip = user?.isVip ?? false;
    final vipLevel = user?.vipLevel ?? 0;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            const Color(0xFF1A1A1A),
            const Color(0xFF1A1A1A).withOpacity(0.8),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: [
          // 用户行 - user-row
          Row(
            children: [
              // 头像
              Stack(
                children: [
                  Container(
                    width: 70,
                    height: 70,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: isVip ? AppTheme.vipGradient : AppTheme.primaryGradient,
                      border: Border.all(
                        color: isVip ? AppTheme.vipGold : AppTheme.primaryColor,
                        width: 2,
                      ),
                    ),
                    child: ClipOval(
                      child: user?.avatar != null
                          ? CachedNetworkImage(
                              imageUrl: ApiService.getFullImageUrl(user!.avatar!),
                              fit: BoxFit.cover,
                            )
                          : const Icon(Icons.person, color: Colors.white, size: 35),
                    ),
                  ),
                  // VIP皇冠
                  if (isVip)
                    Positioned(
                      bottom: 0,
                      right: 0,
                      child: Container(
                        width: 22,
                        height: 22,
                        decoration: const BoxDecoration(
                          shape: BoxShape.circle,
                          gradient: AppTheme.vipGradient,
                        ),
                        child: const Icon(Icons.workspace_premium, color: Colors.black, size: 14),
                      ),
                    ),
                  // 性别图标
                  Positioned(
                    top: 0,
                    right: 0,
                    child: Container(
                      width: 18,
                      height: 18,
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        color: Color(0xFF4A90E2),
                      ),
                      child: const Center(
                        child: Text('♂', style: TextStyle(color: Colors.white, fontSize: 12)),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(width: 16),

              // 用户信息
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // 昵称行
                    Row(
                      children: [
                        Text(
                          user?.displayName ?? '未登录',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        if (vipLevel > 0) ...[
                          const SizedBox(width: 8),
                          Image.asset(
                            AppAssets.getVipIcon(vipLevel),
                            width: 50,
                            height: 20,
                            fit: BoxFit.contain,
                            errorBuilder: (_, __, ___) => _buildVipBadge(vipLevel),
                          ),
                        ],
                      ],
                    ),
                    const SizedBox(height: 6),
                    // 用户ID行
                    Row(
                      children: [
                        Text(
                          user?.username ?? '--------',
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.5),
                            fontSize: 13,
                          ),
                        ),
                        if (user?.username != null) ...[
                          const SizedBox(width: 8),
                          GestureDetector(
                            onTap: () => _copyId(user?.username),
                            child: Icon(
                              Icons.copy,
                              color: Colors.white.withOpacity(0.5),
                              size: 14,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ],
                ),
              ),

              // 签到按钮
              GestureDetector(
                onTap: _handleSign,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    gradient: AppTheme.primaryGradient,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Image.asset(
                        AppAssets.icSign,
                        width: 18,
                        height: 18,
                        errorBuilder: (_, __, ___) => const Icon(
                          Icons.calendar_today,
                          color: Colors.white,
                          size: 16,
                        ),
                      ),
                      const SizedBox(width: 4),
                      Text(
                        _signingIn ? '签到中...' : '签到',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),

          // 统计行 - stats-row
          Row(
            children: [
              Expanded(
                child: _buildStatItem(user?.coins ?? 0, '缓存视频'),
              ),
              Container(
                width: 1,
                height: 30,
                color: Colors.white.withOpacity(0.1),
              ),
              Expanded(
                child: _buildStatItem(0, '剩余AI脱衣次数'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildVipBadge(int level) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        gradient: AppTheme.vipGradient,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Text(
        'VIP$level',
        style: const TextStyle(
          color: Colors.black,
          fontSize: 11,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _buildStatItem(int value, String label) {
    return Column(
      children: [
        Text(
          '$value',
          style: const TextStyle(
            color: Colors.white,
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: TextStyle(
            color: Colors.white.withOpacity(0.5),
            fontSize: 12,
          ),
        ),
      ],
    );
  }

  /// VIP推广条 - 对应 Vue vip-banner
  Widget _buildVipBanner(user) {
    final isVip = user?.isVip ?? false;
    final vipLevel = user?.vipLevel ?? 0;

    return GestureDetector(
      onTap: () => Navigator.pushNamed(context, '/vip'),
      child: Container(
        margin: const EdgeInsets.all(16),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF2D1F3D), Color(0xFF1A1225)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: const Color(0xFFFFD700).withOpacity(0.3),
            width: 1,
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            // 左侧文字
            isVip
                ? Row(
                    children: [
                      Image.asset(
                        AppAssets.getVipIcon(vipLevel),
                        width: 60,
                        height: 24,
                        fit: BoxFit.contain,
                        errorBuilder: (_, __, ___) => _buildVipBadge(vipLevel),
                      ),
                      const SizedBox(width: 12),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          ShaderMask(
                            shaderCallback: (bounds) => const LinearGradient(
                              colors: [Color(0xFFFFE066), Color(0xFFFFAA00)],
                            ).createShader(bounds),
                            child: Text(
                              '到期时间：${user?.vipExpireTime != null ? _formatDate(user!.vipExpireTime!) : "永久"}',
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 12,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  )
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      ShaderMask(
                        shaderCallback: (bounds) => const LinearGradient(
                          colors: [Color(0xFFFFE066), Color(0xFFFFAA00)],
                        ).createShader(bounds),
                        child: const Text(
                          '开通会员',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '享专属特权',
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.6),
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),

            // 右侧按钮
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                gradient: AppTheme.vipGradient,
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    isVip ? '升级会员' : '开通会员',
                    style: const TextStyle(
                      color: Colors.black,
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(width: 4),
                  Container(
                    width: 18,
                    height: 18,
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.2),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.chevron_right,
                      color: Colors.black,
                      size: 14,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatDate(DateTime date) {
    return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
  }

  /// 三卡片入口 - 对应 Vue card-grid
  Widget _buildCardGrid() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        children: [
          Expanded(child: _buildFeatureCard('VIP特权', AppAssets.vipCenter, '/vip')),
          const SizedBox(width: 10),
          Expanded(child: _buildFeatureCard('我的钱包', AppAssets.myWallet, '/wallet')),
          const SizedBox(width: 10),
          Expanded(child: _buildFeatureCard('代理赚钱', AppAssets.agent, '/agent')),
        ],
      ),
    );
  }

  Widget _buildFeatureCard(String title, String asset, String route) {
    return GestureDetector(
      onTap: () => Navigator.pushNamed(context, route),
      child: Container(
        height: 70,
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF1E1E2E), Color(0xFF151520)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: AppTheme.primaryColor.withOpacity(0.2),
            width: 1,
          ),
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(12),
          child: Image.asset(
            asset,
            fit: BoxFit.cover,
            errorBuilder: (_, __, ___) => Center(
              child: Text(
                title,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  /// 快捷功能 - 对应 Vue quick-menu
  Widget _buildQuickMenu() {
    final menuItems = [
      {'icon': AppAssets.icHistory, 'label': '观看记录', 'route': '/history'},
      {'icon': AppAssets.icCollect, 'label': '我的收藏', 'route': '/favorites'},
      {'icon': AppAssets.icBuy, 'label': '我的购买', 'route': '/purchases'},
      {'icon': AppAssets.icAi, 'label': 'AI女友', 'route': '/ai'},
    ];

    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A1A),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: menuItems.map((item) {
          return GestureDetector(
            onTap: () => Navigator.pushNamed(context, item['route'] as String),
            child: Column(
              children: [
                Container(
                  width: 44,
                  height: 44,
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: const Color(0xFF252525),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Image.asset(
                    item['icon'] as String,
                    errorBuilder: (_, __, ___) => const Icon(
                      Icons.folder_outlined,
                      color: Colors.white54,
                      size: 20,
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  item['label'] as String,
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.8),
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  /// 图标广告位 - 对应 Vue ad-section
  Widget _buildAdSection() {
    if (_iconAds.isEmpty) return const SizedBox();

    final row1 = _iconAds.take(5).toList();
    final row2 = _iconAds.length > 5 ? _iconAds.skip(5).toList() : [];

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        children: [
          // 第一行固定
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: row1.map((ad) => _buildAdItem(ad)).toList(),
          ),

          // 第二行滚动
          if (row2.isNotEmpty) ...[
            const SizedBox(height: 12),
            SizedBox(
              height: 80,
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                itemCount: row2.length,
                itemBuilder: (context, index) {
                  return Padding(
                    padding: const EdgeInsets.only(right: 16),
                    child: _buildAdItem(row2[index]),
                  );
                },
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildAdItem(dynamic ad) {
    return GestureDetector(
      onTap: () {},
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  AppTheme.primaryColor.withOpacity(0.2),
                  AppTheme.secondaryColor.withOpacity(0.2),
                ],
              ),
              borderRadius: BorderRadius.circular(14),
            ),
            child: ad['image'] != null
                ? ClipRRect(
                    borderRadius: BorderRadius.circular(14),
                    child: CachedNetworkImage(
                      imageUrl: ApiService.getFullImageUrl(ad['image']),
                      fit: BoxFit.cover,
                      errorWidget: (_, __, ___) => Center(
                        child: Text(
                          ad['icon'] ?? '📦',
                          style: const TextStyle(fontSize: 24),
                        ),
                      ),
                    ),
                  )
                : Center(
                    child: Text(
                      ad['icon'] ?? '📦',
                      style: const TextStyle(fontSize: 24),
                    ),
                  ),
          ),
          const SizedBox(height: 6),
          Text(
            ad['name'] ?? '',
            style: TextStyle(
              fontSize: 11,
              color: Colors.white.withOpacity(0.7),
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }

  /// 菜单列表 - 对应 Vue menu-section
  Widget _buildMenuList() {
    final menuItems = [
      {'icon': Icons.dashboard_outlined, 'label': '创作中心', 'route': '/creator-center'},
      {'icon': Icons.share_outlined, 'label': '分享邀请', 'route': '/invite-share'},
      {'icon': Icons.apps_outlined, 'label': '应用推荐', 'route': '/app-recommend'},
      {'icon': Icons.group_outlined, 'label': '官方群组', 'route': '/groups'},
      {'icon': Icons.headset_mic_outlined, 'label': '联系客服', 'route': '/customer-service'},
    ];

    return Container(
      margin: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A1A),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: menuItems.asMap().entries.map((entry) {
          final index = entry.key;
          final item = entry.value;
          final isLast = index == menuItems.length - 1;

          return Column(
            children: [
              _buildMenuItem(
                item['icon'] as IconData,
                item['label'] as String,
                item['route'] as String,
              ),
              if (!isLast)
                Divider(
                  height: 1,
                  color: Colors.white.withOpacity(0.06),
                  indent: 52,
                ),
            ],
          );
        }).toList(),
      ),
    );
  }

  Widget _buildMenuItem(IconData icon, String label, String route) {
    return GestureDetector(
      onTap: () => Navigator.pushNamed(context, route),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(
          children: [
            Icon(
              icon,
              color: Colors.white.withOpacity(0.7),
              size: 22,
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Text(
                label,
                style: TextStyle(
                  color: Colors.white.withOpacity(0.9),
                  fontSize: 15,
                ),
              ),
            ),
            Icon(
              Icons.chevron_right,
              color: Colors.white.withOpacity(0.3),
              size: 20,
            ),
          ],
        ),
      ),
    );
  }
}