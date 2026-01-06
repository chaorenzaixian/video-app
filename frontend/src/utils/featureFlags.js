/**
 * Feature Flag 客户端
 * 用于前端获取和管理功能开关/AB测试
 */
import api from '@/utils/api'

class FeatureFlagClient {
  constructor() {
    this.flags = {}
    this.loaded = false
    this.loading = false
    this.listeners = []
  }

  /**
   * 初始化 - 批量获取功能开关
   * @param {string[]} flagKeys - 需要获取的功能开关key列表
   */
  async initialize(flagKeys = []) {
    if (this.loading) {
      // 等待当前加载完成
      return new Promise((resolve) => {
        this.listeners.push(resolve)
      })
    }

    this.loading = true

    try {
      const response = await api.post('/feature-flags/evaluate', {
        flag_keys: flagKeys
      })
      this.flags = response.data.flags || {}
      this.loaded = true
      
      // 通知等待的监听器
      this.listeners.forEach(resolve => resolve(this.flags))
      this.listeners = []
      
      console.log('[FeatureFlags] 加载完成:', Object.keys(this.flags))
      return this.flags
    } catch (error) {
      console.error('[FeatureFlags] 加载失败:', error)
      this.flags = {}
      return {}
    } finally {
      this.loading = false
    }
  }

  /**
   * 检查功能是否启用
   * @param {string} key - 功能开关key
   * @returns {boolean}
   */
  isEnabled(key) {
    const flag = this.flags[key]
    return flag?.enabled === true
  }

  /**
   * 获取AB测试变体名称
   * @param {string} key - 功能开关key
   * @returns {string} - 变体名称，默认 'control'
   */
  getVariant(key) {
    const flag = this.flags[key]
    return flag?.variant || 'control'
  }

  /**
   * 获取功能开关的值
   * @param {string} key - 功能开关key
   * @param {*} defaultValue - 默认值
   * @returns {*}
   */
  getValue(key, defaultValue = null) {
    const flag = this.flags[key]
    return flag?.value ?? defaultValue
  }

  /**
   * 获取完整的功能开关数据
   * @param {string} key - 功能开关key
   * @returns {object|null}
   */
  getFlag(key) {
    return this.flags[key] || null
  }

  /**
   * 追踪实验事件
   * @param {string} flagKey - 功能开关key
   * @param {string} eventType - 事件类型 (click, purchase, signup 等)
   * @param {number} eventValue - 事件值（可选，如订单金额）
   * @param {object} eventData - 附加数据（可选）
   */
  async trackEvent(flagKey, eventType, eventValue = null, eventData = null) {
    try {
      await api.post('/feature-flags/track-event', {
        flag_key: flagKey,
        event_type: eventType,
        event_value: eventValue,
        event_data: eventData
      })
      console.log(`[FeatureFlags] 事件追踪: ${flagKey} -> ${eventType}`)
    } catch (error) {
      console.error('[FeatureFlags] 事件追踪失败:', error)
    }
  }

  /**
   * 刷新功能开关
   * @param {string[]} flagKeys - 需要刷新的key列表
   */
  async refresh(flagKeys = []) {
    this.loaded = false
    return this.initialize(flagKeys.length > 0 ? flagKeys : Object.keys(this.flags))
  }

  /**
   * 检查是否在指定的灰度范围内
   * @param {string} key - 功能开关key
   * @returns {boolean}
   */
  isInRollout(key) {
    const flag = this.flags[key]
    if (!flag) return false
    return flag.enabled === true && flag.reason === 'percentage_rollout'
  }

  /**
   * 获取用户的分桶编号（用于调试）
   * @param {string} key - 功能开关key
   * @returns {number|null}
   */
  getBucket(key) {
    const flag = this.flags[key]
    return flag?.bucket ?? null
  }
}

// 单例导出
export const featureFlags = new FeatureFlagClient()

// 默认导出
export default featureFlags


/**
 * Vue 3 Composable
 */
import { ref, computed, onMounted } from 'vue'

export function useFeatureFlag(key) {
  const isEnabled = computed(() => featureFlags.isEnabled(key))
  const variant = computed(() => featureFlags.getVariant(key))
  const value = computed(() => featureFlags.getValue(key))
  const flag = computed(() => featureFlags.getFlag(key))

  const trackEvent = (eventType, eventValue = null, eventData = null) => {
    featureFlags.trackEvent(key, eventType, eventValue, eventData)
  }

  return {
    isEnabled,
    variant,
    value,
    flag,
    trackEvent
  }
}


/**
 * Vue 3 指令
 * 
 * 使用方式:
 * <div v-feature="'new_feature'">新功能内容</div>
 * <div v-feature:variant="'treatment_a'">A方案</div>
 */
export const featureFlagDirective = {
  mounted(el, binding) {
    const key = binding.value
    const checkVariant = binding.arg === 'variant'
    
    if (checkVariant) {
      // 检查变体
      const targetVariant = binding.value
      const flagKey = binding.modifiers ? Object.keys(binding.modifiers)[0] : null
      if (flagKey && featureFlags.getVariant(flagKey) !== targetVariant) {
        el.style.display = 'none'
      }
    } else {
      // 检查是否启用
      if (!featureFlags.isEnabled(key)) {
        el.style.display = 'none'
      }
    }
  }
}


/**
 * 常用功能开关 Key 常量
 */
export const FLAG_KEYS = {
  // UI 相关
  NEW_PLAYER_UI: 'new_player_ui',
  NEW_HOME_LAYOUT: 'new_home_layout',
  DARK_MODE_V2: 'dark_mode_v2',
  
  // 功能相关
  VIDEO_DOWNLOAD: 'video_download',
  AI_RECOMMENDATIONS: 'ai_recommendations',
  LIVE_CHAT: 'live_chat',
  
  // AB测试
  CHECKOUT_FLOW_V2: 'checkout_flow_v2',
  VIP_DISCOUNT_BANNER: 'vip_discount_banner',
  PAYMENT_METHODS: 'payment_methods',
  
  // 灰度发布
  NEW_API_VERSION: 'new_api_version',
  PERFORMANCE_OPTIMIZATIONS: 'performance_optimizations',
}


