class Category {
  final int id;
  final String name;
  final String? description;
  final String? icon;
  final int videoCount;
  final int sortOrder;
  final bool isFeatured;
  final List<Category> children;
  
  Category({
    required this.id,
    required this.name,
    this.description,
    this.icon,
    this.videoCount = 0,
    this.sortOrder = 0,
    this.isFeatured = false,
    this.children = const [],
  });
  
  factory Category.fromJson(Map<String, dynamic> json) {
    return Category(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      icon: json['icon'],
      videoCount: json['video_count'] ?? 0,
      sortOrder: json['sort_order'] ?? 0,
      isFeatured: json['is_featured'] ?? false,
      children: (json['children'] as List?)
          ?.map((e) => Category.fromJson(e))
          .toList() ?? [],
    );
  }
}
