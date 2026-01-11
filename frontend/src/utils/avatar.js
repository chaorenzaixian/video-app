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
  const id = parseInt(userId)
  // 如果userId无效（NaN、空字符串等），使用第一个默认头像
  const validId = isNaN(id) || id <= 0 ? 1 : id
  const index = validId % totalAvatars
  
  if (index < 17) {
    // icon_avatar_1.webp 到 icon_avatar_17.webp
    return `/images/avatars/icon_avatar_${index + 1}.webp`
  } else if (index < 32) {
    // DM_20251217202131_001.JPEG 到 DM_20251217202131_015.JPEG
    const num = String(index - 17 + 1).padStart(3, '0')
    return `/images/avatars/DM_20251217202131_${num}.JPEG`
  } else {
    // DM_20251217202341_001 到 DM_20251217202341_020，扩展名不一致
    const num = String(index - 32 + 1).padStart(3, '0')
    // 某些文件是.webp，某些是.JPEG，需要根据实际文件判断
    const webpFiles = ['002', '006', '015', '018']
    const ext = webpFiles.includes(num) ? 'webp' : 'JPEG'
    return `/images/avatars/DM_20251217202341_${num}.${ext}`
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
  // 检查avatar是否有有效值（非空字符串）
  if (avatar && avatar.trim() !== '') {
    // 处理相对路径
    if (avatar.startsWith('/') || avatar.startsWith('http')) {
      return avatar
    }
    return '/' + avatar
  }
  return getDefaultAvatarPath(userId)
}
