import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../app/routes.dart';
import '../../../app/theme.dart';
import '../../../core/providers/video_provider.dart';
import '../../../core/providers/auth_provider.dart';
import '../widgets/video_grid.dart';
import '../widgets/category_tabs.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;
  int? _selectedCategoryId;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    final videoProvider = context.read<VideoProvider>();
    await videoProvider.loadCategories();
    await videoProvider.loadVideos(refresh: true);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: [
          _buildHomePage(),
          _buildShortsPage(),
          _buildProfilePage(),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_outlined),
            activeIcon: Icon(Icons.home),
            label: '首页',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.play_circle_outline),
            activeIcon: Icon(Icons.play_circle),
            label: '短视频',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person_outline),
            activeIcon: Icon(Icons.person),
            label: '我的',
          ),
        ],
      ),
    );
  }

  Widget _buildHomePage() {
    return SafeArea(
      child: Column(
        children: [
          // 顶部栏
          Padding(
            padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 8.h),
            child: Row(
              children: [
                Text(
                  'VOD 视频',
                  style: TextStyle(
                    fontSize: 22.sp,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.textPrimary,
                  ),
                ),
                const Spacer(),
                IconButton(
                  icon: const Icon(Icons.search),
                  onPressed: () {
                    Navigator.pushNamed(context, AppRoutes.search);
                  },
                ),
              ],
            ),
          ),
          
          // 分类标签
          Consumer<VideoProvider>(
            builder: (context, provider, _) {
              return CategoryTabs(
                categories: provider.categories,
                selectedId: _selectedCategoryId,
                onSelected: (id) {
                  setState(() {
                    _selectedCategoryId = id;
                  });
                  provider.loadVideos(
                    categoryId: id,
                    refresh: true,
                  );
                },
              );
            },
          ),
          
          // 视频列表
          Expanded(
            child: Consumer<VideoProvider>(
              builder: (context, provider, _) {
                return VideoGrid(
                  videos: provider.videos,
                  isLoading: provider.isLoading,
                  hasMore: provider.hasMore,
                  onRefresh: () => provider.loadVideos(
                    categoryId: _selectedCategoryId,
                    refresh: true,
                  ),
                  onLoadMore: () => provider.loadVideos(
                    categoryId: _selectedCategoryId,
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildShortsPage() {
    return const Center(
      child: Text(
        '短视频',
        style: TextStyle(color: AppTheme.textPrimary),
      ),
    );
  }

  Widget _buildProfilePage() {
    return SafeArea(
      child: Consumer<AuthProvider>(
        builder: (context, auth, _) {
          final user = auth.user;
          
          return ListView(
            padding: EdgeInsets.all(16.w),
            children: [
              // 用户信息卡片
              Container(
                padding: EdgeInsets.all(16.w),
                decoration: BoxDecoration(
                  color: AppTheme.cardColor,
                  borderRadius: BorderRadius.circular(12.r),
                ),
                child: Row(
                  children: [
                    CircleAvatar(
                      radius: 30.r,
                      backgroundColor: AppTheme.primaryColor,
                      child: Text(
                        user?.displayName.substring(0, 1).toUpperCase() ?? 'U',
                        style: TextStyle(
                          fontSize: 24.sp,
                          color: Colors.white,
                        ),
                      ),
                    ),
                    SizedBox(width: 16.w),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            user?.displayName ?? '未登录',
                            style: TextStyle(
                              fontSize: 18.sp,
                              fontWeight: FontWeight.bold,
                              color: AppTheme.textPrimary,
                            ),
                          ),
                          SizedBox(height: 4.h),
                          if (user?.isVip == true)
                            Container(
                              padding: EdgeInsets.symmetric(
                                horizontal: 8.w,
                                vertical: 2.h,
                              ),
                              decoration: BoxDecoration(
                                gradient: const LinearGradient(
                                  colors: [Color(0xFFFFD700), Color(0xFFFFA500)],
                                ),
                                borderRadius: BorderRadius.circular(4.r),
                              ),
                              child: Text(
                                user?.vipLevelName ?? 'VIP',
                                style: TextStyle(
                                  fontSize: 12.sp,
                                  color: Colors.black,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            )
                          else
                            Text(
                              '普通用户',
                              style: TextStyle(
                                fontSize: 14.sp,
                                color: AppTheme.textSecondary,
                              ),
                            ),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.chevron_right),
                      onPressed: () {},
                    ),
                  ],
                ),
              ),
              SizedBox(height: 16.h),
              
              // VIP 入口
              if (user?.isVip != true)
                GestureDetector(
                  onTap: () {
                    Navigator.pushNamed(context, AppRoutes.vip);
                  },
                  child: Container(
                    padding: EdgeInsets.all(16.w),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFF6366F1), Color(0xFF8B5CF6)],
                      ),
                      borderRadius: BorderRadius.circular(12.r),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.diamond, color: Colors.white, size: 32.w),
                        SizedBox(width: 12.w),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '开通 VIP 会员',
                                style: TextStyle(
                                  fontSize: 16.sp,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.white,
                                ),
                              ),
                              Text(
                                '畅享全站精彩内容',
                                style: TextStyle(
                                  fontSize: 12.sp,
                                  color: Colors.white70,
                                ),
                              ),
                            ],
                          ),
                        ),
                        Container(
                          padding: EdgeInsets.symmetric(
                            horizontal: 12.w,
                            vertical: 6.h,
                          ),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(16.r),
                          ),
                          child: Text(
                            '立即开通',
                            style: TextStyle(
                              fontSize: 12.sp,
                              color: AppTheme.primaryColor,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              SizedBox(height: 16.h),
              
              // 功能列表
              _buildMenuItem(Icons.history, '观看历史', () {}),
              _buildMenuItem(Icons.favorite_border, '我的收藏', () {}),
              _buildMenuItem(Icons.download_outlined, '我的下载', () {}),
              _buildMenuItem(Icons.card_giftcard, '邀请好友', () {}),
              _buildMenuItem(Icons.settings_outlined, '设置', () {}),
              
              SizedBox(height: 24.h),
              
              // 退出登录
              TextButton(
                onPressed: () async {
                  await auth.logout();
                  if (mounted) {
                    Navigator.pushReplacementNamed(context, AppRoutes.login);
                  }
                },
                child: const Text(
                  '退出登录',
                  style: TextStyle(color: Colors.red),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildMenuItem(IconData icon, String title, VoidCallback onTap) {
    return ListTile(
      leading: Icon(icon, color: AppTheme.textSecondary),
      title: Text(
        title,
        style: TextStyle(
          fontSize: 16.sp,
          color: AppTheme.textPrimary,
        ),
      ),
      trailing: const Icon(Icons.chevron_right, color: AppTheme.textSecondary),
      onTap: onTap,
    );
  }
}
