<template>
  <div 
    class="video-card"
    @click="$emit('click', video)"
    @mouseenter="startPreview"
    @mouseleave="stopPreview"
    @touchstart.passive="onTouchStart"
  >
    <div class="video-cover">
      <img 
        :src="coverUrl" 
        :alt="video.title"
        :class="{ 'hidden': isPreviewPlaying }"
        loading="lazy"
      />
      
      <!-- 视频预览 -->
      <video
        v-if="video.preview_url && shouldLoadPreview"
        ref="previewRef"
        :src="previewUrl"
        :class="['preview-video', { 'visible': isPreviewPlaying }]"
        muted
        loop
        playsinline
        preload="none"
      ></video>
      
      <!-- 左下角播放量 -->
      <div class="cover-views">
        <span class="play-icon">▶</span>
        <span>{{ formatViewCount(video.view_count) }}</span>
      </div>
      
      <!-- 右下角时长 -->
      <div class="video-duration">{{ formatDuration(video.duration) }}</div>
      
      <!-- VIP标签 -->
      <div v-if="video.is_vip_only" class="vip-tag">VIP</div>
    </div>
    
    <div class="video-info">
      <p class="video-title">{{ video.title }}</p>
      <div class="video-meta">
        <span class="video-tag" v-if="video.tags && video.tags.length > 0">{{ video.tags[0] }}</span>
        <span class="video-tag" v-else-if="video.category_name">{{ video.category_name }}</span>
        <span class="video-tag" v-else>精选</span>
        <span class="video-comments">评论 {{ video.comment_count || 0 }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import { formatViewCount, formatDuration } from '@/utils/format'

const props = defineProps({
  video: {
    type: Object,
    required: true
  },
  enablePreview: {
    type: Boolean,
    default: true
  }
})

defineEmits(['click'])

const previewRef = ref(null)
const isPreviewPlaying = ref(false)
const shouldLoadPreview = ref(false)
const isTouchMode = ref(false)
let previewTimer = null

// 封面URL
const coverUrl = computed(() => {
  const url = props.video.cover_url
  if (!url) return '/placeholder.webp'
  if (url.startsWith('http')) return url
  return url
})

// 预览URL
const previewUrl = computed(() => {
  const url = props.video.preview_url
  if (!url) return ''
  if (url.startsWith('http')) return url
  return url
})

// 开始预览（PC端）
const startPreview = () => {
  if (!props.enablePreview || !props.video.preview_url || isTouchMode.value) return
  
  shouldLoadPreview.value = true
  
  if (previewTimer) clearTimeout(previewTimer)
  previewTimer = setTimeout(() => {
    if (previewRef.value) {
      previewRef.value.currentTime = 0
      previewRef.value.play().catch(() => {})
      isPreviewPlaying.value = true
    }
  }, 300)
}

// 停止预览（PC端）
const stopPreview = () => {
  if (isTouchMode.value) return
  
  if (previewTimer) {
    clearTimeout(previewTimer)
    previewTimer = null
  }
  
  if (previewRef.value) {
    previewRef.value.pause()
    previewRef.value.currentTime = 0
  }
  isPreviewPlaying.value = false
}

// 触摸开始（移动端）
const onTouchStart = () => {
  isTouchMode.value = true
}

onBeforeUnmount(() => {
  if (previewTimer) {
    clearTimeout(previewTimer)
  }
  if (previewRef.value) {
    previewRef.value.pause()
    previewRef.value.src = ''
  }
})
</script>

<style lang="scss" scoped>
.video-card {
  cursor: pointer;
  transition: transform 0.2s;
  
  &:hover {
    transform: scale(1.02);
  }
  
  &:active {
    transform: scale(0.98);
  }
}

.video-cover {
  position: relative;
  aspect-ratio: 16/9;
  border-radius: 8px;
  overflow: hidden;
  background: #1a1a1a;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: opacity 0.3s;
    
    &.hidden {
      opacity: 0;
    }
  }
  
  .preview-video {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    opacity: 0;
    transition: opacity 0.3s;
    
    &.visible {
      opacity: 1;
    }
  }
}

.cover-views {
  position: absolute;
  bottom: 8px;
  left: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(0, 0, 0, 0.6);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #fff;
  
  .play-icon {
    font-size: 10px;
  }
}

.video-duration {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.6);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  color: #fff;
}

.vip-tag {
  position: absolute;
  top: 8px;
  right: 8px;
  background: linear-gradient(135deg, #ffd700, #ffb700);
  color: #000;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.video-info {
  padding: 8px 4px;
}

.video-title {
  font-size: 14px;
  color: #fff;
  margin: 0 0 6px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.4;
}

.video-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  
  .video-tag {
    background: rgba(139, 92, 246, 0.2);
    color: #a78bfa;
    padding: 2px 8px;
    border-radius: 4px;
  }
}
</style>
