/**
 * 格式化工具函数
 */

/**
 * 格式化相对时间
 * @param {string|Date} time - 时间
 * @returns {string} 相对时间字符串
 */
export function formatRelativeTime(time) {
  if (!time) return ''
  
  const date = new Date(time)
  const now = Date.now()
  const diff = (now - date.getTime()) / 1000
  
  if (diff < 0) return '刚刚'
  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + '小时前'
  if (diff < 604800) return Math.floor(diff / 86400) + '天前'
  if (diff < 2592000) return Math.floor(diff / 604800) + '周前'
  if (diff < 31536000) return Math.floor(diff / 2592000) + '个月前'
  return Math.floor(diff / 31536000) + '年前'
}

/**
 * 格式化日期时间
 * @param {string|Date} time - 时间
 * @param {string} format - 格式 'date' | 'datetime' | 'time'
 * @returns {string} 格式化后的时间
 */
export function formatDateTime(time, format = 'datetime') {
  if (!time) return ''
  
  const date = new Date(time)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  
  switch (format) {
    case 'date':
      return `${year}-${month}-${day}`
    case 'time':
      return `${hours}:${minutes}`
    case 'datetime':
    default:
      return `${year}-${month}-${day} ${hours}:${minutes}`
  }
}

/**
 * 格式化视频时长
 * @param {number} seconds - 秒数
 * @returns {string} 格式化后的时长 (HH:MM:SS 或 MM:SS)
 */
export function formatDuration(seconds) {
  if (!seconds || seconds <= 0) return '00:00'
  
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  
  if (h > 0) {
    return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  }
  return `${m}:${String(s).padStart(2, '0')}`
}

/**
 * 格式化数字（带单位）
 * @param {number} num - 数字
 * @returns {string} 格式化后的数字
 */
export function formatNumber(num) {
  if (!num || num <= 0) return '0'
  
  if (num >= 100000000) {
    return (num / 100000000).toFixed(1).replace(/\.0$/, '') + '亿'
  }
  if (num >= 10000) {
    return (num / 10000).toFixed(1).replace(/\.0$/, '') + '万'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1).replace(/\.0$/, '') + 'k'
  }
  return String(num)
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的大小
 */
export function formatFileSize(bytes) {
  if (!bytes || bytes <= 0) return '0 B'
  
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let index = 0
  let size = bytes
  
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024
    index++
  }
  
  return `${size.toFixed(index > 0 ? 1 : 0)} ${units[index]}`
}

/**
 * 格式化金额
 * @param {number} amount - 金额（分）
 * @param {boolean} showSymbol - 是否显示货币符号
 * @returns {string} 格式化后的金额
 */
export function formatMoney(amount, showSymbol = true) {
  const yuan = (amount / 100).toFixed(2)
  return showSymbol ? `¥${yuan}` : yuan
}
