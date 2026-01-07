<template>
  <Teleport to="body">
    <div class="share-modal-overlay" v-if="visible" @click.self="close">
      <div class="share-modal-content">
        <!-- 关闭按钮 -->
        <button class="share-modal-close" @click="close">×</button>
        
        <!-- Logo 和标题 -->
        <div class="share-header">
          <img src="/images/backgrounds/ic_launcher.webp" alt="Logo" class="share-logo" />
          <div class="share-title-info">
            <h3 class="share-site-name">{{ siteName }}</h3>
            <p class="share-site-desc">{{ siteDesc }}</p>
          </div>
        </div>
        
        <!-- 推广图片 -->
        <div class="share-promo-image">
          <img :src="coverUrl || '/images/default-cover.webp'" alt="推广图" />
        </div>
        
        <!-- 二维码和邀请信息 -->
        <div class="share-qr-section">
          <div class="share-qrcode">
            <img :src="qrCodeUrl" alt="二维码" />
          </div>
          <div class="share-invite-info">
            <div class="invite-code">邀请码 <span>{{ inviteCode }}</span></div>
            <div class="official-url">官方网址:{{ baseUrl }}</div>
          </div>
        </div>
        
        <!-- 操作按钮 -->
        <div class="share-actions">
          <button class="copy-link-btn" @click="copyLink">复制链接</button>
          <button class="save-image-btn" @click="saveImage">保存图片</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  coverUrl: {
    type: String,
    default: ''
  },
  shareUrl: {
    type: String,
    default: ''
  },
  inviteCode: {
    type: String,
    default: ''
  },
  siteName: {
    type: String,
    default: 'Soul成人版'
  },
  siteDesc: {
    type: String,
    default: '全网最全成人视频平台'
  }
})

const emit = defineEmits(['update:visible', 'close'])

// 基础URL
const baseUrl = computed(() => {
  return window.location.origin.replace(/^https?:\/\//, '')
})

// 二维码URL
const qrCodeUrl = computed(() => {
  const url = props.shareUrl || window.location.href
  return `https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${encodeURIComponent(url)}`
})

// 关闭
const close = () => {
  emit('update:visible', false)
  emit('close')
}

// 复制链接
const copyLink = async () => {
  try {
    const url = props.shareUrl || window.location.href
    await navigator.clipboard.writeText(url)
    ElMessage.success('链接已复制')
  } catch (e) {
    ElMessage.error('复制失败')
  }
}

// 保存图片
const saveImage = () => {
  // 创建下载链接
  const link = document.createElement('a')
  link.href = qrCodeUrl.value
  link.download = 'share-qrcode.webp'
  link.click()
  ElMessage.success('图片已保存')
}
</script>

<style lang="scss" scoped>
.share-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

.share-modal-content {
  background: linear-gradient(180deg, #1a1030 0%, #0d0d1a 100%);
  border-radius: 16px;
  padding: 24px;
  max-width: 340px;
  width: 100%;
  position: relative;
  border: 1px solid rgba(139, 92, 246, 0.3);
}

.share-modal-close {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 32px;
  height: 32px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 50%;
  color: #fff;
  font-size: 20px;
  cursor: pointer;
  transition: background 0.2s;
  
  &:hover {
    background: rgba(255, 255, 255, 0.2);
  }
}

.share-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  
  .share-logo {
    width: 48px;
    height: 48px;
    border-radius: 12px;
  }
  
  .share-title-info {
    .share-site-name {
      font-size: 18px;
      font-weight: 600;
      color: #fff;
      margin: 0 0 4px;
    }
    
    .share-site-desc {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.6);
      margin: 0;
    }
  }
}

.share-promo-image {
  width: 100%;
  aspect-ratio: 16/9;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.share-qr-section {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  
  .share-qrcode {
    width: 100px;
    height: 100px;
    background: #fff;
    border-radius: 8px;
    padding: 4px;
    flex-shrink: 0;
    
    img {
      width: 100%;
      height: 100%;
    }
  }
  
  .share-invite-info {
    flex: 1;
    
    .invite-code {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.7);
      margin-bottom: 8px;
      
      span {
        color: #ffd700;
        font-weight: 600;
        margin-left: 4px;
      }
    }
    
    .official-url {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);
      word-break: break-all;
    }
  }
}

.share-actions {
  display: flex;
  gap: 12px;
  
  button {
    flex: 1;
    padding: 12px;
    border-radius: 24px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    border: none;
    
    &:hover {
      transform: scale(1.02);
    }
    
    &:active {
      transform: scale(0.98);
    }
  }
  
  .copy-link-btn {
    background: rgba(255, 255, 255, 0.1);
    color: #fff;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }
  
  .save-image-btn {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #fff;
  }
}
</style>
