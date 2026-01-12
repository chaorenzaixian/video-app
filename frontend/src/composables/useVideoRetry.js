/**
 * 视频播放重试 composable
 * 提供自动重试、错误恢复功能
 */
import { ref } from 'vue'

export function useVideoRetry(options = {}) {
  const {
    maxRetries = 3,
    retryDelay = 1000,
    onRetry = null,
    onMaxRetriesReached = null
  } = options

  const retryCount = ref(0)
  const isRetrying = ref(false)
  const lastError = ref(null)

  /**
   * 带重试的视频播放
   * @param {HTMLVideoElement|Object} player - 视频元素或播放器实例
   * @param {string} url - 视频URL
   */
  const playWithRetry = async (player, url) => {
    retryCount.value = 0
    lastError.value = null

    const attemptPlay = async () => {
      try {
        isRetrying.value = retryCount.value > 0

        // ArtPlayer 实例
        if (player && typeof player.switchUrl === 'function') {
          if (retryCount.value > 0) {
            await player.switchUrl(url)
          }
          await player.play()
          isRetrying.value = false
          return true
        }

        // 原生 video 元素
        if (player instanceof HTMLVideoElement) {
          if (retryCount.value > 0) {
            player.src = url
            player.load()
          }
          await player.play()
          isRetrying.value = false
          return true
        }

        return false
      } catch (error) {
        lastError.value = error
        retryCount.value++

        if (retryCount.value < maxRetries) {
          onRetry?.(retryCount.value, error)
          
          // 指数退避延迟
          const delay = retryDelay * Math.pow(2, retryCount.value - 1)
          await new Promise(r => setTimeout(r, delay))
          
          return attemptPlay()
        } else {
          isRetrying.value = false
          onMaxRetriesReached?.(error)
          throw error
        }
      }
    }

    return attemptPlay()
  }

  /**
   * 重置重试状态
   */
  const resetRetry = () => {
    retryCount.value = 0
    isRetrying.value = false
    lastError.value = null
  }

  /**
   * 处理视频错误事件
   * @param {Event} event - 错误事件
   * @param {Function} retryFn - 重试函数
   */
  const handleVideoError = async (event, retryFn) => {
    const video = event.target
    const error = video?.error

    // 判断是否可重试的错误
    const retryableErrors = [
      MediaError.MEDIA_ERR_NETWORK,    // 网络错误
      MediaError.MEDIA_ERR_DECODE,     // 解码错误
    ]

    if (error && retryableErrors.includes(error.code)) {
      if (retryCount.value < maxRetries) {
        retryCount.value++
        onRetry?.(retryCount.value, error)
        
        const delay = retryDelay * Math.pow(2, retryCount.value - 1)
        await new Promise(r => setTimeout(r, delay))
        
        retryFn?.()
      } else {
        onMaxRetriesReached?.(error)
      }
    }
  }

  return {
    retryCount,
    isRetrying,
    lastError,
    playWithRetry,
    resetRetry,
    handleVideoError
  }
}

/**
 * HLS 播放重试
 */
export function useHlsRetry(options = {}) {
  const { maxRetries = 3, onError = null } = options
  
  const setupHlsRetry = (hls, player) => {
    if (!hls) return

    let retryCount = 0

    hls.on('hlsError', (event, data) => {
      if (data.fatal) {
        switch (data.type) {
          case 'networkError':
            if (retryCount < maxRetries) {
              retryCount++
              console.log(`[HLS] Network error, retrying... (${retryCount}/${maxRetries})`)
              setTimeout(() => hls.startLoad(), 1000 * retryCount)
            } else {
              onError?.('network', data)
            }
            break
          case 'mediaError':
            if (retryCount < maxRetries) {
              retryCount++
              console.log(`[HLS] Media error, recovering... (${retryCount}/${maxRetries})`)
              hls.recoverMediaError()
            } else {
              onError?.('media', data)
            }
            break
          default:
            onError?.('fatal', data)
            break
        }
      }
    })

    // 成功加载后重置计数
    hls.on('hlsManifestParsed', () => {
      retryCount = 0
    })
  }

  return { setupHlsRetry }
}
