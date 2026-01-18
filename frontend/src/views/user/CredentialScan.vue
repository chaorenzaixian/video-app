<template>
  <div class="scan-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </div>
      <h1 class="page-title">扫码登录</h1>
      <div class="header-right"></div>
    </header>

    <!-- 扫描区域 -->
    <div class="scan-area">
      <div class="scan-frame">
        <div class="corner corner-tl"></div>
        <div class="corner corner-tr"></div>
        <div class="corner corner-bl"></div>
        <div class="corner corner-br"></div>
        <div class="scan-line"></div>
        
        <!-- 预览图片 -->
        <img v-if="previewImage" :src="previewImage" class="preview-image" />
        
        <!-- 提示文字 -->
        <div class="scan-tip" v-if="!previewImage">
          <p>将凭证二维码放入框内</p>
          <p class="sub-tip">从相册选择或输入凭证</p>
        </div>
      </div>
    </div>

    <!-- 底部按钮 -->
    <div class="bottom-actions">
      <div class="action-item" @click="selectFromAlbum">
        <div class="action-icon">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/>
          </svg>
        </div>
        <span class="action-text">相册</span>
      </div>
      
      <div class="action-item" @click="goToMyCredential">
        <div class="action-icon">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
          </svg>
        </div>
        <span class="action-text">我的凭证</span>
      </div>
    </div>

    <!-- 隐藏的文件输入 -->
    <input 
      type="file" 
      ref="fileInput" 
      accept="image/*" 
      @change="handleFileSelect"
      style="display: none"
    />

    <!-- 手动输入凭证弹窗 -->
    <div class="input-modal" v-if="showInputModal" @click.self="showInputModal = false">
      <div class="modal-content">
        <h3>输入凭证令牌</h3>
        <p class="modal-tip">如果无法扫码，请手动输入凭证令牌</p>
        <input 
          type="text" 
          v-model="manualToken" 
          placeholder="请输入凭证令牌"
          class="token-input"
        />
        <div class="modal-actions">
          <button class="cancel-btn" @click="showInputModal = false">取消</button>
          <button class="confirm-btn" @click="loginWithToken" :disabled="!manualToken">确认登录</button>
        </div>
      </div>
    </div>

    <!-- 处理中遮罩 -->
    <div class="loading-overlay" v-if="processing">
      <div class="loading-spinner"></div>
      <p>正在识别二维码...</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import jsQR from 'jsqr'

const router = useRouter()
const userStore = useUserStore()

const fileInput = ref(null)
const previewImage = ref('')
const processing = ref(false)
const showInputModal = ref(false)
const manualToken = ref('')

// 从相册选择
const selectFromAlbum = () => {
  fileInput.value?.click()
}

// 处理文件选择
const handleFileSelect = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  // 显示预览
  previewImage.value = URL.createObjectURL(file)
  processing.value = true
  
  try {
    // 使用 jsQR 或其他方式解析二维码
    const token = await parseQRCode(file)
    
    if (token) {
      // 找到令牌，进行登录
      await loginWithQRToken(token)
    } else {
      ElMessage.warning('未识别到有效的二维码，请重试')
      previewImage.value = ''
    }
  } catch (error) {
    console.error('解析二维码失败:', error)
    ElMessage.error('识别失败，请尝试手动输入凭证')
    showInputModal.value = true
  } finally {
    processing.value = false
    // 清空文件输入
    event.target.value = ''
  }
}

// 解析二维码（使用 jsQR）
const parseQRCode = async (file) => {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      try {
        const canvas = document.createElement('canvas')
        const ctx = canvas.getContext('2d')
        canvas.width = img.width
        canvas.height = img.height
        ctx.drawImage(img, 0, 0)
        
        // 获取图像数据
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
        
        // 使用 jsQR 解析二维码
        const qrCode = jsQR(imageData.data, imageData.width, imageData.height)
        
        if (qrCode && qrCode.data) {
          console.log('二维码内容:', qrCode.data)
          
          // 尝试从二维码内容中提取 token
          // 格式可能是: URL?token=xxx 或直接是 token
          let token = null
          
          try {
            const url = new URL(qrCode.data)
            token = url.searchParams.get('token')
          } catch {
            // 如果不是URL，直接使用内容作为 token
            token = qrCode.data
          }
          
          resolve(token)
        } else {
          resolve(null)
        }
      } catch (err) {
        console.error('解析二维码出错:', err)
        reject(err)
      }
    }
    img.onerror = () => reject(new Error('图片加载失败'))
    img.src = URL.createObjectURL(file)
  })
}

// 使用令牌登录
const loginWithQRToken = async (token) => {
  try {
    const res = await axios.post('/api/v1/auth/qr-login', null, {
      params: {
        token: token,
        device_id: generateDeviceId(),
        device_info: getDeviceInfo()
      }
    })
    
    // 保存登录信息
    localStorage.setItem('token', res.data.access_token)
    if (res.data.refresh_token) {
      localStorage.setItem('refresh_token', res.data.refresh_token)
    }
    
    // 更新用户状态
    await userStore.fetchUser()
    
    ElMessage.success('登录成功！')
    router.push('/user/profile')
  } catch (error) {
    console.error('登录失败:', error)
    if (error.response?.status === 400 || error.response?.status === 404) {
      ElMessage.error('凭证无效或已过期')
    } else {
      ElMessage.error(error.response?.data?.detail || '登录失败，请重试')
    }
    previewImage.value = ''
  }
}

// 手动输入令牌登录
const loginWithToken = async () => {
  if (!manualToken.value) return
  
  processing.value = true
  showInputModal.value = false
  
  try {
    await loginWithQRToken(manualToken.value.trim())
  } finally {
    processing.value = false
    manualToken.value = ''
  }
}

// 去我的凭证页面
const goToMyCredential = () => {
  router.push('/user/account-credential')
}

// 生成设备ID
const generateDeviceId = () => {
  const ua = navigator.userAgent
  const screen = `${window.screen.width}x${window.screen.height}`
  const fingerprint = `${ua}-${screen}-${Date.now()}`
  
  let hash = 0
  for (let i = 0; i < fingerprint.length; i++) {
    const char = fingerprint.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash
  }
  return Math.abs(hash).toString(16).padStart(16, '0')
}

// 获取设备信息
const getDeviceInfo = () => {
  const ua = navigator.userAgent
  if (/iPhone/i.test(ua)) return 'iPhone'
  if (/iPad/i.test(ua)) return 'iPad'
  if (/Android/i.test(ua)) return 'Android'
  if (/Windows/i.test(ua)) return 'Windows'
  if (/Mac/i.test(ua)) return 'Mac'
  return 'Unknown'
}
</script>

<style lang="scss" scoped>
.scan-page {
  min-height: 100vh;
  background: #000;
  color: #fff;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  padding-top: calc(16px + env(safe-area-inset-top, 0px));
  background: transparent;
  position: relative;
  z-index: 10;
  
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

.scan-area {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.scan-frame {
  width: 280px;
  height: 280px;
  position: relative;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  overflow: hidden;
  
  .corner {
    position: absolute;
    width: 30px;
    height: 30px;
    border: 3px solid #fff;
    
    &.corner-tl {
      top: 0;
      left: 0;
      border-right: none;
      border-bottom: none;
      border-radius: 8px 0 0 0;
    }
    
    &.corner-tr {
      top: 0;
      right: 0;
      border-left: none;
      border-bottom: none;
      border-radius: 0 8px 0 0;
    }
    
    &.corner-bl {
      bottom: 0;
      left: 0;
      border-right: none;
      border-top: none;
      border-radius: 0 0 0 8px;
    }
    
    &.corner-br {
      bottom: 0;
      right: 0;
      border-left: none;
      border-top: none;
      border-radius: 0 0 8px 0;
    }
  }
  
  .scan-line {
    position: absolute;
    left: 10%;
    width: 80%;
    height: 2px;
    background: linear-gradient(90deg, transparent, #667eea, transparent);
    animation: scan 2s linear infinite;
  }
  
  .preview-image {
    width: 100%;
    height: 100%;
    object-fit: contain;
    padding: 20px;
  }
  
  .scan-tip {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
    
    p {
      margin: 0;
      font-size: 14px;
      color: rgba(255, 255, 255, 0.8);
      
      &.sub-tip {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.5);
        margin-top: 8px;
      }
    }
  }
}

@keyframes scan {
  0% { top: 10%; opacity: 0; }
  50% { opacity: 1; }
  100% { top: 90%; opacity: 0; }
}

.bottom-actions {
  display: flex;
  justify-content: center;
  gap: 80px;
  padding: 40px 20px;
  padding-bottom: calc(40px + env(safe-area-inset-bottom, 20px));
  
  .action-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    cursor: pointer;
    
    &:active {
      opacity: 0.7;
    }
    
    .action-icon {
      width: 56px;
      height: 56px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      
      svg {
        width: 28px;
        height: 28px;
        fill: #fff;
      }
    }
    
    .action-text {
      font-size: 14px;
      color: #fff;
    }
  }
}

.input-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 20px;
  
  .modal-content {
    background: #1a1a2e;
    border-radius: 16px;
    padding: 24px;
    width: 100%;
    max-width: 320px;
    
    h3 {
      font-size: 18px;
      font-weight: 600;
      margin: 0 0 8px;
      text-align: center;
    }
    
    .modal-tip {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.6);
      text-align: center;
      margin: 0 0 20px;
    }
    
    .token-input {
      width: 100%;
      padding: 14px 16px;
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 10px;
      color: #fff;
      font-size: 14px;
      outline: none;
      
      &::placeholder {
        color: rgba(255, 255, 255, 0.4);
      }
      
      &:focus {
        border-color: #667eea;
      }
    }
    
    .modal-actions {
      display: flex;
      gap: 12px;
      margin-top: 20px;
      
      button {
        flex: 1;
        padding: 12px;
        border-radius: 10px;
        font-size: 15px;
        font-weight: 500;
        cursor: pointer;
        transition: opacity 0.2s;
        
        &:active {
          opacity: 0.8;
        }
        
        &:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      }
      
      .cancel-btn {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: #fff;
      }
      
      .confirm-btn {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border: none;
        color: #fff;
      }
    }
  }
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 100;
  
  .loading-spinner {
    width: 48px;
    height: 48px;
    border: 3px solid rgba(102, 126, 234, 0.3);
    border-top-color: #667eea;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  p {
    margin-top: 16px;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.8);
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

// 响应式优化
@media (min-width: 768px) {
  .scan-page {
    max-width: 500px;
    margin: 0 auto;
  }
  
  .page-header {
    max-width: 500px;
    left: 50%;
    transform: translateX(-50%);
  }
  
  .scan-frame {
    width: 320px;
    height: 320px;
  }
  
  .input-modal .modal-content {
    max-width: 400px;
  }
}

@media (min-width: 1024px) {
  .scan-page {
    max-width: 550px;
  }
  
  .page-header {
    max-width: 550px;
  }
}

@media (hover: hover) {
  .action-item:hover {
    .action-icon {
      background: rgba(255, 255, 255, 0.15);
    }
  }
  
  .cancel-btn:hover {
    background: rgba(255, 255, 255, 0.15);
  }
  
  .confirm-btn:hover:not(:disabled) {
    opacity: 0.9;
  }
}
</style>



