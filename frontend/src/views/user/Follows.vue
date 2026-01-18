<template>
  <div class="follows-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </div>
      <h1 class="page-title">关注/粉丝</h1>
      <div class="header-right"></div>
    </header>

    <!-- Tab 切换 -->
    <div class="tabs">
      <div 
        class="tab-item" 
        :class="{ active: activeTab === 'following' }"
        @click="activeTab = 'following'"
      >
        关注 <span class="count">{{ followingCount }}</span>
      </div>
      <div 
        class="tab-item" 
        :class="{ active: activeTab === 'followers' }"
        @click="activeTab = 'followers'"
      >
        粉丝 <span class="count">{{ followersCount }}</span>
      </div>
    </div>

    <!-- 用户列表 -->
    <div class="user-list">
      <!-- 加载中 -->
      <div class="loading-state" v-if="isLoading">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>

      <!-- 用户列表 -->
      <template v-else-if="currentList.length > 0">
        <div class="user-item" v-for="user in currentList" :key="user.id" @click="goToUserProfile(user)">
          <img 
            :src="getUserAvatar(user)" 
            :alt="user.nickname" 
            class="user-avatar"
            @error="handleAvatarError"
          />
          <div class="user-info">
            <div class="user-nickname-row">
              <span class="user-nickname gradient-gold">{{ user.nickname || '用户' + user.id }}</span>
              <img 
                v-if="user.vip_level && user.vip_level > 0" 
                :src="getVipIcon(user.vip_level)" 
                class="vip-badge"
                :alt="`VIP${user.vip_level}`"
              />
            </div>
            <div class="user-bio">{{ user.bio || '这个人很懒，什么都没写~' }}</div>
          </div>
          <button 
            v-if="activeTab === 'following'"
            class="action-btn following"
            @click.stop="handleUnfollow(user)"
          >
            已关注
          </button>
          <button 
            v-else
            class="action-btn"
            :class="{ following: user.is_following }"
            @click.stop="handleFollowToggle(user)"
          >
            {{ user.is_following ? '已关注' : '关注' }}
          </button>
        </div>
      </template>

      <!-- 空状态 -->
      <div class="empty-state" v-else>
        <img src="/images/backgrounds/no_data.webp" alt="暂无数据" class="empty-image" />
        <p class="empty-text">{{ activeTab === 'following' ? '还没有关注任何人' : '还没有粉丝' }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'
import { getAvatarUrl } from '@/utils/avatar'

const router = useRouter()

const activeTab = ref('following')
const isLoading = ref(true)
const followingList = ref([])
const followersList = ref([])
const followingCount = ref(0)
const followersCount = ref(0)

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

// 当前显示的列表
const currentList = computed(() => {
  return activeTab.value === 'following' ? followingList.value : followersList.value
})

// 获取用户头像（使用统一的工具函数）
const getUserAvatar = (user) => {
  return getAvatarUrl(user.avatar, user.id)
}

// 头像加载失败时的处理
const handleAvatarError = (e) => {
  e.target.src = '/images/avatars/icon_avatar_1.webp'
}

// 获取关注列表
const fetchFollowing = async () => {
  try {
    const res = await api.get('/creator/following')
    if (res.data) {
      followingList.value = res.data.items || []
      followingCount.value = res.data.total || 0
    }
  } catch (error) {
    // 404 表示没有关注任何人，正常情况
    if (error.response?.status !== 404) {
      console.error('获取关注列表失败:', error)
    }
    followingList.value = []
    followingCount.value = 0
  }
}

// 获取粉丝列表
const fetchFollowers = async () => {
  try {
    const res = await api.get('/creator/followers')
    if (res.data) {
      followersList.value = res.data.items || []
      followersCount.value = res.data.total || 0
    }
  } catch (error) {
    // 404 表示没有粉丝，正常情况
    if (error.response?.status !== 404) {
      console.error('获取粉丝列表失败:', error)
    }
    followersList.value = []
    followersCount.value = 0
  }
}

// 加载数据
const loadData = async () => {
  isLoading.value = true
  await Promise.all([fetchFollowing(), fetchFollowers()])
  isLoading.value = false
}

// 取消关注
const handleUnfollow = async (user) => {
  try {
    await api.delete(`/creator/follow/${user.id}`)
    followingList.value = followingList.value.filter(u => u.id !== user.id)
    followingCount.value = Math.max(0, followingCount.value - 1)
    ElMessage.success('已取消关注')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

// 关注/取消关注切换
const handleFollowToggle = async (user) => {
  try {
    if (user.is_following) {
      await api.delete(`/users/${user.id}/follow`)
      user.is_following = false
      ElMessage.success('已取消关注')
    } else {
      await api.post(`/users/${user.id}/follow`)
      user.is_following = true
      ElMessage.success('关注成功')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

// 跳转到用户主页
const goToUserProfile = (user) => {
  router.push(`/user/member/${user.id}`)
}

onMounted(loadData)
</script>

<style lang="scss" scoped>
$breakpoint-lg: 768px;
$breakpoint-xl: 1024px;

.follows-page {
  min-height: 100vh;
  background: #0a0a0a;
  color: #fff;
  
  @media (min-width: $breakpoint-lg) {
    max-width: 650px;
    margin: 0 auto;
  }
  @media (min-width: $breakpoint-xl) {
    max-width: 750px;
  }
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  padding-top: calc(16px + env(safe-area-inset-top, 0px));
  background: #0a0a0a;
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
      fill: #fff;
    }
  }
  
  .page-title {
    font-size: 16px;
    font-weight: 600;
    margin: 0;
  }
  
  .header-right {
    width: 32px;
  }
}

.tabs {
  display: flex;
  padding: 0 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  
  .tab-item {
    flex: 1;
    text-align: center;
    padding: 12px 0;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.6);
    cursor: pointer;
    position: relative;
    transition: color 0.3s;
    
    .count {
      margin-left: 4px;
      font-size: 13px;
    }
    
    &.active {
      color: #fff;
      font-weight: 600;
      
      &::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 24px;
        height: 3px;
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 1.5px;
      }
    }
  }
}

.user-list {
  padding: 16px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 20px;
  
  .loading-spinner {
    width: 36px;
    height: 36px;
    border: 3px solid rgba(102, 126, 234, 0.3);
    border-top-color: #667eea;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  p {
    margin-top: 12px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.6);
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.user-item {
  display: flex;
  align-items: center;
  padding: 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 10px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: background 0.2s;
  min-height: 72px;
  
  @media (hover: hover) {
    &:hover {
      background: rgba(255, 255, 255, 0.06);
    }
  }
  
  &:active {
    background: rgba(255, 255, 255, 0.06);
  }
  
  .user-avatar {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    object-fit: cover;
    margin-right: 12px;
    flex-shrink: 0;
    background: #1a1a1a;
  }
  
  .user-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
    
    .user-nickname-row {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 4px;
      height: 20px;
    }
    
    .user-nickname {
      font-size: 14px;
      font-weight: 600;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 140px;
      
      &.gradient-gold {
        background: linear-gradient(135deg, #ffd700 0%, #ffb800 30%, #ffa500 60%, #ff8c00 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }
    }
    
    .vip-badge {
      width: 32px;
      height: 16px;
      object-fit: contain;
      flex-shrink: 0;
    }
    
    .user-bio {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      line-height: 1.4;
    }
  }
  
  .action-btn {
    padding: 6px 16px;
    font-size: 12px;
    border-radius: 16px;
    cursor: pointer;
    transition: all 0.2s;
    flex-shrink: 0;
    min-width: 64px;
    text-align: center;
    
    &:not(.following) {
      background: linear-gradient(135deg, #667eea, #764ba2);
      border: none;
      color: #fff;
    }
    
    &.following {
      background: transparent;
      border: 1px solid rgba(255, 255, 255, 0.3);
      color: rgba(255, 255, 255, 0.7);
    }
    
    &:active {
      opacity: 0.8;
    }
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 20px;
  
  .empty-image {
    width: 100px;
    height: auto;
    margin-bottom: 16px;
    opacity: 0.6;
  }
  
  .empty-text {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.5);
    margin: 0;
  }
}
</style>



