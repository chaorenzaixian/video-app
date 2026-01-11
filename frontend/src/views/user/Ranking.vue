<template>
  <div class="ranking-page">
    <!-- 顶部返回 -->
    <div class="page-header">
      <span class="back-btn" @click="$router.back()">‹</span>
    </div>

    <!-- 热门排行标题图 -->
    <div class="ranking-banner">
      <img src="/images/ranking/ranking_header.webp" alt="热门排行" class="banner-img" />
      <p class="banner-subtitle">根据实时热度排行</p>
    </div>

    <!-- 分类标签 -->
    <div class="category-tabs">
      <span 
        v-for="cat in categories" 
        :key="cat.key"
        :class="['tab-item', { active: activeCategory === cat.key }]"
        @click="switchCategory(cat.key)"
      >
        {{ cat.label }}
      </span>
    </div>

    <!-- 时间筛选 -->
    <div class="time-tabs">
      <span 
        v-for="time in timeFilters" 
        :key="time.key"
        :class="['time-item', { active: activeTime === time.key }]"
        @click="switchTime(time.key)"
      >
        {{ time.label }}
      </span>
    </div>

    <!-- 排行列表 -->
    <div class="ranking-list" ref="listRef" @scroll="handleScroll">
      <div v-if="loading && list.length === 0" class="loading-state">
        <div v-for="i in 5" :key="i" class="skeleton-item">
          <div class="skeleton-cover"></div>
          <div class="skeleton-info">
            <div class="skeleton-title"></div>
            <div class="skeleton-meta"></div>
          </div>
        </div>
      </div>

      <div v-else-if="!loading && list.length === 0" class="empty-state">
        暂无排行数据
      </div>

      <div 
        v-else
        v-for="(item, index) in list" 
        :key="item.id"
        class="ranking-item"
        @click="goToDetail(item)"
      >
        <!-- 左侧封面 -->
        <div class="item-cover">
          <img :src="item.cover_url || item.cover" :alt="item.title" />
          <div class="cover-stats">
            <span class="views">👁 {{ formatCount(item.view_count) }}</span>
            <span class="duration" v-if="item.duration">{{ formatDuration(item.duration) }}</span>
          </div>
        </div>

        <!-- 右侧信息 -->
        <div class="item-info">
          <!-- 排名图标 -->
          <div class="rank-badge">
            <img :src="getRankIcon(index + 1)" class="rank-icon" />
            <span class="rank-num">NO.{{ index + 1 }}</span>
          </div>
          
          <p class="item-title">{{ item.title }}</p>
          
          <div class="item-meta">
            <span class="tag" v-if="item.category_name || item.tag">{{ item.category_name || item.tag }}</span>
            <span class="likes">☆ {{ formatCount(item.like_count || item.favorite_count || 0) }}</span>
          </div>
        </div>
      </div>

      <!-- 加载更多 -->
      <div v-if="loadingMore" class="loading-more">加载中...</div>
      <div v-if="!hasMore && list.length > 0" class="no-more">已加载全部</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'

const router = useRouter()
const listRef = ref(null)

const categories = [
  { key: 'video', label: '视频' },
  { key: 'douyin', label: '抖音' },
  { key: 'post', label: '帖子' },
  { key: 'novel', label: '小说' },
  { key: 'gallery', label: '图集' }
]

const timeFilters = [
  { key: 'week', label: '周榜' },
  { key: 'month', label: '月榜' },
  { key: 'season', label: '季榜' },
  { key: 'total', label: '总榜' }
]

const activeCategory = ref('video')
const activeTime = ref('week')
const list = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const hasMore = ref(true)
const page = ref(1)
const pageSize = 20

// 获取排名图标
const getRankIcon = (rank) => {
  if (rank === 1) return '/images/ranking/rank_1.webp'
  if (rank === 2) return '/images/ranking/rank_2.webp'
  if (rank === 3) return '/images/ranking/rank_3.webp'
  return '/images/ranking/rank_default.webp'
}

// 格式化数量
const formatCount = (count) => {
  if (!count) return '0'
  if (count >= 10000) return (count / 10000).toFixed(1) + 'W'
  if (count >= 1000) return (count / 1000).toFixed(1) + 'K'
  return count.toString()
}

// 格式化时长
const formatDuration = (seconds) => {
  if (!seconds) return ''
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

// 切换分类
const switchCategory = (key) => {
  activeCategory.value = key
  page.value = 1
  list.value = []
  hasMore.value = true
  fetchRanking()
}

// 切换时间
const switchTime = (key) => {
  activeTime.value = key
  page.value = 1
  list.value = []
  hasMore.value = true
  fetchRanking()
}

// 获取排行数据
const fetchRanking = async () => {
  if (page.value === 1) {
    loading.value = true
  } else {
    loadingMore.value = true
  }

  try {
    let endpoint = ''
    const params = { 
      page: page.value, 
      page_size: pageSize,
      time_range: activeTime.value
    }

    switch (activeCategory.value) {
      case 'video':
        endpoint = '/ranking/videos'
        break
      case 'douyin':
        endpoint = '/ranking/shorts'
        break
      case 'post':
        endpoint = '/ranking/posts'
        break
      case 'novel':
        endpoint = '/ranking/novels'
        break
      case 'gallery':
        endpoint = '/ranking/galleries'
        break
    }

    const res = await api.get(endpoint, { params })
    const items = res.data?.items || res.data || []

    if (page.value === 1) {
      list.value = items
    } else {
      list.value = [...list.value, ...items]
    }

    hasMore.value = items.length >= pageSize && list.value.length < 1000
  } catch (e) {
    console.error('获取排行失败:', e)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// 滚动加载
const handleScroll = () => {
  if (!listRef.value || loadingMore.value || !hasMore.value) return
  
  const { scrollTop, scrollHeight, clientHeight } = listRef.value
  if (scrollTop + clientHeight >= scrollHeight - 100) {
    page.value++
    fetchRanking()
  }
}

// 跳转详情
const goToDetail = (item) => {
  switch (activeCategory.value) {
    case 'video':
      router.push(`/user/video/${item.id}`)
      break
    case 'douyin':
      router.push(`/user/short-video/${item.id}`)
      break
    case 'post':
      router.push(`/user/community/post/${item.id}`)
      break
    case 'novel':
      if (item.novel_type === 'audio') {
        router.push(`/user/audio-novel/${item.id}`)
      } else {
        router.push(`/user/novel/${item.id}`)
      }
      break
    case 'gallery':
      router.push(`/user/gallery/${item.id}`)
      break
  }
}

onMounted(() => {
  fetchRanking()
})
</script>

<style lang="scss" scoped>
.ranking-page {
  min-height: 100vh;
  min-height: 100dvh;
  background: #0a0a12;
  color: #fff;
  display: flex;
  flex-direction: column;
}

.page-header {
  padding: 16px;
  
  .back-btn {
    font-size: 32px;
    color: #a855f7;
    cursor: pointer;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.ranking-banner {
  text-align: center;
  padding: 0 20px 20px;
  
  .banner-img {
    max-width: 200px;
    height: auto;
  }
  
  .banner-subtitle {
    color: rgba(255, 255, 255, 0.5);
    font-size: 13px;
    margin-top: 8px;
  }
}

.category-tabs {
  display: flex;
  justify-content: center;
  gap: 24px;
  padding: 0 16px 16px;
  
  .tab-item {
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
        left: 0;
        right: 0;
        height: 2px;
        background: #a855f7;
        border-radius: 1px;
      }
    }
  }
}

.time-tabs {
  display: flex;
  justify-content: flex-start;
  gap: 12px;
  padding: 0 16px 16px;
  
  .time-item {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.6);
    padding: 6px 16px;
    border-radius: 16px;
    cursor: pointer;
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.2);
    
    &.active {
      background: linear-gradient(135deg, #a855f7, #7c3aed);
      color: #fff;
      border-color: transparent;
    }
  }
}

.ranking-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px 20px;
  -webkit-overflow-scrolling: touch;
}

.ranking-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  margin-bottom: 12px;
  cursor: pointer;
  
  &:active {
    background: rgba(255, 255, 255, 0.08);
  }
}

.item-cover {
  position: relative;
  width: 140px;
  height: 80px;
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
  background: #1a1a28;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  .cover-stats {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 4px 8px;
    background: linear-gradient(transparent, rgba(0, 0, 0, 0.8));
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: #fff;
  }
}

.item-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.rank-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  
  .rank-icon {
    width: 24px;
    height: 24px;
  }
  
  .rank-num {
    font-size: 14px;
    font-weight: 600;
    color: #f0c14b;
  }
}

.item-title {
  font-size: 14px;
  color: #eee;
  margin: 6px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.4;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  
  .tag {
    font-size: 11px;
    color: #a855f7;
    padding: 2px 8px;
    background: rgba(168, 85, 247, 0.15);
    border-radius: 10px;
  }
  
  .likes {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.5);
  }
}

.loading-state {
  .skeleton-item {
    display: flex;
    gap: 12px;
    padding: 12px;
    margin-bottom: 12px;
    
    .skeleton-cover {
      width: 140px;
      height: 80px;
      background: #1a1a28;
      border-radius: 8px;
    }
    
    .skeleton-info {
      flex: 1;
      
      .skeleton-title {
        height: 16px;
        background: #1a1a28;
        border-radius: 4px;
        margin-bottom: 12px;
      }
      
      .skeleton-meta {
        height: 12px;
        width: 60%;
        background: #1a1a28;
        border-radius: 4px;
      }
    }
  }
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: rgba(255, 255, 255, 0.5);
}

.loading-more, .no-more {
  text-align: center;
  padding: 20px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 13px;
}
</style>
