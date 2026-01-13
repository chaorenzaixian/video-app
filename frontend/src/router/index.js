import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { isAdminPath } from '@/constants/routes'

const routes = [
  // 用户端路由 - 使用 webpackPrefetch 预加载常用页面
  {
    path: '/user',
    name: 'UserHome',
    component: () => import(/* webpackPrefetch: true */ '@/views/user/Home/index.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/user/video/:id',
    name: 'VideoPlayer',
    component: () => import(/* webpackPrefetch: true */ '@/views/user/VideoPlayer.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/user/category/:id',
    name: 'Category',
    component: () => import(/* webpackPrefetch: true */ '@/views/user/Category.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/user/vip',
    name: 'UserVip',
    component: () => import(/* webpackPrefetch: true */ '@/views/user/Vip/index.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/user/profile',
    name: 'UserProfile',
    component: () => import(/* webpackPrefetch: true */ '@/views/user/Profile/index.vue'),
    meta: { requiresAuth: false }
  },
  // 用户登录页面已移除，使用自动注册+扫码登录
  // 旧路由重定向到账号找回页面
  {
    path: '/user/login',
    redirect: '/user/settings/recovery'
  },
  // 短视频
  {
    path: '/shorts',
    name: 'ShortVideo',
    component: () => import(/* webpackPrefetch: true */ '@/views/user/ShortVideo/index.vue'),
    meta: { requiresAuth: false, hideNav: true }
  },
  {
    path: '/shorts/:id',
    name: 'ShortVideoDetail',
    component: () => import('@/views/user/ShortVideo/index.vue'),
    meta: { requiresAuth: false, hideNav: true }
  },
  {
    path: '/shorts/upload',
    name: 'ShortVideoUpload',
    component: () => import('@/views/user/ShortVideoUpload.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/user/member/:id',
    name: 'MemberProfile',
    component: () => import('@/views/user/UserProfile.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/user/messages',
    name: 'UserMessages',
    component: () => import('@/views/user/Messages.vue'),
    meta: { requiresAuth: true, hideNav: true }
  },
  {
    path: '/user/chat/:id',
    name: 'PrivateChat',
    component: () => import('@/views/user/Chat.vue'),
    meta: { requiresAuth: true, hideNav: true }
  },
  {
    path: '/user/search',
    name: 'UserSearch',
    component: () => import(/* webpackPrefetch: true */ '@/views/user/Search.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/user/search-result',
    name: 'SearchResult',
    component: () => import('@/views/user/SearchResult.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/user/video-library',
    name: 'VideoLibrary',
    component: () => import('@/views/user/VideoLibrary.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/user/ranking',
    name: 'Ranking',
    component: () => import('@/views/user/Ranking.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/user/history',
    name: 'UserHistory',
    component: () => import('@/views/user/History.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/user/favorites',
    name: 'UserFavorites',
    component: () => import('@/views/user/Favorites.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/user/likes',
    name: 'UserLikes',
    component: () => import('@/views/user/Likes.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/user/account-bind',
    name: 'AccountBind',
    component: () => import('@/views/user/AccountBind.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/user/promotion',
    name: 'Promotion',
    component: () => import('@/views/user/Promotion.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/user/invite-share',
    name: 'InviteShare',
    component: () => import('@/views/user/InviteShare.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/user/downloads',
    name: 'Downloads',
    component: () => import('@/views/user/Downloads.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/user/groups',
    name: 'OfficialGroups',
    component: () => import('@/views/user/OfficialGroups.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/user/customer-service',
    name: 'CustomerService',
    component: () => import('@/views/user/CustomerService.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/user/ios-install',
    name: 'IOSInstall',
    component: () => import('@/views/user/IOSInstall.vue'),
    meta: { requiresAuth: false, hideNav: true }
  },
  {
    path: '/user/redeem',
    name: 'Redeem',
    component: () => import('@/views/user/Redeem.vue'),
    meta: { requiresAuth: true }
  },
  // 社区功能
  {
    path: '/user/community',
    name: 'Community',
    component: () => import('@/views/user/Community/index.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/user/community/publish',
    name: 'CommunityPublish',
    component: () => import('@/views/user/CommunityPublish.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/user/community/post/:id',
    name: 'CommunityDetail',
    component: () => import('@/views/user/CommunityDetail.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/user/community/topic/:id',
    name: 'PostCategory',
    component: () => import('@/views/user/PostCategory.vue'),
    meta: { requiresAuth: false }
  },
  // 图集详情
  {
    path: '/user/gallery/:id',
    name: 'GalleryDetail',
    component: () => import('@/views/user/GalleryDetail.vue'),
    meta: { requiresAuth: false }
  },
  // 小说详情
  {
    path: '/user/novel/:id',
    name: 'NovelDetail',
    component: () => import('@/views/user/NovelDetail.vue'),
    meta: { requiresAuth: false }
  },
  // 有声小说播放器
  {
    path: '/user/audio-novel/:id',
    name: 'AudioNovelPlayer',
    component: () => import('@/views/user/AudioNovelPlayer.vue'),
    meta: { requiresAuth: false, hideNav: true }
  },
  // 交友页面
  {
    path: '/user/dating',
    name: 'Dating',
    component: () => import('@/views/user/Dating.vue'),
    meta: { requiresAuth: true }
  },
  // 暗网入口页面
  {
    path: '/user/darkweb-entry',
    name: 'DarkwebEntry',
    component: () => import('@/views/user/DarkwebEntry.vue'),
    meta: { requiresAuth: true }
  },
  // 暗网视频专区
  {
    path: '/user/darkweb',
    name: 'Darkweb',
    component: () => import('@/views/user/Darkweb.vue'),
    meta: { requiresAuth: true, hideNav: true }
  },
  {
    path: '/user/darkweb/video/:id',
    name: 'DarkwebPlayer',
    component: () => import('@/views/user/DarkwebPlayer.vue'),
    meta: { requiresAuth: true, hideNav: true }
  },
  {
    path: '/user/tasks',
    name: 'Tasks',
    component: () => import('@/views/user/Tasks.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/user/coins',
    name: 'CoinsRecharge',
    component: () => import('@/views/user/CoinsRecharge.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/user/purchases',
    name: 'PurchaseHistory',
    component: () => import('@/views/user/PurchaseHistory.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/creator',
    name: 'CreatorCenter',
    component: () => import('@/views/user/CreatorCenter.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/creator/videos',
    name: 'CreatorVideos',
    component: () => import('@/views/creator/CreatorVideos.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/creator/upload',
    name: 'CreatorUpload',
    component: () => import('@/views/creator/VideoUpload.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/creator/collections',
    name: 'CreatorCollections',
    component: () => import('@/views/creator/Collections.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/creator/earnings',
    name: 'CreatorEarnings',
    component: () => import('@/views/creator/Earnings.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/creator/withdraw',
    name: 'CreatorWithdraw',
    redirect: '/user/withdraw?type=creator',
    meta: { requiresAuth: true }
  },
  {
    path: '/user/earnings',
    name: 'UserEarnings',
    component: () => import('@/views/user/Earnings.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/user/invite-records',
    name: 'InviteRecords',
    component: () => import('@/views/user/InviteRecords.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/user/account-credential',
    name: 'AccountCredential',
    component: () => import('@/views/user/AccountCredential.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/qr-login',
    name: 'QRLogin',
    component: () => import('@/views/user/QRLogin.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/user/agent',
    name: 'Agent',
    component: () => import('@/views/user/Agent.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/user/app-recommend',
    name: 'AppRecommend',
    component: () => import('@/views/user/AppRecommend.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/user/promotion-data',
    name: 'PromotionData',
    component: () => import('@/views/user/PromotionData.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/user/withdraw',
    name: 'Withdraw',
    component: () => import('@/views/user/Withdraw.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/user/withdraw-history',
    name: 'WithdrawHistory',
    component: () => import('@/views/user/WithdrawHistory.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/user/creator-center',
    name: 'UserCreatorCenter',
    component: () => import('@/views/user/CreatorCenter.vue'),
    meta: { requiresAuth: true, hideNav: true }
  },
  {
    path: '/user/earnings-detail',
    name: 'EarningsDetail',
    component: () => import('@/views/user/EarningsDetail.vue'),
    meta: { requiresAuth: true, hideNav: true }
  },
  {
    path: '/user/follows',
    name: 'Follows',
    component: () => import('@/views/user/Follows.vue'),
    meta: { requiresAuth: true, hideNav: true }
  },
  {
    path: '/user/publish/image',
    name: 'PublishImage',
    component: () => import('@/views/user/PublishImage.vue'),
    meta: { requiresAuth: true, hideNav: true }
  },
  {
    path: '/user/publish/video',
    name: 'PublishVideo',
    component: () => import('@/views/user/PublishVideo.vue'),
    meta: { requiresAuth: true, hideNav: true }
  },
  {
    path: '/user/publish/text-image',
    name: 'PublishTextImage',
    component: () => import('@/views/user/PublishTextImage.vue'),
    meta: { requiresAuth: true, hideNav: true }
  },
  // 设置中心相关路由
  {
    path: '/user/settings',
    name: 'UserSettings',
    component: () => import('@/views/user/Settings.vue'),
    meta: { requiresAuth: true, hideNav: true }
  },
  {
    path: '/user/settings/avatar',
    name: 'AvatarSelect',
    component: () => import('@/views/user/AvatarSelect.vue'),
    meta: { requiresAuth: true, hideNav: true }
  },
  {
    path: '/user/settings/nickname',
    name: 'NicknameEdit',
    component: () => import('@/views/user/NicknameEdit.vue'),
    meta: { requiresAuth: true, hideNav: true }
  },
  {
    path: '/user/settings/gender',
    name: 'GenderSelect',
    component: () => import('@/views/user/GenderSelect.vue'),
    meta: { requiresAuth: true, hideNav: true }
  },
  {
    path: '/user/settings/email',
    name: 'EmailBind',
    component: () => import('@/views/user/EmailBind.vue'),
    meta: { requiresAuth: true, hideNav: true }
  },
  {
    path: '/user/settings/recovery',
    name: 'AccountRecovery',
    component: () => import('@/views/user/AccountRecovery.vue'),
    meta: { requiresAuth: true, hideNav: true }
  },
  {
    path: '/user/settings/recovery/email',
    name: 'EmailRecovery',
    component: () => import('@/views/user/EmailRecovery.vue'),
    meta: { requiresAuth: false, hideNav: true }
  },
  {
    path: '/user/settings/recovery/credential',
    name: 'CredentialScan',
    component: () => import('@/views/user/CredentialScan.vue'),
    meta: { requiresAuth: false, hideNav: true }
  },
  {
    path: '/user/settings/faq',
    name: 'FAQ',
    component: () => import('@/views/user/FAQ.vue'),
    meta: { requiresAuth: true, hideNav: true }
  },
  // 根路径重定向到用户首页
  {
    path: '/',
    redirect: '/user'
  },
  // 管理后台登录路由
  {
    path: '/login',
    redirect: '/admin/login'
  },
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    redirect: '/admin/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表盘', icon: 'DataBoard' }
      },
      {
        path: 'videos',
        name: 'Videos',
        component: () => import('@/views/Videos.vue'),
        meta: { title: '视频管理', icon: 'VideoPlay' }
      },
      {
        path: 'videos/upload',
        name: 'VideoUpload',
        component: () => import('@/views/VideoUpload.vue'),
        meta: { title: '上传视频', icon: 'Upload' }
      },
      {
        path: 'videos/batch-upload',
        name: 'BatchUpload',
        component: () => import('@/views/BatchUpload.vue'),
        meta: { title: '批量上传', icon: 'FolderAdd' }
      },
      {
        path: 'short-videos',
        name: 'ShortVideoManage',
        component: () => import('@/views/admin/ShortVideoManage.vue'),
        meta: { title: '短视频管理', icon: 'VideoCamera' }
      },
      {
        path: 'short-categories',
        name: 'ShortCategoryManage',
        component: () => import('@/views/admin/ShortCategoryManage.vue'),
        meta: { title: '短视频分类', icon: 'Grid' }
      },
      {
        path: 'featured',
        name: 'Featured',
        component: () => import('@/views/Featured.vue'),
        meta: { title: '推荐管理', icon: 'Star' }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/Users.vue'),
        meta: { title: '用户管理', icon: 'User' }
      },
      {
        path: 'vip-levels',
        name: 'VipLevels',
        component: () => import('@/views/VipLevels.vue'),
        meta: { title: '会员等级', icon: 'Medal' }
      },
      {
        path: 'orders',
        name: 'Orders',
        component: () => import('@/views/Orders.vue'),
        meta: { title: '订单管理', icon: 'Tickets' }
      },
      {
        path: 'ads',
        name: 'Ads',
        component: () => import('@/views/Ads.vue'),
        meta: { title: '广告管理', icon: 'Picture' }
      },
      {
        path: 'icon-ads',
        name: 'IconAds',
        component: () => import('@/views/IconAds.vue'),
        meta: { title: '图标广告位', icon: 'Grid' }
      },
      {
        path: 'func-entries',
        name: 'FuncEntries',
        component: () => import('@/views/FuncEntries.vue'),
        meta: { title: '功能入口管理', icon: 'Operation' }
      },
      {
        path: 'announcements',
        name: 'Announcements',
        component: () => import('@/views/Announcements.vue'),
        meta: { title: '公告管理', icon: 'Bell' }
      },
      {
        path: 'categories',
        name: 'Categories',
        component: () => import('@/views/Categories.vue'),
        meta: { title: '分类管理', icon: 'Menu' }
      },
      {
        path: 'tags',
        name: 'Tags',
        component: () => import('@/views/Tags.vue'),
        meta: { title: '标签管理', icon: 'PriceTag' }
      },
      {
        path: 'unified-comments',
        name: 'UnifiedComments',
        component: () => import('@/views/admin/UnifiedComments.vue'),
        meta: { title: '评论管理中心', icon: 'ChatDotRound' }
      },
      {
        path: 'comments',
        name: 'Comments',
        redirect: 'unified-comments'
      },
      {
        path: 'comment-announcement',
        name: 'CommentAnnouncement',
        component: () => import('@/views/CommentAnnouncement.vue'),
        meta: { title: '评论公告', icon: 'Notification' }
      },
      {
        path: 'monitor',
        name: 'Monitor',
        component: () => import('@/views/Monitor.vue'),
        meta: { title: '系统监控', icon: 'Monitor' }
      },
      {
        path: 'promotion-dashboard',
        name: 'PromotionDashboard',
        component: () => import('@/views/PromotionDashboard.vue'),
        meta: { title: '推广数据', icon: 'DataLine' }
      },
      {
        path: 'agents',
        name: 'Agents',
        component: () => import('@/views/Agents.vue'),
        meta: { title: '代理管理', icon: 'UserFilled' }
      },
      {
        path: 'withdrawals',
        name: 'Withdrawals',
        component: () => import('@/views/Withdrawals.vue'),
        meta: { title: '提现管理', icon: 'Wallet' }
      },
      {
        path: 'tasks-manage',
        name: 'TasksManage',
        component: () => import('@/views/TasksManage.vue'),
        meta: { title: '任务管理', icon: 'List' }
      },
      {
        path: 'exchange-manage',
        name: 'ExchangeManage',
        component: () => import('@/views/ExchangeManage.vue'),
        meta: { title: '积分兑换管理', icon: 'ShoppingCart' }
      },
      {
        path: 'points-query',
        name: 'PointsQuery',
        component: () => import('@/views/PointsQuery.vue'),
        meta: { title: '用户积分查询', icon: 'Coin' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: '系统设置', icon: 'Setting' }
      },
      {
        path: 'site-settings',
        name: 'SiteSettings',
        component: () => import('@/views/SiteSettings.vue'),
        meta: { title: '网站设置', icon: 'Chrome' }
      },
      {
        path: 'system-config',
        name: 'SystemConfig',
        component: () => import('@/views/SystemConfig.vue'),
        meta: { title: '系统配置', icon: 'Setting' }
      },
      // 5大核心管理页面
      {
        path: 'coins-manage',
        name: 'CoinsManage',
        component: () => import('@/views/admin/CoinsManage.vue'),
        meta: { title: '金币管理', icon: 'Coin' }
      },
      {
        path: 'video-review',
        name: 'VideoReviewManage',
        component: () => import('@/views/admin/VideoReviewManage.vue'),
        meta: { title: '视频审核', icon: 'VideoCamera' }
      },
      {
        path: 'creator-manage',
        name: 'CreatorManage',
        component: () => import('@/views/admin/CreatorManage.vue'),
        meta: { title: '创作者管理', icon: 'Avatar' }
      },
      {
        path: 'withdrawal-manage',
        name: 'WithdrawalManage',
        component: () => import('@/views/admin/WithdrawalManage.vue'),
        meta: { title: '提现审核', icon: 'Wallet' }
      },
      {
        path: 'statistics',
        name: 'StatisticsDashboard',
        component: () => import('@/views/admin/StatisticsDashboard.vue'),
        meta: { title: '数据统计', icon: 'DataAnalysis' }
      },
      // 新增管理页面
      {
        path: 'finance-manage',
        name: 'FinanceManage',
        component: () => import('@/views/admin/FinanceManage.vue'),
        meta: { title: '财务管理', icon: 'Money' }
      },
      {
        path: 'admin-logs',
        name: 'AdminLogs',
        component: () => import('@/views/admin/AdminLogs.vue'),
        meta: { title: '操作日志', icon: 'Document' }
      },
      {
        path: 'banner-manage',
        name: 'BannerManage',
        component: () => import('@/views/admin/BannerManage.vue'),
        meta: { title: '轮播图管理', icon: 'Picture' }
      },
      {
        path: 'batch-video-ops',
        name: 'BatchVideoOps',
        component: () => import('@/views/admin/BatchVideoOps.vue'),
        meta: { title: '视频批量操作', icon: 'Files' }
      },
      {
        path: 'report-manage',
        name: 'ReportManage',
        component: () => import('@/views/admin/ReportManage.vue'),
        meta: { title: '举报管理', icon: 'Warning' }
      },
      {
        path: 'watermark-manage',
        name: 'WatermarkManage',
        component: () => import('@/views/admin/WatermarkManage.vue'),
        meta: { title: '水印管理', icon: 'Stamp' }
      },
      {
        path: 'vip-manage',
        name: 'VipManage',
        component: () => import('@/views/admin/VipManage.vue'),
        meta: { title: 'VIP会员管理', icon: 'Medal' }
      },
      {
        path: 'group-manage',
        name: 'GroupManage',
        component: () => import('@/views/admin/GroupManage.vue'),
        meta: { title: '官方群组管理', icon: 'ChatDotRound' }
      },
      {
        path: 'customer-service-manage',
        name: 'CustomerServiceManage',
        component: () => import('@/views/admin/CustomerServiceManage.vue'),
        meta: { title: '客服管理', icon: 'Service' }
      },
      {
        path: 'customer-service-chat',
        name: 'CustomerServiceChat',
        component: () => import('@/views/admin/CustomerServiceChat.vue'),
        meta: { title: '在线客服', icon: 'ChatDotRound' }
      },
      // 社区管理
      {
        path: 'community-posts',
        name: 'CommunityPosts',
        component: () => import('@/views/admin/CommunityPosts.vue'),
        meta: { title: '帖子管理', icon: 'Document' }
      },
      {
        path: 'community-topics',
        name: 'CommunityTopics',
        component: () => import('@/views/admin/CommunityTopics.vue'),
        meta: { title: '话题管理', icon: 'Collection' }
      },
      {
        path: 'community-comments',
        name: 'CommunityComments',
        redirect: 'unified-comments'
      },
      // 图集小说管理
      {
        path: 'gallery-manage',
        name: 'GalleryManage',
        component: () => import('@/views/admin/GalleryManage.vue'),
        meta: { title: '图集管理', icon: 'Picture' }
      },
      {
        path: 'novel-manage',
        name: 'NovelManage',
        component: () => import('@/views/admin/NovelManage.vue'),
        meta: { title: '小说管理', icon: 'Reading' }
      },
      {
        path: 'novel-statistics',
        name: 'NovelStatistics',
        component: () => import('@/views/admin/NovelStatistics.vue'),
        meta: { title: '阅读统计', icon: 'DataAnalysis' }
      },
      {
        path: 'audio-novel-manage',
        name: 'AudioNovelManage',
        component: () => import('@/views/admin/AudioNovelManage.vue'),
        meta: { title: '有声小说', icon: 'Headset' }
      },
      // 暗网视频管理
      {
        path: 'darkweb-manage',
        name: 'DarkwebManage',
        component: () => import('@/views/admin/DarkwebManage.vue'),
        meta: { title: '暗网视频', icon: 'Lock' }
      },
      // 交友管理
      {
        path: 'dating-manage',
        name: 'DatingManage',
        component: () => import('@/views/admin/DatingManage.vue'),
        meta: { title: '交友管理', icon: 'ChatDotRound' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    // 如果是浏览器后退，恢复位置
    if (savedPosition) {
      return savedPosition
    }
    // 否则滚动到顶部
    return { top: 0, left: 0 }
  }
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  
  // 管理员登录页始终允许访问（不检查登录状态）
  if (to.name === 'AdminLogin') {
    // 如果已登录且是管理员，跳转到后台首页
    if (userStore.isLoggedIn && userStore.user) {
      const role = userStore.user.role
      if (role === 'admin' || role === 'super_admin') {
        next({ name: 'Dashboard' })
        return
      }
    }
    // 否则直接显示登录页（清除可能存在的普通用户token）
    next()
    return
  }
  
  // 检查是否需要管理员权限
  const needsAdmin = isAdminPath(to.path)
  
  // 检查是否已登录
  if (to.meta.requiresAuth !== false && !userStore.isLoggedIn) {
    if (needsAdmin) {
      next({ path: '/admin/login', query: { redirect: to.fullPath } })
    } else {
      // 普通用户页面，等待自动注册完成
      next()
    }
    return
  }
  
  // 如果已登录，确保获取用户信息
  if (userStore.isLoggedIn && !userStore.user) {
    await userStore.fetchUser()
  }
  
  // 如果访问后台管理页面，检查管理员权限
  if (needsAdmin) {
    const role = userStore.user?.role
    if (role !== 'admin' && role !== 'super_admin') {
      next({ name: 'UserHome' })
      return
    }
  }
  
  next()
})

export default router
