/**
 * 短视频播放控制逻辑
 */
import { ref } from 'vue'

export function useShortVideoPlayer(timers) {
  const isPlaying = ref(false)
  const userPaused = ref(false)
  const hasAutoPlayed = ref(false)
  const progress = ref(0)
  const currentPlayTime = ref(0)
  const isTrialEnded = ref(false)
  const trialRemaining = ref(15)
  const videoRefs = ref({})
  
  let playTimerId = null
  let lastPauseTime = 0

  // 设置视频引用
  const setVideoRef = (index, el) => {
    if (el) {
      videoRefs.value[index] = el
    }
  }

  // 检查是否是试看视频
  const isTrialVideo = (video) => {
    if (!video) return false
    if (video.is_purchased) return false
    return (video.trial_seconds && video.trial_seconds > 0)
  }

  // 获取试看时长
  const getTrialSeconds = (video) => {
    if (!video || !isTrialVideo(video)) return 0
    return video.trial_seconds || 15
  }

  // 播放当前视频
  const playCurrentVideo = (currentIndex) => {
    const videoEl = videoRefs.value[currentIndex]
    const timeSincePause = Date.now() - lastPauseTime
    
    if (lastPauseTime > 0 && timeSincePause < 500) return
    
    // 暂停其他视频
    Object.entries(videoRefs.value).forEach(([idx, video]) => {
      if (video && parseInt(idx) !== currentIndex) {
        video.pause()
      }
    })
    
    if (videoEl && !userPaused.value) {
      videoEl.play().catch((err) => {
        if (err.name === 'NotAllowedError') {
          videoEl.muted = true
          videoEl.play().catch(() => {})
        }
      })
    }
  }

  // 切换播放/暂停
  const togglePlay = (index, video) => {
    const videoEl = videoRefs.value[index]
    if (!videoEl) return
    
    if (isTrialEnded.value && isTrialVideo(video)) return
    
    if (videoEl.paused) {
      Object.entries(videoRefs.value).forEach(([idx, v]) => {
        if (v && parseInt(idx) !== index) v.pause()
      })
      
      hasAutoPlayed.value = true
      userPaused.value = false
      lastPauseTime = 0
      
      videoEl.play().catch((err) => {
        if (err.name === 'NotAllowedError') {
          videoEl.muted = true
          videoEl.play().catch(() => {})
        }
      })
    } else {
      userPaused.value = true
      lastPauseTime = Date.now()
      if (playTimerId && timers) {
        timers.clearTimeout(playTimerId)
        playTimerId = null
      }
      videoEl.pause()
    }
  }

  // 视频播放事件
  const onVideoPlay = (index, currentIndex) => {
    if (index === currentIndex) {
      isPlaying.value = true
    }
  }

  // 视频暂停事件
  const onVideoPause = (index, currentIndex) => {
    if (index === currentIndex) {
      isPlaying.value = false
    }
  }

  // 视频时间更新
  const onTimeUpdate = (index, e, currentIndex, video) => {
    if (index !== currentIndex) return
    
    const videoEl = e.target
    if (!videoEl.duration) return
    
    progress.value = (videoEl.currentTime / videoEl.duration) * 100
    currentPlayTime.value = videoEl.currentTime
    
    if (isTrialVideo(video) && !isTrialEnded.value) {
      const trialLimit = getTrialSeconds(video)
      trialRemaining.value = Math.max(0, Math.ceil(trialLimit - videoEl.currentTime))
      
      if (videoEl.currentTime >= trialLimit) {
        isTrialEnded.value = true
        videoEl.pause()
        isPlaying.value = false
      }
    }
  }

  // 重置播放状态
  const resetPlayState = (video) => {
    userPaused.value = false
    hasAutoPlayed.value = false
    isTrialEnded.value = false
    currentPlayTime.value = 0
    progress.value = 0
    trialRemaining.value = getTrialSeconds(video)
  }

  // 停止所有视频
  const stopAllVideos = () => {
    if (playTimerId && timers) {
      timers.clearTimeout(playTimerId)
      playTimerId = null
    }
    
    Object.values(videoRefs.value).forEach(video => {
      try {
        if (video) {
          video.pause()
          video.removeAttribute('src')
          video.load()
        }
      } catch (e) {
        console.warn('停止视频失败:', e)
      }
    })
    
    videoRefs.value = {}
  }

  return {
    isPlaying,
    userPaused,
    hasAutoPlayed,
    progress,
    currentPlayTime,
    isTrialEnded,
    trialRemaining,
    videoRefs,
    setVideoRef,
    isTrialVideo,
    getTrialSeconds,
    playCurrentVideo,
    togglePlay,
    onVideoPlay,
    onVideoPause,
    onTimeUpdate,
    resetPlayState,
    stopAllVideos
  }
}
