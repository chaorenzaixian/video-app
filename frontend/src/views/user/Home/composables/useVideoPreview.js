/**
 * 视频预览逻辑（悬停播放）
 */
import { ref } from 'vue'

export function useVideoPreview(videoCleanup, timers) {
  // 预览视频引用
  const previewRefs = ref({})
  // 当前正在预览的视频ID
  const previewingVideoId = ref(null)
  // 触摸模式
  const isTouchMode = ref(false)
  // 预览定时器ID
  let previewTimerId = null

  // 设置预览视频ref
  const setPreviewRef = (id, el) => {
    if (el) {
      previewRefs.value[id] = el
      if (videoCleanup) {
        videoCleanup.registerVideo(`preview_${id}`, el)
      }
    }
  }

  // 检查视频是否正在预览
  const isPreviewPlaying = (videoId) => {
    return previewingVideoId.value === videoId
  }

  // 播放预览
  const playPreview = (video) => {
    // 停止其他预览
    if (previewingVideoId.value && previewingVideoId.value !== video.id) {
      const oldVideoEl = previewRefs.value[previewingVideoId.value]
      if (oldVideoEl) {
        oldVideoEl.pause()
        oldVideoEl.currentTime = 0
      }
    }
    
    previewingVideoId.value = video.id
    const videoEl = previewRefs.value[video.id]
    if (videoEl) {
      videoEl.currentTime = 0
      videoEl.play().catch(err => {
        console.log('预览播放失败:', err)
      })
    }
  }

  // 停止当前预览
  const stopCurrentPreview = () => {
    if (previewingVideoId.value) {
      const videoEl = previewRefs.value[previewingVideoId.value]
      if (videoEl) {
        videoEl.pause()
        videoEl.currentTime = 0
      }
      previewingVideoId.value = null
    }
  }

  // 开始预览 (PC鼠标悬停)
  const startPreview = (video) => {
    if (!video.preview_url || isTouchMode.value) return
    
    previewingVideoId.value = video.id
    
    if (previewTimerId && timers) timers.clearTimeout(previewTimerId)
    if (timers) {
      previewTimerId = timers.setTimeout(() => {
        if (previewingVideoId.value === video.id) {
          playPreview(video)
        }
      }, 300)
    }
  }

  // 停止预览 (PC鼠标离开)
  const stopPreview = (video) => {
    if (isTouchMode.value) return
    
    if (previewTimerId && timers) {
      timers.clearTimeout(previewTimerId)
      previewTimerId = null
    }
    
    if (previewingVideoId.value === video.id) {
      previewingVideoId.value = null
      const videoEl = previewRefs.value[video.id]
      if (videoEl) {
        videoEl.pause()
        videoEl.currentTime = 0
      }
    }
  }

  // 触摸开始时启用触摸模式
  const onTouchStart = () => {
    isTouchMode.value = true
  }

  // 视频卡片点击处理
  const handleVideoClick = (video, goToVideo) => {
    // 触摸模式：第一次点击预览，第二次进入视频
    if (isTouchMode.value && video.preview_url) {
      if (previewingVideoId.value === video.id) {
        stopCurrentPreview()
        goToVideo(video.id)
      } else {
        playPreview(video)
      }
      return
    }
    // PC模式：直接进入视频
    goToVideo(video.id)
  }

  return {
    previewRefs,
    previewingVideoId,
    isTouchMode,
    setPreviewRef,
    isPreviewPlaying,
    playPreview,
    stopCurrentPreview,
    startPreview,
    stopPreview,
    onTouchStart,
    handleVideoClick
  }
}
