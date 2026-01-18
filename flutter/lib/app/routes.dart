import 'package:flutter/material.dart';

import '../features/auth/screens/login_screen.dart';
import '../features/auth/screens/register_screen.dart';
import '../features/home/screens/home_screen.dart';
import '../features/video/screens/video_player_screen.dart';
import '../features/video/screens/video_list_screen.dart';
import '../features/shorts/screens/shorts_screen.dart';
import '../features/profile/screens/profile_screen.dart';
import '../features/vip/screens/vip_screen.dart';
import '../features/search/screens/search_screen.dart';
import '../screens/common/main_layout.dart';
import '../screens/splash/splash_screen.dart';

class AppRoutes {
  static const String splash = '/';
  static const String login = '/login';
  static const String register = '/register';
  static const String home = '/home';
  static const String videoPlayer = '/video';
  static const String videoList = '/videos';
  static const String shorts = '/shorts';
  static const String profile = '/profile';
  static const String vip = '/vip';
  static const String search = '/search';
  
  static Route<dynamic> generateRoute(RouteSettings settings) {
    switch (settings.name) {
      case splash:
        return MaterialPageRoute(builder: (_) => const SplashScreen());
      
      case login:
        return MaterialPageRoute(builder: (_) => const LoginScreen());
      
      case register:
        return MaterialPageRoute(builder: (_) => const RegisterScreen());
      
      case home:
        // 使用 MainLayout 作为主页面，包含底部导航和 WebView 页面
        return MaterialPageRoute(builder: (_) => const MainLayout());
      
      case videoPlayer:
        final args = settings.arguments as Map<String, dynamic>;
        return MaterialPageRoute(
          builder: (_) => VideoPlayerScreen(videoId: args['videoId']),
        );
      
      case videoList:
        final args = settings.arguments as Map<String, dynamic>?;
        return MaterialPageRoute(
          builder: (_) => VideoListScreen(
            categoryId: args?['categoryId'],
            title: args?['title'] ?? '视频列表',
          ),
        );
      
      case shorts:
        return MaterialPageRoute(builder: (_) => const ShortsScreen());
      
      case profile:
        return MaterialPageRoute(builder: (_) => const ProfileScreen());
      
      case vip:
        return MaterialPageRoute(builder: (_) => const VipScreen());
      
      case search:
        return MaterialPageRoute(builder: (_) => const SearchScreen());
      
      default:
        return MaterialPageRoute(
          builder: (_) => Scaffold(
            body: Center(
              child: Text('页面不存在: ${settings.name}'),
            ),
          ),
        );
    }
  }
}
