<template>
  <div class="invite-share-page">
    <!-- 全屏背景图 -->
    <div class="page-bg">
      <img src="/images/backgrounds/girl2.webp" alt="背景" />
    </div>
    
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </div>
      <h1 class="page-title">邀请分享</h1>
      <div class="header-right" @click="$router.push('/user/invite-records')">
        <span>记录</span>
      </div>
    </header>

    <!-- 内容区域 -->
    <div class="content-area" ref="shareCardRef">
      <!-- 二维码区域 -->
      <div class="qr-section">
        <div class="qr-frame">
          <div class="qr-code" ref="qrCodeRef"></div>
        </div>
      </div>
      
      <!-- 邀请码信息 -->
      <div class="invite-info">
        <span class="invite-label">邀请码</span>
        <span class="invite-code">{{ inviteCode }}</span>
        <span class="site-url" @click="copySiteUrl">
          SOUL 官网地址 {{ siteUrl }}
          <span class="copy-hint">（点击复制）</span>
        </span>
        <span class="scan-tip">提示*苹果手机请用相机扫码/安卓手机推荐UC浏览器扫码</span>
      </div>
    </div>

    <!-- 底部按钮 -->
    <div class="bottom-actions">
      <button class="action-btn copy-btn" @click="copyLink">
        <span>复制链接</span>
      </button>
      <button class="action-btn save-btn" @click="saveImage">
        <span>保存图片</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import QRCode from 'qrcode'
import api from '@/utils/api'

const userStore = useUserStore()

const inviteCode = ref('')
const inviteUrl = ref('')
const siteUrl = ref('')
const shareCardRef = ref(null)
const qrCodeRef = ref(null)

// 获取邀请信息
const fetchInviteInfo = async () => {
  try {
    const res = await api.get('/promotion/invite-code')
    inviteCode.value = res.data?.invite_code || userStore.user?.invite_code || ''
    inviteUrl.value = res.data?.invite_url || ''
    // 从 invite_url 提取域名
    if (inviteUrl.value) {
      const url = new URL(inviteUrl.value)
      siteUrl.value = url.origin
    } else {
      siteUrl.value = window.location.origin
    }
  } catch (error) {
    console.error('获取邀请信息失败:', error)
    // 降级使用本地数据
    inviteCode.value = userStore.user?.invite_code || ''
    siteUrl.value = window.location.origin
    inviteUrl.value = `${siteUrl.value}/user?invite=${inviteCode.value}`
  }
}

// 生成二维码
const generateQRCode = async () => {
  if (!qrCodeRef.value || !inviteUrl.value) return
  
  try {
    // 清空之前的二维码
    qrCodeRef.value.innerHTML = ''
    
    // 创建canvas
    const canvas = document.createElement('canvas')
    await QRCode.toCanvas(canvas, inviteUrl.value, {
      width: 140,
      margin: 1,
      color: {
        dark: '#000000',
        light: '#ffffff'
      }
    })
    qrCodeRef.value.appendChild(canvas)
  } catch (error) {
    console.error('生成二维码失败:', error)
  }
}

// 复制链接
const copyLink = () => {
  const link = inviteUrl.value || `${siteUrl.value}/user?invite=${inviteCode.value}`
  if (navigator.clipboard) {
    navigator.clipboard.writeText(link)
    ElMessage.success('链接已复制')
  } else {
    // 降级方案
    const textarea = document.createElement('textarea')
    textarea.value = link
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    ElMessage.success('链接已复制')
  }
}

// 复制官网地址
const copySiteUrl = () => {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(siteUrl.value)
    ElMessage.success('官网地址已复制')
  } else {
    const textarea = document.createElement('textarea')
    textarea.value = siteUrl.value
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    ElMessage.success('官网地址已复制')
  }
}

// 保存图片
const saveImage = async () => {
  try {
    // 动态导入 html2canvas
    const html2canvas = (await import('html2canvas')).default
    
    if (!shareCardRef.value) return
    
    const canvas = await html2canvas(shareCardRef.value, {
      scale: 2,
      useCORS: true,
      allowTaint: true,
      backgroundColor: null
    })
    
    // 转换为图片并下载
    const link = document.createElement('a')
    link.download = `invite_${inviteCode.value}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
    
    ElMessage.success('图片已保存')
  } catch (error) {
    console.error('保存图片失败:', error)
    ElMessage.error('保存图片失败，请重试')
  }
}

onMounted(async () => {
  await fetchInviteInfo()
  await nextTick()
  generateQRCode()
})
</script>

<style lang="scss" scoped>
$breakpoint-lg: 768px;
$breakpoint-xl: 1024px;

.invite-share-page {
  height: 100vh;
  color: #fff;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  
  @media (min-width: $breakpoint-lg) {
    max-width: 500px;
    margin: 0 auto;
  }
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
      rgba(0, 0, 0, 0.3) 0%,
      rgba(0, 0, 0, 0.1) 30%,
      rgba(0, 0, 0, 0.1) 50%,
      rgba(0, 0, 0, 0.6) 80%,
      rgba(0, 0, 0, 0.85) 100%
    );
  }
}

// 顶部导航
.page-header {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  padding-top: calc(12px + env(safe-area-inset-top, 0px));
  flex-shrink: 0;
  
  .back-btn {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    color: #fff;
  }
  
  .page-title {
    flex: 1;
    text-align: center;
    font-size: 16px;
    font-weight: 600;
    margin: 0;
  }
  
  .header-right {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.8);
    cursor: pointer;
    padding: 4px 8px;
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
  padding-bottom: 40px;
}

// 二维码区域
.qr-section {
  margin-bottom: 24px;
}

.qr-frame {
  padding: 8px;
  background: #fff;
  border-radius: 8px;
  position: relative;
  
  // 四角装饰
  &::before,
  &::after {
    content: '';
    position: absolute;
    width: 18px;
    height: 18px;
    border: 3px solid #e74c3c;
  }
  
  &::before {
    top: -4px;
    left: -4px;
    border-right: none;
    border-bottom: none;
  }
  
  &::after {
    top: -4px;
    right: -4px;
    border-left: none;
    border-bottom: none;
  }
}

.qr-code {
  width: 160px;
  height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  
  canvas {
    max-width: 100%;
    max-height: 100%;
  }
  
  &::before,
  &::after {
    content: '';
    position: absolute;
    width: 18px;
    height: 18px;
    border: 3px solid #e74c3c;
  }
  
  &::before {
    bottom: -12px;
    left: -12px;
    border-right: none;
    border-top: none;
  }
  
  &::after {
    bottom: -12px;
    right: -12px;
    border-left: none;
    border-top: none;
  }
}

// 邀请码信息
.invite-info {
  text-align: center;
  
  .invite-label {
    display: block;
    font-size: 16px;
    color: rgba(255, 255, 255, 0.8);
    margin-bottom: 6px;
  }
  
  .invite-code {
    display: block;
    font-size: 32px;
    font-weight: 700;
    color: #fff;
    letter-spacing: 4px;
    margin-bottom: 16px;
    text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
  }
  
  .site-url {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    font-size: 14px;
    font-weight: 500;
    background: linear-gradient(90deg, #f7d774 0%, #e6ac00 50%, #f7d774 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 16px;
    cursor: pointer;
    
    .copy-hint {
      font-size: 12px;
      font-weight: 400;
    }
    
    &:active {
      opacity: 0.7;
    }
  }
  
  .scan-tip {
    display: block;
    font-size: 13px;
    font-weight: 500;
    background: linear-gradient(90deg, #f7d774 0%, #e6ac00 50%, #f7d774 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-top: 8px;
  }
}

// 底部按钮
.bottom-actions {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  padding-bottom: calc(12px + env(safe-area-inset-bottom, 0px));
  flex-shrink: 0;
  
  .action-btn {
    flex: 1;
    padding: 12px 20px;
    border-radius: 22px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    
    &:active {
      transform: scale(0.98);
      opacity: 0.9;
    }
  }
  
  .copy-btn {
    background: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.4);
    color: #fff;
    backdrop-filter: blur(10px);
  }
  
  .save-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    color: #fff;
  }
}
</style>

