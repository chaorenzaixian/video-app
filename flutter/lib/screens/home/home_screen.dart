import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:carousel_slider/carousel_slider.dart' as carousel;
import 'package:cached_network_image/cached_network_image.dart';
import '../../app/theme.dart';
import '../../providers/app_provider.dart';
import '../../models/video.dart';
import '../../services/api_service.dart';
import '../../widgets/video_card.dart';
import '../../utils/assets.dart';

/// 首页 - 完全复刻 Vue.js Home.vue
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  // 数据
  List<Video> _videos = [];
  List<dynamic> _categories = [];
  List<dynamic> _banners = [];
  List<dynamic> _iconAdsRow1 = [];
  List<dynamic> _iconAdsRow2 = [];
  List<dynamic> _funcItems = [];
  List<dynamic> _subCategories = [];
  List<dynamic> _announcements = [];
  
  // 状态
  bool _isLoading = false;
  String? _errorMessage;
  int _currentPage = 1;
  int _activeCategory = 0;
  int _activeVideoFilter = 0;
  int _gridMode = 2; // 1=单列, 2=双列
  bool _showNavDrawer = false;
  bool _showPromo = true;
  int _currentBannerIndex = 0;
  
  // 滚动控制器
  final ScrollController _scrollController = ScrollController();
  final ScrollController _categoryScrollController = ScrollController();
  Timer? _bannerTimer;
  Timer? _scrollAdTimer;
  double _scrollAdOffset = 0;

  // 视频筛选选项
  final List<Map<String, String>> _videoFilters = [
    {'label': '最新', 'key': 'created_at'},
    {'label': '最热', 'key': 'view_count'},
    {'label': 'VIP', 'key': 'vip'},
  ];

  @override
  void initState() {
    super.initState();
    _fetchAllData();
    _startBannerAutoPlay();
    _startScrollAdAnimation();
  }

  @override
  void dispose() {
    _scrollController.dispose();
    _categoryScrollController.dispose();
    _bannerTimer?.cancel();
    _scrollAdTimer?.cancel();
    super.dispose();
  }

  // 获取所有数据
  Future<void> _fetchAllData() async {
    setState(() => _isLoading = true);
    await Future.wait([
      _fetchCategories(),
      _fetchBanners(),
      _fetchIconAds(),
      _fetchFuncEntries(),
      _fetchVideos(refresh: true),
      _fetchAnnouncements(),
    ]);
    setState(() => _isLoading = false);
  }

  // 获取分类
  Future<void> _fetchCategories() async {
    try {
      final response = await ApiService.get('/videos/categories');
      final data = response.data;
      if (data != null && data is List) {
        setState(() {
          _categories = [
            {'id': 0, 'name': '推荐'},
            ...data,
          ];
        });
      }
    } catch (e) {
      debugPrint('获取分类失败: $e');
    }
  }

  // 获取轮播图
  Future<void> _fetchBanners() async {
    try {
      final response = await ApiService.get('/home/banners', params: {'position': 'home'});
      setState(() {
        _banners = response.data ?? [];
      });
    } catch (e) {
      debugPrint('获取轮播图失败: $e');
    }
  }

  // 获取图标广告
  Future<void> _fetchIconAds() async {
    try {
      final response = await ApiService.get('/ads/icons');
      final data = response.data ?? [];
      setState(() {
        _iconAdsRow1 = data.length > 5 ? data.sublist(0, 5) : data;
        _iconAdsRow2 = data.length > 5 ? data.sublist(5, data.length > 10 ? 10 : data.length) : [];
      });
    } catch (e) {
      debugPrint('获取图标广告失败: $e');
    }
  }

  // 获取功能入口
  Future<void> _fetchFuncEntries() async {
    try {
      final response = await ApiService.get('/ads/func-entries');
      setState(() {
        _funcItems = response.data ?? [];
      });
    } catch (e) {
      debugPrint('获取功能入口失败: $e');
    }
  }

  // 获取公告
  Future<void> _fetchAnnouncements() async {
    try {
      final response = await ApiService.get('/ads/announcements');
      setState(() {
        _announcements = response.data ?? [];
      });
    } catch (e) {
      debugPrint('获取公告失败: $e');
    }
  }

  // 获取视频列表
  Future<void> _fetchVideos({bool refresh = false}) async {
    try {
      if (refresh) _currentPage = 1;
      
      final params = <String, dynamic>{
        'page': _currentPage,
        'page_size': 20,
        'sort_by': _videoFilters[_activeVideoFilter]['key'],
      };
      
      if (_activeCategory != 0) {
        params['category_id'] = _activeCategory;
      }

      final response = await ApiService.get('/videos', params: params);
      final data = response.data;
      debugPrint('📺 视频API响应: $data');
      debugPrint('📺 data类型: ${data.runtimeType}');
      
      // 处理不同的响应格式
      List<dynamic> videoList = [];
      if (data is List) {
        videoList = data;
      } else if (data is Map) {
        videoList = data['items'] ?? data['videos'] ?? data['data'] ?? [];
      }
      debugPrint('📺 视频数量: ${videoList.length}');
      
      final List<Video> newVideos = videoList
          .map<Video>((json) => Video.fromJson(json))
          .toList();

      setState(() {
        _errorMessage = null;
        if (refresh) {
          _videos = newVideos;
        } else {
          _videos.addAll(newVideos);
        }
        _currentPage++;
      });
    } catch (e) {
      setState(() {
        _errorMessage = '加载失败: $e';
      });
    }
  }

  // 开始轮播自动播放
  void _startBannerAutoPlay() {
    _bannerTimer = Timer.periodic(const Duration(seconds: 4), (timer) {
      if (_banners.isNotEmpty) {
        setState(() {
          _currentBannerIndex = (_currentBannerIndex + 1) % _banners.length;
        });
      }
    });
  }

  // 开始滚动广告动画
  void _startScrollAdAnimation() {
    _scrollAdTimer = Timer.periodic(const Duration(milliseconds: 50), (timer) {
      setState(() {
        _scrollAdOffset += 0.5;
      });
    });
  }

  // 选择分类
  void _selectCategory(int catId) {
    setState(() {
      _activeCategory = catId;
    });
    _fetchVideos(refresh: true);
    // 滚动到选中的分类
    _scrollToCategory(catId);
  }

  // 滚动到选中的分类
  void _scrollToCategory(int catId) {
    final index = _categories.indexWhere((c) => c['id'] == catId);
    if (index != -1 && _categoryScrollController.hasClients) {
      final offset = (index * 70.0) - 100;
      _categoryScrollController.animateTo(
        offset.clamp(0, _categoryScrollController.position.maxScrollExtent),
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    }
  }

  // 切换视频筛选
  void _changeVideoFilter(int index) {
    setState(() {
      _activeVideoFilter = index;
    });
    _fetchVideos(refresh: true);
  }

  // 格式化播放量
  String _formatCount(int? count) {
    if (count == null) return '0';
    if (count >= 10000) {
      return '${(count / 10000).toStringAsFixed(1)}W';
    }
    return count.toString();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      body: Stack(
        children: [
          // 主体内容
          Column(
            children: [
              // 安全区域
              SizedBox(height: MediaQuery.of(context).padding.top),
              
              // 固定头部
              _buildHeader(),
              
              // 分类导航
              _buildCategoryNav(),
              
              // 可滚动内容
              Expanded(
                child: RefreshIndicator(
                  onRefresh: _fetchAllData,
                  color: AppTheme.primaryColor,
                  child: CustomScrollView(
                    controller: _scrollController,
                    slivers: [
                      // 轮播广告
                      SliverToBoxAdapter(child: _buildBanner()),
                      
                      // 固定图标广告位
                      SliverToBoxAdapter(child: _buildPromoGridFixed()),
                      
                      // 滚动图标广告位
                      SliverToBoxAdapter(child: _buildPromoGridScroll()),
                      
                      // 功能入口
                      SliverToBoxAdapter(child: _buildFuncScroll()),
                      
                      // 热门标签/二级分类
                      SliverToBoxAdapter(child: _buildHotSection()),
                      
                      // 视频筛选栏
                      SliverToBoxAdapter(child: _buildFilterBar()),
                      
                      // 视频列表
                      _buildVideoGrid(),
                      
                      // 底部间距
                      const SliverToBoxAdapter(child: SizedBox(height: 100)),
                    ],
                  ),
                ),
              ),
            ],
          ),

          // 底部公告条
          if (_showPromo && _announcements.isNotEmpty)
            Positioned(
              bottom: 60,
              left: 0,
              right: 0,
              child: _buildBottomPromo(),
            ),

          // 短视频浮动入口
          _buildShortVideoFloat(),

          // 导航抽屉遮罩
          if (_showNavDrawer)
            GestureDetector(
              onTap: () => setState(() => _showNavDrawer = false),
              child: Container(
                color: Colors.black.withOpacity(0.5),
              ),
            ),

          // 导航抽屉
          if (_showNavDrawer) _buildNavDrawer(),
        ],
      ),
    );
  }

  /// 顶部头部 - 对应 .header-top
  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      child: Row(
        children: [
          // 左边福利图标 - .welfare-icon
          Expanded(
            child: GestureDetector(
              onTap: () => Navigator.pushNamed(context, '/vip'),
              child: Align(
                alignment: Alignment.centerLeft,
                child: Image.asset(
                  AppAssets.fuli,
                  width: 42,
                  height: 42,
                  fit: BoxFit.contain,
                  errorBuilder: (_, __, ___) => Container(
                    width: 42,
                    height: 42,
                    decoration: BoxDecoration(
                      gradient: AppTheme.primaryGradient,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Center(
                      child: Text('福利', style: TextStyle(color: Colors.white, fontSize: 12)),
                    ),
                  ),
                ),
              ),
            ),
          ),

          // 中间 Logo - .header-center
          Expanded(
            flex: 2,
            child: Center(
              child: Image.asset(
                AppAssets.soulTitle,
                height: 36,
                fit: BoxFit.contain,
                errorBuilder: (_, __, ___) => ShaderMask(
                  shaderCallback: (bounds) => const LinearGradient(
                    colors: [Colors.white, Colors.white, Color(0xFFA855F7)],
                    stops: [0.0, 0.6, 1.0],
                  ).createShader(bounds),
                  child: const Text(
                    'Soul',
                    style: TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.w300,
                      fontStyle: FontStyle.italic,
                      color: Colors.white,
                      letterSpacing: 2,
                    ),
                  ),
                ),
              ),
            ),
          ),

          // 右边搜索和菜单 - .header-right
          Expanded(
            child: Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                // 搜索图标
                GestureDetector(
                  onTap: () => Navigator.pushNamed(context, '/search'),
                  child: Image.asset(
                    AppAssets.icSearch,
                    width: 28,
                    height: 28,
                    fit: BoxFit.contain,
                    errorBuilder: (_, __, ___) => Icon(
                      Icons.search,
                      color: Colors.white.withOpacity(0.8),
                      size: 24,
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                // 菜单图标
                GestureDetector(
                  onTap: () => setState(() => _showNavDrawer = true),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: List.generate(3, (i) => Container(
                      width: 20,
                      height: 2,
                      margin: EdgeInsets.only(bottom: i < 2 ? 5 : 0),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.8),
                        borderRadius: BorderRadius.circular(1),
                      ),
                    )),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// 分类导航 - .category-nav
  Widget _buildCategoryNav() {
    return SizedBox(
      height: 48,
      child: ListView.builder(
        controller: _categoryScrollController,
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 14),
        itemCount: _categories.length,
        itemBuilder: (context, index) {
          final cat = _categories[index];
          final isActive = _activeCategory == cat['id'];
          
          return GestureDetector(
            onTap: () => _selectCategory(cat['id']),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    cat['name'] ?? '',
                    style: TextStyle(
                      fontSize: 15,
                      color: isActive ? Colors.white : Colors.white.withOpacity(0.6),
                      fontWeight: isActive ? FontWeight.w600 : FontWeight.normal,
                    ),
                  ),
                  const SizedBox(height: 4),
                  // 下划线
                  if (isActive)
                    Container(
                      width: 20,
                      height: 3,
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFFA855F7), Color(0xFF6366F1)],
                        ),
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  /// 轮播广告 - .banner-carousel
  Widget _buildBanner() {
    if (_banners.isEmpty) return const SizedBox();
    
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      child: Column(
        children: [
          AspectRatio(
            aspectRatio: 750 / 300,
            child: ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: PageView.builder(
                itemCount: _banners.length,
                onPageChanged: (index) {
                  setState(() => _currentBannerIndex = index);
                },
                itemBuilder: (context, index) {
                  final banner = _banners[index];
                  final imageUrl = ApiService.getFullImageUrl(banner['image_url']);
                  return GestureDetector(
                    onTap: () => _handleBannerClick(banner),
                    child: CachedNetworkImage(
                      imageUrl: imageUrl,
                      fit: BoxFit.cover,
                      placeholder: (_, __) => Container(color: const Color(0xFF1A1A1A)),
                      errorWidget: (_, __, ___) => Container(color: const Color(0xFF1A1A1A)),
                    ),
                  );
                },
              ),
            ),
          ),
          // 指示点
          if (_banners.length > 1)
            Padding(
              padding: const EdgeInsets.only(top: 10),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(_banners.length, (index) {
                  final isActive = _currentBannerIndex == index;
                  return Container(
                    width: isActive ? 18 : 6,
                    height: 6,
                    margin: const EdgeInsets.symmetric(horizontal: 3),
                    decoration: BoxDecoration(
                      color: isActive ? Colors.white : Colors.white.withOpacity(0.4),
                      borderRadius: BorderRadius.circular(3),
                    ),
                  );
                }),
              ),
            ),
        ],
      ),
    );
  }

  // 处理轮播点击
  void _handleBannerClick(dynamic banner) {
    final linkType = banner['link_type'] ?? 'url';
    final linkUrl = banner['link_url'];
    
    if (linkUrl == null) return;
    
    if (linkType == 'video') {
      Navigator.pushNamed(context, '/video/$linkUrl');
    } else if (linkType == 'vip') {
      Navigator.pushNamed(context, '/vip');
    }
    // 其他类型可以用 url_launcher 打开外部链接
  }

  /// 固定图标广告位 - .promo-grid-fixed
  Widget _buildPromoGridFixed() {
    if (_iconAdsRow1.isEmpty) return const SizedBox();
    
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: _iconAdsRow1.map((ad) => _buildPromoItem(ad)).toList(),
      ),
    );
  }

  /// 滚动图标广告位 - .promo-scroll-container
  Widget _buildPromoGridScroll() {
    if (_iconAdsRow2.isEmpty) return const SizedBox();
    
    // 复制列表实现无限滚动
    final doubleList = [..._iconAdsRow2, ..._iconAdsRow2];
    
    return SizedBox(
      height: 90,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 6),
        itemCount: doubleList.length,
        itemBuilder: (context, index) => _buildPromoItem(doubleList[index]),
      ),
    );
  }

  /// 广告项 - .promo-item
  Widget _buildPromoItem(dynamic ad) {
    final imageUrl = ApiService.getFullImageUrl(ad['image'] ?? '');
    final bg = ad['bg'] ?? '#6366f1';
    
    return GestureDetector(
      onTap: () => _handleAdClick(ad),
      child: Container(
        width: 70,
        margin: const EdgeInsets.symmetric(horizontal: 4),
        child: Column(
          children: [
            // 图标
            Container(
              width: 60,
              height: 60,
              decoration: BoxDecoration(
                color: _parseColor(bg),
                borderRadius: BorderRadius.circular(12),
              ),
              clipBehavior: Clip.antiAlias,
              child: imageUrl.isNotEmpty
                  ? CachedNetworkImage(
                      imageUrl: imageUrl,
                      fit: BoxFit.cover,
                      errorWidget: (_, __, ___) => Center(
                        child: Text(
                          ad['icon'] ?? '📦',
                          style: const TextStyle(fontSize: 28),
                        ),
                      ),
                    )
                  : Center(
                      child: Text(
                        ad['icon'] ?? '📦',
                        style: const TextStyle(fontSize: 28),
                      ),
                    ),
            ),
            const SizedBox(height: 6),
            // 名称
            Text(
              ad['name'] ?? '',
              style: TextStyle(
                fontSize: 12,
                color: Colors.white.withOpacity(0.7),
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  // 解析颜色
  Color _parseColor(String colorStr) {
    if (colorStr.startsWith('#')) {
      return Color(int.parse(colorStr.substring(1), radix: 16) + 0xFF000000);
    }
    return const Color(0xFF6366F1);
  }

  // 处理广告点击
  void _handleAdClick(dynamic ad) {
    final link = ad['link'] ?? ad['link_url'];
    if (link != null && link.toString().isNotEmpty) {
      if (link.toString().startsWith('/')) {
        Navigator.pushNamed(context, link);
      }
    }
  }

  /// 功能入口 - .func-scroll-wrapper
  Widget _buildFuncScroll() {
    if (_funcItems.isEmpty) return const SizedBox();
    
    return SizedBox(
      height: 95,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        itemCount: _funcItems.length,
        itemBuilder: (context, index) {
          final func = _funcItems[index];
          final imageUrl = ApiService.getFullImageUrl(func['image'] ?? '');
          
          return GestureDetector(
            onTap: () => _handleFuncClick(func),
            child: Container(
              width: 72,
              margin: const EdgeInsets.only(right: 16),
              child: Column(
                children: [
                  // 图标盒子 - .func-icon-box
                  Container(
                    width: 56,
                    height: 56,
                    decoration: BoxDecoration(
                      gradient: imageUrl.isEmpty
                          ? const LinearGradient(
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                              colors: [Color(0xFF6366F1), Color(0xFF8B5CF6)],
                            )
                          : null,
                      borderRadius: BorderRadius.circular(14),
                    ),
                    clipBehavior: Clip.antiAlias,
                    child: imageUrl.isNotEmpty
                        ? CachedNetworkImage(
                            imageUrl: imageUrl,
                            fit: BoxFit.cover,
                            errorWidget: (_, __, ___) => Center(
                              child: Text(
                                _getFuncShortName(func['name'] ?? ''),
                                style: const TextStyle(
                                  fontSize: 22,
                                  fontWeight: FontWeight.w500,
                                  color: Colors.white,
                                ),
                              ),
                            ),
                          )
                        : Center(
                            child: Text(
                              _getFuncShortName(func['name'] ?? ''),
                              style: const TextStyle(
                                fontSize: 22,
                                fontWeight: FontWeight.w500,
                                color: Colors.white,
                              ),
                            ),
                          ),
                  ),
                  const SizedBox(height: 8),
                  // 名称
                  Text(
                    func['name'] ?? '',
                    style: TextStyle(
                      fontSize: 13,
                      color: Colors.white.withOpacity(0.85),
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  // 获取功能简称
  String _getFuncShortName(String name) {
    final shortNames = {
      '广场': '广',
      'AI广场': 'A',
      '会员中心': '会',
      '社区广场': '社',
      '分享邀请': '分',
      '排行榜': '排',
      '签到福利': '签',
    };
    return shortNames[name] ?? (name.isNotEmpty ? name[0] : '');
  }

  // 处理功能入口点击
  void _handleFuncClick(dynamic func) {
    final link = func['link'] ?? func['link_url'];
    if (link != null && link.toString().isNotEmpty) {
      if (link.toString().startsWith('/')) {
        Navigator.pushNamed(context, link);
      }
    }
  }

  /// 热门标签区域 - .hot-section
  Widget _buildHotSection() {
    if (_subCategories.isEmpty) return const SizedBox();
    
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      child: Wrap(
        spacing: 10,
        runSpacing: 10,
        children: _subCategories.map((subCat) {
          return GestureDetector(
            onTap: () => Navigator.pushNamed(context, '/category/${subCat['id']}'),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.08),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                subCat['name'] ?? '',
                style: TextStyle(
                  fontSize: 13,
                  color: Colors.white.withOpacity(0.75),
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  /// 视频筛选栏 - .filter-bar
  Widget _buildFilterBar() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 6),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
      decoration: BoxDecoration(
        color: const Color(0xFF0A0A0A),
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(12),
          topRight: Radius.circular(12),
        ),
        border: Border(
          bottom: BorderSide(color: Colors.white.withOpacity(0.06)),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // 筛选标签 - .filter-tabs
          Row(
            children: List.generate(_videoFilters.length, (index) {
              final isActive = _activeVideoFilter == index;
              return GestureDetector(
                onTap: () => _changeVideoFilter(index),
                child: Container(
                  margin: const EdgeInsets.only(right: 20),
                  child: Column(
                    children: [
                      Text(
                        _videoFilters[index]['label']!,
                        style: TextStyle(
                          fontSize: 14,
                          color: isActive ? Colors.white : Colors.white.withOpacity(0.5),
                          fontWeight: isActive ? FontWeight.w600 : FontWeight.normal,
                        ),
                      ),
                      const SizedBox(height: 4),
                      if (isActive)
                        Container(
                          width: 20,
                          height: 2,
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(
                              colors: [Color(0xFFA855F7), Color(0xFF7C3AED)],
                            ),
                            borderRadius: BorderRadius.circular(1),
                          ),
                        ),
                    ],
                  ),
                ),
              );
            }),
          ),
          
          // 切换按钮 - .view-toggle
          GestureDetector(
            onTap: () {
              setState(() {
                _gridMode = _gridMode == 1 ? 2 : 1;
              });
            },
            child: Row(
              children: [
                Text(
                  '切换',
                  style: TextStyle(
                    fontSize: 13,
                    color: Colors.white.withOpacity(0.7),
                  ),
                ),
                const SizedBox(width: 4),
                // 切换图标
                _gridMode == 1
                    ? _buildListIcon()
                    : _buildGridIcon(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // 列表图标
  Widget _buildListIcon() {
    return Column(
      children: List.generate(3, (i) => Container(
        width: 16,
        height: 2,
        margin: EdgeInsets.only(bottom: i < 2 ? 2 : 0),
        color: Colors.white.withOpacity(0.8),
      )),
    );
  }

  // 网格图标
  Widget _buildGridIcon() {
    return Wrap(
      spacing: 3,
      runSpacing: 3,
      children: List.generate(4, (_) => Container(
        width: 6,
        height: 6,
        color: Colors.white.withOpacity(0.8),
      )),
    );
  }

  /// 视频网格 - .video-list
  Widget _buildVideoGrid() {
    if (_videos.isEmpty && _isLoading) {
      return const SliverFillRemaining(
        child: Center(child: CircularProgressIndicator(color: AppTheme.primaryColor)),
      );
    }

    if (_errorMessage != null) {
      return SliverFillRemaining(
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 64, color: Colors.red),
              const SizedBox(height: 16),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Text(
                  _errorMessage!,
                  style: const TextStyle(color: Colors.red, fontSize: 14),
                  textAlign: TextAlign.center,
                ),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => _fetchVideos(refresh: true),
                child: const Text('重试'),
              ),
            ],
          ),
        ),
      );
    }

    if (_videos.isEmpty) {
      return SliverFillRemaining(
        child: Center(
          child: Text(
            '暂无视频',
            style: TextStyle(
              color: Colors.white.withOpacity(0.35),
              fontSize: 15,
            ),
          ),
        ),
      );
    }

    final aspectRatio = _gridMode == 1 ? 1.6 : 0.68;
    
    return SliverPadding(
      padding: const EdgeInsets.symmetric(horizontal: 6),
      sliver: SliverGrid(
        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: _gridMode,
          mainAxisSpacing: _gridMode == 1 ? 16 : 12,
          crossAxisSpacing: _gridMode == 1 ? 16 : 8,
          childAspectRatio: aspectRatio,
        ),
        delegate: SliverChildBuilderDelegate(
          (context, index) {
            if (index >= _videos.length) return null;
            return VideoCard(
              video: _videos[index],
              gridMode: _gridMode,
            );
          },
          childCount: _videos.length,
        ),
      ),
    );
  }

  /// 底部公告条 - .bottom-promo
  Widget _buildBottomPromo() {
    final text = _announcements.map((a) => a['content'] ?? '').join(' 🔸 ');
    
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      color: const Color(0xFF1E0F2D).withOpacity(0.5),
      child: Row(
        children: [
          // 喇叭图标
          Icon(Icons.campaign, color: const Color(0xFF7C3AED), size: 24),
          const SizedBox(width: 10),
          // 滚动文字
          Expanded(
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Text(
                '$text 🔸 $text',
                style: TextStyle(
                  fontSize: 13,
                  color: Colors.white.withOpacity(0.7),
                ),
              ),
            ),
          ),
          // 关闭按钮
          GestureDetector(
            onTap: () => setState(() => _showPromo = false),
            child: Padding(
              padding: const EdgeInsets.only(left: 8),
              child: Text(
                '✕',
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.white.withOpacity(0.6),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// 短视频浮动入口 - .short-video-float
  Widget _buildShortVideoFloat() {
    return Positioned(
      right: 16,
      bottom: 100,
      child: GestureDetector(
        onTap: () => Navigator.pushNamed(context, '/shorts'),
        child: Container(
          width: 60,
          height: 60,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.4),
                blurRadius: 20,
                offset: const Offset(0, 4),
              ),
              BoxShadow(
                color: const Color(0xFF00E0FF).withOpacity(0.3),
                blurRadius: 15,
              ),
            ],
          ),
          clipBehavior: Clip.antiAlias,
          child: Image.asset(
            AppAssets.shortLogo,
            fit: BoxFit.cover,
            errorBuilder: (_, __, ___) => Container(
              color: AppTheme.primaryColor,
              child: const Icon(Icons.play_arrow, color: Colors.white, size: 32),
            ),
          ),
        ),
      ),
    );
  }

  /// 导航抽屉 - .nav-drawer
  Widget _buildNavDrawer() {
    return Positioned(
      top: 0,
      right: 0,
      bottom: 0,
      width: MediaQuery.of(context).size.width * 0.55,
      child: Container(
        color: const Color(0xFF1A1A1A).withOpacity(0.6),
        padding: const EdgeInsets.fromLTRB(20, 60, 20, 20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '导航列表',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 20),
            Expanded(
              child: GridView.builder(
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  mainAxisSpacing: 12,
                  crossAxisSpacing: 12,
                  childAspectRatio: 2.5,
                ),
                itemCount: _categories.where((c) => c['id'] != 0).length,
                itemBuilder: (context, index) {
                  final cat = _categories.where((c) => c['id'] != 0).toList()[index];
                  final isActive = _activeCategory == cat['id'];
                  
                  return GestureDetector(
                    onTap: () {
                      setState(() => _showNavDrawer = false);
                      _selectCategory(cat['id']);
                    },
                    child: Container(
                      decoration: BoxDecoration(
                        color: isActive 
                            ? null 
                            : Colors.white.withOpacity(0.05),
                        gradient: isActive
                            ? const LinearGradient(
                                colors: [Color(0xFFA855F7), Color(0xFF7C3AED)],
                              )
                            : null,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      alignment: Alignment.center,
                      child: Text(
                        cat['name'] ?? '',
                        style: TextStyle(
                          fontSize: 13,
                          color: isActive ? Colors.white : Colors.white.withOpacity(0.85),
                          fontWeight: isActive ? FontWeight.w500 : FontWeight.normal,
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}



import 'package:provider/provider.dart';
import 'package:carousel_slider/carousel_slider.dart' as carousel;
import 'package:cached_network_image/cached_network_image.dart';
import '../../app/theme.dart';
import '../../providers/app_provider.dart';
import '../../models/video.dart';
import '../../services/api_service.dart';
import '../../widgets/video_card.dart';
import '../../utils/assets.dart';

/// 首页 - 完全复刻 Vue.js Home.vue
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  // 数据
  List<Video> _videos = [];
  List<dynamic> _categories = [];
  List<dynamic> _banners = [];
  List<dynamic> _iconAdsRow1 = [];
  List<dynamic> _iconAdsRow2 = [];
  List<dynamic> _funcItems = [];
  List<dynamic> _subCategories = [];
  List<dynamic> _announcements = [];
  
  // 状态
  bool _isLoading = false;
  String? _errorMessage;
  int _currentPage = 1;
  int _activeCategory = 0;
  int _activeVideoFilter = 0;
  int _gridMode = 2; // 1=单列, 2=双列
  bool _showNavDrawer = false;
  bool _showPromo = true;
  int _currentBannerIndex = 0;
  
  // 滚动控制器
  final ScrollController _scrollController = ScrollController();
  final ScrollController _categoryScrollController = ScrollController();
  Timer? _bannerTimer;
  Timer? _scrollAdTimer;
  double _scrollAdOffset = 0;

  // 视频筛选选项
  final List<Map<String, String>> _videoFilters = [
    {'label': '最新', 'key': 'created_at'},
    {'label': '最热', 'key': 'view_count'},
    {'label': 'VIP', 'key': 'vip'},
  ];

  @override
  void initState() {
    super.initState();
    _fetchAllData();
    _startBannerAutoPlay();
    _startScrollAdAnimation();
  }

  @override
  void dispose() {
    _scrollController.dispose();
    _categoryScrollController.dispose();
    _bannerTimer?.cancel();
    _scrollAdTimer?.cancel();
    super.dispose();
  }

  // 获取所有数据
  Future<void> _fetchAllData() async {
    setState(() => _isLoading = true);
    await Future.wait([
      _fetchCategories(),
      _fetchBanners(),
      _fetchIconAds(),
      _fetchFuncEntries(),
      _fetchVideos(refresh: true),
      _fetchAnnouncements(),
    ]);
    setState(() => _isLoading = false);
  }

  // 获取分类
  Future<void> _fetchCategories() async {
    try {
      final response = await ApiService.get('/videos/categories');
      final data = response.data;
      if (data != null && data is List) {
        setState(() {
          _categories = [
            {'id': 0, 'name': '推荐'},
            ...data,
          ];
        });
      }
    } catch (e) {
      debugPrint('获取分类失败: $e');
    }
  }

  // 获取轮播图
  Future<void> _fetchBanners() async {
    try {
      final response = await ApiService.get('/home/banners', params: {'position': 'home'});
      setState(() {
        _banners = response.data ?? [];
      });
    } catch (e) {
      debugPrint('获取轮播图失败: $e');
    }
  }

  // 获取图标广告
  Future<void> _fetchIconAds() async {
    try {
      final response = await ApiService.get('/ads/icons');
      final data = response.data ?? [];
      setState(() {
        _iconAdsRow1 = data.length > 5 ? data.sublist(0, 5) : data;
        _iconAdsRow2 = data.length > 5 ? data.sublist(5, data.length > 10 ? 10 : data.length) : [];
      });
    } catch (e) {
      debugPrint('获取图标广告失败: $e');
    }
  }

  // 获取功能入口
  Future<void> _fetchFuncEntries() async {
    try {
      final response = await ApiService.get('/ads/func-entries');
      setState(() {
        _funcItems = response.data ?? [];
      });
    } catch (e) {
      debugPrint('获取功能入口失败: $e');
    }
  }

  // 获取公告
  Future<void> _fetchAnnouncements() async {
    try {
      final response = await ApiService.get('/ads/announcements');
      setState(() {
        _announcements = response.data ?? [];
      });
    } catch (e) {
      debugPrint('获取公告失败: $e');
    }
  }

  // 获取视频列表
  Future<void> _fetchVideos({bool refresh = false}) async {
    try {
      if (refresh) _currentPage = 1;
      
      final params = <String, dynamic>{
        'page': _currentPage,
        'page_size': 20,
        'sort_by': _videoFilters[_activeVideoFilter]['key'],
      };
      
      if (_activeCategory != 0) {
        params['category_id'] = _activeCategory;
      }

      final response = await ApiService.get('/videos', params: params);
      final data = response.data;
      debugPrint('📺 视频API响应: $data');
      debugPrint('📺 data类型: ${data.runtimeType}');
      
      // 处理不同的响应格式
      List<dynamic> videoList = [];
      if (data is List) {
        videoList = data;
      } else if (data is Map) {
        videoList = data['items'] ?? data['videos'] ?? data['data'] ?? [];
      }
      debugPrint('📺 视频数量: ${videoList.length}');
      
      final List<Video> newVideos = videoList
          .map<Video>((json) => Video.fromJson(json))
          .toList();

      setState(() {
        _errorMessage = null;
        if (refresh) {
          _videos = newVideos;
        } else {
          _videos.addAll(newVideos);
        }
        _currentPage++;
      });
    } catch (e) {
      setState(() {
        _errorMessage = '加载失败: $e';
      });
    }
  }

  // 开始轮播自动播放
  void _startBannerAutoPlay() {
    _bannerTimer = Timer.periodic(const Duration(seconds: 4), (timer) {
      if (_banners.isNotEmpty) {
        setState(() {
          _currentBannerIndex = (_currentBannerIndex + 1) % _banners.length;
        });
      }
    });
  }

  // 开始滚动广告动画
  void _startScrollAdAnimation() {
    _scrollAdTimer = Timer.periodic(const Duration(milliseconds: 50), (timer) {
      setState(() {
        _scrollAdOffset += 0.5;
      });
    });
  }

  // 选择分类
  void _selectCategory(int catId) {
    setState(() {
      _activeCategory = catId;
    });
    _fetchVideos(refresh: true);
    // 滚动到选中的分类
    _scrollToCategory(catId);
  }

  // 滚动到选中的分类
  void _scrollToCategory(int catId) {
    final index = _categories.indexWhere((c) => c['id'] == catId);
    if (index != -1 && _categoryScrollController.hasClients) {
      final offset = (index * 70.0) - 100;
      _categoryScrollController.animateTo(
        offset.clamp(0, _categoryScrollController.position.maxScrollExtent),
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    }
  }

  // 切换视频筛选
  void _changeVideoFilter(int index) {
    setState(() {
      _activeVideoFilter = index;
    });
    _fetchVideos(refresh: true);
  }

  // 格式化播放量
  String _formatCount(int? count) {
    if (count == null) return '0';
    if (count >= 10000) {
      return '${(count / 10000).toStringAsFixed(1)}W';
    }
    return count.toString();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      body: Stack(
        children: [
          // 主体内容
          Column(
            children: [
              // 安全区域
              SizedBox(height: MediaQuery.of(context).padding.top),
              
              // 固定头部
              _buildHeader(),
              
              // 分类导航
              _buildCategoryNav(),
              
              // 可滚动内容
              Expanded(
                child: RefreshIndicator(
                  onRefresh: _fetchAllData,
                  color: AppTheme.primaryColor,
                  child: CustomScrollView(
                    controller: _scrollController,
                    slivers: [
                      // 轮播广告
                      SliverToBoxAdapter(child: _buildBanner()),
                      
                      // 固定图标广告位
                      SliverToBoxAdapter(child: _buildPromoGridFixed()),
                      
                      // 滚动图标广告位
                      SliverToBoxAdapter(child: _buildPromoGridScroll()),
                      
                      // 功能入口
                      SliverToBoxAdapter(child: _buildFuncScroll()),
                      
                      // 热门标签/二级分类
                      SliverToBoxAdapter(child: _buildHotSection()),
                      
                      // 视频筛选栏
                      SliverToBoxAdapter(child: _buildFilterBar()),
                      
                      // 视频列表
                      _buildVideoGrid(),
                      
                      // 底部间距
                      const SliverToBoxAdapter(child: SizedBox(height: 100)),
                    ],
                  ),
                ),
              ),
            ],
          ),

          // 底部公告条
          if (_showPromo && _announcements.isNotEmpty)
            Positioned(
              bottom: 60,
              left: 0,
              right: 0,
              child: _buildBottomPromo(),
            ),

          // 短视频浮动入口
          _buildShortVideoFloat(),

          // 导航抽屉遮罩
          if (_showNavDrawer)
            GestureDetector(
              onTap: () => setState(() => _showNavDrawer = false),
              child: Container(
                color: Colors.black.withOpacity(0.5),
              ),
            ),

          // 导航抽屉
          if (_showNavDrawer) _buildNavDrawer(),
        ],
      ),
    );
  }

  /// 顶部头部 - 对应 .header-top
  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      child: Row(
        children: [
          // 左边福利图标 - .welfare-icon
          Expanded(
            child: GestureDetector(
              onTap: () => Navigator.pushNamed(context, '/vip'),
              child: Align(
                alignment: Alignment.centerLeft,
                child: Image.asset(
                  AppAssets.fuli,
                  width: 42,
                  height: 42,
                  fit: BoxFit.contain,
                  errorBuilder: (_, __, ___) => Container(
                    width: 42,
                    height: 42,
                    decoration: BoxDecoration(
                      gradient: AppTheme.primaryGradient,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Center(
                      child: Text('福利', style: TextStyle(color: Colors.white, fontSize: 12)),
                    ),
                  ),
                ),
              ),
            ),
          ),

          // 中间 Logo - .header-center
          Expanded(
            flex: 2,
            child: Center(
              child: Image.asset(
                AppAssets.soulTitle,
                height: 36,
                fit: BoxFit.contain,
                errorBuilder: (_, __, ___) => ShaderMask(
                  shaderCallback: (bounds) => const LinearGradient(
                    colors: [Colors.white, Colors.white, Color(0xFFA855F7)],
                    stops: [0.0, 0.6, 1.0],
                  ).createShader(bounds),
                  child: const Text(
                    'Soul',
                    style: TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.w300,
                      fontStyle: FontStyle.italic,
                      color: Colors.white,
                      letterSpacing: 2,
                    ),
                  ),
                ),
              ),
            ),
          ),

          // 右边搜索和菜单 - .header-right
          Expanded(
            child: Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                // 搜索图标
                GestureDetector(
                  onTap: () => Navigator.pushNamed(context, '/search'),
                  child: Image.asset(
                    AppAssets.icSearch,
                    width: 28,
                    height: 28,
                    fit: BoxFit.contain,
                    errorBuilder: (_, __, ___) => Icon(
                      Icons.search,
                      color: Colors.white.withOpacity(0.8),
                      size: 24,
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                // 菜单图标
                GestureDetector(
                  onTap: () => setState(() => _showNavDrawer = true),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: List.generate(3, (i) => Container(
                      width: 20,
                      height: 2,
                      margin: EdgeInsets.only(bottom: i < 2 ? 5 : 0),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.8),
                        borderRadius: BorderRadius.circular(1),
                      ),
                    )),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// 分类导航 - .category-nav
  Widget _buildCategoryNav() {
    return SizedBox(
      height: 48,
      child: ListView.builder(
        controller: _categoryScrollController,
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 14),
        itemCount: _categories.length,
        itemBuilder: (context, index) {
          final cat = _categories[index];
          final isActive = _activeCategory == cat['id'];
          
          return GestureDetector(
            onTap: () => _selectCategory(cat['id']),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    cat['name'] ?? '',
                    style: TextStyle(
                      fontSize: 15,
                      color: isActive ? Colors.white : Colors.white.withOpacity(0.6),
                      fontWeight: isActive ? FontWeight.w600 : FontWeight.normal,
                    ),
                  ),
                  const SizedBox(height: 4),
                  // 下划线
                  if (isActive)
                    Container(
                      width: 20,
                      height: 3,
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFFA855F7), Color(0xFF6366F1)],
                        ),
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  /// 轮播广告 - .banner-carousel
  Widget _buildBanner() {
    if (_banners.isEmpty) return const SizedBox();
    
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      child: Column(
        children: [
          AspectRatio(
            aspectRatio: 750 / 300,
            child: ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: PageView.builder(
                itemCount: _banners.length,
                onPageChanged: (index) {
                  setState(() => _currentBannerIndex = index);
                },
                itemBuilder: (context, index) {
                  final banner = _banners[index];
                  final imageUrl = ApiService.getFullImageUrl(banner['image_url']);
                  return GestureDetector(
                    onTap: () => _handleBannerClick(banner),
                    child: CachedNetworkImage(
                      imageUrl: imageUrl,
                      fit: BoxFit.cover,
                      placeholder: (_, __) => Container(color: const Color(0xFF1A1A1A)),
                      errorWidget: (_, __, ___) => Container(color: const Color(0xFF1A1A1A)),
                    ),
                  );
                },
              ),
            ),
          ),
          // 指示点
          if (_banners.length > 1)
            Padding(
              padding: const EdgeInsets.only(top: 10),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(_banners.length, (index) {
                  final isActive = _currentBannerIndex == index;
                  return Container(
                    width: isActive ? 18 : 6,
                    height: 6,
                    margin: const EdgeInsets.symmetric(horizontal: 3),
                    decoration: BoxDecoration(
                      color: isActive ? Colors.white : Colors.white.withOpacity(0.4),
                      borderRadius: BorderRadius.circular(3),
                    ),
                  );
                }),
              ),
            ),
        ],
      ),
    );
  }

  // 处理轮播点击
  void _handleBannerClick(dynamic banner) {
    final linkType = banner['link_type'] ?? 'url';
    final linkUrl = banner['link_url'];
    
    if (linkUrl == null) return;
    
    if (linkType == 'video') {
      Navigator.pushNamed(context, '/video/$linkUrl');
    } else if (linkType == 'vip') {
      Navigator.pushNamed(context, '/vip');
    }
    // 其他类型可以用 url_launcher 打开外部链接
  }

  /// 固定图标广告位 - .promo-grid-fixed
  Widget _buildPromoGridFixed() {
    if (_iconAdsRow1.isEmpty) return const SizedBox();
    
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: _iconAdsRow1.map((ad) => _buildPromoItem(ad)).toList(),
      ),
    );
  }

  /// 滚动图标广告位 - .promo-scroll-container
  Widget _buildPromoGridScroll() {
    if (_iconAdsRow2.isEmpty) return const SizedBox();
    
    // 复制列表实现无限滚动
    final doubleList = [..._iconAdsRow2, ..._iconAdsRow2];
    
    return SizedBox(
      height: 90,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 6),
        itemCount: doubleList.length,
        itemBuilder: (context, index) => _buildPromoItem(doubleList[index]),
      ),
    );
  }

  /// 广告项 - .promo-item
  Widget _buildPromoItem(dynamic ad) {
    final imageUrl = ApiService.getFullImageUrl(ad['image'] ?? '');
    final bg = ad['bg'] ?? '#6366f1';
    
    return GestureDetector(
      onTap: () => _handleAdClick(ad),
      child: Container(
        width: 70,
        margin: const EdgeInsets.symmetric(horizontal: 4),
        child: Column(
          children: [
            // 图标
            Container(
              width: 60,
              height: 60,
              decoration: BoxDecoration(
                color: _parseColor(bg),
                borderRadius: BorderRadius.circular(12),
              ),
              clipBehavior: Clip.antiAlias,
              child: imageUrl.isNotEmpty
                  ? CachedNetworkImage(
                      imageUrl: imageUrl,
                      fit: BoxFit.cover,
                      errorWidget: (_, __, ___) => Center(
                        child: Text(
                          ad['icon'] ?? '📦',
                          style: const TextStyle(fontSize: 28),
                        ),
                      ),
                    )
                  : Center(
                      child: Text(
                        ad['icon'] ?? '📦',
                        style: const TextStyle(fontSize: 28),
                      ),
                    ),
            ),
            const SizedBox(height: 6),
            // 名称
            Text(
              ad['name'] ?? '',
              style: TextStyle(
                fontSize: 12,
                color: Colors.white.withOpacity(0.7),
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  // 解析颜色
  Color _parseColor(String colorStr) {
    if (colorStr.startsWith('#')) {
      return Color(int.parse(colorStr.substring(1), radix: 16) + 0xFF000000);
    }
    return const Color(0xFF6366F1);
  }

  // 处理广告点击
  void _handleAdClick(dynamic ad) {
    final link = ad['link'] ?? ad['link_url'];
    if (link != null && link.toString().isNotEmpty) {
      if (link.toString().startsWith('/')) {
        Navigator.pushNamed(context, link);
      }
    }
  }

  /// 功能入口 - .func-scroll-wrapper
  Widget _buildFuncScroll() {
    if (_funcItems.isEmpty) return const SizedBox();
    
    return SizedBox(
      height: 95,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        itemCount: _funcItems.length,
        itemBuilder: (context, index) {
          final func = _funcItems[index];
          final imageUrl = ApiService.getFullImageUrl(func['image'] ?? '');
          
          return GestureDetector(
            onTap: () => _handleFuncClick(func),
            child: Container(
              width: 72,
              margin: const EdgeInsets.only(right: 16),
              child: Column(
                children: [
                  // 图标盒子 - .func-icon-box
                  Container(
                    width: 56,
                    height: 56,
                    decoration: BoxDecoration(
                      gradient: imageUrl.isEmpty
                          ? const LinearGradient(
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                              colors: [Color(0xFF6366F1), Color(0xFF8B5CF6)],
                            )
                          : null,
                      borderRadius: BorderRadius.circular(14),
                    ),
                    clipBehavior: Clip.antiAlias,
                    child: imageUrl.isNotEmpty
                        ? CachedNetworkImage(
                            imageUrl: imageUrl,
                            fit: BoxFit.cover,
                            errorWidget: (_, __, ___) => Center(
                              child: Text(
                                _getFuncShortName(func['name'] ?? ''),
                                style: const TextStyle(
                                  fontSize: 22,
                                  fontWeight: FontWeight.w500,
                                  color: Colors.white,
                                ),
                              ),
                            ),
                          )
                        : Center(
                            child: Text(
                              _getFuncShortName(func['name'] ?? ''),
                              style: const TextStyle(
                                fontSize: 22,
                                fontWeight: FontWeight.w500,
                                color: Colors.white,
                              ),
                            ),
                          ),
                  ),
                  const SizedBox(height: 8),
                  // 名称
                  Text(
                    func['name'] ?? '',
                    style: TextStyle(
                      fontSize: 13,
                      color: Colors.white.withOpacity(0.85),
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  // 获取功能简称
  String _getFuncShortName(String name) {
    final shortNames = {
      '广场': '广',
      'AI广场': 'A',
      '会员中心': '会',
      '社区广场': '社',
      '分享邀请': '分',
      '排行榜': '排',
      '签到福利': '签',
    };
    return shortNames[name] ?? (name.isNotEmpty ? name[0] : '');
  }

  // 处理功能入口点击
  void _handleFuncClick(dynamic func) {
    final link = func['link'] ?? func['link_url'];
    if (link != null && link.toString().isNotEmpty) {
      if (link.toString().startsWith('/')) {
        Navigator.pushNamed(context, link);
      }
    }
  }

  /// 热门标签区域 - .hot-section
  Widget _buildHotSection() {
    if (_subCategories.isEmpty) return const SizedBox();
    
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      child: Wrap(
        spacing: 10,
        runSpacing: 10,
        children: _subCategories.map((subCat) {
          return GestureDetector(
            onTap: () => Navigator.pushNamed(context, '/category/${subCat['id']}'),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.08),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                subCat['name'] ?? '',
                style: TextStyle(
                  fontSize: 13,
                  color: Colors.white.withOpacity(0.75),
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  /// 视频筛选栏 - .filter-bar
  Widget _buildFilterBar() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 6),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
      decoration: BoxDecoration(
        color: const Color(0xFF0A0A0A),
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(12),
          topRight: Radius.circular(12),
        ),
        border: Border(
          bottom: BorderSide(color: Colors.white.withOpacity(0.06)),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // 筛选标签 - .filter-tabs
          Row(
            children: List.generate(_videoFilters.length, (index) {
              final isActive = _activeVideoFilter == index;
              return GestureDetector(
                onTap: () => _changeVideoFilter(index),
                child: Container(
                  margin: const EdgeInsets.only(right: 20),
                  child: Column(
                    children: [
                      Text(
                        _videoFilters[index]['label']!,
                        style: TextStyle(
                          fontSize: 14,
                          color: isActive ? Colors.white : Colors.white.withOpacity(0.5),
                          fontWeight: isActive ? FontWeight.w600 : FontWeight.normal,
                        ),
                      ),
                      const SizedBox(height: 4),
                      if (isActive)
                        Container(
                          width: 20,
                          height: 2,
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(
                              colors: [Color(0xFFA855F7), Color(0xFF7C3AED)],
                            ),
                            borderRadius: BorderRadius.circular(1),
                          ),
                        ),
                    ],
                  ),
                ),
              );
            }),
          ),
          
          // 切换按钮 - .view-toggle
          GestureDetector(
            onTap: () {
              setState(() {
                _gridMode = _gridMode == 1 ? 2 : 1;
              });
            },
            child: Row(
              children: [
                Text(
                  '切换',
                  style: TextStyle(
                    fontSize: 13,
                    color: Colors.white.withOpacity(0.7),
                  ),
                ),
                const SizedBox(width: 4),
                // 切换图标
                _gridMode == 1
                    ? _buildListIcon()
                    : _buildGridIcon(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // 列表图标
  Widget _buildListIcon() {
    return Column(
      children: List.generate(3, (i) => Container(
        width: 16,
        height: 2,
        margin: EdgeInsets.only(bottom: i < 2 ? 2 : 0),
        color: Colors.white.withOpacity(0.8),
      )),
    );
  }

  // 网格图标
  Widget _buildGridIcon() {
    return Wrap(
      spacing: 3,
      runSpacing: 3,
      children: List.generate(4, (_) => Container(
        width: 6,
        height: 6,
        color: Colors.white.withOpacity(0.8),
      )),
    );
  }

  /// 视频网格 - .video-list
  Widget _buildVideoGrid() {
    if (_videos.isEmpty && _isLoading) {
      return const SliverFillRemaining(
        child: Center(child: CircularProgressIndicator(color: AppTheme.primaryColor)),
      );
    }

    if (_errorMessage != null) {
      return SliverFillRemaining(
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 64, color: Colors.red),
              const SizedBox(height: 16),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Text(
                  _errorMessage!,
                  style: const TextStyle(color: Colors.red, fontSize: 14),
                  textAlign: TextAlign.center,
                ),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => _fetchVideos(refresh: true),
                child: const Text('重试'),
              ),
            ],
          ),
        ),
      );
    }

    if (_videos.isEmpty) {
      return SliverFillRemaining(
        child: Center(
          child: Text(
            '暂无视频',
            style: TextStyle(
              color: Colors.white.withOpacity(0.35),
              fontSize: 15,
            ),
          ),
        ),
      );
    }

    final aspectRatio = _gridMode == 1 ? 1.6 : 0.68;
    
    return SliverPadding(
      padding: const EdgeInsets.symmetric(horizontal: 6),
      sliver: SliverGrid(
        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: _gridMode,
          mainAxisSpacing: _gridMode == 1 ? 16 : 12,
          crossAxisSpacing: _gridMode == 1 ? 16 : 8,
          childAspectRatio: aspectRatio,
        ),
        delegate: SliverChildBuilderDelegate(
          (context, index) {
            if (index >= _videos.length) return null;
            return VideoCard(
              video: _videos[index],
              gridMode: _gridMode,
            );
          },
          childCount: _videos.length,
        ),
      ),
    );
  }

  /// 底部公告条 - .bottom-promo
  Widget _buildBottomPromo() {
    final text = _announcements.map((a) => a['content'] ?? '').join(' 🔸 ');
    
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      color: const Color(0xFF1E0F2D).withOpacity(0.5),
      child: Row(
        children: [
          // 喇叭图标
          Icon(Icons.campaign, color: const Color(0xFF7C3AED), size: 24),
          const SizedBox(width: 10),
          // 滚动文字
          Expanded(
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Text(
                '$text 🔸 $text',
                style: TextStyle(
                  fontSize: 13,
                  color: Colors.white.withOpacity(0.7),
                ),
              ),
            ),
          ),
          // 关闭按钮
          GestureDetector(
            onTap: () => setState(() => _showPromo = false),
            child: Padding(
              padding: const EdgeInsets.only(left: 8),
              child: Text(
                '✕',
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.white.withOpacity(0.6),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// 短视频浮动入口 - .short-video-float
  Widget _buildShortVideoFloat() {
    return Positioned(
      right: 16,
      bottom: 100,
      child: GestureDetector(
        onTap: () => Navigator.pushNamed(context, '/shorts'),
        child: Container(
          width: 60,
          height: 60,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.4),
                blurRadius: 20,
                offset: const Offset(0, 4),
              ),
              BoxShadow(
                color: const Color(0xFF00E0FF).withOpacity(0.3),
                blurRadius: 15,
              ),
            ],
          ),
          clipBehavior: Clip.antiAlias,
          child: Image.asset(
            AppAssets.shortLogo,
            fit: BoxFit.cover,
            errorBuilder: (_, __, ___) => Container(
              color: AppTheme.primaryColor,
              child: const Icon(Icons.play_arrow, color: Colors.white, size: 32),
            ),
          ),
        ),
      ),
    );
  }

  /// 导航抽屉 - .nav-drawer
  Widget _buildNavDrawer() {
    return Positioned(
      top: 0,
      right: 0,
      bottom: 0,
      width: MediaQuery.of(context).size.width * 0.55,
      child: Container(
        color: const Color(0xFF1A1A1A).withOpacity(0.6),
        padding: const EdgeInsets.fromLTRB(20, 60, 20, 20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '导航列表',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 20),
            Expanded(
              child: GridView.builder(
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  mainAxisSpacing: 12,
                  crossAxisSpacing: 12,
                  childAspectRatio: 2.5,
                ),
                itemCount: _categories.where((c) => c['id'] != 0).length,
                itemBuilder: (context, index) {
                  final cat = _categories.where((c) => c['id'] != 0).toList()[index];
                  final isActive = _activeCategory == cat['id'];
                  
                  return GestureDetector(
                    onTap: () {
                      setState(() => _showNavDrawer = false);
                      _selectCategory(cat['id']);
                    },
                    child: Container(
                      decoration: BoxDecoration(
                        color: isActive 
                            ? null 
                            : Colors.white.withOpacity(0.05),
                        gradient: isActive
                            ? const LinearGradient(
                                colors: [Color(0xFFA855F7), Color(0xFF7C3AED)],
                              )
                            : null,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      alignment: Alignment.center,
                      child: Text(
                        cat['name'] ?? '',
                        style: TextStyle(
                          fontSize: 13,
                          color: isActive ? Colors.white : Colors.white.withOpacity(0.85),
                          fontWeight: isActive ? FontWeight.w500 : FontWeight.normal,
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}