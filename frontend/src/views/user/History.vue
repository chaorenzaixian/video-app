<template>
  <div class="history-page">
    <!-- 顶部 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.push('/user/profile')">
        <span>←</span>
      </div>
      <h1>观看历史</h1>
      <div class="clear-btn" @click="clearAll">清空</div>
    </header>

    <!-- 视频列表 -->
    <div class="video-list double-column">
      <div 
        v-for="item in history" 
        :key="item.id"
        class="video-card"
        @click="goToVideo(item.video_id)"
      >
        <div class="video-cover">
          <img :src="getCoverUrl(item.cover_url)" :alt="item.title" loading="lazy" />
          <div class="cover-views">
            <span class="play-icon">▶</span>
            <span>{{ formatCount(item.view_count) }}</span>
          </div>
          <div class="video-duration">{{ formatDuration(item.duration) }}</div>
          <div class="progress-bar">
            <div class="progress" :style="{ width: (item.watch_progress || item.progress || 0) + '%' }"></div>
          </div>
        </div>
        <div class="video-info">
          <p class="video-title">{{ item.title }}</p>
          <div class="video-meta">
            <span class="video-tag">{{ formatProgress(item.watch_progress || item.progress || 0) }}</span>
            <span class="delete-icon" @click.stop="deleteItem(item.id)">✕</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div class="empty-state" v-if="!history.length">
      <img src="/images/backgrounds/no_data.webp" alt="暂无内容" class="empty-icon" />
      <p class="empty-text">暂无观看记录</p>
    </div>

    <!-- 底部导航 -->
    <BottomNav />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'
import BottomNav from '@/components/common/BottomNav.vue'

const router = useRouter()
const history = ref([])

const groupedHistory = computed(() => {
  const groups = {}
  history.value.forEach(item => {
    const date = formatDate(item.watched_at)
    if (!groups[date]) {
      groups[date] = { date, items: [] }
    }
    groups[date].items.push(item)
  })
  return Object.values(groups)
})

const fetchHistory = async () => {
  try {
    const res = await api.get('/users/me/history')
    history.value = res.data?.items || res || []
  } catch (error) {
    // 模拟数据
    history.value = [
      { id: 1, video_id: 1, title: '极品女神激情缠绵', cover_url: '/uploads/thumbnails/3.jpg', duration: 2032, view_count: 131700, uploader_name: '创作者A', progress: 75, watched_at: new Date() },
      { id: 2, video_id: 2, title: '清纯学妹宿舍私拍', cover_url: '/uploads/thumbnails/3.jpg', duration: 1800, view_count: 89000, uploader_name: '创作者B', progress: 30, watched_at: new Date(Date.now() - 86400000) },
      { id: 3, video_id: 3, title: '人妻诱惑完整版', cover_url: '/uploads/thumbnails/3.jpg', duration: 2400, view_count: 56000, uploader_name: '创作者C', progress: 100, watched_at: new Date(Date.now() - 86400000) }
    ]
  }
}

const goToVideo = (id) => {
  router.push(`/user/video/${id}`)
}

const deleteItem = async (id) => {
  history.value = history.value.filter(h => h.id !== id)
  ElMessage.success('已删除')
}

const clearAll = async () => {
  try {
    await ElMessageBox.confirm('确定清空所有观看记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    history.value = []
    ElMessage.success('已清空')
  } catch {}
}

// VIP等级图标映射
const VIP_LEVEL_ICONS = {
  1: '/images/backgrounds/vip_gold.webp',
  2: '/images/backgrounds/vip_1.webp',
  3: '/images/backgrounds/vip_2.webp',
  4: '/images/backgrounds/vip_3.webp',
  5: '/images/backgrounds/super_vip_red.webp',    // 黄金至尊
  6: '/images/backgrounds/super_vip_blue.webp'    // 紫色限定至尊
}

const getVipLevelIcon = (level) => {
  return VIP_LEVEL_ICONS[level] || ''
}

const getCoverUrl = (url) => {
  if (!url) return '/placeholder.jpg'
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

const formatDate = (date) => {
  const d = new Date(date)
  const today = new Date()
  const yesterday = new Date(today.getTime() - 86400000)
  
  if (d.toDateString() === today.toDateString()) return '今天'
  if (d.toDateString() === yesterday.toDateString()) return '昨天'
  return `${d.getMonth() + 1}月${d.getDate()}日`
}

const formatProgress = (progress) => {
  if (progress >= 100) return '已看完'
  return `${progress}%`
}

onMounted(() => {
  fetchHistory()
})
</script>

<style lang="scss" scoped>
// ============================================
// 响应式断点变量
// ============================================
$breakpoint-xs: 375px;
$breakpoint-sm: 414px;
$breakpoint-md: 600px;
$breakpoint-lg: 768px;
$breakpoint-xl: 1024px;
$breakpoint-xxl: 1280px;

.history-page {
  min-height: 100vh;
  min-height: 100dvh;
  background: #000;
  color: #fff;
  padding-bottom: 70px;
  padding-bottom: calc(70px + env(safe-area-inset-bottom, 0px));
  padding-left: env(safe-area-inset-left, 0px);
  padding-right: env(safe-area-inset-right, 0px);
  width: 100%;
  max-width: 100vw;
  margin: 0 auto;
  overflow-x: hidden;
  
  @media (min-width: $breakpoint-lg) {
    max-width: 750px;
  }
  
  @media (min-width: $breakpoint-xl) {
    max-width: 900px;
  }
  
  @media (min-width: $breakpoint-xxl) {
    max-width: 1200px;
  }
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: clamp(12px, 4vw, 20px) clamp(12px, 4vw, 24px);
  padding-top: calc(clamp(12px, 4vw, 20px) + env(safe-area-inset-top, 0px));
  background: #000;
  position: sticky;
  top: 0;
  z-index: 100;
  
  .back-btn {
    font-size: clamp(20px, 6vw, 28px);
    cursor: pointer;
    opacity: 0.8;
    width: clamp(32px, 10vw, 48px);
    transition: opacity 0.2s;
    
    &:hover {
      opacity: 1;
    }
  }
  
  h1 {
    font-size: clamp(16px, 4.5vw, 22px);
    margin: 0;
  }
  
  .clear-btn {
    font-size: clamp(12px, 3.5vw, 15px);
    color: rgba(255, 255, 255, 0.6);
    cursor: pointer;
    width: clamp(32px, 10vw, 48px);
    text-align: right;
    transition: color 0.2s;
    
    &:hover {
      color: rgba(255, 255, 255, 0.9);
    }
  }
}

// 视频网格
.video-list {
  display: grid;
  gap: 12px;
  padding: 12px;
  
  &.double-column {
    grid-template-columns: repeat(2, 1fr);
  }
}

.video-card {
  position: relative;
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
      color: #fff;
      
      .play-icon {
        font-size: 8px;
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
    
    .progress-bar {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: rgba(255, 255, 255, 0.2);
      
      .progress {
        height: 100%;
        background: #ec4899;
      }
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
        background: rgba(236, 72, 153, 0.2);
        border-radius: 3px;
        color: #ec4899;
        font-size: 10px;
      }
      
      .delete-icon {
        cursor: pointer;
        opacity: 0.5;
        transition: opacity 0.2s;
        
        &:hover {
          opacity: 1;
        }
      }
    }
  }
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

// 横屏模式优化
@media (orientation: landscape) and (max-height: 500px) {
  .page-header {
    padding: 8px 16px;
    
    .back-btn {
      font-size: 20px;
    }
    
    h1 {
      font-size: 16px;
    }
  }
  
  .history-item {
    padding: 10px 0;
    
    .video-cover {
      width: 140px;
    }
  }
}

// VIP标志动画
@keyframes vip-glow {
  0%, 100% {
    filter: drop-shadow(0 0 2px rgba(255, 215, 0, 0.5));
    transform: scale(1);
  }
  50% {
    filter: drop-shadow(0 0 6px rgba(255, 215, 0, 0.9));
    transform: scale(1.08);
  }
}

// ============ 超大屏幕优化 ============
@media (min-width: 1920px) {
  .history-page {
    max-width: 1400px;
    margin: 0 auto;
    font-size: 18px;
  }
  
  .video-grid {
    grid-template-columns: repeat(5, 1fr);
    gap: 20px;
  }
}

@media (min-width: 2560px) {
  .history-page {
    max-width: 1800px;
    font-size: 20px;
  }
  
  .video-grid {
    grid-template-columns: repeat(6, 1fr);
    gap: 24px;
  }
}

// 触摸设备优化
@media (hover: none) and (pointer: coarse) {
  .video-card:hover {
    transform: none !important;
  }
  
  .video-card:active {
    transform: scale(0.98);
    opacity: 0.9;
  }
}
</style>
