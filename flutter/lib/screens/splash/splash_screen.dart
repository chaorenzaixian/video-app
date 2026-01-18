import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// 原生开屏页
class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    // 设置全屏沉浸式
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
    
    // 延迟后跳转到主页
    Future.delayed(const Duration(seconds: 2), () {
      if (mounted) {
        // 恢复状态栏
        SystemChrome.setEnabledSystemUIMode(
          SystemUiMode.edgeToEdge,
          overlays: [SystemUiOverlay.top, SystemUiOverlay.bottom],
        );
        Navigator.of(context).pushReplacementNamed('/home');
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: const BoxDecoration(
          image: DecorationImage(
            image: AssetImage('assets/images/launch/ic_splash_bg.webp'),
            fit: BoxFit.cover,
          ),
        ),
      ),
    );
  }
}
