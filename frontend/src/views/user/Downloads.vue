<template>
  <div class="downloads-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </div>
      <h1 class="page-title">下载缓存</h1>
      <div class="header-right" @click="toggleEdit">{{ isEditing ? '完成' : '编辑' }}</div>
    </header>

    <!-- 分类标签 -->
    <div class="tabs">
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
    <div class="content">
      <div v-if="filteredDownloads.length > 0" class="download-list">
        <div v-for="item in filteredDownloads" :key="item.id" class="download-item">
          <!-- 选择框（编辑模式） -->
          <div v-if="isEditing" class="checkbox" @click="toggleSelect(item)">
            <div :class="['check-box', { checked: selectedIds.includes(item.id) }]">
              <svg v-if="selectedIds.includes(item.id)" viewBox="0 0 24 24" fill="currentColor">
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
              </svg>
            </div>
          </div>
          
          <!-- 视频缩略图 -->
          <div class="thumbnail" @click="playVideo(item)">
            <img :src="item.thumbnail || '/images/backgrounds/no_data.webp'" alt="" />
            <div class="play-overlay" v-if="item.status !== 'completed'">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M8 5v14l11-7z"/>
              </svg>
              <span>{{ item.status === 'downloading' ? '下载中' : '已暂停' }}</span>
            </div>
            <span class="duration" v-if="item.duration">{{ formatDuration(item.duration) }}</span>
            <span class="views" v-if="item.views">{{ formatViews(item.views) }}</span>
          </div>
          
          <!-- 视频信息 -->
          <div class="info">
            <h3 class="title">{{ item.title }}</h3>
            <div class="meta">
              <span class="type-tag">{{ item.type === 'short' ? '短视频' : '影视' }}</span>
              <span class="size" v-if="item.fileSize">{{ item.fileSize }}MB</span>
            </div>
            <div class="progress-section">
              <span :class="['status', item.status]">{{ getStatusText(item.status) }}</span>
              <span class="time">{{ formatTime(item.downloadTime) }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-else class="empty-state">
        <img src="/images/backgrounds/no_data.webp" alt="" />
        <p>当前页面暂无内容～</p>
      </div>
    </div>

    <!-- 底部操作栏（编辑模式） -->
    <div v-if="isEditing && filteredDownloads.length > 0" class="bottom-bar">
      <div class="select-all" @click="toggleSelectAll">
        <div :class="['check-box', { checked: isAllSelected }]">
          <svg v-if="isAllSelected" viewBox="0 0 24 24" fill="currentColor">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
          </svg>
        </div>
        <span>全选</span>
      </div>
      <button class="delete-btn" @click="deleteSelected">删除</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()

const tabs = [
  { key: 'all', label: '全部' },
  { key: 'video', label: '影视' },
  { key: 'short', label: '短视频' }
]

const activeTab = ref('all')
const isEditing = ref(false)
const selectedIds = ref([])
const downloads = ref([])

// 根据标签过滤下载列表
const filteredDownloads = computed(() => {
  if (activeTab.value === 'all') {
    return downloads.value
  }
  return downloads.value.filter(item => item.type === activeTab.value)
})

const isAllSelected = computed(() => {
  return filteredDownloads.value.length > 0 && selectedIds.value.length === filteredDownloads.value.length
})

// 从localStorage加载下载记录
const loadDownloads = () => {
  try {
    const saved = localStorage.getItem('video_downloads')
    if (saved) {
      downloads.value = JSON.parse(saved)
    }
  } catch (e) {
    console.error('加载下载记录失败:', e)
    downloads.value = []
  }
}

// 保存下载记录到localStorage
const saveDownloads = () => {
  try {
    localStorage.setItem('video_downloads', JSON.stringify(downloads.value))
  } catch (e) {
    console.error('保存下载记录失败:', e)
  }
}

const toggleEdit = () => {
  isEditing.value = !isEditing.value
  if (!isEditing.value) {
    selectedIds.value = []
  }
}

const toggleSelect = (item) => {
  const index = selectedIds.value.indexOf(item.id)
  if (index > -1) {
    selectedIds.value.splice(index, 1)
  } else {
    selectedIds.value.push(item.id)
  }
}

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = filteredDownloads.value.map(item => item.id)
  }
}

const deleteSelected = () => {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请选择要删除的项目')
    return
  }
  downloads.value = downloads.value.filter(item => !selectedIds.value.includes(item.id))
  saveDownloads()
  selectedIds.value = []
  ElMessage.success('删除成功')
}

const playVideo = (item) => {
  if (!isEditing.value) {
    if (item.type === 'short') {
      // 跳转到短视频播放页
      router.push(`/shorts/${item.videoId}`)
    } else {
      router.push(`/user/video/${item.videoId}`)
    }
  }
}

const formatViews = (views) => {
  if (!views) return ''
  if (views >= 10000) {
    return (views / 10000).toFixed(1) + 'w'
  }
  return views
}

const formatDuration = (seconds) => {
  if (!seconds) return ''
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  if (diff < 604800000) return Math.floor(diff / 86400000) + '天前'
  
  return `${date.getMonth() + 1}/${date.getDate()}`
}

const getStatusText = (status) => {
  const statusMap = {
    downloading: '下载中',
    paused: '已暂停',
    completed: '已完成',
    failed: '下载失败'
  }
  return statusMap[status] || status
}

onMounted(() => {
  loadDownloads()
})
</script>

<style lang="scss" scoped>
$breakpoint-lg: 768px;
$breakpoint-xl: 1024px;

.downloads-page {
  min-height: 100vh;
  background: #0a0a0a;
  padding-bottom: env(safe-area-inset-bottom);
  
  @media (min-width: $breakpoint-lg) {
    max-width: 700px;
    margin: 0 auto;
  }
  @media (min-width: $breakpoint-xl) {
    max-width: 800px;
  }
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  padding-top: calc(12px + env(safe-area-inset-top, 0px));
  background: transparent;
  position: sticky;
  top: 0;
  z-index: 100;
  
  .back-btn {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    
    svg {
      width: 24px;
      height: 24px;
      color: #fff;
    }
  }
  
  .page-title {
    font-size: 16px;
    font-weight: 600;
    color: #fff;
    margin: 0;
  }
  
  .header-right {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.7);
    cursor: pointer;
    padding: 4px 8px;
  }
}

.tabs {
  display: flex;
  padding: 0 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  
  .tab-item {
    padding: 12px 24px;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.6);
    cursor: pointer;
    position: relative;
    
    &.active {
      color: #fff;
      
      &::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 20px;
        height: 3px;
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 2px;
      }
    }
  }
}

.content {
  padding: 16px;
}

.download-list {
  .download-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    margin-bottom: 10px;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 10px;
    
    .checkbox {
      display: flex;
      align-items: center;
      flex-shrink: 0;
      
      .check-box {
        width: 20px;
        height: 20px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        
        &.checked {
          background: linear-gradient(135deg, #667eea, #764ba2);
          border-color: transparent;
        }
        
        svg {
          width: 14px;
          height: 14px;
          color: #fff;
        }
      }
    }
    
    .thumbnail {
      position: relative;
      width: 120px;
      height: 68px;
      border-radius: 6px;
      overflow: hidden;
      flex-shrink: 0;
      cursor: pointer;
      
      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        background: #1a1a1a;
      }
      
      .play-overlay {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        display: flex;
        align-items: center;
        gap: 4px;
        background: rgba(0, 0, 0, 0.7);
        padding: 4px 10px;
        border-radius: 16px;
        
        svg {
          width: 14px;
          height: 14px;
          color: #fff;
        }
        
        span {
          font-size: 11px;
          color: #fff;
        }
      }
      
      .duration {
        position: absolute;
        bottom: 4px;
        right: 4px;
        font-size: 10px;
        color: #fff;
        background: rgba(0, 0, 0, 0.7);
        padding: 2px 4px;
        border-radius: 3px;
      }
      
      .views {
        position: absolute;
        bottom: 4px;
        left: 4px;
        font-size: 10px;
        color: #fff;
        display: flex;
        align-items: center;
        gap: 2px;
        
        &::before {
          content: '▶';
          font-size: 7px;
        }
      }
    }
    
    .info {
      flex: 1;
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 6px;
      
      .title {
        font-size: 13px;
        color: #fff;
        margin: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        line-height: 1.4;
      }
      
      .meta {
        display: flex;
        align-items: center;
        gap: 8px;
        
        .type-tag {
          font-size: 10px;
          color: #fff;
          background: linear-gradient(135deg, #667eea, #764ba2);
          padding: 2px 6px;
          border-radius: 3px;
        }
        
        .size {
          font-size: 11px;
          color: rgba(255, 255, 255, 0.5);
        }
      }
      
      .progress-section {
        display: flex;
        align-items: center;
        justify-content: space-between;
        
        .status {
          font-size: 11px;
          
          &.downloading { color: #4CAF50; }
          &.paused { color: #ff9800; }
          &.completed { color: #2196F3; }
          &.failed { color: #f44336; }
        }
        
        .time {
          font-size: 11px;
          color: rgba(255, 255, 255, 0.4);
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
  
  img {
    width: 150px;
    height: auto;
    margin-bottom: 16px;
    opacity: 0.8;
  }
  
  p {
    font-size: 13px;
    color: #4a9eff;
  }
}

.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  padding-bottom: calc(12px + env(safe-area-inset-bottom));
  background: #1a1a1a;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  
  @media (min-width: $breakpoint-lg) {
    max-width: 700px;
    left: 50%;
    transform: translateX(-50%);
  }
  @media (min-width: $breakpoint-xl) {
    max-width: 800px;
  }
  
  .select-all {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    
    .check-box {
      width: 20px;
      height: 20px;
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      
      &.checked {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-color: transparent;
      }
      
      svg {
        width: 14px;
        height: 14px;
        color: #fff;
      }
    }
    
    span {
      font-size: 14px;
      color: #fff;
    }
  }
  
  .delete-btn {
    padding: 8px 24px;
    background: #f44336;
    color: #fff;
    border: none;
    border-radius: 20px;
    font-size: 14px;
    cursor: pointer;
  }
}
</style>


