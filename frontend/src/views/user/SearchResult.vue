<template>
  <div class="search-result-page">
    <!-- 固定顶部区域 -->
    <div class="sticky-top-area">
      <!-- 共享顶部导航 -->
      <SearchHeader 
        current-page="result"
        :show-search-box="true"
        v-model:keyword="keyword"
        placeholder=""
        @search="handleSearch"
      />

      <!-- 分类标签栏 -->
      <div class="category-tabs">
        <span 
          v-for="(cat, index) in categories" 
          :key="cat.key"
          :class="['category-tab', { active: activeCategory === index }]"
          @click="activeCategory = index"
        >
          {{ cat.label }}
        </span>
      </div>
    </div>
    
    <!-- 搜索结果标题 -->
    <div class="result-title">
      <span class="keyword-highlight">{{ keyword }}</span>
      <span class="title-suffix">标签内容</span>
    </div>

    <!-- 视频列表区域 -->
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
        <span>暂无搜索结果</span>
      </div>

      <!-- 视频列表 -->
      <div v-else class="video-list double-column">
        <div 
          v-for="video in videos" 
          :key="video.id"
          class="video-card"
          @click="goToVideo(video.id)"
        >
          <div class="video-cover">
            <img :src="getCoverUrl(video.cover_url)" :alt="video.title"/>
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
              <span class="video-tag">{{ video.tag || '精选' }}</span>
              <span class="video-comments">评论 {{ video.comment_count || 0 }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 查看更多按钮 -->
      <div class="view-more-btn" v-if="videos.length && hasMore" @click="loadMore">
        <span>查看更多</span>
        <span class="arrow">›</span>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '@/utils/api'
import SearchHeader from '@/components/SearchHeader.vue'

const router = useRouter()
const route = useRoute()

const activeTab = ref('search')
const keyword = ref('')
const activeCategory = ref(0)
const loading = ref(false)
const hasMore = ref(true)
const page = ref(1)

// 分类标签
const categories = ref([
  { key: 'video', label: '视频' },
  { key: 'douyin', label: '抖音' },
  { key: 'post', label: '帖子' },
  { key: 'anime', label: '动漫' },
  { key: 'manga', label: '漫画' },
  { key: 'gallery', label: '图集' }
])

// 视频列表
const videos = ref([])

// 获取封面URL
const getCoverUrl = (url) => {
  if (!url) return '/images/default-cover.jpg'
  if (url.startsWith('http')) return url
  return url
}

// 格式化播放量
const formatCount = (count) => {
  if (!count) return '0'
  if (count >= 10000) {
    return (count / 10000).toFixed(1) + 'w'
  }
  return count.toString()
}

// 格式化时长
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

// 跳转到视频
const goToVideo = (id) => {
  router.push(`/user/video/${id}`)
}

// 清除关键词
const clearKeyword = () => {
  keyword.value = ''
}

// 搜索
const handleSearch = async () => {
  if (!keyword.value.trim()) return
  page.value = 1
  await fetchVideos()
}

// 获取视频列表
const fetchVideos = async () => {
  if (!keyword.value.trim()) return
  
  loading.value = true
  try {
    const res = await api.get('/videos', {
      params: {
        search: keyword.value.trim(),
        page: page.value,
        page_size: 20
      }
    })
    const items = (res.data?.items || res.data || []).map(v => ({
      ...v,
      tag: v.category_name || '国产',
      comment_count: v.comment_count || 0
    }))
    
    if (page.value === 1) {
      videos.value = items
    } else {
      videos.value = [...videos.value, ...items]
    }
    
    hasMore.value = items.length >= 20
  } catch (error) {
    console.error('搜索失败:', error)
    if (page.value === 1) {
      videos.value = []
    }
  } finally {
    loading.value = false
  }
}

// 加载更多
const loadMore = async () => {
  page.value++
  await fetchVideos()
}

// 监听路由参数变化
watch(() => route.query.keyword, (newKeyword) => {
  if (newKeyword) {
    keyword.value = newKeyword
    handleSearch()
  }
}, { immediate: true })

onMounted(() => {
  // 从路由获取关键词
  if (route.query.keyword) {
    keyword.value = route.query.keyword
    handleSearch()
  }
})
</script>

<style lang="scss" scoped>
.search-result-page {
  min-height: 100vh;
  min-height: 100dvh;
  background: #0a0a12;
  color: #fff;
  padding-bottom: 20px;
  padding-bottom: calc(20px + env(safe-area-inset-bottom, 0px));
  width: 100%;
  max-width: 100vw;
  overflow-x: clip;
  
  // 平板和桌面限制宽度（与Search.vue保持一致）
  @media (min-width: 768px) {
    max-width: 768px;
    margin: 0 auto;
  }
  
  @media (min-width: 1024px) {
    max-width: 1024px;
  }
  
  @media (min-width: 1440px) {
    max-width: 1200px;
  }
}

// 固定顶部区域
.sticky-top-area {
  position: sticky;
  top: 0;
  z-index: 100;
  background: #0a0a12;
}

// 顶部导航
.page-header {
  display: flex;
  align-items: center;
  padding: 16px;
  background: #0a0a12;
  position: sticky;
  top: 0;
  z-index: 100;
  
  .back-btn {
    font-size: 36px;
    color: #a855f7;
    cursor: pointer;
    font-weight: 400;
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  
  .header-tabs {
    flex: 1;
    display: flex;
    justify-content: center;
    gap: 60px;
    margin-right: 44px;
    
    .tab {
      font-size: 15px;
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
          width: 24px;
          height: 3px;
          background: #a855f7;
          border-radius: 2px;
        }
      }
    }
  }
}

// 搜索框
.search-box {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 16px 8px;
  
  .search-input-wrapper {
    flex: 1;
    max-width: 600px;
    display: flex;
    align-items: center;
    background: #0a0a12;
    border-radius: 22px;
    padding: 0 5px 0 14px;
    height: 44px;
    box-sizing: border-box;
    border: 1px solid #a855f7;
    
    .search-icon {
      width: clamp(16px, 4.5vw, 20px);
      height: clamp(16px, 4.5vw, 20px);
      color: #a855f7;
      margin-right: clamp(6px, 2vw, 10px);
      flex-shrink: 0;
      
      svg {
        width: 100%;
        height: 100%;
      }
    }
    
    input {
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      color: #a855f7;
      font-size: clamp(14px, 3.8vw, 16px);
      padding: clamp(3px, 1vw, 5px) 0;
      
      &::placeholder {
        color: rgba(168, 85, 247, 0.5);
      }
    }
    
    .clear-input {
      width: clamp(20px, 5vw, 26px);
      height: clamp(20px, 5vw, 26px);
      cursor: pointer;
      margin-left: clamp(4px, 1.5vw, 8px);
      margin-right: clamp(18px, 4vw, 28px);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      background: rgba(255, 255, 255, 0.15);
      border-radius: 50%;
      padding: 4px;
      
      svg {
        width: 100%;
        height: 100%;
        color: rgba(255, 255, 255, 0.6);
      }
      
      &:hover {
        background: rgba(255, 255, 255, 0.25);
      }
      
      &:active {
        opacity: 0.7;
      }
    }
    
    .search-btn {
      background: linear-gradient(135deg, #a855f7, #7c3aed);
      border: none;
      color: #fff;
      padding: 0 22px;
      height: 34px !important;
      min-height: 34px !important;
      line-height: 34px;
      border-radius: 17px;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.3s;
      flex-shrink: 0;
      
      &:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.4);
      }
      
      &:active {
        transform: scale(0.98);
      }
    }
  }
}

// 分类标签栏
.category-tabs {
  display: flex;
  gap: 24px;
  padding: 0 16px 16px;
  border-bottom: 1px solid #2a2a3a;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  
  &::-webkit-scrollbar {
    display: none;
  }
  
  .category-tab {
    font-size: 15px;
    color: rgba(255, 255, 255, 0.5);
    white-space: nowrap;
    cursor: pointer;
    position: relative;
    padding-bottom: 8px;
    
    &.active {
      color: #fff;
      font-weight: 600;
      
      &::after {
        content: '';
        position: absolute;
        bottom: -1px;
        left: 0;
        right: 0;
        height: 2px;
        background: #a855f7;
        border-radius: 1px;
      }
    }
  }
}

// 搜索结果标题
.result-title {
  padding: 16px;
  font-size: 16px;
  
  .keyword-highlight {
    color: #a855f7;
    font-weight: 600;
    margin-right: 6px;
  }
  
  .title-suffix {
    color: rgba(255, 255, 255, 0.8);
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
      transition: transform 0.3s ease;
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

// 查看更多按钮
.view-more-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  margin: 16px 0;
  background: #1a1a28;
  border: 1px solid #2a2a3a;
  border-radius: 25px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  cursor: pointer;
  
  .arrow {
    font-size: 18px;
    color: #a855f7;
  }
}
</style>
