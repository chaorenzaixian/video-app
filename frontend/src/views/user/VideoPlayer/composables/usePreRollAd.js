/**
 * 前贴广告逻辑
 */
import { ref, computed } from 'vue'
import api from '@/utils/api'

export function usePreRollAd(isVip, timers) {
  const adVideoRef = ref(null)
  const preRollAd = ref(null)
  const showPreRollAd = ref(false)
  const adCountdown = ref(5)
  const canSkipAd = ref(false)
  const adPlayed = ref(false)
  
  let adTimerId = null
  
  const fetchPreRollAd = async () => {
    // VIP用户不显示广告
    if (isVip.value) {
      console.log('[Ad] VIP user, skip ad')
      return
    }
    
    try {
      const res = await api.get('/ads', {
        params: { position: 'video_pre', limit: 1 }
      })
      const ads = res.data || res || []
      if (ads.length > 0) {
        preRollAd.value = ads[0]
        console.log('[Ad] Loaded pre-roll ad:', preRollAd.value.title)
      }
    } catch (error) {
      console.log('[Ad] Failed to load ad:', error)
    }
  }
  
  const startPreRollAd = () => {
    if (!preRollAd.value || adPlayed.value || isVip.value) {
      return false
    }
    
    showPreRollAd.value = true
    adCountdown.value = preRollAd.value.duration || 5
    adPlayed.value = true
    canSkipAd.value = false
    
    console.log('[Ad] Starting pre-roll ad')
    return true
  }
  
  const onAdTimeUpdate = () => {
    if (adVideoRef.value) {
      const currentTime = adVideoRef.value.currentTime
      const duration = preRollAd.value?.duration || 5
      const remaining = Math.max(0, Math.ceil(duration - currentTime))
      adCountdown.value = remaining
      
      if (remaining <= 0) {
        canSkipAd.value = true
      }
    }
  }
  
  const onAdCanPlay = () => {
    if (adVideoRef.value) {
      adVideoRef.value.play().catch(() => {
        adVideoRef.value.muted = true
        adVideoRef.value.play()
      })
    }
  }
  
  const onAdEnded = () => {
    console.log('[Ad] Ad video ended, show close button')
    canSkipAd.value = true
    adCountdown.value = 0
    
    // 循环播放直到用户关闭
    if (adVideoRef.value && preRollAd.value?.ad_type === 'video') {
      adVideoRef.value.currentTime = 0
      adVideoRef.value.play().catch(() => {})
    }
  }
  
  const skipAd = (onComplete) => {
    console.log('[Ad] Close ad by user')
    showPreRollAd.value = false
    
    if (adTimerId) {
      timers.clearInterval(adTimerId)
      adTimerId = null
    }
    
    if (adVideoRef.value) {
      adVideoRef.value.pause()
    }
    
    onComplete?.()
  }
  
  const onAdClick = async () => {
    if (preRollAd.value?.id) {
      try {
        await api.post(`/ads/${preRollAd.value.id}/click`)
      } catch (e) {
        // 忽略错误
      }
    }
  }
  
  const onAdImageLoad = () => {
    const duration = preRollAd.value?.duration || 5
    adCountdown.value = duration
    canSkipAd.value = false
    
    adTimerId = timers.setInterval(() => {
      adCountdown.value--
      if (adCountdown.value <= 0) {
        timers.clearInterval(adTimerId)
        adTimerId = null
        canSkipAd.value = true
      }
    }, 1000)
  }
  
  const onAdImageClick = () => {
    if (preRollAd.value?.target_url) {
      onAdClick()
      window.open(preRollAd.value.target_url, '_blank')
    }
  }
  
  const cleanup = () => {
    if (adTimerId) {
      timers.clearInterval(adTimerId)
      adTimerId = null
    }
  }
  
  return {
    adVideoRef,
    preRollAd,
    showPreRollAd,
    adCountdown,
    canSkipAd,
    adPlayed,
    
    fetchPreRollAd,
    startPreRollAd,
    onAdTimeUpdate,
    onAdCanPlay,
    onAdEnded,
    skipAd,
    onAdClick,
    onAdImageLoad,
    onAdImageClick,
    cleanup
  }
}
