<template>
  <div class="invite-share-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()">
        <svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
          <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
        </svg>
      </div>
      <h1 class="page-title">邀请分享</h1>
      <div class="header-right" @click="$router.push('/user/invite-records')">
        <span>记录</span>
      </div>
    </header>

    <!-- 分享卡片 -->
    <div class="share-card-container">
      <div class="share-card" ref="shareCardRef">
        <!-- 背景图 -->
        <div class="card-bg">
          <img src="/images/backgrounds/girl2.webp" alt="背景" />
        </div>
        
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
          <span class="site-url">SOUL 官网地址 {{ siteUrl }}</span>
          <span class="scan-tip">提示*苹果手机请用相机扫码/安卓手机推荐UC浏览器扫码</span>
        </div>
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

const userStore = useUserStore()

const inviteCode = ref('')
const siteUrl = ref('https://soul9.fm')
const shareCardRef = ref(null)
const qrCodeRef = ref(null)

// 生成二维码
const generateQRCode = async () => {
  if (!qrCodeRef.value) return
  
  const inviteLink = `${siteUrl.value}?code=${inviteCode.value}`
  
  try {
    // 清空之前的二维码
    qrCodeRef.value.innerHTML = ''
    
    // 创建canvas
    const canvas = document.createElement('canvas')
    await QRCode.toCanvas(canvas, inviteLink, {
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
  const link = `${siteUrl.value}?code=${inviteCode.value}`
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
  inviteCode.value = userStore.user?.invite_code || 'T5884L'
  
  await nextTick()
  generateQRCode()
})
</script>

<style lang="scss" scoped>
.invite-share-page {
  height: 100vh;
  background: #0a0a0a;
  color: #fff;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

// 顶部导航
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  padding-top: calc(12px + env(safe-area-inset-top, 0px));
  background: rgba(0, 0, 0, 0.3);
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

// 分享卡片容器
.share-card-container {
  flex: 1;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 0;
}

// 分享卡片
.share-card {
  position: relative;
  width: 100%;
  max-width: 320px;
  max-height: 100%;
  border-radius: 10px;
  overflow: hidden;
  background: #1a1a2e;
  
  .card-bg {
    position: relative;
    width: 100%;
    
    img {
      width: 100%;
      height: auto;
      display: block;
    }
  }
  
  // 二维码区域
  .qr-section {
    position: absolute;
    top: 45%;
    left: 50%;
    transform: translate(-50%, -50%);
  }
  
  .qr-frame {
    padding: 6px;
    background: #fff;
    border-radius: 6px;
    position: relative;
    
    // 四角装饰
    &::before,
    &::after {
      content: '';
      position: absolute;
      width: 16px;
      height: 16px;
      border: 2px solid #e74c3c;
    }
    
    &::before {
      top: -3px;
      left: -3px;
      border-right: none;
      border-bottom: none;
    }
    
    &::after {
      top: -3px;
      right: -3px;
      border-left: none;
      border-bottom: none;
    }
  }
  
  .qr-code {
    width: 140px;
    height: 140px;
    display: flex;
    align-items: center;
    justify-content: center;
    
    canvas {
      max-width: 100%;
      max-height: 100%;
    }
  }
  
  // 邀请码信息
  .invite-info {
    padding: 16px 12px 20px;
    text-align: center;
    background: linear-gradient(to bottom, transparent, rgba(0, 0, 0, 0.8) 30%);
    
    .invite-label {
      display: block;
      font-size: 13px;
      color: rgba(255, 255, 255, 0.7);
      margin-bottom: 4px;
    }
    
    .invite-code {
      display: block;
      font-size: 28px;
      font-weight: 700;
      color: #fff;
      letter-spacing: 3px;
      margin-bottom: 10px;
    }
    
    .site-url {
      display: block;
      font-size: 13px;
      color: rgba(255, 255, 255, 0.8);
      margin-bottom: 8px;
    }
    
    .scan-tip {
      display: block;
      font-size: 11px;
      color: #5b8def;
    }
  }
}

// 底部按钮
.bottom-actions {
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
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: #fff;
  }
  
  .save-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    color: #fff;
  }
}

// 添加二维码角落装饰的伪元素
.qr-frame {
  &::before,
  &::after,
  > .qr-code::before,
  > .qr-code::after {
    content: '';
    position: absolute;
    width: 16px;
    height: 16px;
    border: 2px solid #e74c3c;
  }
}

.qr-code {
  position: relative;
  
  &::before {
    bottom: -9px;
    left: -9px;
    border-right: none;
    border-top: none;
  }
  
  &::after {
    bottom: -9px;
    right: -9px;
    border-left: none;
    border-top: none;
  }
}
</style>

