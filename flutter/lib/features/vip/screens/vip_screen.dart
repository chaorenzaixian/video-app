import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../app/theme.dart';
import '../../../core/services/api_service.dart';

class VipScreen extends StatefulWidget {
  const VipScreen({super.key});

  @override
  State<VipScreen> createState() => _VipScreenState();
}

class _VipScreenState extends State<VipScreen> {
  int _selectedPlan = 1; // 默认选中月度
  String _selectedPayType = 'alipay'; // 默认支付宝
  bool _isProcessing = false;

  final List<Map<String, dynamic>> _plans = [
    {
      'id': 0,
      'name': '月度会员',
      'price': 29,
      'originalPrice': 39,
      'days': 30,
      'tag': '',
      'orderType': 'VIP_MONTHLY',
    },
    {
      'id': 1,
      'name': '季度会员',
      'price': 79,
      'originalPrice': 117,
      'days': 90,
      'tag': '推荐',
      'orderType': 'VIP_QUARTERLY',
    },
    {
      'id': 2,
      'name': '年度会员',
      'price': 199,
      'originalPrice': 468,
      'days': 365,
      'tag': '超值',
      'orderType': 'VIP_YEARLY',
    },
    {
      'id': 3,
      'name': '永久会员',
      'price': 499,
      'originalPrice': 999,
      'days': 36500,
      'tag': '终身',
      'orderType': 'VIP_LIFETIME',
    },
  ];

  final List<Map<String, dynamic>> _paymentMethods = [
    {'type': 'alipay', 'name': '支付宝', 'icon': Icons.account_balance_wallet},
    {'type': 'wxpay', 'name': '微信支付', 'icon': Icons.chat_bubble},
    {'type': 'qqpay', 'name': 'QQ钱包', 'icon': Icons.account_circle},
  ];

  Future<void> _handlePay() async {
    // 显示支付方式选择弹窗
    final result = await showModalBottomSheet<bool>(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => _buildPaymentSheet(),
    );
    
    if (result == true) {
      _processPayment();
    }
  }

  Future<void> _processPayment() async {
    if (_isProcessing) return;
    
    setState(() => _isProcessing = true);
    
    try {
      final orderType = _plans[_selectedPlan]['orderType'];
      final response = await ApiService().createEpayOrder(orderType, _selectedPayType);
      
      if (response.statusCode == 200) {
        final data = response.data;
        final paymentUrl = data['payment_url'];
        
        if (paymentUrl != null) {
          // 打开支付页面
          final uri = Uri.parse(paymentUrl);
          if (await canLaunchUrl(uri)) {
            await launchUrl(uri, mode: LaunchMode.externalApplication);
          } else {
            _showError('无法打开支付页面');
          }
        } else if (data['qr_code'] != null) {
          // 显示二维码（可选实现）
          _showMessage('请使用手机扫码支付');
        } else {
          _showError('获取支付链接失败');
        }
      } else {
        _showError('创建订单失败');
      }
    } catch (e) {
      _showError('支付失败: $e');
    } finally {
      setState(() => _isProcessing = false);
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }

  void _showMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  Widget _buildPaymentSheet() {
    return StatefulBuilder(
      builder: (context, setSheetState) {
        return Container(
          decoration: BoxDecoration(
            color: AppTheme.surfaceColor,
            borderRadius: BorderRadius.vertical(top: Radius.circular(20.r)),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // 标题栏
              Container(
                padding: EdgeInsets.all(16.w),
                decoration: BoxDecoration(
                  border: Border(
                    bottom: BorderSide(color: Colors.white10),
                  ),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '选择支付方式',
                      style: TextStyle(
                        fontSize: 18.sp,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close),
                      onPressed: () => Navigator.pop(context),
                    ),
                  ],
                ),
              ),
              
              // 支付方式列表
              Padding(
                padding: EdgeInsets.all(16.w),
                child: Column(
                  children: _paymentMethods.map((method) {
                    final isSelected = _selectedPayType == method['type'];
                    return GestureDetector(
                      onTap: () {
                        setSheetState(() {
                          _selectedPayType = method['type'];
                        });
                        setState(() {});
                      },
                      child: Container(
                        margin: EdgeInsets.only(bottom: 12.h),
                        padding: EdgeInsets.all(16.w),
                        decoration: BoxDecoration(
                          color: isSelected 
                              ? AppTheme.primaryColor.withOpacity(0.1)
                              : AppTheme.cardColor,
                          borderRadius: BorderRadius.circular(12.r),
                          border: Border.all(
                            color: isSelected 
                                ? AppTheme.primaryColor 
                                : Colors.transparent,
                            width: 2,
                          ),
                        ),
                        child: Row(
                          children: [
                            Icon(
                              method['icon'],
                              size: 28.w,
                              color: isSelected 
                                  ? AppTheme.primaryColor 
                                  : AppTheme.textSecondary,
                            ),
                            SizedBox(width: 12.w),
                            Text(
                              method['name'],
                              style: TextStyle(
                                fontSize: 16.sp,
                                color: AppTheme.textPrimary,
                              ),
                            ),
                            const Spacer(),
                            if (isSelected)
                              Icon(
                                Icons.check_circle,
                                color: AppTheme.primaryColor,
                                size: 24.w,
                              ),
                          ],
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ),
              
              // 金额显示
              Padding(
                padding: EdgeInsets.symmetric(horizontal: 16.w),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '支付金额',
                      style: TextStyle(
                        fontSize: 14.sp,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                    Text(
                      '¥${_plans[_selectedPlan]['price']}',
                      style: TextStyle(
                        fontSize: 24.sp,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.primaryColor,
                      ),
                    ),
                  ],
                ),
              ),
              
              // 确认按钮
              Padding(
                padding: EdgeInsets.all(16.w),
                child: SafeArea(
                  child: SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _isProcessing 
                          ? null 
                          : () => Navigator.pop(context, true),
                      style: ElevatedButton.styleFrom(
                        padding: EdgeInsets.symmetric(vertical: 14.h),
                      ),
                      child: Text(_isProcessing ? '处理中...' : '确认支付'),
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('开通 VIP'),
      ),
      body: Column(
        children: [
          // VIP 权益展示
          Container(
            width: double.infinity,
            padding: EdgeInsets.all(24.w),
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xFF6366F1), Color(0xFF8B5CF6)],
              ),
            ),
            child: Column(
              children: [
                Icon(
                  Icons.diamond,
                  size: 48.w,
                  color: Colors.white,
                ),
                SizedBox(height: 12.h),
                Text(
                  'VIP 会员特权',
                  style: TextStyle(
                    fontSize: 20.sp,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                SizedBox(height: 16.h),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    _buildPrivilege(Icons.hd, '高清画质'),
                    _buildPrivilege(Icons.download, '离线下载'),
                    _buildPrivilege(Icons.block, '免广告'),
                    _buildPrivilege(Icons.star, '专属内容'),
                  ],
                ),
              ],
            ),
          ),
          
          // 套餐选择
          Expanded(
            child: ListView(
              padding: EdgeInsets.all(16.w),
              children: [
                Text(
                  '选择套餐',
                  style: TextStyle(
                    fontSize: 18.sp,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.textPrimary,
                  ),
                ),
                SizedBox(height: 16.h),
                
                ..._plans.map((plan) => _buildPlanCard(plan)),
              ],
            ),
          ),
          
          // 底部支付按钮
          Container(
            padding: EdgeInsets.all(16.w),
            decoration: BoxDecoration(
              color: AppTheme.surfaceColor,
              boxShadow: [
                BoxShadow(
                  color: Colors.black26,
                  blurRadius: 8,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            child: SafeArea(
              child: Row(
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        '¥${_plans[_selectedPlan]['price']}',
                        style: TextStyle(
                          fontSize: 24.sp,
                          fontWeight: FontWeight.bold,
                          color: AppTheme.primaryColor,
                        ),
                      ),
                      Text(
                        '原价 ¥${_plans[_selectedPlan]['originalPrice']}',
                        style: TextStyle(
                          fontSize: 12.sp,
                          color: AppTheme.textSecondary,
                          decoration: TextDecoration.lineThrough,
                        ),
                      ),
                    ],
                  ),
                  SizedBox(width: 16.w),
                  Expanded(
                    child: ElevatedButton(
                      onPressed: _isProcessing ? null : _handlePay,
                      style: ElevatedButton.styleFrom(
                        padding: EdgeInsets.symmetric(vertical: 14.h),
                      ),
                      child: Text(_isProcessing ? '处理中...' : '立即开通'),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPrivilege(IconData icon, String label) {
    return Column(
      children: [
        Icon(icon, size: 24.w, color: Colors.white),
        SizedBox(height: 4.h),
        Text(
          label,
          style: TextStyle(
            fontSize: 12.sp,
            color: Colors.white70,
          ),
        ),
      ],
    );
  }

  Widget _buildPlanCard(Map<String, dynamic> plan) {
    final isSelected = _selectedPlan == plan['id'];
    
    return GestureDetector(
      onTap: () {
        setState(() {
          _selectedPlan = plan['id'];
        });
      },
      child: Container(
        margin: EdgeInsets.only(bottom: 12.h),
        padding: EdgeInsets.all(16.w),
        decoration: BoxDecoration(
          color: AppTheme.cardColor,
          borderRadius: BorderRadius.circular(12.r),
          border: Border.all(
            color: isSelected ? AppTheme.primaryColor : Colors.transparent,
            width: 2,
          ),
        ),
        child: Row(
          children: [
            // 选中指示器
            Container(
              width: 24.w,
              height: 24.w,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: isSelected ? AppTheme.primaryColor : Colors.transparent,
                border: Border.all(
                  color: isSelected ? AppTheme.primaryColor : AppTheme.textSecondary,
                  width: 2,
                ),
              ),
              child: isSelected
                  ? Icon(Icons.check, size: 16.w, color: Colors.white)
                  : null,
            ),
            SizedBox(width: 12.w),
            
            // 套餐信息
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(
                        plan['name'],
                        style: TextStyle(
                          fontSize: 16.sp,
                          fontWeight: FontWeight.bold,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                      if (plan['tag'].isNotEmpty) ...[
                        SizedBox(width: 8.w),
                        Container(
                          padding: EdgeInsets.symmetric(
                            horizontal: 6.w,
                            vertical: 2.h,
                          ),
                          decoration: BoxDecoration(
                            color: AppTheme.accentColor,
                            borderRadius: BorderRadius.circular(4.r),
                          ),
                          child: Text(
                            plan['tag'],
                            style: TextStyle(
                              fontSize: 10.sp,
                              color: Colors.white,
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                  SizedBox(height: 4.h),
                  Text(
                    '${plan['days']}天',
                    style: TextStyle(
                      fontSize: 12.sp,
                      color: AppTheme.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
            
            // 价格
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  '¥${plan['price']}',
                  style: TextStyle(
                    fontSize: 20.sp,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.primaryColor,
                  ),
                ),
                Text(
                  '¥${plan['originalPrice']}',
                  style: TextStyle(
                    fontSize: 12.sp,
                    color: AppTheme.textSecondary,
                    decoration: TextDecoration.lineThrough,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
