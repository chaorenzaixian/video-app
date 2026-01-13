<template>
  <div class="search-page">
    <!-- 顶部固定区域（导航+搜索框） -->
    <div class="sticky-top-area" ref="stickyTopRef">
      <!-- 使用共享的 SearchHeader 组件（包含搜索框） -->
      <SearchHeader 
        current-page="search"
        :show-search-box="true"
        v-model:keyword="keyword"
        :placeholder="hotSearches[0] || '搜索'"
        @search="handleSearch"
      />
    </div>

    <!-- 广告位 - 只在有API数据时显示 -->
    <div class="ad-section" v-if="adRow1.length > 0 && adRow1.some(item => !item._imgError)">
        <div class="ad-row">
          <div 
            class="ad-item" 
            v-for="item in adRow1" 
            :key="item.id"
            :class="{ hidden: item._imgError }"
            @click="handleAdClick(item)"
          >
            <div class="ad-img">
              <img :src="item.image" @error="item._imgError = true" />
            </div>
            <span class="ad-name">{{ item.name }}</span>
          </div>
        </div>
        <div class="ad-row-scroll" v-if="adRow2.length > 0 && adRow2.some(item => !item._imgError)">
          <div class="scroll-track">
            <div class="scroll-content">
              <div 
                class="ad-item" 
                v-for="item in adRow2" 
                :key="'a-' + item.id"
                :class="{ hidden: item._imgError }"
                @click="handleAdClick(item)"
              >
                <div class="ad-img">
                  <img :src="item.image" @error="item._imgError = true" />
                </div>
                <span class="ad-name">{{ item.name }}</span>
              </div>
              <div 
                class="ad-item" 
                v-for="item in adRow2" 
                :key="'b-' + item.id"
                :class="{ hidden: item._imgError }"
                @click="handleAdClick(item)"
              >
                <div class="ad-img">
                  <img :src="item.image" @error="item._imgError = true" />
                </div>
              <span class="ad-name">{{ item.name }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 搜索记录 -->
    <div class="search-history-section" v-if="searchHistory.length > 0">
      <div class="section-header">
        <h3 class="section-title">搜索记录</h3>
        <div class="clear-btn" @click="clearSearchHistory">
          <img src="/images/backgrounds/ic_search_clear.webp" alt="清除" class="clear-icon" />
        </div>
      </div>
      <div class="history-tags">
        <span 
          class="history-tag" 
          v-for="(item, index) in searchHistory" 
          :key="index"
          @click="searchKeyword(item)"
        >
          {{ item }}
        </span>
      </div>
    </div>

    <!-- 热门搜索 -->
    <div class="hot-search-section">
      <h3 class="section-title">
        <span class="title-bar"></span>
        热门搜索
      </h3>
      <div class="hot-list">
        <div 
          class="hot-item" 
          v-for="(item, index) in hotSearches" 
          :key="index"
          @click="searchKeyword(item)"
        >
          <span :class="['rank', `rank-${index + 1}`]">
            <img v-if="index === 0" src="/images/backgrounds/hot_1.webp" alt="1" class="rank-icon" />
            <img v-else-if="index === 1" src="/images/backgrounds/hot_2.webp" alt="2" class="rank-icon" />
            <img v-else-if="index === 2" src="/images/backgrounds/hot_3.webp" alt="3" class="rank-icon" />
            <template v-else>{{ index + 1 }}</template>
          </span>
          <span class="keyword">{{ item }}</span>
        </div>
      </div>
    </div>

    <!-- 筛选栏和视频列表 - 只在有视频数据时显示 -->
    <template v-if="videos.length > 0">
      <div class="filter-bar" :style="{ top: filterBarTop + 'px' }">
        <div class="filter-tabs">
          <span 
            v-for="(filter, index) in filters" 
            :key="filter.key"
            :class="['filter-item', { active: activeFilter === index }]"
            @click="changeFilter(index)"
          >
            {{ filter.label }}
          </span>
        </div>
        <div class="view-toggle" @click="gridMode = gridMode === 1 ? 2 : 1">
          <span class="toggle-label">切换</span>
          <span class="toggle-icon" v-if="gridMode === 1">
            <i></i><i></i><i></i>
          </span>
          <span class="toggle-icon grid" v-else>
            <i></i><i></i><i></i><i></i>
          </span>
        </div>
      </div>

      <div class="video-section">
        <div :class="['video-list', gridMode === 1 ? 'single-column' : 'double-column']">
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
              <div class="cover-views">
                <span class="play-icon">▶</span>
                <span>{{ formatCount(video.view_count) }}</span>
              </div>
              <div class="video-duration">{{ formatDuration(video.duration) }}</div>
              <div v-if="video.is_vip_only" class="vip-tag">VIP</div>
            </div>
            <div class="video-info">
              <p class="video-title">{{ video.title }}</p>
              <div class="video-meta">
                <span class="video-tag" v-if="video.tags && video.tags.length > 0">{{ video.tags[0] }}</span>
                <span class="video-tag" v-else-if="video.category_name">{{ video.category_name }}</span>
                <span class="video-tag" v-else-if="video.tag">{{ video.tag }}</span>
                <span class="video-tag" v-else>精选</span>
                <span class="video-comments">评论 {{ video.comment_count || 0 }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="load-more" v-if="hasMore && videos.length" @click="loadMore">
          加载更多
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import SearchHeader from '@/components/SearchHeader.vue'

// 顶部固定区域引用
const stickyTopRef = ref(null)
// 筛选栏的 top 值
const filterBarTop = ref(118)

const router = useRouter()

const activeTab = ref('search')
const keyword = ref('')
const activeFilter = ref(0)
const hasMore = ref(true)
const gridMode = ref(2) // 1=单列, 2=双列

// 预览视频引用
const previewRefs = ref({})
// 当前正在预览的视频ID
const previewingVideoId = ref(null)
let previewTimer = null
// 触摸模式（首次触摸时启用）
const isTouchMode = ref(false)

const setPreviewRef = (id, el) => {
  if (el) {
    previewRefs.value[id] = el
  }
}

// 检查视频是否正在预览
const isPreviewPlaying = (videoId) => {
  return previewingVideoId.value === videoId
}

// 播放预览
const playPreview = (video) => {
  // 停止其他预览
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
    videoEl.play().catch(err => {
      console.log('预览播放失败:', err)
    })
  }
}

// 停止预览
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

// 开始预览 (PC鼠标悬停)
const startPreview = (video) => {
  if (!video.preview_url || isTouchMode.value) return
  
  previewingVideoId.value = video.id
  
  if (previewTimer) clearTimeout(previewTimer)
  previewTimer = setTimeout(() => {
    if (previewingVideoId.value === video.id) {
      playPreview(video)
    }
  }, 300)
}

// 停止预览 (PC鼠标离开)
const stopPreview = (video) => {
  if (isTouchMode.value) return
  
  if (previewTimer) {
    clearTimeout(previewTimer)
    previewTimer = null
  }
  
  if (previewingVideoId.value === video.id) {
    previewingVideoId.value = null
    const videoEl = previewRefs.value[video.id]
    if (videoEl) {
      videoEl.pause()
      videoEl.currentTime = 0
    }
  }
}

// 触摸开始时启用触摸模式
const onTouchStart = () => {
  isTouchMode.value = true
}

// 视频卡片点击处理
const handleVideoClick = (video) => {
  // 触摸模式：第一次点击预览，第二次进入视频
  if (isTouchMode.value && video.preview_url) {
    if (previewingVideoId.value === video.id) {
      // 正在预览，进入视频
      stopCurrentPreview()
      goToVideo(video.id)
    } else {
      // 开始预览
      playPreview(video)
    }
    return
  }
  
  // PC模式：直接进入视频
  goToVideo(video.id)
}

// 获取预览视频URL
const getPreviewUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return url
}

// 搜索记录
const searchHistory = ref([])
const SEARCH_HISTORY_KEY = 'video_search_history'
const MAX_HISTORY_COUNT = 20

// 加载搜索记录
const loadSearchHistory = () => {
  try {
    const history = localStorage.getItem(SEARCH_HISTORY_KEY)
    if (history) {
      searchHistory.value = JSON.parse(history)
    }
  } catch (e) {
    searchHistory.value = []
  }
}

// 保存搜索记录
const saveSearchHistory = (kw) => {
  if (!kw || !kw.trim()) return
  const trimmedKw = kw.trim()
  // 移除已存在的相同关键词
  const filtered = searchHistory.value.filter(item => item !== trimmedKw)
  // 添加到开头
  filtered.unshift(trimmedKw)
  // 限制数量
  searchHistory.value = filtered.slice(0, MAX_HISTORY_COUNT)
  // 保存到 localStorage
  try {
    localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(searchHistory.value))
  } catch (e) {
    console.error('保存搜索记录失败')
  }
}

// 清除搜索记录
const clearSearchHistory = () => {
  searchHistory.value = []
  try {
    localStorage.removeItem(SEARCH_HISTORY_KEY)
  } catch (e) {
    console.error('清除搜索记录失败')
  }
}

// 广告位数据（从后端获取，与首页共用）
const adRow1 = ref([])
const adRow2 = ref([])

// 获取广告位数据
const fetchAds = async () => {
  try {
    const res = await api.get('/ads/icons')
    if (res.data && res.data.length > 0) {
      adRow1.value = res.data.slice(0, 5)
      adRow2.value = res.data.slice(5)
    }
  } catch (error) {
    // API失败时不显示广告，保持空数组
    console.log('获取广告失败')
  }
}

// 广告点击
const handleAdClick = (item) => {
  if (item.link && item.link !== '#') {
    window.open(item.link, '_blank')
  }
}

const hotSearches = ref([
  '制服', '学生', '萝莉', '少女', '白虎', '巨乳', '乱伦', '调教', '口交', '内射'
])

const filters = ref([
  { key: 'week', label: '本周最热' },
  { key: 'month', label: '本月最热' },
  { key: 'lastMonth', label: '上月最热' }
])

const videos = ref([])
const loading = ref(false)

const fetchVideos = async () => {
  loading.value = true
  try {
    // 根据筛选条件获取视频
    const filterKey = filters.value[activeFilter.value].key
    const res = await api.get('/videos', { 
      params: { 
        page: 1, 
        page_size: 20,
        sort_by: 'view_count',
        time_range: filterKey
      } 
    })
    videos.value = (res.data?.items || res?.items || []).map(v => ({
      ...v,
      tag: v.category_name || '国产',
      comment_count: v.comment_count || Math.floor(Math.random() * 10),
      is_hot: v.view_count > 100000
    }))
  } catch (error) {
    // API失败时不显示视频，保持空数组
    console.log('获取视频失败')
  } finally {
    loading.value = false
  }
}

// 切换筛选条件
const changeFilter = (index) => {
  if (activeFilter.value !== index) {
    activeFilter.value = index
    fetchVideos()
  }
}

const handleSearch = () => {
  if (!keyword.value.trim()) return
  
  // 保存搜索记录
  saveSearchHistory(keyword.value)
  
  // 跳转到搜索结果页面
  router.push({
    path: '/user/search-result',
    query: { keyword: keyword.value.trim() }
  })
}

const searchKeyword = (kw) => {
  keyword.value = kw
  handleSearch()
}


const goToVideo = (id) => {
  router.push(`/user/video/${id}`)
}

const goToLibrary = () => {
  router.push('/user/video-library')
}

const loadMore = () => {
  // 加载更多逻辑
}

const getCoverUrl = (url) => {
  if (!url) return '/placeholder.webp'
  return url.startsWith('/') ? url : '/' + url
}

const formatDuration = (seconds) => {
  if (!seconds) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

const formatCount = (count) => {
  if (!count) return '0'
  if (count >= 10000) return (count / 10000).toFixed(1) + 'W'
  return count.toString()
}

// 计算筛选栏的 top 值
const updateFilterBarTop = () => {
  if (stickyTopRef.value) {
    filterBarTop.value = stickyTopRef.value.offsetHeight -2 // 减1px消除缝隙
  }
}

onMounted(() => {
  loadSearchHistory()
  fetchAds()
  fetchVideos()
  // 自动填入热门搜索第一个关键词
  if (hotSearches.value.length > 0) {
    keyword.value = hotSearches.value[0]
  }
  // 计算顶部区域高度
  nextTick(() => {
    updateFilterBarTop()
  })
  // 监听窗口大小变化
  window.addEventListener('resize', updateFilterBarTop)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateFilterBarTop)
})
</script>

<style lang="scss" scoped>
.search-page {
  min-height: 100vh;
  min-height: 100dvh;
  background: #0a0a12;
  color: #fff;
  padding-bottom: 20px;
  padding-bottom: calc(20px + env(safe-area-inset-bottom, 0px));
  width: 100%;
  max-width: 100vw;
  overflow-x: clip;
}

// 固定顶部区域容器
// 顶部固定区域（导航+搜索框）
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
    
    &:active {
      opacity: 0.7;
    }
  }
  
  .header-tabs {
    flex: 1;
    display: flex;
    justify-content: center;
    gap: 60px;
    margin-right: 44px; // 宽度平衡，使标签居中
    
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


// 广告位公共样式
.ad-item {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 68px;
  cursor: pointer;
  transition: transform 0.2s;
  
  &.hidden {
    display: none;
  }
  
  &:active {
    transform: scale(0.95);
  }
  
  .ad-img {
    width: 60px;
    height: 60px;
    border-radius: 14px;
    display: flex;
    justify-content: center;
    align-items: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    
    .ad-icon {
      font-size: 24px;
    }
    
    .ad-badge {
      position: absolute;
      top: 3px;
      left: 3px;
      right: 3px;
      font-size: 8px;
      padding: 2px 4px;
      border-radius: 4px;
      text-align: center;
      background: rgba(0, 0, 0, 0.7);
      backdrop-filter: blur(4px);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      
      &.hot { background: rgba(255, 55, 95, 0.9); }
      &.purple { background: rgba(139, 92, 246, 0.9); }
      &.gold { background: rgba(255, 204, 0, 0.95); color: #000; }
      &.blue { background: rgba(59, 130, 246, 0.9); }
      &.pink { background: rgba(236, 72, 153, 0.9); }
      &.cyan { background: rgba(6, 182, 212, 0.9); }
      &.red { background: rgba(239, 68, 68, 0.9); }
      &.orange { background: rgba(249, 115, 22, 0.9); }
    }
  }
  
  .ad-name {
    margin-top: 6px;
    font-size: 11px;
    color: rgba(255, 255, 255, 0.85);
    text-align: center;
    white-space: nowrap;
  }
}

// 广告位区域
.ad-section {
  padding: 8px 10px 16px;
  
  // 第一行固定居中
  .ad-row {
    display: flex;
    justify-content: center;
    gap: 8px;
    margin-bottom: 10px;
  }
  
  // 第二行自动滚动
  .ad-row-scroll {
    overflow: hidden;
    position: relative;
    
    &::before,
    &::after {
      content: '';
      position: absolute;
      top: 0;
      bottom: 0;
      width: 20px;
      z-index: 2;
      pointer-events: none;
    }
    
    &::before {
      left: 0;
      background: linear-gradient(to right, #0a0a12, transparent);
    }
    
    &::after {
      right: 0;
      background: linear-gradient(to left, #0a0a12, transparent);
    }
    
    .scroll-track {
      overflow: hidden;
    }
    
    .scroll-content {
      display: flex;
      gap: 10px;
      padding: 4px 0;
      animation: scrollLoop 20s linear infinite;
      width: fit-content;
      
      &:hover {
        animation-play-state: paused;
      }
    }
  }
}

@keyframes scrollLoop {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(-50%);
  }
}

// 搜索记录
.search-history-section {
  background: #12121c;
  margin: 0 12px 16px;
  border-radius: 12px;
  padding: 16px;
  
  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 14px;
    
    .section-title {
      font-size: 16px;
      font-weight: 600;
      margin: 0;
      color: #fff;
    }
    
    .clear-btn {
      width: 24px;
      height: 24px;
      cursor: pointer;
      transition: opacity 0.2s;
      
      &:hover {
        opacity: 0.8;
      }
      
      .clear-icon {
        width: 100%;
        height: 100%;
        object-fit: contain;
      }
    }
  }
  
  .history-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    
    .history-tag {
      background: #1e1e2e;
      color: rgba(255, 255, 255, 0.8);
      padding: 8px 16px;
      border-radius: 20px;
      font-size: 14px;
      cursor: pointer;
      transition: all 0.2s;
      border: 1px solid #2a2a3a;
      
      &:hover {
        background: #2a2a3a;
        color: #fff;
      }
      
      &:active {
        transform: scale(0.95);
      }
    }
  }
}

// 热门搜索
.hot-search-section {
  background-image: url("/images/backgrounds/search_rank_bg.webp");
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  margin: 0 12px 12px;
  border-radius: 12px;
  padding: 14px 16px;
  
  .section-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 600;
    margin: 0 0 12px;
    
    .title-bar {
      width: 4px;
      height: 18px;
      background: #a855f7;
      border-radius: 2px;
    }
  }
  
  .hot-list {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px 16px;
    
    .hot-item {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      padding: 2px 0;
      
      &:hover .keyword {
        color: #a855f7;
      }
      
      .rank {
        min-width: 24px;
        font-size: 15px;
        font-weight: bold;
        display: flex;
        align-items: center;
        justify-content: center;
        
        .rank-icon {
          width: 22px;
          height: 22px;
          object-fit: contain;
        }
        
        &.rank-1, &.rank-2, &.rank-3 {
          font-size: 18px;
        }
        
        &:not(.rank-1):not(.rank-2):not(.rank-3) {
          color: #a855f7;
        }
      }
      
      .keyword {
        font-size: 14px;
        color: rgba(255, 255, 255, 0.85);
        transition: color 0.2s;
      }
    }
  }
}

// 视频列表区域
.video-section {
  background: #0a0a0a;
  margin: 0 clamp(4px, 1.5vw, 10px);
  margin-top: 0;
  border-radius: 0 0 clamp(8px, 3vw, 14px) clamp(8px, 3vw, 14px); // 只保留底部圆角
  overflow: clip;
}

// 筛选栏
// 筛选栏 - 固定在导航+搜索框下方（top值由JS动态计算）
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: clamp(8px, 2.5vw, 14px) clamp(12px, 3vw, 16px);
  background: #0a0a0a;
  border-radius: clamp(8px, 3vw, 14px) clamp(8px, 3vw, 14px) 0 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  margin: 0 clamp(4px, 1.5vw, 10px);
  margin-bottom: 0;
  position: sticky;
  // top 值由 JavaScript 动态设置
  z-index: 50;
  
  .filter-tabs {
    display: flex;
    align-items: center;
    gap: clamp(10px, 3vw, 24px);
    flex-shrink: 0;
    
    .filter-item {
      font-size: clamp(12px, 3.5vw, 15px);
      color: rgba(255, 255, 255, 0.5);
      cursor: pointer;
      transition: all 0.2s;
      padding: clamp(4px, 1.5vw, 8px) 0;
      position: relative;
      white-space: nowrap;
      
      &:hover {
        color: rgba(255, 255, 255, 0.8);
      }
      
      &.active {
        color: #fff;
        font-weight: 600;
        
        &::after {
          content: '';
          position: absolute;
          bottom: 0;
          left: 0;
          right: 0;
          height: 2px;
          background: linear-gradient(90deg, #a855f7, #7c3aed);
          border-radius: 1px;
        }
      }
    }
  }
  
  // 切换按钮
  .view-toggle {
    display: flex;
    align-items: center;
    gap: clamp(3px, 1vw, 6px);
    cursor: pointer;
    padding: clamp(3px, 1vw, 6px) clamp(5px, 1.5vw, 10px);
    border-radius: clamp(3px, 1vw, 5px);
    transition: all 0.2s;
    flex-shrink: 0;
    
    &:hover {
      background: rgba(255, 255, 255, 0.08);
    }
    
    .toggle-label {
      font-size: clamp(11px, 3vw, 14px);
      color: rgba(255, 255, 255, 0.7);
    }
    
    .toggle-icon {
      display: flex;
      flex-direction: column;
      gap: 2px;
      width: clamp(14px, 4vw, 20px);
      height: clamp(14px, 4vw, 20px);
      justify-content: center;
      align-items: center;
      
      i {
        width: clamp(12px, 4vw, 18px);
        height: 2px;
        background: rgba(255, 255, 255, 0.8);
        border-radius: 1px;
      }
      
      &.grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: clamp(2px, 0.8vw, 4px);
        
        i {
          width: clamp(5px, 1.5vw, 8px);
          height: clamp(5px, 1.5vw, 8px);
          border-radius: 1px;
        }
      }
    }
  }
}

// 骨架屏加载效果
.video-card.skeleton {
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
    background: linear-gradient(
      90deg,
      rgba(255, 255, 255, 0) 0%,
      rgba(255, 255, 255, 0.08) 50%,
      rgba(255, 255, 255, 0) 100%
    );
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

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

// 暂无视频
.empty-videos {
  text-align: center;
  padding: clamp(50px, 15vw, 80px) clamp(20px, 5vw, 40px);
  background: #0a0a0a;
  color: rgba(255, 255, 255, 0.35);
  font-size: clamp(13px, 3.5vw, 15px);
}

// 视频列表
.video-list {
  display: grid;
  gap: clamp(10px, 3vw, 16px) clamp(6px, 2vw, 12px);
  padding: clamp(6px, 2vw, 12px) clamp(4px, 1.5vw, 10px);
  background: #0a0a0a;
  
  // 双列模式（默认）
  &.double-column {
    grid-template-columns: repeat(2, 1fr);
  }
  
  // 单列模式
  &.single-column {
    grid-template-columns: 1fr;
    gap: clamp(14px, 4vw, 20px);
    
    .video-card {
      .video-cover {
        border-radius: clamp(4px, 1.5vw, 8px);
      }
      
      .video-info {
        .video-title {
          font-size: clamp(13px, 3.5vw, 16px);
          -webkit-line-clamp: 2;
          margin-bottom: clamp(6px, 2vw, 10px);
          line-height: 1.5;
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
      
      // 视频预览（悬停播放）
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
      
      // 左下角播放量
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
      
      // 右下角时长
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
      
      // 底部标签和评论
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
}

// 加载更多
.load-more {
  text-align: center;
  padding: 20px;
  color: #a855f7;
  font-size: 14px;
  cursor: pointer;
}

// ============ 响应式适配 ============

// 小屏手机 (< 375px)
@media (max-width: 374px) {
  .page-header {
    padding: 12px;
    
    .header-tabs {
      gap: 20px;
      .tab { font-size: 15px; }
    }
  }
  
  .ad-item {
    width: 60px;
    .ad-img { width: 52px; height: 52px; }
    .ad-name { font-size: 10px; }
  }
  
  .search-history-section {
    margin: 0 10px 12px;
    padding: 12px;
    
    .section-header .section-title { font-size: 14px; }
    .history-tags .history-tag { 
      padding: 6px 12px; 
      font-size: 13px; 
    }
  }
  
  .hot-search-section {
    margin: 0 10px 10px;
    padding: 10px 12px;
    
    .section-title { font-size: 14px; margin-bottom: 10px; }
    .hot-list {
      gap: 6px 12px;
      .hot-item {
        .rank .rank-icon { width: 18px; height: 18px; }
        .keyword { font-size: 13px; }
      }
    }
  }
  
  .video-list {
    gap: 10px;
    
    .video-card .video-info .video-title { font-size: 12px; }
  }
  
  .video-section {
    margin: 0 10px;
  }
  
  .filter-bar {
    padding: 10px;
    
    .filter-tabs { gap: 16px; }
    .filter-item { font-size: 13px; }
  }
}

// 平板 (768px+)
@media (min-width: 768px) {
  .search-page {
    max-width: 768px;
    margin: 0 auto;
  }
  
  .page-header {
    padding: 20px 24px;
    
    .header-tabs {
      gap: 40px;
      .tab { font-size: 18px; }
    }
  }
  
  .ad-section {
    padding: 12px 24px 20px;
    
    .ad-row { gap: 12px; }
    
    .ad-item {
      width: 80px;
      .ad-img { width: 70px; height: 70px; }
      .ad-name { font-size: 12px; }
    }
  }
  
  .search-history-section {
    margin: 0 24px 20px;
    padding: 20px;
    
    .history-tags .history-tag {
      padding: 10px 20px;
      font-size: 15px;
    }
  }
  
  .hot-search-section {
    margin: 0 24px 20px;
    padding: 20px;
    
    .hot-list {
      grid-template-columns: repeat(4, 1fr);
      gap: 16px 30px;
    }
  }
  
  .video-list {
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    
    &.single-column {
      grid-template-columns: repeat(2, 1fr);
    }
  }
  
  .video-section {
    margin: 0 24px;
  }
  
  .filter-bar {
    padding: 14px 16px;
    
    .filter-tabs {
      gap: 40px;
      .filter-item { font-size: 15px; }
    }
  }
}

// 大桌面 (1024px+)
@media (min-width: 1024px) {
  .search-page {
    max-width: 1024px;
  }
  
  .video-list {
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    
    &.single-column {
      grid-template-columns: repeat(3, 1fr);
    }
  }
  
  .hot-search-section .hot-list {
    grid-template-columns: repeat(5, 1fr);
  }
}

// 超大桌面 (1440px+)
@media (min-width: 1440px) {
  .search-page {
    max-width: 1200px;
  }
  
  .video-list {
    grid-template-columns: repeat(5, 1fr);
    
    &.single-column {
      grid-template-columns: repeat(4, 1fr);
    }
  }
}

// 2K屏幕 (1920px+)
@media (min-width: 1920px) {
  .search-page {
    max-width: 1400px;
  }
  
  .video-list {
    grid-template-columns: repeat(6, 1fr);
    gap: 24px;
    
    &.single-column {
      grid-template-columns: repeat(5, 1fr);
    }
  }
  
  .page-header .header-tabs .tab {
    font-size: 20px;
  }
}

// 4K屏幕 (2560px+)
@media (min-width: 2560px) {
  .search-page {
    max-width: 1800px;
  }
  
  .video-list {
    grid-template-columns: repeat(7, 1fr);
    gap: 28px;
    
    &.single-column {
      grid-template-columns: repeat(6, 1fr);
    }
  }
  
  .page-header .header-tabs .tab {
    font-size: 22px;
  }
}

// 触摸设备优化
@media (hover: none) and (pointer: coarse) {
  .video-card:hover {
    transform: none !important;
    
    .video-cover img {
      transform: none !important;
    }
  }
  
  .video-card:active {
    transform: scale(0.98);
    opacity: 0.9;
  }
  
  .history-tag:hover,
  .hot-item:hover,
  .ad-item:hover {
    background: transparent !important;
    transform: none !important;
  }
  
  .history-tag:active,
  .hot-item:active,
  .ad-item:active {
    opacity: 0.7;
  }
}

// 搜索结果区域
.search-results {
  padding: 0 16px;
}

// 分类标签栏
.category-tabs {
  display: flex;
  gap: 24px;
  padding: 16px 0;
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
    transition: color 0.2s;
    
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
  padding: 16px 0;
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

// 查看更多按钮
.view-more-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  margin: 16px 16px;
  background: #1a1a28;
  border: 1px solid #2a2a3a;
  border-radius: 25px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    background: #252538;
    border-color: #a855f7;
  }
  
  .arrow {
    font-size: 18px;
    color: #a855f7;
  }
}

// 推荐区域
.recommend-section {
  padding: 20px 16px;
  margin-top: 10px;
}

// 推荐标签
.recommend-tabs {
  display: flex;
  justify-content: center;
  gap: 30px;
  padding-bottom: 16px;
  border-bottom: 1px solid #2a2a3a;
  margin-bottom: 16px;
  
  .recommend-tab {
    font-size: 15px;
    color: rgba(255, 255, 255, 0.5);
    cursor: pointer;
    position: relative;
    padding: 4px 0;
    transition: color 0.2s;
    
    &.active {
      color: #fff;
      font-weight: 600;
    }
    
    // 分隔线
    &:not(:last-child)::after {
      content: '|';
      position: absolute;
      right: -17px;
      color: rgba(255, 255, 255, 0.2);
      font-weight: 300;
    }
  }
}
</style>