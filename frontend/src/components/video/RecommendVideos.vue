<template>
  <div class="recommend-section">
    <!-- 推荐标签 -->
    <div class="recommend-tabs" v-if="tabs.length > 0">
      <div 
        v-for="(tab, index) in tabs" 
        :key="index"
        :class="['rec-tab', { active: activeTab === index }]"
        @click="$emit('update:activeTab', index)"
      >
        {{ tab }}
      </div>
    </div>

    <!-- 视频列表 -->
    <div class="video-list double-column">
      <div 
        v-for="video in videos" 
        :key="video.id"
        class="video-card"
        @click="$emit('videoClick', video)"
        @mouseenter="startPreview(video)"
        @mouseleave="stopPreview(video)"
        @touchstart.passive="onTouchStart"
      >
        <div class="video-cover">
          <img 
            :src="getCoverUrl(video.cover_url)" 
            :alt="video.title"
            :class="{ 'hidden': isPreviewPlaying(video.id) }"
          />
          <!-- 视频预览 -->
          <video
            v-if="video.preview_url"
            :ref="el => setPreviewRef(video.id, el)"
            :data-src="getPreviewUrl(video.preview_url)"
            :class="['preview-video', { 'visible': isPreviewPlaying(video.id) }]"
            muted
            loop
            playsinline
            preload="none"
          ></video>
          <div class="cover-views">
            <span class="play-icon">▶</span>
            <span>{{ formatViewCount(video.view_count) }}</span>
          </div>
          <div class="video-duration">{{ formatDuration(video.duration) }}</div>
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
    </div>

    <!-- 加载更多 -->
    <div class="load-more" v-if="hasMore">
      <button @click="$emit('loadMore')" :disabled="loading" class="load-more-btn">
        {{ loading ? '加载中...' : '加载更多' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount } from 'vue'

const props = defineProps({
  videos: { type: Array, default: () => [] },
  tabs: { type: Array, default: () => [] },
  activeTab: { type: Number, default: 0 },
  hasMore: { type: Boolean, default: false },
  loading: { type: Boolean, default: false }
})

defineEmits(['videoClick', 'loadMore', 'update:activeTab'])

// 预览相关
const previewRefs = ref({})
const previewingVideoId = ref(null)
const isTouchMode = ref(false)
let previewTimer = null

const setPreviewRef = (id, el) => {
  if (el) {
    previewRefs.value[id] = el
  }
}

const isPreviewPlaying = (videoId) => {
  return previewingVideoId.value === videoId
}

const getCoverUrl = (url) => {
  if (!url) return '/placeholder.webp'
  return url
}

const getPreviewUrl = (url) => {
  if (!url) return ''
  return url
}

const formatViewCount = (count) => {
  if (!count) return '0'
  if (count >= 10000) return (count / 10000).toFixed(1) + 'w'
  if (count >= 1000) return (count / 1000).toFixed(1) + 'k'
  return count.toString()
}

const formatDuration = (seconds) => {
  if (!seconds) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const startPreview = (video) => {
  if (!video.preview_url || isTouchMode.value) return
  
  if (previewTimer) clearTimeout(previewTimer)
  previewTimer = setTimeout(() => {
    const videoEl = previewRefs.value[video.id]
    if (videoEl) {
      // 懒加载src
      if (!videoEl.src && videoEl.dataset.src) {
        videoEl.src = videoEl.dataset.src
      }
      videoEl.currentTime = 0
      videoEl.play().catch(() => {})
      previewingVideoId.value = video.id
    }
  }, 300)
}

const stopPreview = (video) => {
  if (isTouchMode.value) return
  
  if (previewTimer) {
    clearTimeout(previewTimer)
    previewTimer = null
  }
  
  if (previewingVideoId.value === video.id) {
    const videoEl = previewRefs.value[video.id]
    if (videoEl) {
      videoEl.pause()
      videoEl.currentTime = 0
    }
    previewingVideoId.value = null
  }
}

const onTouchStart = () => {
  isTouchMode.value = true
}

onBeforeUnmount(() => {
  if (previewTimer) clearTimeout(previewTimer)
  Object.values(previewRefs.value).forEach(el => {
    if (el) {
      el.pause()
      el.src = ''
    }
  })
})
</script>

<style lang="scss" scoped>
.recommend-tabs {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  
  &::-webkit-scrollbar {
    display: none;
  }
  
  .rec-tab {
    padding: 8px 16px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.7);
    white-space: nowrap;
    cursor: pointer;
    transition: all 0.2s;
    
    &:hover {
      background: rgba(255, 255, 255, 0.12);
    }
    
    &.active {
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      color: #fff;
    }
  }
}

.video-list {
  display: grid;
  gap: 12px;
  padding: 0 12px 20px;
  
  &.double-column {
    grid-template-columns: repeat(2, 1fr);
  }
}

.video-card {
  cursor: pointer;
  transition: transform 0.2s;
  
  &:hover {
    transform: scale(1.02);
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
    background: #000;
    
    &.visible {
      opacity: 1;
    }
  }
  
  .cover-views {
    position: absolute;
    bottom: 6px;
    left: 6px;
    display: flex;
    align-items: center;
    gap: 3px;
    font-size: 11px;
    color: #fff;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
    
    .play-icon {
      font-size: 9px;
    }
  }
  
  .video-duration {
    position: absolute;
    bottom: 6px;
    right: 6px;
    font-size: 11px;
    color: #fff;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
  }
}

.video-info {
  padding: 8px 2px;
}

.video-title {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 6px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.4;
  min-height: calc(13px * 1.4 * 2);
}

.video-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  
  .video-tag {
    background: linear-gradient(135deg, #a855f7, #7c3aed);
    color: #fff;
    padding: 2px 8px;
    border-radius: 4px;
  }
  
  .video-comments {
    color: rgba(255, 255, 255, 0.5);
  }
}

.load-more {
  padding: 16px;
  text-align: center;
  
  .load-more-btn {
    background: rgba(255, 255, 255, 0.08);
    border: none;
    color: rgba(255, 255, 255, 0.7);
    padding: 10px 24px;
    border-radius: 20px;
    font-size: 13px;
    cursor: pointer;
    
    &:hover:not(:disabled) {
      background: rgba(255, 255, 255, 0.12);
    }
    
    &:disabled {
      opacity: 0.6;
    }
  }
}
</style>
