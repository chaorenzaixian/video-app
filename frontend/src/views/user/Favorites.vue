<template>
  <div class="favorites-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </div>
      <h1 class="page-title">我的收藏</h1>
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
      
      <div v-else-if="favorites.length > 0" class="favorites-grid" :class="{ 'post-list': activeTab === 'post' }">
        <!-- 帖子列表样式 -->
        <template v-if="activeTab === 'post'">
          <div v-for="item in favorites" :key="item.id" class="post-item" @click="goToVideo(item)">
            <div v-if="isEditing" class="checkbox" @click.stop="toggleSelect(item)">
              <div :class="['check-box', { checked: selectedIds.includes(item.id) }]">
                <svg v-if="selectedIds.includes(item.id)" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                </svg>
              </div>
            </div>
            <div class="post-header">
              <img :src="getAvatarUrl(item.user_avatar, item.user_id)" class="post-avatar" />
              <span class="post-nickname">{{ item.user_nickname }}</span>
            </div>
            <p class="post-content">{{ item.content }}</p>
            <div v-if="item.images && item.images.length > 0" class="post-images">
              <img v-for="(img, idx) in item.images.slice(0, 3)" :key="idx" :src="img" class="post-img" />
            </div>
            <div class="post-stats">
              <span>❤️ {{ item.like_count || 0 }}</span>
              <span>💬 {{ item.comment_count || 0 }}</span>
              <span v-if="item.topics && item.topics.length" class="post-topic-tag">#{{ item.topics[0].name }}</span>
            </div>
          </div>
        </template>
        
        <!-- 其他类型列表样式 -->
        <template v-else>
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
              <img :src="item.thumbnail || item.cover || '/images/backgrounds/no_data.webp'" alt="" />
              <span v-if="activeTab === 'video' || activeTab === 'short'" class="duration">{{ item.duration }}</span>
              <span v-if="activeTab === 'gallery'" class="duration">{{ item.image_count }}张</span>
              <span v-if="activeTab === 'novel'" class="duration">{{ item.chapter_count }}章</span>
              <span v-if="item.is_short" class="short-tag">短视频</span>
              <span v-if="activeTab === 'gallery' || activeTab === 'novel'" class="status-tag">{{ item.status }}</span>
            </div>
            <h3 class="title">{{ item.title }}</h3>
            <p v-if="activeTab === 'novel' && item.author" class="author">{{ item.author }}</p>
          </div>
        </template>
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
import { useUserStore } from '@/stores/user'
import { getAvatarUrl } from '@/utils/avatar'

const router = useRouter()
const userStore = useUserStore()

const tabs = [
  { key: 'video', label: '影视' },
  { key: 'short', label: '短视频' },
  { key: 'gallery', label: '图集' },
  { key: 'novel', label: '小说' },
  { key: 'post', label: '帖子' }
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

// 获取收藏列表
const fetchFavorites = async (reset = false) => {
  if (loading.value) return
  if (!reset && !hasMore.value) return
  
  loading.value = true
  
  try {
    if (reset) {
      page.value = 1
      favorites.value = []
    }
    
    let res
    if (activeTab.value === 'gallery') {
      // 获取收藏的图集
      res = await api.get('/gallery-novel/user/collected/galleries', {
        params: { page: page.value, page_size: 20 }
      })
    } else if (activeTab.value === 'novel') {
      // 获取收藏的小说
      res = await api.get('/gallery-novel/user/collected/novels', {
        params: { page: page.value, page_size: 20 }
      })
    } else if (activeTab.value === 'post') {
      // 获取收藏的帖子
      res = await api.get('/community/user/collected/posts', {
        params: { page: page.value, page_size: 20 }
      })
    } else {
      // 获取收藏的视频
      res = await api.get('/videos/user/collected', {
        params: {
          page: page.value,
          page_size: 20,
          video_type: activeTab.value
        }
      })
    }
    
    const data = res.data || res
    if (data.items && data.items.length > 0) {
      favorites.value = reset ? data.items : [...favorites.value, ...data.items]
      hasMore.value = data.has_more
      page.value++
    } else {
      hasMore.value = false
    }
  } catch (error) {
    console.error('获取收藏列表失败:', error)
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
    // 根据类型批量取消收藏
    for (const id of selectedIds.value) {
      if (activeTab.value === 'gallery') {
        await api.post(`/gallery-novel/gallery/${id}/collect`)
      } else if (activeTab.value === 'novel') {
        await api.post(`/gallery-novel/novel/${id}/collect`)
      } else if (activeTab.value === 'post') {
        await api.post(`/community/posts/${id}/collect`)
      } else {
        await api.post(`/videos/${id}/favorite`)
      }
    }
    
    favorites.value = favorites.value.filter(item => !selectedIds.value.includes(item.id))
    selectedIds.value = []
    ElMessage.success('删除成功')
  } catch (error) {
    console.error('删除失败:', error)
    ElMessage.error('删除失败')
  }
}

// 点击项目跳转
const goToVideo = (item) => {
  if (isEditing.value) {
    toggleSelect(item)
    return
  }
  
  if (activeTab.value === 'gallery') {
    router.push(`/gallery/${item.id}`)
  } else if (activeTab.value === 'novel') {
    router.push(`/novel/${item.id}`)
  } else if (activeTab.value === 'post') {
    router.push(`/user/community/post/${item.id}`)
  } else if (item.is_short) {
    router.push(`/shorts/${item.id}`)
  } else {
    router.push(`/user/video/${item.id}`)
  }
}

// 监听标签切换
watch(activeTab, () => {
  selectedIds.value = []
  isEditing.value = false
  fetchFavorites(true)
})

// 监听用户登录状态
watch(() => userStore.token, (newToken) => {
  if (newToken) {
    fetchFavorites(true)
  }
})

onMounted(() => {
  // 有token就请求
  if (userStore.token) {
    fetchFavorites(true)
  }
})
</script>

<style lang="scss" scoped>
$breakpoint-lg: 768px;
$breakpoint-xl: 1024px;
$breakpoint-xxl: 1280px;

.favorites-page {
  min-height: 100vh;
  background: #0a0a0a;
  padding-bottom: env(safe-area-inset-bottom);
  
  @media (min-width: $breakpoint-lg) {
    max-width: 750px;
    margin: 0 auto;
  }
  @media (min-width: $breakpoint-xl) {
    max-width: 900px;
  }
  @media (min-width: $breakpoint-xxl) {
    max-width: 1100px;
  }
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
  
  @media (min-width: $breakpoint-lg) {
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
  }
  @media (min-width: $breakpoint-xl) {
    grid-template-columns: repeat(4, 1fr);
  }
  @media (min-width: $breakpoint-xxl) {
    grid-template-columns: repeat(5, 1fr);
    gap: 20px;
  }
  
  .favorite-item {
    position: relative;
    cursor: pointer;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 8px;
    overflow: hidden;
    transition: transform 0.2s;
    
    @media (hover: hover) {
      &:hover {
        transform: translateY(-3px);
      }
    }
    
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
      
      .status-tag {
        position: absolute;
        top: 4px;
        left: 4px;
        font-size: 10px;
        color: #fff;
        background: rgba(0, 0, 0, 0.6);
        padding: 2px 6px;
        border-radius: 3px;
      }
    }
    
    .title {
      font-size: 13px;
      color: #fff;
      margin: 0;
      padding: 8px;
      padding-bottom: 4px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      line-height: 1.4;
    }
    
    .author {
      font-size: 11px;
      color: rgba(255, 255, 255, 0.5);
      margin: 0;
      padding: 0 8px 8px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
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
    max-width: 750px;
    left: 50%;
    transform: translateX(-50%);
  }
  @media (min-width: $breakpoint-xl) {
    max-width: 900px;
  }
  @media (min-width: $breakpoint-xxl) {
    max-width: 1100px;
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

// 帖子列表样式
.post-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.post-item {
  position: relative;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 12px;
  cursor: pointer;
  transition: transform 0.2s;
  
  @media (hover: hover) {
    &:hover {
      transform: translateY(-2px);
      background: rgba(255, 255, 255, 0.08);
    }
  }
  
  .checkbox {
    position: absolute;
    top: 12px;
    right: 12px;
    z-index: 10;
  }
  
  .post-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    
    .post-avatar {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      object-fit: cover;
    }
    
    .post-nickname {
      font-size: 14px;
      color: #fff;
      font-weight: 500;
    }
  }
  
  .post-content {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.9);
    line-height: 1.5;
    margin: 0 0 8px;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  
  .post-images {
    display: flex;
    gap: 4px;
    margin-bottom: 8px;
    
    .post-img {
      width: 80px;
      height: 80px;
      object-fit: cover;
      border-radius: 4px;
      
      @media (min-width: $breakpoint-lg) {
        width: 100px;
        height: 100px;
      }
    }
  }
  
  .post-stats {
    display: flex;
    gap: 16px;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.5);
    align-items: center;
    
    .post-topic-tag {
      margin-left: auto;
      padding: 3px 10px;
      background: transparent;
      border: 1px solid rgba(168, 85, 247, 0.5);
      border-radius: 10px;
      color: #a855f7;
      font-size: 11px;
    }
  }
}
</style>