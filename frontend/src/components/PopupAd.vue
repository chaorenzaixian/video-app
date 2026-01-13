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
            <!-- 单图模式 -->
            <template v-if="images.length === 1">
              <img :src="images[0]" :alt="ad?.title || '广告'" class="popup-ad-image single" />
            </template>
            
            <!-- 双图模式：上下排版 -->
            <template v-else-if="images.length === 2">
              <div class="images-vertical">
                <img v-for="(img, idx) in images" :key="idx" :src="img" :alt="`广告${idx + 1}`" class="popup-ad-image half" />
              </div>
            </template>
            
            <!-- 多图模式：宫格排版 -->
            <template v-else-if="images.length > 2">
              <div class="images-grid" :class="gridClass">
                <img v-for="(img, idx) in images" :key="idx" :src="img" :alt="`广告${idx + 1}`" class="popup-ad-image grid-item" />
              </div>
            </template>
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
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const visible = ref(false)
const ad = ref(null)
const noShowToday = ref(false)

const STORAGE_KEY = 'popup_ad_hidden_date'

// 图片列表
const images = computed(() => {
  if (!ad.value) return []
  return ad.value.images || (ad.value.image_url ? [ad.value.image_url] : [])
})

// 宫格样式类
const gridClass = computed(() => {
  const count = images.value.length
  if (count === 3) return 'grid-3'
  if (count === 4) return 'grid-4'
  if (count <= 6) return 'grid-6'
  return 'grid-9'
})

// 检查今天是否已隐藏
const isHiddenToday = () => {
  const hiddenDate = localStorage.getItem(STORAGE_KEY)
  if (!hiddenDate) return false
  const today = new Date().toDateString()
  return hiddenDate === today
}

// 获取弹窗广告
const fetchPopupAd = async () => {
  // 只检查是否今日已隐藏
  if (isHiddenToday()) return
  
  try {
    const res = await axios.get('/api/v1/ads/popup')
    if (res.data && res.data.id) {
      ad.value = res.data
      visible.value = true
    }
  } catch (e) {}
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
    try {
      await axios.post(`/api/v1/ads/${ad.value.id}/click`)
    } catch (e) {}
    window.open(ad.value.target_url, '_blank')
  }
  close()
}

onMounted(() => {
  fetchPopupAd()
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
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.5);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #fff;
  z-index: 10;
}

.close-btn:active {
  transform: scale(0.9);
  background: rgba(0, 0, 0, 0.7);
}

.popup-ad-content {
  cursor: pointer;
}

/* 单图模式 */
.popup-ad-image.single {
  width: 100%;
  display: block;
}

/* 双图上下排版 */
.images-vertical {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px;
}

.popup-ad-image.half {
  width: 100%;
  display: block;
  border-radius: 8px;
}

/* 宫格排版 */
.images-grid {
  display: grid;
  gap: 2px;
}

.images-grid.grid-3 {
  grid-template-columns: repeat(3, 1fr);
}

.images-grid.grid-4 {
  grid-template-columns: repeat(2, 1fr);
}

.images-grid.grid-6 {
  grid-template-columns: repeat(3, 1fr);
}

.images-grid.grid-9 {
  grid-template-columns: repeat(3, 1fr);
}

.popup-ad-image.grid-item {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  display: block;
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
