<template>
  <div class="likes-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
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
      <div v-if="loading && likes.length === 0" class="loading-state">
        <p>加载中...</p>
      </div>
      
      <div v-else-if="likes.length > 0" class="likes-grid" :class="gridClass">
        <!-- 帖子列表 -->
        <template v-if="activeTab === 'post'">
          <div v-for="item in likes" :key="item.id" class="post-item" @click="goToDetail(item)">
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
            </div>
          </div>
        </template>
        
        <!-- 图集列表 -->
        <template v-else-if="activeTab === 'gallery'">
          <div v-for="item in likes" :key="item.id" class="gallery-item" @click="goToDetail(item)">
            <div v-if="isEditing" class="checkbox" @click.stop="toggleSelect(item)">
              <div :class="['check-box', { checked: selectedIds.includes(item.id) }]">
                <svg v-if="selectedIds.includes(item.id)" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                </svg>
              </div>
            </div>
            <div class="gallery-cover">
              <img :src="item.cover || item.thumbnail || '/images/backgrounds/no_data.webp'" alt="" />
              <span class="image-count">{{ item.image_count || 0 }}P</span>
            </div>
            <h3 class="gallery-title">{{ item.title }}</h3>
            <div class="gallery-stats">
              <span>❤️ {{ item.like_count || 0 }}</span>
              <span>👁 {{ item.view_count || 0 }}</span>
            </div>
          </div>
        </template>
        
        <!-- 小说列表 -->
        <template v-else-if="activeTab === 'novel'">
          <div v-for="item in likes" :key="item.id" class="novel-item" @click="goToDetail(item)">
            <div v-if="isEditing" class="checkbox" @click.stop="toggleSelect(item)">
              <div :class="['check-box', { checked: selectedIds.includes(item.id) }]">
                <svg v-if="selectedIds.includes(item.id)" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                </svg>
              </div>
            </div>
            <div class="novel-cover">
              <img :src="item.cover || item.thumbnail || '/images/backgrounds/no_data.webp'" alt="" />
            </div>
            <div class="novel-info">
              <h3 class="novel-title">{{ item.title }}</h3>
              <p class="novel-author">{{ item.author || '佚名' }}</p>
              <div class="novel-meta">
                <span>{{ item.chapter_count || 0 }}章</span>
                <span>{{ item.status }}</span>
              </div>
              <div class="novel-stats">
                <span>❤️ {{ item.like_count || 0 }}</span>
                <span>👁 {{ item.view_count || 0 }}</span>
              </div>
            </div>
          </div>
        </template>
        
        <!-- 视频列表 -->
        <template v-else>
          <div v-for="item in likes" :key="item.id" class="like-item" @click="goToDetail(item)">
            <div v-if="isEditing" class="checkbox" @click.stop="toggleSelect(item)">
              <div :class="['check-box', { checked: selectedIds.includes(item.id) }]">
                <svg v-if="selectedIds.includes(item.id)" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                </svg>
              </div>
            </div>
            <div class="thumbnail">
              <img :src="item.thumbnail || item.cover || '/images/backgrounds/no_data.webp'" alt="" />
              <span class="duration">{{ item.duration }}</span>
              <span v-if="item.is_short" class="short-tag">短视频</span>
            </div>
            <h3 class="title">{{ item.title }}</h3>
          </div>
        </template>
      </div>
      
      <div v-else class="empty-state">
        <img src="/images/backgrounds/no_data.webp" alt="" />
        <p>当前页面暂无内容～</p>
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div v-if="isEditing && likes.length > 0" class="bottom-bar">
      <div class="select-all" @click="toggleSelectAll">
        <div :class="['check-box', { checked: isAllSelected }]">
          <svg v-if="isAllSelected" viewBox="0 0 24 24" fill="currentColor">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
          </svg>
        </div>
        <span>全选</span>
      </div>
      <button class="delete-btn" @click="deleteSelected">取消喜欢</button>
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
const likes = ref([])
const loading = ref(false)
const page = ref(1)
const hasMore = ref(true)

const isAllSelected = computed(() => {
  return likes.value.length > 0 && selectedIds.value.length === likes.value.length
})

const gridClass = computed(() => {
  if (activeTab.value === 'post') return 'post-list'
  if (activeTab.value === 'novel') return 'novel-list'
  return ''
})

// 获取喜欢列表
const fetchLikes = async (reset = false) => {
  if (loading.value) return
  if (!reset && !hasMore.value) return
  
  loading.value = true
  
  try {
    if (reset) {
      page.value = 1
      likes.value = []
    }
    
    let res
    if (activeTab.value === 'post') {
      res = await api.get('/community/user/liked/posts', {
        params: { page: page.value, page_size: 20 }
      })
    } else if (activeTab.value === 'gallery') {
      res = await api.get('/gallery-novel/user/liked/galleries', {
        params: { page: page.value, page_size: 20 }
      })
    } else if (activeTab.value === 'novel') {
      res = await api.get('/gallery-novel/user/liked/novels', {
        params: { page: page.value, page_size: 20 }
      })
    } else {
      res = await api.get('/videos/user/liked', {
        params: {
          page: page.value,
          page_size: 20,
          video_type: activeTab.value
        }
      })
    }
    
    const data = res.data || res
    if (data.items && data.items.length > 0) {
      likes.value = reset ? data.items : [...likes.value, ...data.items]
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
    selectedIds.value = likes.value.map(item => item.id)
  }
}

const deleteSelected = async () => {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请选择要取消的项目')
    return
  }
  
  try {
    for (const id of selectedIds.value) {
      if (activeTab.value === 'post') {
        await api.post(`/community/posts/${id}/like`)
      } else if (activeTab.value === 'gallery') {
        await api.post(`/gallery-novel/gallery/${id}/like`)
      } else if (activeTab.value === 'novel') {
        await api.post(`/gallery-novel/novel/${id}/like`)
      } else {
        await api.post(`/videos/${id}/like`)
      }
    }
    
    likes.value = likes.value.filter(item => !selectedIds.value.includes(item.id))
    selectedIds.value = []
    ElMessage.success('已取消喜欢')
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error('操作失败')
  }
}

const goToDetail = (item) => {
  if (isEditing.value) {
    toggleSelect(item)
    return
  }
  
  if (activeTab.value === 'post') {
    router.push(`/user/community/post/${item.id}`)
  } else if (activeTab.value === 'gallery') {
    router.push(`/user/gallery/${item.id}`)
  } else if (activeTab.value === 'novel') {
    router.push(`/user/novel/${item.id}`)
  } else if (item.is_short) {
    router.push(`/shorts/${item.id}`)
  } else {
    router.push(`/user/video/${item.id}`)
  }
}

watch(activeTab, () => {
  selectedIds.value = []
  isEditing.value = false
  fetchLikes(true)
})

watch(() => userStore.token, (newToken) => {
  if (newToken) {
    fetchLikes(true)
  }
})

onMounted(() => {
  if (userStore.token) {
    fetchLikes(true)
  }
})
</script>

<style lang="scss" scoped>
.likes-page {
  min-height: 100vh;
  background: #0a0a0a;
  padding-bottom: env(safe-area-inset-bottom);
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  position: sticky;
  top: 0;
  z-index: 100;
  background: #0a0a0a;
  
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
  &::-webkit-scrollbar { display: none; }
}

.tabs {
  display: flex;
  padding: 0 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  
  .tab-item {
    padding: 12px 16px;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.6);
    cursor: pointer;
    position: relative;
    white-space: nowrap;
    
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
  p { color: rgba(255, 255, 255, 0.6); font-size: 14px; }
}

.likes-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

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
  
  svg { width: 14px; height: 14px; color: #fff; }
}

.like-item {
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
  }
  
  .thumbnail {
    position: relative;
    width: 100%;
    padding-top: 56.25%;
    
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
  }
}

// 图集样式
.gallery-item {
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
  }
  
  .gallery-cover {
    position: relative;
    width: 100%;
    padding-top: 133%;
    
    img {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      background: #1a1a1a;
    }
    
    .image-count {
      position: absolute;
      bottom: 4px;
      right: 4px;
      font-size: 11px;
      color: #fff;
      background: rgba(0, 0, 0, 0.7);
      padding: 2px 6px;
      border-radius: 3px;
    }
  }
  
  .gallery-title {
    font-size: 13px;
    color: #fff;
    margin: 0;
    padding: 8px 8px 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .gallery-stats {
    display: flex;
    gap: 12px;
    padding: 0 8px 8px;
    font-size: 11px;
    color: rgba(255, 255, 255, 0.5);
  }
}

// 小说样式
.novel-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.novel-item {
  position: relative;
  display: flex;
  gap: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 12px;
  cursor: pointer;
  
  .checkbox {
    position: absolute;
    top: 12px;
    right: 12px;
    z-index: 10;
  }
  
  .novel-cover {
    width: 80px;
    height: 110px;
    flex-shrink: 0;
    border-radius: 6px;
    overflow: hidden;
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      background: #1a1a1a;
    }
  }
  
  .novel-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    
    .novel-title {
      font-size: 15px;
      color: #fff;
      font-weight: 500;
      margin: 0 0 6px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .novel-author {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);
      margin: 0 0 8px;
    }
    
    .novel-meta {
      display: flex;
      gap: 12px;
      font-size: 12px;
      color: rgba(255, 255, 255, 0.6);
      margin-bottom: 8px;
    }
    
    .novel-stats {
      display: flex;
      gap: 16px;
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);
      margin-top: auto;
    }
  }
}

// 帖子样式
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
  
  .checkbox { position: absolute; top: 12px; right: 12px; z-index: 10; }
  
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
    }
  }
  
  .post-stats {
    display: flex;
    gap: 16px;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.5);
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80px 20px;
  
  img { width: 150px; margin-bottom: 16px; opacity: 0.8; }
  p { font-size: 13px; color: #4a9eff; }
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
    
    span { font-size: 14px; color: #fff; }
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
