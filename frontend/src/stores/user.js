import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/api'
import { generateDeviceId } from '@/utils/fingerprint'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || '')
  const isInitialized = ref(false)
  
  // 防止重复fetchUser的锁
  let fetchUserPromise = null
  
  const isLoggedIn = computed(() => !!token.value)
  const isGuest = computed(() => user.value?.is_guest === true)
  const isAdmin = computed(() => user.value?.role === 'admin' || user.value?.role === 'super_admin')
  const isVip = computed(() => user.value?.is_vip === true)
  
  // 自动注册/登录（带重试机制）
  async function autoRegisterGuest(retryCount = 0) {
    const MAX_RETRIES = 3
    const RETRY_DELAYS = [1000, 2000, 4000] // 指数退避：1s, 2s, 4s
    
    // 如果已登录，直接返回
    if (token.value) {
      isInitialized.value = true
      await fetchUser()
      return
    }
    
    try {
      const deviceId = generateDeviceId()
      const res = await api.post('/auth/guest/register', { device_id: deviceId })
      
      token.value = res.data.access_token
      localStorage.setItem('token', res.data.access_token)
      localStorage.setItem('refreshToken', res.data.refresh_token)
      
      await fetchUser()
      console.log('自动注册成功')
    } catch (error) {
      console.error(`注册失败 (尝试 ${retryCount + 1}/${MAX_RETRIES + 1}):`, error)
      
      // 如果是429（频率限制）或5xx错误，且未超过重试次数，则重试
      const status = error.response?.status
      const shouldRetry = (status === 429 || status >= 500) && retryCount < MAX_RETRIES
      
      if (shouldRetry) {
        const delay = RETRY_DELAYS[retryCount] || 4000
        console.log(`${delay/1000}秒后重试...`)
        await new Promise(resolve => setTimeout(resolve, delay))
        return autoRegisterGuest(retryCount + 1)
      }
    } finally {
      isInitialized.value = true
    }
  }
  
  // 正式登录（用户名密码）
  async function login(credentials) {
    const res = await api.post('/auth/login', credentials)
    token.value = res.data.access_token
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('refreshToken', res.data.refresh_token)
    await fetchUser()
    return res.data
  }
  
  // 升级游客账号
  async function upgradeAccount(data) {
    const res = await api.post('/auth/upgrade', data)
    user.value = res.data
    return res.data
  }
  
  // 绑定手机号
  async function bindPhone(phone, code) {
    const res = await api.post('/auth/bind/phone', { phone, code })
    if (user.value) {
      user.value.phone = phone
    }
    return res.data
  }
  
  // 绑定邮箱
  async function bindEmail(email, code) {
    const res = await api.post('/auth/bind/email', { email, code })
    if (user.value) {
      user.value.email = email
    }
    return res.data
  }
  
  async function fetchUser() {
    if (!token.value) return
    
    // 如果已经有正在进行的fetchUser请求，等待它完成
    if (fetchUserPromise) {
      return fetchUserPromise
    }
    
    fetchUserPromise = (async () => {
      try {
        const res = await api.get('/users/me')
        user.value = res.data
      } catch (error) {
        logout()
      } finally {
        fetchUserPromise = null
      }
    })()
    
    return fetchUserPromise
  }
  
  function logout() {
    user.value = null
    token.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
    // 不清除device_id，保留设备识别
  }
  
  async function refreshToken() {
    const refreshTokenValue = localStorage.getItem('refreshToken')
    if (!refreshTokenValue) {
      logout()
      return
    }
    
    try {
      const res = await api.post('/auth/refresh', { refresh_token: refreshTokenValue })
      token.value = res.data.access_token
      localStorage.setItem('token', res.data.access_token)
      localStorage.setItem('refreshToken', res.data.refresh_token)
    } catch (error) {
      logout()
    }
  }
  
  return {
    user,
    token,
    isLoggedIn,
    isGuest,
    isAdmin,
    isVip,
    isInitialized,
    autoRegisterGuest,
    login,
    logout,
    fetchUser,
    refreshToken,
    upgradeAccount,
    bindPhone,
    bindEmail
  }
})




