/**
 * 请求取消 Hook
 * 用于在组件卸载时自动取消未完成的请求，防止内存泄漏
 */

import { onBeforeUnmount } from 'vue'

/**
 * 创建一个可取消的请求控制器
 * @returns {object} { signal, abort, isAborted }
 */
export function useAbortController() {
  const controller = new AbortController()
  let aborted = false

  onBeforeUnmount(() => {
    if (!aborted) {
      controller.abort()
      aborted = true
    }
  })

  return {
    signal: controller.signal,
    abort: () => {
      if (!aborted) {
        controller.abort()
        aborted = true
      }
    },
    get isAborted() {
      return aborted
    }
  }
}

/**
 * 创建多个可取消的请求控制器
 * 适用于需要独立取消不同请求的场景
 * @returns {object} { createController, abortAll }
 */
export function useMultipleAbortControllers() {
  const controllers = new Map()
  let nextId = 0

  onBeforeUnmount(() => {
    controllers.forEach(controller => {
      controller.abort()
    })
    controllers.clear()
  })

  return {
    /**
     * 创建一个新的控制器
     * @param {string} key - 可选的键名，用于后续单独取消
     * @returns {AbortSignal}
     */
    createController(key = null) {
      const id = key || `controller_${nextId++}`
      
      // 如果已存在同名控制器，先取消它
      if (controllers.has(id)) {
        controllers.get(id).abort()
      }
      
      const controller = new AbortController()
      controllers.set(id, controller)
      return controller.signal
    },

    /**
     * 取消指定的控制器
     * @param {string} key - 控制器键名
     */
    abort(key) {
      if (controllers.has(key)) {
        controllers.get(key).abort()
        controllers.delete(key)
      }
    },

    /**
     * 取消所有控制器
     */
    abortAll() {
      controllers.forEach(controller => {
        controller.abort()
      })
      controllers.clear()
    }
  }
}

/**
 * 安全的异步请求包装器
 * 自动处理请求取消错误
 * @param {Function} requestFn - 请求函数
 * @param {object} options - 选项
 * @returns {Promise}
 */
export async function safeRequest(requestFn, options = {}) {
  const { onError, onAbort, signal } = options
  
  try {
    return await requestFn()
  } catch (error) {
    if (error.name === 'AbortError' || error.name === 'CanceledError') {
      // 请求被取消，通常是组件卸载导致的
      if (onAbort) onAbort()
      return null
    }
    
    // 其他错误
    if (onError) {
      onError(error)
    } else {
      console.error('Request failed:', error)
    }
    throw error
  }
}

export default {
  useAbortController,
  useMultipleAbortControllers,
  safeRequest
}
