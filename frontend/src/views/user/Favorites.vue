<template>
  <div class="favorites-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
        </svg>
      </div>
      <h1 class="page-title">我的喜欢</h1>
      <div class="header-right" @click="toggleEdit">{{ isEditing ? '完成' : '编辑' }}</div>
    </header>

    <!-- 分类标签 -->
    <div class="tabs-wrapper">
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
    </div>

    <!-- 内容区域 -->
    <div class="content">
      <!-- 加载中 -->
      <div v-if="loading && favorites.length === 0" class="loading-state">
        <p>加载中...</p>
      </div>
      
      <div v-else-if="favorites.length > 0" class="favorites-grid">
        <div v-for="item in favorites" :key="item.id" class="favorite-item" @click="goToVideo(item)">
          <!-- 选择框 -->
          <div v-if="isEditing" class="checkbox" @click.stop="toggleSelect(item)">
            <div :class="['check-box', { checked: selectedIds.includes(item.id) }]">
              <svg v-if="selectedIds.includes(item.id)" viewBox="0 0 24 24" fill="currentColor">
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
              </svg>
            </div>
          </div>
          
          <div class="thumbnail">
            <img :src="item.thumbnail || '/images/backgrounds/no_data.webp'" alt="" />
            <span class="duration">{{ item.duration }}</span>
            <span v-if="item.is_short" class="short-tag">短视频</span>
          </div>
          <h3 class="title">{{ item.title }}</h3>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-else class="empty-state">
        <img src="/images/backgrounds/no_data.webp" alt="" />
        <p>当前页面暂无内容～</p>
      </div>
    </div>

    <!-- 底部操作栏（编辑模式） -->
    <div v-if="isEditing && favorites.length > 0" class="bottom-bar">
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
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const router = useRouter()

const tabs = [
  { key: 'video', label: '影视' },
  { key: 'short', label: '短视频' }
]

const activeTab = ref('video')
const isEditing = ref(false)
const selectedIds = ref([])
const favorites = ref([])
const loading = ref(false)
const page = ref(1)
const hasMore = ref(true)

const isAllSelected = computed(() => {
  return favorites.value.length > 0 && selectedIds.value.length === favorites.value.length
})

// 获取点赞的视频列表
const fetchFavorites = async (reset = false) => {
  if (loading.value) return
  if (!reset && !hasMore.value) return
  
  loading.value = true
  
  try {
    if (reset) {
      page.value = 1
      favorites.value = []
    }
    
    const res = await api.get('/videos/user/liked', {
      params: {
        page: page.value,
        page_size: 20,
        video_type: activeTab.value
      }
    })
    
    const data = res.data || res
    if (data.items && data.items.length > 0) {
      favorites.value = reset ? data.items : [...favorites.value, ...data.items]
      hasMore.value = data.has_more
      page.value++
    } else {
      hasMore.value = false
    }
  } catch (error) {
    console.error('获取喜欢列表失败:', error)
  } finally {
    loading.value = false
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
    selectedIds.value = favorites.value.map(item => item.id)
  }
}

const deleteSelected = async () => {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请选择要删除的项目')
    return
  }
  
  try {
    // 批量取消点赞
    for (const id of selectedIds.value) {
      await api.post(`/videos/${id}/like`)
    }
    
    favorites.value = favorites.value.filter(item => !selectedIds.value.includes(item.id))
    selectedIds.value = []
    ElMessage.success('删除成功')
  } catch (error) {
    console.error('删除失败:', error)
    ElMessage.error('删除失败')
  }
}

// 点击视频跳转
const goToVideo = (item) => {
  if (isEditing.value) {
    toggleSelect(item)
    return
  }
  
  if (item.is_short) {
    router.push(`/shorts/${item.id}`)
  } else {
    router.push(`/user/video/${item.id}`)
  }
}

// 监听标签切换
watch(activeTab, () => {
  fetchFavorites(true)
})

onMounted(() => {
  fetchFavorites(true)
})
</script>

<style lang="scss" scoped>
.favorites-page {
  min-height: 100vh;
  background: #0a0a0a;
  padding-bottom: env(safe-area-inset-bottom);
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
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

.tabs-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  
  &::-webkit-scrollbar {
    display: none;
  }
}

.tabs {
  display: flex;
  padding: 0 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  white-space: nowrap;
  
  .tab-item {
    padding: 12px 16px;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.6);
    cursor: pointer;
    position: relative;
    flex-shrink: 0;
    
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

.loading-state {
  display: flex;
  justify-content: center;
  padding: 40px;
  
  p {
    color: rgba(255, 255, 255, 0.6);
    font-size: 14px;
  }
}

.favorites-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  
  .favorite-item {
    position: relative;
    cursor: pointer;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 8px;
    overflow: hidden;
    
    .checkbox {
      position: absolute;
      top: 8px;
      left: 8px;
      z-index: 10;
      
      .check-box {
        width: 20px;
        height: 20px;
        border: 2px solid rgba(255, 255, 255, 0.8);
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(0, 0, 0, 0.4);
        
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
      width: 100%;
      padding-top: 56.25%; // 16:9 比例
      overflow: hidden;
      
      img {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        background: #1a1a1a;
      }
      
      .duration {
        position: absolute;
        bottom: 4px;
        right: 4px;
        font-size: 11px;
        color: #fff;
        background: rgba(0, 0, 0, 0.7);
        padding: 2px 6px;
        border-radius: 3px;
      }
      
      .short-tag {
        position: absolute;
        top: 4px;
        right: 4px;
        font-size: 10px;
        color: #fff;
        background: linear-gradient(135deg, #667eea, #764ba2);
        padding: 2px 6px;
        border-radius: 3px;
      }
    }
    
    .title {
      font-size: 13px;
      color: #fff;
      margin: 0;
      padding: 8px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      line-height: 1.4;
      height: 36px;
      display: flex;
      align-items: center;
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