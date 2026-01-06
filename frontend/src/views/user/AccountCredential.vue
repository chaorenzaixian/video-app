<template>
  <div class="credential-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <button class="back-btn" @click="$router.back()">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
        </svg>
      </button>
      <h1 class="page-title">账号凭证</h1>
      <div class="header-right"></div>
    </div>

    <!-- 凭证卡片 -->
    <div class="credential-card">
      <div class="card-background">
        <img src="/images/backgrounds/girl.webp" alt="background" class="bg-image" />
        <div class="bg-overlay"></div>
      </div>
      
      <div class="card-content">
        <!-- 二维码 -->
        <div class="qr-container">
          <div class="qr-frame" v-if="!loading">
            <img :src="qrCodeUrl" alt="QR Code" class="qr-code" />
            <div class="corner corner-tl"></div>
            <div class="corner corner-tr"></div>
            <div class="corner corner-bl"></div>
            <div class="corner corner-br"></div>
          </div>
          <div class="qr-loading" v-else>
            <span>生成中...</span>
          </div>
        </div>

        <!-- 账号信息 -->
        <div class="account-info">
          <h2 class="info-title">账号凭证</h2>
          <p class="user-id">ID {{ userId }}</p>
          <p class="website">{{ siteName }} 官网地址 {{ siteUrl }}</p>
          <p class="tip">{{ tipText }}</p>
        </div>

        <!-- 令牌状态 -->
        <div class="token-status" v-if="tokenUsed">
          <span class="status-warning">⚠ 当前二维码已被使用</span>
          <button class="refresh-btn" @click="regenerateToken">重新生成</button>
        </div>
      </div>
    </div>

    <!-- 底部按钮 -->
    <div class="action-buttons">
      <button class="save-btn" @click="saveImage">
        <span>保存图片</span>
      </button>
      <button class="refresh-btn-bottom" @click="regenerateToken" :disabled="loading">
        <span>{{ loading ? '生成中...' : '重新生成二维码' }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import api from '@/utils/api'

const userStore = useUserStore()

// 配置信息（从后端获取）
const siteName = ref('Soul成人版')
const siteUrl = ref('https://soul9.fm')
const tipText = ref('提示*扫码可直接登录，仅限一台设备使用')

// 获取配置
const fetchConfig = async () => {
  try {
    const res = await api.get('/config/credential')
    if (res.data) {
      siteName.value = res.data.site_name || siteName.value
      siteUrl.value = res.data.site_url || siteUrl.value
      tipText.value = res.data.tip || tipText.value
    }
  } catch (error) {
    console.error('获取配置失败:', error)
  }
}

// 状态
const loading = ref(false)
const loginToken = ref('')
const tokenUsed = ref(false)

// 用户ID
const userId = computed(() => {
  return userStore.user?.id || '0000000'
})

// 二维码内容 - 包含登录令牌
const qrContent = computed(() => {
  if (loginToken.value) {
    return `${siteUrl.value}/qr-login?token=${loginToken.value}`
  }
  return `${siteUrl.value}?ref=${userId.value}`
})

// 使用在线API生成二维码URL
const qrCodeUrl = computed(() => {
  const content = encodeURIComponent(qrContent.value)
  return `https://api.qrserver.com/v1/create-qr-code/?size=140x140&data=${content}`
})

// 获取或生成登录令牌
const fetchOrGenerateToken = async () => {
  loading.value = true
  try {
    // 先检查是否有未使用的令牌
    const statusRes = await api.get('/auth/qr-token-status')
    if (statusRes.data.has_token) {
      loginToken.value = statusRes.data.token
      tokenUsed.value = false
    } else {
      // 生成新令牌
      const res = await api.post('/auth/generate-qr-token')
      loginToken.value = res.data.token
      tokenUsed.value = false
    }
  } catch (error) {
    console.error('获取登录令牌失败:', error)
  } finally {
    loading.value = false
  }
}

// 重新生成令牌
const regenerateToken = async () => {
  loading.value = true
  try {
    const res = await api.post('/auth/regenerate-qr-token')
    loginToken.value = res.data.token
    tokenUsed.value = false
  } catch (error) {
    console.error('重新生成令牌失败:', error)
  } finally {
    loading.value = false
  }
}

// 保存图片
const saveImage = async () => {
  try {
    alert('请长按页面截图保存')
  } catch (error) {
    console.error('保存失败:', error)
  }
}

onMounted(() => {
  fetchConfig()
  fetchOrGenerateToken()
})
</script>

<style lang="scss" scoped>
.credential-page {
  min-height: 100vh;
  background: #0a0a12;
  display: flex;
  flex-direction: column;
  padding-bottom: env(safe-area-inset-bottom, 20px);
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  padding-top: calc(env(safe-area-inset-top, 20px) + 16px);
  background: transparent;
  
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

.credential-card {
  flex: 1;
  margin: 0 16px;
  border-radius: 20px;
  overflow: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
  
  .card-background {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    align-items: flex-start;
    justify-content: center;
    
    .bg-image {
      width: 100%;
      height: auto;
      max-height: 100%;
      object-fit: contain;
      object-position: top center;
    }
    
    .bg-overlay {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: linear-gradient(
        180deg,
        rgba(10, 10, 18, 0) 0%,
        rgba(10, 10, 18, 0.2) 50%,
        rgba(10, 10, 18, 0.85) 75%,
        rgba(10, 10, 18, 0.98) 100%
      );
    }
  }
  
  .card-content {
    position: relative;
    z-index: 1;
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-end;
    padding: 20px 20px 30px;
  }
}

.qr-container {
  margin-bottom: 20px;
}

.qr-frame {
  position: relative;
  padding: 10px;
  background: #fff;
  border-radius: 10px;
  
  .qr-code {
    display: block;
    width: 140px;
    height: 140px;
  }
  
  .corner {
    position: absolute;
    width: 16px;
    height: 16px;
    border: 2px solid #9c6cff;
    
    &.corner-tl {
      top: -2px;
      left: -2px;
      border-right: none;
      border-bottom: none;
      border-radius: 6px 0 0 0;
    }
    
    &.corner-tr {
      top: -2px;
      right: -2px;
      border-left: none;
      border-bottom: none;
      border-radius: 0 6px 0 0;
    }
    
    &.corner-bl {
      bottom: -2px;
      left: -2px;
      border-right: none;
      border-top: none;
      border-radius: 0 0 0 6px;
    }
    
    &.corner-br {
      bottom: -2px;
      right: -2px;
      border-left: none;
      border-top: none;
      border-radius: 0 0 6px 0;
    }
  }
}

.account-info {
  text-align: center;
  color: #fff;
  
  .info-title {
    font-size: 18px;
    font-weight: 500;
    margin-bottom: 8px;
    letter-spacing: 2px;
  }
  
  .user-id {
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 12px;
    letter-spacing: 3px;
  }
  
  .website {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.8);
    margin-bottom: 10px;
  }
  
  .tip {
    font-size: 12px;
    color: #9c6cff;
  }
}

.qr-loading {
  width: 210px;
  height: 210px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 14px;
}

.token-status {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  
  .status-warning {
    color: #ff9800;
    font-size: 14px;
  }
  
  .refresh-btn {
    padding: 8px 20px;
    background: rgba(156, 108, 255, 0.2);
    border: 1px solid #9c6cff;
    border-radius: 20px;
    color: #9c6cff;
    font-size: 13px;
    cursor: pointer;
  }
}

.action-buttons {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.save-btn {
  padding: 16px;
  background: linear-gradient(135deg, #9c6cff 0%, #6c4fff 100%);
  border: none;
  border-radius: 30px;
  color: #fff;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:active {
    transform: scale(0.98);
    opacity: 0.9;
  }
}

.refresh-btn-bottom {
  padding: 14px;
  background: transparent;
  border: 1px solid rgba(156, 108, 255, 0.5);
  border-radius: 30px;
  color: #9c6cff;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  &:active:not(:disabled) {
    background: rgba(156, 108, 255, 0.1);
  }
}
</style>
