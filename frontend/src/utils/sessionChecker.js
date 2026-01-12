/**
 * Session 检测服务
 * 定期检查当前会话是否有效，如果在其他设备登录则自动登出
 */
import api from './api'
import { ElMessageBox } from 'element-plus'
import router from '@/router'

let checkInterval = null
let isChecking = false

// 检测间隔（毫秒）
const CHECK_INTERVAL = 30000 // 30秒检测一次

/**
 * 检查会话是否有效
 */
export const checkSession = async () => {
  if (isChecking) return
  
  const token = localStorage.getItem('token')
  if (!token) return
  
  isChecking = true
  try {
    const res = await api.get('/auth/check-session')
    
    if (!res.data.valid && res.data.reason === 'session_expired') {
      // 会话失效，强制登出
      stopSessionChecker()
      
      // 清除登录信息
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
      
      // 显示提示
      try {
        await ElMessageBox.alert(
          res.data.message || '您的账号已在其他设备登录，当前设备已自动登出',
          '账号已在其他设备登录',
          {
            confirmButtonText: '重新登录',
            type: 'warning',
            showClose: false,
            closeOnClickModal: false,
            closeOnPressEscape: false
          }
        )
      } catch (e) {
        // 用户关闭弹窗
      }
      
      // 跳转到账号找回页面
      router.push('/user/settings/recovery')
    }
  } catch (error) {
    // 401 错误会被拦截器处理
    if (error.response?.status !== 401) {
      console.error('Session check failed:', error)
    }
  } finally {
    isChecking = false
  }
}

/**
 * 启动会话检测
 */
export const startSessionChecker = () => {
  if (checkInterval) return
  
  // 立即检测一次
  checkSession()
  
  // 定期检测
  checkInterval = setInterval(checkSession, CHECK_INTERVAL)
  
  // 页面可见时检测
  document.addEventListener('visibilitychange', handleVisibilityChange)
  
  console.log('[SessionChecker] Started')
}

/**
 * 停止会话检测
 */
export const stopSessionChecker = () => {
  if (checkInterval) {
    clearInterval(checkInterval)
    checkInterval = null
  }
  
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  
  console.log('[SessionChecker] Stopped')
}

/**
 * 页面可见性变化处理
 */
const handleVisibilityChange = () => {
  if (document.visibilityState === 'visible') {
    // 页面变为可见时立即检测
    checkSession()
  }
}

export default {
  start: startSessionChecker,
  stop: stopSessionChecker,
  check: checkSession
}

