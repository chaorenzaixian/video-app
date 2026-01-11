<template>
  <div class="darkweb-page">
    <!-- 固定头部 -->
    <header class="fixed-header">
      <div class="header-top">
        <div class="back-btn" @click="$router.back()"><img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" /></div>
        <div class="header-title">暗网专区</div>
        <div class="header-right">
        </div>
      </div>
      <!-- 分类导航 -->
      <nav class="category-nav">
        <span 
          v-for="cat in topCategories" 
          :key="cat.id"
          :class="['cat-item', { active: activeTopCategory === cat.id }]"
          @click="selectTopCategory(cat.id)"
        >
          {{ cat.name }}
        </span>
      </nav>
    </header>
    
    <!-- 头部占位 -->
    <div class="header-placeholder"></div>

    <!-- 固定图标广告位 -->
    <div class="promo-grid-fixed" v-if="adRow1.length > 0">
      <div 
        v-for="ad in adRow1" 
        :key="ad.id" 
        class="promo-item"
        @click="handleAdClick(ad)"
      >
        <div class="promo-icon-wrap">
          <img v-if="ad.image" :src="ad.image" :alt="ad.name" class="promo-img" />
          <span v-else class="fallback-icon">{{ ad.icon || '📦' }}</span>
        </div>
        <span class="promo-name">{{ ad.name }}</span>
      </div>
    </div>

    <!-- 滚动图标广告位 -->
    <div class="promo-scroll-container" v-if="adRow2.length > 0">
      <div class="promo-grid-scroll">
        <div 
          v-for="(ad, index) in [...adRow2, ...adRow2]" 
          :key="'scroll-' + index" 
          class="promo-item"
          @click="handleAdClick(ad)"
        >
          <div class="promo-icon-wrap">
            <img v-if="ad.image" :src="ad.image" :alt="ad.name" class="promo-img" />
            <span v-else class="fallback-icon">{{ ad.icon || '📦' }}</span>
          </div>
          <span class="promo-name">{{ ad.name }}</span>
        </div>
      </div>
    </div>

    <!-- 二级分类标签 -->
    <div class="hot-section" v-if="subCategories.length > 0">
      <div class="tag-cloud">
        <span 
          v-for="sub in subCategories" 
          :key="sub.id"
          :class="['tag-item', { active: activeSubCategory === sub.id }]"
          @click="selectSubCategory(sub.id)"
        >
          {{ sub.name }}
        </span>
      </div>
    </div>

    <!-- 视频筛选 -->
    <div class="filter-bar">
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
        <span class="toggle-icon" v-if="gridMode === 1"><i></i><i></i><i></i></span>
        <span class="toggle-icon grid" v-else><i></i><i></i><i></i><i></i></span>
      </div>
    </div>

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
        @click="goToVideo(video.id)"
      >
        <div class="video-cover">
          <img :src="video.cover_url || '/images/default-cover.webp'" :alt="video.title" />
          <div class="cover-views">
            <span class="play-icon">▶</span>
            <span>{{ formatCount(video.view_count) }}</span>
          </div>
          <div class="video-duration">{{ formatDuration(video.duration) }}</div>
          <div class="vip-lock" v-if="!hasAccess">🔒</div>
        </div>
        <div class="video-info">
          <p class="video-title">{{ video.title }}</p>
          <div class="video-meta">
            <span class="video-tag" v-if="video.tags && video.tags.length > 0">{{ video.tags[0] }}</span>
            <span class="video-tag" v-else>{{ video.category_name || '暗网' }}</span>
            <span class="video-comments">评论 {{ video.comment_count || 0 }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载更多 -->
    <div class="load-more" v-if="hasMore && !loading && videos.length > 0" @click="loadMore">
      <span>{{ loadingMore ? '加载中...' : '加载更多' }}</span>
    </div>

    <!-- VIP弹窗 -->
    <Teleport to="body">
      <div class="vip-modal-overlay" v-if="showVipModal" @click.self="showVipModal = false">
        <div class="vip-modal">
          <div class="modal-icon">🔒</div>
          <h3>VIP专属内容</h3>
          <p>需要 <span class="vip-level">{{ vipLevelName }}</span> 以上才能观看</p>
          <p class="current-level">您当前等级：{{ currentLevelName }}</p>
          <button class="upgrade-btn" @click="$router.push('/user/vip')">立即升级VIP</button>
          <button class="close-btn" @click="showVipModal = false">取消</button>
        </div>
      </div>
    </Teleport>

    <!-- 底部导航 -->
    <BottomNav />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import BottomNav from '@/components/common/BottomNav.vue'

const router = useRouter()

// 状态
const loading = ref(true)
const loadingMore = ref(false)
const hasAccess = ref(false)
const minVipLevel = ref(5)
const userVipLevel = ref(0)
const categories = ref([])
const videos = ref([])
const activeTopCategory = ref(0)
const activeSubCategory = ref(0)
const activeFilter = ref(0)
const gridMode = ref(2)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const hasMore = computed(() => videos.value.length < total.value)
const showVipModal = ref(false)

// 广告数据
const adRow1 = ref([])
const adRow2 = ref([])

// VIP等级名称
const vipLevelNames = {
  0: '非VIP', 1: '普通VIP', 2: 'VIP1', 3: 'VIP2', 
  4: 'VIP3', 5: '黄金至尊', 6: '紫色限定至尊'
}
const vipLevelName = computed(() => vipLevelNames[minVipLevel.value] || `VIP${minVipLevel.value}`)
const currentLevelName = computed(() => vipLevelNames[userVipLevel.value] || '非VIP')

// 筛选选项
const filters = [
  { key: 'popular', label: '热门推荐' },
  { key: 'latest', label: '最新上架' },
  { key: 'views', label: '最多观看' },
  { key: 'comments', label: '最新热评' }
]

// 顶级分类（不包含"全部"）
const topCategories = computed(() => {
  return categories.value.filter(c => c.level === 1 || !c.parent_id)
})

// 二级分类
const subCategories = computed(() => {
  if (activeTopCategory.value === 0) return []
  const cat = categories.value.find(c => c.id === activeTopCategory.value)
  return cat?.children || []
})

// 检查访问权限
const checkAccess = async () => {
  try {
    const res = await api.get('/darkweb/access-check')
    const data = res.data || res
    hasAccess.value = data.has_access
    minVipLevel.value = data.min_vip_level || 5
    userVipLevel.value = data.user_vip_level || 0
  } catch (error) {
    hasAccess.value = false
  }
}

// 获取分类
const fetchCategories = async () => {
  try {
    const res = await api.get('/darkweb/categories')
    const data = res.data || res
    categories.value = Array.isArray(data) ? data : []
    
    // 默认选中第一个一级分类
    if (categories.value.length > 0) {
      const firstCat = categories.value.find(c => c.level === 1 || !c.parent_id)
      if (firstCat) {
        activeTopCategory.value = firstCat.id
        // 默认选中第一个二级分类
        if (firstCat.children && firstCat.children.length > 0) {
          activeSubCategory.value = firstCat.children[0].id
        }
      }
    }
  } catch (error) {
    categories.value = []
  }
}

// 获取广告
const fetchIconAds = async () => {
  try {
    const res = await api.get('/ads/icons')
    const data = res.data || res
    if (data && data.length > 0) {
      adRow1.value = data.slice(0, 5)
      adRow2.value = data.slice(5, 10)
    }
  } catch (error) {
    console.error('获取广告失败:', error)
  }
}

// 广告点击
const handleAdClick = (ad) => {
  if (ad.link) {
    window.open(ad.link, '_blank')
  }
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
    const params = {
      page: page.value,
      page_size: pageSize.value,
      sort: filters[activeFilter.value].key
    }
    
    if (activeSubCategory.value > 0) {
      params.category_id = activeSubCategory.value
    } else if (activeTopCategory.value > 0) {
      params.category_id = activeTopCategory.value
    }
    
    const res = await api.get('/darkweb/videos', { params })
    const data = res.data || res
    
    if (reset) {
      videos.value = data.items || []
    } else {
      videos.value.push(...(data.items || []))
    }
    total.value = data.total || 0
  } catch (error) {
    console.error('获取视频失败:', error)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// 选择顶级分类
const selectTopCategory = (id) => {
  activeTopCategory.value = id
  activeSubCategory.value = 0
  fetchVideos(true)
}

// 选择二级分类
const selectSubCategory = (id) => {
  activeSubCategory.value = activeSubCategory.value === id ? 0 : id
  fetchVideos(true)
}

// 切换筛选
const changeFilter = (index) => {
  activeFilter.value = index
  fetchVideos(true)
}

// 加载更多
const loadMore = () => {
  if (loadingMore.value || !hasMore.value) return
  page.value++
  fetchVideos(false)
}

// 跳转视频
const goToVideo = (id) => {
  if (!hasAccess.value) {
    showVipModal.value = true
    return
  }
  router.push(`/user/darkweb/video/${id}`)
}

// 格式化
const formatCount = (count) => {
  if (!count) return '0'
  if (count >= 10000) return (count / 10000).toFixed(1) + 'w'
  if (count >= 1000) return (count / 1000).toFixed(1) + 'k'
  return count.toString()
}

const formatDuration = (seconds) => {
  if (!seconds) return '00:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

onMounted(async () => {
  await checkAccess()
  await fetchCategories()
  await fetchIconAds()
  await fetchVideos()
})
</script>

<style lang="scss" scoped>
$breakpoint-md: 600px;
$breakpoint-lg: 768px;
$breakpoint-xl: 1024px;
$breakpoint-xxl: 1280px;

.darkweb-page {
  min-height: 100vh;
  min-height: 100dvh;
  background: #0a0a0a;
  color: #fff;
  padding-bottom: 80px;
  padding-bottom: calc(80px + env(safe-area-inset-bottom, 0px));
  width: 100%;
  max-width: 100vw;
  margin: 0 auto;
  overflow-x: clip;
  
  @media (min-width: $breakpoint-lg) { max-width: 750px; }
  @media (min-width: $breakpoint-xl) { max-width: 900px; }
  @media (min-width: $breakpoint-xxl) { max-width: 1200px; }
}

// 固定头部
.fixed-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: #0a0a0a;
  width: 100%;
  max-width: 100vw;
  margin: 0 auto;
  padding-top: env(safe-area-inset-top, 10px);
  
  @media (min-width: $breakpoint-lg) {
    max-width: 750px;
    left: 50%;
    transform: translateX(-50%);
  }
  @media (min-width: $breakpoint-xl) { max-width: 900px; }
  @media (min-width: $breakpoint-xxl) { max-width: 1200px; }
  
  .header-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: clamp(8px, 2vw, 14px) clamp(10px, 3vw, 20px);
  }
  
  .back-btn {
    font-size: 32px;
    color: #ff4444;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
  }
  
  .header-title {
    font-size: 22px;
    font-weight: 800;
    color: #fff;
    letter-spacing: 4px;
    position: relative;
    padding: 0 12px;
    
    // 血红色下划线装饰
    &::after {
      content: '';
      position: absolute;
      bottom: -4px;
      left: 50%;
      transform: translateX(-50%);
      width: 60%;
      height: 3px;
      background: linear-gradient(90deg, transparent, #ff0000, transparent);
      border-radius: 2px;
    }
  }
  
  .header-right {
    width: 60px;
    text-align: right;
    
    .vip-badge {
      font-size: 11px;
      padding: 3px 8px;
      background: linear-gradient(135deg, #ffd700, #ff8c00);
      border-radius: 10px;
      color: #000;
    }
  }
}

// 分类导航
.category-nav {
  display: flex;
  gap: clamp(16px, 5vw, 28px);
  padding: clamp(8px, 2vw, 12px) clamp(12px, 4vw, 20px);
  overflow-x: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
  
  &::-webkit-scrollbar { display: none; }
  
  .cat-item {
    font-size: clamp(14px, 4vw, 16px);
    color: rgba(255, 255, 255, 0.5);
    white-space: nowrap;
    cursor: pointer;
    padding-bottom: 6px;
    position: relative;
    transition: color 0.2s;
    
    &:hover { color: rgba(255, 255, 255, 0.8); }
    
    &.active {
      color: #ff4444;
      font-weight: 600;
      
      &::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 20px;
        height: 2px;
        background: #ff4444;
        border-radius: 1px;
      }
    }
  }
}

// 头部占位
.header-placeholder {
  height: calc(clamp(100px, 28vw, 130px) + env(safe-area-inset-top, 0px));
}

// 固定图标广告位
.promo-grid-fixed {
  display: flex;
  justify-content: space-around;
  padding: clamp(8px, 2vw, 14px) clamp(4px, 1.5vw, 10px);
  gap: clamp(4px, 1.5vw, 10px);
}

// 滚动广告容器
.promo-scroll-container {
  overflow: hidden;
  padding: clamp(2px, 1vw, 6px) 0;
  
  .promo-grid-scroll {
    display: flex;
    gap: clamp(4px, 1.5vw, 10px);
    padding: 0 clamp(4px, 1.5vw, 10px);
    width: max-content;
    animation: scroll-ads 20s linear infinite;
  }
}

@keyframes scroll-ads {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

.promo-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: clamp(4px, 1.5vw, 8px);
  cursor: pointer;
  min-width: clamp(56px, 15vw, 80px);
  transition: transform 0.2s;
  
  &:hover { transform: scale(1.05); }
  
  .promo-icon-wrap {
    width: clamp(56px, 15vw, 80px);
    height: clamp(56px, 15vw, 80px);
    border-radius: clamp(10px, 3vw, 14px);
    display: flex;
    justify-content: center;
    align-items: center;
    background: rgba(255, 68, 68, 0.1);
    
    .promo-img {
      width: 100%;
      height: 100%;
      border-radius: clamp(10px, 3vw, 14px);
      object-fit: cover;
    }
    
    .fallback-icon {
      font-size: clamp(24px, 6vw, 36px);
    }
  }
  
  .promo-name {
    font-size: clamp(11px, 3vw, 13px);
    color: rgba(255, 255, 255, 0.7);
    text-align: center;
    max-width: clamp(54px, 14vw, 76px);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

// 二级分类标签
.hot-section {
  padding: clamp(8px, 2.5vw, 14px) clamp(10px, 3vw, 16px);
}

.tag-cloud {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: clamp(6px, 2vw, 12px);
  
  @media (min-width: $breakpoint-md) { grid-template-columns: repeat(5, 1fr); }
  @media (min-width: $breakpoint-lg) { grid-template-columns: repeat(6, 1fr); }
  
  .tag-item {
    padding: clamp(6px, 2vw, 10px) clamp(2px, 1vw, 6px);
    background: rgba(255, 255, 255, 0.08);
    border-radius: clamp(4px, 1.5vw, 8px);
    font-size: clamp(12px, 3.5vw, 14px);
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    color: rgba(255, 255, 255, 0.75);
    
    &:hover {
      background: linear-gradient(135deg, #ff4444, #cc0000);
      transform: translateY(-1px);
    }
    
    &.active {
      background: linear-gradient(135deg, #ff4444, #cc0000);
      color: #fff;
    }
  }
}

// 视频筛选
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: clamp(8px, 2.5vw, 14px) clamp(6px, 2vw, 12px);
  background: #0a0a0a;
  margin: 0 clamp(4px, 1.5vw, 10px);
  border-radius: clamp(8px, 3vw, 14px) clamp(8px, 3vw, 14px) 0 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  position: sticky;
  top: calc(clamp(100px, 28vw, 130px) + env(safe-area-inset-top, 0px) - 1px);
  z-index: 40;
  
  .filter-tabs {
    display: flex;
    gap: clamp(10px, 3vw, 24px);
    
    .filter-item {
      font-size: clamp(12px, 3.5vw, 15px);
      color: rgba(255, 255, 255, 0.5);
      cursor: pointer;
      padding: clamp(4px, 1.5vw, 8px) 0;
      position: relative;
      white-space: nowrap;
      
      &:hover { color: rgba(255, 255, 255, 0.8); }
      
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
          background: linear-gradient(90deg, #ff4444, #cc0000);
          border-radius: 1px;
        }
      }
    }
  }
  
  .view-toggle {
    display: flex;
    align-items: center;
    gap: clamp(3px, 1vw, 6px);
    cursor: pointer;
    padding: clamp(3px, 1vw, 6px) clamp(5px, 1.5vw, 10px);
    border-radius: clamp(3px, 1vw, 5px);
    
    &:hover { background: rgba(255, 255, 255, 0.08); }
    
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
        }
      }
    }
  }
}

// 视频列表
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
  }
  
  &.single-column {
    grid-template-columns: 1fr;
    gap: clamp(14px, 4vw, 20px);
    @media (min-width: $breakpoint-md) { grid-template-columns: repeat(2, 1fr); }
    @media (min-width: $breakpoint-xl) { grid-template-columns: repeat(3, 1fr); }
  }
}

.video-card {
  background: transparent;
  cursor: pointer;
  transition: transform 0.2s;
  
  &:hover {
    transform: translateY(-3px);
    .video-cover img { transform: scale(1.03); }
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
    
    .vip-lock {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      font-size: 20px;
      background: rgba(0, 0, 0, 0.6);
      width: 36px;
      height: 36px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
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
        background: linear-gradient(135deg, #ff4444, #cc0000);
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
    background: linear-gradient(90deg, rgba(255, 255, 255, 0) 0%, rgba(255, 255, 255, 0.08) 50%, rgba(255, 255, 255, 0) 100%);
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
  margin: 0 clamp(4px, 1.5vw, 10px);
  color: rgba(255, 255, 255, 0.35);
  font-size: clamp(13px, 3.5vw, 15px);
  border-radius: 0 0 clamp(8px, 3vw, 14px) clamp(8px, 3vw, 14px);
}

// 加载更多
.load-more {
  display: flex;
  justify-content: center;
  padding: 20px;
  
  span {
    background: rgba(255, 68, 68, 0.2);
    color: #ff4444;
    padding: 12px 40px;
    border-radius: 25px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.3s;
    
    &:hover { background: rgba(255, 68, 68, 0.3); }
  }
}

// VIP弹窗
.vip-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.vip-modal {
  background: linear-gradient(180deg, #1a0a0a 0%, #0a0a0a 100%);
  border-radius: 16px;
  padding: 30px;
  text-align: center;
  width: 300px;
  
  .modal-icon { font-size: 48px; margin-bottom: 16px; }
  
  h3 {
    font-size: 20px;
    color: #ff4444;
    margin-bottom: 12px;
  }
  
  p {
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 8px;
    
    .vip-level {
      color: #ffd700;
      font-weight: bold;
    }
  }
  
  .current-level { margin-bottom: 20px; }
  
  .upgrade-btn {
    display: block;
    width: 100%;
    padding: 12px 0;
    background: linear-gradient(135deg, #ffd700, #ff8c00);
    border: none;
    border-radius: 25px;
    color: #000;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
    margin-bottom: 10px;
  }
  
  .close-btn {
    display: block;
    width: 100%;
    padding: 10px 0;
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 25px;
    color: #fff;
    font-size: 14px;
    cursor: pointer;
  }
}
</style>
