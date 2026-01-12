<template>
  <Teleport to="body">
    <div class="share-modal-overlay" v-if="visible" @click.self="$emit('close')">
      <div class="share-modal-content">
        <button class="share-modal-close" @click="$emit('close')">×</button>
        
        <div class="share-header">
          <img src="/images/backgrounds/ic_launcher.webp" alt="Logo" class="share-logo" />
          <div class="share-title-info">
            <h3 class="share-site-name">Soul成人版</h3>
            <p class="share-site-desc">全网最全成人视频平台</p>
          </div>
        </div>
        
        <div class="share-promo-image">
          <img :src="video?.cover_url || '/images/default-cover.webp'" alt="推广图" />
        </div>
        
        <div class="share-qr-section">
          <div class="share-qrcode">
            <img :src="qrCodeUrl" alt="二维码" />
          </div>
          <div class="share-invite-info">
            <div class="invite-code">邀请码 <span>{{ inviteCode }}</span></div>
            <div class="official-url">官方网址:{{ baseUrl }}</div>
          </div>
        </div>
        
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
  visible: { type: Boolean, default: false },
  video: { type: Object, default: null },
  inviteCode: { type: String, default: '3AUUHR' }
})

defineEmits(['close'])

const baseUrl = computed(() => window.location.origin.replace(/^https?:\/\//, ''))
const shareFullUrl = computed(() => {
  if (!props.video) return ''
  return `${window.location.origin}/shorts/${props.video.id}?ref=${props.inviteCode}`
})
const qrCodeUrl = computed(() => `https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${encodeURIComponent(shareFullUrl.value)}`)

const copyLink = () => {
  navigator.clipboard.writeText(shareFullUrl.value).then(() => {
    ElMessage.success('分享链接已复制，分享给好友注册后可获得3日VIP')
  }).catch(() => {
    ElMessage.info('请复制链接分享：' + shareFullUrl.value)
  })
}

const saveImage = () => {
  ElMessage.info('长按图片保存到相册')
}
</script>

<style lang="scss" scoped>
.share-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10000;
  padding: 20px;
  
  .share-modal-content {
    background: #1a1a2e;
    border-radius: 14px;
    width: 100%;
    max-width: 300px;
    padding: 18px 16px;
    position: relative;
    
    .share-modal-close {
      position: absolute;
      top: 8px;
      right: 8px;
      width: 24px;
      height: 24px;
      border: none;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 50%;
      font-size: 16px;
      color: rgba(255, 255, 255, 0.7);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      
      &:hover { background: rgba(255, 255, 255, 0.2); }
    }
    
    .share-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 10px;
      
      .share-logo { width: 32px; height: 32px; border-radius: 6px; object-fit: cover; }
      .share-title-info {
        .share-site-name { font-size: 14px; font-weight: 600; color: #fff; margin: 0 0 2px 0; }
        .share-site-desc { font-size: 11px; color: rgba(255, 255, 255, 0.6); margin: 0; }
      }
    }
    
    .share-promo-image {
      width: 100%;
      border-radius: 10px;
      overflow: hidden;
      margin-bottom: 12px;
      
      img { width: 100%; height: 380px; object-fit: cover; display: block; }
    }
    
    .share-qr-section {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 14px;
      
      .share-qrcode {
        flex-shrink: 0;
        background: #fff;
        padding: 4px;
        border-radius: 6px;
        
        img { width: 70px; height: 70px; border-radius: 4px; display: block; }
      }
      
      .share-invite-info {
        .invite-code {
          font-size: 13px; color: #fff; margin-bottom: 6px;
          span { font-weight: 700; color: #a855f7; margin-left: 4px; }
        }
        .official-url { font-size: 11px; color: rgba(255, 255, 255, 0.6); word-break: break-all; }
      }
    }
    
    .share-actions {
      display: flex;
      gap: 10px;
      
      .copy-link-btn, .save-image-btn {
        flex: 1;
        padding: 10px 12px;
        border-radius: 50px;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        transition: opacity 0.2s;
        
        &:hover { opacity: 0.85; }
      }
      
      .copy-link-btn {
        background: transparent;
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: #fff;
      }
      
      .save-image-btn {
        background: linear-gradient(90deg, #8b5cf6, #a855f7);
        border: none;
        color: #fff;
      }
    }
  }
}
</style>
