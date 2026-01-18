<template>
  <div class="community-page">
    <!-- 固定顶部区域：导航 + 一级分类 -->
    <header ref="fixedHeaderRef" class="top-header">
      <div class="main-tabs">
        <div 
          v-for="tab in mainTabs" 
          :key="tab.value"
          :class="['tab-item', { active: activeMainTab === tab.value }]"
          @click="switchMainTab(tab.value)"
        >
          <img v-if="activeMainTab === tab.value && tab.activeIcon" :src="tab.activeIcon" :alt="tab.label" class="tab-icon" />
          <span v-else class="tab-text">{{ tab.label }}</span>
        </div>
        <router-link to="/user/search" class="search-btn">
          <img src="/images/backgrounds/ic_search.webp" alt="搜索" />
        </router-link>
      </div>

      <!-- 一级分类（顶级分类）- 仅社区显示 -->
      <div class="category-tabs" v-if="activeMainTab === 'community'">
        <div class="category-scroll">
          <span 
            v-for="cat in topCategories" 
            :key="cat.id"
            :class="['category-tab', { active: selectedCategory === cat.id }]"
            @click="selectCategory(cat)"
          >{{ cat.name }}</span>
        </div>
      </div>

      <!-- 图集分类 -->
      <div class="category-tabs" v-if="activeMainTab === 'gallery'">
        <div class="category-scroll">
          <span 
            v-for="cat in galleryCategories" 
            :key="cat.id"
            :class="['category-tab', { active: selectedGalleryCategory === cat.id }]"
            @click="selectGalleryCategory(cat.id)"
          >{{ cat.name }}</span>
        </div>
      </div>

      <!-- 小说类型和分类 -->
      <div class="novel-type-tabs" v-if="activeMainTab === 'novel'">
        <div class="type-tabs">
          <span 
            :class="['type-tab', { active: selectedNovelType === 'text' }]"
            @click="switchNovelType('text')"
          >文字小说</span>
          <span 
            :class="['type-tab', { active: selectedNovelType === 'audio' }]"
            @click="switchNovelType('audio')"
          >有声小说</span>
        </div>
        <div class="category-scroll">
          <span 
            v-for="cat in novelCategories" 
            :key="cat.id"
            :class="['category-tab', { active: selectedNovelCategory === cat.id }]"
            @click="selectNovelCategory(cat.id)"
          >{{ cat.name }}</span>
        </div>
      </div>
    </header>

    <!-- 头部占位 -->
    <div class="header-placeholder" :style="{ height: fixedHeaderHeight + 'px' }"></div>

    <!-- 图标广告位 -->
    <div class="promo-grid-fixed" v-if="iconAds.length">
      <div 
        v-for="ad in iconAds.slice(0, 5)" 
        :key="ad.id" 
        class="promo-item"
        @click="openAdLink(ad)"
      >
        <div class="promo-icon-wrap">
          <img v-if="ad.image" :src="ad.image" :alt="ad.name" class="promo-img" />
          <span v-else class="fallback-icon">{{ ad.icon || '📦' }}</span>
        </div>
        <span class="promo-name">{{ ad.name }}</span>
      </div>
    </div>
    <!-- 滚动广告位 -->
    <div class="promo-scroll-container" v-if="iconAds.length > 5">
      <div class="promo-grid-scroll">
        <div 
          v-for="ad in [...iconAds.slice(5), ...iconAds.slice(5)]" 
          :key="ad.id + '-' + Math.random()" 
          class="promo-item"
          @click="openAdLink(ad)"
        >
          <div class="promo-icon-wrap">
            <img v-if="ad.image" :src="ad.image" :alt="ad.name" class="promo-img" />
            <span v-else class="fallback-icon">{{ ad.icon || '📦' }}</span>
          </div>
          <span class="promo-name">{{ ad.name }}</span>
        </div>
      </div>
    </div>

    <!-- 二级分类（子话题）- 仅社区显示 -->
    <div class="topic-cards" v-if="activeMainTab === 'community' && currentSubTopics.length">
      <div class="topic-grid">
        <div 
          v-for="topic in currentSubTopics" 
          :key="topic.id"
          :class="['topic-card', { active: selectedTopic === topic.id }]"
          :style="topic.cover ? { backgroundImage: `url(${topic.cover})` } : {}"
          @click="selectTopic(topic)"
        >
          <span class="topic-name">{{ topic.name }}</span>
          <span class="topic-count">{{ formatCount(topic.post_count) }}个帖子</span>
        </div>
      </div>
    </div>

    <!-- 筛选标签 - 独立出来实现吸顶效果 -->
    <div 
      ref="filterBarRef"
      :class="['filter-tabs', { 'is-fixed': isFilterFixed }]" 
      :style="isFilterFixed ? { top: fixedHeaderHeight + 'px' } : {}"
      v-if="activeMainTab === 'community'"
    >
      <span 
        v-for="filter in filterTabs" 
        :key="filter.value"
        :class="['filter-tab', { active: activeFilter === filter.value }]"
        @click="activeFilter = filter.value; fetchPosts(true)"
      >{{ filter.label }}</span>
    </div>
    <!-- 筛选栏固定时的占位 -->
    <div class="filter-placeholder" v-if="isFilterFixed && activeMainTab === 'community'"></div>

    <!-- 内容区域 -->
    <div class="content-area">
      <!-- 社区动态列表 -->
      <div v-if="activeMainTab === 'community'" class="posts-list">
        <div v-for="post in posts" :key="post.id" class="post-card" @click="goToDetail(post.id)">
          <div class="post-header">
            <img :src="getAvatarUrl(post.user?.avatar, post.user?.id)" class="avatar clickable" @click.stop="goToUserProfile(post.user?.id)" />
            <div class="user-info">
              <div class="user-name-row">
                <span class="username clickable" @click.stop="goToUserProfile(post.user?.id)">{{ post.user?.nickname || post.user?.username || '匿名用户' }}</span>
                <img v-if="post.user?.is_vip" :src="getVipIcon(post.user?.vip_level)" class="vip-icon" alt="VIP" />
              </div>
              <span class="time">{{ formatTime(post.created_at) }}</span>
            </div>
          </div>
          <p class="post-text">{{ post.content }}</p>
          <div v-if="post.images && post.images.length" class="post-images" @click="goToDetail(post.id)">
            <div :class="['images-grid', `grid-${Math.min(post.images.length, 4)}`]">
              <div v-for="(img, idx) in post.images.slice(0, 4)" :key="idx" class="img-item">
                <img :src="img" />
                <span v-if="idx === 3 && post.images.length > 4" class="more-count">+{{ post.images.length - 4 }}</span>
              </div>
            </div>
          </div>
          <div class="post-stats">
            <span>👁 {{ formatCount(post.view_count) }}</span>
            <span>💬 {{ post.comment_count || 0 }}</span>
            <span @click.stop="likePost(post)">{{ post.is_liked ? '❤️' : '🤍' }} {{ formatCount(post.like_count) }}</span>
            <span v-if="post.topics && post.topics.length" class="post-topic-tag">#{{ post.topics[0].name }}</span>
          </div>
        </div>
        <div v-if="loading" class="loading">加载中...</div>
        <div v-if="!loading && !hasMore && posts.length" class="no-more">没有更多了</div>
        <div v-if="!loading && !posts.length" class="empty">暂无内容</div>
      </div>

      <!-- 图集列表 -->
      <div v-else-if="activeMainTab === 'gallery'" class="gallery-list">
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="!galleryItems.length" class="empty">暂无图集</div>
        <div v-else class="gallery-grid">
          <div v-for="item in galleryItems" :key="item.id" class="gallery-item" @click="goToGalleryDetail(item.id)">
            <div class="gallery-cover">
              <img :src="item.cover" :alt="item.title" />
              <div class="gallery-info">
                <span class="views">👁 {{ formatCount(item.views) }}</span>
                <span class="count">📷 {{ item.count }}</span>
              </div>
              <div class="gallery-status" v-if="item.status === 'ongoing'">连载中</div>
            </div>
            <p class="gallery-title">{{ item.title }}</p>
          </div>
        </div>
      </div>

      <!-- 小说列表 -->
      <div v-else-if="activeMainTab === 'novel'" class="novel-list">
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="!novelItems.length" class="empty">暂无小说</div>
        <div v-else class="novel-grid">
          <div v-for="item in novelItems" :key="item.id" class="novel-item" @click="goToNovelDetail(item)">
            <div class="novel-cover-wrap">
              <img :src="item.cover" :alt="item.title" class="novel-cover" />
              <span v-if="selectedNovelType === 'audio'" class="audio-badge">🎧</span>
              <div class="novel-status" v-if="item.status === 'ongoing'">连载中</div>
            </div>
            <div class="novel-info">
              <p class="novel-title">{{ item.title }}</p>
              <p class="novel-author">{{ item.author }}</p>
              <p class="novel-chapters">共{{ item.chapters }}章</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 发布按钮 -->
    <div class="publish-btn" @click="showPublishModal = true" v-if="activeMainTab === 'community'">
      <img src="/images/backgrounds/publish.webp" alt="发布" class="publish-icon" />
    </div>

    <!-- 发布类型选择弹窗 -->
    <div class="publish-modal-overlay" v-if="showPublishModal" @click="showPublishModal = false">
      <div class="publish-modal" @click.stop>
        <div class="modal-handle"></div>
        <h3 class="modal-title">选择发布类型</h3>
        <div class="publish-types">
          <div class="publish-type-item" @click="goPublishImage">
            <img src="/images/backgrounds/publish_img_1.webp" alt="图片" class="type-icon" />
            <span class="type-label">图片</span>
          </div>
          <div class="publish-type-item" @click="goPublishVideo">
            <img src="/images/backgrounds/publish_video.webp" alt="视频" class="type-icon" />
            <span class="type-label">视频</span>
          </div>
          <div class="publish-type-item" @click="goPublishTextImage">
            <img src="/images/backgrounds/publish_img_text.webp" alt="图文" class="type-icon" />
            <span class="type-label">图文</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部导航 - 使用公共组件 -->
    <BottomNav />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import api from '@/utils/api'
import { getAvatarUrl } from '@/utils/avatar'
import { formatCount, formatCommentTime } from '@/utils/format'
import { getVipLevelIcon } from '@/constants/vip'
import { useAbortController } from '@/composables/useAbortController'
import { useActionLock, useDebounce } from '@/composables/useDebounce'
import BottomNav from '@/components/common/BottomNav.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 请求取消控制器 - 防止内存泄漏
const { signal } = useAbortController()

// 点赞防重复
const { withLock } = useActionLock()

// 获取VIP图标 - 使用统一的常量
const getVipIcon = (level) => getVipLevelIcon(level)

// 固定头部相关
const fixedHeaderRef = ref(null)
const filterBarRef = ref(null)
const fixedHeaderHeight = ref(0)
const isFilterFixed = ref(false)
const filterBarOriginalTop = ref(0)

// 计算固定头部高度
const updateHeaderHeight = () => {
  if (fixedHeaderRef.value) {
    fixedHeaderHeight.value = fixedHeaderRef.value.offsetHeight
  }
}

// 记录筛选栏原始位置
const updateFilterBarPosition = () => {
  if (filterBarRef.value && !isFilterFixed.value) {
    const rect = filterBarRef.value.getBoundingClientRect()
    filterBarOriginalTop.value = rect.top + window.scrollY
  }
}

// 滚动处理
const handleScroll = () => {
  if (!filterBarRef.value) return
  
  const scrollY = window.scrollY
  // 当滚动超过筛选栏原始位置减去固定头部高度时，固定筛选栏
  const threshold = filterBarOriginalTop.value - fixedHeaderHeight.value
  
  if (scrollY >= threshold && !isFilterFixed.value) {
    isFilterFixed.value = true
  } else if (scrollY < threshold && isFilterFixed.value) {
    isFilterFixed.value = false
  }
}

// 主Tab配置
const mainTabs = [
  { label: '社区', value: 'community', activeIcon: '/images/backgrounds/tab_one_active.webp' },
  { label: '图集', value: 'gallery', activeIcon: '/images/backgrounds/tab_two_active.webp' },
  { label: '小说', value: 'novel', activeIcon: '/images/backgrounds/tab_three_active.webp' }
]

const filterTabs = [
  { label: '推荐', value: 'recommend' },
  { label: '最新', value: 'latest' },
  { label: '热评', value: 'hot_comment' },
  { label: '最热', value: 'hot' },
  { label: '视频', value: 'video' }
]

const activeMainTab = ref('community')
const activeFilter = ref('recommend')
const selectedCategory = ref(null)  // 选中的一级分类ID
const selectedTopic = ref(null)     // 选中的二级话题ID

// 分类数据
const categoriesData = ref([])  // 完整的分类树数据
const topCategories = ref([])   // 一级分类列表
const topicsMap = ref({})       // 话题ID到名称的映射

// 当前选中分类的子话题
const currentSubTopics = computed(() => {
  if (!selectedCategory.value) return []
  const cat = categoriesData.value.find(c => c.id === selectedCategory.value)
  return cat?.children || []
})

const posts = ref([])
const iconAds = ref([])
const galleryItems = ref([])
const novelItems = ref([])
const loading = ref(false)
const hasMore = ref(true)
const page = ref(1)

// 切换主Tab
const switchMainTab = (tab) => {
  activeMainTab.value = tab
  if (tab === 'community') {
    fetchPosts(true)
  } else if (tab === 'gallery') {
    fetchGalleries()
  } else if (tab === 'novel') {
    fetchNovels()
  }
}

// 选择一级分类
const selectCategory = (cat) => {
  selectedCategory.value = cat.id
  selectedTopic.value = null  // 重置二级话题选择
  fetchPosts(true)
}

// 选择二级话题 - 跳转到话题列表页
const selectTopic = (topic) => {
  router.push({
    path: `/user/community/topic/${topic.id}`,
    query: { name: topic.name }
  })
}

// 获取图标广告
const fetchIconAds = async () => {
  try {
    const res = await api.get('/ads/icons')
    iconAds.value = res.data || []
  } catch (e) {
    console.error('获取广告失败', e)
  }
}

// 获取分类数据（带子话题）
const fetchCategories = async () => {
  try {
    const res = await api.get('/community/topics/categories')
    const data = res.data || []
    categoriesData.value = data
    
    // 构建一级分类列表
    topCategories.value = data.map(c => ({ id: c.id, name: c.name, icon: c.icon }))
    
    // 默认选中第一个分类
    if (data.length > 0 && !selectedCategory.value) {
      selectedCategory.value = data[0].id
    }
    
    // 构建话题映射
    data.forEach(cat => {
      topicsMap.value[cat.id] = cat.name
      if (cat.children) {
        cat.children.forEach(t => {
          topicsMap.value[t.id] = t.name
        })
      }
    })
  } catch (e) {
    console.error('获取分类失败', e)
    // 如果API不存在，使用旧的话题接口
    fetchTopicsLegacy()
  }
}

// 兼容旧的话题接口
const fetchTopicsLegacy = async () => {
  try {
    const res = await api.get('/community/topics', { params: { page_size: 30 } })
    const data = res.data || []
    topCategories.value = data.map(t => ({ id: t.id, name: t.name }))
    
    // 默认选中第一个
    if (data.length > 0 && !selectedCategory.value) {
      selectedCategory.value = data[0].id
    }
    
    data.forEach(t => { topicsMap.value[t.id] = t.name })
  } catch (e) {
    console.error('获取话题失败', e)
  }
}

// 获取动态列表 - 添加请求取消支持
const fetchPosts = async (reset = false) => {
  if (loading.value) return
  if (reset) {
    page.value = 1
    hasMore.value = true
    posts.value = []
  }
  if (!hasMore.value) return

  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: 20,
      feed_type: activeFilter.value === 'video' ? 'recommend' : activeFilter.value
    }
    // 如果选择了二级话题，按话题筛选
    if (selectedTopic.value) {
      params.topic_id = selectedTopic.value
    } 
    // 如果只选择了一级分类（非热门推荐），可以按分类下所有话题筛选
    // 这里简化处理，暂时不做

    const res = await api.get('/community/posts', { params, signal })
    const data = res.data || []
    
    if (data.length < 20) hasMore.value = false
    posts.value = reset ? data : [...posts.value, ...data]
    page.value++
  } catch (e) {
    // 忽略请求取消错误
    if (e.name !== 'AbortError' && e.name !== 'CanceledError') {
      console.error('获取动态失败', e)
    }
  } finally {
    loading.value = false
  }
}

// 点赞 - 添加防重复点击
const likePost = async (post) => {
  await withLock(`like_post_${post.id}`, async () => {
    try {
      const res = await api.post(`/community/posts/${post.id}/like`, null, { signal })
      post.is_liked = res.data.liked
      post.like_count = res.data.like_count
    } catch (e) {
      if (e.name !== 'AbortError' && e.name !== 'CanceledError') {
        console.error('点赞失败', e)
      }
    }
  })
}

// 使用统一的格式化函数（已从 @/utils/format 导入）
const formatTime = (time) => formatCommentTime(time)

const goToDetail = (id) => router.push(`/user/community/post/${id}`)

// 发布弹窗
const showPublishModal = ref(false)
const goPublishImage = () => {
  showPublishModal.value = false
  router.push('/user/publish/image')
}
const goPublishVideo = () => {
  showPublishModal.value = false
  router.push('/user/publish/video')
}
const goPublishTextImage = () => {
  showPublishModal.value = false
  router.push('/user/publish/text-image')
}

const goToUserProfile = (userId) => {
  if (userId) router.push(`/user/member/${userId}`)
}
const goToGalleryDetail = (id) => router.push(`/user/gallery/${id}`)
const goToNovelDetail = (item) => {
  // 有声小说跳转到专用播放器
  if (selectedNovelType.value === 'audio') {
    router.push(`/user/audio-novel/${item.id}`)
  } else {
    router.push(`/user/novel/${item.id}`)
  }
}
const previewImage = (images, idx) => { /* 图片预览 */ }
const openAdLink = (ad) => { if (ad.link) window.open(ad.link, '_blank') }

// 图集相关
const galleryCategories = ref([])
const selectedGalleryCategory = ref(null)

const fetchGalleryCategories = async () => {
  try {
    const res = await api.get('/gallery-novel/gallery/categories')
    galleryCategories.value = [
      { id: null, name: '全部' },
      ...(res.data || [])
    ]
  } catch (e) {
    console.error('获取图集分类失败', e)
  }
}

const fetchGalleries = async () => {
  loading.value = true
  try {
    const params = { page: 1, page_size: 30 }
    if (selectedGalleryCategory.value) {
      params.category_id = selectedGalleryCategory.value
    }
    const res = await api.get('/gallery-novel/gallery/list', { params })
    galleryItems.value = (res.data || []).map(g => ({
      id: g.id,
      title: g.title,
      cover: g.cover,
      views: g.view_count,
      count: g.image_count,
      status: g.status
    }))
  } catch (e) {
    console.error('获取图集失败', e)
  } finally {
    loading.value = false
  }
}

const selectGalleryCategory = (catId) => {
  selectedGalleryCategory.value = catId
  fetchGalleries()
}

// 小说相关
const novelCategories = ref([])
const selectedNovelType = ref('text')
const selectedNovelCategory = ref(null)

const fetchNovelCategories = async () => {
  try {
    const res = await api.get('/gallery-novel/novel/categories', { params: { novel_type: selectedNovelType.value } })
    novelCategories.value = [
      { id: null, name: '全部' },
      ...(res.data || [])
    ]
  } catch (e) {
    console.error('获取小说分类失败', e)
  }
}

const fetchNovels = async () => {
  loading.value = true
  try {
    const params = { page: 1, page_size: 30, novel_type: selectedNovelType.value }
    if (selectedNovelCategory.value) {
      params.category_id = selectedNovelCategory.value
    }
    const res = await api.get('/gallery-novel/novel/list', { params })
    novelItems.value = (res.data || []).map(n => ({
      id: n.id,
      title: n.title,
      author: n.author || '佚名',
      cover: n.cover,
      chapters: n.chapter_count,
      status: n.status
    }))
  } catch (e) {
    console.error('获取小说失败', e)
  } finally {
    loading.value = false
  }
}

const switchNovelType = (type) => {
  selectedNovelType.value = type
  selectedNovelCategory.value = null
  fetchNovelCategories()
  fetchNovels()
}

const selectNovelCategory = (catId) => {
  selectedNovelCategory.value = catId
  fetchNovels()
}

onMounted(() => {
  // 从URL参数读取tab
  const tabParam = route.query.tab
  if (tabParam && ['community', 'gallery', 'novel'].includes(tabParam)) {
    activeMainTab.value = tabParam
  }
  
  // 从URL参数读取小说类型
  const typeParam = route.query.type
  if (typeParam && ['text', 'audio'].includes(typeParam)) {
    selectedNovelType.value = typeParam
  }
  
  fetchIconAds()
  fetchCategories()
  fetchGalleryCategories()
  fetchNovelCategories()
  
  // 根据当前tab加载数据
  if (activeMainTab.value === 'community') {
    fetchPosts(true)
  } else if (activeMainTab.value === 'gallery') {
    fetchGalleries()
  } else if (activeMainTab.value === 'novel') {
    fetchNovels()
  }
  
  // 初始化固定头部高度
  nextTick(() => {
    updateHeaderHeight()
    // 延迟计算筛选栏位置，等待内容渲染
    setTimeout(() => {
      updateFilterBarPosition()
    }, 100)
  })
  
  // 监听滚动
  window.addEventListener('scroll', handleScroll, { passive: true })
  // 监听窗口大小变化
  window.addEventListener('resize', () => {
    updateHeaderHeight()
    updateFilterBarPosition()
  }, { passive: true })
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', handleScroll)
  window.removeEventListener('resize', updateHeaderHeight)
})
</script>


<style lang="scss" scoped>
.community-page {
  min-height: 100vh;
  background: #0d0d0d;
  padding-bottom: 70px;
}

/* 头部占位 */
.header-placeholder {
  width: 100%;
}

/* 顶部导航 - 固定定位 */
.top-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: #0d0d0d;
  
  @media (min-width: 768px) {
    max-width: 750px;
    left: 50%;
    transform: translateX(-50%);
  }
  
  @media (min-width: 1024px) {
    max-width: 900px;
  }
  
  @media (min-width: 1280px) {
    max-width: 1200px;
  }
}

.main-tabs {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  gap: 20px;
}

.tab-item {
  cursor: pointer;
}

.tab-item .tab-text {
  color: #666;
  font-size: 17px;
}

.tab-item.active .tab-text {
  color: #fff;
  font-weight: bold;
}

.tab-item .tab-icon {
  height: 30px;
  width: auto;
}

.search-btn {
  margin-left: auto;
}

.search-btn img {
  width: 28px;
  height: 28px;
}

/* 一级分类 */
.category-tabs {
  padding: 0 16px 10px;
}

.category-scroll {
  display: flex;
  gap: 18px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.category-scroll::-webkit-scrollbar { display: none; }

.category-tab {
  flex-shrink: 0;
  color: #888;
  font-size: 14px;
  cursor: pointer;
  white-space: nowrap;
  padding: 4px 0;
}

.category-tab.active {
  color: #fff;
  font-weight: 600;
}

/* 二级分类卡片 */
.topic-cards {
  padding: 0 12px 12px;
}

.topic-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.topic-card {
  background-color: #1a1a1a;
  background-size: cover;
  background-position: center bottom;
  border-radius: 8px;
  padding: 10px 8px;
  min-height: 60px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
}

.topic-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 8px;
  pointer-events: none;
}

.topic-card:hover {
  background-color: #222;
}

.topic-card.active {
  border-color: #8b5cf6;
}

.topic-name {
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  position: relative;
  z-index: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.topic-count {
  color: rgba(255,255,255,0.8);
  font-size: 12px;
  margin-top: 4px;
  position: relative;
  z-index: 1;
}

/* 响应式 - 平板及以上 */
@media (min-width: 768px) {
  .community-page {
    max-width: 750px;
    margin: 0 auto;
  }
  
  .topic-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
  }
  
  .topic-card {
    min-height: 70px;
    padding: 12px 10px;
  }
  
  .topic-name {
    font-size: 14px;
  }
  
  .topic-count {
    font-size: 12px;
  }
  
  .posts-list {
    padding: 0 16px;
  }
  
  .post-card {
    padding: 20px;
  }
}

/* 响应式 - 桌面端 */
@media (min-width: 1024px) {
  .community-page {
    max-width: 900px;
  }
  
  .topic-grid {
    grid-template-columns: repeat(5, 1fr);
  }
}

/* 响应式 - 大屏 */
@media (min-width: 1280px) {
  .community-page {
    max-width: 1200px;
  }
}

/* 筛选标签 */
.filter-tabs {
  display: flex;
  gap: 24px;
  padding: 10px 16px 12px;
  border-bottom: 1px solid #1a1a1a;
  background: #0d0d0d;
  transition: none;
  
  /* 固定状态 */
  &.is-fixed {
    position: fixed;
    left: 0;
    right: 0;
    z-index: 99;
    
    @media (min-width: 768px) {
      max-width: 750px;
      left: 50%;
      transform: translateX(-50%);
    }
    
    @media (min-width: 1024px) {
      max-width: 900px;
    }
    
    @media (min-width: 1280px) {
      max-width: 1200px;
    }
  }
}

/* 筛选栏占位 */
.filter-placeholder {
  height: 46px; /* 与筛选栏高度一致 */
}

.filter-tab {
  color: #666;
  font-size: 14px;
  cursor: pointer;
  padding: 4px 0;
  position: relative;
}

.filter-tab.active {
  color: #fff;
  font-weight: 500;
}

.filter-tab.active::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 2px;
  background: #8b5cf6;
  border-radius: 1px;
}

/* 图标广告位 - 与首页一致的样式 */
.promo-grid-fixed {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 4px;
  padding: 8px 8px 4px;
}

.promo-scroll-container {
  overflow: hidden;
  padding: 4px 0;
  
  .promo-grid-scroll {
    display: flex;
    gap: 8px;
    padding: 0 8px;
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
  gap: 4px;
  cursor: pointer;
  min-width: 56px;
  transition: transform 0.2s;
  
  &:hover {
    transform: scale(1.05);
  }
  
  .promo-icon-wrap {
    width: 56px;
    height: 56px;
    border-radius: 12px;
    display: flex;
    justify-content: center;
    align-items: center;
    background: linear-gradient(135deg, #667eea, #764ba2);
    overflow: hidden;
    
    .promo-img {
      width: 100%;
      height: 100%;
      border-radius: 12px;
      object-fit: cover;
    }
    
    .fallback-icon {
      font-size: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 100%;
      height: 100%;
    }
  }
  
  .promo-name {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.7);
    text-align: center;
    max-width: 54px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

/* 动态列表 */
.posts-list {
  padding: 0 12px;
}

.post-card {
  background: #151515;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}

.post-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  
  &.clickable {
    cursor: pointer;
    transition: transform 0.2s;
    
    &:hover {
      transform: scale(1.05);
    }
  }
}

.user-info {
  margin-left: 12px;
}

.user-name-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.username {
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  
  &.clickable {
    cursor: pointer;
    
    &:hover {
      color: #a855f7;
    }
  }
}

.vip-icon {
  width: 36px;
  height: 18px;
  object-fit: contain;
}

.time {
  color: #666;
  font-size: 12px;
}

.post-text {
  color: #ddd;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 图片网格 */
.post-images {
  margin-bottom: 12px;
}

.images-grid {
  display: grid;
  gap: 4px;
  border-radius: 8px;
  overflow: hidden;
}

.images-grid.grid-1 { grid-template-columns: 1fr; max-width: 70%; }
.images-grid.grid-2 { grid-template-columns: repeat(2, 1fr); }
.images-grid.grid-3 { grid-template-columns: repeat(3, 1fr); }
.images-grid.grid-4 { grid-template-columns: repeat(4, 1fr); }

.img-item {
  position: relative;
  aspect-ratio: 1;
}

.img-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.more-count {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
}

.post-stats {
  display: flex;
  align-items: center;
  gap: 20px;
  color: #666;
  font-size: 13px;
}

.post-stats span {
  cursor: pointer;
}

.post-topic-tag {
  margin-left: auto;
  padding: 4px 12px;
  background: transparent;
  border: 1px solid rgba(168, 85, 247, 0.5);
  border-radius: 12px;
  color: #a855f7;
  font-size: 12px;
  cursor: pointer;
}

/* 图集列表 */
.gallery-list {
  padding: 12px;
}

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px 12px;
}

.gallery-item {
  cursor: pointer;
  display: flex;
  flex-direction: column;
}

.gallery-cover {
  position: relative;
  width: 100%;
  padding-top: 133.33%; /* 3:4 比例 */
  border-radius: 8px;
  overflow: hidden;
  background: #1a1a1a;
}

.gallery-cover img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
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
}

.gallery-status {
  position: absolute;
  top: 6px;
  right: 6px;
  background: rgba(139, 92, 246, 0.9);
  color: #fff;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.gallery-title {
  color: #eee;
  font-size: 13px;
  font-weight: 500;
  margin: 8px 2px 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.3;
}

/* 图集列表响应式 */
@media (min-width: 480px) {
  .gallery-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
  }
}

@media (min-width: 768px) {
  .gallery-grid {
    grid-template-columns: repeat(5, 1fr);
    gap: 20px;
  }
  
  .gallery-title {
    font-size: 14px;
  }
}

@media (min-width: 1024px) {
  .gallery-grid {
    grid-template-columns: repeat(6, 1fr);
  }
}

/* 小说类型切换 */
.novel-type-tabs {
  padding: 0 16px 10px;
}

.type-tabs {
  display: flex;
  gap: 20px;
  margin-bottom: 12px;
}

.type-tab {
  color: #666;
  font-size: 15px;
  cursor: pointer;
  padding: 4px 0;
  position: relative;
}

.type-tab.active {
  color: #fff;
  font-weight: 600;
}

.type-tab.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: #8b5cf6;
  border-radius: 1px;
}

/* 小说列表 */
.novel-list {
  padding: 12px;
}

.novel-grid {
  display: grid !important;
  grid-template-columns: repeat(3, 1fr) !important;
  gap: 16px 12px !important;
  align-items: start !important;
}

.novel-item {
  cursor: pointer;
  display: flex !important;
  flex-direction: column !important;
  width: 100% !important;
  overflow: hidden;
}

.novel-cover-wrap {
  position: relative !important;
  width: 100% !important;
  height: 0 !important;
  padding-bottom: 133.33% !important; /* 3:4 比例 */
  border-radius: 8px !important;
  overflow: hidden !important;
  background: #1a1a1a !important;
}

.novel-cover {
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  width: 100% !important;
  height: 100% !important;
  object-fit: cover !important;
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

.novel-status {
  position: absolute;
  top: 6px;
  right: 6px;
  background: rgba(234, 179, 8, 0.9);
  color: #000;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
  z-index: 1;
}

.novel-info {
  padding: 8px 2px 0;
}

.novel-title {
  color: #eee;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.3;
}

.novel-author {
  color: #888;
  font-size: 11px;
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.novel-chapters {
  color: #666;
  font-size: 11px;
}

/* 发布按钮 */
.publish-btn {
  position: fixed;
  right: 20px;
  bottom: 90px;
  width: 50px;
  height: 50px;
  cursor: pointer;
  z-index: 100;
}

.publish-icon {
  width: 50px;
  height: 50px;
  object-fit: contain;
}

/* 发布类型弹窗 */
.publish-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  z-index: 200;
  display: flex;
  align-items: flex-end;
}

.publish-modal {
  width: 100%;
  background: linear-gradient(180deg, #1a2a4a 0%, #0d1525 100%);
  border-radius: 20px 20px 0 0;
  padding: 16px 24px 40px;
}

.modal-handle {
  width: 40px;
  height: 4px;
  background: #444;
  border-radius: 2px;
  margin: 0 auto 20px;
}

.modal-title {
  text-align: center;
  color: #fff;
  font-size: 16px;
  font-weight: 500;
  margin: 0 0 24px;
}

.publish-types {
  display: flex;
  justify-content: center;
  gap: 40px;
}

.publish-type-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.publish-type-item .type-icon {
  width: 56px;
  height: 56px;
  object-fit: contain;
  border-radius: 12px;
}

.publish-type-item .type-label {
  color: #fff;
  font-size: 14px;
}

.loading, .no-more, .empty {
  text-align: center;
  padding: 30px;
  color: #666;
}
</style>
