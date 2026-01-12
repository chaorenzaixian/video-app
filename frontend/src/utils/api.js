import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 检测运行环境，返回对应的 API 地址
const getBaseURL = () => {
  // 优先使用环境变量
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  
  const hostname = window.location.hostname
  const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1'
  
  if (!isLocalhost) {
    // 生产环境或远程访问：使用 Nginx 反向代理
    return '/api/v1'
  }
  
  // 本地开发使用 vite 代理
  return '/api/v1'
}

// 请求去重管理
const pendingRequests = new Map()

const api = axios.create({
  baseURL: getBaseURL(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // 请求去重（仅对GET请求和非文件上传请求）
    if (config.method === 'get' || (config.method === 'post' && !config.headers['Content-Type']?.includes('multipart'))) {
      const key = `${config.method}:${config.url}:${JSON.stringify(config.params || {})}`
      
      // 如果有相同请求正在进行，取消当前请求
      if (pendingRequests.has(key)) {
        const controller = pendingRequests.get(key)
        controller.abort()
      }
      
      // 创建新的AbortController
      const controller = new AbortController()
      pendingRequests.set(key, controller)
      config.signal = controller.signal
      config._requestKey = key
    }
    
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    // 请求完成，移除pending
    if (response.config._requestKey) {
      pendingRequests.delete(response.config._requestKey)
    }
    return response
  },
  error => {
    // 请求完成，移除pending
    if (error.config?._requestKey) {
      pendingRequests.delete(error.config._requestKey)
    }
    
    // 如果是取消的请求，不显示错误
    if (axios.isCancel(error) || error.name === 'CanceledError') {
      return Promise.reject(error)
    }
    
    const { response } = error
    
    if (response) {
      switch (response.status) {
        case 401:
          localStorage.removeItem('token')
          localStorage.removeItem('refreshToken')
          // 根据当前页面判断跳转到用户端还是管理端登录页
          const isUserPage = window.location.pathname.startsWith('/user') || 
                             window.location.pathname.startsWith('/shorts')
          if (isUserPage) {
            // 用户端不跳转到登录页，让游客自动注册机制处理
            console.log('用户端401错误，等待游客自动注册')
          } else {
            router.push('/login')
            ElMessage.error('登录已过期，请重新登录')
          }
          break
        case 403:
          ElMessage.error('没有权限执行此操作')
          break
        case 404:
          // 404错误由调用方自行处理，不在这里显示全局提示
          break
        case 422:
          const detail = response.data?.detail
          if (Array.isArray(detail)) {
            ElMessage.error(detail[0]?.msg || '请求参数错误')
          } else {
            ElMessage.error(detail || '请求参数错误')
          }
          break
        case 429:
          ElMessage.warning('请求过于频繁，请稍后再试')
          break
        case 500:
          ElMessage.error('服务器错误，请稍后重试')
          break
        case 400:
          // 400错误由调用方自行处理，不在这里显示
          break
        default:
          ElMessage.error(response.data?.detail || '请求失败')
      }
    } else if (error.message !== 'canceled') {
      ElMessage.error('网络错误，请检查网络连接')
    }
    
    return Promise.reject(error)
  }
)

export default api








