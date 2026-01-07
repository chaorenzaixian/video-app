/**
 * 资源清理 Hook
 * 用于统一管理定时器、事件监听器等资源的清理
 */

import { onBeforeUnmount } from 'vue'

/**
 * 定时器管理 Hook
 * @returns {object}
 */
export function useTimers() {
  const timers = new Set()
  const intervals = new Set()
  const animationFrames = new Set()

  onBeforeUnmount(() => {
    // 清理所有 setTimeout
    timers.forEach(id => clearTimeout(id))
    timers.clear()

    // 清理所有 setInterval
    intervals.forEach(id => clearInterval(id))
    intervals.clear()

    // 清理所有 requestAnimationFrame
    animationFrames.forEach(id => cancelAnimationFrame(id))
    animationFrames.clear()
  })

  return {
    /**
     * 设置一个可自动清理的 setTimeout
     */
    setTimeout(fn, delay) {
      const id = setTimeout(() => {
        timers.delete(id)
        fn()
      }, delay)
      timers.add(id)
      return id
    },

    /**
     * 清除指定的 setTimeout
     */
    clearTimeout(id) {
      clearTimeout(id)
      timers.delete(id)
    },

    /**
     * 设置一个可自动清理的 setInterval
     */
    setInterval(fn, delay) {
      const id = setInterval(fn, delay)
      intervals.add(id)
      return id
    },

    /**
     * 清除指定的 setInterval
     */
    clearInterval(id) {
      clearInterval(id)
      intervals.delete(id)
    },

    /**
     * 设置一个可自动清理的 requestAnimationFrame
     */
    requestAnimationFrame(fn) {
      const id = requestAnimationFrame((time) => {
        animationFrames.delete(id)
        fn(time)
      })
      animationFrames.add(id)
      return id
    },

    /**
     * 清除指定的 requestAnimationFrame
     */
    cancelAnimationFrame(id) {
      cancelAnimationFrame(id)
      animationFrames.delete(id)
    },

    /**
     * 清理所有定时器
     */
    clearAll() {
      timers.forEach(id => clearTimeout(id))
      timers.clear()
      intervals.forEach(id => clearInterval(id))
      intervals.clear()
      animationFrames.forEach(id => cancelAnimationFrame(id))
      animationFrames.clear()
    }
  }
}

/**
 * 事件监听器管理 Hook
 * @returns {object}
 */
export function useEventListeners() {
  const listeners = []

  onBeforeUnmount(() => {
    listeners.forEach(({ target, event, handler, options }) => {
      target.removeEventListener(event, handler, options)
    })
    listeners.length = 0
  })

  return {
    /**
     * 添加一个可自动清理的事件监听器
     */
    addEventListener(target, event, handler, options) {
      target.addEventListener(event, handler, options)
      listeners.push({ target, event, handler, options })
    },

    /**
     * 移除指定的事件监听器
     */
    removeEventListener(target, event, handler, options) {
      target.removeEventListener(event, handler, options)
      const index = listeners.findIndex(
        l => l.target === target && l.event === event && l.handler === handler
      )
      if (index > -1) {
        listeners.splice(index, 1)
      }
    },

    /**
     * 移除所有事件监听器
     */
    removeAll() {
      listeners.forEach(({ target, event, handler, options }) => {
        target.removeEventListener(event, handler, options)
      })
      listeners.length = 0
    }
  }
}

/**
 * 视频资源管理 Hook
 * @returns {object}
 */
export function useVideoCleanup() {
  const videoRefs = new Map()

  onBeforeUnmount(() => {
    // 暂停并释放所有视频资源
    videoRefs.forEach((video) => {
      if (video) {
        video.pause()
        video.src = ''
        video.load()
      }
    })
    videoRefs.clear()
  })

  return {
    /**
     * 注册一个视频元素
     */
    registerVideo(key, videoEl) {
      if (videoEl) {
        videoRefs.set(key, videoEl)
      }
    },

    /**
     * 注销一个视频元素
     */
    unregisterVideo(key) {
      const video = videoRefs.get(key)
      if (video) {
        video.pause()
        video.src = ''
        video.load()
      }
      videoRefs.delete(key)
    },

    /**
     * 获取视频元素
     */
    getVideo(key) {
      return videoRefs.get(key)
    },

    /**
     * 暂停所有视频
     */
    pauseAll() {
      videoRefs.forEach((video) => {
        if (video && !video.paused) {
          video.pause()
        }
      })
    },

    /**
     * 释放所有视频资源
     */
    releaseAll() {
      videoRefs.forEach((video) => {
        if (video) {
          video.pause()
          video.src = ''
          video.load()
        }
      })
      videoRefs.clear()
    }
  }
}

/**
 * 综合资源清理 Hook
 * 整合定时器、事件监听器、请求等资源的管理
 * @returns {object}
 */
export function useResourceCleanup() {
  const timers = useTimers()
  const events = useEventListeners()
  const videos = useVideoCleanup()

  return {
    timers,
    events,
    videos,
    
    /**
     * 清理所有资源
     */
    cleanupAll() {
      timers.clearAll()
      events.removeAll()
      videos.releaseAll()
    }
  }
}

export default {
  useTimers,
  useEventListeners,
  useVideoCleanup,
  useResourceCleanup
}
