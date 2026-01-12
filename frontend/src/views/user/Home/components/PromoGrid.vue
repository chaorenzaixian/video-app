<template>
  <div>
    <!-- 固定图标广告位 -->
    <div class="promo-grid-fixed" v-if="adRow1.length > 0">
      <div 
        v-for="ad in adRow1" 
        :key="ad.id" 
        class="promo-item"
        @click="handleClick(ad)"
      >
        <div class="promo-icon-wrap" :style="{ background: ad.bg }">
          <img v-if="ad.image && !ad._imgError" :src="ad.image" :alt="ad.name" class="promo-img" @error="ad._imgError = true" />
          <span v-else class="fallback-icon">{{ ad.icon || '📦' }}</span>
        </div>
        <span class="promo-name">{{ ad.name }}</span>
      </div>
    </div>

    <!-- 滚动图标广告位 -->
    <div class="promo-scroll-container" v-if="adRow2.length > 0">
      <div class="promo-grid-scroll" ref="scrollContainer">
        <div 
          v-for="(ad, index) in [...adRow2, ...adRow2]" 
          :key="`${ad.id}-${index}`" 
          class="promo-item"
          @click="handleClick(ad)"
        >
          <div class="promo-icon-wrap" :style="{ background: ad.bg }">
            <img v-if="ad.image && !ad._imgError" :src="ad.image" :alt="ad.name" class="promo-img" @error="ad._imgError = true" />
            <span v-else class="fallback-icon">{{ ad.icon || '📦' }}</span>
          </div>
          <span class="promo-name">{{ ad.name }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

defineProps({
  adRow1: { type: Array, default: () => [] },
  adRow2: { type: Array, default: () => [] }
})

const scrollContainer = ref(null)
let animationId = null

const handleClick = (ad) => {
  if (ad.link) {
    window.open(ad.link, '_blank')
  }
}

// 启动滚动动画
const startScrollAnimation = () => {
  if (!scrollContainer.value) return
  const container = scrollContainer.value
  let scrollPos = 0
  const scrollSpeed = 0.5
  
  const animate = () => {
    scrollPos += scrollSpeed
    if (scrollPos >= container.scrollWidth / 2) {
      scrollPos = 0
    }
    container.scrollLeft = scrollPos
    animationId = requestAnimationFrame(animate)
  }
  animationId = requestAnimationFrame(animate)
}

onMounted(() => {
  setTimeout(() => startScrollAnimation(), 500)
})

onUnmounted(() => {
  if (animationId) cancelAnimationFrame(animationId)
})
</script>

<style lang="scss" scoped>
$breakpoint-md: 600px;
$breakpoint-lg: 768px;
$breakpoint-xl: 1024px;

.promo-grid-fixed {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: clamp(4px, 1.5vw, 10px);
  padding: clamp(6px, 2vw, 12px) clamp(4px, 1.5vw, 10px) clamp(2px, 1vw, 6px);
  
  @media (min-width: $breakpoint-md) { grid-template-columns: repeat(6, 1fr); }
  @media (min-width: $breakpoint-lg) { grid-template-columns: repeat(7, 1fr); }
  @media (min-width: $breakpoint-xl) { grid-template-columns: repeat(8, 1fr); }
}

.promo-scroll-container {
  overflow: hidden;
  padding: clamp(2px, 1vw, 6px) 0;
  
  .promo-grid-scroll {
    display: flex;
    gap: clamp(4px, 1.5vw, 10px);
    padding: 0 clamp(4px, 1.5vw, 10px);
    width: max-content;
  }
}

.promo-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: clamp(4px, 1.5vw, 8px);
  cursor: pointer;
  min-width: clamp(56px, 15vw, 80px);
  transition: transform 0.2s;
  
  &:hover { transform: scale(1.05); }
  
  .promo-icon-wrap {
    width: clamp(56px, 15vw, 80px);
    height: clamp(56px, 15vw, 80px);
    border-radius: clamp(10px, 3vw, 14px);
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: clamp(22px, 6vw, 30px);
    
    .promo-img {
      width: 100%;
      height: 100%;
      border-radius: clamp(10px, 3vw, 14px);
      object-fit: cover;
    }
    
    .fallback-icon {
      font-size: clamp(24px, 6vw, 36px);
      display: flex;
      align-items: center;
      justify-content: center;
      width: 100%;
      height: 100%;
    }
  }
  
  .promo-name {
    font-size: clamp(11px, 3vw, 13px);
    color: rgba(255, 255, 255, 0.7);
    text-align: center;
    max-width: clamp(54px, 14vw, 76px);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
</style>
