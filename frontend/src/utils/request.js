/**
 * 请求工具函数
 */

/**
 * 请求去重 - 防止重复请求
 */
class RequestDedup {
  constructor() {
    this.pending = new Map()
  }
  
  /**
   * 执行去重请求
   * @param {string} key - 请求唯一标识
   * @param {Function} fn - 请求函数
   * @returns {Promise} 请求结果
   */
  async dedup(key, fn) {
    if (this.pending.has(key)) {
      return this.pending.get(key)
    }
    
    const promise = fn().finally(() => {
      this.pending.delete(key)
    })
    
    this.pending.set(key, promise)
    return promise
  }
  
  /**
   * 取消指定请求
   * @param {string} key - 请求唯一标识
   */
  cancel(key) {
    this.pending.delete(key)
  }
  
  /**
   * 清除所有待处理请求
   */
  clear() {
    this.pending.clear()
  }
}

export const requestDedup = new RequestDedup()

/**
 * 请求去重 composable
 */
export function useRequestDedup() {
  const pending = new Map()
  
  const dedup = async (key, fn) => {
    if (pending.has(key)) {
      return pending.get(key)
    }
    
    const promise = fn().finally(() => {
      pending.delete(key)
    })
    
    pending.set(key, promise)
    return promise
  }
  
  const cancel = (key) => {
    pending.delete(key)
  }
  
  const clear = () => {
    pending.clear()
  }
  
  return { dedup, cancel, clear }
}

/**
 * 带重试的请求
 * @param {Function} fn - 请求函数
 * @param {number} maxRetries - 最大重试次数
 * @param {number} delay - 重试延迟（毫秒）
 * @returns {Promise} 请求结果
 */
export async function requestWithRetry(fn, maxRetries = 3, delay = 1000) {
  let lastError
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error
      
      // 不重试的错误类型
      if (error.response?.status === 401 || 
          error.response?.status === 403 ||
          error.response?.status === 404) {
        throw error
      }
      
      // 最后一次不等待
      if (i < maxRetries - 1) {
        await new Promise(r => setTimeout(r, delay * Math.pow(2, i)))
      }
    }
  }
  
  throw lastError
}

/**
 * 防抖请求
 * @param {Function} fn - 请求函数
 * @param {number} wait - 等待时间（毫秒）
 * @returns {Function} 防抖后的函数
 */
export function debounceRequest(fn, wait = 300) {
  let timer = null
  
  return function(...args) {
    if (timer) clearTimeout(timer)
    
    return new Promise((resolve, reject) => {
      timer = setTimeout(async () => {
        try {
          const result = await fn.apply(this, args)
          resolve(result)
        } catch (error) {
          reject(error)
        }
      }, wait)
    })
  }
}

/**
 * 节流请求
 * @param {Function} fn - 请求函数
 * @param {number} wait - 等待时间（毫秒）
 * @returns {Function} 节流后的函数
 */
export function throttleRequest(fn, wait = 300) {
  let lastTime = 0
  let pending = null
  
  return function(...args) {
    const now = Date.now()
    
    if (now - lastTime >= wait) {
      lastTime = now
      return fn.apply(this, args)
    }
    
    // 返回上一次的 pending promise
    if (pending) return pending
    
    pending = new Promise((resolve) => {
      setTimeout(() => {
        lastTime = Date.now()
        pending = null
        resolve(fn.apply(this, args))
      }, wait - (now - lastTime))
    })
    
    return pending
  }
}
