/**
 * 设备指纹生成工具
 * 
 * 基于浏览器特征生成唯一设备ID
 */

// 获取Canvas指纹
function getCanvasFingerprint() {
  try {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    
    // 绘制特定图形
    ctx.textBaseline = 'top'
    ctx.font = '14px Arial'
    ctx.fillStyle = '#f60'
    ctx.fillRect(125, 1, 62, 20)
    ctx.fillStyle = '#069'
    ctx.fillText('Soul App', 2, 15)
    ctx.fillStyle = 'rgba(102, 204, 0, 0.7)'
    ctx.fillText('Soul App', 4, 17)
    
    return canvas.toDataURL()
  } catch (e) {
    return ''
  }
}

// 获取WebGL指纹
function getWebGLFingerprint() {
  try {
    const canvas = document.createElement('canvas')
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl')
    
    if (!gl) return ''
    
    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info')
    if (debugInfo) {
      const vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL)
      const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)
      return `${vendor}~${renderer}`
    }
    
    return gl.getParameter(gl.VERSION)
  } catch (e) {
    return ''
  }
}

// 获取屏幕信息
function getScreenFingerprint() {
  const { width, height, colorDepth, pixelDepth } = window.screen
  const devicePixelRatio = window.devicePixelRatio || 1
  return `${width}x${height}x${colorDepth}x${pixelDepth}x${devicePixelRatio}`
}

// 获取时区
function getTimezone() {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || new Date().getTimezoneOffset()
}

// 获取语言
function getLanguage() {
  return navigator.language || navigator.userLanguage || ''
}

// 获取平台信息
function getPlatform() {
  return navigator.platform || ''
}

// 获取插件信息
function getPlugins() {
  if (!navigator.plugins) return ''
  
  const plugins = []
  for (let i = 0; i < Math.min(navigator.plugins.length, 5); i++) {
    plugins.push(navigator.plugins[i].name)
  }
  return plugins.join(',')
}

// 简单哈希函数
function simpleHash(str) {
  let hash = 0
  if (str.length === 0) return hash.toString(16)
  
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash // Convert to 32bit integer
  }
  
  // 转换为正数的16进制
  return Math.abs(hash).toString(16)
}

// 生成设备指纹
export function generateDeviceId() {
  // 先检查本地是否已有设备ID
  const existingId = localStorage.getItem('device_id')
  if (existingId) {
    return existingId
  }
  
  // 收集设备特征
  const components = [
    getCanvasFingerprint(),
    getWebGLFingerprint(),
    getScreenFingerprint(),
    getTimezone(),
    getLanguage(),
    getPlatform(),
    getPlugins(),
    navigator.userAgent,
    navigator.hardwareConcurrency || '',
    navigator.maxTouchPoints || ''
  ]
  
  // 合并特征生成哈希
  const fingerprint = components.join('|||')
  const hash1 = simpleHash(fingerprint)
  const hash2 = simpleHash(fingerprint.split('').reverse().join(''))
  
  // 添加随机部分确保唯一性
  const randomPart = Math.random().toString(36).substring(2, 10)
  const timestamp = Date.now().toString(36)
  
  const deviceId = `${hash1}${hash2}${randomPart}${timestamp}`.substring(0, 64)
  
  // 保存到本地
  localStorage.setItem('device_id', deviceId)
  
  return deviceId
}

// 获取已存储的设备ID
export function getStoredDeviceId() {
  return localStorage.getItem('device_id')
}

// 清除设备ID（用于调试）
export function clearDeviceId() {
  localStorage.removeItem('device_id')
}

export default {
  generateDeviceId,
  getStoredDeviceId,
  clearDeviceId
}






