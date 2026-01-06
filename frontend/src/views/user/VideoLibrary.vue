<template>
  <div class="video-library-page">
    <!-- 共享顶部导航（固定） -->
    <div class="sticky-header">
      <SearchHeader 
        current-page="library"
        :show-search-box="false"
      />
    </div>

    <!-- 筛选区域 -->
    <div class="filter-section">
      <!-- 分类筛选 -->
      <div class="filter-row">
        <span class="filter-label">分类</span>
        <div class="filter-options">
          <span 
            v-for="item in categoryFilters" 
            :key="item.key"
            :class="['filter-option', { active: activeCategory === item.key }]"
            @click="activeCategory = item.key"
          >
            {{ item.label }}
          </span>
        </div>
      </div>

      <!-- 标签筛选 -->
      <div class="filter-row">
        <span class="filter-label">标签</span>
        <div class="filter-options">
          <span 
            v-for="item in tagFilters" 
            :key="item.key"
            :class="['filter-option', { active: activeTag === item.key }]"
            @click="activeTag = item.key"
          >
            {{ item.label }}
          </span>
        </div>
      </div>

      <!-- 类型筛选 -->
      <div class="filter-row">
        <span class="filter-label">类型</span>
        <div class="filter-options">
          <span 
            v-for="item in typeFilters" 
            :key="item.key"
            :class="['filter-option', { active: activeType === item.key }]"
            @click="activeType = item.key"
          >
            {{ item.label }}
          </span>
        </div>
      </div>

      <!-- 排序筛选 -->
      <div class="filter-row">
        <span class="filter-label">排序</span>
        <div class="filter-options">
          <span 
            v-for="item in sortFilters" 
            :key="item.key"
            :class="['filter-option', { active: activeSort === item.key }]"
            @click="activeSort = item.key"
          >
            {{ item.label }}
          </span>
        </div>
      </div>
    </div>

    <!-- 视频列表 -->
    <div class="video-section">
      <!-- 骨架屏加载状态 -->
      <div v-if="loading && videos.length === 0" class="video-list double-column">
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
      <div v-else class="video-list double-column">
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
      <div class="load-more" v-if="hasMore && !loading && videos.length > 0" @click="loadMore">
        <span>加载更多</span>
      </div>
      
      <!-- 加载中 -->
      <div class="loading-more" v-if="loadingMore">
        <span>加载中...</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import SearchHeader from '@/components/SearchHeader.vue'

const router = useRouter()

const activeTab = ref('library')

// 筛选选项
const categoryFilters = ref([
  { key: 'all', label: '影片' },
  { key: 'douyin', label: '抖音' },
  { key: 'anime', label: '动漫' },
  { key: 'manga', label: '漫画' },
  { key: 'gallery', label: '图集' },
  { key: 'post', label: '帖子' }
])

const tagFilters = ref([
  { key: 'all', label: '全部类型' },
  { key: 'big_breast', label: '巨乳美乳' },
  { key: 'domestic', label: '国产' },
  { key: 'voyeur', label: '偷拍' },
  { key: 'ethics', label: '伦理之爱' }
])

const typeFilters = ref([
  { key: 'all', label: '全部' },
  { key: 'vip', label: 'VIP' },
  { key: 'coin', label: '金币' }
])

const sortFilters = ref([
  { key: 'favorite', label: '最多收藏' },
  { key: 'view', label: '最多观看' },
  { key: 'newest', label: '最新上架' }
])

const activeCategory = ref('all')
const activeTag = ref('all')
const activeType = ref('all')
const activeSort = ref('favorite')

// 视频列表
const videos = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const hasMore = ref(true)
const page = ref(1)
const pageSize = 20

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

// 工具函数
const getCoverUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return url
}

const getPreviewUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return url
}

const formatCount = (count) => {
  if (!count) return '0'
  if (count >= 10000) return (count / 10000).toFixed(1) + 'W'
  if (count >= 1000) return (count / 1000).toFixed(1) + 'K'
  return count.toString()
}

const formatDuration = (seconds) => {
  if (!seconds) return '00:00'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) {
    return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

// 导航
const goToSearch = () => {
  router.push('/user/search')
}

const goToVideo = (id) => {
  router.push(`/user/video/${id}`)
}

// 获取视频
const fetchVideos = async (reset = true) => {
  if (reset) {
    loading.value = true
    page.value = 1
    videos.value = []
  } else {
    loadingMore.value = true
  }

  try {
    const sortMap = {
      'favorite': 'favorite_count',
      'view': 'view_count',
      'newest': 'created_at'
    }

    const params = {
      page: page.value,
      page_size: pageSize,
      sort_by: sortMap[activeSort.value] || 'favorite_count'
    }

    // 添加VIP筛选
    if (activeType.value === 'vip') {
      params.is_vip_only = true
    }

    const res = await api.get('/videos', { params })
    const items = (res.data?.items || res.data || []).map(v => ({
      ...v,
      comment_count: v.comment_count || 0
    }))

    if (reset) {
      videos.value = items
    } else {
      videos.value = [...videos.value, ...items]
    }

    hasMore.value = items.length >= pageSize
  } catch (error) {
    console.error('获取视频失败:', error)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const loadMore = () => {
  if (loadingMore.value || !hasMore.value) return
  page.value++
  fetchVideos(false)
}

// 监听筛选变化
watch([activeCategory, activeTag, activeType, activeSort], () => {
  fetchVideos()
})

onMounted(() => {
  fetchVideos()
})
</script>

<style lang="scss" scoped>
.video-library-page {
  min-height: 100vh;
  min-height: 100dvh;
  background: #0a0a12;
  color: #fff;
  padding-bottom: 20px;
  padding-bottom: calc(20px + env(safe-area-inset-bottom, 0px));
  overflow-x: clip;
}

// 固定顶部导航
.sticky-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: #0a0a12;
}

// 顶部导航
.page-header {
  display: flex;
  align-items: center;
  padding: clamp(12px, 4vw, 20px) clamp(12px, 4vw, 20px);
  background: #0a0a12;
  position: sticky;
  top: 0;
  z-index: 100;
  
  .back-btn {
    font-size: clamp(28px, 8vw, 36px);
    color: #a855f7;
    cursor: pointer;
    font-weight: 400;
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    
    &:active {
      opacity: 0.7;
    }
  }
  
  .header-tabs {
    flex: 1;
    display: flex;
    justify-content: center;
    gap: clamp(40px, 12vw, 80px);
    margin-right: 44px;
    
    .tab {
      font-size: clamp(15px, 4.5vw, 18px);
      color: rgba(255, 255, 255, 0.5);
      cursor: pointer;
      padding-bottom: 8px;
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
          width: clamp(20px, 6vw, 28px);
          height: 3px;
          background: #a855f7;
          border-radius: 2px;
        }
      }
    }
  }
}

// 筛选区域
.filter-section {
  padding: 0 clamp(12px, 4vw, 20px);
  margin-bottom: clamp(10px, 3vw, 16px);
}

.filter-row {
  display: flex;
  align-items: center;
  margin-bottom: clamp(12px, 3vw, 18px);
  
  .filter-label {
    font-size: clamp(14px, 3.5vw, 15px);
    color: #fff;
    font-weight: 500;
    width: clamp(40px, 11vw, 55px);
    flex-shrink: 0;
    line-height: 1.4;
  }
  
  .filter-options {
    flex: 1;
    display: flex;
    flex-wrap: wrap;
    gap: clamp(10px, 3vw, 16px) clamp(16px, 4vw, 24px);
    
    .filter-option {
      font-size: clamp(13px, 3.5vw, 15px);
      color: rgba(255, 255, 255, 0.5);
      cursor: pointer;
      transition: color 0.2s;
      white-space: nowrap;
      
      &:hover {
        color: rgba(255, 255, 255, 0.8);
      }
      
      &.active {
        color: #a855f7;
        font-weight: 500;
      }
    }
  }
}

// 视频区域
.video-section {
  padding: 0 clamp(4px, 1.5vw, 10px);
}

// 视频列表
.video-list {
  display: grid;
  gap: clamp(10px, 3vw, 16px) clamp(6px, 2vw, 12px);
  padding: clamp(6px, 2vw, 12px) clamp(4px, 1.5vw, 10px);
  background: #0a0a0a;
  border-radius: 0 0 clamp(8px, 3vw, 14px) clamp(8px, 3vw, 14px);
  
  &.double-column {
    grid-template-columns: repeat(2, 1fr);
    
    @media (min-width: 768px) {
      grid-template-columns: repeat(3, 1fr);
    }
    
    @media (min-width: 1024px) {
      grid-template-columns: repeat(4, 1fr);
    }
    
    @media (min-width: 1440px) {
      grid-template-columns: repeat(5, 1fr);
    }
  }
}

// 视频卡片
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
    background: #1a1a28;
    
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

// 暂无视频
.empty-videos {
  text-align: center;
  padding: 60px 20px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
}

// 加载更多
.load-more {
  display: flex;
  justify-content: center;
  padding: 20px;
  
  span {
    background: rgba(168, 85, 247, 0.2);
    color: #a855f7;
    padding: 12px 40px;
    border-radius: 25px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.3s;
    
    &:hover {
      background: rgba(168, 85, 247, 0.3);
    }
  }
}

.loading-more {
  text-align: center;
  padding: 20px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
}

// 响应式
@media (min-width: 768px) {
  .video-library-page {
    max-width: 1024px;
    margin: 0 auto;
  }
  
  .filter-row {
    .filter-label {
      width: 60px;
    }
    
    .filter-options {
      gap: 12px 30px;
    }
  }
}

@media (min-width: 1024px) {
  .video-library-page {
    max-width: 1200px;
  }
}
</style>