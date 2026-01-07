<template>
  <div class="creator-center-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
        </svg>
      </div>
      <h1 class="page-title">创作中心</h1>
      <div class="header-right"></div>
    </header>

    <!-- 非VIP提示 -->
    <div class="not-vip-notice" v-if="!isLoading && !isCreator">
      <div class="notice-icon">
        <svg viewBox="0 0 24 24" width="48" height="48" fill="#ffd700">
          <path d="M12 2L4 5v6.09c0 5.05 3.41 9.76 8 10.91 4.59-1.15 8-5.86 8-10.91V5l-8-3zm-1 15h2v2h-2v-2zm0-8h2v6h-2V9z"/>
        </svg>
      </div>
      <h3 class="notice-title">开通VIP成为创作者</h3>
      <p class="notice-desc">VIP用户可享受创作者权益，上传视频赚取收益</p>
      <button class="vip-btn" @click="$router.push('/user/vip')">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
          <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>
        </svg>
        立即开通VIP
      </button>
    </div>

    <!-- 收益卡片 (仅创作者可见) -->
    <div class="earnings-card" v-if="isCreator">
      <div class="earnings-content">
        <div class="earnings-item">
          <span class="label">收益余额</span>
          <span class="value">{{ earningsBalance }}</span>
          <button class="action-btn" @click="handleWithdraw">立即提现</button>
          </div>
        <div class="earnings-item">
          <span class="label">累计收益</span>
          <span class="value">{{ totalEarnings }}</span>
          <button class="action-btn" @click="handleDetail">业绩明细</button>
          </div>
        </div>
      </div>

    <!-- Tab 切换 (仅创作者可见) -->
    <div class="tabs" v-if="isCreator">
      <div 
        class="tab-item" 
        :class="{ active: activeTab === 'published' }"
        @click="activeTab = 'published'"
      >
        已发布
          </div>
      <div 
        class="tab-item" 
        :class="{ active: activeTab === 'pending' }"
        @click="activeTab = 'pending'"
      >
        待审核
          </div>
      <div 
        class="tab-item" 
        :class="{ active: activeTab === 'rejected' }"
        @click="activeTab = 'rejected'"
      >
        未通过
          </div>
        </div>
        
    <!-- 内容列表 (仅创作者可见) -->
    <div class="content-area" v-if="isCreator">
      <!-- 加载中 -->
      <div class="loading-state" v-if="isLoading">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>
      
      <!-- 视频列表 -->
      <div class="video-list" v-else-if="currentList.length > 0">
        <div class="video-item" v-for="video in currentList" :key="video.id" @click="handleVideoClick(video)">
          <div class="video-cover">
            <img :src="video.cover_url || '/images/default-cover.webp'" :alt="video.title" />
            <span v-if="video.review_status === 'rejected'" class="status-tag rejected">未通过</span>
            <span v-else-if="video.review_status === 'pending'" class="status-tag pending">审核中</span>
          </div>
          <div class="video-info">
            <h3 class="video-title">{{ video.title }}</h3>
            <div class="video-stats">
              <span><svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg> {{ video.view_count || 0 }}</span>
              <span><svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg> {{ video.like_count || 0 }}</span>
          </div>
            <p v-if="video.reject_reason" class="reject-reason">{{ video.reject_reason }}</p>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div class="empty-state" v-else>
        <img src="/images/backgrounds/no_data.webp" alt="暂无内容" class="empty-image" />
        <p class="empty-text">当前页面暂无内容~</p>
        </div>
      </div>

    <!-- 底部发布按钮 (仅创作者可见) -->
    <div class="publish-btn" v-if="isCreator" @click="showPublishModal = true">
      <img src="/images/backgrounds/publish.webp" alt="发布" />
      </div>

    <!-- 发布类型选择弹窗 -->
    <div class="publish-modal" v-if="showPublishModal" @click.self="showPublishModal = false">
      <div class="modal-content">
        <div class="modal-handle"></div>
        <h3 class="modal-title">选择发布类型</h3>
        <div class="publish-options">
          <div class="publish-option" @click="handlePublishType('image')">
            <img src="/images/backgrounds/publish_img_1.webp" alt="图片" />
            <span>图片</span>
        </div>
          <div class="publish-option" @click="handlePublishType('video')">
            <img src="/images/backgrounds/publish_video.webp" alt="视频" />
            <span>视频</span>
          </div>
          <div class="publish-option" @click="handlePublishType('article')">
            <img src="/images/backgrounds/publish_img_text.webp" alt="图文" />
            <span>图文</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const router = useRouter()

const activeTab = ref('published')
const earningsBalance = ref(0)
const totalEarnings = ref(0)
const isCreator = ref(false)
const isLoading = ref(true)
const showPublishModal = ref(false)

// 视频列表
const publishedVideos = ref([])
const pendingVideos = ref([])
const rejectedVideos = ref([])

// 当前显示的列表
const currentList = computed(() => {
  switch (activeTab.value) {
    case 'published':
      return publishedVideos.value
    case 'pending':
      return pendingVideos.value
    case 'rejected':
      return rejectedVideos.value
    default:
      return []
  }
})

// 格式化时长
const formatDuration = (seconds) => {
  if (!seconds) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 获取创作者数据
const fetchCreatorData = async () => {
  isLoading.value = true
  
  try {
    // 获取收益数据（使用 dashboard 接口）
    const dashboardRes = await api.get('/creator/dashboard')
    if (dashboardRes.data) {
      isCreator.value = true
      earningsBalance.value = dashboardRes.data.available_coins || 0
      totalEarnings.value = dashboardRes.data.total_coins_earned || 0
    }
  } catch (error) {
    // 404 表示用户还不是创作者，这是正常情况
    if (error.response?.status === 404) {
      isCreator.value = false
    } else {
      console.log('获取收益数据失败:', error)
    }
  }

  // 无论是否是创作者，都尝试获取视频列表（用户上传的视频）
  try {
    const publishedRes = await api.get('/creator/videos', { params: { status: 'approved' } })
    if (publishedRes.data) {
      publishedVideos.value = Array.isArray(publishedRes.data) ? publishedRes.data : []
    }
  } catch (error) {
    if (error.response?.status !== 404) {
      console.log('获取已发布视频失败:', error)
    }
  }

  try {
    const pendingRes = await api.get('/creator/videos', { params: { status: 'pending' } })
    if (pendingRes.data) {
      pendingVideos.value = Array.isArray(pendingRes.data) ? pendingRes.data : []
    }
  } catch (error) {
    if (error.response?.status !== 404) {
      console.log('获取待审核视频失败:', error)
    }
  }

  try {
    const rejectedRes = await api.get('/creator/videos', { params: { status: 'rejected' } })
    if (rejectedRes.data) {
      rejectedVideos.value = Array.isArray(rejectedRes.data) ? rejectedRes.data : []
    }
  } catch (error) {
    if (error.response?.status !== 404) {
      console.log('获取未通过视频失败:', error)
    }
  }
  
  isLoading.value = false
}

// 立即提现
const handleWithdraw = () => {
  router.push('/user/withdraw?type=creator') // 跳转到统一提现页面（创作者模式）
}

// 业绩明细
const handleDetail = () => {
  router.push('/user/earnings-detail')
}

// 视频点击
const handleVideoClick = (video) => {
  router.push(`/video/${video.id}`)
}

// 发布内容
const handlePublishType = (type) => {
  showPublishModal.value = false
  
  switch (type) {
    case 'image':
      router.push('/user/publish/image')
      break
    case 'video':
      router.push('/user/publish/video')
      break
    case 'article':
      router.push('/user/publish/text-image')
      break
  }
}

onMounted(() => {
  fetchCreatorData()
})
</script>

<style lang="scss" scoped>
.creator-center-page {
  min-height: 100vh;
  background: #0a0a0a;
  color: #fff;
  padding-bottom: 100px;
}

// 非VIP提示
.not-vip-notice {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  
  .notice-icon {
    margin-bottom: 20px;
    
    svg {
      filter: drop-shadow(0 4px 12px rgba(255, 215, 0, 0.3));
    }
  }
  
  .notice-title {
    font-size: 18px;
    font-weight: 600;
    color: #fff;
    margin: 0 0 10px;
  }
  
  .notice-desc {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.6);
    margin: 0 0 24px;
    max-width: 260px;
  }
  
  .vip-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 32px;
    background: linear-gradient(135deg, #ffd700, #ffb800);
    border: none;
    border-radius: 24px;
    color: #1a1a2e;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 16px rgba(255, 215, 0, 0.3);
    transition: all 0.3s;
    
    &:active {
      transform: scale(0.95);
      opacity: 0.9;
    }
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

.earnings-card {
  margin: 0 16px 16px;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f0f1a 100%);
  border-radius: 12px;
  padding: 18px 16px;
  position: relative;
  overflow: hidden;
  
  // 装饰曲线
  &::before {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 200px;
    height: 100%;
    background: linear-gradient(135deg, transparent 30%, rgba(118, 75, 162, 0.1) 50%, rgba(102, 126, 234, 0.15) 100%);
    border-radius: 0 16px 16px 0;
  }
  
  &::after {
    content: '';
    position: absolute;
    top: 50%;
    right: 60px;
    width: 150px;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255, 215, 0, 0.3), transparent);
    transform: rotate(-15deg);
  }
  
  .earnings-content {
    display: flex;
    justify-content: space-around;
    position: relative;
    z-index: 1;
  }
  
  .earnings-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    
    .label {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.7);
    }
    
    .value {
      font-size: 28px;
      font-weight: 700;
    color: #fff;
    }
    
    .action-btn {
      margin-top: 6px;
      padding: 5px 20px;
      background: linear-gradient(135deg, #667eea, #764ba2);
      border: none;
      border-radius: 16px;
      color: #fff;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.3s;
      
      &:active {
        transform: scale(0.95);
        opacity: 0.9;
      }
    }
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
        border-radius: 2px;
      }
    }
  }
}

.content-area {
  flex: 1;
  padding: 16px;
  }
  
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  
  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid rgba(102, 126, 234, 0.3);
    border-top-color: #667eea;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  p {
    margin-top: 16px;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.6);
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.video-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  
  .video-item {
    display: flex;
    gap: 12px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    overflow: hidden;
    cursor: pointer;
    transition: background 0.2s;
    
    &:active {
      background: rgba(255, 255, 255, 0.08);
    }
    
    .video-cover {
      width: 140px;
      height: 80px;
      flex-shrink: 0;
      position: relative;
      border-radius: 8px;
      overflow: hidden;
      
      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
      
      .status-tag {
        position: absolute;
        top: 4px;
        left: 4px;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 10px;
      color: #fff;
      
      &.pending {
          background: rgba(255, 193, 7, 0.9);
        }
        
        &.rejected {
          background: rgba(244, 67, 54, 0.9);
        }
      }
    }
    
    .video-info {
      flex: 1;
      padding: 10px 12px 10px 0;
    display: flex;
      flex-direction: column;
    justify-content: space-between;
    
      .video-title {
      font-size: 14px;
        font-weight: 500;
        margin: 0;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }
      
      .video-stats {
        display: flex;
        gap: 16px;
      font-size: 12px;
        color: rgba(255, 255, 255, 0.5);
        
        span {
    display: flex;
    align-items: center;
          gap: 4px;
          
          svg {
            fill: currentColor;
          }
        }
      }
      
      .reject-reason {
        font-size: 12px;
        color: #f44336;
        margin: 4px 0 0;
        display: -webkit-box;
        -webkit-line-clamp: 1;
        -webkit-box-orient: vertical;
    overflow: hidden;
    }
  }
  }
}

.empty-state {
    display: flex;
  flex-direction: column;
    align-items: center;
  justify-content: center;
  padding: 60px 20px;
  
  .empty-image {
    width: 100px;
    height: auto;
    margin-bottom: 16px;
  }
  
  .empty-text {
    font-size: 13px;
    color: rgba(102, 126, 234, 0.8);
    margin: 0;
  }
}

.publish-btn {
  position: fixed;
  bottom: calc(30px + env(safe-area-inset-bottom, 0px));
  right: 16px;
  width: 48px;
  height: 48px;
  cursor: pointer;
  z-index: 100;
  transition: transform 0.2s;
  
  &:active {
    transform: scale(0.9);
  }
  
  img {
    width: 100%;
    height: 100%;
    object-fit: contain;
  }
}

.publish-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 200;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  
  .modal-content {
    width: 100%;
    background: #0f0f1a;
    border-radius: 16px 16px 0 0;
    padding: 12px 20px;
    padding-bottom: calc(20px + env(safe-area-inset-bottom, 0px));
    animation: slideUp 0.3s ease;
  }
  
  .modal-handle {
    width: 32px;
    height: 3px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 2px;
    margin: 0 auto 12px;
  }
  
  .modal-title {
    font-size: 14px;
    font-weight: 600;
      color: #fff;
    text-align: center;
    margin: 0 0 18px;
  }
  
  .publish-options {
    display: flex;
    justify-content: center;
    gap: 32px;
  }
  
  .publish-option {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    transition: transform 0.2s;
    
    &:active {
      transform: scale(0.95);
    }
    
    img {
      width: 44px;
      height: 44px;
      border-radius: 12px;
    }
    
    span {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.8);
    }
  }
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
  }
  to {
    transform: translateY(0);
  }
}
</style>