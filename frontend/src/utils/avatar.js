/**
 * 头像URL处理工具
 */

/**
 * 获取头像URL
 * @param {string} avatar - 用户头像路径
 * @param {number|string} userId - 用户ID（用于生成默认头像）
 * @returns {string} 完整的头像URL
 */
export function getAvatarUrl(avatar, userId) {
  if (avatar) {
    return avatar.startsWith('/') ? avatar : '/' + avatar
  }
  
  // 根据用户ID生成默认头像
  const index = (parseInt(userId) || 1) % 52
  
  if (index < 17) {
    return `/images/avatars/icon_avatar_${index + 1}.webp`
  } else if (index < 32) {
    return `/images/avatars/DM_20251217202131_${String(index - 17 + 1).padStart(3, '0')}.JPEG`
  } else {
    return `/images/avatars/DM_20251217202341_${String(index - 32 + 1).padStart(3, '0')}.JPEG`
  }
}

/**
 * 获取VIP等级图标
 * @param {number} level - VIP等级
 * @returns {string} VIP图标路径
 */
export function getVipIcon(level) {
  const icons = {
    1: '/images/vip/vip1.webp',
    2: '/images/vip/vip2.webp',
    3: '/images/vip/vip3.webp',
    4: '/images/vip/vip4.webp',
    5: '/images/vip/vip5.webp',
    6: '/images/vip/vip6.webp',
  }
  return icons[level] || ''
}

/**
 * 获取默认封面图
 * @param {string} coverUrl - 封面URL
 * @returns {string} 封面URL或默认图
 */
export function getCoverUrl(coverUrl) {
  if (!coverUrl) return '/placeholder.webp'
  return coverUrl.startsWith('http') || coverUrl.startsWith('/') 
    ? coverUrl 
    : '/' + coverUrl
}
