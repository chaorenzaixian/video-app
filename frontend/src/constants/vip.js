/**
 * VIP相关常量
 * 统一管理VIP等级图标、名称等配置
 */

// VIP等级图标映射
export const VIP_LEVEL_ICONS = {
  1: '/images/backgrounds/vip_gold.webp',      // 普通VIP
  2: '/images/backgrounds/vip_1.webp',         // VIP1
  3: '/images/backgrounds/vip_2.webp',         // VIP2
  4: '/images/backgrounds/vip_3.webp',         // VIP3
  5: '/images/backgrounds/super_vip_red.webp', // 黄金至尊
  6: '/images/backgrounds/super_vip_blue.webp' // 钻石至尊
}

// VIP等级名称映射
export const VIP_LEVEL_NAMES = {
  0: '非VIP',
  1: '普通VIP',
  2: 'VIP1',
  3: 'VIP2',
  4: 'VIP3',
  5: '黄金至尊',
  6: '钻石至尊'
}

// VIP等级颜色映射
export const VIP_LEVEL_COLORS = {
  1: '#ffd700',
  2: '#ff9500',
  3: '#ff6b00',
  4: '#ff4500',
  5: '#ff0000',
  6: '#8b5cf6'
}

// VIP等级权益描述
export const VIP_LEVEL_BENEFITS = {
  1: 'VIP视频免费',
  2: 'VIP+金币视频',
  3: '全部永久免费',
  4: '尊享全部特权',
  5: '帝王级体验',
  6: '至尊级体验',
  7: '限定尊享体验'
}

/**
 * 获取VIP等级图标
 * @param {number} level - VIP等级
 * @returns {string} 图标URL
 */
export const getVipLevelIcon = (level) => {
  return VIP_LEVEL_ICONS[level] || ''
}

/**
 * 获取VIP等级名称
 * @param {number} level - VIP等级
 * @returns {string} 等级名称
 */
export const getVipLevelName = (level) => {
  return VIP_LEVEL_NAMES[level] || '非VIP'
}

/**
 * 获取VIP等级颜色
 * @param {number} level - VIP等级
 * @returns {string} 颜色值
 */
export const getVipLevelColor = (level) => {
  return VIP_LEVEL_COLORS[level] || '#999'
}

/**
 * 检查是否是VIP
 * @param {object} user - 用户对象
 * @returns {boolean}
 */
export const isUserVip = (user) => {
  if (!user) return false
  return user.is_vip === true || (user.vip_level && user.vip_level > 0)
}

export default {
  VIP_LEVEL_ICONS,
  VIP_LEVEL_NAMES,
  VIP_LEVEL_COLORS,
  VIP_LEVEL_BENEFITS,
  getVipLevelIcon,
  getVipLevelName,
  getVipLevelColor,
  isUserVip
}
