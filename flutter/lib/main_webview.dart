import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:wakelock_plus/wakelock_plus.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:dio/dio.dart';
import 'package:url_launcher/url_launcher.dart';

/// WebView 版本入口 - 快速上线方案
/// 加载现有的 Vue.js 前端
void main() {
  WidgetsFlutterBinding.ensureInitialized();
  
  // 设置状态栏样式
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light,
  ));
  
  runApp(const WebViewApp());
}

// ==================== 配置 ====================
class AppConfig {
  // 🚀 生产环境配置
  static const String baseUrl = 'https://ssoul.cc';
  static const String apiBaseUrl = 'https://ssoul.cc';
  static const String webUrl = '$baseUrl/user';
  
  // 开屏广告配置
  static const int splashDuration = 3; // 默认开屏时长（秒）
  static const int adDuration = 5; // 广告显示时长（秒）
}

class WebViewApp extends StatelessWidget {
  const WebViewApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '视频App',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        primaryColor: const Color(0xFFA855F7),
        scaffoldBackgroundColor: const Color(0xFF0A0A0A),
      ),
      home: const SplashScreen(),
    );
  }
}

// ==================== 开屏页面 ====================
class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> with SingleTickerProviderStateMixin {
  int _countdown = AppConfig.splashDuration;
  Timer? _timer;
  Map<String, dynamic>? _splashAd;
  bool _isLoadingAd = true;
  late AnimationController _fadeController;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    
    // 淡入动画
    _fadeController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _fadeController, curve: Curves.easeIn),
    );
    _fadeController.forward();
    
    _loadSplashAd();
  }

  @override
  void dispose() {
    _timer?.cancel();
    _fadeController.dispose();
    super.dispose();
  }

  // 加载开屏广告
  Future<void> _loadSplashAd() async {
    try {
      final dio = Dio();
      dio.options.connectTimeout = const Duration(seconds: 3);
      dio.options.receiveTimeout = const Duration(seconds: 3);
      
      final response = await dio.get(
        '${AppConfig.apiBaseUrl}/api/v1/ads/splash',
      );
      
      if (response.statusCode == 200 && response.data != null) {
        final data = response.data;
        if (data['image_url'] != null && data['image_url'].toString().isNotEmpty) {
          setState(() {
            _splashAd = data;
            _countdown = data['duration'] ?? AppConfig.adDuration;
          });
        }
      }
    } catch (e) {
      debugPrint('📱 加载开屏广告失败: $e');
    } finally {
      setState(() => _isLoadingAd = false);
      _startCountdown();
    }
  }

  // 开始倒计时
  void _startCountdown() {
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_countdown <= 1) {
        timer.cancel();
        _navigateToMain();
      } else {
        setState(() => _countdown--);
      }
    });
  }

  // 跳过广告
  void _skipAd() {
    _timer?.cancel();
    _navigateToMain();
  }

  // 点击广告
  void _onAdTap() async {
    if (_splashAd != null && _splashAd!['link_url'] != null) {
      final url = _splashAd!['link_url'].toString();
      if (url.isNotEmpty) {
        // 如果是内部链接，跳转到 WebView
        if (url.startsWith('/') || url.contains(AppConfig.baseUrl)) {
          _timer?.cancel();
          _navigateToMain(initialUrl: url.startsWith('/') ? '${AppConfig.baseUrl}$url' : url);
        } else {
          // 外部链接用浏览器打开
          final uri = Uri.parse(url);
          if (await canLaunchUrl(uri)) {
            await launchUrl(uri, mode: LaunchMode.externalApplication);
          }
        }
      }
    }
  }

  // 跳转到主页面
  void _navigateToMain({String? initialUrl}) {
    Navigator.of(context).pushReplacement(
      PageRouteBuilder(
        pageBuilder: (context, animation, secondaryAnimation) => 
            WebViewScreen(initialUrl: initialUrl),
        transitionsBuilder: (context, animation, secondaryAnimation, child) {
          return FadeTransition(opacity: animation, child: child);
        },
        transitionDuration: const Duration(milliseconds: 300),
      ),
    );
  }

  // 获取完整图片 URL
  String _getFullImageUrl(String? url) {
    if (url == null || url.isEmpty) return '';
    if (url.startsWith('http')) return url;
    return '${AppConfig.apiBaseUrl}$url';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      body: FadeTransition(
        opacity: _fadeAnimation,
        child: Stack(
          fit: StackFit.expand,
          children: [
            // 背景 - 开屏广告或默认 Logo
            if (_splashAd != null && _splashAd!['image_url'] != null)
              // 开屏广告图片
              GestureDetector(
                onTap: _onAdTap,
                child: CachedNetworkImage(
                  imageUrl: _getFullImageUrl(_splashAd!['image_url']),
                  fit: BoxFit.cover,
                  placeholder: (context, url) => _buildDefaultSplash(),
                  errorWidget: (context, url, error) => _buildDefaultSplash(),
                ),
              )
            else
              // 默认开屏页面
              _buildDefaultSplash(),
            
            // 跳过按钮
            if (!_isLoadingAd)
              Positioned(
                top: MediaQuery.of(context).padding.top + 16,
                right: 16,
                child: GestureDetector(
                  onTap: _skipAd,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.5),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: Colors.white24),
                    ),
                    child: Text(
                      _splashAd != null ? '跳过 $_countdown' : '$_countdown',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                ),
              ),
            
            // 底部版权信息
            Positioned(
              bottom: MediaQuery.of(context).padding.bottom + 30,
              left: 0,
              right: 0,
              child: Column(
                children: [
                  Text(
                    'Soul视频',
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.6),
                      fontSize: 14,
                      letterSpacing: 1,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'v1.0.0',
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.3),
                      fontSize: 12,
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

  // 默认开屏页面 - 使用本地图片
  Widget _buildDefaultSplash() {
    return Image.asset(
      'assets/images/ic_splash_bg.webp',
      fit: BoxFit.cover,
      width: double.infinity,
      height: double.infinity,
      errorBuilder: (context, error, stackTrace) {
        // 图片加载失败时显示备用界面
        return Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                Color(0xFF1A1A2E),
                Color(0xFF0A0A0A),
              ],
            ),
          ),
          child: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 120,
                  height: 120,
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFFA855F7), Color(0xFF7C3AED)],
                    ),
                    borderRadius: BorderRadius.circular(30),
                  ),
                  child: const Icon(
                    Icons.play_arrow_rounded,
                    size: 70,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 30),
                const Text(
                  'Soul视频',
                  style: TextStyle(
                    fontSize: 36,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

// ==================== WebView 页面 ====================
class WebViewScreen extends StatefulWidget {
  final String? initialUrl;
  
  const WebViewScreen({super.key, this.initialUrl});

  @override
  State<WebViewScreen> createState() => _WebViewScreenState();
}

class _WebViewScreenState extends State<WebViewScreen> {
  late final WebViewController _controller;
  bool _isLoading = true;
  double _loadingProgress = 0;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _initWebView();
    WakelockPlus.enable();
  }

  @override
  void dispose() {
    WakelockPlus.disable();
    super.dispose();
  }

  void _initWebView() {
    final url = widget.initialUrl ?? AppConfig.webUrl;
    
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(const Color(0xFF0A0A0A))
      ..enableZoom(false)
      ..setNavigationDelegate(NavigationDelegate(
        onProgress: (progress) {
          setState(() => _loadingProgress = progress / 100);
        },
        onPageStarted: (url) {
          setState(() {
            _isLoading = true;
            _errorMessage = null;
          });
          debugPrint('📱 WebView 开始加载: $url');
        },
        onPageFinished: (url) async {
          setState(() => _isLoading = false);
          debugPrint('📱 WebView 加载完成: $url');
          _injectCustomCSS();
        },
        onWebResourceError: (error) {
          debugPrint('📱 WebView 错误: ${error.description}');
          setState(() {
            _errorMessage = '加载失败: ${error.description}';
            _isLoading = false;
          });
        },
        onNavigationRequest: (request) {
          if (request.url.startsWith('tel:') ||
              request.url.startsWith('mailto:') ||
              request.url.startsWith('sms:')) {
            return NavigationDecision.prevent;
          }
          return NavigationDecision.navigate;
        },
      ))
      ..addJavaScriptChannel(
        'FlutterBridge',
        onMessageReceived: (message) {
          _handleJSMessage(message.message);
        },
      )
      ..loadRequest(Uri.parse(url));
  }

  void _handleJSMessage(String message) {
    debugPrint('📱 收到 JS 消息: $message');
  }

  void _injectCustomCSS() {
    _controller.runJavaScript('''
      var style = document.createElement('style');
      style.innerHTML = \`
        body {
          -webkit-user-select: none;
          user-select: none;
        }
      \`;
      document.head.appendChild(style);
      window.isFlutterApp = true;
    ''');
  }

  void _refresh() {
    _controller.reload();
  }

  Future<bool> _goBack() async {
    if (await _controller.canGoBack()) {
      await _controller.goBack();
      return false;
    }
    return true;
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) async {
        if (didPop) return;
        final shouldPop = await _goBack();
        if (shouldPop && context.mounted) {
          _showExitDialog(context);
        }
      },
      child: Scaffold(
        backgroundColor: const Color(0xFF0A0A0A),
        body: Stack(
          children: [
            // WebView - 顶部留出状态栏空间
            Positioned(
              top: MediaQuery.of(context).padding.top,
              left: 0,
              right: 0,
              bottom: 0,
              child: WebViewWidget(controller: _controller),
            ),
            
            // 顶部状态栏背景
            Positioned(
              top: 0,
              left: 0,
              right: 0,
              height: MediaQuery.of(context).padding.top,
              child: Container(color: const Color(0xFF0A0A0A)),
            ),
            
            // 进度条
            if (_isLoading)
              Positioned(
                top: MediaQuery.of(context).padding.top,
                left: 0,
                right: 0,
                child: LinearProgressIndicator(
                  value: _loadingProgress,
                  backgroundColor: Colors.transparent,
                  valueColor: const AlwaysStoppedAnimation<Color>(
                    Color(0xFFA855F7),
                  ),
                  minHeight: 2,
                ),
              ),
              
              if (_isLoading && _loadingProgress < 0.3)
                Container(
                  color: const Color(0xFF0A0A0A),
                  child: const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        CircularProgressIndicator(color: Color(0xFFA855F7)),
                        SizedBox(height: 16),
                        Text(
                          '加载中...',
                          style: TextStyle(color: Colors.white70, fontSize: 14),
                        ),
                      ],
                    ),
                  ),
                ),
              
              if (_errorMessage != null)
                Container(
                  color: const Color(0xFF0A0A0A),
                  child: Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.wifi_off, size: 64, color: Colors.white30),
                        const SizedBox(height: 16),
                        Text(
                          _errorMessage!,
                          style: const TextStyle(color: Colors.white54, fontSize: 14),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 24),
                        ElevatedButton(
                          onPressed: _refresh,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFFA855F7),
                            foregroundColor: Colors.white,
                          ),
                          child: const Text('重新加载'),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        ),
      );
  }

  void _showExitDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1A1A1A),
        title: const Text('退出应用', style: TextStyle(color: Colors.white)),
        content: const Text('确定要退出应用吗？', style: TextStyle(color: Colors.white70)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('取消', style: TextStyle(color: Colors.white54)),
          ),
          TextButton(
            onPressed: () => SystemNavigator.pop(),
            child: const Text('退出', style: TextStyle(color: Color(0xFFA855F7))),
          ),
        ],
      ),
    );
  }
}