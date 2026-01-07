<template>
  <Teleport to="body">
    <div v-if="visible" class="image-preview-overlay" @click.self="close">
      <div class="preview-container">
        <!-- 关闭按钮 -->
        <button class="close-btn" @click="close">✕</button>
        
        <!-- 图片计数 -->
        <div class="image-counter" v-if="images.length > 1">
          {{ currentIndex + 1 }} / {{ images.length }}
        </div>
        
        <!-- 图片容器 -->
        <div 
          class="image-wrapper"
          @touchstart="onTouchStart"
          @touchmove="onTouchMove"
          @touchend="onTouchEnd"
        >
          <img 
            :src="currentImage" 
            class="preview-image"
            :style="imageStyle"
            @load="onImageLoad"
            @click.stop
          />
        </div>
        
        <!-- 左右切换按钮 -->
        <button 
          v-if="images.length > 1 && currentIndex > 0" 
          class="nav-btn prev"
          @click="prev"
        >
          ‹
        </button>
        <button 
          v-if="images.length > 1 && currentIndex < images.length - 1" 
          class="nav-btn next"
          @click="next"
        >
          ›
        </button>
        
        <!-- 缩放控制 -->
        <div class="zoom-controls">
          <button class="zoom-btn" @click="zoomOut" :disabled="scale <= 0.5">−</button>
          <span class="zoom-level">{{ Math.round(scale * 100) }}%</span>
          <button class="zoom-btn" @click="zoomIn" :disabled="scale >= 3">+</button>
          <button class="zoom-btn reset" @click="resetZoom">重置</button>
        </div>
        
        <!-- 缩略图列表 -->
        <div class="thumbnail-list" v-if="images.length > 1">
          <div 
            v-for="(img, idx) in images" 
            :key="idx"
            :class="['thumbnail', { active: idx === currentIndex }]"
            @click="goTo(idx)"
          >
            <img :src="img" />
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  images: {
    type: Array,
    default: () => []
  },
  initialIndex: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['update:visible', 'close'])

const currentIndex = ref(0)
const scale = ref(1)
const translateX = ref(0)
const translateY = ref(0)

// 触摸相关
const touchStartX = ref(0)
const touchStartY = ref(0)
const isSwiping = ref(false)

// 当前图片
const currentImage = computed(() => {
  return props.images[currentIndex.value] || ''
})

// 图片样式
const imageStyle = computed(() => ({
  transform: `scale(${scale.value}) translate(${translateX.value}px, ${translateY.value}px)`
}))

// 监听 visible 变化
watch(() => props.visible, (val) => {
  if (val) {
    currentIndex.value = props.initialIndex
    resetZoom()
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})

// 关闭
const close = () => {
  emit('update:visible', false)
  emit('close')
}

// 上一张
const prev = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--
    resetZoom()
  }
}

// 下一张
const next = () => {
  if (currentIndex.value < props.images.length - 1) {
    currentIndex.value++
    resetZoom()
  }
}

// 跳转到指定图片
const goTo = (idx) => {
  currentIndex.value = idx
  resetZoom()
}

// 放大
const zoomIn = () => {
  if (scale.value < 3) {
    scale.value = Math.min(3, scale.value + 0.5)
  }
}

// 缩小
const zoomOut = () => {
  if (scale.value > 0.5) {
    scale.value = Math.max(0.5, scale.value - 0.5)
  }
}

// 重置缩放
const resetZoom = () => {
  scale.value = 1
  translateX.value = 0
  translateY.value = 0
}

// 图片加载完成
const onImageLoad = () => {
  // 可以在这里添加加载完成的处理
}

// 触摸开始
const onTouchStart = (e) => {
  if (e.touches.length === 1) {
    touchStartX.value = e.touches[0].clientX
    touchStartY.value = e.touches[0].clientY
    isSwiping.value = true
  }
}

// 触摸移动
const onTouchMove = (e) => {
  if (!isSwiping.value || e.touches.length !== 1) return
  
  const deltaX = e.touches[0].clientX - touchStartX.value
  const deltaY = e.touches[0].clientY - touchStartY.value
  
  // 如果是缩放状态，允许拖动
  if (scale.value > 1) {
    translateX.value += deltaX * 0.5
    translateY.value += deltaY * 0.5
    touchStartX.value = e.touches[0].clientX
    touchStartY.value = e.touches[0].clientY
  }
}

// 触摸结束
const onTouchEnd = (e) => {
  if (!isSwiping.value) return
  
  const deltaX = e.changedTouches[0].clientX - touchStartX.value
  
  // 如果不是缩放状态，检测滑动切换
  if (scale.value === 1) {
    if (deltaX > 50 && currentIndex.value > 0) {
      prev()
    } else if (deltaX < -50 && currentIndex.value < props.images.length - 1) {
      next()
    }
  }
  
  isSwiping.value = false
}

// 键盘事件
const handleKeydown = (e) => {
  if (!props.visible) return
  
  switch (e.key) {
    case 'Escape':
      close()
      break
    case 'ArrowLeft':
      prev()
      break
    case 'ArrowRight':
      next()
      break
    case '+':
    case '=':
      zoomIn()
      break
    case '-':
      zoomOut()
      break
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
  document.body.style.overflow = ''
})
</script>

<style lang="scss" scoped>
.image-preview-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.95);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 50%;
  color: #fff;
  font-size: 20px;
  cursor: pointer;
  z-index: 10;
  transition: background 0.2s;
  
  &:hover {
    background: rgba(255, 255, 255, 0.2);
  }
}

.image-counter {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 14px;
  z-index: 10;
}

.image-wrapper {
  max-width: 90vw;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-image {
  max-width: 100%;
  max-height: 80vh;
  object-fit: contain;
  transition: transform 0.2s ease;
  user-select: none;
  -webkit-user-drag: none;
}

.nav-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 50px;
  height: 50px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 50%;
  color: #fff;
  font-size: 30px;
  cursor: pointer;
  z-index: 10;
  transition: background 0.2s;
  
  &:hover {
    background: rgba(255, 255, 255, 0.2);
  }
  
  &.prev {
    left: 20px;
  }
  
  &.next {
    right: 20px;
  }
}

.zoom-controls {
  position: absolute;
  bottom: 100px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(0, 0, 0, 0.5);
  padding: 8px 16px;
  border-radius: 24px;
  z-index: 10;
  
  .zoom-btn {
    width: 32px;
    height: 32px;
    background: rgba(255, 255, 255, 0.1);
    border: none;
    border-radius: 50%;
    color: #fff;
    font-size: 18px;
    cursor: pointer;
    transition: background 0.2s;
    
    &:hover:not(:disabled) {
      background: rgba(255, 255, 255, 0.2);
    }
    
    &:disabled {
      opacity: 0.3;
      cursor: not-allowed;
    }
    
    &.reset {
      width: auto;
      padding: 0 12px;
      border-radius: 16px;
      font-size: 12px;
    }
  }
  
  .zoom-level {
    color: #fff;
    font-size: 14px;
    min-width: 50px;
    text-align: center;
  }
}

.thumbnail-list {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
  padding: 8px;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 8px;
  max-width: 90vw;
  overflow-x: auto;
  z-index: 10;
  
  &::-webkit-scrollbar {
    display: none;
  }
  
  .thumbnail {
    width: 50px;
    height: 50px;
    border-radius: 4px;
    overflow: hidden;
    cursor: pointer;
    opacity: 0.5;
    transition: opacity 0.2s;
    flex-shrink: 0;
    border: 2px solid transparent;
    
    &.active {
      opacity: 1;
      border-color: #fff;
    }
    
    &:hover:not(.active) {
      opacity: 0.8;
    }
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }
}

// 移动端适配
@media (max-width: 768px) {
  .nav-btn {
    width: 40px;
    height: 40px;
    font-size: 24px;
    
    &.prev {
      left: 10px;
    }
    
    &.next {
      right: 10px;
    }
  }
  
  .zoom-controls {
    bottom: 80px;
    padding: 6px 12px;
    gap: 8px;
    
    .zoom-btn {
      width: 28px;
      height: 28px;
      font-size: 16px;
    }
  }
  
  .thumbnail-list {
    .thumbnail {
      width: 40px;
      height: 40px;
    }
  }
}
</style>
