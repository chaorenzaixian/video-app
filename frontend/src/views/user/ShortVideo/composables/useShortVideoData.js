/**
 * 短视频数据获取逻辑
 */
import { ref } from 'vue'
import api from '@/utils/api'

export function useShortVideoData(abortSignal) {
  const videos = ref([])
  const loading = ref(false)
  const page = ref(1)
  const hasMore = ref(true)

  // 获取短视频列表
  const fetchVideos = async (reset = false) => {
    if (loading.value || (!hasMore.value && !reset)) return
    
    loading.value = true
    
    try {
      if (reset) {
        page.value = 1
        videos.value = []
      }
      
      const res = await api.get('/shorts', {
        params: { page: page.value, limit: 10 },
        signal: abortSignal
      })
      
      const data = res.data || res
      if (data.items && data.items.length > 0) {
        videos.value = reset ? data.items : [...videos.value, ...data.items]
        hasMore.value = data.has_more
        page.value++
        return data.items
      } else {
        hasMore.value = false
        return []
      }
    } catch (error) {
      if (error.name !== 'CanceledError' && error.name !== 'AbortError') {
        console.error('获取短视频失败:', error)
      }
      return []
    } finally {
      loading.value = false
    }
  }

  // 获取指定视频
  const fetchVideoById = async (videoId) => {
    try {
      const res = await api.get(`/shorts/${videoId}`, { signal: abortSignal })
      return res.data || res
    } catch (error) {
      if (error.name !== 'CanceledError' && error.name !== 'AbortError') {
        console.error('获取指定短视频失败:', error)
      }
      return null
    }
  }

  return {
    videos,
    loading,
    page,
    hasMore,
    fetchVideos,
    fetchVideoById
  }
}
