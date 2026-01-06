import 'package:dio/dio.dart';
import 'storage_service.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  
  late Dio _dio;
  
  // API 基础地址（根据环境配置）
  static const String baseUrl = 'http://your-server-ip:8001/api/v1';
  
  ApiService._internal() {
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
      headers: {
        'Content-Type': 'application/json',
      },
    ));
    
    // 请求拦截器
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        // 添加 Token
        final token = StorageService.getToken();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        
        // 添加设备指纹
        final deviceId = StorageService.getDeviceId();
        if (deviceId != null) {
          options.headers['X-Device-Fingerprint'] = deviceId;
        }
        
        return handler.next(options);
      },
      onError: (error, handler) async {
        // 401 错误处理
        if (error.response?.statusCode == 401) {
          // 尝试刷新 Token
          final refreshed = await _refreshToken();
          if (refreshed) {
            // 重试请求
            final opts = error.requestOptions;
            opts.headers['Authorization'] = 'Bearer ${StorageService.getToken()}';
            final response = await _dio.fetch(opts);
            return handler.resolve(response);
          }
        }
        return handler.next(error);
      },
    ));
  }
  
  Future<bool> _refreshToken() async {
    try {
      final refreshToken = StorageService.getRefreshToken();
      if (refreshToken == null) return false;
      
      final response = await _dio.post('/auth/refresh', data: {
        'refresh_token': refreshToken,
      });
      
      if (response.statusCode == 200) {
        final data = response.data;
        await StorageService.saveToken(data['access_token']);
        await StorageService.saveRefreshToken(data['refresh_token']);
        return true;
      }
    } catch (e) {
      // 刷新失败，清除登录状态
      await StorageService.clearAuth();
    }
    return false;
  }
  
  // ========== 认证接口 ==========
  
  Future<Response> login(String username, String password) {
    return _dio.post('/auth/login', data: {
      'username': username,
      'password': password,
    });
  }
  
  Future<Response> register(String username, String email, String password, {String? inviteCode}) {
    return _dio.post('/auth/register', data: {
      'username': username,
      'email': email,
      'password': password,
      if (inviteCode != null) 'invite_code': inviteCode,
    });
  }
  
  Future<Response> guestRegister(String deviceId) {
    return _dio.post('/auth/guest/register', data: {
      'device_id': deviceId,
    });
  }
  
  // ========== 用户接口 ==========
  
  Future<Response> getCurrentUser() {
    return _dio.get('/users/me');
  }
  
  Future<Response> updateProfile(Map<String, dynamic> data) {
    return _dio.put('/users/me', data: data);
  }
  
  // ========== 视频接口 ==========
  
  Future<Response> getVideos({
    int page = 1,
    int pageSize = 20,
    int? categoryId,
    String? search,
    String? sortBy,
  }) {
    return _dio.get('/videos', queryParameters: {
      'page': page,
      'page_size': pageSize,
      if (categoryId != null) 'category_id': categoryId,
      if (search != null) 'search': search,
      if (sortBy != null) 'sort_by': sortBy,
    });
  }
  
  Future<Response> getVideoDetail(int videoId) {
    return _dio.get('/videos/$videoId');
  }
  
  Future<Response> getCategories() {
    return _dio.get('/videos/categories');
  }
  
  Future<Response> getShorts({int page = 1, int pageSize = 10}) {
    return _dio.get('/shorts', queryParameters: {
      'page': page,
      'page_size': pageSize,
    });
  }
  
  // ========== VIP 接口 ==========
  
  Future<Response> getVipPrices() {
    return _dio.get('/payments/prices');
  }
  
  Future<Response> getVipCards() {
    return _dio.get('/vip/cards');
  }
  
  Future<Response> createOrder(String orderType, String paymentMethod) {
    return _dio.post('/payments/orders', data: {
      'order_type': orderType,
      'payment_method': paymentMethod,
    });
  }
  
  // ========== 易支付接口 ==========
  
  /// 创建易支付订单（页面跳转方式）
  /// [orderType] 订单类型: VIP_MONTHLY, VIP_QUARTERLY, VIP_YEARLY, VIP_LIFETIME
  /// [payType] 支付方式: alipay, wxpay, qqpay
  Future<Response> createEpayOrder(String orderType, String payType) {
    return _dio.post('/payments/epay/create', 
      data: {'order_type': orderType},
      queryParameters: {'pay_type': payType},
    );
  }
  
  /// 创建易支付订单（获取二维码）
  Future<Response> createEpayQrOrder(String orderType, String payType) {
    return _dio.post('/payments/epay/create-qr',
      data: {'order_type': orderType},
      queryParameters: {'pay_type': payType},
    );
  }
  
  /// 查询易支付订单状态
  Future<Response> queryEpayOrder(String orderNo) {
    return _dio.get('/payments/epay/query/$orderNo');
  }
  
  // ========== 社交接口 ==========
  
  Future<Response> likeVideo(int videoId) {
    return _dio.post('/social/videos/$videoId/like');
  }
  
  Future<Response> favoriteVideo(int videoId) {
    return _dio.post('/social/videos/$videoId/favorite');
  }
  
  Future<Response> getComments(int videoId, {int page = 1}) {
    return _dio.get('/comments/video/$videoId', queryParameters: {
      'page': page,
    });
  }
  
  Future<Response> addComment(int videoId, String content) {
    return _dio.post('/comments', data: {
      'video_id': videoId,
      'content': content,
    });
  }
}
