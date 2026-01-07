<template>
  <div class="pre-roll-ad" v-if="visible && ad">
    <div class="ad-video-container">
      <!-- 视频广告 -->
      <video
        v-if="ad.ad_type === 'video'"
        ref="adVideoRef"
        class="ad-video"
        :src="ad.media_url"
        @timeupdate="onTimeUpdate"
        @ended="onEnded"
        @canplay="onCanPlay"
        autoplay
        playsinline
        muted
      />
      
      <!-- 图片广告 -->
      <div v-else class="ad-image-wrapper" @click="onImageClick">
        <img 
          :src="ad.media_url" 
          class="ad-image"
          @load="onImageLoad"
        />
      </div>
      
      <!-- 广告覆盖层 -->
      <div class="ad-overlay">
        <!-- 倒计时 -->
        <div class="ad-countdown" v-if="!canSkip">
          广告 {{ countdown }}s
        </div>
        <!-- 关闭按钮 -->
        <div class="ad-close-btn" v-else @click="skip">
          关闭广告 ✕
        </div>
        
        <!-- 了解更多链接 -->
        <a 
          v-if="ad.target_url" 
          :href="ad.target_url" 
          target="_blank" 
          class="ad-link"
          @click="onClick"
        >
          了解更多
        </a>
      </div>
      
      <!-- 广告标签 -->
      <div class="ad-label">广告</div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onBeforeUnmount } from 'vue'
import { useTimers } from '@/composables/useCleanup'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  ad: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['skip', 'click', 'ended'])

const { setInterval, clearInterval } = useTimers()

const adVideoRef = ref(null)
const countdown = ref(5)
const canSkip = ref(false)
let countdownTimer = null

// 监听可见性变化
watch(() => props.visible, (val) => {
  if (val && props.ad) {
    startCountdown()
  } else {
    stopCountdown()
  }
})

// 开始倒计时
const startCountdown = () => {
  countdown.value = props.ad?.duration || 5
  canSkip.value = false
  
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      canSkip.value = true
      stopCountdown()
    }
  }, 1000)
}

// 停止倒计时
const stopCountdown = () => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
}

// 视频时间更新
const onTimeUpdate = () => {
  if (adVideoRef.value) {
    const currentTime = adVideoRef.value.currentTime
    const duration = props.ad?.duration || 5
    const remaining = Math.max(0, Math.ceil(duration - currentTime))
    countdown.value = remaining
    
    if (remaining <= 0) {
      canSkip.value = true
    }
  }
}

// 视频可以播放
const onCanPlay = () => {
  if (adVideoRef.value) {
    adVideoRef.value.play().catch(() => {
      adVideoRef.value.muted = true
      adVideoRef.value.play()
    })
  }
}

// 视频播放结束
const onEnded = () => {
  canSkip.value = true
  // 循环播放直到用户关闭
  if (adVideoRef.value && props.ad?.ad_type === 'video') {
    adVideoRef.value.currentTime = 0
    adVideoRef.value.play().catch(() => {})
  }
}

// 图片加载完成
const onImageLoad = () => {
  startCountdown()
}

// 图片点击
const onImageClick = () => {
  if (props.ad?.target_url) {
    onClick()
    window.open(props.ad.target_url, '_blank')
  }
}

// 广告点击
const onClick = () => {
  emit('click', props.ad)
}

// 跳过广告
const skip = () => {
  stopCountdown()
  if (adVideoRef.value) {
    adVideoRef.value.pause()
  }
  emit('skip')
}

onBeforeUnmount(() => {
  stopCountdown()
})
</script>

<style lang="scss" scoped>
.pre-roll-ad {
  position: absolute;
  inset: 0;
  z-index: 100;
  background: #000;
}

.ad-video-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ad-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.ad-image-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  
  .ad-image {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
  }
}

.ad-overlay {
  position: absolute;
  top: 0;
  right: 0;
  padding: 16px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
}

.ad-countdown {
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
}

.ad-close-btn {
  background: rgba(255, 255, 255, 0.9);
  color: #333;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    background: #fff;
  }
}

.ad-link {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  padding: 8px 20px;
  border-radius: 20px;
  font-size: 14px;
  text-decoration: none;
  transition: all 0.2s;
  
  &:hover {
    transform: scale(1.05);
  }
}

.ad-label {
  position: absolute;
  top: 16px;
  left: 16px;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
}
</style>
