import 'package:flutter/material.dart';
import 'routes.dart';
import 'theme.dart';

class VODApp extends StatelessWidget {
  const VODApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Soul',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      initialRoute: AppRoutes.splash,  // 从开屏页启动
      onGenerateRoute: AppRoutes.generateRoute,
    );
  }
}
