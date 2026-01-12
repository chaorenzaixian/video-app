<template>
  <Teleport to="body">
    <Transition name="popup-fade">
      <div v-if="visible" class="popup-ad-overlay" @click.self="close">
        <div class="popup-ad-container">
          <!-- 关闭按钮 -->
          <button class="close-btn" @click="close">
            <span>×</span>
          </button>
          
          <!-- 广告内容 -->
          <div class="popup-ad-content" @click="handleClick">
            <img 
              v-if="ad?.image_url" 
              :src="ad.image_url" 
              :alt="ad.title || '广告'"
              class="popup-ad-image"
            />
            <div v-if="ad?.title" class="popup-ad-title">{{ ad.title }}</div>
          </div>
          
          <!-- 今日不再显示 -->
          <label class="no-show-today">
            <input type="checkbox" v-model="noShowToday" />
            <span>今日不再显示</span>
          </label>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const visible = ref(false)
const ad = ref(null)
const noShowToday = ref(false)

const STORAGE_KEY = 'popup_ad_hidden_date'

// 检查今天是否已隐藏
const isHiddenToday = () => {
  const hiddenDate = localStorage.getItem(STORAGE_KEY)
  if (!hiddenDate) return false
  
  const today = new Date().toDateString()
  return hiddenDate === today
}

// 获取弹窗广告
const fetchPopupAd = async () => {
  // 检查是否今日已隐藏
  if (isHiddenToday()) return
  
  // 检查本次会话是否已显示
  if (sessionStorage.getItem('popup_ad_shown')) return
  
  try {
    const res = await axios.get('/api/v1/ads/popup')
    if (res.data && res.data.id) {
      ad.value = res.data
      visible.value = true
      sessionStorage.setItem('popup_ad_shown', 'true')
    }
  } catch (e) {
    // 忽略错误
  }
}

// 关闭弹窗
const close = () => {
  if (noShowToday.value) {
    localStorage.setItem(STORAGE_KEY, new Date().toDateString())
  }
  visible.value = false
}

// 点击广告
const handleClick = async () => {
  if (ad.value?.target_url) {
    // 记录点击
    try {
      await axios.post(`/api/v1/ads/${ad.value.id}/click`)
    } catch (e) {}
    
    window.open(ad.value.target_url, '_blank')
  }
  close()
}

onMounted(() => {
  // 延迟1秒显示弹窗，避免和开屏广告冲突
  setTimeout(fetchPopupAd, 1000)
})
</script>

<style scoped>
.popup-ad-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9998;
  backdrop-filter: blur(4px);
}

.popup-ad-container {
  position: relative;
  max-width: 320px;
  width: 85%;
  background: #1a1a1a;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.close-btn {
  position: absolute;
  top: -12px;
  right: -12px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #333;
  z-index: 10;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.close-btn:active {
  transform: scale(0.95);
}

.popup-ad-content {
  cursor: pointer;
}

.popup-ad-image {
  width: 100%;
  display: block;
}

.popup-ad-title {
  padding: 12px 16px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  text-align: center;
  background: linear-gradient(135deg, #a855f7, #7c3aed);
}

.no-show-today {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
}

.no-show-today input {
  width: 14px;
  height: 14px;
  accent-color: #a855f7;
}

/* 动画 */
.popup-fade-enter-active,
.popup-fade-leave-active {
  transition: all 0.3s ease;
}

.popup-fade-enter-active .popup-ad-container,
.popup-fade-leave-active .popup-ad-container {
  transition: all 0.3s ease;
}

.popup-fade-enter-from,
.popup-fade-leave-to {
  opacity: 0;
}

.popup-fade-enter-from .popup-ad-container,
.popup-fade-leave-to .popup-ad-container {
  transform: scale(0.9);
  opacity: 0;
}
</style>
