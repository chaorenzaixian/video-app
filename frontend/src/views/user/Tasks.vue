<template>
  <div class="tasks-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.push('/user/profile')"><img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" /></div>
      <nav class="header-tabs">
        <span class="tab-item" @click="$router.push('/user/agent')">代理赚钱</span>
        <span class="tab-item active">福利任务</span>
        <span class="tab-item" @click="$router.push('/user/app-recommend')">应用推荐</span>
      </nav>
    </header>

    <!-- 用户信息区 + VIP按钮（合并） -->
    <div class="user-vip-section">
      <div class="section-background">
        <img src="/images/backgrounds/welfare_vip_background.webp" alt="" class="bg-image" />
        <div class="bg-overlay"></div>
      </div>
      <div class="section-content">
      <div class="user-info">
          <div class="avatar-wrapper">
            <div :class="['avatar-container', { 'is-vip': userStore.isVip }]">
              <div class="avatar-frame">
                <img :src="avatarUrl" class="avatar" alt="">
              </div>
              <!-- VIP皇冠徽章 -->
              <div class="vip-crown" v-if="userStore.isVip">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M5 16L3 5l5.5 5L12 4l3.5 6L21 5l-2 11H5zm14 3c0 .6-.4 1-1 1H6c-.6 0-1-.4-1-1v-1h14v1z"/>
                </svg>
              </div>
            </div>
          </div>
        <div class="info-text">
            <div class="nickname-row">
              <span class="nickname">{{ userStore.user?.nickname || userStore.user?.username }}</span>
              <!-- VIP会员图标 -->
              <img 
                v-if="userStore.isVip && vipLevelIcon" 
                :src="vipLevelIcon" 
                class="vip-level-badge"
                alt="VIP"
              />
        </div>
            <div class="user-id-row">
              <span class="user-id" v-if="userStore.isVip">
                到期: {{ formatVipExpire(userStore.user?.vip_expire_date) }}
              </span>
              <span class="user-id upgrade-hint" v-else @click="$router.push('/user/vip')">
                升级会员 →
              </span>
      </div>
    </div>
        </div>
      </div>
    <button class="vip-btn" @click="$router.push('/user/vip')">
        {{ userStore.isVip ? '续费VIP会员' : '开通VIP不限次数观看' }}
    </button>
    </div>

    <!-- Tab切换 -->
    <div class="tab-section">
      <div class="tabs">
        <span 
          class="tab-item" 
          :class="{ active: activeTab === 'tasks' }"
          @click="activeTab = 'tasks'"
        >福利任务</span>
        <span 
          class="tab-item" 
          :class="{ active: activeTab === 'exchange' }"
          @click="activeTab = 'exchange'"
        >积分兑换</span>
      </div>
    </div>

    <!-- 统计栏 -->
    <div class="stats-bar">
      <div class="stats-left">
        <span>邀请人数<em>{{ pointsInfo.invite_count }}</em>人</span>
        <span>我的积分<em>{{ pointsInfo.available_points }}</em></span>
      </div>
      <button class="record-btn" @click="showHistory = true">兑换记录</button>
    </div>

    <!-- 福利任务列表 -->
    <div v-if="activeTab === 'tasks'" class="task-list">
      <!-- 签到任务 -->
      <div class="task-item">
        <div class="task-icon" style="background: linear-gradient(360deg, #9e52cf, #4d45bf);">
          <span>○</span>
        </div>
        <div class="task-info">
          <div class="task-name">签到任务</div>
          <div class="task-desc">每日签到 <span class="points">+5积分</span></div>
        </div>
        <button 
          class="task-btn" 
          :class="hasCheckedIn ? 'claimed' : 'todo'"
          :disabled="hasCheckedIn"
          @click="doCheckin"
        >
          {{ hasCheckedIn ? '已签到' : '签到' }}
        </button>
      </div>

      <!-- 每日发帖 -->
      <div class="task-item">
        <div class="task-icon" style="background: linear-gradient(360deg, #9e52cf, #4d45bf);">
          <span>📷</span>
        </div>
        <div class="task-info">
          <div class="task-name">每日发帖</div>
          <div class="task-desc">发布帖子 <span class="points">+5积分</span></div>
        </div>
        <button class="task-btn todo">去完成</button>
      </div>

      <!-- 帖子评论 -->
      <div class="task-item">
        <div class="task-icon" style="background: linear-gradient(135deg, #22c55e, #10b981);">
          <span>✏️</span>
        </div>
        <div class="task-info">
          <div class="task-name">帖子评论</div>
          <div class="task-desc">帖子评论十个字以上 获得<span class="points">5积分</span></div>
        </div>
        <button class="task-btn todo">去完成</button>
      </div>

      <!-- 视频评论 -->
      <div class="task-item">
        <div class="task-icon" style="background: linear-gradient(135deg, #22c55e, #10b981);">
          <span>✏️</span>
        </div>
        <div class="task-info">
          <div class="task-name">视频评论</div>
          <div class="task-desc">视频评论十个字以上 获得<span class="points">5积分</span></div>
        </div>
        <button class="task-btn todo">去完成</button>
      </div>

      <!-- 每日邀请 -->
      <div class="task-item">
        <div class="task-icon" style="background: linear-gradient(360deg, #9e52cf, #4d45bf);">
          <span>👥</span>
        </div>
        <div class="task-info">
          <div class="task-name">每日邀请</div>
          <div class="task-desc">每日邀请用户<span class="points">+20积分</span></div>
        </div>
        <button class="task-btn todo" @click="$router.push('/user/promotion')">去完成</button>
      </div>

      <!-- 购买VIP -->
      <div class="task-item">
        <div class="task-icon" style="background: linear-gradient(360deg, #9e52cf, #4d45bf);">
          <span>💎</span>
        </div>
        <div class="task-info">
          <div class="task-name">购买VIP+100积分</div>
          <div class="task-desc">购买任意VIP 即可获得<span class="points">100积分</span></div>
        </div>
        <button class="task-btn todo" @click="$router.push('/user/vip')">去完成</button>
      </div>

      <!-- 下载APP -->
      <div class="task-item">
        <div class="task-icon" style="background: linear-gradient(360deg, #9e52cf, #4d45bf);">
          <span>⬇️</span>
        </div>
        <div class="task-info">
          <div class="task-name">下载APP</div>
          <div class="task-desc">下载好色，即可获得<span class="points">20积分</span></div>
        </div>
        <button 
          class="task-btn" 
          :class="hasDownloadedApp ? 'claimed' : 'todo'"
          :disabled="hasDownloadedApp"
          @click="claimDownloadReward"
        >
          {{ hasDownloadedApp ? '已领取' : '领取' }}
        </button>
      </div>
    </div>

    <!-- 积分兑换 -->
    <div v-else class="exchange-grid">
      <div 
        v-for="(item, index) in exchangeItems" 
        :key="item.id" 
        class="exchange-card"
        :class="['card-theme-' + (index % 6), { 'has-image': item.image_url }]"
      >
        <!-- 票券主体部分 -->
        <div class="ticket-body" :style="getTicketStyle(item)">
          <!-- 只有没有图片时才显示文字 -->
          <div class="ticket-content" v-if="!item.image_url">
            <div class="ticket-title">{{ item.item_name }}</div>
            <div class="ticket-desc">{{ item.item_desc || '兑换精彩好礼' }}</div>
        </div>
        </div>
        <!-- 底部操作区 -->
        <div class="card-footer">
          <div class="card-cost">花费<em>{{ item.points_cost }}</em>积分</div>
        <button 
          class="exchange-btn"
          :disabled="pointsInfo.available_points < item.points_cost"
          @click="doExchange(item)"
        >
          立即兑换
        </button>
        </div>
      </div>

      <div v-if="exchangeItems.length === 0" class="empty-state">
        <span>📦</span>
        <p>暂无可兑换商品</p>
      </div>
    </div>

    <!-- 兑换记录弹窗 - 全屏页面样式 -->
    <div v-if="showHistory" class="history-page">
      <!-- 顶部导航 -->
      <header class="history-header">
        <div class="back-btn" @click="showHistory = false"><img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" /></div>
        <h1 class="header-title">会员兑换</h1>
        <div class="placeholder"></div>
      </header>

      <!-- 当前积分卡片 -->
      <div class="points-card">
        <div class="points-label">当前积分</div>
        <div class="points-value">{{ pointsInfo.available_points }}</div>
        </div>

      <!-- 兑换记录区域 -->
      <div class="records-section">
        <h2 class="section-title">兑换记录</h2>
        
        <!-- 表头 -->
        <div class="records-header">
          <span class="col-name">兑换</span>
          <span class="col-type">兑换类型</span>
          <span class="col-time">兑换时间</span>
            </div>

        <!-- 记录列表 -->
        <div class="records-list">
          <div v-for="record in exchangeRecords" :key="record.id" class="record-row">
            <span class="col-name">{{ record.item_name }}</span>
            <span class="col-type">{{ getExchangeTypeName(record.item_type) }}</span>
            <span class="col-time">{{ formatRecordTime(record.created_at) }}</span>
          </div>
          <div v-if="exchangeRecords.length === 0" class="empty-records">
            <p>暂无兑换记录</p>
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
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('tasks')
const pointsInfo = ref({
  total_points: 0,
  available_points: 0,
  frozen_points: 0,
  invite_count: 0
})
const exchangeItems = ref([])
const exchangeRecords = ref([])
const showHistory = ref(false)
const hasCheckedIn = ref(false)
const hasDownloadedApp = ref(false)

// VIP等级图标映射
const VIP_LEVEL_ICONS = {
  1: '/images/backgrounds/vip_gold.webp',      // 普通VIP
  2: '/images/backgrounds/vip_1.webp',         // VIP1
  3: '/images/backgrounds/vip_2.webp',         // VIP2
  4: '/images/backgrounds/vip_3.webp',         // VIP3
  5: '/images/backgrounds/super_vip_red.webp', // 黄金至尊
  6: '/images/backgrounds/super_vip_blue.webp' // 紫色限定至尊
}

// VIP等级名称
const VIP_LEVEL_NAMES = {
  1: '普通VIP',
  2: 'VIP1',
  3: 'VIP2',
  4: 'VIP3',
  5: '黄金至尊',
  6: '紫色至尊'
}

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

// 根据用户ID自动分配头像
const avatarUrl = computed(() => {
  if (userStore.user?.avatar) {
    return userStore.user.avatar
  }
  const numericId = parseInt(userStore.user?.id) || 1
  return getDefaultAvatarPath(numericId)
})

// VIP等级图标
const vipLevelIcon = computed(() => {
  const level = userStore.user?.vip_level || 1
  return VIP_LEVEL_ICONS[level] || VIP_LEVEL_ICONS[1]
})

// VIP等级名称
const vipLevelName = computed(() => {
  return VIP_LEVEL_NAMES[userStore.user?.vip_level] || '普通VIP'
})

// 复制账号
const copyId = () => {
  if (navigator.clipboard && userStore.user?.username) {
    navigator.clipboard.writeText(String(userStore.user.username))
    ElMessage.success('账号已复制')
  }
}

// 获取积分信息
const fetchPointsInfo = async () => {
  try {
    const res = await api.get('/points/info')
    pointsInfo.value = res.data
  } catch (error) {
    console.error('获取积分信息失败:', error)
  }
}

// 获取任务状态
const fetchTaskStatus = async () => {
  try {
    const res = await api.get('/points/tasks')
    const checkinTask = res.data.find(t => t.task_type === 'checkin')
    if (checkinTask) {
      hasCheckedIn.value = checkinTask.status === 'claimed'
    }
    const downloadTask = res.data.find(t => t.task_type === 'download')
    if (downloadTask) {
      hasDownloadedApp.value = downloadTask.status === 'claimed'
    }
  } catch (error) {
    console.error('获取任务状态失败:', error)
  }
}

// 获取兑换商品
const fetchExchangeItems = async () => {
  try {
    const res = await api.get('/points/exchange/items')
    exchangeItems.value = res.data
  } catch (error) {
    console.error('获取兑换商品失败:', error)
  }
}

// 获取兑换记录
const fetchExchangeRecords = async () => {
  try {
    const res = await api.get('/points/exchange/records')
    exchangeRecords.value = res.data
  } catch (error) {
    console.error('获取兑换记录失败:', error)
  }
}

// 签到
const doCheckin = async () => {
  if (hasCheckedIn.value) return
  try {
    const res = await api.post('/points/tasks/checkin')
    ElMessage.success(res.data.message)
    hasCheckedIn.value = true
    fetchPointsInfo()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '签到失败')
  }
}

// 领取下载APP奖励
const claimDownloadReward = async () => {
  if (hasDownloadedApp.value) return
  try {
    const res = await api.post('/points/tasks/download')
    ElMessage.success(res.data?.message || '领取成功！+20积分')
    hasDownloadedApp.value = true
    fetchPointsInfo()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '领取失败')
  }
}

// 兑换商品
const doExchange = async (item) => {
  try {
    const res = await api.post(`/points/exchange/${item.id}`)
    ElMessage.success(res.data.message)
    fetchPointsInfo()
    fetchExchangeItems()
    // 如果兑换的是VIP，刷新用户信息以更新VIP状态
    if (item.item_type === 'vip_days') {
      await userStore.fetchUser()
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '兑换失败')
  }
}

// 格式化时间
const formatTime = (time) => {
  const d = new Date(time)
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

// 格式化兑换记录时间
const formatRecordTime = (time) => {
  const d = new Date(time)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

// 获取兑换类型名称
const getExchangeTypeName = (type) => {
  const typeMap = {
    'vip_days': 'VIP会员',
    'coins': '金币',
    'ai_tech': 'AI科技券',
    'blind_box': '情趣盲盒'
  }
  return typeMap[type] || type
}

// 格式化VIP到期时间
const formatVipExpire = (date) => {
  if (!date) return '未知'
  const d = new Date(date)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

// 获取票券样式（支持后台上传图片）
const getTicketStyle = (item) => {
  if (item.image_url) {
    let imageUrl = item.image_url
    if (!imageUrl.startsWith('http')) {
      // 开发环境使用相对路径让Vite代理处理
      if (!import.meta.env.DEV) {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
        imageUrl = `${baseUrl}${imageUrl}`
      }
    }
    return {
      backgroundImage: `url(${imageUrl})`,
      backgroundSize: '100% 100%',
      backgroundPosition: 'center',
      backgroundRepeat: 'no-repeat'
    }
  }
  return {}
}

onMounted(() => {
  fetchPointsInfo()
  fetchTaskStatus()
  fetchExchangeItems()
})
</script>

<style lang="scss" scoped>
.tasks-page {
  min-height: 100vh;
  min-height: 100dvh;
  background: #0a0a0a;
  color: #fff;
  width: 100%;
  max-width: 100%;
  padding: 0 env(safe-area-inset-right) 0 env(safe-area-inset-left);
  box-sizing: border-box;
}

// 顶部导航
.page-header {
  display: flex;
  align-items: center;
  padding: 12px 8px;
  padding-top: calc(env(safe-area-inset-top, 16px) + 12px);
  gap: 12px;
  position: sticky;
  top: 0;
  z-index: 100;
  background: linear-gradient(180deg, rgba(30, 25, 40, 1) 0%, rgba(30, 25, 40, 0.95) 100%);
  
  .back-btn {
    font-size: 33px;
    color: #fff;
    cursor: pointer;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
  }
  
  .header-tabs {
    display: flex;
    flex: 1;
    justify-content: space-around;
    align-items: center;
    
    .tab-item {
      font-size: 15px;
      color: rgba(255, 255, 255, 0.5);
      cursor: pointer;
      position: relative;
      padding-bottom: 6px;
      
      &.active {
        color: #fff;
        font-weight: 600;
        
        &::after {
          content: '';
          position: absolute;
          bottom: 0;
          left: 50%;
          transform: translateX(-50%);
          width: 20px;
          height: 2px;
          background: linear-gradient(90deg, #d4af37, #f5d799);
          border-radius: 1px;
        }
      }
    }
  }
}

// 用户信息区 + VIP按钮（合并）
.user-vip-section {
  position: relative;
  margin: 0 12px 20px;
  padding-bottom: 20px;
  border-radius: 16px;
  overflow: hidden;
  width: calc(100% - 24px);
  box-sizing: border-box;
  
  .section-background {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    
    .bg-image {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    
    .bg-overlay {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: linear-gradient(
        180deg,
        rgba(0, 0, 0, 0.1) 0%,
        rgba(0, 0, 0, 0.3) 100%
      );
    }
  }
  
  .section-content {
    position: relative;
    z-index: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  }
  
  .user-info {
    display: flex;
    align-items: center;
    gap: 14px;
    
    .avatar-wrapper {
      .avatar-container {
        position: relative;
        
        .avatar-frame {
          width: 60px;
          height: 60px;
          border-radius: 50%;
          padding: 2px;
          background: rgba(255, 255, 255, 0.2);
    
    .avatar {
            width: 100%;
            height: 100%;
      border-radius: 50%;
      object-fit: cover;
            background: #1a1a1a;
          }
        }
        
        // VIP金色边框效果
        &.is-vip .avatar-frame {
          padding: 3px;
          background: linear-gradient(135deg, #ffd700 0%, #ffec8b 25%, #daa520 50%, #ffd700 75%, #ffec8b 100%);
          background-size: 200% 200%;
          animation: vip-border-shine 3s ease-in-out infinite;
          box-shadow: 
            0 0 10px rgba(255, 215, 0, 0.4),
            0 0 20px rgba(255, 215, 0, 0.2);
        }
        
        // VIP皇冠徽章
        .vip-crown {
          position: absolute;
          top: -6px;
          right: -4px;
          width: 24px;
          height: 24px;
          background: linear-gradient(135deg, #ffd700, #ffec8b);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 2px 8px rgba(255, 215, 0, 0.5);
          animation: crown-bounce 2s ease-in-out infinite;
          
          svg {
            width: 16px;
            height: 16px;
            fill: #8b4513;
          }
        }
      }
    }
    
    .info-text {
      .nickname-row {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 6px;
        
      .nickname {
          font-size: 16px;
        font-weight: 600;
          background: linear-gradient(135deg, #ffd700 0%, #ffec8b 30%, #daa520 60%, #ffd700 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          letter-spacing: 0.5px;
        }
        
        .vip-level-badge {
          height: 20px;
          width: auto;
          max-width: 60px;
          object-fit: contain;
          animation: vip-badge-glow 2s ease-in-out infinite;
        }
      }
      
      .user-id-row {
        display: flex;
        align-items: center;
        gap: 6px;
        
        .user-id {
          font-size: 12px;
        color: rgba(255, 255, 255, 0.6);
          letter-spacing: 0.5px;
          
          &.upgrade-hint {
            color: #a855f7;
          cursor: pointer;
            font-weight: 500;
          
          &:active {
              opacity: 0.8;
            }
          }
        }
      }
    }
  }
  
  @keyframes crown-bounce {
    0%, 100% { transform: translateY(0) rotate(-5deg); }
    50% { transform: translateY(-3px) rotate(5deg); }
  }
  
  @keyframes vip-border-shine {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
  }
  
  @keyframes vip-badge-glow {
    0%, 100% {
      filter: drop-shadow(0 0 3px rgba(255, 215, 0, 0.4));
      transform: scale(1);
    }
    50% {
      filter: drop-shadow(0 0 6px rgba(255, 215, 0, 0.7));
      transform: scale(1.05);
    }
  }

.vip-btn {
    position: relative;
    z-index: 1;
  display: block;
    width: 70%;
    max-width: 280px;
    margin: 16px auto 0;
    padding: 8px 24px;
    background: linear-gradient(360deg, #9e52cf, #4d45bf);
  border: none;
  border-radius: 25px;
  color: #fff;
    font-size: 15px;
    font-weight: 500;
  cursor: pointer;
    box-shadow: 0 4px 15px rgba(158, 82, 207, 0.4);
    transition: all 0.3s ease;
    
    &:active {
      transform: scale(0.98);
    }
  }
}

// Tab切换
.tab-section {
  padding: 0 12px;
  margin-bottom: 12px;
  width: 100%;
  box-sizing: border-box;
  
  .tabs {
    display: flex;
    gap: 24px;
    
    .tab-item {
      font-size: 15px;
      font-weight: 500;
      color: rgba(255, 255, 255, 0.4);
      cursor: pointer;
      
      &.active {
        color: #fff;
      }
    }
  }
}

// 统计栏
.stats-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  margin-bottom: 16px;
  
  .stats-left {
    display: flex;
    gap: 20px;
    
    span {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.6);
      
      em {
        font-style: normal;
        color: #fff;
        margin: 0 2px;
      }
    }
  }
  
  .record-btn {
    height: 30px !important;
    min-height: 30px;
    max-height: 30px;
    padding: 0 16px !important;
    background: linear-gradient(135deg, #d4af37, #f5d799, #d4af37) !important;
    border: none !important;
    border-radius: 15px !important;
    color: #1a1a2e;
    font-size: 12px !important;
    font-weight: 600;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    line-height: 1;
    box-sizing: border-box;
    box-shadow: 0 2px 8px rgba(212, 175, 55, 0.3);
    transition: all 0.3s ease;
    
    &:hover {
      box-shadow: 0 4px 12px rgba(212, 175, 55, 0.5);
      transform: translateY(-1px);
    }
    
    &:active {
      transform: scale(0.98);
    }
  }
}

// 任务列表
.task-list {
  padding: 0 12px;
  width: 100%;
  box-sizing: border-box;
  
  .task-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px;
    background: rgba(30, 27, 75, 0.6);
    border-radius: 12px;
    margin-bottom: 10px;
    
    .task-icon {
      width: 32px;
      height: 32px;
      min-width: 32px;
      min-height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 8px;
      font-size: 16px;
      flex-shrink: 0;
      
      // 确保emoji/图标居中且大小一致
      span, img {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        height: 100%;
        font-family: "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif;
        line-height: 1;
      }
      
      img {
        width: 22px;
        height: 22px;
        object-fit: contain;
      }
    }
    
    .task-info {
      flex: 1;
      
      .task-name {
        font-size: 13px;
        font-weight: 500;
        margin-bottom: 4px;
      }
      
      .task-desc {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.5);
        
        .points {
          color: rgba(255, 255, 255, 0.7);
        }
      }
    }
    
    .task-btn {
      height: 30px !important;
      min-height: 30px;
      max-height: 30px;
      padding: 0 16px !important;
      border-radius: 15px !important;
      font-size: 12px !important;
      font-weight: 500;
      cursor: pointer;
      flex-shrink: 0;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      line-height: 1;
      box-sizing: border-box;
      
      &.todo {
        background: linear-gradient(360deg, #9e52cf, #4d45bf) !important;
        border: none !important;
        color: #fff;
      }
      
      &.pending {
        background: transparent !important;
        border: 1.5px solid #d4a574 !important;
        color: #d4a574;
      }
      
      &.claimed {
        background: rgba(158, 82, 207, 0.3) !important;
        border: none !important;
        color: rgba(255, 255, 255, 0.5);
        cursor: not-allowed;
      }
    }
  }
}

// 积分兑换 - 票券风格卡片
.exchange-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  padding: 0 16px;
  
  .exchange-card {
    border-radius: 12px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    background: #1a1a24;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
    
    &:active {
      transform: scale(0.98);
    }
    
    // 票券主体部分
    .ticket-body {
      position: relative;
      aspect-ratio: 2.2 / 1;
      border-radius: 8px;
      margin: 6px 6px 0 6px;
      overflow: hidden;
      display: flex;
      align-items: flex-end;
      
      .ticket-content {
      position: relative;
      z-index: 1;
        padding: 12px;
        width: 100%;
        
        .ticket-title {
          font-size: 16px;
          font-weight: 700;
        color: #fff;
          margin-bottom: 4px;
          text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
          line-height: 1.2;
        }
        
        .ticket-desc {
        font-size: 11px;
          color: rgba(255, 255, 255, 0.85);
          text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
          line-height: 1.3;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
      }
    }
    
    // 没有图片时显示遮罩
    &:not(.has-image) .ticket-body::after {
      content: '';
      position: absolute;
      inset: 0;
      background: linear-gradient(
        to top,
        rgba(0, 0, 0, 0.6) 0%,
        rgba(0, 0, 0, 0.2) 50%,
        transparent 100%
      );
      pointer-events: none;
    }
    
    // 底部操作区
    .card-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 10px;
      gap: 8px;
      
      .card-cost {
        font-size: 10px;
        color: rgba(255, 255, 255, 0.6);
        white-space: nowrap;
        
        em {
          font-style: normal;
          font-weight: 600;
        color: #ffd700;
          font-size: 12px;
        }
      }
      
      button.exchange-btn {
        height: 24px !important;
        min-height: auto !important;
        min-width: auto !important;
        padding: 0 12px !important;
        background: linear-gradient(135deg, #9333ea 0%, #a855f7 50%, #7c3aed 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        color: #fff !important;
        font-size: 11px !important;
        font-weight: 500 !important;
      cursor: pointer;
        transition: all 0.2s;
        box-shadow: none !important;
        -webkit-appearance: none !important;
        appearance: none !important;
        white-space: nowrap !important;
        flex-shrink: 0;
        
        &:active {
          transform: scale(0.95);
          opacity: 0.9;
        }
      
      &:disabled {
          background: linear-gradient(135deg, #9333ea 0%, #a855f7 50%, #7c3aed 100%) !important;
          color: #fff !important;
          opacity: 0.6;
        cursor: not-allowed;
        }
      }
    }
    
    // 默认主题颜色（当没有上传图片时）
    &.card-theme-0 .ticket-body {
      background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
    }
    &.card-theme-1 .ticket-body {
      background: linear-gradient(135deg, #374151 0%, #111827 100%);
    }
    &.card-theme-2 .ticket-body {
      background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
    }
    &.card-theme-3 .ticket-body {
      background: linear-gradient(135deg, #ec4899 0%, #db2777 100%);
    }
    &.card-theme-4 .ticket-body {
      background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
    }
    &.card-theme-5 .ticket-body {
      background: linear-gradient(135deg, #a855f7 0%, #9333ea 100%);
    }
  }
  
  .empty-state {
    grid-column: span 2;
    text-align: center;
    padding: 60px;
    
    span {
      font-size: 48px;
      opacity: 0.5;
    }
    
    p {
      color: rgba(255, 255, 255, 0.5);
      margin-top: 16px;
      font-size: 14px;
    }
  }
}

// 兑换记录页面 - 全屏样式
.history-page {
  position: fixed;
  inset: 0;
  background: linear-gradient(180deg, #1a1a2e 0%, #0d0d15 100%);
  z-index: 200;
  overflow-y: auto;
  color: #fff;
  
  // 顶部导航
  .history-header {
      display: flex;
      align-items: center;
    justify-content: space-between;
      padding: 16px 20px;
    padding-top: calc(env(safe-area-inset-top) + 16px);
    
    .back-btn {
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      color: #fff;
      cursor: pointer;
    }
    
    .header-title {
      font-size: 15px;
      font-weight: 600;
      margin: 0;
    }
    
    .placeholder {
      width: 32px;
    }
  }
  
  // 当前积分卡片
  .points-card {
    margin: 16px 20px;
    padding: 24px;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(88, 28, 135, 0.25) 100%);
    border: 1px solid rgba(139, 92, 246, 0.5);
    border-radius: 12px;
    text-align: center;
    
    .points-label {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.7);
      margin-bottom: 8px;
    }
    
    .points-value {
      font-size: 42px;
      font-weight: 700;
      color: #a855f7;
      line-height: 1;
    }
  }
  
  // 兑换记录区域
  .records-section {
    padding: 0 20px;
    
    .section-title {
        font-size: 16px;
        font-weight: 600;
      margin: 24px 0 16px;
    }
    
    // 表头
    .records-header {
      display: flex;
      background: #2a2a3a;
      border-radius: 8px;
      padding: 12px 16px;
      margin-bottom: 8px;
      
      span {
        font-size: 13px;
        color: rgba(255, 255, 255, 0.7);
        font-weight: 500;
      }
      
      .col-name {
        flex: 1;
      }
      
      .col-type {
        flex: 1;
        text-align: center;
      }
      
      .col-time {
        flex: 1.2;
        text-align: right;
      }
    }
    
    // 记录列表
    .records-list {
      .record-row {
        display: flex;
        padding: 14px 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        
        span {
          font-size: 13px;
        }
        
        .col-name {
          flex: 1;
          color: #fff;
        }
        
        .col-type {
          flex: 1;
          text-align: center;
          color: rgba(255, 255, 255, 0.7);
        }
        
        .col-time {
          flex: 1.2;
          text-align: right;
          color: rgba(255, 255, 255, 0.5);
          font-size: 12px;
        }
      }
      
      .empty-records {
        text-align: center;
        padding: 60px 20px;
        
        p {
        color: rgba(255, 255, 255, 0.5);
          font-size: 14px;
        }
      }
    }
  }
}

// ============ 响应式适配 ============

// 小屏幕手机
@media (max-width: 374px) {
  .task-item {
    padding: 12px;
    gap: 10px;
    
    .task-icon {
      width: 28px;
      height: 28px;
      min-width: 28px;
      min-height: 28px;
      font-size: 14px;
    }
    
    .task-info {
      .task-name {
        font-size: 14px;
      }
      .task-desc {
        font-size: 12px;
      }
    }
    
    .task-btn {
      padding: 6px 12px;
      font-size: 12px;
    }
  }
  
  .exchange-grid {
    gap: 12px;
  }
}

// 平板 (768px+)
@media (min-width: 768px) {
  .tasks-page {
    max-width: 750px;
    margin: 0 auto;
  }
  
  .task-item {
    padding: 18px 20px;
    
    .task-icon {
      width: 36px;
      height: 36px;
      min-width: 36px;
      min-height: 36px;
      font-size: 18px;
      border-radius: 10px;
    }
    
    .task-info {
      .task-name {
        font-size: 16px;
      }
      .task-desc {
        font-size: 14px;
      }
    }
  }
  
  .exchange-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
  }
}

// 桌面 (1024px+)
@media (min-width: 1024px) {
  .tasks-page {
    max-width: 900px;
  }
  
  .exchange-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

// 大桌面 (1280px+)
@media (min-width: 1280px) {
  .tasks-page {
    max-width: 1100px;
  }
}

// 触摸设备优化
@media (hover: none) and (pointer: coarse) {
  .task-item:hover,
  .exchange-card:hover {
    transform: none !important;
  }
  
  .task-item:active,
  .exchange-card:active {
    transform: scale(0.98);
    opacity: 0.9;
  }
}
</style>