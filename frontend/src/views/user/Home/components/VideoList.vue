<template>
  <div>
    <!-- 骨架屏 -->
    <div v-if="loading && videos.length === 0" :class="['video-list', gridMode === 1 ? 'single-column' : 'double-column']">
      <div v-for="i in 6" :key="'skeleton-'+i" class="video-card skeleton">
        <div class="video-cover skeleton-cover">
          <div class="skeleton-shimmer"></div>
        </div>
        <div class="video-info">
          <div class="skeleton-title"></div>
          <div class="skeleton-meta"></div>
        </div>
      </div>
    </div>

    <!-- 暂无视频 -->
    <div v-else-if="!loading && videos.length === 0" class="empty-videos">
      <span>暂无视频</span>
    </div>

    <!-- 视频列表 -->
    <div v-else :class="['video-list', gridMode === 1 ? 'single-column' : 'double-column']">
      <div 
        v-for="video in videos" 
        :key="video.id"
        class="video-card"
        @click="$emit('video-click', video)"
        @mouseenter="$emit('preview-start', video)"
        @mouseleave="$emit('preview-stop', video)"
        @touchstart.passive="$emit('touch-start')"
      >
        <div class="video-cover">
          <img 
            :src="getCoverUrl(video.cover_url)" 
            :alt="video.title"
            :class="{ 'hidden': isPreviewPlaying(video.id) }"
          />
          <video
            v-if="video.preview_url"
            :ref="el => $emit('set-preview-ref', video.id, el)"
            :src="getPreviewUrl(video.preview_url)"
            :class="['preview-video', { 'visible': isPreviewPlaying(video.id) }]"
            muted loop playsinline preload="metadata"
          ></video>
          <div class="cover-views">
            <span class="play-icon">▶</span>
            <span>{{ formatCount(video.view_count) }}</span>
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
  </div>
</template>

<script setup>
import { formatCount, formatDuration } from '@/utils/format'

const props = defineProps({
  videos: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  gridMode: { type: Number, default: 2 },
  previewingVideoId: { type: [Number, null], default: null }
})

defineEmits(['video-click', 'preview-start', 'preview-stop', 'touch-start', 'set-preview-ref'])

const getCoverUrl = (url) => {
  if (!url) return '/placeholder.webp'
  return url.startsWith('http') ? url : url
}

const getPreviewUrl = (url) => {
  if (!url) return ''
  return url.startsWith('http') ? url : url
}

const isPreviewPlaying = (videoId) => {
  return props.previewingVideoId === videoId
}
</script>

<style lang="scss" scoped>
$breakpoint-md: 600px;
$breakpoint-lg: 768px;
$breakpoint-xl: 1024px;
$breakpoint-xxl: 1280px;

.video-list {
  display: grid;
  gap: clamp(10px, 3vw, 16px) clamp(6px, 2vw, 12px);
  padding: clamp(6px, 2vw, 12px) clamp(4px, 1.5vw, 10px);
  background: #0a0a0a;
  margin: 0 clamp(4px, 1.5vw, 10px);
  border-radius: 0 0 clamp(8px, 3vw, 14px) clamp(8px, 3vw, 14px);
  
  &.double-column {
    grid-template-columns: repeat(2, 1fr);
    @media (min-width: $breakpoint-md) { grid-template-columns: repeat(3, 1fr); }
    @media (min-width: $breakpoint-xl) { grid-template-columns: repeat(4, 1fr); }
    @media (min-width: $breakpoint-xxl) { grid-template-columns: repeat(5, 1fr); }
    
    .video-card {
      width: 100%;
      min-width: 0;
    }
  }
  
  &.single-column {
    grid-template-columns: 1fr;
    gap: clamp(14px, 4vw, 20px);
    @media (min-width: $breakpoint-md) { grid-template-columns: repeat(2, 1fr); }
    @media (min-width: $breakpoint-xl) { grid-template-columns: repeat(3, 1fr); }
    
    .video-card {
      width: 100%;
      min-width: 0;
      
      .video-cover {
        border-radius: clamp(4px, 1.5vw, 8px);
      }
      
      .video-info {
        .video-title {
          font-size: clamp(13px, 3.5vw, 16px);
          margin-bottom: clamp(6px, 2vw, 10px);
          min-height: calc(clamp(13px, 3.5vw, 16px) * 1.5 * 2);
        }
      }
    }
  }
}

.video-card {
  background: transparent;
  cursor: pointer;
  transition: transform 0.2s;
  width: 100%;
  min-width: 0;
  
  &:hover {
    transform: translateY(-3px);
    .video-cover img { transform: scale(1.03); }
  }
  
  &.skeleton {
    pointer-events: none;
    .skeleton-cover {
      background: rgba(255, 255, 255, 0.05);
      border-radius: 8px;
      aspect-ratio: 16 / 9;
      position: relative;
      overflow: hidden;
    }
    .skeleton-shimmer {
      position: absolute;
      inset: 0;
      background: linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0) 100%);
      animation: shimmer 1.5s infinite;
    }
    .skeleton-title {
      height: 16px;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 4px;
      margin-bottom: 8px;
      width: 80%;
    }
    .skeleton-meta {
      height: 12px;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 4px;
      width: 50%;
    }
  }
  
  .video-cover {
    position: relative;
    width: 100%;
    aspect-ratio: 16/9;
    border-radius: clamp(3px, 1vw, 6px);
    overflow: hidden;
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
      transition: transform 0.3s ease, opacity 0.3s ease;
      &.hidden { opacity: 0; }
    }
    
    .preview-video {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      opacity: 0;
      z-index: 1;
      transition: opacity 0.3s ease;
      pointer-events: none;
      background: #000;
      &.visible { opacity: 1; }
    }
    
    .cover-views {
      position: absolute;
      bottom: clamp(6px, 2vw, 10px);
      left: clamp(6px, 2vw, 10px);
      display: flex;
      align-items: center;
      gap: clamp(2px, 1vw, 5px);
      font-size: clamp(11px, 3vw, 13px);
      color: #fff;
      text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8);
      .play-icon { font-size: clamp(8px, 2.5vw, 11px); }
    }
    
    .video-duration {
      position: absolute;
      bottom: clamp(6px, 2vw, 10px);
      right: clamp(6px, 2vw, 10px);
      font-size: clamp(11px, 3vw, 13px);
      color: #fff;
      text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8);
    }
  }
  
  .video-info {
    padding: clamp(2px, 1vw, 6px) clamp(1px, 0.5vw, 4px);
    
    .video-title {
      font-size: clamp(12px, 3.5vw, 15px);
      color: rgba(255, 255, 255, 0.92);
      margin: 0 0 4px;
      overflow: hidden;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      line-height: 1.5;
      font-weight: 500;
      min-height: calc(clamp(12px, 3.5vw, 15px) * 1.5 * 2);
    }
    
    .video-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .video-tag {
        background: linear-gradient(135deg, #a855f7, #7c3aed);
        color: #fff;
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 500;
      }
      
      .video-comments {
        font-size: 11px;
        color: rgba(255, 255, 255, 0.5);
      }
    }
  }
}

.empty-videos {
  text-align: center;
  padding: clamp(50px, 15vw, 80px) clamp(20px, 5vw, 40px);
  background: #0a0a0a;
  margin: 0 clamp(4px, 1.5vw, 10px);
  color: rgba(255, 255, 255, 0.35);
  font-size: clamp(13px, 3.5vw, 15px);
  border-radius: 0 0 clamp(8px, 3vw, 14px) clamp(8px, 3vw, 14px);
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
</style>
