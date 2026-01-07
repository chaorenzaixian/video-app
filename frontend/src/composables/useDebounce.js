/**
 * 防抖和节流 Hook
 * 用于防止重复请求和优化性能
 */

import { ref, watch, onBeforeUnmount } from 'vue'

/**
 * 防抖 ref
 * @param {any} initialValue - 初始值
 * @param {number} delay - 延迟时间（毫秒）
 * @returns {Ref}
 */
export function useDebouncedRef(initialValue, delay = 300) {
  const value = ref(initialValue)
  const debouncedValue = ref(initialValue)
  let timeout = null

  watch(value, (newValue) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => {
      debouncedValue.value = newValue
    }, delay)
  })

  onBeforeUnmount(() => {
    if (timeout) clearTimeout(timeout)
  })

  return {
    value,
    debouncedValue
  }
}

/**
 * 防抖函数
 * @param {Function} fn - 要防抖的函数
 * @param {number} delay - 延迟时间（毫秒）
 * @returns {Function}
 */
export function useDebounce(fn, delay = 300) {
  let timeout = null

  const debouncedFn = (...args) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => {
      fn(...args)
    }, delay)
  }

  onBeforeUnmount(() => {
    if (timeout) clearTimeout(timeout)
  })

  debouncedFn.cancel = () => {
    if (timeout) {
      clearTimeout(timeout)
      timeout = null
    }
  }

  return debouncedFn
}

/**
 * 节流函数
 * @param {Function} fn - 要节流的函数
 * @param {number} limit - 时间限制（毫秒）
 * @returns {Function}
 */
export function useThrottle(fn, limit = 300) {
  let inThrottle = false
  let lastArgs = null

  const throttledFn = (...args) => {
    if (!inThrottle) {
      fn(...args)
      inThrottle = true
      setTimeout(() => {
        inThrottle = false
        if (lastArgs) {
          fn(...lastArgs)
          lastArgs = null
        }
      }, limit)
    } else {
      lastArgs = args
    }
  }

  return throttledFn
}

/**
 * 防止重复点击的 Hook
 * @param {Function} fn - 要执行的异步函数
 * @param {object} options - 选项
 * @returns {object} { execute, loading }
 */
export function useAsyncLock(fn, options = {}) {
  const { minDelay = 0 } = options
  const loading = ref(false)

  const execute = async (...args) => {
    if (loading.value) return null

    loading.value = true
    const startTime = Date.now()

    try {
      const result = await fn(...args)
      
      // 确保最小延迟时间
      const elapsed = Date.now() - startTime
      if (minDelay > 0 && elapsed < minDelay) {
        await new Promise(resolve => setTimeout(resolve, minDelay - elapsed))
      }
      
      return result
    } finally {
      loading.value = false
    }
  }

  return {
    execute,
    loading
  }
}

/**
 * 点赞/收藏等操作的防重复 Hook
 * @returns {object}
 */
export function useActionLock() {
  const lockMap = new Map()

  const isLocked = (key) => lockMap.get(key) === true

  const lock = (key) => {
    lockMap.set(key, true)
  }

  const unlock = (key) => {
    lockMap.delete(key)
  }

  const withLock = async (key, fn) => {
    if (isLocked(key)) return null
    
    lock(key)
    try {
      return await fn()
    } finally {
      unlock(key)
    }
  }

  onBeforeUnmount(() => {
    lockMap.clear()
  })

  return {
    isLocked,
    lock,
    unlock,
    withLock
  }
}

export default {
  useDebouncedRef,
  useDebounce,
  useThrottle,
  useAsyncLock,
  useActionLock
}
