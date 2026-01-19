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
      // 确保整个应用背景是黑色，避免白色闪烁
      builder: (context, child) {
        return Container(
          color: Colors.black,
          child: child,
        );
      },
      initialRoute: AppRoutes.splash,  // 从开屏页启动
      onGenerateRoute: AppRoutes.generateRoute,
    );
  }
}
