import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'dart:async';

import 'app/app.dart';
import 'core/providers/auth_provider.dart';
import 'core/providers/video_provider.dart';
import 'core/providers/user_provider.dart';
import 'services/api_service.dart';
import 'services/storage_service.dart';

void main() async {
  // 捕获 Flutter 框架错误
  FlutterError.onError = (FlutterErrorDetails details) {
    FlutterError.presentError(details);
    debugPrint('Flutter Error: ${details.exception}');
  };
  
  // 捕获异步错误
  runZonedGuarded(() async {
    WidgetsFlutterBinding.ensureInitialized();
    
    // 设置状态栏样式
    SystemChrome.setSystemUIOverlayStyle(
      const SystemUiOverlayStyle(
        statusBarColor: Colors.transparent,
        statusBarIconBrightness: Brightness.light,
      ),
    );
    
    // 初始化服务
    try {
      await StorageService.init();
    } catch (e) {
      debugPrint('StorageService init error: $e');
    }
    
    runApp(const MyApp());
  }, (error, stackTrace) {
    debugPrint('Uncaught error: $error');
    debugPrint('Stack trace: $stackTrace');
  });
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ScreenUtilInit(
      designSize: const Size(375, 812),
      minTextAdapt: true,
      builder: (context, child) {
        return MultiProvider(
          providers: [
            ChangeNotifierProvider(create: (_) => AuthProvider()),
            ChangeNotifierProvider(create: (_) => UserProvider()),
            ChangeNotifierProvider(create: (_) => VideoProvider()),
          ],
          child: const VODApp(),
        );
      },
    );
  }
}
