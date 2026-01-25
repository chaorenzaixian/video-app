<template>
  <div class="purchase-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()"><img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" /></div>
      <h1>我的购买</h1>
      <div class="placeholder"></div>
    </header>

    <!-- 分类标签 -->
    <div class="category-tabs">
      <div 
        v-for="tab in tabs" 
        :key="tab.key"
        :class="['tab-item', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </div>
    </div>

    <!-- 内容区域 -->
    <div class="content-area">
      <!-- 加载中 -->
      <div v-if="loading" class="video-list double-column">
        <div v-for="i in 6" :key="'skeleton-'+i" class="video-card skeleton">
          <div class="video-cover">
            <div class="skeleton-shimmer"></div>
          </div>
          <div class="video-info">
            <div class="skeleton-title"></div>
            <div class="skeleton-meta"></div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!items.length" class="empty-state">
        <img src="/images/backgrounds/no_data.webp" alt="暂无内容" class="empty-icon" />
        <p class="empty-text">当前页面暂无内容～</p>
      </div>

      <!-- 视频网格列表 -->
      <div v-else class="video-list double-column">
        <div 
          v-for="item in items" 
          :key="item.id"
          class="video-card"
          @click="goToDetail(item)"
        >
          <div class="video-cover">
            <img :src="getCoverUrl(item.cover_url)" :alt="item.title" loading="lazy" />
            <div class="cover-views">
              <span class="coin-icon">🪙</span>
              <span>{{ item.price }}</span>
            </div>
            <div v-if="item.duration" class="video-duration">{{ formatDuration(item.duration) }}</div>
          </div>
          <div class="video-info">
            <p class="video-title">{{ item.title }}</p>
            <div class="video-meta">
              <span class="video-tag">已购买</span>
              <span class="purchase-time">{{ formatTime(item.purchased_at) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 加载更多 -->
      <div v-if="items.length && hasMore" class="load-more" @click="loadMore">
        <span v-if="loadingMore">加载中...</span>
        <span v-else>加载更多</span>
      </div>
    </div>

    <!-- 底部导航 -->
    <BottomNav />
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import BottomNav from '@/components/common/BottomNav.vue'

const router = useRouter()

const tabs = [
  { key: 'video', label: '影视' },
  { key: 'douyin', label: '抖音' },
  { key: 'post', label: '帖子' },
  { key: 'comic', label: '漫画' },
  { key: 'anime', label: '动漫' },
  { key: 'album', label: '图集' },
  { key: 'novel', label: '小说' }
]

const activeTab = ref('video')
const items = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const page = ref(1)
const hasMore = ref(false)

const fetchPurchases = async (append = false) => {
  if (!append) {
    loading.value = true
    page.value = 1
  } else {
    loadingMore.value = true
  }

  try {
    const res = await api.get('/coins/purchases', {
      params: {
        type: activeTab.value,
        page: page.value,
        page_size: 20
      }
    })
    const data = res.data || res
    
    if (append) {
      items.value = [...items.value, ...(data.items || [])]
    } else {
      items.value = data.items || []
    }
    hasMore.value = (data.items?.length || 0) >= 20
  } catch (error) {
    console.error('获取购买记录失败:', error)
    items.value = []
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const loadMore = () => {
  if (loadingMore.value || !hasMore.value) return
  page.value++
  fetchPurchases(true)
}

const goToDetail = (item) => {
  if (activeTab.value === 'video') {
    router.push(`/user/video/${item.video_id || item.id}`)
  }
}

const getCoverUrl = (url) => {
  if (!url) return '/images/default-cover.webp'
  if (url.startsWith('http')) return url
  return url
}

const formatDuration = (seconds) => {
  if (!seconds) return ''
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  
  if (diff < 86400000) return '今天'
  if (diff < 172800000) return '昨天'
  return `${date.getMonth() + 1}/${date.getDate()}`
}

watch(activeTab, () => {
  fetchPurchases()
})

onMounted(() => {
  fetchPurchases()
})
</script>

<style lang="scss" scoped>
.purchase-page {
  min-height: 100vh;
  background: #000;
  color: #fff;
  padding-bottom: 70px;
  width: 100%;
  max-width: 100vw;
  margin: 0 auto;
  
  @media (min-width: 768px) {
    max-width: 750px;
  }
  
  @media (min-width: 1024px) {
    max-width: 900px;
  }
  
  @media (min-width: 1280px) {
    max-width: 1200px;
  }
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  padding-top: calc(12px + env(safe-area-inset-top, 0px));
  background: #000;
  position: sticky;
  top: 0;
  z-index: 100;
  
  .back-btn {
    font-size: 24px;
    cursor: pointer;
    width: 32px;
    color: #fff;
  }
  
  h1 {
    font-size: 15px;
    font-weight: 600;
    margin: 0;
  }
  
  .placeholder {
    width: 32px;
  }
}

.category-tabs {
  display: flex;
  padding: 0 12px;
  background: #000;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  overflow-x: auto;
  position: sticky;
  top: 48px;
  z-index: 99;
  -webkit-overflow-scrolling: touch;

  &::-webkit-scrollbar {
    display: none;
  }

  .tab-item {
    flex-shrink: 0;
    padding: 12px 16px;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.6);
    cursor: pointer;
    position: relative;
    white-space: nowrap;

    &.active {
      color: #fff;
      font-weight: 500;

      &::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 20px;
        height: 2px;
        background: #6366f1;
        border-radius: 1px;
      }
    }
  }
}

.content-area {
  padding: 12px;
  min-height: calc(100vh - 170px);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;

  .empty-icon {
    width: 150px;
    height: auto;
    margin-bottom: 16px;
  }

  .empty-text {
    font-size: 14px;
    color: #6366f1;
    margin: 0;
  }
}

// 视频网格
.video-list {
  display: grid;
  gap: 12px;
  
  &.double-column {
    grid-template-columns: repeat(2, 1fr);
  }
}

.video-card {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  
  &:active {
    transform: scale(0.98);
  }
  
  .video-cover {
    position: relative;
    width: 100%;
    aspect-ratio: 16/9;
    background: #1a1a1a;
    overflow: hidden;
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    
    .cover-views {
      position: absolute;
      bottom: 6px;
      left: 6px;
      display: flex;
      align-items: center;
      gap: 3px;
      padding: 2px 6px;
      background: rgba(0, 0, 0, 0.7);
      border-radius: 4px;
      font-size: 11px;
      color: #fbbf24;
      
      .coin-icon {
        font-size: 10px;
      }
    }
    
    .video-duration {
      position: absolute;
      bottom: 6px;
      right: 6px;
      padding: 2px 6px;
      background: rgba(0, 0, 0, 0.7);
      border-radius: 4px;
      font-size: 11px;
      color: #fff;
    }
  }
  
  .video-info {
    padding: 8px;
    
    .video-title {
      font-size: 13px;
      font-weight: 400;
      margin: 0 0 6px;
      overflow: hidden;
      text-overflow: ellipsis;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      line-height: 1.4;
      color: rgba(255, 255, 255, 0.9);
    }
    
    .video-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11px;
      color: rgba(255, 255, 255, 0.5);
      
      .video-tag {
        padding: 2px 6px;
        background: rgba(99, 102, 241, 0.2);
        border-radius: 3px;
        color: #818cf8;
        font-size: 10px;
      }
      
      .purchase-time {
        color: rgba(255, 255, 255, 0.4);
      }
    }
  }
  
  // 骨架屏
  &.skeleton {
    .video-cover {
      background: #1a1a1a;
      
      .skeleton-shimmer {
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, #1a1a1a 25%, #2a2a2a 50%, #1a1a1a 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
      }
    }
    
    .skeleton-title {
      height: 14px;
      background: #1a1a1a;
      border-radius: 4px;
      margin-bottom: 6px;
    }
    
    .skeleton-meta {
      height: 10px;
      width: 60%;
      background: #1a1a1a;
      border-radius: 4px;
    }
  }
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.load-more {
  display: flex;
  justify-content: center;
  padding: 20px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 13px;
  cursor: pointer;
}
</style>


