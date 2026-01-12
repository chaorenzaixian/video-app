<template>
  <div class="qr-login-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <button class="back-btn" @click="$router.push('/user')">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
        </svg>
      </button>
      <h1 class="page-title">扫码登录</h1>
      <div class="header-right"></div>
    </div>

    <!-- 登录状态 -->
    <div class="login-content">
      <!-- 加载中 -->
      <div class="status-card" v-if="status === 'loading'">
        <div class="loading-spinner"></div>
        <p class="status-text">正在验证登录信息...</p>
      </div>

      <!-- 登录成功 -->
      <div class="status-card success" v-else-if="status === 'success'">
        <div class="status-icon">✓</div>
        <h2 class="status-title">登录成功</h2>
        <p class="status-text">欢迎回来，{{ username }}</p>
        <p class="status-sub">其他设备已自动登出</p>
        <button class="action-btn" @click="goHome">进入首页</button>
      </div>

      <!-- 登录失败 -->
      <div class="status-card error" v-else-if="status === 'error'">
        <div class="status-icon">✕</div>
        <h2 class="status-title">登录失败</h2>
        <p class="status-text">{{ errorMessage }}</p>
        <button class="action-btn secondary" @click="$router.push('/user/settings/recovery')">
          账号找回
        </button>
      </div>

      <!-- 无效令牌 -->
      <div class="status-card warning" v-else-if="status === 'invalid'">
        <div class="status-icon">!</div>
        <h2 class="status-title">二维码无效</h2>
        <p class="status-text">该二维码已过期或已被使用</p>
        <button class="action-btn secondary" @click="$router.push('/user/settings/recovery')">
          账号找回
        </button>
      </div>

      <!-- 确认登录 -->
      <div class="status-card confirm" v-else-if="status === 'confirm'">
        <div class="status-icon">?</div>
        <h2 class="status-title">确认登录</h2>
        <p class="status-text">您正在使用二维码登录</p>
        <p class="status-sub">登录后，原设备将自动登出</p>
        <div class="device-info" v-if="deviceInfo">
          <span>当前设备：{{ deviceInfo }}</span>
        </div>
        <div class="action-buttons">
          <button class="action-btn" @click="confirmLogin" :disabled="confirming">
            {{ confirming ? '登录中...' : '确认登录' }}
          </button>
          <button class="action-btn secondary" @click="$router.push('/user')">
            取消
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import api from '@/utils/api'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const status = ref('loading') // loading, confirm, success, error, invalid
const errorMessage = ref('')
const username = ref('')
const confirming = ref(false)
const deviceInfo = ref('')

// 获取设备信息
const getDeviceInfo = () => {
  const ua = navigator.userAgent
  if (/iPhone/i.test(ua)) return 'iPhone'
  if (/iPad/i.test(ua)) return 'iPad'
  if (/Android/i.test(ua)) return 'Android'
  if (/Windows/i.test(ua)) return 'Windows PC'
  if (/Mac/i.test(ua)) return 'Mac'
  return 'Unknown Device'
}

// 生成设备指纹
const generateDeviceId = () => {
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  ctx.textBaseline = 'top'
  ctx.font = '14px Arial'
  ctx.fillText('device-fingerprint', 2, 2)
  const canvasData = canvas.toDataURL()
  
  const ua = navigator.userAgent
  const screen = `${window.screen.width}x${window.screen.height}x${window.screen.colorDepth}`
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone
  const lang = navigator.language
  
  const fingerprint = `${ua}-${screen}-${timezone}-${lang}-${canvasData.slice(-50)}`
  
  // 简单hash
  let hash = 0
  for (let i = 0; i < fingerprint.length; i++) {
    const char = fingerprint.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash
  }
  return Math.abs(hash).toString(16).padStart(16, '0')
}

// 确认登录
const confirmLogin = async () => {
  const token = route.query.token
  if (!token) {
    status.value = 'invalid'
    return
  }

  confirming.value = true
  try {
    const deviceId = generateDeviceId()
    const res = await api.post('/auth/qr-login', null, {
      params: {
        token: token,
        device_id: deviceId,
        device_info: deviceInfo.value
      }
    })

    // 保存登录信息
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('refresh_token', res.data.refresh_token)
    
    // 更新用户状态
    await userStore.fetchUser()
    
    username.value = res.data.username || '用户'
    status.value = 'success'
  } catch (error) {
    console.error('登录失败:', error)
    if (error.response?.status === 400) {
      status.value = 'invalid'
      errorMessage.value = error.response?.data?.detail || '该二维码已被使用'
    } else if (error.response?.status === 404) {
      status.value = 'invalid'
      errorMessage.value = '无效的登录二维码'
    } else if (error.response?.status === 429) {
      status.value = 'error'
      errorMessage.value = error.response?.data?.detail || '设备切换过于频繁，请稍后再试'
    } else {
      status.value = 'error'
      errorMessage.value = error.response?.data?.detail || '登录失败，请重试'
    }
  } finally {
    confirming.value = false
  }
}

// 进入首页
const goHome = () => {
  router.push('/user')
}

onMounted(() => {
  const token = route.query.token
  if (!token) {
    status.value = 'invalid'
    return
  }
  
  deviceInfo.value = getDeviceInfo()
  status.value = 'confirm'
})
</script>

<style lang="scss" scoped>
.qr-login-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #1a1a2e 0%, #0a0a12 100%);
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  padding-top: calc(env(safe-area-inset-top, 20px) + 16px);
  
  .back-btn {
    width: 40px;
    height: 40px;
    border: none;
    background: transparent;
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    
    svg {
      width: 24px;
      height: 24px;
    }
  }
  
  .page-title {
    font-size: 18px;
    font-weight: 600;
    color: #fff;
  }
  
  .header-right {
    width: 40px;
  }
}

.login-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.status-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 20px;
  padding: 40px 30px;
  text-align: center;
  max-width: 320px;
  width: 100%;
  
  .status-icon {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 40px;
    margin: 0 auto 24px;
    background: rgba(156, 108, 255, 0.2);
    color: #9c6cff;
  }
  
  &.success .status-icon {
    background: rgba(76, 175, 80, 0.2);
    color: #4caf50;
  }
  
  &.error .status-icon,
  &.warning .status-icon {
    background: rgba(244, 67, 54, 0.2);
    color: #f44336;
  }
  
  &.warning .status-icon {
    background: rgba(255, 152, 0, 0.2);
    color: #ff9800;
  }
  
  .status-title {
    font-size: 22px;
    font-weight: 600;
    color: #fff;
    margin-bottom: 12px;
  }
  
  .status-text {
    font-size: 15px;
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 8px;
  }
  
  .status-sub {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.5);
    margin-bottom: 24px;
  }
  
  .device-info {
    background: rgba(255, 255, 255, 0.05);
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 24px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.6);
  }
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 3px solid rgba(156, 108, 255, 0.2);
  border-top-color: #9c6cff;
  border-radius: 50%;
  margin: 0 auto 24px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-btn {
  width: 100%;
  padding: 14px;
  border: none;
  border-radius: 25px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, #9c6cff 0%, #6c4fff 100%);
  color: #fff;
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  &:active:not(:disabled) {
    transform: scale(0.98);
  }
  
  &.secondary {
    background: transparent;
    border: 1px solid rgba(156, 108, 255, 0.5);
    color: #9c6cff;
  }
}
</style>

