<template>
  <div class="dating-page" ref="scrollContainer">
    <!-- 主标签导航 -->
    <div class="main-tabs">
      <div 
        :class="['tab-item', { active: activeMainTab === 'soul' }]"
        @click="activeMainTab = 'soul'"
      >
        <img v-if="activeMainTab === 'soul'" src="/images/backgrounds/dating_group_card.webp" class="tab-icon-img active-img" />
        <span v-else>SOUL群</span>
      </div>
      <div 
        :class="['tab-item', { active: activeMainTab === 'chat' }]"
        @click="activeMainTab = 'chat'"
      >
        <img v-if="activeMainTab === 'chat'" src="/images/backgrounds/dating_user_card.webp" class="tab-icon-img active-img" />
        <span v-else>裸聊</span>
      </div>
      <div 
        :class="['tab-item', { active: activeMainTab === 'live' }]"
        @click="activeMainTab = 'live'"
      >
        <img v-if="activeMainTab === 'live'" src="/images/backgrounds/dating_banner.webp" class="tab-icon-img active-img" />
        <span v-else>直播</span>
      </div>
      <div 
        :class="['tab-item', { active: activeMainTab === 'ai' }]"
        @click="activeMainTab = 'ai'"
      >
        <img v-if="activeMainTab === 'ai'" src="/images/backgrounds/dating_ai_tab.webp" class="tab-icon-img active-img" />
        <span v-else>AI广场</span>
      </div>
    </div>

    <!-- 内容区域 -->
    <div class="content-area">
      <!-- 图标广告 - 只在有API数据时显示 -->
      <IconAdsGrid v-if="activeMainTab !== 'live' && adRow1.length > 0" :row1="adRow1" :row2="adRow2" />

      <!-- SOUL群内容 - 只在有数据时显示 -->
      <template v-if="activeMainTab === 'soul' && groupList.length > 0">
        <div class="section-title">猜你喜欢</div>
        
        <!-- 群聊列表 -->
        <div class="group-list">
          <div 
            v-for="group in groupList" 
            :key="group.id" 
            class="group-card"
          >
            <img 
              :src="group._imgError ? '/images/icons/default_group_avatar.webp' : group.avatar" 
              class="group-avatar" 
              @error="group._imgError = true" 
            />
            <div class="group-info">
              <div class="group-name">{{ group.name }}</div>
              <div class="group-desc">{{ group.description }}</div>
              <div class="group-stats">
                <span class="fire">🔥</span>
                <span>{{ group.memberCount }}人在玩</span>
              </div>
            </div>
            <div class="group-action">
              <span v-if="group.isFree" class="free-tag">限时免费</span>
              <button class="join-btn" @click="joinGroup(group)">
                加入群聊
              </button>
              <div class="coin-cost">
                <span class="coin">🪙</span>
                <span>{{ group.coinCost }}</span>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- 裸聊内容 - 只在有数据时显示 -->
      <template v-if="activeMainTab === 'chat' && userList.length > 0">
        <!-- 子分类标签 -->
        <div class="sub-tabs">
          <span 
            v-for="sub in chatSubTabs" 
            :key="sub"
            :class="['sub-tab', { active: activeSubTab === sub }]"
            @click="activeSubTab = sub"
          >
            {{ sub }}
          </span>
        </div>

        <!-- 用户卡片列表 -->
        <div class="user-grid">
          <div v-for="user in userList" :key="user.id" class="user-card" @click="viewUser(user)">
            <div class="user-cover">
              <img :src="user.avatar" :alt="user.nickname" />
              <div class="chat-badge" v-if="user.chatCount">
                <img src="/images/backgrounds/dating_tab_soul.webp" class="chat-icon" />
                <span>{{ user.chatCount }}人聊过</span>
              </div>
              <div class="host-tag" v-if="user.isHost">王牌主播</div>
            </div>
            <div class="user-info">
              <div class="user-name">
                {{ user.nickname }}
                <span class="vip-icon" v-if="user.isVip">👑</span>
              </div>
              <div class="user-stats">
                {{ user.age }}岁 {{ user.height }}cm {{ user.weight }}kg {{ user.cup }}罩杯
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- 直播内容 - 只在有数据时显示 -->
      <template v-if="activeMainTab === 'live' && hostList.length > 0">
        <!-- 子分类标签 - 独立在导航下 -->
        <div class="sub-tabs live-sub-tabs">
          <span 
            v-for="sub in liveSubTabs" 
            :key="sub"
            :class="['sub-tab', { active: activeLiveTab === sub }]"
            @click="activeLiveTab = sub"
          >
            {{ sub }}
          </span>
        </div>
        
        <!-- 直播页面 -->
        <div class="live-page">
          <!-- 背景图框架 -->
          <div class="live-banner-frame">
            <img src="/images/backgrounds/dating_tab_chat.webp" alt="直播" class="live-banner-img" />
            <!-- 主播列表叠加在背景图横线下方 -->
            <div class="host-grid-overlay">
              <div v-for="host in hostList" :key="host.id" class="host-card" @click="enterLive(host)">
                <div class="host-cover">
                  <img :src="host.avatar" :alt="host.nickname" />
                  <div class="host-tag">王牌主播</div>
                </div>
                <div class="host-name">{{ host.nickname }}</div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- AI广场内容 -->
      <template v-if="activeMainTab === 'ai'">
        <div class="coming-soon">
          <span class="icon">🤖</span>
          <p>AI广场即将上线</p>
          <p class="sub">敬请期待</p>
        </div>
      </template>
    </div>

    <!-- 底部导航 -->
    <BottomNav />
  </div>
</template>

<script setup>
defineOptions({ name: 'Dating' })

import { ref, onMounted, onActivated, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import BottomNav from '@/components/common/BottomNav.vue'
import IconAdsGrid from '@/components/common/IconAdsGrid.vue'
import api from '@/utils/api'

const router = useRouter()
const activeMainTab = ref('soul')
const activeSubTab = ref('学生萝莉')
const activeLiveTab = ref('推荐')
const scrollContainer = ref(null)

// 子分类
const chatSubTabs = ['学生萝莉', '人妻少妇', '主播御姐', '模特兼职']
const liveSubTabs = ['推荐', '中国', '日韩', '越南', '乌克兰', '俄罗斯', '欧美', '男主播']

// 第一排广告 - 固定（从后台获取）
const adRow1 = ref([])

// 第二排广告 - 循环滚动（从后台获取）
const adRow2 = ref([])

// 获取图标广告
const fetchIconAds = async () => {
  try {
    const res = await api.get('/ads/icons')
    const ads = res.data || res || []
    // 分成两排
    adRow1.value = ads.slice(0, 5)
    adRow2.value = ads.slice(5, 11)
  } catch (error) {
    // API失败时不显示广告，保持空数组
    console.log('获取广告失败')
  }
}

// 群聊列表
const groupList = ref([])

// 用户列表（裸聊）
const userList = ref([])

// 主播列表（直播）
const hostList = ref([])

// 获取群聊列表
const fetchGroups = async () => {
  try {
    const res = await api.get('/dating/groups', { params: { category: 'soul' } })
    const data = res.data || res || []
    groupList.value = data.map(g => ({
      id: g.id,
      name: g.name,
      description: g.description,
      memberCount: g.member_count,
      coinCost: g.coin_cost,
      isFree: g.is_free,
      avatar: g.avatar,
      joinUrl: g.join_url
    }))
  } catch (error) {
    // API失败时不显示群聊，保持空数组
    console.log('获取群聊失败')
  }
}

// 获取裸聊用户列表
const fetchChatUsers = async () => {
  try {
    const res = await api.get('/dating/hosts', { params: { category: 'chat', sub_category: activeSubTab.value } })
    const data = res.data || res || []
    userList.value = data.map(h => ({
      id: h.id,
      nickname: h.nickname,
      age: h.age,
      height: h.height,
      weight: h.weight,
      cup: h.cup,
      avatar: h.avatar,
      chatCount: h.chat_count,
      isVip: h.is_vip,
      isHost: h.is_ace,
      profileUrl: h.profile_url
    }))
  } catch (error) {
    console.log('获取裸聊用户失败')
  }
}

// 获取直播主播列表
const fetchLiveHosts = async () => {
  try {
    const res = await api.get('/dating/hosts', { params: { category: 'live' } })
    const data = res.data || res || []
    hostList.value = data.map(h => ({
      id: h.id,
      nickname: h.nickname,
      avatar: h.avatar,
      isAce: h.is_ace,
      profileUrl: h.profile_url
    }))
  } catch (error) {
    console.log('获取主播失败')
  }
}

// 事件处理
const handleAdClick = (ad) => {
  if (ad.target_url) {
    window.open(ad.target_url, '_blank')
  }
}

const joinGroup = (group) => {
  if (group.joinUrl) {
    window.open(group.joinUrl, '_blank')
  }
}

const viewUser = (user) => {
  if (user.profileUrl) {
    window.open(user.profileUrl, '_blank')
  }
}

const enterLive = (host) => {
  if (host.profileUrl) {
    window.open(host.profileUrl, '_blank')
  }
}

onMounted(() => {
  fetchIconAds()
  fetchGroups()
  fetchChatUsers()
  fetchLiveHosts()
})

// keep-alive 激活时滚动到顶部
onActivated(async () => {
  await nextTick()
  // 滚动容器到顶部
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = 0
  }
})

// 监听子分类切换
watch(activeSubTab, () => {
  fetchChatUsers()
})

// 监听主标签切换
watch(activeMainTab, (newTab) => {
  if (newTab === 'chat') {
    fetchChatUsers()
  } else if (newTab === 'live') {
    fetchLiveHosts()
  } else if (newTab === 'soul') {
    fetchGroups()
  }
})
</script>

<style lang="scss" scoped>
.dating-page {
  height: 100vh;
  height: 100dvh;
  background: #0a0a0a;
  color: #fff;
  padding-bottom: calc(52px + var(--safe-area-bottom, 0px));
  overflow-x: hidden;
  overflow-y: auto;
}

// 主标签导航
.main-tabs {
  display: flex;
  justify-content: flex-start;
  gap: 24px;
  padding: 12px 16px;
  padding-top: calc(12px + env(safe-area-inset-top, 0px));
  background: #0a0a0a;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
  
  .tab-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 8px 10px;
    cursor: pointer;
    color: rgba(255, 255, 255, 0.6);
    font-size: 15px;
    transition: all 0.3s;
    position: relative;
    min-height: 36px;
    
    .tab-icon-img {
      height: 26px;
      width: auto;
      object-fit: contain;
      
      &.active-img {
        height: 32px;
        border-radius: 5px;
      }
    }
    
    &.active {
      color: #a855f7;
      font-weight: 600;
      
      &::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 50%;
        transform: translateX(-50%);
        width: 22px;
        height: 3px;
        background: linear-gradient(90deg, #a855f7, #6366f1);
        border-radius: 2px;
      }
    }
  }
}

// 内容区域
.content-area {
  padding: 0 12px 12px;
}

// 区块标题
.section-title {
  font-size: 16px;
  font-weight: 600;
  padding: 16px 0 12px;
  color: #fff;
}

// 群聊列表
.group-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.group-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  
  .group-avatar {
    width: 60px;
    height: 60px;
    border-radius: 12px;
    object-fit: cover;
  }
  
  .group-info {
    flex: 1;
    min-width: 0;
    
    .group-name {
      font-size: 14px;
      font-weight: 600;
      color: #fff;
      margin-bottom: 4px;
    }
    
    .group-desc {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      margin-bottom: 4px;
    }
    
    .group-stats {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 12px;
      color: rgba(255, 255, 255, 0.6);
      
      .fire {
        font-size: 14px;
      }
    }
  }
  
  .group-action {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    
    .free-tag {
      font-size: 10px;
      color: #a855f7;
      background: rgba(168, 85, 247, 0.2);
      padding: 2px 6px;
      border-radius: 4px;
    }
    
    .join-btn {
      background: linear-gradient(135deg, #a855f7 0%, #6366f1 100%);
      color: #fff;
      border: none;
      padding: 8px 16px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.2s;
      
      &:active {
        transform: scale(0.95);
      }
    }
    
    .coin-cost {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 11px;
      color: #ffd700;
      
      .coin {
        font-size: 12px;
      }
    }
  }
}

// 子分类标签
.sub-tabs {
  display: flex;
  gap: 12px;
  padding: 12px 0;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  
  &::-webkit-scrollbar {
    display: none;
  }
  
  .sub-tab {
    padding: 6px 14px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.7);
    white-space: nowrap;
    cursor: pointer;
    transition: all 0.3s;
    
    &.active {
      background: linear-gradient(135deg, #a855f7 0%, #6366f1 100%);
      color: #fff;
    }
  }
}

// 用户卡片网格
.user-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.user-card {
  background: #1a1a2e;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s;
  
  &:active {
    transform: scale(0.98);
  }
  
  .user-cover {
    position: relative;
    aspect-ratio: 3/4;
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    
    .chat-badge {
      position: absolute;
      top: 8px;
      left: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 4px;
      background: url('/images/backgrounds/dating_tab_soul.webp') no-repeat center center;
      background-size: contain;
      padding: 8px 12px 8px 42px;
      border-radius: 14px;
      font-size: 12px;
      font-weight: 500;
      color: #fff;
      min-width: 80px;
      min-height: 28px;
      
      .chat-icon {
        display: none;
      }
    }
    
    .host-tag {
      position: absolute;
      bottom: 8px;
      left: 8px;
      background: linear-gradient(135deg, #a855f7 0%, #6366f1 100%);
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 10px;
      color: #fff;
      font-weight: 600;
    }
  }
  
  .user-info {
    padding: 10px;
    
    .user-name {
      font-size: 14px;
      font-weight: 600;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 4px;
      margin-bottom: 4px;
      
      .vip-icon {
        font-size: 12px;
      }
    }
    
    .user-stats {
      font-size: 11px;
      color: rgba(255, 255, 255, 0.5);
    }
  }
}

// 直播横幅
.live-banner {
  position: relative;
  margin: 12px 0;
  border-radius: 12px;
  overflow: hidden;
  
  img {
    width: 100%;
    height: auto;
    display: block;
  }
  
  .banner-btn {
    position: absolute;
    bottom: 16px;
    right: 16px;
    
    img {
      width: 120px;
      height: auto;
    }
  }
}

// 直播页面
.live-page {
  margin: 0 -12px -12px;
  padding: 0;
  
  .live-banner-frame {
    width: 100%;
    position: relative;
    
    .live-banner-img {
      width: 100%;
      height: auto;
      display: block;
    }
    
    // 主播列表叠加在背景图横线下方
    .host-grid-overlay {
      position: absolute;
      top: 40%;
      left: 12px;
      right: 12px;
      bottom: 12px;
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
      overflow-y: auto;
      padding-bottom: 60px;
      
      &::-webkit-scrollbar {
        display: none;
      }
    }
  }
}

.live-sub-tabs {
  margin: 0 -12px;
  padding: 12px 12px;
  background: #0a0a0a;
}

// 主播网格
.host-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.host-card {
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.2) 0%, rgba(99, 102, 241, 0.2) 100%);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s;
  border: 2px solid rgba(236, 72, 153, 0.5);
  box-shadow: 0 4px 15px rgba(236, 72, 153, 0.2);
  
  &:active {
    transform: scale(0.98);
  }
  
  .host-cover {
    position: relative;
    aspect-ratio: 1;
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    
    .host-tag {
      position: absolute;
      top: 8px;
      right: 8px;
      background: linear-gradient(135deg, #ec4899 0%, #f472b6 100%);
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 10px;
      color: #fff;
      font-weight: 600;
      white-space: nowrap;
    }
  }
  
  .host-name {
    padding: 8px;
    font-size: 12px;
    color: #fff;
    text-align: left;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    background: rgba(0, 0, 0, 0.3);
  }
}

// AI广场占位
.coming-soon {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  
  .icon {
    font-size: 48px;
    margin-bottom: 16px;
  }
  
  p {
    font-size: 18px;
    color: #fff;
    margin: 0;
    
    &.sub {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.5);
      margin-top: 8px;
    }
  }
}

// 响应式样式
@media (max-width: 360px) {
  .main-tabs {
    gap: 16px;
    padding: 10px 12px;
    
    .tab-item {
      font-size: 13px;
      padding: 6px 6px;
      
      .tab-icon-img.active-img {
        height: 26px;
      }
    }
  }
  
  .ad-row-fixed {
    grid-template-columns: repeat(4, 1fr);
  }
  
  .ad-item {
    min-width: 50px;
    
    .ad-icon-wrap {
      width: 48px;
      height: 48px;
    }
    
    .ad-name {
      font-size: 10px;
    }
  }
  
  .group-card {
    padding: 10px;
    
    .group-avatar {
      width: 50px;
      height: 50px;
    }
    
    .group-action .join-btn {
      padding: 6px 12px;
      font-size: 11px;
    }
  }
  
  .user-grid {
    gap: 8px;
  }
  
  .host-grid {
    gap: 8px;
  }
}

@media (min-width: 480px) {
  .ad-row-fixed {
    grid-template-columns: repeat(6, 1fr);
  }
  
  .user-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .host-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (min-width: 768px) {
  .dating-page {
    max-width: 750px;
    margin: 0 auto;
  }
  
  .main-tabs {
    gap: 32px;
    padding: 14px 20px;
    
    .tab-item {
      font-size: 16px;
      
      .tab-icon-img.active-img {
        height: 38px;
      }
    }
  }
  
  .ad-row-fixed {
    grid-template-columns: repeat(7, 1fr);
  }
  
  .ad-item {
    .ad-icon-wrap {
      width: 64px;
      height: 64px;
    }
    
    .ad-name {
      font-size: 12px;
    }
  }
  
  .group-card {
    padding: 16px;
    
    .group-avatar {
      width: 70px;
      height: 70px;
    }
    
    .group-info {
      .group-name {
        font-size: 16px;
      }
      
      .group-desc {
        font-size: 13px;
      }
    }
  }
  
  .user-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
  }
  
  .host-grid {
    grid-template-columns: repeat(5, 1fr);
    gap: 16px;
  }
}

@media (min-width: 1024px) {
  .dating-page {
    max-width: 960px;
  }
  
  .ad-row-fixed {
    grid-template-columns: repeat(8, 1fr);
  }
  
  .user-grid {
    grid-template-columns: repeat(5, 1fr);
  }
  
  .host-grid {
    grid-template-columns: repeat(6, 1fr);
  }
  
  .live-page .live-banner-frame .host-grid-overlay {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (min-width: 1280px) {
  .dating-page {
    max-width: 1100px;
  }
  
  .user-grid {
    grid-template-columns: repeat(6, 1fr);
  }
  
  .host-grid {
    grid-template-columns: repeat(7, 1fr);
  }
  
  .live-page .live-banner-frame .host-grid-overlay {
    grid-template-columns: repeat(5, 1fr);
  }
}

// 触摸设备优化
@media (hover: none) and (pointer: coarse) {
  .group-card:hover,
  .user-card:hover,
  .host-card:hover {
    transform: none;
  }
  
  .group-card:active,
  .user-card:active,
  .host-card:active {
    transform: scale(0.98);
  }
}
</style>