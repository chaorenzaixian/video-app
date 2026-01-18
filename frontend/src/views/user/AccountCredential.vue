<template>
  <div class="credential-page">
    <!-- 全屏背景图 -->
    <div class="page-bg">
      <img src="/images/backgrounds/girl.webp" alt="background" />
    </div>
    
    <!-- 顶部导航 -->
    <div class="page-header">
      <button class="back-btn" @click="$router.back()">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </button>
      <h1 class="page-title">账号凭证</h1>
      <div class="header-right"></div>
    </div>

    <!-- 内容区域 -->
    <div class="content-area">
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
const siteUrl = ref('')
const tipText = ref('提示*扫码可直接登录，仅限一台设备使用')

// 获取配置
const fetchConfig = async () => {
  try {
    const res = await api.get('/config/credential')
    if (res.data) {
      siteName.value = res.data.site_name || siteName.value
      siteUrl.value = res.data.site_url || window.location.origin
      tipText.value = res.data.tip || tipText.value
    }
  } catch (error) {
    console.error('获取配置失败:', error)
    siteUrl.value = window.location.origin
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
    const statusRes = await api.get('/auth/qr-token-status')
    if (statusRes.data.has_token) {
      loginToken.value = statusRes.data.token
      tokenUsed.value = false
    } else {
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
  display: flex;
  flex-direction: column;
  position: relative;
  color: #fff;
}

// 全屏背景图
.page-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: top center;
  }
  
  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
      180deg,
      rgba(10, 10, 18, 0.3) 0%,
      rgba(10, 10, 18, 0.1) 30%,
      rgba(10, 10, 18, 0.1) 50%,
      rgba(10, 10, 18, 0.6) 80%,
      rgba(10, 10, 18, 0.9) 100%
    );
  }
}

.page-header {
  position: relative;
  z-index: 1;
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

// 内容区域
.content-area {
  position: relative;
  z-index: 1;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  padding: 20px;
  padding-bottom: 30px;
}

.qr-container {
  margin-bottom: 24px;
}

.qr-frame {
  position: relative;
  padding: 10px;
  background: #fff;
  border-radius: 10px;
  
  .qr-code {
    display: block;
    width: 160px;
    height: 160px;
  }
  
  .corner {
    position: absolute;
    width: 18px;
    height: 18px;
    border: 3px solid #9c6cff;
    
    &.corner-tl {
      top: -3px;
      left: -3px;
      border-right: none;
      border-bottom: none;
      border-radius: 6px 0 0 0;
    }
    
    &.corner-tr {
      top: -3px;
      right: -3px;
      border-left: none;
      border-bottom: none;
      border-radius: 0 6px 0 0;
    }
    
    &.corner-bl {
      bottom: -3px;
      left: -3px;
      border-right: none;
      border-top: none;
      border-radius: 0 0 0 6px;
    }
    
    &.corner-br {
      bottom: -3px;
      right: -3px;
      border-left: none;
      border-top: none;
      border-radius: 0 0 6px 0;
    }
  }
}

.account-info {
  text-align: center;
  
  .info-title {
    font-size: 18px;
    font-weight: 500;
    margin-bottom: 8px;
    letter-spacing: 2px;
  }
  
  .user-id {
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 16px;
    letter-spacing: 3px;
    text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
  }
  
  .website {
    font-size: 15px;
    font-weight: 500;
    background: linear-gradient(90deg, #f7d774 0%, #e6ac00 50%, #f7d774 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 14px;
  }
  
  .tip {
    font-size: 14px;
    font-weight: 500;
    color: #9c6cff;
  }
}

.qr-loading {
  width: 180px;
  height: 180px;
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
  position: relative;
  z-index: 1;
  padding: 20px;
  padding-bottom: calc(env(safe-area-inset-bottom, 20px) + 20px);
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
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(156, 108, 255, 0.5);
  border-radius: 30px;
  color: #9c6cff;
  font-size: 14px;
  cursor: pointer;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  &:active:not(:disabled) {
    background: rgba(156, 108, 255, 0.2);
  }
}

// 响应式优化
@media (min-width: 768px) {
  .credential-page {
    max-width: 500px;
    margin: 0 auto;
  }
  
  .qr-frame .qr-code {
    width: 180px;
    height: 180px;
  }
  
  .account-info .user-id {
    font-size: 36px;
  }
}
</style>
