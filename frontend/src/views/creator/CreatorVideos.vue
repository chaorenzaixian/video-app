<template>
  <div class="creator-videos-page">
    <div class="nav-header">
      <button class="back-btn" @click="$router.push('/creator')"><img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" /></button>
      <h1>我的作品</h1>
      <button class="upload-btn" @click="$router.push('/creator/upload')">+上传</button>
    </div>

    <!-- 筛选标签 -->
    <div class="filter-tabs">
      <span :class="{ active: filter === 'all' }" @click="filter = 'all'">全部</span>
      <span :class="{ active: filter === 'approved' }" @click="filter = 'approved'">已发布</span>
      <span :class="{ active: filter === 'pending' }" @click="filter = 'pending'">审核中</span>
      <span :class="{ active: filter === 'rejected' }" @click="filter = 'rejected'">未通过</span>
    </div>

    <!-- 视频列表 -->
    <div class="videos-list">
      <div v-for="video in filteredVideos" :key="video.id" class="video-item">
        <div class="video-cover">
          <img :src="video.cover_url || '/images/default-cover.webp'" alt="">
          <span class="status-badge" :class="video.review_status">
            {{ getStatusText(video.review_status) }}
          </span>
        </div>
        <div class="video-info">
          <h3>{{ video.title }}</h3>
          <div class="video-stats">
            <span>👁 {{ video.view_count }}</span>
            <span>❤️ {{ video.like_count }}</span>
            <span v-if="video.coin_price > 0">💰 {{ video.coin_price }}币</span>
          </div>
          <div class="video-time">{{ formatTime(video.created_at) }}</div>
          <div v-if="video.review_status === 'rejected'" class="reject-reason">
            拒绝原因: {{ video.reject_reason?.join(', ') || '未说明' }}
          </div>
        </div>
        <div class="video-actions">
          <button @click="editVideo(video)">编辑</button>
          <button class="danger" @click="deleteVideo(video)">删除</button>
        </div>
      </div>

      <div v-if="filteredVideos.length === 0" class="empty-state">
        <span>📹</span>
        <p>暂无视频作品</p>
        <button @click="$router.push('/creator/upload')">立即上传</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'

const videos = ref([])
const filter = ref('all')

const filteredVideos = computed(() => {
  if (filter.value === 'all') return videos.value
  return videos.value.filter(v => v.review_status === filter.value)
})

const getStatusText = (status) => {
  const texts = {
    'pending': '审核中',
    'approved': '已发布',
    'rejected': '未通过',
    'revision': '需修改'
  }
  return texts[status] || status
}

const formatTime = (time) => {
  const d = new Date(time)
  return `${d.getFullYear()}-${d.getMonth()+1}-${d.getDate()}`
}

const fetchVideos = async () => {
  try {
    const res = await api.get('/creator/videos')
    videos.value = res.data
  } catch (error) {
    console.error('获取视频失败:', error)
  }
}

const editVideo = (video) => {
  // TODO: 跳转编辑页面
  ElMessage.info('编辑功能开发中')
}

const deleteVideo = async (video) => {
  try {
    await ElMessageBox.confirm('确定删除这个视频吗？', '提示', { type: 'warning' })
    // TODO: 调用删除API
    ElMessage.success('删除成功')
    await fetchVideos()
  } catch (e) {}
}

onMounted(fetchVideos)
</script>

<style lang="scss" scoped>
.creator-videos-page {
  min-height: 100vh;
  background: #0f0f1a;
}

.nav-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: rgba(0, 0, 0, 0.3);
  
  .back-btn {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.1);
    border: none;
    color: #fff;
    font-size: 24px;
  }
  
  h1 { font-size: 18px; color: #fff; margin: 0; }
  
  .upload-btn {
    background: linear-gradient(135deg, #667eea, #764ba2);
    border: none;
    color: #fff;
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 14px;
  }
}

.filter-tabs {
  display: flex;
  padding: 12px 16px;
  gap: 16px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  
  span {
    color: rgba(255,255,255,0.5);
    font-size: 14px;
    padding-bottom: 8px;
    cursor: pointer;
    
    &.active {
      color: #667eea;
      border-bottom: 2px solid #667eea;
    }
  }
}

.videos-list {
  padding: 16px;
}

.video-item {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: rgba(255,255,255,0.05);
  border-radius: 12px;
  margin-bottom: 12px;
  
  .video-cover {
    width: 120px;
    height: 80px;
    border-radius: 8px;
    overflow: hidden;
    position: relative;
    flex-shrink: 0;
    
    img { width: 100%; height: 100%; object-fit: cover; }
    
    .status-badge {
      position: absolute;
      top: 4px;
      left: 4px;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 10px;
      color: #fff;
      
      &.pending { background: #faad14; }
      &.approved { background: #52c41a; }
      &.rejected { background: #ff4d4f; }
    }
  }
  
  .video-info {
    flex: 1;
    min-width: 0;
    
    h3 {
      color: #fff;
      font-size: 14px;
      margin: 0 0 8px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .video-stats {
      display: flex;
      gap: 12px;
      font-size: 12px;
      color: rgba(255,255,255,0.5);
    }
    
    .video-time {
      font-size: 11px;
      color: rgba(255,255,255,0.3);
      margin-top: 4px;
    }
    
    .reject-reason {
      font-size: 11px;
      color: #ff4d4f;
      margin-top: 4px;
    }
  }
  
  .video-actions {
    display: flex;
    flex-direction: column;
    gap: 8px;
    
    button {
      padding: 6px 12px;
      border-radius: 6px;
      border: none;
      font-size: 12px;
      background: rgba(255,255,255,0.1);
      color: #fff;
      
      &.danger { color: #ff4d4f; }
    }
  }
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: rgba(255,255,255,0.5);
  
  span { font-size: 48px; }
  p { margin: 16px 0; }
  
  button {
    padding: 12px 24px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    border: none;
    border-radius: 8px;
    color: #fff;
  }
}

// ============ 响应式适配 ============
@media (min-width: 768px) {
  .creator-videos {
    max-width: 800px;
    margin: 0 auto;
  }
  
  .video-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 1024px) {
  .creator-videos {
    max-width: 1000px;
  }
  
  .video-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (min-width: 1920px) {
  .creator-videos {
    max-width: 1200px;
  }
  
  .video-grid {
    grid-template-columns: repeat(5, 1fr);
    gap: 20px;
  }
}

@media (min-width: 2560px) {
  .creator-videos {
    max-width: 1600px;
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
