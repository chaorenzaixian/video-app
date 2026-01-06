<template>
  <div class="category-page">
    <!-- 头部导航 -->
    <header class="page-header">
      <div class="header-left" @click="goBack">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path d="M15 18L9 12L15 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <div class="header-title">{{ categoryInfo.name || '分类' }}</div>
      <div class="header-right"></div>
    </header>
    
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-tabs">
        <span 
          v-for="(filter, index) in sortOptions" 
          :key="filter.key"
          :class="['filter-item', { active: activeSort === index }]"
          @click="changeSort(index)"
        >
          {{ filter.label }}
        </span>
      </div>
      <div class="view-toggle" @click="gridMode = gridMode === 1 ? 2 : 1">
        <span class="toggle-icon" v-if="gridMode === 1">
          <i></i><i></i><i></i>
        </span>
        <span class="toggle-icon grid" v-else>
          <i></i><i></i><i></i><i></i>
        </span>
      </div>
    </div>
    
    <!-- 视频列表 -->
    <div class="video-list-wrapper">
      <!-- 骨架屏加载状态 -->
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
      
      <div v-else-if="!loading && videos.length === 0" class="empty">
        <span>暂无视频</span>
      </div>
      
      <div v-else :class="['video-list', gridMode === 1 ? 'single-column' : 'double-column']">
        <div 
          v-for="video in videos" 
          :key="video.id" 
          class="video-card"
          @click="handleVideoClick(video)"
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
              :src="getPreviewUrl(video.preview_url)"
              :class="['preview-video', { 'visible': isPreviewPlaying(video.id) }]"
              muted
              loop
              playsinline
              preload="metadata"
            ></video>
            <!-- 左下角播放量 -->
            <div class="cover-views">
              <span class="play-icon">▶</span>
              <span>{{ formatCount(video.view_count) }}</span>
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
      </div>
      
      <!-- 加载更多 -->
      <div class="load-more" v-if="hasMore && !loading && videos.length > 0">
        <el-button @click="loadMore" :loading="loadingMore">加载更多</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()

// 分类信息
const categoryInfo = ref({})

// 排序选项
const sortOptions = [
  { label: '最新', key: 'created_at' },
  { label: '最热', key: 'hot' },
  { label: '最多播放', key: 'view_count' }
]
const activeSort = ref(0)

// 视频列表
const videos = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const gridMode = ref(2)
const page = ref(1)
const pageSize = 20
const hasMore = ref(true)

// 预览相关
const previewRefs = ref({})
const previewingVideoId = ref(null)
const isTouchMode = ref(false)

const setPreviewRef = (id, el) => {
  if (el) {
    previewRefs.value[id] = el
  }
}

const isPreviewPlaying = (videoId) => {
  return previewingVideoId.value === videoId
}

const startPreview = (video) => {
  if (isTouchMode.value || !video.preview_url) return
  playPreview(video)
}

const playPreview = (video) => {
  if (previewingVideoId.value && previewingVideoId.value !== video.id) {
    const oldVideoEl = previewRefs.value[previewingVideoId.value]
    if (oldVideoEl) {
      oldVideoEl.pause()
      oldVideoEl.currentTime = 0
    }
  }
  
  previewingVideoId.value = video.id
  const videoEl = previewRefs.value[video.id]
  if (videoEl) {
    videoEl.currentTime = 0
    videoEl.play().catch(() => {
      stopCurrentPreview()
    })
  }
}

const stopPreview = (video) => {
  if (isTouchMode.value) return
  if (previewingVideoId.value === video.id) {
    const videoEl = previewRefs.value[video.id]
    if (videoEl) {
      videoEl.pause()
      videoEl.currentTime = 0
    }
    previewingVideoId.value = null
  }
}

const stopCurrentPreview = () => {
  if (previewingVideoId.value) {
    const videoEl = previewRefs.value[previewingVideoId.value]
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

const handleVideoClick = (video) => {
  if (isTouchMode.value && video.preview_url) {
    if (previewingVideoId.value === video.id) {
      stopCurrentPreview()
      goToVideo(video.id)
    } else {
      playPreview(video)
    }
    return
  }
  goToVideo(video.id)
}

// 获取封面URL
const getCoverUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `${import.meta.env.VITE_API_BASE_URL || ''}${url}`
}

// 获取预览URL
const getPreviewUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `${import.meta.env.VITE_API_BASE_URL || ''}${url}`
}

// 格式化时长
const formatDuration = (seconds) => {
  if (!seconds) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 格式化数量
const formatCount = (count) => {
  if (!count) return '0'
  if (count >= 10000) return (count / 10000).toFixed(1) + 'w'
  if (count >= 1000) return (count / 1000).toFixed(1) + 'k'
  return count.toString()
}

// 返回首页
const goBack = () => {
  router.push('/user')
}

// 跳转到视频详情
const goToVideo = (videoId) => {
  router.push(`/user/video/${videoId}`)
}

// 获取分类信息
const fetchCategoryInfo = async () => {
  try {
    const res = await axios.get('/api/v1/videos/categories')
    const categoryId = parseInt(route.params.id)
    
    // 查找分类信息（包括二级分类）
    const findCategory = (list, id) => {
      for (const cat of list) {
        if (cat.id === id) return cat
        if (cat.children) {
          const found = findCategory(cat.children, id)
          if (found) return found
        }
      }
      return null
    }
    
    const category = findCategory(res.data, categoryId)
    if (category) {
      categoryInfo.value = category
    }
  } catch (e) {
    console.error('获取分类信息失败', e)
  }
}

// 获取视频列表
const fetchVideos = async (reset = true) => {
  if (reset) {
    loading.value = true
    page.value = 1
    videos.value = []
  } else {
    loadingMore.value = true
  }
  
  try {
    const categoryId = parseInt(route.params.id)
    const sortBy = sortOptions[activeSort.value].key
    
    const res = await axios.get('/api/v1/videos', {
      params: {
        category_id: categoryId,
        sort_by: sortBy,
        page: page.value,
        page_size: pageSize
      }
    })
    
    const items = res.data.items || res.data || []
    if (reset) {
      videos.value = items
    } else {
      videos.value.push(...items)
    }
    
    hasMore.value = items.length >= pageSize
  } catch (e) {
    console.error('获取视频列表失败', e)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// 切换排序
const changeSort = (index) => {
  activeSort.value = index
  fetchVideos()
}

// 加载更多
const loadMore = () => {
  page.value++
  fetchVideos(false)
}

// 监听路由参数变化
watch(() => route.params.id, () => {
  if (route.params.id) {
    fetchCategoryInfo()
    fetchVideos()
  }
})

onMounted(() => {
  fetchCategoryInfo()
  fetchVideos()
})
</script>

<style lang="scss" scoped>
.category-page {
  min-height: 100vh;
  background: #0a0a0a;
  color: #fff;
  padding-bottom: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #0a0a0a;
  position: sticky;
  top: 0;
  z-index: 100;
  
  .header-left, .header-right {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    color: rgba(255, 255, 255, 0.8);
  }
  
  .header-title {
    font-size: 18px;
    font-weight: 600;
  }
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  
  .filter-tabs {
    display: flex;
    gap: 24px;
    
    .filter-item {
      font-size: 16px;
      color: rgba(255, 255, 255, 0.5);
      cursor: pointer;
      padding: 6px 0;
      position: relative;
      
      &.active {
        color: #fff;
        font-weight: 600;
        
        &::after {
          content: '';
          position: absolute;
          bottom: 0;
          left: 50%;
          transform: translateX(-50%);
          width: 20px;
          height: 3px;
          background: linear-gradient(90deg, #a855f7, #7c3aed);
          border-radius: 2px;
        }
      }
    }
  }
  
  .view-toggle {
    cursor: pointer;
    padding: 8px;
    
    .toggle-icon {
      display: flex;
      flex-direction: column;
      gap: 3px;
      
      i {
        width: 16px;
        height: 2px;
        background: rgba(255, 255, 255, 0.6);
        border-radius: 1px;
      }
      
      &.grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 2px;
        
        i {
          width: 7px;
          height: 7px;
          border-radius: 1px;
        }
      }
    }
  }
}

.video-list-wrapper {
  padding: 0 clamp(4px, 1.5vw, 10px);
  max-width: 1200px;
  margin: 0 auto;
}

.empty {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px;
  color: rgba(255, 255, 255, 0.5);
}

.video-list {
  display: grid;
  gap: clamp(10px, 3vw, 16px) clamp(6px, 2vw, 12px);
  padding: clamp(6px, 2vw, 12px) clamp(4px, 1.5vw, 10px);
  background: #0a0a0a;
  border-radius: 0 0 clamp(8px, 3vw, 14px) clamp(8px, 3vw, 14px);
  
  &.double-column {
    grid-template-columns: repeat(2, 1fr);
    
    @media (min-width: 600px) {
      grid-template-columns: repeat(3, 1fr);
    }
    
    @media (min-width: 768px) {
      grid-template-columns: repeat(3, 1fr);
    }
    
    @media (min-width: 1024px) {
      grid-template-columns: repeat(4, 1fr);
    }
    
    @media (min-width: 1280px) {
      grid-template-columns: repeat(5, 1fr);
    }
    
    @media (min-width: 1920px) {
      grid-template-columns: repeat(6, 1fr);
      gap: 20px;
    }
    
    @media (min-width: 2560px) {
      grid-template-columns: repeat(7, 1fr);
      gap: 24px;
    }
    
    .video-card {
      width: 100%;
      min-width: 0;
    }
  }
  
  &.single-column {
    grid-template-columns: 1fr;
    gap: clamp(14px, 4vw, 20px);
    
    @media (min-width: 600px) {
      grid-template-columns: repeat(2, 1fr);
    }
    
    @media (min-width: 1024px) {
      grid-template-columns: repeat(3, 1fr);
    }
    
    @media (min-width: 1920px) {
      grid-template-columns: repeat(4, 1fr);
    }
    
    @media (min-width: 2560px) {
      grid-template-columns: repeat(5, 1fr);
    }
    
    .video-card {
      .video-cover {
        border-radius: clamp(4px, 1.5vw, 8px);
      }
      
      .video-info {
        padding: clamp(2px, 1vw, 6px) clamp(1px, 0.5vw, 4px);
        text-align: left;
        
        .video-title {
          font-size: clamp(13px, 3.5vw, 16px);
          -webkit-line-clamp: 2;
          margin-bottom: clamp(6px, 2vw, 10px);
          line-height: 1.5;
          letter-spacing: 0.5px;
          min-height: calc(clamp(13px, 3.5vw, 16px) * 1.5 * 2);
          text-align: left;
        }
      }
    }
  }
}

.video-card {
  background: transparent;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  width: 100%;
  min-width: 0;
  
  &:hover {
    transform: translateY(-3px);
    
    .video-cover img {
      transform: scale(1.03);
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
      
      &.hidden {
        opacity: 0;
      }
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
      
      &.visible {
        opacity: 1;
      }
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
      
      .play-icon {
        font-size: clamp(8px, 2.5vw, 11px);
      }
    }
    
    .video-duration {
      position: absolute;
      bottom: clamp(6px, 2vw, 10px);
      right: clamp(6px, 2vw, 10px);
      font-size: clamp(11px, 3vw, 13px);
      color: #fff;
      text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8);
    }
    
    .vip-tag {
      position: absolute;
      top: clamp(6px, 2vw, 10px);
      left: clamp(6px, 2vw, 10px);
      background: linear-gradient(135deg, #ffcc00, #ff9500);
      color: #000;
      padding: clamp(2px, 0.8vw, 4px) clamp(8px, 2.5vw, 12px);
      border-radius: clamp(3px, 1vw, 5px);
      font-size: clamp(9px, 2.5vw, 11px);
      font-weight: bold;
      box-shadow: 0 2px 8px rgba(255, 204, 0, 0.3);
    }
  }
  
  .video-info {
    padding: clamp(2px, 1vw, 6px) clamp(1px, 0.5vw, 4px);
    text-align: left;
    
    .video-title {
      font-size: clamp(12px, 3.5vw, 15px);
      color: rgba(255, 255, 255, 0.92);
      margin: 0 0 4px;
      overflow: hidden;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      line-height: 1.5;
      letter-spacing: 0.5px;
      font-weight: 500;
      min-height: calc(clamp(12px, 3.5vw, 15px) * 1.5 * 2);
      text-align: left;
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

// 骨架屏
.skeleton {
  .skeleton-cover {
    position: relative;
    overflow: hidden;
    background: #1a1a28;
    
    .skeleton-shimmer {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: linear-gradient(90deg, #1a1a28 25%, #252538 50%, #1a1a28 75%);
      background-size: 200% 100%;
      animation: shimmer 1.5s infinite;
    }
  }
  
  .skeleton-title {
    height: 14px;
    background: #1a1a28;
    border-radius: 4px;
    margin-bottom: 8px;
  }
  
  .skeleton-meta {
    height: 12px;
    width: 60%;
    background: #1a1a28;
    border-radius: 4px;
  }
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.load-more {
  display: flex;
  justify-content: center;
  padding: 20px;
  
  :deep(.el-button) {
    background: rgba(255, 255, 255, 0.1);
    border: none;
    color: #fff;
    
    &:hover {
      background: rgba(255, 255, 255, 0.2);
    }
  }
}

// ============ 响应式适配 ============
@media (min-width: 768px) {
  .category-page {
    max-width: 900px;
    margin: 0 auto;
  }
}

@media (min-width: 1280px) {
  .category-page {
    max-width: 1200px;
  }
}

@media (min-width: 1920px) {
  .category-page {
    max-width: 1400px;
  }
  
  .category-header h2 {
    font-size: 24px;
  }
}

@media (min-width: 2560px) {
  .category-page {
    max-width: 1800px;
  }
  
  .category-header h2 {
    font-size: 28px;
  }
}

// 触摸设备优化
@media (hover: none) and (pointer: coarse) {
  .video-card {
    &:hover {
      transform: none !important;
      
      .video-cover img {
        transform: none !important;
      }
    }
    
    &:active {
      transform: scale(0.98);
      opacity: 0.9;
    }
  }
  
  .filter-item:hover,
  .cat-item:hover {
    opacity: 1 !important;
    transform: none !important;
  }
  
  .filter-item:active,
  .cat-item:active {
    opacity: 0.7;
  }
}

// 横屏优化
@media (orientation: landscape) and (max-height: 500px) {
  .category-header {
    padding: 8px 12px;
  }
}
</style>