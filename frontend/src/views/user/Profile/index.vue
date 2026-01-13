<template>
  <div class="profile-page">
    <div class="profile-bg">
      <img src="/images/backgrounds/profile_bg.webp" alt="" />
      <div class="bg-overlay"></div>
    </div>

    <UserHeader :unread-count="unreadMessageCount" />
    <UserInfo :user="user" :avatar-url="avatarUrl" :vip-level-icon="vipLevelIcon" :vip-level-name="vipLevelName" :loading="isLoading" :signing-in="signingIn" @copy="copyId" @sign="handleSign" />
    <VipBanner :is-vip="user.is_vip" :vip-level="user.vip_level" :vip-level-icon="vipLevelIcon" :vip-level-name="vipLevelName" :expire-date="formattedExpireDate" />

    <div class="card-grid">
      <div class="feature-card card-vip" @click="$router.push('/user/vip')"></div>
      <div class="feature-card card-wallet" @click="$router.push('/user/coins')"></div>
      <div class="feature-card card-agent" @click="$router.push('/user/agent')"></div>
    </div>

    <QuickMenu @coming-soon="showComingSoon" />

    <div class="ad-section" v-if="iconAds.length > 0">
      <div class="ad-row">
        <div v-for="ad in iconAds.slice(0, 5)" :key="ad.id" class="ad-item" @click="handleAdClick(ad)">
          <div class="ad-icon"><img v-if="ad.image" :src="ad.image" :alt="ad.name" /><span v-else>{{ ad.icon }}</span></div>
          <span class="ad-name">{{ ad.name }}</span>
        </div>
      </div>
    </div>

    <MenuList @check-update="checkUpdate" />

    <div class="desktop-icon-section">
      <div class="section-header">
        <span class="section-title">设置桌面图标</span>
        <span class="reset-btn" @click="resetDesktopIcon">恢复默认</span>
      </div>
      <div class="icon-options">
        <div v-for="icon in desktopIcons" :key="icon.id" :class="['icon-option', { active: selectedIcon === icon.id }]" @click="selectDesktopIcon(icon.id)">
          <img :src="icon.image" :alt="icon.name" class="icon-img" />
          <span>{{ icon.name }}</span>
        </div>
      </div>
    </div>

    <BottomNav />
  </div>
</template>

<script setup>
defineOptions({ name: 'UserProfile' })

import { ref, onMounted, onActivated, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import api from '@/utils/api'
import { useAbortController } from '@/composables/useAbortController'
import { useAsyncLock } from '@/composables/useDebounce'
import BottomNav from '@/components/common/BottomNav.vue'
import UserHeader from './components/UserHeader.vue'
import UserInfo from './components/UserInfo.vue'
import VipBanner from './components/VipBanner.vue'
import QuickMenu from './components/QuickMenu.vue'
import MenuList from './components/MenuList.vue'
import { useProfileData } from './composables/useProfileData'

const userStore = useUserStore()
const { signal } = useAbortController()

// 是否已初始化
const hasInitialized = ref(false)

// 签到防重复
const { execute: executeSign, loading: signingIn } = useAsyncLock(async () => {
  const res = await api.post('/points/tasks/checkin', null, { signal })
  return res.data?.points || 0
})

// 使用composables
const { user, iconAds, isLoading, unreadMessageCount, avatarUrl, vipLevelIcon, vipLevelName, formattedExpireDate, initUserData, fetchUserVipInfo, fetchIconAds, fetchUnreadCount } = useProfileData(signal)

// 桌面图标
const selectedIcon = ref('icon_0')
const desktopIcons = ref([
  { id: 'icon_0', name: 'SOUL', image: '/images/app_icon/icon_0.webp' },
  { id: 'icon_1', name: '爱音乐', image: '/images/app_icon/icon_1.webp' },
  { id: 'icon_2', name: '爱阅读', image: '/images/app_icon/icon_2.webp' },
  { id: 'icon_3', name: '支付宝', image: '/images/app_icon/icon_3.webp' },
  { id: 'icon_4', name: '哔哩哔哩', image: '/images/app_icon/icon_4.webp' },
  { id: 'icon_5', name: '饼干大作战', image: '/images/app_icon/icon_5.webp' },
  { id: 'icon_6', name: '美食借鉴', image: '/images/app_icon/icon_6.webp' },
  { id: 'icon_7', name: '我的世界', image: '/images/app_icon/icon_7.webp' }
])

const copyId = () => {
  if (navigator.clipboard && user.value.username) {
    navigator.clipboard.writeText(String(user.value.username))
    ElMessage.success('账号已复制')
  }
}

const handleSign = async () => {
  try {
    const points = await executeSign()
    if (points !== null) {
      ElMessage.success(`签到成功！获得 ${points} 积分`)
      fetchUserVipInfo()
    }
  } catch (error) {
    const msg = error.response?.data?.detail || ''
    if (msg.includes('已签到') || msg.includes('已完成')) {
      ElMessage.warning('今日已签到，请明天再来~')
    } else if (msg) {
      ElMessage.error(msg)
    }
  }
}

const handleAdClick = (ad) => { if (ad.link) window.open(ad.link, '_blank') }
const checkUpdate = () => { ElMessage.success('当前已是最新版本 v1.0.0') }
const showComingSoon = () => { ElMessage.info('正在开发中，敬请期待') }
const selectDesktopIcon = (iconId) => { selectedIcon.value = iconId; ElMessage.success('桌面图标已更换') }
const resetDesktopIcon = () => { selectedIcon.value = 'icon_0'; ElMessage.success('已恢复默认图标') }

// 初始化数据
const initData = async () => {
  if (hasInitialized.value) return
  hasInitialized.value = true
  
  // 并行加载所有数据，提升加载速度
  const promises = [fetchIconAds(), fetchUnreadCount()]
  
  if (userStore.isLoggedIn && userStore.user) {
    initUserData(userStore.user)
    promises.push(fetchUserVipInfo())
  } else {
    isLoading.value = false
  }
  
  // 等待所有请求完成
  await Promise.allSettled(promises)
}

onMounted(() => {
  initData()
})

// keep-alive 激活时滚动到顶部，只刷新未读消息数
onActivated(async () => {
  await nextTick()
  // 多种方式确保滚动到顶部
  window.scrollTo({ top: 0, left: 0, behavior: 'instant' })
  document.documentElement.scrollTop = 0
  document.body.scrollTop = 0
  
  if (hasInitialized.value) {
    // 只刷新未读消息数，不重新加载全部数据
    fetchUnreadCount()
  }
})
</script>

<style lang="scss" scoped>
.profile-page {
  min-height: 100vh;
  min-height: 100dvh;
  background: #0d0d0d;
  color: #fff;
  padding-bottom: calc(65px + env(safe-area-inset-bottom, 0px));
  width: 100%;
  max-width: 100vw;
  margin: 0 auto;
  position: relative;

  @media (min-width: 768px) { max-width: 750px; }
  @media (min-width: 1024px) { max-width: 900px; }
}

.profile-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 220px;
  overflow: hidden;
  z-index: 0;

  img { width: 100%; height: 100%; object-fit: cover; filter: brightness(0.5); }

  .bg-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(to bottom, rgba(13, 13, 13, 0.3) 0%, rgba(13, 13, 13, 0.5) 50%, rgba(13, 13, 13, 0.9) 85%, rgba(13, 13, 13, 1) 100%);
  }
}

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
    &:hover { transform: translateY(-2px); }
    &:active { transform: scale(0.98); }
    &.card-vip { background-image: url("/images/backgrounds/vip_center.webp"); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); }
    &.card-wallet { background-image: url("/images/backgrounds/my_wallet.webp"); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); }
    &.card-agent { background-image: url("/images/backgrounds/agent.webp"); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); }
  }
}

.ad-section {
  padding: 0 clamp(12px, 4vw, 20px);
  margin-bottom: clamp(12px, 4vw, 18px);

  .ad-row {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: clamp(1px, 0.5vw, 2px);
    margin-bottom: clamp(8px, 2.5vw, 12px);
  }

  .ad-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: clamp(4px, 1.5vw, 6px);
    cursor: pointer;
    transition: transform 0.2s;
    &:hover { transform: scale(1.05); }

    .ad-icon {
      width: clamp(56px, 16vw, 75px);
      height: clamp(56px, 16vw, 75px);
      border-radius: clamp(10px, 3.5vw, 16px);
      overflow: hidden;
      background: #1a1a1a;
      display: flex;
      align-items: center;
      justify-content: center;

      img { width: 100%; height: 100%; object-fit: cover; }
      span { font-size: clamp(22px, 7vw, 32px); }
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

.desktop-icon-section {
  margin: clamp(12px, 4vw, 20px);
  margin-bottom: 10px;

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: clamp(12px, 4vw, 16px);

    .section-title { font-size: clamp(13px, 4vw, 15px); color: rgba(255, 255, 255, 0.6); }
    .reset-btn { font-size: clamp(14px, 3.5vw, 14px); color: rgba(255, 255, 255, 0.4); cursor: pointer; transition: color 0.2s; &:hover { color: rgba(255, 255, 255, 0.7); } }
  }

  .icon-options {
    display: flex;
    gap: clamp(12px, 4vw, 20px);
    overflow-x: auto;
    padding-bottom: 8px;
    &::-webkit-scrollbar { height: 4px; }
    &::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 2px; }

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

      > span { font-size: clamp(11px, 3vw, 13px); color: rgba(255, 255, 255, 0.6); transition: color 0.2s; }
      &:hover { transform: translateY(-2px); .icon-img { border-color: rgba(138, 99, 210, 0.5); } > span { color: rgba(255, 255, 255, 0.9); } }
      &.active { .icon-img { border-color: #8a63d2; box-shadow: 0 0 12px rgba(138, 99, 210, 0.5); } > span { color: #8a63d2; } }
    }
  }
}
</style>
