/// 资源文件路径管理 - 与 Web 版本完全一致
/// 所有图片资源从 frontend/public/images/backgrounds 复制而来
class AppAssets {
  // ============================================
  // 底部导航图标 (home_X_Y: X=tab索引, Y=0未选中/1选中)
  // ============================================
  static const String home00 = 'assets/images/home_0_0.webp'; // 首页-未选中
  static const String home01 = 'assets/images/home_0_1.webp'; // 首页-选中
  static const String home10 = 'assets/images/home_1_0.webp'; // 禁区-未选中
  static const String home11 = 'assets/images/home_1_1.webp'; // 禁区-选中
  static const String home20 = 'assets/images/home_2_0.webp'; // Soul-未选中
  static const String home21 = 'assets/images/home_2_1.webp'; // Soul-选中
  static const String home30 = 'assets/images/home_3_0.webp'; // 广场-未选中
  static const String home31 = 'assets/images/home_3_1.webp'; // 广场-选中
  static const String home40 = 'assets/images/home_4_0.webp'; // 自己-未选中
  static const String home41 = 'assets/images/home_4_1.webp'; // 自己-选中
  
  // ============================================
  // 顶部栏图标
  // ============================================
  static const String fuli = 'assets/images/fuli.webp';              // 福利图标
  static const String soulTitle = 'assets/images/soul_title.webp';   // Soul Logo
  static const String icSearch = 'assets/images/ic_search.webp';     // 搜索图标
  static const String shortLogo = 'assets/images/short_logo.webp';   // 短视频浮动入口
  
  // ============================================
  // 个人中心图标
  // ============================================
  static const String mineNotification = 'assets/images/mine_notification.png'; // 通知图标
  static const String icService = 'assets/images/ic_service.webp';   // 客服图标
  static const String icSetting = 'assets/images/ic_setting.webp';   // 设置图标
  static const String icSign = 'assets/images/ic_sign.webp';         // 签到图标
  static const String icHistory = 'assets/images/ic_history.webp';   // 观看记录
  static const String icCollect = 'assets/images/ic_collect.webp';   // 我的收藏
  static const String icBuy = 'assets/images/ic_buy.webp';           // 我的购买
  static const String icAi = 'assets/images/ic_ai.webp';             // AI女友
  static const String icCoin = 'assets/images/ic_coin.webp';         // 金币图标
  static const String icGift = 'assets/images/ic_gift.webp';         // 礼物图标
  
  // ============================================
  // VIP相关
  // ============================================
  static const String vipGold = 'assets/images/vip_gold.webp';       // VIP金色等级
  static const String vip1 = 'assets/images/vip_1.webp';             // VIP等级1
  static const String vip2 = 'assets/images/vip_2.webp';             // VIP等级2
  static const String vip3 = 'assets/images/vip_3.webp';             // VIP等级3
  static const String vipCenter = 'assets/images/vip_center.webp';   // VIP中心
  static const String superVipBlue = 'assets/images/super_vip_blue.webp';   // 超级VIP蓝
  static const String superVipRed = 'assets/images/super_vip_red.webp';     // 超级VIP红
  static const String vipRecommend = 'assets/images/vip_recommend.webp';    // VIP推荐
  static const String vipRecommendHeader = 'assets/images/vip_recommend_header.webp';
  static const String imgCrown = 'assets/images/img_crown.webp';     // 皇冠图标
  
  // ============================================
  // 钱包相关
  // ============================================
  static const String myWallet = 'assets/images/my_wallet.webp';     // 我的钱包
  static const String agent = 'assets/images/agent.webp';            // 代理
  static const String proxyBanner = 'assets/images/proxy_banner.webp'; // 代理横幅
  static const String withdrawNow = 'assets/images/withdraw_now.webp'; // 立即提现
  
  // ============================================
  // 发布相关
  // ============================================
  static const String publishVideo = 'assets/images/publish_video.png';    // 发布视频
  static const String publishImg = 'assets/images/publish_img_1.webp';     // 发布图片
  static const String publishImgText = 'assets/images/publish_img_text.webp'; // 发布图文
  static const String publish = 'assets/images/publish.png';               // 发布按钮
  
  // ============================================
  // 背景图片
  // ============================================
  static const String girl = 'assets/images/girl.webp';
  static const String girl2 = 'assets/images/girl2.webp';
  static const String welfareVipBg = 'assets/images/welfare_vip_background.webp';
  static const String walletCoinBg = 'assets/images/wallet_coin_bg_1.png';
  static const String walletCoinBg6 = 'assets/images/wallet_coin_bg6_1.webp';
  static const String searchRankBg = 'assets/images/search_rank_bg.webp';
  
  // ============================================
  // 其他图标
  // ============================================
  static const String noData = 'assets/images/no_data.webp';         // 无数据
  static const String collectStart = 'assets/images/collect_start.webp'; // 收藏星
  static const String icLauncher = 'assets/images/ic_launcher.webp'; // 启动图标
  static const String icUnionPay = 'assets/images/ic_union_pay.webp'; // 银联
  static const String icUsdt = 'assets/images/ic_usdt.webp';         // USDT
  static const String walfareLogo = 'assets/images/walfare_logo.webp'; // 福利Logo
  
  // ============================================
  // 热门标签
  // ============================================
  static const String hot1 = 'assets/images/hot_1.webp';
  static const String hot2 = 'assets/images/hot_2.webp';
  static const String hot3 = 'assets/images/hot_3.webp';
  
  // ============================================
  // 辅助方法
  // ============================================
  
  /// 获取底部导航图标
  /// [index] - tab索引 (0-4)
  /// [isActive] - 是否选中
  static String getNavIcon(int index, bool isActive) {
    switch (index) {
      case 0:
        return isActive ? home01 : home00;
      case 1:
        return isActive ? home11 : home10;
      case 2:
        return isActive ? home21 : home20;
      case 3:
        return isActive ? home31 : home30;
      case 4:
        return isActive ? home41 : home40;
      default:
        return home00;
    }
  }
  
  /// 获取VIP等级图标
  /// [level] - VIP等级 (1-6)
  static String getVipIcon(int level) {
    switch (level) {
      case 1:
        return vipGold;      // 普通VIP
      case 2:
        return vip1;         // VIP 1
      case 3:
        return vip2;         // VIP 2
      case 4:
        return vip3;         // VIP 3
      case 5:
        return superVipBlue; // 黄金至尊
      case 6:
        return superVipRed;  // 紫色限定至尊
      default:
        return vipGold;
    }
  }
  
  /// 获取热门标签图标
  static String getHotIcon(int index) {
    switch (index % 3) {
      case 0:
        return hot1;
      case 1:
        return hot2;
      case 2:
        return hot3;
      default:
        return hot1;
    }
  }
}



class AppAssets {
  // ============================================
  // 底部导航图标 (home_X_Y: X=tab索引, Y=0未选中/1选中)
  // ============================================
  static const String home00 = 'assets/images/home_0_0.webp'; // 首页-未选中
  static const String home01 = 'assets/images/home_0_1.webp'; // 首页-选中
  static const String home10 = 'assets/images/home_1_0.webp'; // 禁区-未选中
  static const String home11 = 'assets/images/home_1_1.webp'; // 禁区-选中
  static const String home20 = 'assets/images/home_2_0.webp'; // Soul-未选中
  static const String home21 = 'assets/images/home_2_1.webp'; // Soul-选中
  static const String home30 = 'assets/images/home_3_0.webp'; // 广场-未选中
  static const String home31 = 'assets/images/home_3_1.webp'; // 广场-选中
  static const String home40 = 'assets/images/home_4_0.webp'; // 自己-未选中
  static const String home41 = 'assets/images/home_4_1.webp'; // 自己-选中
  
  // ============================================
  // 顶部栏图标
  // ============================================
  static const String fuli = 'assets/images/fuli.webp';              // 福利图标
  static const String soulTitle = 'assets/images/soul_title.webp';   // Soul Logo
  static const String icSearch = 'assets/images/ic_search.webp';     // 搜索图标
  static const String shortLogo = 'assets/images/short_logo.webp';   // 短视频浮动入口
  
  // ============================================
  // 个人中心图标
  // ============================================
  static const String mineNotification = 'assets/images/mine_notification.png'; // 通知图标
  static const String icService = 'assets/images/ic_service.webp';   // 客服图标
  static const String icSetting = 'assets/images/ic_setting.webp';   // 设置图标
  static const String icSign = 'assets/images/ic_sign.webp';         // 签到图标
  static const String icHistory = 'assets/images/ic_history.webp';   // 观看记录
  static const String icCollect = 'assets/images/ic_collect.webp';   // 我的收藏
  static const String icBuy = 'assets/images/ic_buy.webp';           // 我的购买
  static const String icAi = 'assets/images/ic_ai.webp';             // AI女友
  static const String icCoin = 'assets/images/ic_coin.webp';         // 金币图标
  static const String icGift = 'assets/images/ic_gift.webp';         // 礼物图标
  
  // ============================================
  // VIP相关
  // ============================================
  static const String vipGold = 'assets/images/vip_gold.webp';       // VIP金色等级
  static const String vip1 = 'assets/images/vip_1.webp';             // VIP等级1
  static const String vip2 = 'assets/images/vip_2.webp';             // VIP等级2
  static const String vip3 = 'assets/images/vip_3.webp';             // VIP等级3
  static const String vipCenter = 'assets/images/vip_center.webp';   // VIP中心
  static const String superVipBlue = 'assets/images/super_vip_blue.webp';   // 超级VIP蓝
  static const String superVipRed = 'assets/images/super_vip_red.webp';     // 超级VIP红
  static const String vipRecommend = 'assets/images/vip_recommend.webp';    // VIP推荐
  static const String vipRecommendHeader = 'assets/images/vip_recommend_header.webp';
  static const String imgCrown = 'assets/images/img_crown.webp';     // 皇冠图标
  
  // ============================================
  // 钱包相关
  // ============================================
  static const String myWallet = 'assets/images/my_wallet.webp';     // 我的钱包
  static const String agent = 'assets/images/agent.webp';            // 代理
  static const String proxyBanner = 'assets/images/proxy_banner.webp'; // 代理横幅
  static const String withdrawNow = 'assets/images/withdraw_now.webp'; // 立即提现
  
  // ============================================
  // 发布相关
  // ============================================
  static const String publishVideo = 'assets/images/publish_video.png';    // 发布视频
  static const String publishImg = 'assets/images/publish_img_1.webp';     // 发布图片
  static const String publishImgText = 'assets/images/publish_img_text.webp'; // 发布图文
  static const String publish = 'assets/images/publish.png';               // 发布按钮
  
  // ============================================
  // 背景图片
  // ============================================
  static const String girl = 'assets/images/girl.webp';
  static const String girl2 = 'assets/images/girl2.webp';
  static const String welfareVipBg = 'assets/images/welfare_vip_background.webp';
  static const String walletCoinBg = 'assets/images/wallet_coin_bg_1.png';
  static const String walletCoinBg6 = 'assets/images/wallet_coin_bg6_1.webp';
  static const String searchRankBg = 'assets/images/search_rank_bg.webp';
  
  // ============================================
  // 其他图标
  // ============================================
  static const String noData = 'assets/images/no_data.webp';         // 无数据
  static const String collectStart = 'assets/images/collect_start.webp'; // 收藏星
  static const String icLauncher = 'assets/images/ic_launcher.webp'; // 启动图标
  static const String icUnionPay = 'assets/images/ic_union_pay.webp'; // 银联
  static const String icUsdt = 'assets/images/ic_usdt.webp';         // USDT
  static const String walfareLogo = 'assets/images/walfare_logo.webp'; // 福利Logo
  
  // ============================================
  // 热门标签
  // ============================================
  static const String hot1 = 'assets/images/hot_1.webp';
  static const String hot2 = 'assets/images/hot_2.webp';
  static const String hot3 = 'assets/images/hot_3.webp';
  
  // ============================================
  // 辅助方法
  // ============================================
  
  /// 获取底部导航图标
  /// [index] - tab索引 (0-4)
  /// [isActive] - 是否选中
  static String getNavIcon(int index, bool isActive) {
    switch (index) {
      case 0:
        return isActive ? home01 : home00;
      case 1:
        return isActive ? home11 : home10;
      case 2:
        return isActive ? home21 : home20;
      case 3:
        return isActive ? home31 : home30;
      case 4:
        return isActive ? home41 : home40;
      default:
        return home00;
    }
  }
  
  /// 获取VIP等级图标
  /// [level] - VIP等级 (1-6)
  static String getVipIcon(int level) {
    switch (level) {
      case 1:
        return vipGold;      // 普通VIP
      case 2:
        return vip1;         // VIP 1
      case 3:
        return vip2;         // VIP 2
      case 4:
        return vip3;         // VIP 3
      case 5:
        return superVipBlue; // 黄金至尊
      case 6:
        return superVipRed;  // 紫色限定至尊
      default:
        return vipGold;
    }
  }
  
  /// 获取热门标签图标
  static String getHotIcon(int index) {
    switch (index % 3) {
      case 0:
        return hot1;
      case 1:
        return hot2;
      case 2:
        return hot3;
      default:
        return hot1;
    }
  }
}