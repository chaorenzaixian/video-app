/**
 * 视频购买/试看逻辑
 */
import { ref, computed } from 'vue'
import api from '@/utils/api'

export function usePurchase(video, isVip, userVipLevel) {
  const hasPurchased = ref(false)
  const needsPurchase = ref(false)
  const isTrialEnded = ref(false)
  const isVipFree = ref(false)
  const purchasing = ref(false)
  const userCoins = ref(0)
  const currentPlayTime = ref(0)
  
  // 显示价格（VIP折扣）
  const displayPrice = computed(() => {
    const v = video.value
    if (!v) return 0
    
    const basePrice = v.coin_price || 0
    if (!isVip.value) return basePrice
    
    // VIP折扣
    const discount = v.vip_discount || 1
    return Math.ceil(basePrice * discount)
  })
  
  // 试看倒计时显示
  const showTrialCountdown = computed(() => {
    if (!needsPurchase.value || hasPurchased.value || isTrialEnded.value || isVipFree.value) {
      return false
    }
    const trialLimit = video.value?.free_preview_seconds || 0
    if (trialLimit <= 0) return false
    return currentPlayTime.value >= (trialLimit - 10) && currentPlayTime.value < trialLimit
  })
  
  const remainingTrialTime = computed(() => {
    const trialLimit = video.value?.free_preview_seconds || 30
    return Math.max(0, Math.ceil(trialLimit - currentPlayTime.value))
  })
  
  const checkVideoPurchase = async (abortSignal = null) => {
    const v = video.value
    if (!v) return
    
    // 重置状态
    isVipFree.value = false
    isTrialEnded.value = false
    hasPurchased.value = false
    needsPurchase.value = false
    currentPlayTime.value = 0
    
    // 免费视频
    if (!v.pay_type || v.pay_type === 'free') {
      needsPurchase.value = false
      hasPurchased.value = true
      return
    }
    
    // VIP免费视频
    if (v.pay_type === 'vip_free' && isVip.value) {
      needsPurchase.value = false
      hasPurchased.value = true
      isVipFree.value = true
      return
    }
    
    // 黄金至尊及以上全免费
    if (userVipLevel.value >= 5) {
      needsPurchase.value = false
      hasPurchased.value = true
      isVipFree.value = true
      return
    }
    
    // VIP等级免费
    if (v.vip_free_level > 0 && userVipLevel.value >= v.vip_free_level) {
      needsPurchase.value = false
      hasPurchased.value = true
      isVipFree.value = true
      return
    }
    
    // 需要付费，检查是否已购买
    needsPurchase.value = true
    
    try {
      const res = await api.get(`/coins/purchase/video/${v.id}/check`, { signal: abortSignal })
      const data = res.data || res
      hasPurchased.value = data.purchased === true || data.can_watch === true
      
      if (data.is_vip_free) {
        isVipFree.value = true
        hasPurchased.value = true
        needsPurchase.value = false
      }
    } catch (error) {
      if (error.name !== 'CanceledError' && error.name !== 'AbortError') {
        console.log('检查购买状态失败:', error)
      }
      hasPurchased.value = false
    }
  }
  
  const fetchUserCoins = async (abortSignal = null) => {
    try {
      const res = await api.get('/coins/balance', { signal: abortSignal })
      const data = res.data || res
      userCoins.value = data.balance || 0
    } catch (error) {
      if (error.name !== 'CanceledError' && error.name !== 'AbortError') {
        console.log('获取金币余额失败')
      }
      userCoins.value = 0
    }
  }
  
  const purchaseVideo = async () => {
    if (purchasing.value) return { success: false }
    
    // 先获取最新余额
    await fetchUserCoins()
    
    if (userCoins.value < displayPrice.value) {
      return { success: false, error: 'INSUFFICIENT_BALANCE' }
    }
    
    purchasing.value = true
    
    try {
      const res = await api.post(`/coins/purchase/video/${video.value.id}`)
      const data = res.data || res
      
      if (data.success) {
        hasPurchased.value = true
        isTrialEnded.value = false
        userCoins.value = data.balance_after || (userCoins.value - displayPrice.value)
        return { success: true, data }
      } else {
        return { success: false, error: data.message || '购买失败' }
      }
    } catch (error) {
      console.error('购买失败:', error)
      return { 
        success: false, 
        error: error.response?.data?.detail || '购买失败，请重试' 
      }
    } finally {
      purchasing.value = false
    }
  }
  
  const checkTrialTime = (currentTime, onTrialEnded) => {
    if (!needsPurchase.value || hasPurchased.value || isVipFree.value) return false
    
    currentPlayTime.value = currentTime
    const trialLimit = video.value?.free_preview_seconds || 30
    
    if (currentTime >= trialLimit) {
      isTrialEnded.value = true
      onTrialEnded?.()
      return true
    }
    return false
  }
  
  const resetTrialState = () => {
    isTrialEnded.value = false
    currentPlayTime.value = 0
  }
  
  return {
    hasPurchased,
    needsPurchase,
    isTrialEnded,
    isVipFree,
    purchasing,
    userCoins,
    currentPlayTime,
    displayPrice,
    showTrialCountdown,
    remainingTrialTime,
    
    checkVideoPurchase,
    fetchUserCoins,
    purchaseVideo,
    checkTrialTime,
    resetTrialState
  }
}
