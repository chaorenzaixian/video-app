import 'package:flutter/material.dart';
import '../../../core/services/api_service.dart';
import '../widgets/post_card.dart';

class CommunityScreen extends StatefulWidget {
  const CommunityScreen({super.key});

  @override
  State<CommunityScreen> createState() => _CommunityScreenState();
}

class _CommunityScreenState extends State<CommunityScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final List<String> _tabs = ['推荐', '关注', '热门', '最新'];
  final List<String> _feedTypes = ['recommend', 'following', 'hot', 'latest'];
  
  List<dynamic> _posts = [];
  List<dynamic> _topics = [];
  int? _selectedTopicId;
  bool _loading = false;
  bool _hasMore = true;
  int _page = 1;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _tabs.length, vsync: this);
    _tabController.addListener(_onTabChanged);
    _fetchTopics();
    _fetchPosts(reset: true);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  void _onTabChanged() {
    if (_tabController.indexIsChanging) return;
    _fetchPosts(reset: true);
  }

  Future<void> _fetchTopics() async {
    try {
      final res = await ApiService.get('/community/topics', queryParams: {'is_hot': 'true', 'page_size': '10'});
      if (mounted) {
        setState(() => _topics = res ?? []);
      }
    } catch (e) {
      debugPrint('获取话题失败: $e');
    }
  }

  Future<void> _fetchPosts({bool reset = false}) async {
    if (_loading) return;
    if (reset) {
      _page = 1;
      _hasMore = true;
      _posts = [];
    }
    if (!_hasMore) return;

    setState(() => _loading = true);

    try {
      final params = {
        'page': _page.toString(),
        'page_size': '20',
        'feed_type': _feedTypes[_tabController.index],
      };
      if (_selectedTopicId != null) {
        params['topic_id'] = _selectedTopicId.toString();
      }

      final res = await ApiService.get('/community/posts', queryParams: params);
      final data = res as List? ?? [];
      
      if (mounted) {
        setState(() {
          if (data.length < 20) _hasMore = false;
          _posts = reset ? data : [..._posts, ...data];
          _page++;
          _loading = false;
        });
      }
    } catch (e) {
      debugPrint('获取动态失败: $e');
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _likePost(int index) async {
    final post = _posts[index];
    try {
      final res = await ApiService.post('/community/posts/${post['id']}/like');
      if (mounted) {
        setState(() {
          _posts[index]['is_liked'] = res['liked'];
          _posts[index]['like_count'] = res['like_count'];
        });
      }
    } catch (e) {
      debugPrint('点赞失败: $e');
    }
  }

  Future<void> _followUser(int index) async {
    final post = _posts[index];
    try {
      final res = await ApiService.post('/community/users/${post['user']['id']}/follow');
      if (mounted) {
        setState(() {
          _posts[index]['is_followed'] = res['followed'];
        });
      }
    } catch (e) {
      debugPrint('关注失败: $e');
    }
  }

  void _selectTopic(int? id) {
    setState(() {
      _selectedTopicId = _selectedTopicId == id ? null : id;
    });
    _fetchPosts(reset: true);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF111111),
        title: TabBar(
          controller: _tabController,
          isScrollable: true,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.grey,
          indicatorColor: const Color(0xFFFF4757),
          tabs: _tabs.map((t) => Tab(text: t)).toList(),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.search, color: Colors.white),
            onPressed: () => Navigator.pushNamed(context, '/search'),
          ),
        ],
      ),
      body: Column(
        children: [
          // 话题横滑
          if (_topics.isNotEmpty)
            SizedBox(
              height: 44,
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                itemCount: _topics.length,
                itemBuilder: (ctx, i) {
                  final topic = _topics[i];
                  final selected = _selectedTopicId == topic['id'];
                  return GestureDetector(
                    onTap: () => _selectTopic(topic['id']),
                    child: Container(
                      margin: const EdgeInsets.only(right: 8),
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                      decoration: BoxDecoration(
                        color: selected ? const Color(0xFFFF4757) : const Color(0xFF222222),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(
                        '#${topic['name']}',
                        style: TextStyle(
                          color: selected ? Colors.white : Colors.grey,
                          fontSize: 13,
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
          // 动态列表
          Expanded(
            child: RefreshIndicator(
              onRefresh: () => _fetchPosts(reset: true),
              child: ListView.builder(
                padding: const EdgeInsets.all(8),
                itemCount: _posts.length + 1,
                itemBuilder: (ctx, i) {
                  if (i == _posts.length) {
                    if (_loading) {
                      return const Center(child: Padding(
                        padding: EdgeInsets.all(16),
                        child: CircularProgressIndicator(),
                      ));
                    }
                    if (!_hasMore) {
                      return const Center(child: Padding(
                        padding: EdgeInsets.all(16),
                        child: Text('没有更多了', style: TextStyle(color: Colors.grey)),
                      ));
                    }
                    return const SizedBox.shrink();
                  }
                  return PostCard(
                    post: _posts[i],
                    onLike: () => _likePost(i),
                    onFollow: () => _followUser(i),
                    onTap: () => Navigator.pushNamed(context, '/community/post/${_posts[i]['id']}'),
                  );
                },
              ),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: const Color(0xFFFF4757),
        onPressed: () => Navigator.pushNamed(context, '/community/publish'),
        child: const Icon(Icons.add, color: Colors.white),
      ),
    );
  }
}
