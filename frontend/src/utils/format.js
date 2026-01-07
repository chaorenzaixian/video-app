/**
 * 统一的格式化工具函数
 * 解决多个组件中重复定义格式化函数的问题
 */

import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

/**
 * 格式化相对时间（如：刚刚、5分钟前、2小时前）
 */
export const formatRelativeTime = (time) => {
  if (!time) return ''
  return dayjs(time).fromNow()
}

/**
 * 格式化日期（如：2024.01.15）
 */
export const formatDate = (time) => {
  if (!time) return ''
  const d = new Date(time)
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`
}

/**
 * 格式化日期时间（如：2024-01-15 14:30）
 */
export const formatDateTime = (time) => {
  if (!time) return ''
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

/**
 * 格式化评论时间（智能显示）
 */
export const formatCommentTime = (time) => {
  if (!time) return ''
  const d = new Date(time)
  const now = new Date()
  const diff = (now - d) / 1000

  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + '小时前'
  if (diff < 2592000) return Math.floor(diff / 86400) + '天前'

  return `${d.getMonth() + 1}/${d.getDate()}`
}

/**
 * 格式化数量（如：1.2W、3.5K）
 */
export const formatCount = (count) => {
  if (!count) return '0'
  if (count >= 10000) return (count / 10000).toFixed(1) + 'W'
  if (count >= 1000) return (count / 1000).toFixed(1) + 'K'
  return String(count)
}

/**
 * 格式化播放量（带单位）
 */
export const formatViewCount = (count) => {
  if (!count) return '0'
  if (count >= 10000) {
    return (count / 10000).toFixed(1) + 'W'
  }
  return count.toString()
}

/**
 * 格式化视频时长（秒 -> 分:秒）
 */
export const formatDuration = (seconds) => {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

/**
 * 格式化文件大小
 */
export const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024
    i++
  }
  return `${bytes.toFixed(1)} ${units[i]}`
}

/**
 * 格式化试看时间
 */
export const formatTrialTime = (seconds) => {
  if (!seconds) return '0秒'
  if (seconds < 60) return `${seconds}秒`
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return s > 0 ? `${m}分${s}秒` : `${m}分钟`
}

export default {
  formatRelativeTime,
  formatDate,
  formatDateTime,
  formatCommentTime,
  formatCount,
  formatViewCount,
  formatDuration,
  formatFileSize,
  formatTrialTime
}
