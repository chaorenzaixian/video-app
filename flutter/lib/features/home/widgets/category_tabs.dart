import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../app/theme.dart';
import '../../../core/models/category.dart';

class CategoryTabs extends StatelessWidget {
  final List<Category> categories;
  final int? selectedId;
  final Function(int?) onSelected;

  const CategoryTabs({
    super.key,
    required this.categories,
    required this.selectedId,
    required this.onSelected,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 40.h,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: EdgeInsets.symmetric(horizontal: 12.w),
        itemCount: categories.length + 1, // +1 for "全部"
        itemBuilder: (context, index) {
          if (index == 0) {
            return _buildTab(
              id: null,
              name: '全部',
              isSelected: selectedId == null,
            );
          }
          
          final category = categories[index - 1];
          return _buildTab(
            id: category.id,
            name: category.name,
            isSelected: selectedId == category.id,
          );
        },
      ),
    );
  }

  Widget _buildTab({
    required int? id,
    required String name,
    required bool isSelected,
  }) {
    return GestureDetector(
      onTap: () => onSelected(id),
      child: Container(
        margin: EdgeInsets.only(right: 8.w),
        padding: EdgeInsets.symmetric(horizontal: 16.w),
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.primaryColor : AppTheme.surfaceColor,
          borderRadius: BorderRadius.circular(20.r),
        ),
        alignment: Alignment.center,
        child: Text(
          name,
          style: TextStyle(
            fontSize: 14.sp,
            color: isSelected ? Colors.white : AppTheme.textSecondary,
            fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
          ),
        ),
      ),
    );
  }
}
