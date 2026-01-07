<template>
  <div class="vip-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <button class="back-btn" @click="$router.back()">‹</button>
      <h1>会员中心</h1>
      <button class="record-btn" @click="showRecords = true">充值记录</button>
    </header>

    <!-- 用户信息 -->
    <div class="user-info-section">
      <div class="avatar-wrapper">
        <div :class="['avatar-container', { 'is-vip': user.is_vip }]">
          <img :src="avatarUrl" class="user-avatar" />
        </div>
      </div>
      <div class="user-details">
        <div class="nickname-row">
          <span class="username">{{ user.nickname || user.username || '未登录' }}</span>
          <img 
            v-if="user.vip_level > 0" 
            :src="vipLevelIcon" 
            class="vip-level-badge"
          />
        </div>
        <div class="vip-status">
          <span v-if="!user.is_vip">您还不是会员</span>
          <span v-else>{{ user.vip_level_name }} · 到期：{{ formatDate(user.vip_expire_date) }}</span>
          <a href="javascript:;" class="open-vip-link" v-if="!user.is_vip">开通会员</a>
          <span class="benefit-text">畅享特权</span>
        </div>
      </div>
    </div>

    <!-- VIP卡片轮播 -->
    <div class="vip-cards-section">
      <div class="cards-scroll" ref="cardsScroll">
        <div 
          v-for="(card, index) in vipCards" 
          :key="card.id"
          class="vip-card"
          :class="{ 'selected': selectedCard?.id === card.id }"
          @click="selectCard(card)"
        >
          <!-- 卡片背景图 -->
          <img :src="card.background_image" class="card-bg" />
        </div>
      </div>
        </div>

    <!-- 简洁卡片网格区域 -->
    <div class="simple-cards-section">
      <div class="simple-cards-grid">
        <div 
          v-for="(card, index) in vipCards" 
          :key="'simple-' + card.id"
          class="simple-card"
          :class="{ 'selected': selectedCard?.id === card.id }"
          @click="selectCard(card)"
        >
          <!-- 角标 - 不同颜色 -->
          <div 
            class="simple-badge" 
            :class="getBadgeColorClass(index)"
            v-if="card.badge_text"
          >{{ card.badge_text }}</div>
          
          <!-- 卡片名称 -->
          <div class="simple-card-name">{{ card.name }}</div>
          
          <!-- 价格 -->
          <div class="simple-card-price">
            <span class="currency">¥</span>
            <span class="amount">{{ card.price }}</span>
        </div>
          
          <!-- 描述 -->
          <div class="simple-card-desc">
            {{ card.duration_days === 0 ? '永久解锁' : card.duration_days + '天' }}{{ card.description || getLevelBenefit(card.level) }}
        </div>
          
          <!-- 每日费用 -->
          <div class="simple-daily-cost" v-if="card.duration_days > 0">
            每日仅需{{ (card.price / card.duration_days).toFixed(1) }}元
        </div>
        </div>
      </div>
    </div>

    <!-- 会员特权区域 -->
    <div class="privileges-section">
      <div class="privileges-list">
        <div 
          v-for="privilege in currentPrivileges" 
          :key="privilege.id"
          class="privilege-item"
        >
          <div class="privilege-icon">
            <img :src="privilege.icon" alt="" />
          </div>
          <div class="privilege-info">
            <div class="privilege-name">{{ privilege.name }}</div>
            <div class="privilege-desc">{{ privilege.description }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 提示文字区域（页面内容底部） -->
    <div class="tips-section">
      <p class="tips">
        *如提示【交易失败】【账户风险】等，可重新发起订单，或在15分钟后重试支付。如支付未到账，请
        <a href="javascript:;" class="link">反馈客服订单号</a>
      </p>
    </div>

    <!-- 底部支付区域（固定） -->
    <div class="pay-section">
      <button 
        class="pay-btn"
        :disabled="!selectedCard || isProcessing"
        @click="handlePay"
      >
        <span v-if="isProcessing">处理中...</span>
        <span v-else-if="selectedCard">¥{{ selectedCard.price }}/立即支付</span>
        <span v-else>请选择会员卡</span>
      </button>
      
      <p class="support-text">
        支付问题反馈，点击联系 <a href="javascript:;" class="link">在线客服</a>
      </p>
    </div>

    <!-- 支付方式选择弹窗 -->
    <div v-if="showPaymentModal" class="payment-modal" @click.self="showPaymentModal = false">
      <div class="modal-content payment-modal-content">
        <div class="modal-header">
          <span>选择支付方式</span>
          <button class="close-btn" @click="showPaymentModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="payment-methods">
            <div 
              v-for="method in paymentMethods" 
              :key="method.type"
              class="payment-method-item"
              :class="{ 'selected': selectedPayType === method.type }"
              @click="selectedPayType = method.type"
            >
              <span class="method-icon">{{ method.icon }}</span>
              <span class="method-name">{{ method.name }}</span>
              <span class="check-icon" v-if="selectedPayType === method.type">✓</span>
            </div>
          </div>
          <div class="payment-amount">
            <span>支付金额：</span>
            <span class="amount">¥{{ selectedCard?.price }}</span>
          </div>
          <button 
            class="confirm-pay-btn"
            :disabled="isProcessing"
            @click="confirmPay"
          >
            {{ isProcessing ? '处理中...' : '确认支付' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 充值记录弹窗 -->
    <div v-if="showRecords" class="records-modal" @click.self="showRecords = false">
      <div class="modal-content">
        <div class="modal-header">
          <span>充值记录</span>
          <button class="close-btn" @click="showRecords = false">×</button>
        </div>
        <div class="modal-body">
          <div v-for="record in paymentRecords" :key="record.id" class="record-item">
            <div class="record-info">
              <span class="record-name">{{ record.card_name }}</span>
              <span class="record-time">{{ formatDate(record.created_at) }}</span>
            </div>
            <span class="record-amount">¥{{ record.amount }}</span>
          </div>
          <div v-if="paymentRecords.length === 0" class="empty-state">
            暂无充值记录
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
import { useUserStore } from '@/stores/user'
import api from '@/utils/api'
import { useAbortController } from '@/composables/useAbortController'
import { VIP_LEVEL_ICONS, VIP_LEVEL_BENEFITS } from '@/constants/vip'

const router = useRouter()
const userStore = useUserStore()

// 请求取消控制器
const { signal: abortSignal } = useAbortController()

const user = computed(() => userStore.user || {})

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

// 头像URL - 与个人中心保持一致
const avatarUrl = computed(() => {
  // 如果用户有自定义头像，使用自定义头像
  if (user.value.avatar) {
    return user.value.avatar
  }
  // 根据用户ID取模分配预设头像
  const numericId = parseInt(user.value.id) || 1
  return getDefaultAvatarPath(numericId)
})

const vipCards = ref([])
const selectedCard = ref(null)
const vipPrivileges = ref([])
const paymentRecords = ref([])
const isProcessing = ref(false)
const showRecords = ref(false)
const cardsScroll = ref(null)

// 当前选中卡片的特权 - 只显示后台设置的关联特权
const currentPrivileges = computed(() => {
  if (!selectedCard.value) return []
  
  // 只显示后台关联的特权ID列表
  const privilegeIds = selectedCard.value.privilege_ids
  if (privilegeIds && privilegeIds.length > 0) {
    // 按照privilege_ids的顺序返回特权
    return privilegeIds
      .map(id => vipPrivileges.value.find(p => p.id === id))
      .filter(p => p != null)
  }
  
  // 如果没有设置关联特权，返回空数组
  return []
})

// 当前VIP卡片
const currentVipCard = computed(() => {
  if (!user.value.vip_level) return null
  return vipCards.value.find(c => c.level === user.value.vip_level)
})

// VIP等级图标（使用统一常量）
const vipLevelIcon = computed(() => {
  return VIP_LEVEL_ICONS[user.value.vip_level] || ''
})

// 获取角标颜色类名
const getBadgeColorClass = (index) => {
  const colors = ['badge-red', 'badge-orange', 'badge-purple', 'badge-blue', 'badge-green', 'badge-pink']
  return colors[index % colors.length]
}

// 获取等级对应的权益描述（使用统一常量）
const getLevelBenefit = (level) => {
  return VIP_LEVEL_BENEFITS[level] || 'VIP特权'
}

// 获取VIP卡片列表
const fetchVipCards = async () => {
  try {
    const res = await api.get('/vip/cards', { signal: abortSignal })
    vipCards.value = res.data || []
    // 默认选中第一个
    if (vipCards.value.length > 0 && !selectedCard.value) {
      selectedCard.value = vipCards.value[0]
    }
  } catch (error) {
    if (error.name !== 'CanceledError' && error.name !== 'AbortError') {
      console.error('获取VIP卡片失败:', error)
      // 使用默认数据
      vipCards.value = getDefaultCards()
      selectedCard.value = vipCards.value[0]
    }
  }
}

// 获取VIP特权列表
const fetchPrivileges = async () => {
  try {
    const res = await api.get('/vip/privileges', { signal: abortSignal })
    vipPrivileges.value = res.data || []
  } catch (error) {
    if (error.name !== 'CanceledError' && error.name !== 'AbortError') {
      console.error('获取VIP特权失败:', error)
      // 使用默认数据
      vipPrivileges.value = getDefaultPrivileges()
    }
  }
}

// 获取充值记录
const fetchRecords = async () => {
  try {
    const res = await api.get('/vip/records', { signal: abortSignal })
    paymentRecords.value = res.data || []
  } catch (error) {
    if (error.name !== 'CanceledError' && error.name !== 'AbortError') {
      console.error('获取充值记录失败:', error)
    }
  }
}

// 选择卡片
const selectCard = (card) => {
  selectedCard.value = card
  
  // 滚动顶部大卡片到对应位置
  const index = vipCards.value.findIndex(c => c.id === card.id)
  if (index !== -1 && cardsScroll.value) {
    const cardWidth = 168 // 卡片宽度160 + 间距8
    cardsScroll.value.scrollTo({
      left: index * cardWidth,
      behavior: 'smooth'
    })
  }
}

// 支付
const handlePay = async () => {
  if (!selectedCard.value) {
    ElMessage.warning('请选择会员卡')
    return
  }
  
  // 显示支付方式选择
  showPaymentModal.value = true
}

// 支付方式选择
const showPaymentModal = ref(false)
const selectedPayType = ref('alipay')

const paymentMethods = [
  { type: 'alipay', name: '支付宝', icon: '💳' },
  { type: 'wxpay', name: '微信支付', icon: '💚' },
  { type: 'qqpay', name: 'QQ钱包', icon: '🐧' },
]

// 确认支付
const confirmPay = async () => {
  if (!selectedCard.value) return
  
  isProcessing.value = true
  showPaymentModal.value = false
  
  try {
    // 调用易支付接口
    const res = await api.post('/payments/epay/create', {
      order_type: getOrderType(selectedCard.value.level)
    }, {
      params: {
        pay_type: selectedPayType.value
      }
    })
    
    if (res.data?.payment_url) {
      // 跳转到支付页面
      window.location.href = res.data.payment_url
    } else if (res.data?.qr_code) {
      // 显示二维码（可选）
      ElMessage.info('请使用手机扫码支付')
      // 可以在这里显示二维码弹窗
    } else {
      ElMessage.error('获取支付链接失败')
    }
  } catch (error) {
    console.error('支付失败:', error)
    ElMessage.error(error.response?.data?.detail || '支付失败，请重试')
  } finally {
    isProcessing.value = false
  }
}

// 根据VIP等级获取订单类型
const getOrderType = (level) => {
  const typeMap = {
    1: 'VIP_MONTHLY',
    2: 'VIP_QUARTERLY', 
    3: 'VIP_YEARLY',
    4: 'VIP_YEARLY',
    5: 'VIP_LIFETIME',
    6: 'VIP_LIFETIME',
    7: 'VIP_LIFETIME'
  }
  return typeMap[level] || 'VIP_MONTHLY'
}

// 默认卡片数据
const getDefaultCards = () => [
  {
    id: 1,
    level: 3,
    name: '尊享限定卡',
    display_title: '12.12\n尊享限定卡',
    background_image: '/images/vip/card_premium.webp',
    badge_text: '15项特权',
    benefit_line1: '永久VIP特权',
    benefit_line2: '永久金币免费',
    benefit_line3: '30天直播特权',
    benefit_line4: '15次AI脱衣',
    price: 200,
    original_price: 500,
    sort_order: 1
  },
  {
    id: 2,
    level: 2,
    name: '尊享永久卡',
    display_title: '尊享永久卡',
    background_image: '/images/vip/card_forever.webp',
    badge_text: '13项特权',
    benefit_line1: 'VIP+金币视频',
    benefit_line2: '全部永久免费',
    benefit_line3: 'AI脱衣10次',
    price: 200,
    original_price: 400,
    sort_order: 2
  },
  {
    id: 3,
    level: 1,
    name: '至尊会员',
    display_title: '至尊',
    background_image: '/images/vip/card_supreme.webp',
    badge_text: '',
    benefit_line1: 'VIP视频',
    benefit_line2: '30天免费',
    benefit_line3: 'AI脱衣5次',
    benefit_line4: '赠送金币',
    price: 100,
    original_price: 200,
    sort_order: 3
  }
]

// 默认特权数据
const getDefaultPrivileges = () => [
  { id: 1, name: '至尊VIP标识', description: '专属VIP图标 至尊特权', icon: '/images/vip/ic_vip_badge.webp', min_level: 1, sort_order: 1 },
  { id: 2, name: '金币视频免费', description: '全网金币视频免费看', icon: '/images/vip/ic_coin_free.webp', min_level: 1, sort_order: 2 },
  { id: 3, name: 'AI脱衣*15次', description: 'AI科技 女神秒变母狗（价值300元）', icon: '/images/vip/ic_ai.webp', min_level: 1, sort_order: 3 },
  { id: 4, name: '每日下载50', description: '精彩视频 离线下载 告别卡顿', icon: '/images/vip/ic_download.webp', min_level: 1, sort_order: 4 },
  { id: 5, name: '私信半价', description: '私信功能半价使用', icon: '/images/vip/ic_message.webp', min_level: 1, sort_order: 5 },
  { id: 6, name: '头像特权', description: '解锁修改头像', icon: '/images/vip/ic_avatar.webp', min_level: 1, sort_order: 6 },
  { id: 7, name: 'VIP视频免费', description: '百万精选VIP视频免费看', icon: '/images/vip/ic_vip_video.webp', min_level: 2, sort_order: 7 },
  { id: 8, name: '直播免费看', description: '淫女在线直播永久免费看', icon: '/images/vip/ic_live.webp', min_level: 2, sort_order: 8 },
  { id: 9, name: '裸聊解锁', description: '真人裸聊1对1 调教小母狗', icon: '/images/vip/ic_chat.webp', min_level: 2, sort_order: 9 },
  { id: 10, name: '群聊解锁', description: '解锁专属加入群聊特权', icon: '/images/vip/ic_group.webp', min_level: 2, sort_order: 10 },
  { id: 11, name: '每日下载100', description: '精彩视频 离线缓存 告别卡顿', icon: '/images/vip/ic_download.webp', min_level: 3, sort_order: 11 },
  { id: 12, name: '私信免费', description: '免费私信1V1 畅享交友约炮', icon: '/images/vip/ic_message.webp', min_level: 3, sort_order: 12 },
  { id: 13, name: '社区优先审核', description: '社区发帖 优先审核', icon: '/images/vip/ic_community.webp', min_level: 3, sort_order: 13 },
  { id: 14, name: '评论免审', description: '精彩评论 免审通过', icon: '/images/vip/ic_comment.webp', min_level: 3, sort_order: 14 },
  { id: 15, name: '高清线路', description: '专属线路 拒绝卡顿', icon: '/images/vip/ic_hd.webp', min_level: 3, sort_order: 15 },
  { id: 16, name: '专属客服', description: '24小时1V1 专属客服', icon: '/images/vip/ic_service.webp', min_level: 3, sort_order: 16 },
  { id: 17, name: '会员福利群', description: '专属官方福利群', icon: '/images/vip/ic_welfare.webp', min_level: 3, sort_order: 17 },
  { id: 18, name: '昵称特权', description: '解锁修改昵称', icon: '/images/vip/ic_nickname.webp', min_level: 3, sort_order: 18 }
]

const formatDate = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

onMounted(() => {
  fetchVipCards()
  fetchPrivileges()
  fetchRecords()
})
</script>

<style lang="scss" scoped>
.vip-page {
  min-height: 100vh;
  min-height: 100dvh;
  background: 
    url('/images/backgrounds/wallet_coin_bg_1.webp') no-repeat center top / 100% auto,
    linear-gradient(180deg, #1a0a2e 0%, #0d0d1a 30%, #0a0a0a 100%);
  padding-bottom: calc(env(safe-area-inset-bottom) + 180px);
}

// 顶部导航
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  padding-top: calc(env(safe-area-inset-top, 12px) + 12px);
  
  .back-btn {
    width: 32px;
    height: 32px;
    background: transparent;
    border: none;
    color: #fff;
    font-size: 28px;
    cursor: pointer;
  }
  
  h1 {
    font-size: 18px;
    color: #fff;
    margin: 0;
    font-weight: 500;
  }
  
  .record-btn {
    background: none;
    border: none;
    color: rgba(255, 255, 255, 0.7);
    font-size: 14px;
    cursor: pointer;
  }
}

// 用户信息
.user-info-section {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  
  .avatar-wrapper {
    flex-shrink: 0;
    
    .avatar-container {
      width: 56px;
      height: 56px;
      border-radius: 50%;
      padding: 3px;
      background: linear-gradient(135deg, rgba(139, 92, 246, 0.5), rgba(99, 102, 241, 0.5));
      display: flex;
      align-items: center;
      justify-content: center;
      
      &.is-vip {
        background: linear-gradient(135deg, #fbbf24, #f59e0b, #d97706);
        box-shadow: 0 0 12px rgba(251, 191, 36, 0.4);
      }
      
      .user-avatar {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        object-fit: cover;
        background: #1a1a2e;
      }
    }
  }
  
  .user-details {
    flex: 1;
    
    .nickname-row {
      display: flex;
      align-items: center;
      gap: 8px;
      
      .username {
    font-size: 16px;
        font-weight: 600;
        background: linear-gradient(135deg, #ffd700 0%, #ffec8b 30%, #daa520 60%, #ffd700 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }
      
      .vip-level-badge {
        height: 18px;
        width: auto;
      }
    }
    
    .vip-status {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.6);
      margin-top: 4px;
      
      .open-vip-link {
        color: #a855f7;
        margin-left: 8px;
        text-decoration: none;
      }
      
      .benefit-text {
        margin-left: 8px;
        color: rgba(255, 255, 255, 0.5);
      }
    }
  }
}

// VIP卡片区域
.vip-cards-section {
  padding: 0 0 0 12px;
  margin-bottom: 12px;
  
  .cards-scroll {
    display: flex;
    gap: 8px;
    overflow-x: auto;
    padding-right: 12px;
    padding-bottom: 8px;
    scroll-snap-type: x mandatory;
    -webkit-overflow-scrolling: touch;
    
    &::-webkit-scrollbar {
      display: none;
    }
  }
}

.vip-card {
  flex-shrink: 0;
  width: 160px;
  height: 220px;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
  cursor: pointer;
  scroll-snap-align: start;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  
  &.selected {
    border-color: #a855f7;
    box-shadow: 0 0 16px rgba(168, 85, 247, 0.4);
  }
  
  .card-bg {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

// 简洁卡片网格区域
.simple-cards-section {
  padding: 12px;
  background: linear-gradient(180deg, #1a0a2e 0%, #0d0d1a 100%);
  
  .simple-cards-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 6px;
  }
}

.simple-card {
  background: linear-gradient(180deg, #2d1b4e 0%, #1a1030 100%);
  border-radius: 8px;
  padding: 10px 4px 8px;
  text-align: center;
      position: relative;
      cursor: pointer;
  border: 1px solid rgba(139, 92, 246, 0.2);
  transition: all 0.3s ease;
  
  &.selected {
    border-color: #a855f7;
    background: linear-gradient(180deg, #3d2560 0%, #251540 100%);
    box-shadow: 0 0 16px rgba(168, 85, 247, 0.35);
  }
  
  &:active {
    transform: scale(0.98);
  }
  
  .simple-badge {
          position: absolute;
    top: 0;
          left: 50%;
          transform: translateX(-50%);
    background: linear-gradient(90deg, #a855f7, #7c3aed);
    color: #fff;
    font-size: 8px;
    font-weight: 600;
    padding: 1px 8px;
    border-radius: 0 0 5px 5px;
          white-space: nowrap;
    letter-spacing: 0.3px;
    
    // 不同颜色主题
    &.badge-red {
      background: linear-gradient(90deg, #ef4444, #dc2626);
    }
    &.badge-orange {
      background: linear-gradient(90deg, #f97316, #ea580c);
    }
    &.badge-purple {
      background: linear-gradient(90deg, #a855f7, #7c3aed);
    }
    &.badge-blue {
      background: linear-gradient(90deg, #3b82f6, #2563eb);
    }
    &.badge-green {
      background: linear-gradient(90deg, #22c55e, #16a34a);
    }
    &.badge-pink {
      background: linear-gradient(90deg, #ec4899, #db2777);
    }
  }
  
  .simple-card-name {
    font-size: 12px;
    color: #fff;
    font-weight: 600;
    margin-top: 10px;
    margin-bottom: 6px;
    letter-spacing: 0.3px;
  }
  
  .simple-card-price {
    display: flex;
    align-items: baseline;
    justify-content: center;
    margin-bottom: 4px;
        
        .currency {
      font-size: 12px;
      color: #c084fc;
      font-weight: 500;
        }
        
        .amount {
      font-size: 26px;
      font-weight: 700;
      color: #c084fc;
      line-height: 1;
      font-family: 'DIN Alternate', 'Roboto Condensed', sans-serif;
    }
  }
  
  .simple-card-desc {
    font-size: 10px;
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 4px;
    line-height: 1.3;
  }
  
  .simple-daily-cost {
    font-size: 9px;
    color: rgba(192, 132, 252, 0.7);
    margin-top: 2px;
  }
}

// 会员特权区域
.privileges-section {
  background: url('/images/backgrounds/vip_recommend.webp') no-repeat center top;
  background-size: 100% auto;
  border-radius: 20px 20px 0 0;
  margin: 0 12px;
  padding: 40px 16px 24px;
  position: relative;
}

.privileges-list {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 0;
  
  .privilege-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 12px 0;
    border-bottom: 1px solid rgba(139, 92, 246, 0.15);
    
    &:last-child {
      border-bottom: none;
    }
    
    .privilege-icon {
      width: 44px;
      height: 44px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      
      img {
        width: 44px;
        height: 44px;
        object-fit: contain;
      }
    }
    
    .privilege-info {
      flex: 1;
      
      .privilege-name {
        font-size: 13px;
        font-weight: 600;
        margin-bottom: 4px;
        background: linear-gradient(90deg, #e9d5ff 0%, #a855f7 40%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }
      
      .privilege-desc {
        font-size: 12px;
        background: linear-gradient(90deg, #c084fc 0%, #a855f7 50%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1.4;
      }
    }
  }
}

// 提示文字区域（页面内容底部）
.tips-section {
  padding: 16px;
  margin-bottom: 120px;
  
  .tips {
    font-size: 13px;
    color: #fff;
    line-height: 1.7;
    
    .link {
      color: #c084fc;
      text-decoration: none;
      font-weight: 500;
    }
  }
}

// 底部支付区域（固定）
.pay-section {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px 16px;
  padding-bottom: calc(env(safe-area-inset-bottom) + 12px);
  background: transparent;
  z-index: 100;
  
  .pay-btn {
    width: 80%;
    margin: 0 auto;
    display: block;
    padding: 12px;
    background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
    border: none;
    border-radius: 24px;
    color: #fff;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:active {
      transform: scale(0.98);
      opacity: 0.9;
    }
    
    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
  
  .support-text {
    text-align: center;
    font-size: 14px;
    color: #fff;
    margin-top: 14px;
    
    .link {
      color: #c084fc;
      text-decoration: none;
      font-weight: 500;
    }
  }
}

// 记录弹窗
.records-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: flex-end;
  z-index: 200;
  
  .modal-content {
    width: 100%;
    max-height: 60vh;
    background: #1a1a2e;
    border-radius: 20px 20px 0 0;
    display: flex;
    flex-direction: column;
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    
    span {
      font-size: 18px;
      font-weight: 600;
      color: #fff;
    }
    
    .close-btn {
      width: 30px;
      height: 30px;
      background: rgba(255, 255, 255, 0.1);
      border: none;
      border-radius: 50%;
      color: #fff;
      font-size: 20px;
      cursor: pointer;
    }
  }
  
  .modal-body {
      flex: 1;
    overflow-y: auto;
    padding: 0 20px;
  }
  
  .record-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    
    .record-info {
      display: flex;
      flex-direction: column;
      gap: 4px;
      
      .record-name {
        font-size: 14px;
        color: #fff;
      }
      
      .record-time {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.4);
      }
    }
    
    .record-amount {
      font-size: 16px;
      font-weight: 600;
      color: #a855f7;
    }
  }
  
  .empty-state {
    text-align: center;
    padding: 40px;
    color: rgba(255, 255, 255, 0.4);
  }
}

// 支付方式弹窗
.payment-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 20px;
  
  .payment-modal-content {
    width: 100%;
    max-width: 360px;
    background: linear-gradient(180deg, #1a1030 0%, #0d0d1a 100%);
    border-radius: 16px;
    border: 1px solid rgba(139, 92, 246, 0.3);
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    
    span {
      font-size: 18px;
      font-weight: 600;
      color: #fff;
    }
    
    .close-btn {
      width: 30px;
      height: 30px;
      background: rgba(255, 255, 255, 0.1);
      border: none;
      border-radius: 50%;
      color: #fff;
      font-size: 20px;
      cursor: pointer;
    }
  }
  
  .modal-body {
    padding: 20px;
  }
  
  .payment-methods {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 20px;
  }
  
  .payment-method-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 16px;
    background: rgba(139, 92, 246, 0.1);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.3s ease;
    
    &.selected {
      background: rgba(139, 92, 246, 0.2);
      border-color: #a855f7;
    }
    
    .method-icon {
      font-size: 24px;
    }
    
    .method-name {
      flex: 1;
      font-size: 15px;
      color: #fff;
    }
    
    .check-icon {
      color: #a855f7;
      font-size: 18px;
      font-weight: bold;
    }
  }
  
  .payment-amount {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    margin-bottom: 16px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    
    span {
      color: rgba(255, 255, 255, 0.7);
      font-size: 14px;
    }
    
    .amount {
      font-size: 22px;
      font-weight: bold;
      color: #c084fc;
    }
  }
  
  .confirm-pay-btn {
    width: 100%;
    padding: 14px;
    background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
    border: none;
    border-radius: 24px;
    color: #fff;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:active {
      transform: scale(0.98);
      opacity: 0.9;
    }
    
    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
}

// 响应式
@media (min-width: 768px) {
  .vip-page {
    max-width: 600px;
    margin: 0 auto;
  }
  
  .vip-card {
    width: 220px;
    height: 300px;
  }
  
  .page-header {
    padding: 20px 30px;
    h1 { font-size: 24px; }
  }
  
  .vip-card {
    padding: 30px;
    
    .card-bg {
      padding: 50px 30px;
      border-radius: 24px;
      
      .crown { font-size: 60px; }
      h2 { font-size: 28px; }
      p { font-size: 16px; }
    }
  }
  
  .benefits {
    padding: 30px;
    
    h3 { font-size: 18px; }
    
    .benefit-grid {
      gap: 20px;
      
      .benefit-item {
        padding: 20px;
        
        .icon { font-size: 36px; }
        span { font-size: 14px; }
      }
    }
  }
  
  .plans {
    padding: 30px;
    
    h3 { font-size: 18px; }
    
    .plan-list {
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      
      .plan-item {
        padding: 24px 15px;
      }
    }
  }
  
  .pay-section {
    padding: 30px;
    
    .pay-btn {
      max-width: 400px;
      height: 56px;
      font-size: 20px;
    }

  }
  
  .payment-methods {
    padding: 30px;
    
    .method-list {
      max-width: 400px;
      margin: 0 auto;
    }
  }
}

@media (max-width: 374px) {
  .vip-card {
    padding: 15px;
    
    .card-bg {
      padding: 30px 20px;
      
      .crown { font-size: 40px; }
      h2 { font-size: 20px; }
    }
  }
  
  .benefits {
    padding: 15px;
    
    .benefit-grid {
      gap: 10px;
      
      .benefit-item {
        padding: 12px 8px;
        
        .icon { font-size: 24px; }
        span { font-size: 11px; }
      }
    }
  }
  
  .plans {
    padding: 15px;
    
    .plan-list .plan-item {
      padding: 15px 10px;
      
      .plan-price .amount { font-size: 24px; }
    }
  }
  
  .pay-section .pay-btn {
    width: 90%;
    height: 46px;
    font-size: 16px;
  }
}
</style>
