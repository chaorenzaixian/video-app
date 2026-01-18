import 'dart:async';
import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../../app/theme.dart';
import '../../models/video.dart';
import '../../services/api_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<Video> _videos = [];
  List<dynamic> _categories = [];
  bool _isLoading = false;
  String? _errorMessage;
  int _currentPage = 1;
  int _activeCategory = 0;
  int _activeVideoFilter = 0;
  int _gridMode = 2;
  final ScrollController _scrollController = ScrollController();
  final ScrollController _categoryScrollController = ScrollController();
  final List<Map<String, String>> _videoFilters = [
    {'label': '最新', 'key': 'created_at'},
    {'label': '最热', 'key': 'view_count'},
    {'label': 'VIP', 'key': 'vip'},
  ];

  @override
  void initState() { super.initState(); _fetchAllData(); }
  @override
  void dispose() { _scrollController.dispose(); _categoryScrollController.dispose(); super.dispose(); }

  Future<void> _fetchAllData() async {
    setState(() => _isLoading = true);
    await Future.wait([_fetchCategories(), _fetchVideos(refresh: true)]);
    setState(() => _isLoading = false);
  }

  Future<void> _fetchCategories() async {
    try {
      final response = await ApiService.get('/videos/categories');
      final data = response.data;
      if (data != null && data is List) {
        setState(() { _categories = [{'id': 0, 'name': '推荐'}, ...data]; });
      }
    } catch (e) { debugPrint('获取分类失败: $e'); }
  }

  Future<void> _fetchVideos({bool refresh = false}) async {
    try {
      if (refresh) _currentPage = 1;
      final params = <String, dynamic>{'page': _currentPage, 'page_size': 20, 'sort_by': _videoFilters[_activeVideoFilter]['key']};
      if (_activeCategory != 0) params['category_id'] = _activeCategory;
      final response = await ApiService.get('/videos', params: params);
      final data = response.data;
      List<dynamic> videoList = [];
      if (data is List) videoList = data;
      else if (data is Map) videoList = data['items'] ?? data['videos'] ?? data['data'] ?? [];
      final List<Video> newVideos = videoList.map<Video>((json) => Video.fromJson(json)).toList();
      setState(() {
        _errorMessage = null;
        if (refresh) _videos = newVideos; else _videos.addAll(newVideos);
        _currentPage++;
      });
    } catch (e) { setState(() => _errorMessage = '加载失败: $e'); }
  }

  void _selectCategory(int catId) { setState(() => _activeCategory = catId); _fetchVideos(refresh: true); }
  void _changeVideoFilter(int index) { setState(() => _activeVideoFilter = index); _fetchVideos(refresh: true); }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      body: SafeArea(
        child: Column(children: [
          _buildHeader(),
          _buildCategoryNav(),
          Expanded(child: RefreshIndicator(
            onRefresh: _fetchAllData, color: AppTheme.primaryColor,
            child: CustomScrollView(controller: _scrollController, slivers: [
              SliverToBoxAdapter(child: _buildFilterBar()),
              _buildVideoGrid(),
              const SliverToBoxAdapter(child: SizedBox(height: 100)),
            ]),
          )),
        ]),
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      child: Row(children: [
        Expanded(child: GestureDetector(
          onTap: () => Navigator.pushNamed(context, '/vip'),
          child: Container(width: 42, height: 42,
            decoration: BoxDecoration(gradient: AppTheme.primaryGradient, borderRadius: BorderRadius.circular(8)),
            child: const Center(child: Text('福利', style: TextStyle(color: Colors.white, fontSize: 12)))),
        )),
        const Expanded(flex: 2, child: Center(child: Text('Soul', style: TextStyle(fontSize: 32, fontWeight: FontWeight.w300, fontStyle: FontStyle.italic, color: Colors.white, letterSpacing: 2)))),
        Expanded(child: Row(mainAxisAlignment: MainAxisAlignment.end, children: [
          GestureDetector(onTap: () => Navigator.pushNamed(context, '/search'), child: const Icon(Icons.search, color: Colors.white70, size: 24)),
        ])),
      ]),
    );
  }

  Widget _buildCategoryNav() {
    return SizedBox(height: 48, child: ListView.builder(
      controller: _categoryScrollController, scrollDirection: Axis.horizontal, padding: const EdgeInsets.symmetric(horizontal: 14), itemCount: _categories.length,
      itemBuilder: (context, index) {
        final cat = _categories[index]; final isActive = _activeCategory == cat['id'];
        return GestureDetector(onTap: () => _selectCategory(cat['id']),
          child: Container(padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
              Text(cat['name'] ?? '', style: TextStyle(fontSize: 15, color: isActive ? Colors.white : Colors.white60, fontWeight: isActive ? FontWeight.w600 : FontWeight.normal)),
              const SizedBox(height: 4),
              if (isActive) Container(width: 20, height: 3, decoration: BoxDecoration(gradient: const LinearGradient(colors: [Color(0xFFA855F7), Color(0xFF6366F1)]), borderRadius: BorderRadius.circular(2))),
            ]),
          ),
        );
      },
    ));
  }

  Widget _buildFilterBar() {
    return Container(margin: const EdgeInsets.symmetric(horizontal: 6), padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
      child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        Row(children: List.generate(_videoFilters.length, (index) {
          final isActive = _activeVideoFilter == index;
          return GestureDetector(onTap: () => _changeVideoFilter(index),
            child: Container(margin: const EdgeInsets.only(right: 20),
              child: Text(_videoFilters[index]['label']!, style: TextStyle(fontSize: 14, color: isActive ? Colors.white : Colors.white54, fontWeight: isActive ? FontWeight.w600 : FontWeight.normal))));
        })),
        GestureDetector(onTap: () => setState(() => _gridMode = _gridMode == 1 ? 2 : 1), child: Icon(_gridMode == 1 ? Icons.view_list : Icons.grid_view, color: Colors.white70, size: 18)),
      ]),
    );
  }

  Widget _buildVideoGrid() {
    if (_videos.isEmpty && _isLoading) return const SliverFillRemaining(child: Center(child: CircularProgressIndicator(color: AppTheme.primaryColor)));
    if (_errorMessage != null) return SliverFillRemaining(child: Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [const Icon(Icons.error_outline, size: 64, color: Colors.red), const SizedBox(height: 16), Text(_errorMessage!, style: const TextStyle(color: Colors.red)), const SizedBox(height: 16), ElevatedButton(onPressed: () => _fetchVideos(refresh: true), child: const Text('重试'))])));
    if (_videos.isEmpty) return const SliverFillRemaining(child: Center(child: Text('暂无视频', style: TextStyle(color: Colors.white38))));
    return SliverPadding(padding: const EdgeInsets.symmetric(horizontal: 6),
      sliver: SliverGrid(gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: _gridMode == 1 ? 1 : 2, childAspectRatio: _gridMode == 1 ? 1.6 : 0.68, crossAxisSpacing: 8, mainAxisSpacing: 8),
        delegate: SliverChildBuilderDelegate((context, index) => _buildVideoCard(_videos[index]), childCount: _videos.length)));
  }

  Widget _buildVideoCard(Video video) {
    final coverUrl = ApiService.getFullImageUrl(video.cover ?? '');
    return GestureDetector(onTap: () => Navigator.pushNamed(context, '/video', arguments: {'videoId': video.id}),
      child: Container(decoration: BoxDecoration(color: const Color(0xFF1A1A1A), borderRadius: BorderRadius.circular(8)), clipBehavior: Clip.antiAlias,
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Expanded(child: Stack(fit: StackFit.expand, children: [
            coverUrl.isNotEmpty ? CachedNetworkImage(imageUrl: coverUrl, fit: BoxFit.cover, placeholder: (_, __) => Container(color: const Color(0xFF252525)), errorWidget: (_, __, ___) => Container(color: const Color(0xFF252525), child: const Icon(Icons.image, color: Colors.white24))) : Container(color: const Color(0xFF252525)),
            if (video.isVip) Positioned(left: 6, top: 6, child: Container(padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2), decoration: BoxDecoration(gradient: const LinearGradient(colors: [Color(0xFFFFD700), Color(0xFFFFA500)]), borderRadius: BorderRadius.circular(4)), child: const Text('VIP', style: TextStyle(color: Colors.black, fontSize: 10, fontWeight: FontWeight.bold)))),
          ])),
          Padding(padding: const EdgeInsets.all(8), child: Text(video.title, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(color: Colors.white70, fontSize: 13))),
        ]),
      ),
    );
  }
}