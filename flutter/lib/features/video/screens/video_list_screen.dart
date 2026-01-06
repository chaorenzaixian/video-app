import 'package:flutter/material.dart';

class VideoListScreen extends StatelessWidget {
  final int? categoryId;
  final String title;

  const VideoListScreen({
    super.key,
    this.categoryId,
    required this.title,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(title),
      ),
      body: const Center(
        child: Text('视频列表'),
      ),
    );
  }
}
