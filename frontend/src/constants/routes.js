/**
 * 路由常量配置
 */

// 需要管理员权限的路径
export const ADMIN_PATHS = [
  '/admin/dashboard',
  '/admin/videos',
  '/admin/users',
  '/admin/vip-manage',
  '/admin/vip-levels',
  '/admin/categories',
  '/admin/tags',
  '/admin/orders',
  '/admin/ads',
  '/admin/settings',
  '/admin/featured',
  '/admin/comments',
  '/admin/unified-comments',
  '/admin/coins-manage',
  '/admin/video-review',
  '/admin/creator-manage',
  '/admin/withdrawal-manage',
  '/admin/statistics',
  '/admin/finance-manage',
  '/admin/admin-logs',
  '/admin/banner-manage',
  '/admin/batch-video-ops',
  '/admin/report-manage',
  '/admin/watermark-manage',
  '/admin/announcements',
  '/admin/icon-ads',
  '/admin/func-entries',
  '/admin/monitor',
  '/admin/promotion-dashboard',
  '/admin/agents',
  '/admin/withdrawals',
  '/admin/tasks-manage',
  '/admin/exchange-manage',
  '/admin/points-query',
  '/admin/site-settings',
  '/admin/system-config',
  '/admin/comment-announcement',
  '/admin/group-manage',
  '/admin/customer-service-manage',
  '/admin/customer-service-chat',
  '/admin/community-posts',
  '/admin/community-topics',
  '/admin/community-comments',
  '/admin/gallery-manage',
  '/admin/novel-manage',
  '/admin/short-videos',
  '/admin/short-categories',
  '/admin/darkweb-manage',
  '/admin/dating-manage',
  '/admin/audio-novel-manage',
  '/admin/novel-statistics'
]

/**
 * 检查路径是否需要管理员权限
 */
export function isAdminPath(path) {
  return path.startsWith('/admin') && path !== '/admin/login'
}

/**
 * 检查路径是否需要登录
 */
export function requiresAuth(path) {
  const publicPaths = [
    '/user',
    '/user/video/',
    '/user/category/',
    '/user/search',
    '/user/community',
    '/shorts',
    '/qr-login'
  ]
  
  return !publicPaths.some(p => path === p || path.startsWith(p))
}
