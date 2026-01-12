import { ref, computed } from 'vue'
import api from '@/utils/api'
import { VIP_LEVEL_ICONS, VIP_LEVEL_BENEFITS } from '@/constants/vip'

export function useVipData(signal) {
  const vipCards = ref([])
  const selectedCard = ref(null)
  const vipPrivileges = ref([])
  const paymentRecords = ref([])
  const isProcessing = ref(false)

  // 当前选中卡片的特权
  const currentPrivileges = computed(() => {
    if (!selectedCard.value) return []
    const privilegeIds = selectedCard.value.privilege_ids
    if (privilegeIds && privilegeIds.length > 0) {
      return privilegeIds.map(id => vipPrivileges.value.find(p => p.id === id)).filter(p => p != null)
    }
    return []
  })

  // VIP等级图标
  const getVipLevelIcon = (level) => VIP_LEVEL_ICONS[level] || ''

  // 获取等级对应的权益描述
  const getLevelBenefit = (level) => VIP_LEVEL_BENEFITS[level] || 'VIP特权'

  // 获取角标颜色类名
  const getBadgeColorClass = (index) => {
    const colors = ['badge-red', 'badge-orange', 'badge-purple', 'badge-blue', 'badge-green', 'badge-pink']
    return colors[index % colors.length]
  }

  // 获取VIP卡片列表
  const fetchVipCards = async () => {
    try {
      const res = await api.get('/vip/cards', { signal })
      vipCards.value = res.data || []
      if (vipCards.value.length > 0 && !selectedCard.value) {
        selectedCard.value = vipCards.value[0]
      }
    } catch (error) {
      if (error.name !== 'CanceledError' && error.name !== 'AbortError') {
        vipCards.value = getDefaultCards()
        selectedCard.value = vipCards.value[0]
      }
    }
  }

  // 获取VIP特权列表
  const fetchPrivileges = async () => {
    try {
      const res = await api.get('/vip/privileges', { signal })
      vipPrivileges.value = res.data || []
    } catch (error) {
      if (error.name !== 'CanceledError' && error.name !== 'AbortError') {
        vipPrivileges.value = getDefaultPrivileges()
      }
    }
  }

  // 获取充值记录
  const fetchRecords = async () => {
    try {
      const res = await api.get('/vip/records', { signal })
      paymentRecords.value = res.data || []
    } catch (error) {
      if (error.name !== 'CanceledError' && error.name !== 'AbortError') {
        console.error('获取充值记录失败:', error)
      }
    }
  }

  // 选择卡片
  const selectCard = (card, cardsScroll) => {
    selectedCard.value = card
    const index = vipCards.value.findIndex(c => c.id === card.id)
    if (index !== -1 && cardsScroll) {
      const cardWidth = 168
      cardsScroll.scrollTo({ left: index * cardWidth, behavior: 'smooth' })
    }
  }

  return {
    vipCards,
    selectedCard,
    vipPrivileges,
    paymentRecords,
    isProcessing,
    currentPrivileges,
    getVipLevelIcon,
    getLevelBenefit,
    getBadgeColorClass,
    fetchVipCards,
    fetchPrivileges,
    fetchRecords,
    selectCard
  }
}

// 默认卡片数据
function getDefaultCards() {
  return [
    { id: 1, level: 3, name: '尊享限定卡', background_image: '/images/vip/card_premium.webp', badge_text: '15项特权', price: 200, original_price: 500, duration_days: 0 },
    { id: 2, level: 2, name: '尊享永久卡', background_image: '/images/vip/card_forever.webp', badge_text: '13项特权', price: 200, original_price: 400, duration_days: 0 },
    { id: 3, level: 1, name: '至尊会员', background_image: '/images/vip/card_supreme.webp', badge_text: '', price: 100, original_price: 200, duration_days: 30 }
  ]
}

// 默认特权数据
function getDefaultPrivileges() {
  return [
    { id: 1, name: '至尊VIP标识', description: '专属VIP图标 至尊特权', icon: '/images/vip/ic_vip_badge.webp' },
    { id: 2, name: '金币视频免费', description: '全网金币视频免费看', icon: '/images/vip/ic_coin_free.webp' },
    { id: 3, name: 'AI脱衣*15次', description: 'AI科技 女神秒变母狗', icon: '/images/vip/ic_ai.webp' },
    { id: 4, name: '每日下载50', description: '精彩视频 离线下载', icon: '/images/vip/ic_download.webp' },
    { id: 5, name: '私信半价', description: '私信功能半价使用', icon: '/images/vip/ic_message.webp' },
    { id: 6, name: '头像特权', description: '解锁修改头像', icon: '/images/vip/ic_avatar.webp' }
  ]
}
