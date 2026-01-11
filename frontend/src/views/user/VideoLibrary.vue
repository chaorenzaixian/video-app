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
    <div class="video-section" v-if="activeCategory === 'video'">
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

    <!-- 抖音列表 -->
    <div class="video-section" v-if="activeCategory === 'douyin'">
      <div v-if="loading && shortVideos.length === 0" class="loading-state">加载中...</div>
      <div v-else-if="!loading && shortVideos.length === 0" class="empty-videos">
        <span>暂无短视频</span>
      </div>
      <div v-else class="video-list double-column">
        <div 
          v-for="video in shortVideos" 
          :key="video.id"
          class="video-card"
          @click="goToShortVideo(video.id)"
        >
          <div class="video-cover vertical">
            <img :src="getCoverUrl(video.cover_url)" :alt="video.title"/>
            <div class="cover-views">
              <span class="play-icon">▶</span>
              <span>{{ formatCount(video.view_count) }}</span>
            </div>
          </div>
          <div class="video-info">
            <p class="video-title">{{ video.title }}</p>
          </div>
        </div>
      </div>
      <div class="load-more" v-if="hasMoreShort && shortVideos.length > 0" @click="loadMoreShort">
        <span>加载更多</span>
      </div>
    </div>

    <!-- 图集列表 -->
    <div class="gallery-section" v-if="activeCategory === 'gallery'">
      <div v-if="loading && galleries.length === 0" class="loading-state">加载中...</div>
      <div v-else-if="!loading && galleries.length === 0" class="empty-videos">
        <span>暂无图集</span>
      </div>
      <div v-else class="gallery-grid">
        <div 
          v-for="gallery in galleries" 
          :key="gallery.id"
          class="gallery-item"
          @click="goToGallery(gallery.id)"
        >
          <div class="gallery-cover">
            <img :src="gallery.cover" :alt="gallery.title" />
            <div class="gallery-info">
              <span class="views">👁 {{ formatCount(gallery.view_count) }}</span>
              <span class="count">📷 {{ gallery.image_count }}</span>
            </div>
          </div>
          <p class="gallery-title">{{ gallery.title }}</p>
        </div>
      </div>
      <div class="load-more" v-if="hasMoreGallery && galleries.length > 0" @click="loadMoreGallery">
        <span>加载更多</span>
      </div>
    </div>

    <!-- 小说列表 -->
    <div class="novel-section" v-if="activeCategory === 'novel'">
      <div v-if="loading && novels.length === 0" class="loading-state">加载中...</div>
      <div v-else-if="!loading && novels.length === 0" class="empty-videos">
        <span>暂无小说</span>
      </div>
      <div v-else class="novel-grid">
        <div 
          v-for="novel in novels" 
          :key="novel.id"
          class="novel-item"
          @click="goToNovel(novel)"
        >
          <div class="novel-cover-wrap">
            <img :src="novel.cover || '/images/default-novel.webp'" :alt="novel.title" class="novel-cover" />
            <span v-if="novel.novel_type === 'audio'" class="audio-badge">🎧</span>
          </div>
          <div class="novel-info">
            <p class="novel-title">{{ novel.title }}</p>
            <p class="novel-author">{{ novel.author || '佚名' }}</p>
            <p class="novel-chapters">共{{ novel.chapter_count || 0 }}章</p>
          </div>
        </div>
      </div>
      <div class="load-more" v-if="hasMoreNovel && novels.length > 0" @click="loadMoreNovel">
        <span>加载更多</span>
      </div>
    </div>

    <!-- 帖子列表 -->
    <div class="post-section" v-if="activeCategory === 'post'">
      <div v-if="loading && posts.length === 0" class="loading-state">加载中...</div>
      <div v-else-if="!loading && posts.length === 0" class="empty-videos">
        <span>暂无帖子</span>
      </div>
      <div v-else class="post-list">
        <div 
          v-for="post in posts" 
          :key="post.id"
          class="post-card"
          @click="goToPost(post.id)"
        >
          <div class="post-header">
            <img :src="post.user?.avatar || '/images/avatars/icon_avatar_1.webp'" class="post-avatar" />
            <div class="post-user-info">
              <span class="post-username">{{ post.user?.nickname || '用户' }}</span>
              <span class="post-time">{{ formatTime(post.created_at) }}</span>
            </div>
          </div>
          <p class="post-content">{{ post.content }}</p>
          <div v-if="post.images && post.images.length" class="post-images">
            <img v-for="(img, idx) in post.images.slice(0, 3)" :key="idx" :src="img" class="post-img" />
          </div>
          <div class="post-stats">
            <span>👁 {{ formatCount(post.view_count) }}</span>
            <span>💬 {{ post.comment_count || 0 }}</span>
            <span>❤️ {{ formatCount(post.like_count) }}</span>
            <span v-if="post.topics && post.topics.length" class="post-topic-tag">#{{ post.topics[0].name }}</span>
          </div>
        </div>
      </div>
      <div class="load-more" v-if="hasMorePost && posts.length > 0" @click="loadMorePost">
        <span>加载更多</span>
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
  { key: 'video', label: '影片' },
  { key: 'douyin', label: '抖音' },
  { key: 'gallery', label: '图集' },
  { key: 'novel', label: '小说' },
  { key: 'post', label: '帖子' }
])

const tagFilters = ref([
  { key: 'all', label: '全部类型' }
])

const typeFilters = ref([
  { key: 'all', label: '全部' },
  { key: 'vip', label: 'VIP' }
])

const sortFilters = ref([
  { key: 'favorite', label: '最多收藏' },
  { key: 'view', label: '最多观看' },
  { key: 'newest', label: '最新上架' }
])

const activeCategory = ref('video')
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

// 抖音列表
const shortVideos = ref([])
const hasMoreShort = ref(true)
const pageShort = ref(1)

// 图集列表
const galleries = ref([])
const hasMoreGallery = ref(true)
const pageGallery = ref(1)

// 小说列表
const novels = ref([])
const hasMoreNovel = ref(true)
const pageNovel = ref(1)

// 帖子列表
const posts = ref([])
const hasMorePost = ref(true)
const pagePost = ref(1)

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

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = (now - date) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + '小时前'
  return date.toLocaleDateString()
}

// 导航
const goToSearch = () => router.push('/user/search')
const goToVideo = (id) => router.push(`/user/video/${id}`)
const goToShortVideo = (id) => router.push(`/user/short-video/${id}`)
const goToGallery = (id) => router.push(`/user/gallery/${id}`)
const goToPost = (id) => router.push(`/user/community/post/${id}`)
const goToNovel = (novel) => {
  if (novel.novel_type === 'audio') {
    router.push(`/user/audio-novel/${novel.id}`)
  } else {
    router.push(`/user/novel/${novel.id}`)
  }
}

// 根据分类加载数据
const loadByCategory = async () => {
  loading.value = true
  try {
    switch (activeCategory.value) {
      case 'video':
        await fetchVideos(true)
        break
      case 'douyin':
        await fetchShortVideos(true)
        break
      case 'gallery':
        await fetchGalleries(true)
        break
      case 'novel':
        await fetchNovels(true)
        break
      case 'post':
        await fetchPosts(true)
        break
    }
  } finally {
    loading.value = false
  }
}

// 获取视频
const fetchVideos = async (reset = true) => {
  if (reset) {
    page.value = 1
    videos.value = []
  } else {
    loadingMore.value = true
  }

  try {
    const sortMap = {
      'favorite': 'hot',
      'view': 'view_count',
      'newest': 'created_at'
    }

    const params = {
      page: page.value,
      limit: pageSize,
      sort_by: sortMap[activeSort.value] || 'hot'
    }

    if (activeType.value === 'vip') {
      params.is_vip_only = true
    }

    // 标签筛选 - 使用分类ID
    if (activeTag.value !== 'all') {
      params.category_id = parseInt(activeTag.value)
    }

    const res = await api.get('/videos', { params })
    const items = (res.data?.videos || res.data?.items || res.data || []).map(v => ({
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
    loadingMore.value = false
  }
}

// 获取抖音
const fetchShortVideos = async (reset = true) => {
  if (reset) {
    pageShort.value = 1
    shortVideos.value = []
  }
  try {
    const res = await api.get('/shorts', {
      params: { page: pageShort.value, limit: pageSize }
    })
    const items = res.data?.items || res.data || []
    shortVideos.value = reset ? items : [...shortVideos.value, ...items]
    hasMoreShort.value = items.length >= pageSize
  } catch (e) {
    console.error('获取抖音失败:', e)
  }
}

// 获取图集
const fetchGalleries = async (reset = true) => {
  if (reset) {
    pageGallery.value = 1
    galleries.value = []
  }
  try {
    const res = await api.get('/gallery-novel/gallery/list', {
      params: { page: pageGallery.value, page_size: pageSize }
    })
    const items = res.data || []
    galleries.value = reset ? items : [...galleries.value, ...items]
    hasMoreGallery.value = items.length >= pageSize
  } catch (e) {
    console.error('获取图集失败:', e)
  }
}

// 获取小说
const fetchNovels = async (reset = true) => {
  if (reset) {
    pageNovel.value = 1
    novels.value = []
  }
  try {
    const res = await api.get('/gallery-novel/novel/list', {
      params: { page: pageNovel.value, page_size: pageSize, novel_type: 'all' }
    })
    // 过滤掉无效数据
    const items = (res.data || []).filter(n => n.title && n.id)
    novels.value = reset ? items : [...novels.value, ...items]
    hasMoreNovel.value = items.length >= pageSize
  } catch (e) {
    console.error('获取小说失败:', e)
  }
}

// 获取帖子
const fetchPosts = async (reset = true) => {
  if (reset) {
    pagePost.value = 1
    posts.value = []
  }
  try {
    const res = await api.get('/community/posts', {
      params: { page: pagePost.value, page_size: pageSize }
    })
    const items = res.data || []
    posts.value = reset ? items : [...posts.value, ...items]
    hasMorePost.value = items.length >= pageSize
  } catch (e) {
    console.error('获取帖子失败:', e)
  }
}

// 加载更多
const loadMore = () => {
  if (loadingMore.value || !hasMore.value) return
  page.value++
  fetchVideos(false)
}

const loadMoreShort = async () => {
  pageShort.value++
  await fetchShortVideos(false)
}

const loadMoreGallery = async () => {
  pageGallery.value++
  await fetchGalleries(false)
}

const loadMoreNovel = async () => {
  pageNovel.value++
  await fetchNovels(false)
}

const loadMorePost = async () => {
  pagePost.value++
  await fetchPosts(false)
}

// 获取视频分类
const fetchCategories = async () => {
  try {
    const res = await api.get('/videos/categories')
    const cats = res.data || []
    tagFilters.value = [
      { key: 'all', label: '全部类型' },
      ...cats.map(c => ({ key: String(c.id), label: c.name }))
    ]
  } catch (e) {
    console.error('获取分类失败:', e)
  }
}

// 监听分类切换
watch(activeCategory, () => {
  loadByCategory()
})

// 监听筛选变化（仅影片）
watch([activeTag, activeType, activeSort], () => {
  if (activeCategory.value === 'video') {
    fetchVideos(true)
  }
})

onMounted(() => {
  fetchCategories()
  loadByCategory()
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
    gap: clamp(16px, 4vw, 24px);
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    padding-bottom: 4px;
    
    &::-webkit-scrollbar {
      display: none;
    }
    
    .filter-option {
      font-size: clamp(13px, 3.5vw, 15px);
      color: rgba(255, 255, 255, 0.5);
      cursor: pointer;
      transition: color 0.2s;
      white-space: nowrap;
      flex-shrink: 0;
      
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

.loading-state {
  text-align: center;
  padding: 40px;
  color: rgba(255, 255, 255, 0.5);
}

// 抖音竖屏封面
.video-cover.vertical {
  aspect-ratio: 9/16;
}

// 图集列表
.gallery-section {
  padding: 0 12px;
}

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px 12px;
}

.gallery-item {
  cursor: pointer;
  width: 100%;
  min-width: 0;
  
  .gallery-cover {
    position: relative;
    width: 100%;
    height: 0;
    padding-bottom: 133.33%;
    border-radius: 8px;
    overflow: hidden;
    background: #1a1a1a;
    
    img {
      position: absolute;
      top: 0;
      left: 0;
      width: 100% !important;
      height: 100% !important;
      object-fit: cover !important;
      max-width: none !important;
    }
    
    .gallery-info {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      padding: 6px 8px;
      background: linear-gradient(transparent, rgba(0,0,0,0.8));
      display: flex;
      justify-content: space-between;
      font-size: 11px;
      color: #fff;
      z-index: 1;
    }
  }
  
  .gallery-title {
    color: #eee;
    font-size: 13px;
    margin: 8px 0 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

// 小说列表
.novel-section {
  padding: 0 12px;
}

.novel-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px 12px;
}

.novel-item {
  cursor: pointer;
  width: 100%;
  min-width: 0;
  
  .novel-cover-wrap {
    position: relative;
    width: 100%;
    height: 0;
    padding-bottom: 133.33%;
    border-radius: 8px;
    overflow: hidden;
    background: #1a1a1a;
    
    .novel-cover {
      position: absolute;
      top: 0;
      left: 0;
      width: 100% !important;
      height: 100% !important;
      object-fit: cover !important;
      max-width: none !important;
    }
    
    .audio-badge {
      position: absolute;
      top: 6px;
      left: 6px;
      background: rgba(0, 0, 0, 0.6);
      padding: 4px 6px;
      border-radius: 10px;
      font-size: 12px;
      z-index: 1;
    }
  }
  
  .novel-info {
    padding: 8px 0;
    
    .novel-title {
      color: #eee;
      font-size: 13px;
      font-weight: 500;
      margin: 0 0 4px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .novel-author {
      color: #888;
      font-size: 11px;
      margin: 0 0 2px;
    }
    
    .novel-chapters {
      color: #666;
      font-size: 11px;
      margin: 0;
    }
  }
}

// 帖子列表
.post-section {
  padding: 0 12px;
}

.post-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.post-card {
  background: #151520;
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  
  .post-header {
    display: flex;
    align-items: center;
    margin-bottom: 12px;
    
    .post-avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      object-fit: cover;
    }
    
    .post-user-info {
      margin-left: 12px;
      display: flex;
      flex-direction: column;
      
      .post-username {
        color: #fff;
        font-size: 14px;
        font-weight: 500;
      }
      
      .post-time {
        color: #666;
        font-size: 12px;
      }
    }
  }
  
  .post-content {
    color: #ddd;
    font-size: 14px;
    line-height: 1.6;
    margin: 0 0 12px;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  
  .post-images {
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
    
    .post-img {
      width: 100px;
      height: 100px;
      object-fit: cover;
      border-radius: 8px;
    }
  }
  
  .post-stats {
    display: flex;
    gap: 20px;
    color: #666;
    font-size: 13px;
    align-items: center;
    
    .post-topic-tag {
      margin-left: auto;
      padding: 4px 12px;
      background: transparent;
      border: 1px solid rgba(168, 85, 247, 0.5);
      border-radius: 12px;
      color: #a855f7;
      font-size: 12px;
    }
  }
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