import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';
import 'package:webview_flutter_wkwebview/webview_flutter_wkwebview.dart';
import 'package:vod_app/core/services/token_manager.dart';
import 'package:vod_app/core/services/js_bridge.dart';
import 'package:file_picker/file_picker.dart';
import 'dart:io' show Platform, File;

/// WebView 页面容器
class WebViewPage extends StatefulWidget {
  final String url;
  final String? title;
  final bool showAppBar;
  final bool enableEdgeSwipeBack;

  const WebViewPage({
    super.key,
    required this.url,
    this.title,
    this.showAppBar = true,
    this.enableEdgeSwipeBack = false,
  });

  @override
  State<WebViewPage> createState() => _WebViewPageState();
}

class _WebViewPageState extends State<WebViewPage> with WidgetsBindingObserver {
  late WebViewController _controller;
  late JSBridge _jsBridge;
  bool _isLoading = true;
  bool _hasError = false;
  int _loadingProgress = 0;
  bool _mounted = true;
  bool _isFirstLoad = true;  // 首次加载标记，用于隐藏进度条
  
  // 边缘滑动返回相关
  double _dragStartX = 0;
  bool _isDragging = false;
  static const double _edgeWidth = 30.0; // 左边缘触发区域宽度

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initWebView();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _mounted = false;
    super.dispose();
  }

  // 监听App生命周期，从后台恢复时重新注入token
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      debugPrint('App从后台恢复，重新注入Token');
      _injectToken();
    }
  }

  // 注入Token到WebView
  Future<void> _injectToken() async {
    try {
      final script = TokenManager().generateTokenInjectionScript();
      if (script.isNotEmpty) {
        await _controller.runJavaScript(script);
        debugPrint('Token注入成功');
      }
    } catch (e) {
      debugPrint('Token注入失败: $e');
    }
  }

  void _safeSetState(VoidCallback fn) {
    if (_mounted && mounted) {
      setState(fn);
    }
  }

  void _initWebView() {
    debugPrint('WebView 初始化: ${widget.url}');
    
    // 平台特定配置
    late final PlatformWebViewControllerCreationParams params;
    if (Platform.isIOS) {
      // iOS: 配置WKWebView数据持久化
      params = WebKitWebViewControllerCreationParams(
        allowsInlineMediaPlayback: true,
        mediaTypesRequiringUserAction: const <PlaybackMediaTypes>{},
      );
    } else {
      params = const PlatformWebViewControllerCreationParams();
    }
    
    _controller = WebViewController.fromPlatformCreationParams(params)
      ..setBackgroundColor(Colors.black)  // 设置 WebView 背景为黑色
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(NavigationDelegate(
        onPageStarted: (url) {
          debugPrint('WebView 开始加载: $url');
          _safeSetState(() {
            _isLoading = true;
            _hasError = false;
          });
        },
        onPageFinished: (url) {
          debugPrint('WebView 加载完成: $url');
          _onPageLoaded();
        },
        onProgress: (progress) {
          _safeSetState(() => _loadingProgress = progress);
        },
        onNavigationRequest: (request) {
          debugPrint('WebView 导航请求: ${request.url}');
          return NavigationDecision.navigate;
        },
        onWebResourceError: (error) {
          // 只记录主框架错误，忽略资源加载错误（如视频、图片）
          if (error.isForMainFrame == true) {
            debugPrint('WebView 主框架错误: ${error.description}, URL: ${error.url}');
            _safeSetState(() {
              _hasError = true;
              _isLoading = false;
            });
          }
          // 资源加载错误不显示错误页面，只记录日志
        },
      ))
      ..loadRequest(Uri.parse(widget.url));
    
    // Android 平台配置文件选择器
    if (Platform.isAndroid) {
      final androidController = _controller.platform as AndroidWebViewController;
      androidController.setOnShowFileSelector((params) async {
        debugPrint('文件选择器被调用: ${params.acceptTypes}');
        
        // 根据 acceptTypes 确定文件类型
        FileType fileType = FileType.any;
        List<String>? allowedExtensions;
        
        final acceptTypes = params.acceptTypes;
        if (acceptTypes.isNotEmpty) {
          final firstType = acceptTypes.first.toLowerCase();
          if (firstType.contains('image')) {
            fileType = FileType.image;
          } else if (firstType.contains('video')) {
            fileType = FileType.video;
          } else if (firstType.contains('audio')) {
            fileType = FileType.audio;
          }
        }
        
        try {
          final result = await FilePicker.platform.pickFiles(
            type: fileType,
            allowMultiple: params.mode == FileSelectorMode.openMultiple,
            allowedExtensions: allowedExtensions,
          );
          
          if (result != null && result.files.isNotEmpty) {
            final paths = result.files
                .where((f) => f.path != null)
                .map((f) => 'file://${f.path}')
                .toList();
            debugPrint('选择的文件: $paths');
            return paths;
          }
        } catch (e) {
          debugPrint('文件选择错误: $e');
        }
        
        return [];
      });
    }

    _jsBridge = JSBridge(
      controller: _controller,
      onNavigate: _handleNavigation,
      onTokenUpdate: _handleTokenUpdate,
    );
    _jsBridge.init();
  }

  Future<void> _onPageLoaded() async {
    if (!_mounted || !mounted) return;
    
    // 注入 Token
    await _injectToken();
    
    _safeSetState(() {
      _isLoading = false;
      _isFirstLoad = false;  // 首次加载完成
    });
  }

  void _handleNavigation(String route, Map<String, dynamic>? params) {
    // 通过 Navigator 处理导航
    Navigator.pushNamed(context, route, arguments: params);
  }

  void _handleTokenUpdate(String token) {
    TokenManager().setToken(token);
  }

  Future<bool> _onWillPop() async {
    if (await _controller.canGoBack()) {
      await _controller.goBack();
      return false;
    }
    return true;
  }

  // 处理边缘滑动开始
  void _onHorizontalDragStart(DragStartDetails details) {
    if (!widget.enableEdgeSwipeBack) return;
    
    // 只在左边缘触发
    if (details.localPosition.dx <= _edgeWidth) {
      _dragStartX = details.localPosition.dx;
      _isDragging = true;
    }
  }

  // 处理边缘滑动更新
  void _onHorizontalDragUpdate(DragUpdateDetails details) {
    // 可以在这里添加滑动动画效果
  }

  // 处理边缘滑动结束
  void _onHorizontalDragEnd(DragEndDetails details) async {
    if (!_isDragging) return;
    _isDragging = false;
    
    // 检查滑动速度，如果向右滑动且速度足够快，执行返回
    if (details.velocity.pixelsPerSecond.dx > 200) {
      if (await _controller.canGoBack()) {
        await _controller.goBack();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    Widget webViewContent = Container(
      color: Colors.black,
      child: Stack(
        children: [
          WebViewWidget(controller: _controller),
        // 只在非首次加载时显示进度条，避免开屏后的紫色闪烁
        if (_isLoading && _loadingProgress < 100 && !_isFirstLoad)
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: LinearProgressIndicator(
              value: _loadingProgress / 100,
              backgroundColor: Colors.transparent,
              valueColor: const AlwaysStoppedAnimation<Color>(Colors.white24),
            ),
          ),
        if (_hasError) _buildErrorWidget(),
        // 左边缘滑动检测区域
        if (widget.enableEdgeSwipeBack)
          Positioned(
            left: 0,
            top: 0,
            bottom: 0,
            width: _edgeWidth,
            child: GestureDetector(
              onHorizontalDragStart: _onHorizontalDragStart,
              onHorizontalDragUpdate: _onHorizontalDragUpdate,
              onHorizontalDragEnd: _onHorizontalDragEnd,
              behavior: HitTestBehavior.translucent,
            ),
          ),
      ],
      ),
    );

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) async {
        if (didPop) return;
        final canPop = await _onWillPop();
        if (canPop && context.mounted) {
          Navigator.of(context).pop();
        }
      },
      child: Scaffold(
        backgroundColor: Colors.black,
        appBar: widget.showAppBar
            ? AppBar(
                title: Text(widget.title ?? ''),
                actions: [
                  if (_isLoading)
                    const Padding(
                      padding: EdgeInsets.all(16),
                      child: SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                    ),
                ],
              )
            : null,
        body: webViewContent,
      ),
    );
  }

  Widget _buildErrorWidget() {
    return Container(
      color: Colors.white,
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.red),
            const SizedBox(height: 16),
            const Text('页面加载失败', style: TextStyle(fontSize: 16)),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () {
                setState(() {
                  _hasError = false;
                  _isLoading = true;
                });
                _controller.reload();
              },
              child: const Text('重试'),
            ),
          ],
        ),
      ),
    );
  }
}
