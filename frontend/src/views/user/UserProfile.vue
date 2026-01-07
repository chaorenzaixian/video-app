<template>
  <div class="user-profile-page">
    <!-- 头部背景 -->
    <div class="profile-header">
      <!-- 返回按钮 -->
      <div class="back-btn" @click="$router.back()">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
        </svg>
      </div>
      
      <!-- 用户信息区域 -->
      <div class="user-section">
        <!-- 左侧：头像 -->
        <div class="avatar-wrapper">
          <img :src="getAvatarUrl(userInfo.avatar)" class="avatar" />
        </div>
        
        <!-- 右侧：操作按钮（不显示在自己的主页） -->
        <div class="user-actions" v-if="!isOwnProfile">
          <div class="msg-btn" @click="handleMessage">
            <img src="/images/backgrounds/msg_button.webp" alt="私信" />
          </div>
          <button class="follow-btn" :class="{ followed: isFollowed }" @click="toggleFollow">
            <span v-if="!isFollowed">+ 关注</span>
            <span v-else>已关注</span>
          </button>
        </div>
      </div>
      
      <!-- 用户名 -->
      <div class="user-name-row">
        <span class="user-name gradient-gold">{{ userInfo.nickname || userInfo.username }}</span>
        <img 
          v-if="userInfo.vip_level && userInfo.vip_level > 0" 
          :src="getVipIcon(userInfo.vip_level)" 
          class="vip-badge"
          :alt="`VIP${userInfo.vip_level}`"
        />
      </div>
      
      <!-- 统计信息 -->
      <div class="user-stats">
        <span class="stat-item">{{ userInfo.video_count || 0 }} 作品</span>
        <span class="stat-divider"></span>
        <span class="stat-item">{{ userInfo.fans_count || 0 }}粉丝</span>
      </div>
      
      <!-- Tab切换 - 放在header内部实现透明效果 -->
      <div class="content-tabs">
        <div 
          v-for="tab in tabs" 
          :key="tab.key"
          :class="['tab-item', { active: activeTab === tab.key }]"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
          <div class="tab-indicator" v-if="activeTab === tab.key"></div>
        </div>
      </div>
    </div>
    
    <!-- 内容区域 -->
    <div class="content-area">
      <!-- 视频列表 - 首页横屏样式 -->
      <div v-if="activeTab === 'video'" class="video-list">
        <div v-if="videos.length > 0" class="video-grid-horizontal">
          <div 
            v-for="video in videos" 
            :key="video.id" 
            class="video-card"
            @click="goToVideo(video)"
          >
            <div class="video-cover-wrapper">
              <img :src="video.cover_url" class="video-cover" />
              <div class="video-duration">{{ formatDuration(video.duration) }}</div>
              <div class="play-overlay">
                <svg viewBox="0 0 24 24" fill="white">
                  <path d="M8 5v14l11-7z"/>
                </svg>
              </div>
            </div>
            <div class="video-info">
              <h3 class="video-title">{{ video.title }}</h3>
              <div class="video-meta">
                <span>{{ formatCount(video.view_count) }}播放</span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <img src="/images/backgrounds/no_data.webp" class="empty-icon" />
          <p class="empty-text">当前页面暂无内容 ~</p>
          <p class="retry-text" @click="fetchUserVideos">点击重试</p>
        </div>
      </div>
      
      <!-- 抖音（短视频） - 竖屏列表样式 -->
      <div v-else-if="activeTab === 'short'" class="short-list">
        <div v-if="shorts.length > 0" class="short-grid-vertical">
          <div 
            v-for="video in shorts" 
            :key="video.id" 
            class="short-item"
            @click="goToShort(video)"
          >
            <img :src="video.cover_url" class="short-cover" />
            <div class="short-info">
              <span class="play-count">▶ {{ formatCount(video.view_count) }}</span>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <img src="/images/backgrounds/no_data.webp" class="empty-icon" />
          <p class="empty-text">当前页面暂无内容 ~</p>
          <p class="retry-text" @click="fetchUserShorts">点击重试</p>
        </div>
      </div>
      
      <!-- 帖子 -->
      <div v-else-if="activeTab === 'post'" class="post-list">
        <div v-if="posts.length > 0" class="posts-grid">
          <div 
            v-for="post in posts" 
            :key="post.id" 
            class="post-item"
            @click="goToPost(post.id)"
          >
            <p class="post-content">{{ post.content }}</p>
            <div v-if="post.images && post.images.length" class="post-images">
              <img :src="post.images[0]" class="post-thumb" />
              <span v-if="post.images.length > 1" class="image-count">+{{ post.images.length - 1 }}</span>
            </div>
            <div class="post-stats">
              <span>👁 {{ formatCount(post.view_count) }}</span>
              <span>💬 {{ post.comment_count || 0 }}</span>
              <span>❤️ {{ formatCount(post.like_count) }}</span>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <img src="/images/backgrounds/no_data.webp" class="empty-icon" />
          <p class="empty-text">当前页面暂无内容 ~</p>
          <p class="retry-text" @click="fetchUserPosts">点击重试</p>
        </div>
      </div>
      
      <!-- 图集 -->
      <div v-else-if="activeTab === 'album'" class="album-list">
        <div class="empty-state">
          <img src="/images/backgrounds/no_data.webp" class="empty-icon" />
          <p class="empty-text">当前页面暂无内容 ~</p>
          <p class="retry-text">点击重试</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 判断是否是自己的主页
const isOwnProfile = computed(() => {
  const profileUserId = parseInt(route.params.id)
  const currentUserId = userStore.user?.id
  return currentUserId && profileUserId === currentUserId
})

// VIP等级图标映射
const VIP_LEVEL_ICONS = {
  1: '/images/backgrounds/vip_gold.webp',
  2: '/images/backgrounds/vip_1.webp',
  3: '/images/backgrounds/vip_2.webp',
  4: '/images/backgrounds/vip_3.webp',
  5: '/images/backgrounds/super_vip_red.webp',
  6: '/images/backgrounds/super_vip_blue.webp'
}

// 获取VIP图标
const getVipIcon = (level) => {
  return VIP_LEVEL_ICONS[level] || VIP_LEVEL_ICONS[1]
}

// 用户信息
const userInfo = ref({})
const isFollowed = ref(false)
const loading = ref(false)

// Tab配置
const tabs = [
  { key: 'video', label: '视频' },
  { key: 'short', label: '抖音' },
  { key: 'post', label: '帖子' },
  { key: 'album', label: '图集' }
]
const activeTab = ref('video')

// 视频数据
const videos = ref([])
const shorts = ref([])
const posts = ref([])

// 获取默认头像路径（共52个）
const getDefaultAvatarPath = (userId) => {
  const totalAvatars = 52
  const index = (userId % totalAvatars)
  
  if (index < 17) {
    return `/images/avatars/icon_avatar_${index + 1}.webp`
  } else if (index < 32) {
    const num = String(index - 17 + 1).padStart(3, '0')
    return `/images/avatars/DM_20251217202131_${num}.JPEG`
  } else {
    const num = String(index - 32 + 1).padStart(3, '0')
    return `/images/avatars/DM_20251217202341_${num}.JPEG`
  }
}

// 获取头像URL - 有自定义头像用自定义，没有用默认头像
const getAvatarUrl = (avatar) => {
  if (avatar) {
    // 如果头像路径是相对路径，添加前缀
    if (avatar.startsWith('/')) return avatar
    if (avatar.startsWith('http')) return avatar
    return '/' + avatar
  }
  // 使用默认头像
  const userId = parseInt(route.params.id) || 1
  return getDefaultAvatarPath(userId)
}

// 格式化数量
const formatCount = (count) => {
  if (!count) return '0'
  if (count >= 10000) return (count / 10000).toFixed(1) + 'w'
  if (count >= 1000) return (count / 1000).toFixed(1) + 'k'
  return count.toString()
}

// 格式化时长
const formatDuration = (seconds) => {
  if (!seconds) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 获取用户信息
const fetchUserInfo = async () => {
  const userId = route.params.id
  if (!userId) return
  
  try {
    const res = await api.get(`/users/${userId}/profile`)
    userInfo.value = res.data || res
    isFollowed.value = userInfo.value.is_followed || false
  } catch (error) {
    console.error('获取用户信息失败:', error)
    // 使用默认数据
    userInfo.value = {
      id: userId,
      nickname: `用户${userId}`,
      video_count: 0,
      fans_count: 0
    }
  }
}

// 获取用户视频
const fetchUserVideos = async () => {
  const userId = route.params.id
  if (!userId) return
  
  try {
    const res = await api.get('/videos', {
      params: { uploader_id: userId, limit: 20 }
    })
    videos.value = res.data?.items || res.data || []
  } catch (error) {
    console.error('获取视频失败:', error)
  }
}

// 获取用户短视频
const fetchUserShorts = async () => {
  const userId = route.params.id
  if (!userId) return
  
  try {
    const res = await api.get('/shorts', {
      params: { uploader_id: userId, limit: 20 }
    })
    shorts.value = res.data?.items || res.data || []
  } catch (error) {
    console.error('获取短视频失败:', error)
  }
}

// 获取用户帖子
const fetchUserPosts = async () => {
  const userId = route.params.id
  if (!userId) return
  
  try {
    const res = await api.get('/community/posts', {
      params: { user_id: userId, page_size: 20 }
    })
    posts.value = res.data || []
  } catch (error) {
    console.error('获取帖子失败:', error)
  }
}

// 关注/取消关注
const toggleFollow = async () => {
  const userId = route.params.id
  if (!userId) return
  
  try {
    if (isFollowed.value) {
      await api.delete(`/users/${userId}/follow`)
      isFollowed.value = false
      ElMessage.success('已取消关注')
    } else {
      await api.post(`/users/${userId}/follow`)
      isFollowed.value = true
      ElMessage.success('关注成功')
    }
  } catch (error) {
    if (error.response?.status === 401) {
      ElMessage.warning('请先登录')
    } else {
      ElMessage.error('操作失败')
    }
  }
}

// 私信
const handleMessage = () => {
  const userId = route.params.id
  router.push({
    path: `/user/chat/${userId}`,
    query: {
      nickname: userInfo.value.nickname || userInfo.value.username,
      avatar: userInfo.value.avatar
    }
  })
}

// 跳转视频
const goToVideo = (video) => {
  router.push(`/user/video/${video.id}`)
}

// 跳转短视频
const goToShort = (video) => {
  router.push(`/shorts?id=${video.id}`)
}

// 跳转帖子
const goToPost = (postId) => {
  router.push(`/user/community/post/${postId}`)
}

onMounted(() => {
  fetchUserInfo()
  fetchUserVideos()
  fetchUserShorts()
  fetchUserPosts()
})
</script>

<style lang="scss" scoped>
.user-profile-page {
  min-height: 100vh;
  background: #0a0a0a;
  color: #fff;
}

.profile-header {
  position: relative;
  background: url('/images/backgrounds/account_certificate_bg.webp') center top / cover no-repeat;
  padding: 50px 16px 16px;
  
  .back-btn {
    position: absolute;
    top: 12px;
    left: 12px;
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10;
    cursor: pointer;
    
    svg {
      width: 24px;
      height: 24px;
      color: #fff;
      filter: drop-shadow(0 1px 2px rgba(0,0,0,0.5));
    }
  }
  
  .user-section {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-top: 40px;
    margin-bottom: 10px;
    
    .avatar-wrapper {
      .avatar {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        border: 3px solid #fff;
        object-fit: cover;
        background: #1a1a2e;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
      }
    }
    
    .user-actions {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 5px;
      
      .msg-btn {
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        
        img {
          width: 100%;
          height: 100%;
          object-fit: contain;
        }
      }
      
      .follow-btn {
        padding: 8px 20px;
        background: linear-gradient(90deg, #8b5cf6, #a855f7);
        border: none;
        border-radius: 18px;
        color: #fff;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        
        &:hover {
          opacity: 0.9;
        }
        
        &.followed {
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.3);
        }
      }
    }
  }
  
  .user-name-row {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 8px;
    margin-bottom: 6px;
  }
  
  .user-name {
    font-size: 14px;
    font-weight: 600;
    
    &.gradient-gold {
      background: linear-gradient(135deg, #ffd700 0%, #ffb800 30%, #ffa500 60%, #ff8c00 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
  }
  
  .vip-badge {
    width: 40px;
    height: 20px;
    object-fit: contain;
  }
  
  .user-stats {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 30px;
    
    .stat-item {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.7);
    }
    
    .stat-divider {
      width: 12px;
    }
  }
  
  .content-tabs {
    display: flex;
    justify-content: space-around;
    padding: 12px 0;
    background: transparent;
    
    .tab-item {
      position: relative;
      padding: 8px 16px;
      font-size: 15px;
      color: rgba(255, 255, 255, 0.5);
      cursor: pointer;
      transition: color 0.2s;
      
      &.active {
        color: #fff;
        font-weight: 500;
      }
      
      .tab-indicator {
        position: absolute;
        bottom: -2px;
        left: 50%;
        transform: translateX(-50%);
        width: 20px;
        height: 2px;
        background: #a855f7;
        border-radius: 1px;
      }
    }
  }
}

.content-area {
  min-height: 400px;
  padding: 12px;
}

// 视频列表 - 首页横屏样式
.video-grid-horizontal {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  
  .video-card {
    background: #1a1a2e;
    border-radius: 8px;
    overflow: hidden;
    cursor: pointer;
    transition: transform 0.2s;
    
    &:hover {
      transform: scale(1.02);
    }
    
    .video-cover-wrapper {
      position: relative;
      aspect-ratio: 16/9;
      
      .video-cover {
        width: 100%;
        height: 100%;
        object-fit: cover;
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
      
      .play-overlay {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 40px;
        height: 40px;
        background: rgba(0, 0, 0, 0.5);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0;
        transition: opacity 0.2s;
        
        svg {
          width: 20px;
          height: 20px;
        }
      }
      
      &:hover .play-overlay {
        opacity: 1;
      }
    }
    
    .video-info {
      padding: 10px;
      
      .video-title {
        font-size: 13px;
        font-weight: 500;
        color: #fff;
        margin: 0 0 6px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      
      .video-meta {
        font-size: 11px;
        color: rgba(255, 255, 255, 0.5);
      }
    }
  }
}

// 抖音短视频 - 竖屏列表样式
.short-grid-vertical {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2px;
  
  .short-item {
    position: relative;
    aspect-ratio: 9/16;
    cursor: pointer;
    overflow: hidden;
    
    .short-cover {
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.2s;
    }
    
    &:hover .short-cover {
      transform: scale(1.05);
    }
    
    .short-info {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      padding: 8px;
      background: linear-gradient(transparent, rgba(0,0,0,0.7));
      
      .play-count {
        font-size: 12px;
        color: #fff;
      }
    }
  }
}

// 帖子列表样式
.posts-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
  
  .post-item {
    background: #1a1a2e;
    border-radius: 8px;
    padding: 12px;
    cursor: pointer;
    transition: background 0.2s;
    
    &:hover {
      background: #252540;
    }
    
    .post-content {
      font-size: 14px;
      color: #ddd;
      line-height: 1.5;
      margin: 0 0 10px;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
    
    .post-images {
      position: relative;
      width: 80px;
      height: 80px;
      border-radius: 6px;
      overflow: hidden;
      margin-bottom: 10px;
      
      .post-thumb {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
      
      .image-count {
        position: absolute;
        bottom: 4px;
        right: 4px;
        background: rgba(0, 0, 0, 0.6);
        color: #fff;
        font-size: 11px;
        padding: 2px 6px;
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
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  
  .empty-icon {
    width: 160px;
    height: auto;
    margin-bottom: 20px;
  }
  
  .empty-text {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.5);
    margin-bottom: 12px;
  }
  
  .retry-text {
    font-size: 14px;
    color: #a855f7;
    cursor: pointer;
    
    &:hover {
      text-decoration: underline;
    }
  }
}
</style>



