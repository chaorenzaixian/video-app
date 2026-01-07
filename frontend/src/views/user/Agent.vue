<template>
  <div class="agent-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.push('/user/profile')">‹</div>
      <nav class="header-tabs">
        <span class="tab-item active">代理赚钱</span>
        <span class="tab-item" @click="$router.push('/user/tasks')">福利任务</span>
        <span class="tab-item" @click="$router.push('/user/app-recommend')">应用推荐</span>
      </nav>
    </header>

    <!-- 代理卡片 -->
    <div class="agent-card">
      <div class="card-row">
        <div class="card-left">
          <div :class="['avatar-container', { 'is-vip': userIsVip }]">
            <div class="avatar-frame">
              <img :src="avatarUrl" class="user-avatar" />
            </div>
          </div>
          <div class="agent-info">
            <div class="nickname-row">
              <span class="user-nickname">{{ userNickname }}</span>
              <img 
                v-if="userIsVip && vipLevelIcon" 
                :src="vipLevelIcon" 
                class="vip-level-badge"
                alt="VIP"
              />
            </div>
            <span class="agent-level">{{ agentLevelName }}</span>
          </div>
        </div>
        <div class="card-right">
          <span class="balance-label">可提现金额</span>
          <span class="balance-value">{{ Math.floor(availableBalance) }}</span>
        </div>
      </div>
      <div class="card-buttons">
        <button class="btn-withdraw" @click="$router.push('/user/withdraw')">
          <img src="/images/backgrounds/withdraw_now.webp" alt="btn" />
        </button>
        <button class="btn-data" @click="$router.push('/user/promotion-data')">
          <img src="/images/backgrounds/promotional_data.webp" alt="btn" />
        </button>
      </div>
    </div>

    <!-- 推广Banner -->
    <div class="promo-banner" @click="$router.push('/user/promotion')">
      <img src="/images/backgrounds/proxy_banner.webp" alt="banner" class="banner-bg" />
    </div>

    <!-- 操作简单 无限级返利 -->
    <div class="section-block">
      <div class="section-title-fancy">
        <img src="/images/backgrounds/app_dlbtw.webp" alt="" class="title-icon left" />
        <span class="title-text gradient-gold">操作简单 无限级返利</span>
        <img src="/images/backgrounds/app_dlbtw2.webp" alt="" class="title-icon right" />
      </div>
      
      <div class="content-box">
        <h4 class="sub-title gradient-gold">操作说明</h4>
        <p class="desc-text">在APP里，依次点击【我的】-【分享推广】获取专属推广链接或二维码，推荐分享给他其他人下载，就可以获得收益。</p>
        
        <h4 class="sub-title gradient-gold">收益来源</h4>
        <p class="desc-text">1.直推收益</p>
        <p class="desc-text">2.层级收益</p>
      </div>
    </div>

    <!-- 代理等级说明 -->
    <div class="section-block">
      <div class="section-title-fancy">
        <img src="/images/backgrounds/app_dlbtw.webp" alt="" class="title-icon left" />
        <span class="title-text gradient-gold">代理等级说明</span>
        <img src="/images/backgrounds/app_dlbtw2.webp" alt="" class="title-icon right" />
      </div>
      
      <div class="level-table">
        <div class="table-header">
          <span>代理等级</span>
          <span>返利比例</span>
          <span>条件</span>
        </div>
        <div class="table-row" v-for="(level, index) in levelList" :key="index">
          <span class="col-level">{{ level.name }}</span>
          <span class="col-rate">{{ level.rate }}</span>
          <span class="col-condition">{{ level.condition }}</span>
        </div>
      </div>
    </div>

    <!-- 直推收益 -->
    <div class="section-block">
      <div class="section-title-fancy">
        <img src="/images/backgrounds/app_dlbtw.webp" alt="" class="title-icon left" />
        <span class="title-text gradient-gold">直推收益</span>
        <img src="/images/backgrounds/app_dlbtw2.webp" alt="" class="title-icon right" />
      </div>
      
      <p class="desc-text center gradient-gold">您直接推广的所有用户的会员充值，你都将获得直推收益</p>
      
      <!-- 直推层级图 -->
      <div class="hierarchy-diagram">
        <img src="/images/backgrounds/app_dlcj.png" alt="层级图" class="hierarchy-img" />
      </div>
    </div>

    <!-- 层级收益 -->
    <div class="section-block">
      <div class="section-title-fancy">
        <img src="/images/backgrounds/app_dlbtw.webp" alt="" class="title-icon left" />
        <span class="title-text gradient-gold">层级收益（月入十万秘籍）</span>
        <img src="/images/backgrounds/app_dlbtw2.webp" alt="" class="title-icon right" />
      </div>
      
      <p class="desc-text gradient-gold">如果您的下级也参与代理推广，若您的等级高于他们，就能从他们所有伞下业绩中获取层级收益</p>
      
      <!-- 层级收益图 -->
      <div class="commission-diagram">
        <img src="/images/backgrounds/app_dlcy.webp" alt="层级收益图" class="commission-img" />
      </div>
      
      <!-- 说明文字 -->
      <div class="commission-desc">
        <p class="gradient-gold">子代理A等级为铂金，与你相差1级，A伞下的所有用户会员充值，你获得6%的返利 <span class="green">（绿色部分）</span></p>
        <p class="gradient-gold">子代理B等级为黄金，与你相差2级，A伞下的所有用户会员充值，你获得12%的返利 <span class="blue">（蓝色部分）</span></p>
        <p class="gradient-gold">子代理C等级为普通，与你相差5级，A伞下的所有用户会员充值，你获得30%的返利 <span class="yellow">（黄色部分）</span></p>
      </div>
    </div>

    <!-- 总结 -->
    <div class="section-block">
      <div class="section-title-fancy">
        <img src="/images/backgrounds/app_dlbtw.webp" alt="" class="title-icon left" />
        <span class="title-text gradient-gold">总结</span>
        <img src="/images/backgrounds/app_dlbtw2.webp" alt="" class="title-icon right" />
      </div>
      
      <div class="summary-content">
        <p class="gradient-gold">1.除了直推用户，更快的赚钱方式是发展子代理，子代理的所有伞下业绩，你都可以直接获得层级收益，子代理多了，完全是躺着数钱！</p>
        <p class="gradient-gold">2.自己也需要尽快升级，你的级别越高，跟子代理的层级差越大，收益越高。如果差一级，你可以拿6%层级查，如果差两级，你可以拿12%层级差，以此类推，最高可以获得30%的层级差收益。</p>
      </div>
    </div>

    <!-- 底部按钮 -->
    <div class="bottom-section">
      <p class="question-text gradient-gold">规则看懂了不会实操？</p>
      <button class="btn-group-img" @click="joinGroup">
        <img src="/images/backgrounds/app_dljq.png" alt="加群" />
      </button>
    </div>

    <!-- 固定底部推广按钮 -->
    <div class="fixed-bottom">
      <button class="btn-promote-img" @click="$router.push('/user/promotion')">
        <img src="/images/backgrounds/app_proxy_btn_bg.webp" alt="立即推广" />
      </button>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import api from '@/utils/api'

const userStore = useUserStore()

// 数据
const agentInfo = ref({
  agent_level: 0,
  available_balance: 0,
  remaining_views: 0
})
const remainingViews = computed(() => agentInfo.value.remaining_views || 0)

// 用户信息
const userNickname = computed(() => userStore.user?.nickname || userStore.user?.username || '用户')
const userIsVip = computed(() => userStore.user?.is_vip || false)

// VIP等级图标映射（与个人中心一致）
const VIP_LEVEL_ICONS = {
  1: '/images/backgrounds/vip_gold.webp',
  2: '/images/backgrounds/vip_1.webp',
  3: '/images/backgrounds/vip_2.webp',
  4: '/images/backgrounds/vip_3.webp',
  5: '/images/backgrounds/super_vip_red.webp',
  6: '/images/backgrounds/super_vip_blue.webp'
}

// VIP等级图标
const vipLevelIcon = computed(() => {
  const level = userStore.user?.vip_level || 1
  return VIP_LEVEL_ICONS[level] || VIP_LEVEL_ICONS[1]
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

// 根据用户ID自动分配头像（与个人中心一致）
const avatarUrl = computed(() => {
  // 如果用户有自定义头像，使用自定义头像
  if (userStore.user?.avatar) {
    return userStore.user.avatar
  }
  // 根据用户ID取模分配预设头像
  const numericId = parseInt(userStore.user?.id) || 1
  return getDefaultAvatarPath(numericId)
})

const agentLevelName = computed(() => {
  const levels = ['邀请好友快速提现', '推广达人', '高级代理', '超级代理', '钻石代理']
  return levels[agentInfo.value.agent_level] || '邀请好友快速提现'
})
const availableBalance = computed(() => agentInfo.value.available_balance || 0)

// 等级列表
const levelList = ref([])

// 获取代理等级配置
const fetchAgentLevels = async () => {
  try {
    const res = await api.get('/config/agent-levels')
    const data = res.data || res
    if (data.levels && data.levels.length > 0) {
      levelList.value = data.levels.map(l => ({
        name: l.name,
        rate: l.rate + '%',
        condition: l.condition
      }))
    } else {
      // 默认配置
      levelList.value = [
        { name: '钻石级', rate: '70%', condition: '累计直推400个付费会员+2个直属铂金以上代理' },
        { name: '铂金级', rate: '64%', condition: '累计直推100个付费会员+2个直属黄金以上代理' },
        { name: '黄金级', rate: '58%', condition: '累计直推50个付费会员+2个直属白银以上代理' },
        { name: '白银级', rate: '52%', condition: '累计直推20个付费会员+2个直属青铜以上代理' },
        { name: '青铜级', rate: '46%', condition: '累计直推5个付费会员' },
        { name: '普通级', rate: '40%', condition: '邀请1人充值成为普通代理' }
      ]
    }
  } catch (error) {
    console.error('获取代理等级配置失败:', error)
    // 使用默认配置
    levelList.value = [
      { name: '钻石级', rate: '70%', condition: '累计直推400个付费会员+2个直属铂金以上代理' },
      { name: '铂金级', rate: '64%', condition: '累计直推100个付费会员+2个直属黄金以上代理' },
      { name: '黄金级', rate: '58%', condition: '累计直推50个付费会员+2个直属白银以上代理' },
      { name: '白银级', rate: '52%', condition: '累计直推20个付费会员+2个直属青铜以上代理' },
      { name: '青铜级', rate: '46%', condition: '累计直推5个付费会员' },
      { name: '普通级', rate: '40%', condition: '邀请1人充值成为普通代理' }
    ]
  }
}

// 获取代理信息
const fetchAgentInfo = async () => {
  try {
    const res = await api.get('/promotion/agent/info')
    agentInfo.value = res.data || agentInfo.value
  } catch (error) {
    console.error('获取代理信息失败:', error)
  }
}

const joinGroup = () => {
  alert('请联系客服获取群链接')
}

onMounted(() => {
  fetchAgentInfo()
  fetchAgentLevels()
})
</script>

<style lang="scss" scoped>
.agent-page {
  min-height: 100vh;
  background: #0a0a0a;
  color: #fff;
  padding-bottom: 100px;
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
          background: #8b5cf6;
          border-radius: 1px;
        }
      }
    }
  }
}

// 代理卡片
.agent-card {
  margin: 0 16px 16px;
  padding: 24px 18px 20px;
  
  .card-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 18px;
  }
  
  .card-left {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .avatar-container {
    position: relative;
    flex-shrink: 0;
    
    .avatar-frame {
      width: 56px;
      height: 56px;
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
  }
  
  @keyframes vip-border-shine {
    0%, 100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
  }
  
  .agent-info {
    display: flex;
    flex-direction: column;
    gap: 1px;
    
    .nickname-row {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    
    .user-nickname {
      font-size: 16px;
      font-weight: 600;
      line-height: 1.3;
      background: linear-gradient(135deg, #ffd700 0%, #ffec8b 30%, #daa520 60%, #ffd700 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    
    .vip-level-badge {
      height: 22px;
      width: auto;
      max-width: 60px;
      object-fit: contain;
      animation: vip-badge-glow 2s ease-in-out infinite;
    }
    
    .agent-level {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.5);
    }
  }
  
  @keyframes vip-badge-glow {
    0%, 100% {
      filter: drop-shadow(0 0 2px rgba(255, 215, 0, 0.4));
    }
    50% {
      filter: drop-shadow(0 0 5px rgba(255, 215, 0, 0.7));
    }
  }
  
  .card-right {
    text-align: right;
    flex-shrink: 0;
    
    .balance-label {
      display: block;
      font-size: 13px;
      font-weight: 500;
      background: linear-gradient(135deg, #f5e6b8 0%, #d4af37 50%, #f5e6b8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin-bottom: 2px;
    }
    
    .balance-value {
      font-size: 24px;
      font-weight: 700;
      color: #d4af37;
      line-height: 1;
    }
  }
  
  .card-buttons {
    display: flex;
    justify-content: center;
    gap: 40px;
    width: 100%;
    margin-top: 10px;
    
    button {
      width: 130px;
      height: auto;
      border: none;
      background: transparent;
      cursor: pointer;
      border-radius: 12px;
      overflow: hidden;
      
      img {
        width: 100%;
        height: auto;
        display: block;
      }
    }
  }
}

// 推广Banner
.promo-banner {
  margin: 0 16px 16px;
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  
  .banner-bg {
    width: 100%;
    height: auto;
    display: block;
  }
}

// 区块样式
.section-block {
  margin: 0 16px 20px;
  background: rgba(30, 25, 40, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 20px 16px;
}

// 浅金色渐变文字
.gradient-gold {
  background: linear-gradient(135deg, #f5e6b8 0%, #d4af37 50%, #f5e6b8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.section-title-fancy {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 16px;
  
  .title-icon {
    width: 28px;
    height: auto;
    object-fit: contain;
    
    &.left {
      // 左侧图标
    }
    
    &.right {
      // 右侧图标
    }
  }
  
  .title-text {
    font-size: 16px;
    font-weight: 600;
  }
}

.content-box {
  .sub-title {
    font-size: 14px;
    font-weight: 600;
    margin: 12px 0 8px;
    
    &:first-child {
      margin-top: 0;
    }
  }
}

.desc-text {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.8;
  margin-bottom: 8px;
  
  &.center {
    text-align: center;
  }
}

// 等级表格
.level-table {
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  overflow: hidden;
  
  .table-header {
    display: grid;
    grid-template-columns: 80px 80px 1fr;
    background: rgba(138, 92, 246, 0.2);
    
    span {
      padding: 10px 8px;
      font-size: 12px;
      font-weight: 600;
      text-align: center;
      border-right: 1px solid rgba(138, 92, 246, 0.2);
      background: linear-gradient(135deg, #f5e6b8 0%, #d4af37 50%, #f5e6b8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      
      &:last-child {
        border-right: none;
      }
    }
  }
  
  .table-row {
    display: grid;
    grid-template-columns: 80px 80px 1fr;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    
    &:last-child {
      border-bottom: none;
    }
    
    span {
      padding: 12px 8px;
      font-size: 12px;
      color: rgba(255, 255, 255, 0.8);
      text-align: center;
      border-right: 1px solid rgba(255, 255, 255, 0.08);
      display: flex;
      align-items: center;
      justify-content: center;
      
      &:last-child {
        border-right: none;
        text-align: left;
        justify-content: flex-start;
      }
    }
    
    .col-level {
      font-weight: 500;
      background: linear-gradient(135deg, #f5e6b8 0%, #d4af37 50%, #f5e6b8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
  }
}

// 直推层级图
.hierarchy-diagram {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 0;
  
  .hierarchy-img {
    width: 100%;
    max-width: 400px;
    height: auto;
    object-fit: contain;
  }
  
  .hierarchy-top {
    margin-bottom: 10px;
  }
  
  .node-you {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: linear-gradient(135deg, #d4af37, #b8962e);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    font-weight: 600;
    color: #1a1510;
    border: 3px solid #d4af37;
  }
  
  .hierarchy-line-vertical {
    width: 2px;
    height: 20px;
    background: #d4af37;
  }
  
  .hierarchy-line-horizontal {
    width: 280px;
    height: 2px;
    background: #d4af37;
    position: relative;
    
    &::before, &::after {
      content: '';
      position: absolute;
      width: 2px;
      height: 20px;
      background: #d4af37;
      bottom: 0;
    }
    
    &::before { left: 0; }
    &::after { right: 0; }
  }
  
  .hierarchy-bottom {
    display: flex;
    justify-content: space-between;
    width: 300px;
    margin-top: 20px;
  }
  
  .node-user {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    background: rgba(138, 92, 246, 0.2);
    border: 2px solid #d4af37;
    display: flex;
    align-items: center;
    justify-content: center;
    
    span {
      font-size: 10px;
      color: #d4af37;
    }
  }
}

// 层级收益图
.commission-diagram {
  padding: 16px 0;
  display: flex;
  justify-content: center;
  
  .commission-img {
    width: 100%;
    max-width: 400px;
    height: auto;
    object-fit: contain;
  }
  
  .diagram-level {
    display: flex;
    justify-content: center;
    gap: 30px;
    
    &.level-1 {
      margin-bottom: 10px;
    }
    
    &.level-2 {
      margin-bottom: 20px;
    }
  }
  
  .diagram-lines-1 {
    height: 40px;
    
    svg {
      width: 100%;
      height: 100%;
    }
  }
  
  .node-agent {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    
    &.green { background: #4a9; border: 2px solid #4a9; }
    &.blue { background: #48f; border: 2px solid #48f; }
    &.yellow { background: #fa2; border: 2px solid #fa2; }
    
    .agent-name {
      font-size: 10px;
      color: #fff;
    }
    
    .agent-label {
      font-size: 14px;
      font-weight: 600;
      color: #fff;
    }
  }
  
  .diagram-lines-2 {
    display: flex;
    justify-content: center;
    gap: 30px;
    padding: 10px 0;
    
    .line-group {
      display: flex;
      gap: 8px;
      
      .rate {
        font-size: 11px;
        padding: 2px 6px;
        border-radius: 10px;
      }
      
      &.green .rate { color: #4a9; }
      &.blue .rate { color: #48f; }
      &.yellow .rate { color: #fa2; }
    }
  }
  
  .diagram-level.level-3 {
    gap: 20px;
    
    .user-rates {
      display: flex;
      gap: 6px;
      
      span {
        font-size: 10px;
        padding: 2px 4px;
      }
      
      &.green span { color: #4a9; }
      &.blue span { color: #48f; }
    }
  }
}

.commission-desc {
  margin-top: 20px;
  
  p {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.8);
    line-height: 1.8;
    margin-bottom: 8px;
    
    .green { color: #4a9; }
    .blue { color: #48f; }
    .yellow { color: #fa2; }
  }
}

// 总结
.summary-content {
  p {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.8);
    line-height: 1.8;
    margin-bottom: 12px;
  }
}

// 底部按钮区域
.bottom-section {
  padding: 20px 16px;
  text-align: center;
  
  .question-text {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 16px;
  }
  
  .btn-group {
    width: 100%;
    padding: 14px;
    background: transparent;
    border: 1px solid rgba(138, 92, 246, 0.3);
    border-radius: 25px;
    color: #d4af37;
    font-size: 14px;
    cursor: pointer;
  }
  
  .btn-group-img {
    width: 100%;
    max-width: 210px;
    background: transparent;
    border: none;
    cursor: pointer;
    padding: 0;
    
    img {
      width: 100%;
      height: auto;
      display: block;
    }
  }
}

// 固定底部推广按钮
.fixed-bottom {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px 24px;
  padding-bottom: calc(env(safe-area-inset-bottom, 12px) + 12px);
  background: transparent;
  display: flex;
  justify-content: center;
  
  .btn-promote-img {
    background: transparent;
    border: none;
    cursor: pointer;
    padding: 0;
    max-width: 260px;
    width: 100%;
    
    img {
      width: 100%;
      height: auto;
      display: block;
    }
  }
  
  .btn-promote {
    width: 100%;
    height: 50px;
    position: relative;
    border: none;
    background: linear-gradient(135deg, #d4af37, #b8962e);
    border-radius: 25px;
    cursor: pointer;
    overflow: hidden;
    
    .btn-bg {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    
    span {
      position: relative;
      z-index: 1;
      font-size: 18px;
      font-weight: 600;
      color: #1a1510;
    }
  }
}
</style>