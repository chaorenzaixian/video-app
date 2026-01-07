<template>
  <div class="app-container">
    <!-- 固定头部 -->
    <header class="fixed-header">
      <!-- 顶部栏 -->
      <div class="header-top">
        <!-- 左边福利图标 -->
        <div class="header-left">
          <div class="welfare-icon" @click="goToWelfare">
            <img src="/images/backgrounds/fuli.webp" alt="福利" class="fuli-img" />
          </div>
        </div>
        <!-- 中间Logo -->
        <div class="header-center">
          <img v-if="siteSettings.logo" :src="siteSettings.logo" alt="Logo" class="logo-img" />
          <span v-else class="logo-text">Soul</span>
        </div>
        <!-- 右边图标 -->
        <div class="header-right">
          <router-link to="/user/search" class="header-icon search-icon">
            <img src="/images/backgrounds/ic_search.webp" alt="搜索" class="search-img" />
          </router-link>
          <div class="header-icon menu-icon" @click="showNavDrawer = true">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
      <!-- 分类导航 -->
      <nav ref="categoryNavRef" :class="['category-nav', navSlideClass]">
        <span 
          v-for="cat in categories" 
          :key="cat.id"
          :ref="el => setCategoryRef(cat.id, el)"
          :class="['cat-item', { active: activeCategory === cat.id }]"
          @click="selectCategory(cat.id)"
        >
          {{ cat.name }}
        </span>
      </nav>
    </header>
    
    <!-- 头部占位 -->
    <div class="header-placeholder"></div>

    <!-- 轮播广告 -->
    <div class="banner-carousel" v-if="banners.length > 0">
      <div class="banner-wrapper" ref="bannerWrapper">
        <div 
          class="banner-track" 
          :style="{ transform: `translateX(-${currentBannerIndex * 100}%)` }"
        >
          <div 
            v-for="banner in banners" 
            :key="banner.id" 
            class="banner-slide"
            @click="handleBannerClick(banner)"
          >
            <img :src="banner.image_url" :alt="banner.title" class="banner-image" />
          </div>
        </div>
        <!-- 指示点 -->
        <div class="banner-dots" v-if="banners.length > 1">
          <span 
            v-for="(_, index) in banners" 
            :key="index"
            :class="['dot', { active: currentBannerIndex === index }]"
            @click="currentBannerIndex = index"
          ></span>
        </div>
      </div>
    </div>

    <!-- 页面内容区域（带左右滑动效果） -->
    <transition :name="slideDirection" mode="out-in">
      <div class="page-content" :key="activeCategory">
        <!-- 固定图标广告位 -->
        <div class="promo-grid-fixed" v-if="adRow1.length > 0">
          <div 
            v-for="ad in adRow1" 
            :key="ad.id" 
            class="promo-item"
            @click="handleAdClick(ad)"
          >
            <div class="promo-icon-wrap" :style="{ background: ad.bg }">
              <img v-if="ad.image && !ad._imgError" :src="ad.image" :alt="ad.name" class="promo-img" @error="ad._imgError = true" />
              <span v-else class="fallback-icon">{{ ad.icon || '📦' }}</span>
            </div>
            <span class="promo-name">{{ ad.name }}</span>
          </div>
        </div>

        <!-- 滚动图标广告位 -->
        <div class="promo-scroll-container" v-if="adRow2.length > 0">
          <div class="promo-grid-scroll" ref="scrollContainer">
            <div 
              v-for="ad in [...adRow2, ...adRow2]" 
              :key="ad.id + '-' + Math.random()" 
              class="promo-item"
              @click="handleAdClick(ad)"
            >
              <div class="promo-icon-wrap" :style="{ background: ad.bg }">
                <img v-if="ad.image && !ad._imgError" :src="ad.image" :alt="ad.name" class="promo-img" @error="ad._imgError = true" />
                <span v-else class="fallback-icon">{{ ad.icon || '📦' }}</span>
              </div>
              <span class="promo-name">{{ ad.name }}</span>
            </div>
          </div>
        </div>

        <!-- 功能入口 - 横向滚动 -->
        <div class="func-scroll-wrapper">
          <div class="func-scroll">
            <div 
              v-for="func in funcItems" 
              :key="func.id" 
              class="func-item"
              @click="handleFuncClick(func)"
            >
              <div class="func-icon-box" :class="{ 'has-image': func.image && !func.imageError }">
                <img 
                  v-if="func.image && !func.imageError" 
                  :src="func.image" 
                  :alt="func.name" 
                  class="func-icon-img"
                  @error="func.imageError = true"
                />
                <span v-else class="func-icon-text">{{ getFuncShortName(func.name) }}</span>
              </div>
              <span class="func-name">{{ func.name }}</span>
            </div>
          </div>
        </div>

        <!-- 二级分类（原热门标签区域） -->
        <div class="hot-section" v-if="currentSubCategories.length > 0">
          <div class="tag-cloud">
            <span 
              v-for="subCat in currentSubCategories" 
              :key="subCat.id" 
              class="tag-item"
              @click="selectSubCategory(subCat)"
            >
              {{ subCat.name }}
            </span>
          </div>
        </div>

        <!-- 视频筛选 -->
        <div class="filter-bar">
          <div class="filter-tabs">
            <span 
              v-for="(filter, index) in videoFilters" 
              :key="filter.key"
              :class="['filter-item', { active: activeVideoFilter === index }]"
              @click="changeVideoFilter(index)"
            >
              {{ filter.label }}
            </span>
          </div>
          <!-- 列表/网格切换 -->
          <div class="view-toggle" @click="gridMode = gridMode === 1 ? 2 : 1">
            <span class="toggle-label">切换</span>
            <!-- 单列模式显示横线图标，双列模式显示网格图标 -->
            <span class="toggle-icon" v-if="gridMode === 1">
              <i></i><i></i><i></i>
            </span>
            <span class="toggle-icon grid" v-else>
              <i></i><i></i><i></i><i></i>
            </span>
          </div>
        </div>

        <!-- 骨架屏加载状态 -->
        <div v-if="loadingVideos && videos.length === 0" :class="['video-list', gridMode === 1 ? 'single-column' : 'double-column']">
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
        <div v-else-if="!loadingVideos && videos.length === 0" class="empty-videos">
          <span>暂无视频</span>
        </div>

        <!-- 视频列表 -->
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
              <!-- 视频预览（悬停播放） -->
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
    </transition>

    <!-- 底部提示条 -->
    <div class="bottom-promo" v-if="showPromo">
      <div class="promo-icon">
        <svg viewBox="0 0 24 24" fill="none">
          <path d="M11 5L6 9H2v6h4l5 4V5z" fill="#7c3aed"/>
          <path d="M15.54 8.46a5 5 0 0 1 0 7.07" stroke="#7c3aed" stroke-width="2.5" stroke-linecap="round"/>
          <path d="M19.07 4.93a10 10 0 0 1 0 14.14" stroke="#7c3aed" stroke-width="2.5" stroke-linecap="round"/>
        </svg>
      </div>
      <div class="promo-text">
        <span class="scroll-text">{{ announcementText }} 🔸 {{ announcementText }}</span>
      </div>
      <span class="close-btn" @click="showPromo = false">✕</span>
    </div>

    <!-- 短视频浮动入口 -->
    <div class="short-video-float" @click="$router.push('/shorts')">
      <img src="/images/backgrounds/short_logo.webp" alt="短视频" />
    </div>

    <!-- 底部导航 -->
    <BottomNav />
    
    <!-- 导航列表抽屉 -->
    <div class="nav-drawer-mask" v-if="showNavDrawer" @click="showNavDrawer = false"></div>
    <transition name="drawer-slide">
      <div class="nav-drawer" v-if="showNavDrawer">
        <div class="drawer-header">
          <h3>导航列表</h3>
        </div>
        <div class="drawer-grid">
          <div 
            v-for="cat in categories.filter(c => c.id !== 0)" 
            :key="cat.id"
            :class="['drawer-item', { active: activeCategory === cat.id }]"
            @click="selectFromDrawer(cat.id)"
          >
            {{ cat.name }}
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useAbortController } from '@/composables/useAbortController'
import { useTimers, useVideoCleanup } from '@/composables/useCleanup'
import { formatCount, formatDuration } from '@/utils/format'
import BottomNav from '@/components/common/BottomNav.vue'

const router = useRouter()

// 请求取消控制器
const { signal: abortSignal } = useAbortController()

// 定时器管理
const timers = useTimers()

// 视频预览资源管理
const videoCleanup = useVideoCleanup()

// 网站设置
const siteSettings = ref({
  siteName: '视频站',
  logo: ''
})

// 底部提示条显示状态
const showPromo = ref(true)

// 导航列表抽屉
const showNavDrawer = ref(false)

// 公告数据
const announcements = ref([])
const announcementText = ref('限时"尊享永久卡" 消费一次终身受益 还送10次AI脱衣 🎁 女神视频永久免费看')

// 轮播广告
const banners = ref([])
const currentBannerIndex = ref(0)

// 分类（默认数据，会被后台数据覆盖）
const categories = ref([
  { id: 0, name: '推荐' },
  { id: 1, name: '国产' },
  { id: 2, name: '日韩' },
  { id: 3, name: '欧美' },
  { id: 4, name: '动漫' },
  { id: 5, name: '直播' }
])
const activeCategory = ref(0)
const slideDirection = ref('slide-right') // 滑动方向
const navSlideClass = ref('') // 导航栏滑动动画类
const categoryNavRef = ref(null) // 分类导航容器ref
const categoryRefs = {} // 存储各分类元素的ref

// 设置分类元素ref
const setCategoryRef = (id, el) => {
  if (el) {
    categoryRefs[id] = el
  }
}

// 判断是否需要滚动（分类是否在可视区域中央）
const needsScroll = (catId) => {
  const navEl = categoryNavRef.value
  const catEl = categoryRefs[catId]
  
  if (!navEl || !catEl) return false
  
  const navWidth = navEl.offsetWidth
  const currentScroll = navEl.scrollLeft
  const catLeft = catEl.offsetLeft
  const catWidth = catEl.offsetWidth
  
  // 计算分类在可视区域中的位置
  const catVisibleLeft = catLeft - currentScroll
  const catVisibleCenter = catVisibleLeft + catWidth / 2
  
  // 可视区域中间1/3范围
  const centerStart = navWidth / 3
  const centerEnd = navWidth * 2 / 3
  
  // 如果分类已经在中间1/3范围内，不需要滚动
  return !(catVisibleCenter >= centerStart && catVisibleCenter <= centerEnd)
}

// 滚动到选中的分类（使其居中）
const scrollToCategory = (catId) => {
  const navEl = categoryNavRef.value
  const catEl = categoryRefs[catId]
  
  if (!navEl || !catEl) return
  
  const navWidth = navEl.offsetWidth
  const catLeft = catEl.offsetLeft
  const catWidth = catEl.offsetWidth
  
  // 计算滚动位置，使选中分类居中
  const scrollLeft = catLeft - (navWidth / 2) + (catWidth / 2)
  
  navEl.scrollTo({
    left: Math.max(0, scrollLeft),
    behavior: 'smooth'
  })
}

// 所有推荐分类（从后台获取的is_featured=true的分类）
const featuredCategories = ref([])

// 获取当前选中分类的子分类
const currentSubCategories = computed(() => {
  // 如果选择"推荐"，显示所有推荐分类
  if (activeCategory.value === 0) {
    return featuredCategories.value
  }
  const currentCat = categories.value.find(cat => cat.id === activeCategory.value)
  return currentCat?.children || []
})

// 选择一级分类
const selectCategory = (catId) => {
  // 根据分类位置确定滑动方向
  const currentIndex = categories.value.findIndex(c => c.id === activeCategory.value)
  const targetIndex = categories.value.findIndex(c => c.id === catId)
  const isSlideLeft = targetIndex > currentIndex
  const totalCount = categories.value.length
  
  // 页面内容滑动方向
  slideDirection.value = isSlideLeft ? 'slide-left' : 'slide-right'
  
  // 前2个和后2个分类不触发导航栏效果
  const isEdgeCategory = targetIndex < 2 || targetIndex >= totalCount - 2
  
  if (!isEdgeCategory) {
    // 判断是否需要滚动导航栏
    const shouldScroll = needsScroll(catId)
    
    if (shouldScroll) {
      // 需要滚动时，添加晃动效果
      navSlideClass.value = isSlideLeft ? 'nav-slide-left' : 'nav-slide-right'
      setTimeout(() => {
        navSlideClass.value = ''
      }, 150)
      // 滚动到选中的分类使其居中
      scrollToCategory(catId)
    }
  }
  
  activeCategory.value = catId
  fetchVideos()
}

// 选择二级分类 - 跳转到分类列表页
const selectSubCategory = (subCat) => {
  router.push(`/user/category/${subCat.id}`)
}

// 从导航抽屉选择分类
const selectFromDrawer = (catId) => {
  showNavDrawer.value = false
  selectCategory(catId)
}

// 获取分类列表
const fetchCategories = async () => {
  try {
    const res = await axios.get('/api/v1/videos/categories', { signal: abortSignal })
    if (res.data && res.data.length > 0) {
      const allCategories = res.data
      
      // 提取所有推荐分类（一级和二级）
      const featured = []
      const extractFeatured = (list) => {
        for (const cat of list) {
          if (cat.is_featured) {
            featured.push({ id: cat.id, name: cat.name })
          }
          if (cat.children && cat.children.length > 0) {
            extractFeatured(cat.children)
          }
        }
      }
      extractFeatured(allCategories)
      featuredCategories.value = featured
      
      // 添加"推荐"作为第一个选项，保留完整数据包含children
      categories.value = [
        { id: 0, name: '推荐', children: [] },
        ...allCategories.filter(cat => !cat.parent_id || cat.level === 1)
      ]
    }
  } catch (e) {
    if (e.name !== 'CanceledError' && e.name !== 'AbortError') {
      console.error('获取分类失败', e)
    }
  }
}

// 功能入口（默认数据，会被后台数据覆盖）
const funcItems = ref([
  { id: 1, name: '广场', image: '', link: '' },
  { id: 2, name: '会员中心', image: '', link: '/user/vip' },
  { id: 3, name: '社区广场', image: '', link: '' },
  { id: 4, name: '分享邀请', image: '', link: '' },
  { id: 5, name: '排行榜', image: '', link: '' }
])

// 广告位
const adRow1 = ref([])
const adRow2 = ref([])

// 视频筛选
const videoFilters = [
  { label: '热门推荐', key: 'hot' },
  { label: '最新上架', key: 'created_at' },
  { label: '最多观看', key: 'view_count' },
  { label: '最多收藏', key: 'favorite_count' }
]
const activeVideoFilter = ref(0)

// 视频列表
const videos = ref([])
const loadingVideos = ref(false)
const gridMode = ref(2) // 1=单列, 2=双列

// 滚动动画
const scrollContainer = ref(null)

// 获取网站设置
const fetchSiteSettings = async () => {
  try {
    const res = await axios.get('/api/v1/settings/site', { signal: abortSignal })
    if (res.data) {
      siteSettings.value = res.data
    }
  } catch (e) {
    if (e.name !== 'CanceledError' && e.name !== 'AbortError') {
      console.error('获取网站设置失败', e)
    }
  }
}

// 获取功能入口
const fetchFuncEntries = async () => {
  try {
    const res = await axios.get('/api/v1/ads/func-entries', { signal: abortSignal })
    if (res.data && res.data.length > 0) {
      // 添加 imageError 标记用于图片加载失败时显示占位符
      funcItems.value = res.data.map(item => ({
        ...item,
        imageError: false
      }))
    }
  } catch (e) {
    if (e.name !== 'CanceledError' && e.name !== 'AbortError') {
      console.error('获取功能入口失败', e)
    }
  }
}

// 获取广告位
const fetchIconAds = async () => {
  try {
    const res = await axios.get('/api/v1/ads/icons', { signal: abortSignal })
    if (res.data) {
      adRow1.value = res.data.slice(0, 5)
      adRow2.value = res.data.slice(5, 10)
      // 数据加载完成后启动滚动动画
      timers.setTimeout(() => {
        startScrollAnimation()
      }, 500)
    }
  } catch (e) {
    if (e.name !== 'CanceledError' && e.name !== 'AbortError') {
      console.error('获取广告位失败', e)
    }
  }
}

// 获取公告
const fetchAnnouncements = async () => {
  try {
    const res = await axios.get('/api/v1/ads/announcements', { signal: abortSignal })
    if (res.data && res.data.length > 0) {
      announcements.value = res.data
      // 合并所有公告内容为滚动文字
      announcementText.value = res.data.map(a => a.content).join(' 🔸 ')
    }
  } catch (e) {
    if (e.name !== 'CanceledError' && e.name !== 'AbortError') {
      console.error('获取公告失败', e)
    }
  }
}

// 获取视频列表
const fetchVideos = async () => {
  loadingVideos.value = true
  try {
    const sortBy = videoFilters[activeVideoFilter.value].key
    const params = { sort_by: sortBy, limit: 20 }
    // 分类筛选
    if (activeCategory.value === 0) {
      // 选择"推荐"，显示所有视频（热门推荐时优先显示推荐视频）
      // 不再限制 is_featured，显示所有已发布视频
    } else {
      // 选择了某个一级分类，显示该分类下所有视频（包括二级分类的视频）
      params.category_id = activeCategory.value
    }
    const res = await axios.get('/api/v1/videos', { params, signal: abortSignal })
    if (res.data && res.data.items) {
      videos.value = res.data.items
    } else if (Array.isArray(res.data)) {
      videos.value = res.data
    }
  } catch (e) {
    if (e.name !== 'CanceledError' && e.name !== 'AbortError') {
      console.error('获取视频列表失败', e)
    }
  } finally {
    loadingVideos.value = false
  }
}

// 切换视频筛选
const changeVideoFilter = (index) => {
  activeVideoFilter.value = index
  fetchVideos()
}

// 启动滚动动画
const startScrollAnimation = () => {
  if (!scrollContainer.value) return
  
  const container = scrollContainer.value
  let scrollPos = 0
  const scrollSpeed = 0.5
  
  const animate = () => {
    scrollPos += scrollSpeed
    if (scrollPos >= container.scrollWidth / 2) {
      scrollPos = 0
    }
    container.scrollLeft = scrollPos
    timers.requestAnimationFrame(animate)
  }
  
  timers.requestAnimationFrame(animate)
}

// 获取封面URL
const getCoverUrl = (url) => {
  if (!url) return '/placeholder.jpg'
  if (url.startsWith('http')) return url
  return url
}

// 获取预览视频URL
const getPreviewUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return url
}

// 预览视频引用
const previewRefs = ref({})
// 当前正在预览的视频ID
const previewingVideoId = ref(null)
// 触摸模式（首次触摸时启用）
const isTouchMode = ref(false)

const setPreviewRef = (id, el) => {
  if (el) {
    previewRefs.value[id] = el
    videoCleanup.registerVideo(`preview_${id}`, el)
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
let previewTimerId = null
const startPreview = (video) => {
  if (!video.preview_url || isTouchMode.value) return
  
  previewingVideoId.value = video.id
  
  if (previewTimerId) timers.clearTimeout(previewTimerId)
  previewTimerId = timers.setTimeout(() => {
    if (previewingVideoId.value === video.id) {
      playPreview(video)
    }
  }, 300)
}

// 停止预览 (PC鼠标离开)
const stopPreview = (video) => {
  if (isTouchMode.value) return
  
  if (previewTimerId) {
    timers.clearTimeout(previewTimerId)
    previewTimerId = null
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

// 获取默认图标
const getDefaultIcon = (name) => {
  const icons = {
    'AI广场': '🤖',
    '签到福利': '🎁',
    '会员中心': '👑',
    '排行榜': '🏆',
    '分享邀请': '🔗'
  }
  return icons[name] || '📱'
}

// 获取功能入口简称
const getFuncShortName = (name) => {
  const shortNames = {
    '广场': '广',
    'AI广场': 'A',
    '会员中心': '会',
    '社区广场': '社',
    '分享邀请': '分',
    '排行榜': '排',
    '签到福利': '签'
  }
  return shortNames[name] || name.charAt(0)
}

// 跳转视频页
const goToVideo = (id) => {
  router.push(`/user/video/${id}`)
}

// 跳转福利页
const goToWelfare = () => {
  router.push('/user/vip')
}

// 广告点击
const handleAdClick = (ad) => {
  if (ad.link) {
    window.open(ad.link, '_blank')
  }
}

// 功能入口点击
const handleFuncClick = (func) => {
  if (func.link) {
    if (func.link.startsWith('http')) {
      window.open(func.link, '_blank')
    } else {
      router.push(func.link)
    }
  }
}

// 获取轮播广告
const fetchBanners = async () => {
  try {
    const res = await axios.get('/api/v1/home/banners', { params: { position: 'home' }, signal: abortSignal })
    banners.value = res.data || []
    if (banners.value.length > 1) {
      startBannerAutoPlay()
    }
  } catch (e) {
    if (e.name !== 'CanceledError' && e.name !== 'AbortError') {
      console.error('获取轮播广告失败:', e)
    }
  }
}

// 轮播自动播放
let bannerIntervalId = null
const startBannerAutoPlay = () => {
  if (bannerIntervalId) timers.clearInterval(bannerIntervalId)
  bannerIntervalId = timers.setInterval(() => {
    currentBannerIndex.value = (currentBannerIndex.value + 1) % banners.value.length
  }, 4000)
}

// 处理轮播点击
const handleBannerClick = (banner) => {
  if (!banner.link_url) return
  
  const linkType = banner.link_type || 'url'
  if (linkType === 'video' && banner.link_url) {
    router.push(`/user/video/${banner.link_url}`)
  } else if (linkType === 'vip') {
    router.push('/user/vip')
  } else if (linkType === 'url' && banner.link_url) {
    if (banner.link_url.startsWith('http')) {
      window.open(banner.link_url, '_blank')
    } else {
      router.push(banner.link_url)
    }
  }
}

onMounted(() => {
  fetchSiteSettings()
  fetchCategories()
  fetchFuncEntries()
  fetchIconAds()
  fetchVideos()
  fetchAnnouncements()
  fetchBanners()
  
  timers.setTimeout(() => {
    startScrollAnimation()
  }, 1000)
})

// 资源清理由 composables 自动处理
onUnmounted(() => {
  // timers 和 videoCleanup 会在组件卸载时自动清理
})
</script>

<style lang="scss" scoped>
// ============================================
// 响应式断点变量
// ============================================
$breakpoint-xs: 375px;   // 小手机
$breakpoint-sm: 414px;   // 大手机
$breakpoint-md: 600px;   // 平板竖屏
$breakpoint-lg: 768px;   // 平板横屏
$breakpoint-xl: 1024px;  // 小桌面
$breakpoint-xxl: 1280px; // 大桌面

.app-container {
  min-height: 100vh;
  min-height: 100dvh; /* 动态视口高度，解决移动端地址栏问题 */
  background: #0a0a0a;
  color: #fff;
  padding-bottom: 60px;
  padding-bottom: calc(60px + env(safe-area-inset-bottom, 0px)); /* 安全区域适配 */
  padding-left: env(safe-area-inset-left, 0px);
  padding-right: env(safe-area-inset-right, 0px);
  width: 100%;
  max-width: 100vw;
  margin: 0 auto;
  overflow-x: clip; // 使用clip替代hidden，不影响sticky
  
  @media (min-width: $breakpoint-lg) {
    max-width: 750px;
    padding-bottom: 70px;
  }
  
  @media (min-width: $breakpoint-xl) {
    max-width: 900px;
  }
  
  @media (min-width: $breakpoint-xxl) {
    max-width: 1200px;
  }
}

// 轮播广告
.banner-carousel {
  margin: 10px 12px;
  border-radius: 12px;
  overflow: hidden;
  
  .banner-wrapper {
    position: relative;
    width: 100%;
    aspect-ratio: 750 / 300;
    background: #1a1a1a;
    border-radius: 12px;
    overflow: hidden;
  }
  
  .banner-track {
    display: flex;
    width: 100%;
    height: 100%;
    transition: transform 0.5s ease-in-out;
  }
  
  .banner-slide {
    flex: 0 0 100%;
    width: 100%;
    height: 100%;
    cursor: pointer;
    
    .banner-image {
      width: 100%;
      height: 100%;
      object-fit: fill;
    }
  }
  
  .banner-dots {
    position: absolute;
    bottom: 10px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 6px;
    
    .dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.4);
      cursor: pointer;
      transition: all 0.3s;
      
      &.active {
        width: 18px;
        border-radius: 3px;
        background: #fff;
      }
    }
  }
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
  padding-left: env(safe-area-inset-left, 0px);
  padding-right: env(safe-area-inset-right, 0px);
  box-sizing: border-box;
  
  @media (min-width: $breakpoint-lg) {
    max-width: 750px;
    left: 50%;
    transform: translateX(-50%);
  }
  
  @media (min-width: $breakpoint-xl) {
    max-width: 900px;
  }
  
  @media (min-width: $breakpoint-xxl) {
    max-width: 1200px;
  }
  
  .header-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: clamp(8px, 2vw, 14px) clamp(10px, 3vw, 20px);
    width: 100%;
    box-sizing: border-box;
  }
  
  .header-left {
    flex: 1;
    min-width: 0;
    
    .welfare-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      width: fit-content;
      
      .fuli-img {
        width: 36px;
        height: 36px;
        object-fit: contain;
        
        @media (min-width: 375px) {
          width: 42px;
          height: 42px;
        }
      }
    }
  }
  
  .header-center {
    flex: 2;
    display: flex;
    justify-content: center;
    align-items: center;
    min-width: 0;
    
    .logo-img {
      height: 30px;
      max-width: 100px;
      object-fit: contain;
      
      @media (min-width: 375px) {
        height: 36px;
        max-width: 120px;
      }
    }
    
    .logo-text {
      font-size: 26px;
      font-weight: 300;
      font-family: 'Georgia', serif;
      font-style: italic;
      background: linear-gradient(90deg, #fff 0%, #fff 60%, #a855f7 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      letter-spacing: 1px;
      
      @media (min-width: 375px) {
        font-size: 32px;
        letter-spacing: 2px;
      }
    }
  }
  
  .header-right {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 12px;
    min-width: 0;
    
    @media (min-width: 375px) {
      gap: 16px;
    }
    
    .header-icon {
      width: 28px;
      height: 28px;
      display: flex;
      justify-content: center;
      align-items: center;
      color: rgba(255, 255, 255, 0.8);
      cursor: pointer;
      transition: all 0.2s;
      flex-shrink: 0;
      
      @media (min-width: 375px) {
        width: 32px;
        height: 32px;
      }
      
      svg {
        width: 20px;
        height: 20px;
        
        @media (min-width: 375px) {
          width: 24px;
          height: 24px;
        }
      }
      
      &:hover {
        color: #fff;
      }
      
      &.search-icon .search-img {
        width: 28px;
        height: 28px;
        object-fit: contain;
      }
    }
    
    .menu-icon {
      flex-direction: column;
      gap: 5px;
      
      span {
        width: 20px;
        height: 2px;
        background: rgba(255, 255, 255, 0.8);
        border-radius: 1px;
      }
    }
  }
  
  // 分类导航（在固定头部内）
  .category-nav {
    display: flex;
    gap: clamp(14px, 4vw, 28px);
    padding: clamp(8px, 2.5vw, 14px) clamp(10px, 3vw, 20px);
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
    -ms-overflow-style: none;
    width: 100%;
    box-sizing: border-box;
    transition: transform 0.1s ease-out;
    
    &.nav-slide-left {
      animation: nav-nudge-left 0.15s ease-out;
    }
    
    &.nav-slide-right {
      animation: nav-nudge-right 0.15s ease-out;
    }
    
    &::-webkit-scrollbar {
      display: none;
    }
    
    .cat-item {
      padding: clamp(4px, 1.5vw, 8px) 0;
      font-size: clamp(13px, 4vw, 17px);
      white-space: nowrap;
      cursor: pointer;
      transition: all 0.2s;
      color: rgba(255, 255, 255, 0.6);
      position: relative;
      flex-shrink: 0;
      
      &:hover {
        color: rgba(255, 255, 255, 0.9);
      }
      
      &.active {
        color: #fff;
        font-weight: 600;
        
        &::after {
          content: '';
          position: absolute;
          bottom: 0;
          left: 50%;
          transform: translateX(-50%);
          width: clamp(16px, 5vw, 24px);
          height: clamp(2px, 0.8vw, 4px);
          background: linear-gradient(90deg, #a855f7, #6366f1);
          border-radius: 2px;
        }
      }
    }
  }
}

@keyframes shake {
  0%, 100% { transform: rotate(0deg) scale(1); }
  25% { transform: rotate(-8deg) scale(1.1); }
  75% { transform: rotate(8deg) scale(1.1); }
}


@keyframes envelope-shake {
  0%, 100% { transform: rotate(0deg); }
  20% { transform: rotate(-5deg); }
  40% { transform: rotate(5deg); }
  60% { transform: rotate(-3deg); }
  80% { transform: rotate(3deg); }
}

@keyframes fly-out {
  0% {
    opacity: 0;
    transform: translateY(15px) scale(0.5);
  }
  30% {
    opacity: 1;
    transform: translateY(-5px) scale(1);
  }
  60% {
    opacity: 1;
    transform: translateY(-15px) scale(0.9);
  }
  100% {
    opacity: 0;
    transform: translateY(-25px) scale(0.5);
  }
}

.header-placeholder {
  height: clamp(100px, 28vw, 130px);
  height: calc(clamp(100px, 28vw, 130px) + env(safe-area-inset-top, 0px));
}

// 轮播区
.promo-banner {
  margin: 12px;
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  
  .banner-content {
    display: flex;
    align-items: center;
    gap: 10px;
    
    .banner-tag {
      background: rgba(255, 255, 255, 0.2);
      padding: 4px 10px;
      border-radius: 12px;
      font-size: 12px;
    }
  }
}

// 功能入口 - 横向滚动
.func-scroll-wrapper {
  width: 100%;
  overflow: hidden;
  padding: clamp(6px, 2vw, 12px) 0;
}

.func-scroll {
  display: flex;
  gap: clamp(12px, 4vw, 20px);
  padding: 0 clamp(12px, 4vw, 16px);
  overflow-x: auto;
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  
  &::-webkit-scrollbar {
    display: none;
  }
  
  .func-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: clamp(6px, 2vw, 10px);
    cursor: pointer;
    transition: transform 0.2s;
    flex-shrink: 0;
    min-width: clamp(56px, 15vw, 72px);
    
    &:hover {
      transform: scale(1.05);
    }
    
    &:active {
      transform: scale(0.95);
    }
    
    .func-icon-box {
      width: clamp(48px, 13vw, 60px);
      height: clamp(48px, 13vw, 60px);
      display: flex;
      justify-content: center;
      align-items: center;
      border-radius: clamp(12px, 3.5vw, 16px);
      overflow: hidden;
      background: linear-gradient(145deg, #6366f1 0%, #8b5cf6 100%);
      
      // 有图片时取消渐变背景
      &.has-image {
        background: transparent;
      }
      
      .func-icon-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
      
      .func-icon-text {
        font-size: clamp(18px, 5vw, 24px);
        font-weight: 500;
        color: #fff;
      }
    }
    
    .func-name {
      font-size: clamp(12px, 3.2vw, 14px);
      color: rgba(255, 255, 255, 0.85);
      white-space: nowrap;
      text-align: center;
    }
  }
}

// 保留旧的.func-grid类以防其他地方使用
.func-grid {
  display: flex;
  gap: clamp(12px, 4vw, 20px);
  padding: clamp(6px, 2vw, 12px) clamp(12px, 4vw, 16px);
  overflow-x: auto;
  
  .func-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: clamp(4px, 1.5vw, 8px);
    cursor: pointer;
    flex-shrink: 0;
    
    .func-icon-box {
      width: clamp(36px, 10vw, 52px);
      height: clamp(36px, 10vw, 52px);
      display: flex;
      justify-content: center;
      align-items: center;
      border-radius: clamp(10px, 3vw, 14px);
      overflow: hidden;
      background: linear-gradient(145deg, #6366f1 0%, #8b5cf6 100%);
      
      &.has-image {
        background: transparent;
      }
      
      .func-icon-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
      
      .func-icon-text {
        font-size: clamp(16px, 5vw, 22px);
        font-weight: 500;
        color: #fff;
      }
    }
    
    .func-name {
      font-size: clamp(11px, 3vw, 13px);
      color: rgba(255, 255, 255, 0.8);
      white-space: nowrap;
    }
  }
}

// 固定广告位
.promo-grid-fixed {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: clamp(4px, 1.5vw, 10px);
  padding: clamp(6px, 2vw, 12px) clamp(4px, 1.5vw, 10px) clamp(2px, 1vw, 6px);
  
  @media (min-width: $breakpoint-md) {
    grid-template-columns: repeat(6, 1fr);
  }
  
  @media (min-width: $breakpoint-lg) {
    grid-template-columns: repeat(7, 1fr);
  }
  
  @media (min-width: $breakpoint-xl) {
    grid-template-columns: repeat(8, 1fr);
  }
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
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(-50%);
  }
}

.promo-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: clamp(4px, 1.5vw, 8px);
  cursor: pointer;
  min-width: clamp(56px, 15vw, 80px);
  transition: transform 0.2s;
  
  &:hover {
    transform: scale(1.05);
  }
  
  .promo-icon-wrap {
    width: clamp(56px, 15vw, 80px);
    height: clamp(56px, 15vw, 80px);
    border-radius: clamp(10px, 3vw, 14px);
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: clamp(22px, 6vw, 30px);
    position: relative;
    
    .promo-img {
      width: 100%;
      height: 100%;
      border-radius: clamp(10px, 3vw, 14px);
      object-fit: cover;
    }
    
    .fallback-icon {
      font-size: clamp(24px, 6vw, 36px);
      display: flex;
      align-items: center;
      justify-content: center;
      width: 100%;
      height: 100%;
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

// 热门标签
.hot-section {
  padding: clamp(8px, 2.5vw, 14px) clamp(10px, 3vw, 16px);
  
  .section-header {
    margin-bottom: clamp(8px, 2.5vw, 14px);
    
    .section-title {
      font-size: clamp(14px, 4vw, 18px);
      font-weight: 600;
    }
  }
}

.tag-cloud {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: clamp(6px, 2vw, 12px);
  
  @media (min-width: $breakpoint-md) {
    grid-template-columns: repeat(5, 1fr);
  }
  
  @media (min-width: $breakpoint-lg) {
    grid-template-columns: repeat(6, 1fr);
  }
  
  @media (min-width: $breakpoint-xl) {
    grid-template-columns: repeat(7, 1fr);
  }
  
  @media (min-width: $breakpoint-xxl) {
    grid-template-columns: repeat(8, 1fr);
  }
  
  .tag-item {
    padding: clamp(6px, 2vw, 10px) clamp(2px, 1vw, 6px);
    background: rgba(255, 255, 255, 0.08);
    border-radius: clamp(4px, 1.5vw, 8px);
    font-size: clamp(12px, 3.5vw, 14px);
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    letter-spacing: 0.3px;
    color: rgba(255, 255, 255, 0.75);
    font-weight: 500;
    
    &:hover {
      background: linear-gradient(135deg, #a855f7, #7c3aed);
      transform: translateY(-1px);
    }
    
    &.active {
      background: linear-gradient(135deg, #a855f7, #7c3aed);
      color: #fff;
    }
  }
}

// 视频筛选 - sticky吸顶效果
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: clamp(8px, 2.5vw, 14px) clamp(6px, 2vw, 12px);
  background: #0a0a0a;
  margin: 0 clamp(4px, 1.5vw, 10px);
  border-radius: clamp(8px, 3vw, 14px) clamp(8px, 3vw, 14px) 0 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  width: calc(100% - clamp(8px, 3vw, 20px));
  box-sizing: border-box;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  -ms-overflow-style: none;
  position: sticky;
  top: calc(clamp(100px, 28vw, 130px) + env(safe-area-inset-top, 0px) - 1px); // 固定头部高度，减1px消除缝隙
  z-index: 40;
  
  &::-webkit-scrollbar {
    display: none;
  }
  
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
      flex-shrink: 0;
      
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
    margin-left: clamp(6px, 2vw, 14px);
    
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
      
      // 单列模式 - 三条横线
      i {
        width: clamp(12px, 4vw, 18px);
        height: 2px;
        background: rgba(255, 255, 255, 0.8);
        border-radius: 1px;
      }
      
      // 双列模式 - 四个方块
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
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
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

// 视频列表
.video-list {
  display: grid;
  gap: clamp(10px, 3vw, 16px) clamp(6px, 2vw, 12px);
  padding: clamp(6px, 2vw, 12px) clamp(4px, 1.5vw, 10px);
  background: #0a0a0a;
  margin: 0 clamp(4px, 1.5vw, 10px);
  border-radius: 0 0 clamp(8px, 3vw, 14px) clamp(8px, 3vw, 14px);
  
  // 双列模式（默认）
  &.double-column {
    grid-template-columns: repeat(2, 1fr);
    
    @media (min-width: $breakpoint-md) {
      grid-template-columns: repeat(3, 1fr);
    }
    
    @media (min-width: $breakpoint-lg) {
      grid-template-columns: repeat(3, 1fr);
    }
    
    @media (min-width: $breakpoint-xl) {
      grid-template-columns: repeat(4, 1fr);
    }
    
    @media (min-width: $breakpoint-xxl) {
      grid-template-columns: repeat(5, 1fr);
    }
    
    .video-card {
      width: 100%;
      min-width: 0;
    }
  }
  
  // 单列模式 - 视频卡片全宽垂直显示
  &.single-column {
    grid-template-columns: 1fr;
    gap: clamp(14px, 4vw, 20px);
    
    @media (min-width: $breakpoint-md) {
      grid-template-columns: repeat(2, 1fr);
    }
    
    @media (min-width: $breakpoint-xl) {
      grid-template-columns: repeat(3, 1fr);
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
          min-height: calc(clamp(13px, 3.5vw, 16px) * 1.5 * 2); /* 固定两行高度 */
          text-align: left;
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
      
      .video-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(transparent 40%, rgba(0, 0, 0, 0.8));
        display: flex;
        justify-content: center;
        align-items: center;
        opacity: 0;
        transition: opacity 0.3s;
        
        .play-icon {
          font-size: clamp(32px, 10vw, 48px);
          color: #fff;
          text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
        }
      }
      
      &:hover .video-overlay {
        opacity: 1;
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
        min-height: calc(clamp(12px, 3.5vw, 15px) * 1.5 * 2); /* 固定两行高度 */
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
      
      .video-stats {
        display: flex;
        gap: clamp(10px, 3vw, 16px);
        font-size: clamp(10px, 2.8vw, 12px);
        color: rgba(255, 255, 255, 0.4);
      }
    }
  }
}

// 底部提示条
.bottom-promo {
  position: fixed;
  bottom: calc(52px + env(safe-area-inset-bottom, 0px)); /* 底部导航高度约48px + 一点间距 */
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 6px 16px;
  background: rgba(30, 15, 45, 0.85);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  z-index: 99;
  width: 100%;
  
  // 响应式最大宽度 - 与页面内容一致
  @media (min-width: 768px) {
    max-width: 750px;
    left: 50%;
    transform: translateX(-50%);
    bottom: calc(56px + env(safe-area-inset-bottom, 0px)); // 平板导航稍高
    padding: 8px 20px;
  }
  
  @media (min-width: 1024px) {
    max-width: 900px;
  }
  
  @media (min-width: 1280px) {
    max-width: 1200px;
  }
  
  .promo-icon {
    width: 28px;
    height: 28px;
    flex-shrink: 0;
    
    svg {
      width: 100%;
      height: 100%;
    }
    
    @media (min-width: 768px) {
      width: 30px;
      height: 30px;
    }
  }
  
  .promo-text {
    flex: 1;
    overflow: hidden;
    display: flex;
    align-items: center;
    height: 22px;
    position: relative;
    
    @media (min-width: 768px) {
      height: 24px;
    }
    
    .scroll-text {
      display: inline-block;
      font-size: 13px;
      font-weight: 500;
      color: rgba(255, 255, 255, 0.85);
      white-space: nowrap;
      animation: scroll-promo 25s linear infinite;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
      letter-spacing: 0.5px;
      
      @media (min-width: 768px) {
        font-size: 14px;
      }
    }
  }
  
  @keyframes scroll-promo {
    0% { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
  }
  
  .close-btn {
    padding: 4px 8px;
    cursor: pointer;
    opacity: 0.6;
    font-size: 14px;
    margin-left: 4px;
    flex-shrink: 0;
    
    @media (min-width: 768px) {
      font-size: 16px;
      padding: 6px 10px;
    }
    
    &:hover {
      opacity: 1;
    }
  }
}

@keyframes fire-shake {
  0% { transform: translateY(0) scale(1); }
  100% { transform: translateY(-2px) scale(1.05); }
}

// 短视频浮动入口
.short-video-float {
  position: fixed;
  right: 16px;
  bottom: calc(100px + env(safe-area-inset-bottom, 0px)); // 在底部导航上方
  width: 60px;
  height: 60px;
  border-radius: 50%;
  overflow: hidden;
  z-index: 1000;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4), 0 0 15px rgba(0, 224, 255, 0.3);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  &:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 25px rgba(0, 0, 0, 0.5), 0 0 20px rgba(0, 224, 255, 0.5);
  }
  
  &:active {
    transform: scale(0.95);
  }
}

// 横屏模式优化
@media (orientation: landscape) and (max-height: 500px) {
  .fixed-header {
    padding-top: 5px;
    
    .header-top {
      padding: 5px 12px;
    }
    
    .category-nav {
      padding: 6px 12px;
    }
  }
  
  .header-placeholder {
    height: 80px !important;
  }
  
  .short-video-float {
    width: 50px;
    height: 50px;
    right: 12px;
    bottom: calc(80px + env(safe-area-inset-bottom, 0px));
  }
  
  .bottom-promo {
    padding: 4px 12px;
    bottom: calc(40px + env(safe-area-inset-bottom, 0px));
    
    .promo-icon {
      width: 22px;
      height: 22px;
    }
    
    .promo-text {
      height: 18px;
      
      .scroll-text {
        font-size: 12px;
      }
    }
  }
  
  .func-scroll-wrapper, .func-grid {
    padding: 4px 0;
  }
  
  .func-scroll, .func-grid {
    padding-left: 8px;
    padding-right: 8px;
    gap: 10px;
    
    .func-item .func-icon-box {
      width: 40px;
      height: 40px;
    }
  }
  
  .promo-grid-fixed {
    padding: 4px;
  }
  
  .promo-item .promo-icon-wrap {
    width: 48px;
    height: 48px;
  }
}

// 页面内容区域
.page-content {
  width: 100%;
}

// 左滑动画（点击右边的分类）
.slide-left-enter-active,
.slide-left-leave-active {
  transition: all 0.1s ease-out;
}

.slide-left-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.slide-left-leave-to {
  opacity: 0;
  transform: translateX(-100%);
}

// 右滑动画（点击左边的分类）
.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.1s ease-out;
}

.slide-right-enter-from {
  opacity: 0;
  transform: translateX(-100%);
}

.slide-right-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

// 导航栏轻微滑动动画
@keyframes nav-nudge-left {
  0% { transform: translateX(0); }
  50% { transform: translateX(-8px); }
  100% { transform: translateX(0); }
}

@keyframes nav-nudge-right {
  0% { transform: translateX(0); }
  50% { transform: translateX(8px); }
  100% { transform: translateX(0); }
}

// 导航列表抽屉
.nav-drawer-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
}

.nav-drawer {
  position: fixed;
  top: 0;
  right: 0;
  width: 55%;
  max-width: 260px;
  height: 100%;
  background: rgba(26, 26, 26, 0.6);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  z-index: 1000;
  padding: 20px;
  padding-top: 60px;
  box-sizing: border-box;
  overflow-y: auto;
  
  .drawer-header {
    margin-bottom: 20px;
    
    h3 {
      font-size: 18px;
      font-weight: 600;
      margin: 0;
      color: #fff;
    }
  }
  
  .drawer-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  
  .drawer-item {
    padding: 8px 12px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    text-align: center;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.85);
    cursor: pointer;
    transition: all 0.2s;
    
    &:hover {
      background: rgba(255, 255, 255, 0.1);
    }
    
    &.active {
      background: linear-gradient(135deg, #a855f7, #7c3aed);
      color: #fff;
      font-weight: 500;
    }
  }
}

// 抽屉滑入动画
.drawer-slide-enter-active,
.drawer-slide-leave-active {
  transition: transform 0.3s ease;
}

.drawer-slide-enter-from,
.drawer-slide-leave-to {
  transform: translateX(100%);
}
</style>

