/**
 * 短视频操作逻辑（点赞、收藏、关注等）
 */
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

export function useShortVideoActions(timers) {
  const actionLocks = ref({})
  const showLikeAnimation = ref(false)
  const likeAnimationIndex = ref(-1)

  // 点赞
  const handleLike = async (video, index) => {
    if (!video) return
    
    const lockKey = `like_${video.id}`
    if (actionLocks.value[lockKey]) return
    actionLocks.value[lockKey] = true
    
    const wasLiked = video.is_liked
    const oldCount = video.like_count || 0
    
    video.is_liked = !wasLiked
    video.like_count = wasLiked ? Math.max(0, oldCount - 1) : oldCount + 1
    
    try {
      const res = await api.post(`/shorts/${video.id}/like`)
      const data = res.data || res
      video.is_liked = data.liked
      video.like_count = data.like_count
    } catch (error) {
      video.is_liked = wasLiked
      video.like_count = oldCount
      ElMessage.error('操作失败')
    } finally {
      actionLocks.value[lockKey] = false
    }
  }

  // 收藏
  const handleFavorite = async (video, index) => {
    if (!video) return
    
    const lockKey = `favorite_${video.id}`
    if (actionLocks.value[lockKey]) return
    actionLocks.value[lockKey] = true
    
    const wasFavorited = video.is_favorited
    const oldCount = video.favorite_count || 0
    
    video.is_favorited = !wasFavorited
    video.favorite_count = wasFavorited ? Math.max(0, oldCount - 1) : oldCount + 1
    
    try {
      const res = await api.post(`/shorts/${video.id}/favorite`)
      const data = res.data || res
      video.is_favorited = data.favorited
      video.favorite_count = data.favorite_count
      ElMessage.success(data.favorited ? '收藏成功' : '已取消收藏')
    } catch (error) {
      video.is_favorited = wasFavorited
      video.favorite_count = oldCount
      ElMessage.error('操作失败')
    } finally {
      actionLocks.value[lockKey] = false
    }
  }

  // 关注
  const handleFollow = async (video) => {
    const uploaderId = video.uploader_id
    if (!uploaderId) return
    
    const lockKey = `follow_${uploaderId}`
    if (actionLocks.value[lockKey]) return
    actionLocks.value[lockKey] = true
    
    try {
      await api.post(`/users/${uploaderId}/follow`)
      video.is_followed = true
      ElMessage.success('关注成功')
    } catch (error) {
      if (error.response?.status === 401) {
        ElMessage.warning('请先登录')
      } else if (error.response?.status === 400) {
        video.is_followed = true
      } else {
        ElMessage.error(error.response?.data?.detail || '关注失败')
      }
    } finally {
      if (timers) {
        timers.setTimeout(() => {
          actionLocks.value[lockKey] = false
        }, 500)
      } else {
        setTimeout(() => {
          actionLocks.value[lockKey] = false
        }, 500)
      }
    }
  }

  // 双击点赞动画
  const showLikeAnimationEffect = (index) => {
    likeAnimationIndex.value = index
    showLikeAnimation.value = true
    const clearFn = timers ? timers.setTimeout : setTimeout
    clearFn(() => {
      showLikeAnimation.value = false
    }, 1000)
  }

  return {
    actionLocks,
    showLikeAnimation,
    likeAnimationIndex,
    handleLike,
    handleFavorite,
    handleFollow,
    showLikeAnimationEffect
  }
}
