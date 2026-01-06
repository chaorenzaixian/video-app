import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/providers/auth_provider.dart';
import 'routes.dart';
import 'theme.dart';

class VODApp extends StatelessWidget {
  const VODApp({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (context, auth, _) {
        return MaterialApp(
          title: 'VOD 视频',
          debugShowCheckedModeBanner: false,
          theme: AppTheme.darkTheme,
          initialRoute: auth.isLoggedIn ? AppRoutes.home : AppRoutes.login,
          onGenerateRoute: AppRoutes.generateRoute,
        );
      },
    );
  }
}
