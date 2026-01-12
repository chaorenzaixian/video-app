<template>
  <Teleport to="body">
    <div class="share-modal-overlay" v-if="show" @click.self="$emit('close')">
      <div class="share-modal-content">
        <button class="share-modal-close" @click="$emit('close')">×</button>
        
        <!-- Logo 和标题 -->
        <div class="share-header">
          <img src="/images/backgrounds/ic_launcher.webp" alt="Logo" class="share-logo" />
          <div class="share-title-info">
            <h3 class="share-site-name">Soul成人版</h3>
            <p class="share-site-desc">全网最全成人视频平台</p>
          </div>
        </div>
        
        <!-- 推广图片 -->
        <div class="share-promo-image">
          <img :src="coverUrl" alt="推广图" />
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
          <button class="save-image-btn" @click="$emit('saveImage')">保存图片</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  coverUrl: {
    type: String,
    default: '/images/default-cover.webp'
  },
  inviteCode: {
    type: String,
    default: ''
  },
  shareUrl: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['close', 'saveImage'])

const baseUrl = computed(() => {
  return window.location.origin.replace(/^https?:\/\//, '')
})

const qrCodeUrl = computed(() => {
  return `https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${encodeURIComponent(props.shareUrl)}`
})

const copyLink = async () => {
  try {
    await navigator.clipboard.writeText(props.shareUrl)
    ElMessage.success('链接已复制')
  } catch (e) {
    // 降级方案
    const input = document.createElement('input')
    input.value = props.shareUrl
    document.body.appendChild(input)
    input.select()
    document.execCommand('copy')
    document.body.removeChild(input)
    ElMessage.success('链接已复制')
  }
}
</script>

<style scoped>
.share-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.share-modal-content {
  background: #1a1a1a;
  border-radius: 16px;
  padding: 24px;
  width: 90%;
  max-width: 360px;
  position: relative;
}

.share-modal-close {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 28px;
  height: 28px;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  border-radius: 50%;
  font-size: 18px;
  cursor: pointer;
}

.share-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.share-logo {
  width: 48px;
  height: 48px;
  border-radius: 12px;
}

.share-site-name {
  color: #fff;
  font-size: 16px;
  margin: 0;
}

.share-site-desc {
  color: #888;
  font-size: 12px;
  margin: 4px 0 0;
}

.share-promo-image {
  width: 100%;
  aspect-ratio: 16/9;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
}

.share-promo-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.share-qr-section {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.share-qrcode {
  width: 100px;
  height: 100px;
  background: #fff;
  border-radius: 8px;
  padding: 4px;
}

.share-qrcode img {
  width: 100%;
  height: 100%;
}

.share-invite-info {
  flex: 1;
  color: #fff;
}

.invite-code {
  font-size: 14px;
  margin-bottom: 8px;
}

.invite-code span {
  color: #ec4899;
  font-weight: bold;
}

.official-url {
  font-size: 12px;
  color: #888;
  word-break: break-all;
}

.share-actions {
  display: flex;
  gap: 12px;
}

.copy-link-btn,
.save-image-btn {
  flex: 1;
  padding: 12px;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  border: none;
}

.copy-link-btn {
  background: transparent;
  border: 1px solid #ec4899;
  color: #ec4899;
}

.save-image-btn {
  background: linear-gradient(135deg, #ec4899, #f472b6);
  color: #fff;
}
</style>
