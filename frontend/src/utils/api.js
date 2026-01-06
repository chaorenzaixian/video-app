import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 检测运行环境，返回对应的 API 地址
const getBaseURL = () => {
  const hostname = window.location.hostname
  const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1'
  const isProduction = hostname === 'ssoul.cc' || hostname === 'www.ssoul.cc'
  
  if (isProduction) {
    // 生产环境：使用 Nginx 反向代理
    return '/api/v1'
  }
  
  if (!isLocalhost) {
    // 开发环境 IP 访问（手机 WebView 调试）
    return `http://${hostname}:8001/api/v1`
  }
  
  // 本地开发使用 vite 代理
  return '/api/v1'
}

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
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response
  },
  error => {
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
        case 500:
          ElMessage.error('服务器错误，请稍后重试')
          break
        case 400:
          // 400错误由调用方自行处理，不在这里显示
          break
        default:
          ElMessage.error(response.data?.detail || '请求失败')
      }
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }
    
    return Promise.reject(error)
  }
)

export default api








