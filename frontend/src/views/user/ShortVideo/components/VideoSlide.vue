<template>
  <div class="video-slide">
    <!-- 视频播放器 -->
    <video
      ref="videoRef"
      :src="video.video_url || video.hls_url"
      :poster="video.cover_url"
      class="short-video"
      loop
      playsinline
      webkit-playsinline
      x5-playsinline
      preload="auto"
      @timeupdate="onTimeUpdate"
      @loadedmetadata="$emit('loaded')"
      @canplay="$emit('canplay')"
      @play="$emit('play')"
      @pause="$emit('pause')"
    />
    
    <!-- 点击区域 -->
    <div class="tap-area" @touchstart.passive="onTapStart" @touchend="onTapEnd" @click="onTapClick"></div>

    <!-- 暂停图标 -->
    <div class="persistent-pause" v-if="isCurrent && !isPlaying">
      <svg viewBox="0 0 48 48" fill="none">
        <path d="M16 10.5C16 9.5 16.8 8.5 18 9L38 22c1.5 1 1.5 3 0 4L18 39c-1.2 0.5-2-0.5-2-1.5V10.5z" fill="white" fill-opacity="0.85" stroke="white" stroke-width="1" stroke-linejoin="round" stroke-linecap="round"/>
      </svg>
    </div>

    <!-- 双击爱心动画 -->
    <div class="like-animation" v-if="showLikeAnimation">
      <svg class="heart" viewBox="0 0 24 24" fill="#fe2c55">
        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
      </svg>
    </div>

    <!-- 右侧操作栏 -->
    <ActionBar
      :video="video"
      :is-vip="isVip"
      @like="$emit('like')"
      @comment="$emit('comment')"
      @favorite="$emit('favorite')"
      @share="$emit('share')"
      @download="$emit('download')"
      @follow="$emit('follow')"
      @go-profile="$emit('go-profile', $event)"
    />

    <!-- 底部信息 -->
    <div class="video-info">
      <div class="vip-tip-bar" v-if="video.is_vip_only || isTrialVideo" @click.stop="onVipTipClick">
        <template v-if="isVip && video.is_vip_only">
          <span class="vip-icon">👑</span>
          <span class="vip-text">已享VIP免费特权</span>
        </template>
        <template v-else>
          <span class="vip-text">开通会员 畅享完整版</span>
          <span class="vip-arrow">›</span>
        </template>
      </div>
      <div class="author-name">@{{ video.uploader_nickname || '用户' }}</div>
      <div class="video-title">{{ video.title }}</div>
      <div class="video-desc" v-if="video.description">{{ video.description }}</div>
    </div>

    <!-- 进度条 -->
    <div class="progress-bar-container" v-if="isCurrent">
      <span class="time-display">{{ formatDuration(currentPlayTime) }} / {{ formatDuration(video.duration) }}</span>
      <div class="progress-bar" @click.stop="onProgressClick" @touchstart.stop="onProgressTouchStart" @touchmove.stop="onProgressTouchMove" @touchend.stop="onProgressTouchEnd">
        <div class="progress" :style="{ width: progress + '%' }"></div>
        <div class="progress-thumb" :style="{ left: progress + '%' }"></div>
      </div>
    </div>

    <!-- 试看倒计时 -->
    <div class="trial-countdown" v-if="isCurrent && isTrialVideo && !isTrialEnded && trialRemaining > 0 && trialRemaining <= 5">
      <span class="countdown-text">试看剩余 {{ trialRemaining }}s</span>
    </div>

    <!-- 试看结束遮罩 -->
    <div class="trial-overlay" v-if="isCurrent && isTrialEnded && isTrialVideo">
      <div class="trial-content">
        <h3>试看结束</h3>
        <p class="trial-subtitle">开通VIP 永久免费观看</p>
        <div class="trial-top-btns">
          <button class="share-btn" @click.stop="$emit('share')">分享得3日VIP</button>
          <button class="vip-btn" @click.stop="$emit('go-vip')">开通VIP免费看</button>
        </div>
        <div class="trial-divider">或</div>
        <button class="coin-purchase-btn" @click.stop="$emit('purchase')" :disabled="purchasing">
          <span class="coin-icon">🪙</span>
          {{ video.coin_price || 20 }} 金币购买本片
          <span class="arrow">›</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { formatDuration } from '@/utils/format'
import ActionBar from './ActionBar.vue'

const props = defineProps({
  video: { type: Object, required: true },
  isCurrent: { type: Boolean, default: false },
  isPlaying: { type: Boolean, default: false },
  isVip: { type: [Boolean, Number], default: false },
  isTrialEnded: { type: Boolean, default: false },
  trialRemaining: { type: Number, default: 15 },
  purchasing: { type: Boolean, default: false },
  showLikeAnimation: { type: Boolean, default: false }
})

const emit = defineEmits(['like', 'comment', 'favorite', 'share', 'download', 'follow', 'go-profile', 'go-vip', 'purchase', 'tap', 'double-tap', 'time-update', 'progress-seek', 'loaded', 'canplay', 'play', 'pause'])

const videoRef = ref(null)
const progress = ref(0)
const currentPlayTime = ref(0)
const isSeeking = ref(false)

// 点击状态
const tapStartX = ref(0)
const tapStartY = ref(0)
const tapStartTime = ref(0)
const isTapHandled = ref(false)
let lastTapTime = 0

// 是否是试看视频
const isTrialVideo = computed(() => {
  if (!props.video) return false
  if (props.video.is_purchased) return false
  return (props.video.trial_seconds && props.video.trial_seconds > 0)
})

const onVipTipClick = () => {
  if (!(props.isVip && props.video.is_vip_only)) {
    emit('go-vip')
  }
}

// 时间更新
const onTimeUpdate = (e) => {
  if (isSeeking.value) return
  const videoEl = e.target
  if (!videoEl.duration) return
  progress.value = (videoEl.currentTime / videoEl.duration) * 100
  currentPlayTime.value = videoEl.currentTime
  emit('time-update', { currentTime: videoEl.currentTime, duration: videoEl.duration })
}

// 进度条操作
const getSeekTime = (event) => {
  const bar = event.currentTarget
  const rect = bar.getBoundingClientRect()
  const clickX = event.clientX || (event.touches && event.touches[0]?.clientX) || 0
  const percentage = Math.max(0, Math.min(1, (clickX - rect.left) / rect.width))
  const duration = props.video.duration || 0
  if (isTrialVideo.value) {
    const maxTime = props.video.trial_seconds || 15
    return Math.min(percentage * duration, maxTime)
  }
  return percentage * duration
}

const onProgressClick = (e) => {
  const seekTime = getSeekTime(e)
  if (videoRef.value) {
    videoRef.value.currentTime = seekTime
    currentPlayTime.value = seekTime
    progress.value = (seekTime / (props.video.duration || 1)) * 100
  }
  emit('progress-seek', seekTime)
}

const onProgressTouchStart = () => { isSeeking.value = true }
const onProgressTouchMove = (e) => {
  if (!isSeeking.value) return
  const seekTime = getSeekTime(e)
  if (videoRef.value) {
    videoRef.value.currentTime = seekTime
    currentPlayTime.value = seekTime
    progress.value = (seekTime / (props.video.duration || 1)) * 100
  }
}
const onProgressTouchEnd = () => { isSeeking.value = false }

// 点击处理
const onTapStart = (e) => {
  if (e.touches?.length > 0) {
    tapStartX.value = e.touches[0].clientX
    tapStartY.value = e.touches[0].clientY
    tapStartTime.value = Date.now()
    isTapHandled.value = false
  }
}

const onTapEnd = (e) => {
  if (isTapHandled.value) return
  if (!e.changedTouches?.length) return
  const touch = e.changedTouches[0]
  if (Math.abs(touch.clientX - tapStartX.value) > 15 || Math.abs(touch.clientY - tapStartY.value) > 15) return
  isTapHandled.value = true
  e.preventDefault()
  handleTap()
}

const onTapClick = () => {
  if (isTapHandled.value) { isTapHandled.value = false; return }
  handleTap()
}

const handleTap = () => {
  const now = Date.now()
  if (now - lastTapTime < 300 && now - lastTapTime > 0) {
    lastTapTime = 0
    emit('double-tap')
  } else {
    lastTapTime = now
    emit('tap')
  }
}

// 暴露方法
const play = () => videoRef.value?.play()
const pause = () => videoRef.value?.pause()
const seek = (time) => { if (videoRef.value) videoRef.value.currentTime = time }
const getVideoElement = () => videoRef.value

defineExpose({ play, pause, seek, getVideoElement, videoRef })
</script>

<style lang="scss" scoped>
.video-slide {
  width: 100%;
  height: 100vh;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
  
  .short-video { width: 100%; height: 100%; object-fit: cover; }
  
  .tap-area {
    position: absolute;
    top: 60px;
    left: 0;
    right: 80px;
    bottom: 150px;
    z-index: 8;
    cursor: pointer;
    touch-action: manipulation;
  }
}

.persistent-pause {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) translateX(3px);
  pointer-events: none;
  z-index: 15;
  svg { width: 80px; height: 80px; filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.4)); }
}

.like-animation {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
  .heart {
    width: 120px;
    height: 120px;
    animation: like-pop 1s ease-out forwards;
    filter: drop-shadow(0 0 20px rgba(254, 44, 85, 0.6));
  }
}

@keyframes like-pop {
  0% { transform: scale(0); opacity: 1; }
  50% { transform: scale(1.2); opacity: 1; }
  100% { transform: scale(1); opacity: 0; }
}

.video-info {
  position: absolute;
  left: 16px;
  right: 80px;
  bottom: 100px;
  z-index: 10;
  
  .vip-tip-bar {
    display: inline-flex;
    align-items: center;
    background: linear-gradient(90deg, rgba(255, 215, 0, 0.85) 0%, rgba(255, 165, 0, 0.85) 100%);
    padding: 4px 10px;
    border-radius: 12px;
    margin-bottom: 8px;
    cursor: pointer;
    .vip-icon { margin-right: 3px; font-size: 11px; }
    .vip-text { font-size: 11px; font-weight: 500; color: #8B4513; }
    .vip-arrow { margin-left: 2px; font-size: 12px; font-weight: bold; color: #8B4513; }
  }
  
  .author-name { font-size: 16px; font-weight: 500; color: #fff; margin-bottom: 15px; }
  .video-title { font-size: 14px; color: #fff; margin-bottom: 6px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .video-desc { font-size: 13px; color: rgba(255,255,255,0.7); display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden; }
}

.progress-bar-container {
  position: absolute;
  left: 12px;
  right: 12px;
  bottom: 20px;
  z-index: 15;
  display: flex;
  flex-direction: column;
  gap: 6px;
  
  .time-display {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.9);
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
    background: rgba(0, 0, 0, 0.3);
    padding: 2px 8px;
    border-radius: 10px;
    align-self: flex-start;
  }
}

.progress-bar {
  position: relative;
  width: 100%;
  height: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  
  &::before {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    height: 4px;
    background: rgba(255, 255, 255, 0.3);
    border-radius: 2px;
  }
  
  .progress {
    position: absolute;
    left: 0;
    height: 4px;
    background: linear-gradient(90deg, #ff6b9d, #ff4757);
    border-radius: 2px;
    pointer-events: none;
  }
  
  .progress-thumb {
    position: absolute;
    top: 50%;
    transform: translate(-50%, -50%);
    width: 16px;
    height: 16px;
    background: #fff;
    border-radius: 50%;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
    pointer-events: none;
  }
}

.trial-countdown {
  position: absolute;
  top: 100px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.7);
  padding: 8px 16px;
  border-radius: 20px;
  z-index: 15;
  .countdown-text { color: #ff6b6b; font-size: 14px; font-weight: 600; }
}

.trial-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.92);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 15;
  backdrop-filter: blur(6px);
  
  .trial-content {
    text-align: center;
    padding: 20px 16px;
    width: 100%;
    max-width: 280px;
    
    h3 { font-size: 14px; font-weight: 600; color: #fff; margin-bottom: 14px; }
    .trial-subtitle { font-size: 14px; color: #fff; margin-bottom: 18px; }
    
    .trial-top-btns {
      display: flex;
      gap: 14px;
      margin-bottom: 12px;
      
      button {
        flex: 1;
        padding: 6px 20px;
        border-radius: 50px;
        border: none;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        white-space: nowrap;
        &:active { transform: scale(0.97); }
      }
      
      .share-btn { background: linear-gradient(90deg, #FF8C00 0%, #FFA500 100%); color: #fff; }
      .vip-btn { background: linear-gradient(90deg, #8B5CF6 0%, #A855F7 100%); color: #fff; }
    }
    
    .trial-divider { font-size: 11px; color: rgba(255, 255, 255, 0.4); margin-bottom: 12px; }
    
    .coin-purchase-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 5px;
      width: 100%;
      padding: 8px 16px;
      border-radius: 20px;
      border: none;
      background: rgba(50, 50, 50, 0.95);
      color: #fff;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      .coin-icon { font-size: 14px; }
      .arrow { font-size: 16px; margin-left: 3px; color: rgba(255, 255, 255, 0.6); }
      &:active { transform: scale(0.97); }
    }
  }
}
</style>
