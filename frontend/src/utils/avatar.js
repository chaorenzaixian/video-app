/**
 * 头像工具函数
 * 统一管理默认头像分配逻辑
 */

/**
 * 根据用户ID获取默认头像路径
 * 共52个预设头像，根据用户ID取模分配
 * @param {number|string} userId - 用户ID
 * @returns {string} 头像路径
 */
export const getDefaultAvatarPath = (userId) => {
  const totalAvatars = 52
  const index = ((parseInt(userId) || 1) % totalAvatars)
  
  if (index < 17) {
    return `/images/avatars/icon_avatar_${index + 1}.png`
  } else if (index < 32) {
    const num = String(index - 17 + 1).padStart(3, '0')
    return `/images/avatars/DM_20251217202131_${num}.JPEG`
  } else {
    const num = String(index - 32 + 1).padStart(3, '0')
    return `/images/avatars/DM_20251217202341_${num}.JPEG`
  }
}

/**
 * 获取用户头像URL
 * 优先使用自定义头像，否则根据用户ID分配默认头像
 * @param {string|null} avatar - 用户自定义头像URL
 * @param {number|string} userId - 用户ID
 * @returns {string} 头像URL
 */
export const getAvatarUrl = (avatar, userId) => {
  if (avatar) {
    // 处理相对路径
    if (avatar.startsWith('/') || avatar.startsWith('http')) {
      return avatar
    }
    return '/' + avatar
  }
  return getDefaultAvatarPath(userId)
}
