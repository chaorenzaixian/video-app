<template>
  <div class="profile-page">
    <!-- 顶部背景图 -->
    <div class="profile-bg">
      <img src="/images/backgrounds/profile_bg.webp" alt="" />
      <div class="bg-overlay"></div>
    </div>
    
    <!-- 顶部栏 -->
    <header class="page-header">
      <div class="header-left">
        <div class="notification-wrapper" @click="$router.push('/user/messages')">
          <img src="/images/backgrounds/mine_notification.webp" class="header-icon-img" alt="通知" />
          <span v-if="unreadMessageCount > 0" class="notification-badge">{{ unreadMessageCount > 99 ? '99+' : unreadMessageCount }}</span>
        </div>
      </div>
      <div class="header-right">
        <img src="/images/backgrounds/ic_service.webp" class="header-icon-img" alt="客服" @click="$router.push('/user/customer-service')" />
        <img src="/images/backgrounds/ic_setting.webp" class="header-icon-img" alt="设置" @click="$router.push('/user/settings')" />
      </div>
    </header>
    <div class="user-section">
      <div class="user-row">
        <div class="avatar-wrapper">
          <div :class="['avatar-container', { 'is-vip': user.is_vip }]">
            <div class="avatar-frame">
              <img :src="avatarUrl" class="user-avatar" />
            </div>
            <div class="vip-crown" v-if="user.is_vip">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M5 16L3 5l5.5 5L12 4l3.5 6L21 5l-2 11H5zm14 3c0 .6-.4 1-1 1H6c-.6 0-1-.4-1-1v-1h14v1z"/>
              </svg>
            </div>
            <div class="gender-icon">♂</div>
          </div>
        </div>
        <div class="user-info">
          <div class="nickname-row">
            <h2 class="nickname">{{ isLoading ? '加载中...' : (user.nickname || user.username || '未登录') }}</h2>
            <!-- VIP等级标识 - 昵称右侧 -->
            <img 
              v-if="user.vip_level > 0" 
              :src="vipLevelIcon" 
              class="vip-level-badge-inline"
              :alt="vipLevelName"
            />
          </div>
          <div class="user-id-row">
            <span class="user-id">{{ isLoading ? '--------' : user.username }}</span>
            <svg v-if="!isLoading && user.username" class="copy-btn" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" @click="copyId">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
            </svg>
          </div>
        </div>
        <div class="sign-btn" :class="{ disabled: signingIn }" @click="handleSign">
          <img src="/images/backgrounds/ic_sign.webp" class="sign-icon-img" alt="签到" />
          <span>{{ signingIn ? '签到中...' : '签到' }}</span>
        </div>
      </div>
      <!-- 统计数据已隐藏，保留占位空间 -->
      <div class="stats-row" style="height: 50px;"></div>
    </div>

    <!-- VIP推广条 -->
    <div class="vip-banner" @click="$router.push('/user/vip')">
      <!-- 星星装饰 -->
      <div class="vip-stars">
        <span class="star s1">✦</span>
        <span class="star s2">✦</span>
        <span class="star s3">✦</span>
        <span class="star s4">✦</span>
      </div>
      
      <!-- 非会员样式 -->
      <template v-if="!user.is_vip">
        <div class="vip-left">
          <span class="vip-text">
            <span class="text-gradient">开通会员</span>
            <span class="text-gradient-light">享专属特权</span>
          </span>
        </div>
        <div class="vip-btn">
          <span>开通会员</span>
          <div class="arrow-circle">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
            </svg>
          </div>
        </div>
      </template>
      
      <!-- 已是会员样式 -->
      <template v-else>
        <div class="vip-left">
          <div class="vip-member-content">
            <img 
              v-if="user.vip_level > 0" 
              :src="vipLevelIcon" 
              class="vip-icon-inline"
              :alt="vipLevelName"
            />
            <span class="vip-expire-inline">到期时间：{{ formattedExpireDate || '永久' }}</span>
          </div>
        </div>
        <div class="vip-btn" @click.stop="$router.push('/user/vip')">
          <span>升级会员</span>
          <div class="arrow-circle">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
            </svg>
          </div>
        </div>
      </template>
    </div>

    <!-- 三卡片入口 -->
    <div class="card-grid">
      <div class="feature-card card-vip" @click="$router.push('/user/vip')"></div>
      <div class="feature-card card-wallet" @click="$router.push('/user/coins')"></div>
      <div class="feature-card card-agent" @click="$router.push('/user/agent')"></div>
    </div>

    <!-- 快捷功能 -->
    <div class="quick-menu">
      <div class="quick-item" @click="$router.push('/user/history')">
        <div class="quick-icon-img">
          <img src="/images/backgrounds/ic_history.webp" alt="观看记录" />
        </div>
        <span>观看记录</span>
      </div>
      <div class="quick-item" @click="$router.push('/user/favorites')">
        <div class="quick-icon-img">
          <img src="/images/backgrounds/ic_collect.webp" alt="我的收藏" />
        </div>
        <span>我的收藏</span>
      </div>
      <div class="quick-item" @click="$router.push('/user/purchases')">
        <div class="quick-icon-img">
          <img src="/images/backgrounds/ic_buy.webp" alt="我的购买" />
        </div>
        <span>我的购买</span>
      </div>
      <div class="quick-item" @click="showComingSoon">
        <div class="quick-icon-img">
          <img src="/images/backgrounds/ic_ai.webp" alt="AI女友" />
        </div>
        <span>AI女友</span>
      </div>
    </div>

    <!-- 图标广告位 -->
    <div class="ad-section" v-if="iconAds.length > 0">
      <div class="ad-row">
        <div 
          v-for="ad in iconAds.slice(0, 5)" 
          :key="ad.id" 
          class="ad-item"
          @click="handleAdClick(ad)"
        >
          <div class="ad-icon">
            <img v-if="ad.image" :src="ad.image" :alt="ad.name" />
            <span v-else>{{ ad.icon }}</span>
          </div>
          <span class="ad-name">{{ ad.name }}</span>
        </div>
      </div>
      <div class="ad-row-scroll-container" v-if="iconAds.length > 5">
        <div class="ad-row ad-row-scroll" ref="adRowScroll">
          <div 
            v-for="ad in [...iconAds.slice(5), ...iconAds.slice(5)]" 
            :key="`${ad.id}-${Math.random()}`" 
            class="ad-item"
            @click="handleAdClick(ad)"
          >
            <div class="ad-icon">
              <img v-if="ad.image" :src="ad.image" :alt="ad.name" />
              <span v-else>{{ ad.icon }}</span>
            </div>
            <span class="ad-name">{{ ad.name }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 菜单列表 -->
    <div class="menu-section">
      <!-- 创作中心 -->
      <div class="menu-row" @click="$router.push('/user/creator-center')">
        <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="3" width="7" height="7"/>
          <rect x="14" y="3" width="7" height="7"/>
          <rect x="14" y="14" width="7" height="7"/>
          <rect x="3" y="14" width="7" height="7"/>
        </svg>
        <span class="menu-text">创作中心</span>
        <svg class="menu-arrow" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
        </svg>
      </div>
      
      <!-- 关注/粉丝 -->
      <div class="menu-row" @click="$router.push('/user/follows')">
        <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
        </svg>
        <span class="menu-text">关注/粉丝</span>
        <svg class="menu-arrow" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
        </svg>
      </div>
      
      <!-- 账号凭证 -->
      <div class="menu-row" @click="$router.push('/user/account-credential')">
        <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
          <line x1="16" y1="2" x2="16" y2="6"/>
          <line x1="8" y1="2" x2="8" y2="6"/>
          <line x1="3" y1="10" x2="21" y2="10"/>
          <path d="M9 16l2 2 4-4"/>
        </svg>
        <span class="menu-text">账号凭证</span>
        <svg class="menu-arrow" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
        </svg>
      </div>
      
      <!-- 锁屏密码 -->
      <div class="menu-row" @click="$router.push('/user/lock')">
        <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
          <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
        </svg>
        <span class="menu-text">锁屏密码</span>
        <svg class="menu-arrow" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
        </svg>
      </div>
      
      <!-- 邀请分享 -->
      <div class="menu-row" @click="$router.push('/user/invite-share')">
        <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="18" cy="5" r="3"/>
          <circle cx="6" cy="12" r="3"/>
          <circle cx="18" cy="19" r="3"/>
          <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
          <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
        </svg>
        <span class="menu-text">邀请分享</span>
        <svg class="menu-arrow" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
        </svg>
      </div>
      
      <!-- 推广中心 -->
      <div class="menu-row promotion-entry" @click="$router.push('/user/promotion')">
        <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"/>
        </svg>
        <span class="menu-text">推广中心</span>
        <span class="menu-badge hot">赚VIP</span>
        <svg class="menu-arrow" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
        </svg>
      </div>
      
      <!-- 我的下载 -->
      <div class="menu-row" @click="$router.push('/user/downloads')">
        <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="7 10 12 15 17 10"/>
          <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
        <span class="menu-text">我的下载</span>
        <svg class="menu-arrow" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
        </svg>
      </div>
      
      <!-- 我的喜欢 -->
      <div class="menu-row" @click="$router.push('/user/likes')">
        <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
        </svg>
        <span class="menu-text">我的喜欢</span>
        <svg class="menu-arrow" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
        </svg>
      </div>
      
      <!-- 领取兑换 -->
      <div class="menu-row" @click="$router.push('/user/redeem')">
        <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 5H3a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h18a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2z"/>
          <path d="M12 12m-3 0a3 3 0 1 0 6 0a3 3 0 1 0-6 0"/>
          <path d="M3 9h2M19 9h2M3 15h2M19 15h2"/>
        </svg>
        <span class="menu-text">领取兑换</span>
        <svg class="menu-arrow" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
        </svg>
      </div>
      
      <!-- 应用推荐 -->
      <div class="menu-row" @click="$router.push('/user/app-recommend')">
        <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
        <span class="menu-text">应用推荐</span>
        <svg class="menu-arrow" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
        </svg>
      </div>
      
      <!-- 联系客服 -->
      <div class="menu-row" @click="$router.push('/user/customer-service')">
        <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 18v-6a9 9 0 0 1 18 0v6"/>
          <path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/>
        </svg>
        <span class="menu-text">联系客服</span>
        <svg class="menu-arrow" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
        </svg>
      </div>
      
      <!-- 官方群组 -->
      <div class="menu-row" @click="$router.push('/user/groups')">
        <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
          <circle cx="9" cy="7" r="4"/>
          <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>
        </svg>
        <span class="menu-text">官方群组</span>
        <svg class="menu-arrow" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
        </svg>
      </div>
      
      <!-- 检查更新 -->
      <div class="menu-row" @click="checkUpdate">
        <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="23 4 23 10 17 10"/>
          <polyline points="1 20 1 14 7 14"/>
          <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
        </svg>
        <span class="menu-text">检查更新</span>
        <svg class="menu-arrow" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
        </svg>
      </div>
    </div>
    
    <!-- 设置桌面图标 -->
    <div class="desktop-icon-section">
      <div class="section-header">
        <span class="section-title">设置桌面图标</span>
        <span class="reset-btn" @click="resetDesktopIcon">恢复默认</span>
      </div>
      <div class="icon-options">
        <div 
          v-for="icon in desktopIcons" 
          :key="icon.id" 
          :class="['icon-option', { active: selectedIcon === icon.id }]"
          @click="selectDesktopIcon(icon.id)"
        >
          <img :src="icon.image" :alt="icon.name" class="icon-img" />
          <span>{{ icon.name }}</span>
        </div>
      </div>
    </div>

    <!-- 底部导航 -->
    <BottomNav />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import api from '@/utils/api'
import { getAvatarUrl } from '@/utils/avatar'
import { formatDate } from '@/utils/format'
import { getVipLevelIcon, getVipLevelName } from '@/constants/vip'
import { useAbortController } from '@/composables/useAbortController'
import { useTimers } from '@/composables/useCleanup'
import { useAsyncLock } from '@/composables/useDebounce'
import BottomNav from '@/components/common/BottomNav.vue'

const router = useRouter()
const userStore = useUserStore()

// 请求取消控制器
const { signal } = useAbortController()

// 定时器管理
const { setInterval, clearInterval } = useTimers()

// 签到防重复
const { execute: executeSign, loading: signingIn } = useAsyncLock(async () => {
  const res = await api.post('/points/tasks/checkin', null, { signal })
  return res.data?.points || 0
})

const user = ref({
  id: '',
  username: '',
  nickname: '',
  avatar: '',
  is_vip: false,
  vip_level: 0,
  vip_level_name: '非VIP',
  vip_expire_date: null,
  cache_count: 0,
  ai_count: 0
})

// 使用统一的VIP常量（已从 @/constants/vip 导入）

const iconAds = ref([])
const isLoading = ref(true)
const unreadMessageCount = ref(0)

// 桌面图标设置
const selectedIcon = ref('icon_0')
const desktopIcons = ref([
  { id: 'icon_0', name: 'SOUL', image: '/images/app_icon/icon_0.webp' },
  { id: 'icon_1', name: '爱音乐', image: '/images/app_icon/icon_1.webp' },
  { id: 'icon_2', name: '爱阅读', image: '/images/app_icon/icon_2.webp' },
  { id: 'icon_3', name: '支付宝', image: '/images/app_icon/icon_3.webp' },
  { id: 'icon_4', name: '哔哩哔哩', image: '/images/app_icon/icon_4.webp' },
  { id: 'icon_5', name: '饼干大作战', image: '/images/app_icon/icon_5.webp' },
  { id: 'icon_6', name: '美食借鉴', image: '/images/app_icon/icon_6.webp' },
  { id: 'icon_7', name: '我的世界', image: '/images/app_icon/icon_7.webp' },
  { id: 'icon_8', name: '神选之战', image: '/images/app_icon/icon_8.webp' },
  { id: 'icon_9', name: '随心无线', image: '/images/app_icon/icon_9.webp' },
  { id: 'icon_10', name: '特轩小说', image: '/images/app_icon/icon_10.webp' },
  { id: 'icon_11', name: '天天麻将', image: '/images/app_icon/icon_11.webp' },
  { id: 'icon_12', name: '途游', image: '/images/app_icon/icon_12.webp' },
  { id: 'icon_13', name: '微信', image: '/images/app_icon/icon_13.webp' },
  { id: 'icon_14', name: '问道', image: '/images/app_icon/icon_14.webp' },
  { id: 'icon_15', name: '英语图书角', image: '/images/app_icon/icon_15.webp' }
])

const userId = computed(() => {
  return user.value.id || '加载中...'
})

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

// 根据用户ID自动分配头像 - 使用统一的工具函数
const avatarUrl = computed(() => {
  return getAvatarUrl(user.value.avatar, user.value.id)
})

// VIP等级图标 - 使用统一的常量
const vipLevelIcon = computed(() => {
  return getVipLevelIcon(user.value.vip_level)
})

// 签到处理 - 使用防重复锁
const handleSign = async () => {
  try {
    const points = await executeSign()
    if (points !== null) {
      ElMessage.success(`签到成功！获得 ${points} 积分`)
      // 刷新用户信息
      await fetchUserInfo()
    }
  } catch (error) {
    const msg = error.response?.data?.detail || ''
    // 已签到不显示错误，只显示提示
    if (msg.includes('已签到') || msg.includes('已完成')) {
      ElMessage.warning('今日已签到，请明天再来~')
    } else if (msg) {
      ElMessage.error(msg)
    }
  }
}

// VIP等级名称 - 使用统一的常量
const vipLevelName = computed(() => {
  return user.value.vip_level_name || getVipLevelName(user.value.vip_level)
})

// 格式化VIP到期时间 - 使用统一的格式化函数
const formattedExpireDate = computed(() => {
  if (!user.value.vip_expire_date) return ''
  return formatDate(user.value.vip_expire_date)
})

const copyId = () => {
  if (navigator.clipboard && user.value.username) {
    navigator.clipboard.writeText(String(user.value.username))
    ElMessage.success('账号已复制')
  }
}

const handleAdClick = (ad) => {
  if (ad.link) {
    window.open(ad.link, '_blank')
  }
}

const handleLogout = () => {
  userStore.logout()
  ElMessage.success('已退出登录')
  user.value = {}
}

// 检查更新
const checkUpdate = () => {
  ElMessage.success('当前已是最新版本 v1.0.0')
}

// 正在开发中提示
const showComingSoon = () => {
  ElMessage.info('正在开发中，敬请期待')
}

// 选择桌面图标
const selectDesktopIcon = (iconId) => {
  selectedIcon.value = iconId
  ElMessage.success('桌面图标已更换')
}

// 重置桌面图标
const resetDesktopIcon = () => {
  selectedIcon.value = 'icon_0'
  ElMessage.success('已恢复默认图标')
}

const fetchIconAds = async () => {
  try {
    const res = await axios.get('/api/v1/ads/icons')
    iconAds.value = (res.data || []).filter(ad => ad.is_active !== false)
  } catch (error) {
    console.log('获取图标广告失败')
  }
}

// 获取未读消息数量
const fetchUnreadCount = async () => {
  try {
    const res = await api.get('/notifications/unread-count')
    unreadMessageCount.value = res.data?.total || 0
  } catch (error) {
    console.log('获取未读消息数量失败')
  }
}

// 获取用户VIP信息
const fetchUserVipInfo = async () => {
  if (!user.value.id) {
    console.log('用户ID为空，跳过获取VIP信息')
    return
  }
  try {
    console.log('开始获取VIP信息，用户ID:', user.value.id)
    const res = await api.get('/users/me')
    console.log('API响应:', res)
    const data = res.data || res
    console.log('解析后数据:', data)
    if (data) {
      user.value.is_vip = data.is_vip || false
      user.value.vip_level = data.vip_level || 0
      user.value.vip_level_name = data.vip_level_name || '非VIP'
      user.value.vip_expire_date = data.vip_expire_date || null
      console.log('VIP状态:', user.value.is_vip, '等级:', user.value.vip_level, '名称:', user.value.vip_level_name, '到期:', data.vip_expire_date)
    }
  } catch (error) {
    console.error('获取用户VIP信息失败:', error)
  }
}

// 广告滚动ref
const adRowScroll = ref(null)
let scrollInterval = null

// 加载用户数据
const loadUserData = () => {
  if (userStore.isLoggedIn && userStore.user) {
    user.value = {
      id: userStore.user.id || '',
      username: userStore.user.username || '',
      nickname: userStore.user.nickname || userStore.user.username || '',
      avatar: userStore.user.avatar || '',
      is_vip: userStore.user.is_vip || false,
      vip_level: userStore.user.vip_level || 0,
      vip_level_name: userStore.user.vip_level_name || '非VIP',
      vip_expire_date: userStore.user.vip_expire_date || null,
      cache_count: 0,
      ai_count: 0
    }
    isLoading.value = false
    // 后台静默获取最新VIP信息
    fetchUserVipInfo()
    return true
  }
  return false
}

onMounted(async () => {
  // 如果已经有用户数据，直接加载
  if (loadUserData()) {
    // 用户数据已加载
  } else if (!userStore.isInitialized) {
    // 等待初始化完成（游客注册）
    const unwatch = watch(() => userStore.isInitialized, (initialized) => {
      if (initialized) {
        loadUserData()
        if (!userStore.isLoggedIn) {
          isLoading.value = false
        }
        unwatch()
      }
    }, { immediate: true })
    
    // 设置超时，避免无限等待
    setTimeout(() => {
      if (isLoading.value) {
        isLoading.value = false
      }
    }, 5000)
  } else {
    isLoading.value = false
  }
  fetchIconAds()
  fetchUnreadCount()
})

// 监听广告数据变化，启动自动滚动
watch(iconAds, (newAds) => {
  if (newAds.length > 5) {
    nextTick(() => {
      setTimeout(() => {
        if (adRowScroll.value) {
          startAutoScroll()
        }
      }, 500)
    })
  }
}, { once: true })

onUnmounted(() => {
  if (scrollInterval) {
    clearInterval(scrollInterval)
  }
})

const startAutoScroll = () => {
  const scrollElement = adRowScroll.value
  if (!scrollElement) return
  
  let scrollPosition = 0
  const scrollSpeed = 0.5 // 每帧滚动的像素数
  
  scrollInterval = setInterval(() => {
    scrollPosition += scrollSpeed
    scrollElement.scrollLeft = scrollPosition
    
    // 当滚动到一半时重置（因为内容是重复的）
    if (scrollPosition >= scrollElement.scrollWidth / 2) {
      scrollPosition = 0
      scrollElement.scrollLeft = 0
    }
  }, 20)
}
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
$breakpoint-2k: 1920px;
$breakpoint-4k: 2560px;

.profile-page {
  min-height: 100vh;
  min-height: 100dvh;
  background: #0d0d0d;
  color: #fff;
  padding-bottom: calc(65px + env(safe-area-inset-bottom, 0px));
  padding-left: env(safe-area-inset-left, 0px);
  padding-right: env(safe-area-inset-right, 0px);
  width: 100%;
  max-width: 100vw;
  margin: 0 auto;
  position: relative;
  
  @media (min-width: $breakpoint-lg) {
    max-width: 750px;
  }
  
  @media (min-width: $breakpoint-xl) {
    max-width: 900px;
  }
  
  @media (min-width: $breakpoint-xxl) {
    max-width: 1200px;
  }
  
  @media (min-width: $breakpoint-2k) {
    max-width: 1400px;
  }
  
  @media (min-width: $breakpoint-4k) {
    max-width: 1800px;
  }
}

// 顶部背景图
.profile-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 220px;
  overflow: hidden;
  z-index: 0;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    filter: brightness(0.5);
  }
  
  .bg-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
      to bottom,
      rgba(13, 13, 13, 0.3) 0%,
      rgba(13, 13, 13, 0.5) 50%,
      rgba(13, 13, 13, 0.9) 85%,
      rgba(13, 13, 13, 1) 100%
    );
  }
}

// 顶部栏
.page-header {
  position: relative;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: clamp(12px, 4vw, 20px) clamp(14px, 5vw, 24px);
  padding-top: calc(clamp(12px, 4vw, 20px) + env(safe-area-inset-top, 0px));
  
  .header-left, .header-right {
    display: flex;
    align-items: center;
    gap: clamp(14px, 4vw, 20px);
  }
  
  .header-icon {
    width: clamp(20px, 6vw, 28px);
    height: clamp(20px, 6vw, 28px);
    color: rgba(255, 255, 255, 0.85);
    cursor: pointer;
    transition: transform 0.2s;
    
    &:hover {
      transform: scale(1.1);
    }
  }
  
  .header-icon-img {
    width: clamp(22px, 6vw, 28px);
    height: clamp(22px, 6vw, 28px);
    object-fit: contain;
    cursor: pointer;
    transition: transform 0.2s;
    
    &:hover {
      transform: scale(1.1);
    }
  }
  
  .notification-wrapper {
    position: relative;
    display: inline-flex;
    cursor: pointer;
    
    .notification-badge {
      position: absolute;
      top: -6px;
      right: -8px;
      min-width: 18px;
      height: 18px;
      padding: 0 5px;
      background: #ff4757;
      color: #fff;
      font-size: 11px;
      font-weight: 600;
      border-radius: 9px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 2px 6px rgba(255, 71, 87, 0.4);
    }
  }
}

// 用户信息
.user-section {
  position: relative;
  z-index: 10;
  padding: 0 clamp(14px, 5vw, 24px) clamp(4px, 1vw, 8px);
  
  .user-row {
    display: flex;
    align-items: flex-start;
    gap: clamp(10px, 3.5vw, 18px);
    margin-bottom: clamp(10px, 3vw, 16px);
  }
  
  // 头像包装器（包含头像和VIP图标）
  .avatar-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: clamp(4px, 1.5vw, 8px);
    
    .vip-level-badge {
      height: clamp(20px, 6vw, 28px);
      width: auto;
      max-width: clamp(60px, 18vw, 80px);
      object-fit: contain;
      animation: vip-badge-glow 2s ease-in-out infinite;
    }
  }
  
  .avatar-container {
    position: relative;
    
    .avatar-frame {
      width: clamp(58px, 18vw, 80px);
      height: clamp(58px, 18vw, 80px);
      border-radius: 50%;
      padding: 2px;
      background: rgba(255, 255, 255, 0.1);
      
      .user-avatar {
        width: 100%;
        height: 100%;
        border-radius: 50%;
        object-fit: cover;
        background: #1a1a1a;
      }
    }
    
    // VIP金色边框效果
    &.is-vip {
      .avatar-frame {
        padding: 3px;
        background: linear-gradient(135deg, #ffd700 0%, #ffec8b 25%, #daa520 50%, #ffd700 75%, #ffec8b 100%);
        background-size: 200% 200%;
        animation: vip-border-shine 3s ease-in-out infinite;
        box-shadow: 
          0 0 10px rgba(255, 215, 0, 0.4),
          0 0 20px rgba(255, 215, 0, 0.2);
      }
    }
    
    // VIP皇冠徽章
    .vip-crown {
      position: absolute;
      top: -6px;
      right: -4px;
      width: clamp(20px, 6vw, 28px);
      height: clamp(20px, 6vw, 28px);
      background: linear-gradient(135deg, #ffd700, #ffec8b);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 2px 8px rgba(255, 215, 0, 0.5);
      animation: crown-bounce 2s ease-in-out infinite;
      
      svg {
        width: clamp(14px, 4vw, 18px);
        height: clamp(14px, 4vw, 18px);
        fill: #8b4513;
      }
    }
    
    .gender-icon {
      position: absolute;
      bottom: -2px;
      left: -2px;
      width: clamp(18px, 5.5vw, 24px);
      height: clamp(18px, 5.5vw, 24px);
      background: #4a90d9;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: clamp(12px, 3.5vw, 16px);
      border: 2px solid #0d0d0d;
    }
  }
  
  .sign-btn {
    &.disabled {
      opacity: 0.6;
      pointer-events: none;
    }
    
    .sign-icon-img {
      width: clamp(18px, 5vw, 24px);
      height: clamp(18px, 5vw, 24px);
      object-fit: contain;
    }
  }
  
  .user-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-height: clamp(58px, 18vw, 80px);
    
    .nickname-row {
      display: flex;
      align-items: center;
      justify-content: flex-start;
      gap: clamp(6px, 2vw, 10px);
      margin-bottom: clamp(6px, 2vw, 10px);
      
      .vip-level-badge-inline {
        height: clamp(18px, 5vw, 24px);
        width: auto;
        max-width: clamp(50px, 15vw, 70px);
        object-fit: contain;
        animation: vip-badge-glow 2s ease-in-out infinite;
        flex-shrink: 0;
      }
    }
    
    .nickname {
      font-size: clamp(14px, 4vw, 18px);
      font-weight: 600;
      margin: 0;
      line-height: 1.5;
      letter-spacing: -0.8px;
      background: linear-gradient(135deg, #ffd700 0%, #ffec8b 30%, #daa520 60%, #ffd700 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    
    .user-id-row {
      display: flex;
      align-items: center;
      gap: clamp(4px, 1.5vw, 8px);
      
      .user-id {
        font-size: clamp(14px, 3.5vw, 14px);
        color: rgba(255, 255, 255, 0.45);
        letter-spacing: 0.5px;
        
        &::before {
          content: '账号: ';
          color: rgba(255, 255, 255, 0.35);
        }
      }
      
      .copy-btn {
        width: clamp(12px, 3.5vw, 16px);
        height: clamp(12px, 3.5vw, 16px);
        color: rgba(255, 255, 255, 0.35);
        cursor: pointer;
        transition: color 0.2s;
        
        &:hover {
          color: rgba(255, 255, 255, 0.7);
        }
        
        &:active {
          transform: scale(0.9);
        }
      }
    }
  }
  
  .sign-btn {
    display: flex;
    align-items: center;
    gap: clamp(4px, 1.5vw, 8px);
    padding: clamp(8px, 2.5vw, 12px) clamp(12px, 4vw, 18px);
    background: rgba(255, 255, 255, 0.08);
    border-radius: clamp(6px, 2vw, 10px);
    cursor: pointer;
    font-size: clamp(12px, 3.5vw, 15px);
    transition: background 0.2s;
    
    &:hover {
      background: rgba(255, 255, 255, 0.12);
    }
    
    &.disabled {
      opacity: 0.6;
      pointer-events: none;
    }
    
    .sign-icon {
      width: clamp(16px, 4.5vw, 20px);
      height: clamp(16px, 4.5vw, 20px);
      color: rgba(255, 255, 255, 0.8);
    }
    
    .sign-icon-img {
      width: clamp(18px, 5vw, 24px);
      height: clamp(18px, 5vw, 24px);
      object-fit: contain;
  }
}

  // 统计行
  .stats-row {
  display: flex;
  justify-content: center;
  gap: clamp(40px, 15vw, 80px);
    padding: clamp(2px, 0.5vw, 4px) 0;
  
  .stat-box {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: clamp(1px, 0.3vw, 2px);
    
    .stat-num {
      font-size: clamp(22px, 7vw, 32px);
      font-weight: 600;
        background: linear-gradient(180deg, #fff 0%, rgba(255,255,255,0.8) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .stat-text {
      font-size: clamp(11px, 3vw, 13px);
        color: rgba(255, 255, 255, 0.6);
      }
    }
  }
}

// VIP横幅
.vip-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: clamp(6px, 2vw, 10px) clamp(12px, 4vw, 20px);
  padding: clamp(12px, 3.5vw, 16px) clamp(12px, 4vw, 20px);
  min-height: clamp(60px, 18vw, 80px);
  background-image: url("/images/backgrounds/vipbg.webp");
  background-size: 100% 100%;
  background-position: center;
  background-repeat: no-repeat;
  border-radius: clamp(10px, 3.5vw, 16px);
  cursor: pointer;
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 
    0 0 15px rgba(255, 255, 255, 0.15),
    0 0 30px rgba(255, 255, 255, 0.1),
    0 8px 20px rgba(0, 0, 0, 0.3),
    0 4px 8px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.2),
    inset 0 0 20px rgba(255, 255, 255, 0.05);
  transform: perspective(1000px) rotateX(2deg);
  transform-style: preserve-3d;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  
  &:hover {
    transform: perspective(1000px) rotateX(0deg) translateY(-2px);
    box-shadow: 
      0 0 20px rgba(255, 255, 255, 0.2),
      0 0 40px rgba(255, 255, 255, 0.15),
      0 12px 30px rgba(0, 0, 0, 0.35),
      0 6px 12px rgba(0, 0, 0, 0.25),
      inset 0 1px 0 rgba(255, 255, 255, 0.25),
      inset 0 -1px 0 rgba(255, 255, 255, 0.08);
  }
  
  &:active {
    transform: perspective(1000px) rotateX(1deg) translateY(0);
  }
  
  // 星星装饰
  .vip-stars {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
    
    .star {
      position: absolute;
      color: rgba(255, 200, 150, 0.7);
      animation: star-twinkle 2s ease-in-out infinite;
      
      &.s1 { top: 12%; right: 12%; font-size: clamp(8px, 2.5vw, 12px); animation-delay: 0s; }
      &.s2 { top: 50%; right: 8%; font-size: clamp(6px, 2vw, 10px); animation-delay: 0.5s; }
      &.s3 { top: 70%; right: 15%; font-size: clamp(10px, 3vw, 14px); animation-delay: 1s; }
      &.s4 { top: 30%; right: 5%; font-size: clamp(5px, 1.5vw, 8px); animation-delay: 1.5s; }
    }
  }
  
  .vip-left {
    display: flex;
    align-items: center;
    position: relative;
    z-index: 1;
    margin-left: 15%;
    
    .vip-text {
      font-size: clamp(10px, 3vw, 13px);
      font-weight: 600;
      display: flex;
      gap: clamp(3px, 1vw, 5px);
      
      .text-gradient {
        background: linear-gradient(135deg, #ffd700 0%, #ffec8b 50%, #daa520 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }
      
      .text-gradient-light {
        background: linear-gradient(135deg, #ffe066 0%, #ffd700 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }
    }
  }
  
  .vip-btn {
    display: flex;
    align-items: center;
    gap: clamp(3px, 1vw, 5px);
    padding: clamp(5px, 1.5vw, 8px) clamp(10px, 3vw, 14px) clamp(5px, 1.5vw, 8px) clamp(12px, 3.5vw, 16px);
    background: linear-gradient(135deg, #ffd700 0%, #f0c14b 50%, #daa520 100%);
    border-radius: clamp(16px, 5vw, 24px);
    font-size: clamp(11px, 3vw, 14px);
    color: #3d2a1a;
    font-weight: 600;
    position: relative;
    z-index: 1;
    box-shadow: 0 2px 8px rgba(255, 215, 0, 0.3);
    
    
    .arrow-circle {
      width: clamp(14px, 4vw, 18px);
      height: clamp(14px, 4vw, 18px);
      background: rgba(61, 42, 26, 0.15);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      
      svg {
        width: clamp(8px, 2.5vw, 12px);
        height: clamp(8px, 2.5vw, 12px);
        fill: #5a4a3a;
      }
    }
  }
  
  // 已是会员的信息展示 - 垂直布局
  .vip-member-content {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: clamp(4px, 1.5vw, 6px);
    
    .vip-icon-inline {
      height: clamp(22px, 6vw, 30px);
      width: auto;
      object-fit: contain;
      filter: drop-shadow(0 1px 3px rgba(0, 0, 0, 0.3));
    }
    
    .vip-expire-inline {
      font-size: clamp(11px, 3vw, 13px);
      background: linear-gradient(135deg, #ffd700 0%, #ffec8b 50%, #daa520 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      white-space: nowrap;
      font-weight: 600;
    }
  }
}

@keyframes star-twinkle {
  0%, 100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  50% {
    opacity: 1;
    transform: scale(1.2);
  }
}

@keyframes vip-border-shine {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

@keyframes crown-bounce {
  0%, 100% {
    transform: translateY(0) rotate(-5deg);
  }
  50% {
    transform: translateY(-3px) rotate(5deg);
  }
}

@keyframes crown-glow {
  0%, 100% {
    filter: drop-shadow(0 2px 8px rgba(255, 215, 0, 0.5));
  }
  50% {
    filter: drop-shadow(0 2px 12px rgba(255, 215, 0, 0.8));
  }
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

// 三卡片入口
.card-grid {
  display: flex;
  gap: clamp(6px, 2vw, 12px);
  padding: 0 clamp(12px, 4vw, 20px);
  margin-bottom: clamp(6px, 2vw, 10px);
  
  .feature-card {
    flex: 1;
    aspect-ratio: 16 / 9;
    border-radius: clamp(6px, 2vw, 10px);
    overflow: hidden;
    cursor: pointer;
    background-size: 100% 90%;
    background-position: center;
    background-repeat: no-repeat;
    transition: transform 0.2s, box-shadow 0.2s;
    
    &:hover {
      transform: translateY(-2px);
    }
    
    &:active {
      transform: scale(0.98);
    }
    
    &.card-vip {
      background-image: url("/images/backgrounds/vip_center.webp");
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    
    &.card-wallet {
      background-image: url("/images/backgrounds/my_wallet.webp");
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    
    &.card-agent {
      background-image: url("/images/backgrounds/agent.webp");
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
  }
}

// 快捷功能
.quick-menu {
  display: flex;
  justify-content: space-between;
  padding: clamp(8px, 2.5vw, 14px) clamp(14px, 5vw, 24px);
  margin: 0 clamp(12px, 4vw, 20px) clamp(6px, 2vw, 10px);
  background: rgba(255, 255, 255, 0.03);
  border-radius: clamp(10px, 3.5vw, 16px);
  
  .quick-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: clamp(6px, 2vw, 10px);
    cursor: pointer;
    transition: transform 0.2s;
    
    &:hover {
      transform: scale(1.05);
    }
    
    .quick-icon-img {
      width: clamp(36px, 11vw, 50px);
      height: clamp(36px, 11vw, 50px);
      border-radius: clamp(8px, 3vw, 14px);
      overflow: hidden;
      
      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
    }
    
    span {
      font-size: clamp(12px, 3vw, 13px);
      color: rgba(255, 255, 255, 0.85);
    }
    
    .quick-text {
      font-size: clamp(12px, 3vw, 13px);
      color: rgba(255, 255, 255, 0.85);
    }
  }
}

// 广告区
.ad-section {
  padding: 0 clamp(12px, 4vw, 20px);
  margin-bottom: clamp(12px, 4vw, 18px);
  
  .ad-row {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: clamp(1px, 0.5vw, 2px);
    margin-bottom: clamp(8px, 2.5vw, 12px);
    
    @media (min-width: $breakpoint-md) {
      grid-template-columns: repeat(6, 1fr);
    }
    
    @media (min-width: $breakpoint-lg) {
      grid-template-columns: repeat(7, 1fr);
    }
  }
  
  .ad-row-scroll-container {
    overflow: hidden;
    margin-bottom: clamp(10px, 3.5vw, 16px);
    width: 100%;
  }
  
  .ad-row-scroll {
    display: flex;
    gap: clamp(2px, 0.5vw, 4px);
    overflow-x: scroll;
    scrollbar-width: none;
    -ms-overflow-style: none;
    
    &::-webkit-scrollbar {
      display: none;
    }
    
    .ad-item {
      flex-shrink: 0;
      width: clamp(60px, 18vw, 80px);
    }
  }
  
  .ad-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: clamp(4px, 1.5vw, 6px);
    cursor: pointer;
    transition: transform 0.2s;
    
    &:hover {
      transform: scale(1.05);
    }
    
    .ad-icon {
      width: clamp(56px, 16vw, 75px);
      height: clamp(56px, 16vw, 75px);
      border-radius: clamp(10px, 3.5vw, 16px);
      overflow: hidden;
      background: #1a1a1a;
      display: flex;
      align-items: center;
      justify-content: center;
      
      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
      
      span {
        font-size: clamp(22px, 7vw, 32px);
      }
    }
    
    .ad-name {
      font-size: clamp(10px, 3vw, 12px);
      color: rgba(255, 255, 255, 0.7);
      text-align: center;
      max-width: clamp(48px, 14vw, 68px);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
}

// 菜单
.menu-section {
  margin: 0 clamp(12px, 4vw, 20px);
  background: rgba(255, 255, 255, 0.03);
  border-radius: clamp(10px, 3.5vw, 16px);
  overflow: hidden;
  
  .menu-row {
    display: flex;
    align-items: center;
    padding: clamp(12px, 4vw, 18px) clamp(14px, 4.5vw, 20px);
    cursor: pointer;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    transition: background 0.2s;
    
    &:hover {
      background: rgba(255, 255, 255, 0.03);
    }
    
    &:last-child {
      border-bottom: none;
    }
    
    .menu-icon {
      width: clamp(18px, 5.5vw, 24px);
      height: clamp(18px, 5.5vw, 24px);
      color: rgba(255, 255, 255, 0.55);
      margin-right: clamp(10px, 3.5vw, 16px);
    }
    
    .menu-text {
      flex: 1;
      font-size: clamp(14px, 3.5vw, 14px);
      color: rgba(255, 255, 255, 0.85);
    }
    
    .menu-arrow {
      width: clamp(16px, 5vw, 22px);
      height: clamp(16px, 5vw, 22px);
      color: rgba(255, 255, 255, 0.25);
    }
    
    .menu-badge {
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 10px;
      margin-right: 8px;
      
      &.hot {
        background: linear-gradient(135deg, #f97316, #ea580c);
        color: #fff;
      }
    }
    
    &.logout {
      justify-content: center;
      color: #ef4444;
      margin-top: clamp(6px, 2vw, 10px);
      border-top: 1px solid rgba(255, 255, 255, 0.04);
      
      .menu-text {
        flex: none;
      }
    }
  }
}

// 设置桌面图标
.desktop-icon-section {
  margin: clamp(12px, 4vw, 20px);
  margin-bottom: 10px;
  
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: clamp(12px, 4vw, 16px);
    
    .section-title {
      font-size: clamp(13px, 4vw, 15px);
      color: rgba(255, 255, 255, 0.6);
    }
    
    .reset-btn {
      font-size: clamp(14px, 3.5vw, 14px);
      color: rgba(255, 255, 255, 0.4);
      cursor: pointer;
      transition: color 0.2s;
      
      &:hover {
        color: rgba(255, 255, 255, 0.7);
      }
    }
  }
  
  .icon-options {
    display: flex;
    gap: clamp(12px, 4vw, 20px);
    overflow-x: auto;
    padding-bottom: 8px;
    
    &::-webkit-scrollbar {
      height: 4px;
    }
    
    &::-webkit-scrollbar-thumb {
      background: rgba(255, 255, 255, 0.1);
      border-radius: 2px;
    }
    
    .icon-option {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: clamp(6px, 2vw, 10px);
      cursor: pointer;
      flex-shrink: 0;
      transition: transform 0.2s, opacity 0.2s;
      
      .icon-img {
        width: clamp(48px, 14vw, 60px);
        height: clamp(48px, 14vw, 60px);
        border-radius: clamp(10px, 3vw, 14px);
        object-fit: cover;
        border: 2px solid transparent;
        transition: border-color 0.2s, box-shadow 0.2s;
      }
      
      > span {
        font-size: clamp(11px, 3vw, 13px);
        color: rgba(255, 255, 255, 0.6);
        transition: color 0.2s;
      }
      
      &:hover {
        transform: translateY(-2px);
        
        .icon-img {
          border-color: rgba(138, 99, 210, 0.5);
        }
        
        > span {
          color: rgba(255, 255, 255, 0.9);
        }
      }
      
      &.active {
        .icon-img {
          border-color: #8a63d2;
          box-shadow: 0 0 12px rgba(138, 99, 210, 0.5);
        }
        
        > span {
          color: #8a63d2;
        }
      }
    }
  }
}

// ============ 超大屏幕优化 ============
@media (min-width: $breakpoint-2k) {
  .profile-page {
    font-size: 18px;
  }
  
  .user-info .username {
    font-size: 22px;
  }
  
  .stat-value {
    font-size: 22px;
  }
  
  .section-title {
    font-size: 20px;
  }
}

@media (min-width: $breakpoint-4k) {
  .profile-page {
    font-size: 20px;
  }
  
  .user-info .username {
    font-size: 26px;
  }
  
  .stat-value {
    font-size: 26px;
  }
  
  .section-title {
    font-size: 24px;
  }
}

// ============ 触摸设备优化 ============
@media (hover: none) and (pointer: coarse) {
  .menu-item:hover,
  .stat-item:hover,
  .quick-action:hover {
    background: transparent !important;
    transform: none !important;
  }
  
  .menu-item:active,
  .stat-item:active,
  .quick-action:active {
    opacity: 0.7;
    transform: scale(0.98);
  }
}

// 横屏模式优化
@media (orientation: landscape) and (max-height: 500px) {
  .page-header {
    padding: 8px 16px;
  }
  
  .user-section {
    padding: 0 16px 12px;
    
    .user-row {
      margin-bottom: 12px;
    }
    
    .avatar-container .avatar-frame {
      width: 50px;
      height: 50px;
    }
  }
  
  .stats-section {
    gap: 40px;
    
    .stat-box .stat-num {
      font-size: 20px;
    }
  }
  
  .vip-banner {
    margin: 8px 12px;
    padding: 10px 12px;
  }
  
  .card-grid {
    margin-bottom: 10px;
  }
  
  .quick-menu {
    padding: 10px 14px;
    margin: 0 12px 10px;
    
    .quick-item .quick-icon-img {
      width: 32px;
      height: 32px;
    }
  }
}
</style>
