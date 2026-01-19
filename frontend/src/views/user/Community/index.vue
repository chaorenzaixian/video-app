<template>
  <div class="community-page" ref="scrollContainer">
    <!-- 固定顶部区域：导航 + 分类 -->
    <div class="fixed-top" ref="fixedTopRef">
      <!-- 顶部导航 -->
      <div class="main-tabs">
        <div v-for="tab in mainTabs" :key="tab.value" :class="['tab-item', { active: activeMainTab === tab.value }]" @click="switchMainTab(tab.value)">
          <img v-if="activeMainTab === tab.value && tab.activeIcon" :src="tab.activeIcon" :alt="tab.label" class="tab-icon" />
          <span v-else class="tab-text">{{ tab.label }}</span>
        </div>
        <router-link to="/user/search" class="search-btn">
          <img src="/images/backgrounds/ic_search.webp" alt="搜索" />
        </router-link>
      </div>

      <!-- 社区分类 -->
      <template v-if="activeMainTab === 'community'">
        <div class="category-tabs">
          <div class="category-scroll">
            <span v-for="cat in topCategories" :key="cat.id" :class="['category-tab', { active: selectedCategory === cat.id }]" @click="selectCategory(cat)">{{ cat.name }}</span>
          </div>
        </div>
      </template>

      <!-- 图集分类 -->
      <div class="category-tabs" v-if="activeMainTab === 'gallery'">
        <div class="category-scroll">
          <span v-for="cat in galleryCategories" :key="cat.id" :class="['category-tab', { active: selectedGalleryCategory === cat.id }]" @click="selectGalleryCategory(cat.id)">{{ cat.name }}</span>
        </div>
      </div>

      <!-- 小说分类 -->
      <div class="novel-type-tabs" v-if="activeMainTab === 'novel'">
        <div class="type-tabs">
          <span :class="['type-tab', { active: selectedNovelType === 'text' }]" @click="switchNovelType('text')">文字小说</span>
          <span :class="['type-tab', { active: selectedNovelType === 'audio' }]" @click="switchNovelType('audio')">有声小说</span>
        </div>
        <div class="category-scroll">
          <span v-for="cat in novelCategories" :key="cat.id" :class="['category-tab', { active: selectedNovelCategory === cat.id }]" @click="selectNovelCategory(cat.id)">{{ cat.name }}</span>
        </div>
      </div>
    </div>
    
    <!-- 占位元素 -->
    <div :class="['header-placeholder', { 'novel-mode': activeMainTab === 'novel' }]"></div>

    <!-- 图标广告位 -->
    <IconAdsGrid :ads="iconAds" />
    
    <!-- 社区话题卡片 -->
    <template v-if="activeMainTab === 'community'">
      <div class="topic-cards" v-if="currentSubTopics.length">
        <div class="topic-grid">
          <div v-for="topic in currentSubTopics" :key="topic.id" :class="['topic-card', { active: selectedTopic === topic.id }]" :style="topic.cover ? { backgroundImage: `url(${topic.cover})` } : {}" @click="selectTopic(topic)">
            <span class="topic-name">{{ topic.name }}</span>
            <span class="topic-count">{{ formatCount(topic.post_count) }}个帖子</span>
          </div>
        </div>
      </div>
    </template>
    
    <!-- 筛选栏 - sticky定位，滚动到一级分类下固定 -->
    <div class="filter-tabs" v-if="activeMainTab === 'community'">
      <span v-for="filter in filterTabs" :key="filter.value" :class="['filter-tab', { active: activeFilter === filter.value }]" @click="setFilter(filter.value)">{{ filter.label }}</span>
    </div>

    <!-- 内容区域 -->
    <div class="content-area">
      <PostList v-if="activeMainTab === 'community'" :posts="posts" :loading="communityLoading" :has-more="hasMore" @detail="goToDetail" @profile="goToUserProfile" @like="likePost" />
      <GalleryList v-else-if="activeMainTab === 'gallery'" :items="galleryItems" :loading="galleryLoading" @detail="goToGalleryDetail" />
      <NovelList v-else-if="activeMainTab === 'novel'" :items="novelItems" :loading="novelLoading" :is-audio="selectedNovelType === 'audio'" @detail="goToNovelDetail" />
    </div>

    <!-- 发布按钮 -->
    <div class="publish-btn" @click="showPublishModal = true" v-if="activeMainTab === 'community'">
      <img src="/images/backgrounds/publish.webp" alt="发布" class="publish-icon" />
    </div>

    <!-- 发布弹窗 -->
    <PublishModal :visible="showPublishModal" @close="showPublishModal = false" @publish="handlePublish" />

    <BottomNav />
  </div>
</template>

<script setup>
defineOptions({ name: 'Community' })

import { ref, onMounted, onActivated, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '@/utils/api'
import { formatCount } from '@/utils/format'
import { useAbortController } from '@/composables/useAbortController'
import { useActionLock } from '@/composables/useDebounce'
import BottomNav from '@/components/common/BottomNav.vue'
import IconAdsGrid from '@/components/common/IconAdsGrid.vue'
import PostList from './components/PostList.vue'
import GalleryList from './components/GalleryList.vue'
import NovelList from './components/NovelList.vue'
import PublishModal from './components/PublishModal.vue'
import { useCommunityData } from './composables/useCommunityData'
import { useGalleryData } from './composables/useGalleryData'
import { useNovelData } from './composables/useNovelData'

const router = useRouter()
const route = useRoute()
const { signal } = useAbortController()
const { withLock } = useActionLock()
const scrollContainer = ref(null)
const fixedTopRef = ref(null)

// Tab配置
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
const iconAds = ref([])
const showPublishModal = ref(false)

// 使用composables
const { topCategories, selectedCategory, selectedTopic, currentSubTopics, posts, loading: communityLoading, hasMore, activeFilter, fetchCategories, fetchPosts, likePost: doLikePost, selectCategory } = useCommunityData(signal)
const { galleryCategories, selectedGalleryCategory, galleryItems, loading: galleryLoading, fetchGalleryCategories, fetchGalleries, selectGalleryCategory } = useGalleryData(signal)
const { novelCategories, selectedNovelType, selectedNovelCategory, novelItems, loading: novelLoading, fetchNovelCategories, fetchNovels, switchNovelType, selectNovelCategory } = useNovelData(signal)

// 切换主Tab
const switchMainTab = (tab) => {
  activeMainTab.value = tab
  if (tab === 'community') fetchPosts(true)
  else if (tab === 'gallery') fetchGalleries()
  else if (tab === 'novel') fetchNovels()
}

// 设置筛选
const setFilter = (value) => {
  activeFilter.value = value
  fetchPosts(true)
}

// 选择话题
const selectTopic = (topic) => {
  router.push({ path: `/user/community/topic/${topic.id}`, query: { name: topic.name } })
}

// 点赞（带防重复）
const likePost = async (post) => {
  await withLock(`like_post_${post.id}`, () => doLikePost(post))
}

// 获取广告
const fetchIconAds = async () => {
  try {
    const res = await api.get('/ads/icons', { signal })
    iconAds.value = res.data || []
  } catch (e) { /* ignore */ }
}

// 导航
const goToDetail = (id) => router.push(`/user/community/post/${id}`)
const goToUserProfile = (userId) => { if (userId) router.push(`/user/member/${userId}`) }
const goToGalleryDetail = (id) => router.push(`/user/gallery/${id}`)
const goToNovelDetail = (item) => {
  router.push(selectedNovelType.value === 'audio' ? `/user/audio-novel/${item.id}` : `/user/novel/${item.id}`)
}

// 发布
const handlePublish = (type) => {
  showPublishModal.value = false
  const routes = { image: '/user/publish/image', video: '/user/publish/video', 'text-image': '/user/publish/text-image' }
  router.push(routes[type])
}

// 设置固定头部高度
const updateHeaderHeight = () => {
  if (fixedTopRef.value) {
    const rect = fixedTopRef.value.getBoundingClientRect()
    const height = Math.ceil(rect.height)
    headerHeight.value = height
    document.documentElement.style.setProperty('--community-header-height', `${height}px`)
  }
}

onMounted(() => {
  const tabParam = route.query.tab
  if (tabParam && ['community', 'gallery', 'novel'].includes(tabParam)) activeMainTab.value = tabParam
  const typeParam = route.query.type
  if (typeParam && ['text', 'audio'].includes(typeParam)) selectedNovelType.value = typeParam
  
  fetchIconAds()
  fetchCategories()
  fetchGalleryCategories()
  fetchNovelCategories()
  
  if (activeMainTab.value === 'community') fetchPosts(true)
  else if (activeMainTab.value === 'gallery') fetchGalleries()
  else if (activeMainTab.value === 'novel') fetchNovels()
  
  // 初始化头部高度
  updateHeaderHeight()
  // DOM 渲染完成后再次更新
  setTimeout(updateHeaderHeight, 100)
  // 监听窗口大小变化
  window.addEventListener('resize', updateHeaderHeight)
})

// keep-alive 激活时滚动到顶部
onActivated(async () => {
  await nextTick()
  // 滚动容器到顶部
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = 0
  }
  // 重新计算头部高度
  updateHeaderHeight()
})

onUnmounted(() => {
  window.removeEventListener('resize', updateHeaderHeight)
})
</script>

<style lang="scss" scoped>
.community-page {
  height: 100vh;
  height: 100dvh;
  background: #0d0d0d;
  padding-bottom: 70px;
  overflow-x: hidden;
  overflow-y: auto;
  
  @media (min-width: 768px) {
    max-width: 750px;
    margin: 0 auto;
  }
  @media (min-width: 1024px) { max-width: 900px; }
  @media (min-width: 1280px) { max-width: 1100px; }
}

// 固定顶部区域
.fixed-top {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: #0d0d0d;
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
  
  @media (min-width: 768px) {
    max-width: 750px;
    left: 50%;
    transform: translateX(-50%);
  }
  @media (min-width: 1024px) { max-width: 900px; }
  @media (min-width: 1280px) { max-width: 1100px; }
}

// 占位元素 - 使用固定高度
.header-placeholder {
  height: 105px;  /* 54px(导航) + 51px(分类) */
  
  // 小说tab时占位更高（有两行分类）
  &.novel-mode {
    height: 140px;
  }
}

.main-tabs {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  gap: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.tab-item {
  cursor: pointer;
  .tab-text { color: #666; font-size: 17px; }
  &.active .tab-text { color: #fff; font-weight: bold; }
  .tab-icon { height: 30px; width: auto; }
}

.search-btn {
  margin-left: auto;
  img { width: 28px; height: 28px; }
}

.category-tabs { padding: 0 16px 10px; }

.category-scroll {
  display: flex;
  gap: 18px;
  overflow-x: auto;
  padding-bottom: 4px;
  &::-webkit-scrollbar { display: none; }
}

.category-tab {
  flex-shrink: 0;
  color: #888;
  font-size: 15px;
  cursor: pointer;
  white-space: nowrap;
  padding: 4px 0;
  &.active { color: #fff; font-weight: 600; }
}

.topic-cards { padding: 0 12px 12px; }

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
  
  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    border-radius: 8px;
    pointer-events: none;
  }
  &:hover { background-color: #222; }
  &.active { border-color: #8b5cf6; }
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

.filter-tabs {
  display: flex;
  gap: 24px;
  padding: 10px 16px 12px;
  border-bottom: 1px solid #1a1a1a;
  background: #0d0d0d;
  position: sticky;
  top: 105px;  /* 固定值：54px(导航) + 51px(分类) */
  z-index: 90;
}

.filter-tab {
  color: #666;
  font-size: 14px;
  cursor: pointer;
  padding: 4px 0;
  position: relative;
  &.active {
    color: #fff;
    font-weight: 500;
    &::after {
      content: '';
      position: absolute;
      bottom: -2px;
      left: 0;
      right: 0;
      height: 2px;
      background: #8b5cf6;
      border-radius: 1px;
    }
  }
}

.novel-type-tabs { padding: 0 16px 10px; }

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
      background: #8b5cf6;
      border-radius: 1px;
    }
  }
}

.content-area { padding: 0 12px; }

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

@media (min-width: 768px) {
  .topic-grid { grid-template-columns: repeat(4, 1fr); gap: 12px; }
  .topic-card { min-height: 70px; padding: 12px 10px; }
  .main-tabs { padding: 14px 20px; }
  .filter-tabs { gap: 30px; }
}

@media (min-width: 1024px) {
  .topic-grid { grid-template-columns: repeat(5, 1fr); }
  .main-tabs { padding: 16px 24px; gap: 28px; }
}

@media (min-width: 1280px) {
  .topic-grid { grid-template-columns: repeat(6, 1fr); gap: 14px; }
}

// 触摸设备优化
@media (hover: none) {
  .topic-card:hover { background-color: #1a1a1a; }
  .topic-card:active { background-color: #222; }
}
</style>
