/// 资源文件路径管理
class AppAssets {
  // 底部导航图标
  static const String home00 = 'assets/images/home_0_0.webp';
  static const String home01 = 'assets/images/home_0_1.webp';
  static const String home10 = 'assets/images/home_1_0.webp';
  static const String home11 = 'assets/images/home_1_1.webp';
  static const String home20 = 'assets/images/home_2_0.webp';
  static const String home21 = 'assets/images/home_2_1.webp';
  static const String home30 = 'assets/images/home_3_0.webp';
  static const String home31 = 'assets/images/home_3_1.webp';
  static const String home40 = 'assets/images/home_4_0.webp';
  static const String home41 = 'assets/images/home_4_1.webp';
  
  // 顶部栏图标
  static const String fuli = 'assets/images/fuli.webp';
  static const String soulTitle = 'assets/images/soul_title.webp';
  static const String icSearch = 'assets/images/ic_search.webp';
  static const String shortLogo = 'assets/images/short_logo.webp';
  
  // 个人中心图标
  static const String mineNotification = 'assets/images/mine_notification.webp';
  static const String icService = 'assets/images/ic_service.webp';
  static const String icSetting = 'assets/images/ic_setting.webp';
  static const String icSign = 'assets/images/ic_sign.webp';
  static const String icHistory = 'assets/images/ic_history.webp';
  static const String icCollect = 'assets/images/ic_collect.webp';
  static const String icBuy = 'assets/images/ic_buy.webp';
  static const String icAi = 'assets/images/ic_ai.webp';
  static const String icCoin = 'assets/images/ic_coin.webp';
  static const String icGift = 'assets/images/ic_gift.webp';
  
  // VIP相关
  static const String vipGold = 'assets/images/vip_gold.webp';
  static const String vip1 = 'assets/images/vip_1.webp';
  static const String vip2 = 'assets/images/vip_2.webp';
  static const String vip3 = 'assets/images/vip_3.webp';
  static const String vipCenter = 'assets/images/vip_center.webp';
  static const String superVipBlue = 'assets/images/super_vip_blue.webp';
  static const String superVipRed = 'assets/images/super_vip_red.webp';
  static const String vipRecommend = 'assets/images/vip_recommend.webp';
  static const String vipRecommendHeader = 'assets/images/vip_recommend_header.webp';
  static const String imgCrown = 'assets/images/img_crown.webp';
  
  // 钱包相关
  static const String myWallet = 'assets/images/my_wallet.webp';
  static const String agent = 'assets/images/agent.webp';
  static const String proxyBanner = 'assets/images/proxy_banner.webp';
  static const String withdrawNow = 'assets/images/withdraw_now.webp';
  
  // 发布相关
  static const String publishVideo = 'assets/images/publish_video.webp';
  static const String publishImg = 'assets/images/publish_img_1.webp';
  static const String publishImgText = 'assets/images/publish_img_text.webp';
  static const String publish = 'assets/images/publish.webp';
  
  // 背景图片
  static const String girl = 'assets/images/girl.webp';
  static const String girl2 = 'assets/images/girl2.webp';
  static const String welfareVipBg = 'assets/images/welfare_vip_background.webp';
  static const String walletCoinBg = 'assets/images/wallet_coin_bg_1.webp';
  static const String walletCoinBg6 = 'assets/images/wallet_coin_bg6_1.webp';
  static const String searchRankBg = 'assets/images/search_rank_bg.webp';
  
  // 其他图标
  static const String noData = 'assets/images/no_data.webp';
  static const String collectStart = 'assets/images/collect_start.webp';
  static const String icLauncher = 'assets/images/ic_launcher.webp';
  static const String icUnionPay = 'assets/images/ic_union_pay.webp';
  static const String icUsdt = 'assets/images/ic_usdt.webp';
  static const String walfareLogo = 'assets/images/walfare_logo.webp';
  
  // 热门标签
  static const String hot1 = 'assets/images/hot_1.webp';
  static const String hot2 = 'assets/images/hot_2.webp';
  static const String hot3 = 'assets/images/hot_3.webp';
  
  /// 获取底部导航图标
  static String getNavIcon(int index, bool isActive) {
    switch (index) {
      case 0: return isActive ? home01 : home00;
      case 1: return isActive ? home11 : home10;
      case 2: return isActive ? home21 : home20;
      case 3: return isActive ? home31 : home30;
      case 4: return isActive ? home41 : home40;
      default: return home00;
    }
  }
  
  /// 获取VIP等级图标
  static String getVipIcon(int level) {
    switch (level) {
      case 1: return vipGold;
      case 2: return vip1;
      case 3: return vip2;
      case 4: return vip3;
      case 5: return superVipBlue;
      case 6: return superVipRed;
      default: return vipGold;
    }
  }
  
  /// 获取热门标签图标
  static String getHotIcon(int index) {
    switch (index % 3) {
      case 0: return hot1;
      case 1: return hot2;
      case 2: return hot3;
      default: return hot1;
    }
  }
}
