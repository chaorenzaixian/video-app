<template>
  <div class="settings-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </div>
      <h1 class="page-title">设置中心</h1>
      <div class="header-right"></div>
    </header>

    <!-- 设置列表 -->
    <div class="settings-card">
      <!-- 头像 -->
      <div class="setting-item" @click="$router.push('/user/settings/avatar')">
        <span class="setting-label">头像</span>
        <div class="setting-value">
          <img :src="avatarUrl" class="avatar-preview" />
          <svg class="arrow-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
          </svg>
        </div>
      </div>

      <!-- 昵称 -->
      <div class="setting-item" @click="$router.push('/user/settings/nickname')">
        <span class="setting-label">昵称</span>
        <div class="setting-value">
          <span class="value-text">{{ user?.nickname || user?.username || '未设置' }}</span>
          <svg class="arrow-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
          </svg>
        </div>
      </div>

      <!-- 性别 -->
      <div class="setting-item" @click="$router.push('/user/settings/gender')">
        <span class="setting-label">性别</span>
        <div class="setting-value">
          <span class="value-text">{{ genderText }}</span>
          <svg class="arrow-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
          </svg>
        </div>
      </div>

      <!-- SOULID -->
      <div class="setting-item" @click="copySoulId">
        <span class="setting-label">SOULID</span>
        <div class="setting-value">
          <span class="value-text">{{ soulId }}</span>
          <svg class="copy-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/>
          </svg>
        </div>
      </div>

      <!-- 邮箱 -->
      <div class="setting-item" @click="$router.push('/user/settings/email')">
        <span class="setting-label">邮箱</span>
        <div class="setting-value">
          <span class="value-text">{{ maskedEmail || '立即绑定' }}</span>
          <svg class="arrow-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
          </svg>
        </div>
      </div>

      <!-- 账号找回 -->
      <div class="setting-item" @click="$router.push('/user/settings/recovery')">
        <span class="setting-label">账号找回</span>
        <div class="setting-value">
          <svg class="arrow-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
          </svg>
        </div>
      </div>

      <!-- 邀请码 -->
      <div class="setting-item" @click="$router.push('/user/promotion')">
        <span class="setting-label">邀请码</span>
        <div class="setting-value">
          <span class="value-text">{{ user?.invite_code || '未设置' }}</span>
          <svg class="arrow-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
          </svg>
        </div>
      </div>

      <!-- 账号凭证 -->
      <div class="setting-item" @click="$router.push('/user/account-credential')">
        <span class="setting-label">账号凭证</span>
        <div class="setting-value">
          <svg class="arrow-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
          </svg>
        </div>
      </div>

      <!-- 常见问题 -->
      <div class="setting-item" @click="$router.push('/user/settings/faq')">
        <span class="setting-label">常见问题</span>
        <div class="setting-value">
          <svg class="arrow-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
          </svg>
        </div>
      </div>

      <!-- 清除缓存 -->
      <div class="setting-item" @click="clearCache">
        <span class="setting-label">清除缓存</span>
        <div class="setting-value">
          <span class="value-text">{{ cacheSize }}</span>
          <svg class="arrow-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
          </svg>
        </div>
      </div>

      <!-- 检查更新 -->
      <div class="setting-item" @click="checkUpdate">
        <span class="setting-label">检查更新</span>
        <div class="setting-value">
          <span class="value-text">V{{ appVersion }}</span>
          <svg class="arrow-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
          </svg>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated } from 'vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const user = computed(() => userStore.user)

// 页面激活时刷新用户数据
onActivated(() => {
  userStore.fetchUser()
})

const appVersion = ref('1.0.4')
const cacheSize = ref('0.0MB')

// 计算SOULID (使用用户ID)
const soulId = computed(() => {
  if (user.value?.id) {
    return String(1528900 + user.value.id)
  }
  return '------'
})

// 性别文本
const genderText = computed(() => {
  const gender = user.value?.gender
  if (gender === 'male') return '男'
  if (gender === 'female') return '女'
  if (gender === 'secret') return '保密'
  return '未设置'
})

// 隐藏部分的邮箱显示
const maskedEmail = computed(() => {
  const email = user.value?.email
  if (!email) return ''
  const atIndex = email.indexOf('@')
  if (atIndex <= 2) return email
  return email.slice(0, 2) + '***' + email.slice(atIndex - 1)
})

// 获取默认头像路径
const getDefaultAvatarPath = (userId) => {
  const totalAvatars = 52 // 17 + 15 + 20
  const index = (userId % totalAvatars)
  
  if (index < 17) {
    return `/images/avatars/icon_avatar_${index + 1}.webp`
  } else if (index < 32) {
    const num = String(index - 17 + 1).padStart(3, '0')
    return `/images/avatars/DM_20251217202131_${num}.JPEG`
  } else {
    const num = String(index - 32 + 1).padStart(3, '0')
    return `/images/avatars/DM_20251217202341_${num}.JPEG`
  }
}

// 头像URL
const avatarUrl = computed(() => {
  const avatar = user.value?.avatar
  if (avatar) {
    if (avatar.startsWith('http')) return avatar
    return avatar.startsWith('/') ? avatar : `/${avatar}`
  }
  const userId = user.value?.id || 1
  return getDefaultAvatarPath(userId)
})

// 复制SOULID
const copySoulId = async () => {
  try {
    await navigator.clipboard.writeText(soulId.value)
    ElMessage.success('SOULID已复制')
  } catch (err) {
    ElMessage.error('复制失败')
  }
}

// 计算缓存大小
const calculateCacheSize = () => {
  // 估算localStorage大小
  let total = 0
  for (let key in localStorage) {
    if (localStorage.hasOwnProperty(key)) {
      total += localStorage[key].length * 2 // UTF-16
    }
  }
  // 估算sessionStorage
  for (let key in sessionStorage) {
    if (sessionStorage.hasOwnProperty(key)) {
      total += sessionStorage[key].length * 2
    }
  }
  // 转换为MB
  const mb = total / (1024 * 1024)
  cacheSize.value = mb.toFixed(1) + 'MB'
}

// 清除缓存
const clearCache = async () => {
  try {
    // 保留token和用户信息
    const token = localStorage.getItem('token')
    const userInfo = localStorage.getItem('user')
    
    // 清除localStorage
    localStorage.clear()
    
    // 恢复必要数据
    if (token) localStorage.setItem('token', token)
    if (userInfo) localStorage.setItem('user', userInfo)
    
    // 清除sessionStorage
    sessionStorage.clear()
    
    // 尝试清除浏览器缓存
    if ('caches' in window) {
      const cacheNames = await caches.keys()
      await Promise.all(cacheNames.map(name => caches.delete(name)))
    }
    
    calculateCacheSize()
    ElMessage.success('缓存已清除')
  } catch (err) {
    ElMessage.error('清除缓存失败')
  }
}

// 检查更新
const checkUpdate = () => {
  ElMessage.info('当前已是最新版本')
}

onMounted(() => {
  calculateCacheSize()
  userStore.fetchUser()
})
</script>

<style lang="scss" scoped>
.settings-page {
  min-height: 100vh;
  background: #0a0a0a;
  color: #fff;
  padding-bottom: env(safe-area-inset-bottom, 20px);
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  padding-top: calc(16px + env(safe-area-inset-top, 0px));
  background: #0a0a0a;
  position: sticky;
  top: 0;
  z-index: 100;
  
  .back-btn {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    
    svg {
      width: 24px;
      height: 24px;
      fill: #fff;
    }
  }
  
  .page-title {
    font-size: 16px;
    font-weight: 600;
    margin: 0;
  }
  
  .header-right {
    width: 32px;
  }
}

.settings-card {
  margin: 12px;
  background: rgba(25, 30, 45, 0.8);
  border-radius: 16px;
  overflow: hidden;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  cursor: pointer;
  transition: background 0.2s;
  
  &:last-child {
    border-bottom: none;
  }
  
  &:active {
    background: rgba(255, 255, 255, 0.05);
  }
  
  .setting-label {
    font-size: 14px;
    color: #fff;
  }
  
  .setting-value {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .value-text {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.5);
    }
    
    .avatar-preview {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      object-fit: cover;
    }
    
    .arrow-icon {
      width: 20px;
      height: 20px;
      fill: rgba(255, 255, 255, 0.3);
    }
    
    .copy-icon {
      width: 18px;
      height: 18px;
      fill: rgba(255, 255, 255, 0.4);
    }
  }
}
</style>



