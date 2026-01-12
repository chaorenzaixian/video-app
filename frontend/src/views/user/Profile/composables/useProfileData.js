import { ref, computed } from 'vue'
import api from '@/utils/api'
import axios from 'axios'
import { getAvatarUrl } from '@/utils/avatar'
import { formatDate } from '@/utils/format'
import { getVipLevelIcon, getVipLevelName } from '@/constants/vip'

export function useProfileData(signal) {
  const user = ref({
    id: '', username: '', nickname: '', avatar: '', is_vip: false,
    vip_level: 0, vip_level_name: '非VIP', vip_expire_date: null
  })
  const iconAds = ref([])
  const isLoading = ref(true)
  const unreadMessageCount = ref(0)

  // 头像URL
  const avatarUrl = computed(() => getAvatarUrl(user.value.avatar, user.value.id))

  // VIP等级图标
  const vipLevelIcon = computed(() => getVipLevelIcon(user.value.vip_level))

  // VIP等级名称
  const vipLevelName = computed(() => user.value.vip_level_name || getVipLevelName(user.value.vip_level))

  // 格式化VIP到期时间
  const formattedExpireDate = computed(() => {
    if (!user.value.vip_expire_date) return ''
    return formatDate(user.value.vip_expire_date)
  })

  // 初始化用户数据
  const initUserData = (storeUser) => {
    if (storeUser) {
      user.value = {
        id: storeUser.id || '',
        username: storeUser.username || '',
        nickname: storeUser.nickname || storeUser.username || '',
        avatar: storeUser.avatar || '',
        is_vip: storeUser.is_vip || false,
        vip_level: storeUser.vip_level || 0,
        vip_level_name: storeUser.vip_level_name || '非VIP',
        vip_expire_date: storeUser.vip_expire_date || null
      }
    }
    isLoading.value = false
  }

  // 获取用户VIP信息
  const fetchUserVipInfo = async () => {
    if (!user.value.id) return
    try {
      const res = await api.get('/users/me', { signal })
      const data = res.data || res
      if (data) {
        user.value.is_vip = data.is_vip || false
        user.value.vip_level = data.vip_level || 0
        user.value.vip_level_name = data.vip_level_name || '非VIP'
        user.value.vip_expire_date = data.vip_expire_date || null
      }
    } catch (error) {
      if (error.name !== 'CanceledError' && error.name !== 'AbortError') {
        console.error('获取用户VIP信息失败:', error)
      }
    }
  }

  // 获取图标广告
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
      const res = await api.get('/notifications/unread-count', { signal })
      unreadMessageCount.value = res.data?.total || 0
    } catch (error) {
      console.log('获取未读消息数量失败')
    }
  }

  return {
    user, iconAds, isLoading, unreadMessageCount,
    avatarUrl, vipLevelIcon, vipLevelName, formattedExpireDate,
    initUserData, fetchUserVipInfo, fetchIconAds, fetchUnreadCount
  }
}
