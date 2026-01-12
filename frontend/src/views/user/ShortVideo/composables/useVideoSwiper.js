/**
 * 视频滑动逻辑
 */
import { ref } from 'vue'

export function useVideoSwiper(timers) {
  const currentIndex = ref(0)
  const translateY = ref(0)
  const startY = ref(0)
  const isDragging = ref(false)
  const isAnimating = ref(false)
  const slideHeight = ref(0)

  // 触摸开始
  const onTouchStart = (e) => {
    if (isAnimating.value) return
    startY.value = e.touches[0].clientY
    isDragging.value = true
  }

  // 触摸移动
  const onTouchMove = (e, videosLength) => {
    if (!isDragging.value) return
    
    const deltaY = e.touches[0].clientY - startY.value
    const newTranslate = -currentIndex.value * slideHeight.value + deltaY
    
    const maxTranslate = 0
    const minTranslate = -(videosLength - 1) * slideHeight.value
    
    translateY.value = Math.max(minTranslate - 100, Math.min(maxTranslate + 100, newTranslate))
  }

  // 触摸结束
  const onTouchEnd = (e, videosLength, onSlideChange) => {
    if (!isDragging.value) return
    isDragging.value = false
    
    const deltaY = e.changedTouches[0].clientY - startY.value
    const threshold = slideHeight.value * 0.2
    
    if (Math.abs(deltaY) > threshold) {
      if (deltaY < 0 && currentIndex.value < videosLength - 1) {
        goToSlide(currentIndex.value + 1, onSlideChange)
      } else if (deltaY > 0 && currentIndex.value > 0) {
        goToSlide(currentIndex.value - 1, onSlideChange)
      } else {
        goToSlide(currentIndex.value, onSlideChange)
      }
    } else {
      goToSlide(currentIndex.value, onSlideChange)
    }
  }

  // 跳转到指定视频
  const goToSlide = (index, onSlideChange) => {
    const isChangingVideo = index !== currentIndex.value
    
    isAnimating.value = true
    translateY.value = -index * slideHeight.value
    
    if (isChangingVideo) {
      currentIndex.value = index
      if (onSlideChange) onSlideChange(index)
    }
    
    if (timers) {
      timers.setTimeout(() => {
        isAnimating.value = false
      }, 300)
    } else {
      setTimeout(() => {
        isAnimating.value = false
      }, 300)
    }
  }

  // 初始化高度
  const initHeight = () => {
    slideHeight.value = window.innerHeight
    translateY.value = -currentIndex.value * slideHeight.value
  }

  // 窗口大小变化
  const handleResize = () => {
    slideHeight.value = window.innerHeight
    translateY.value = -currentIndex.value * slideHeight.value
  }

  return {
    currentIndex,
    translateY,
    isDragging,
    isAnimating,
    slideHeight,
    onTouchStart,
    onTouchMove,
    onTouchEnd,
    goToSlide,
    initHeight,
    handleResize
  }
}
