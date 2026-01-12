<template>
  <nav ref="navRef" :class="['category-nav', slideClass]">
    <span 
      v-for="cat in categories" 
      :key="cat.id"
      :ref="el => setCategoryRef(cat.id, el)"
      :class="['cat-item', { active: activeCategory === cat.id }]"
      @click="handleSelect(cat.id)"
    >
      {{ cat.name }}
    </span>
  </nav>
</template>

<script setup>
import { ref, nextTick } from 'vue'

const props = defineProps({
  categories: { type: Array, default: () => [] },
  activeCategory: { type: Number, default: 0 }
})

const emit = defineEmits(['select', 'slide-direction'])

const navRef = ref(null)
const slideClass = ref('')
const categoryRefs = {}

const setCategoryRef = (id, el) => {
  if (el) categoryRefs[id] = el
}

// 判断是否需要滚动
const needsScroll = (catId) => {
  const navEl = navRef.value
  const catEl = categoryRefs[catId]
  if (!navEl || !catEl) return false
  
  const navWidth = navEl.offsetWidth
  const currentScroll = navEl.scrollLeft
  const catLeft = catEl.offsetLeft
  const catWidth = catEl.offsetWidth
  const catVisibleLeft = catLeft - currentScroll
  const catVisibleCenter = catVisibleLeft + catWidth / 2
  const centerStart = navWidth / 3
  const centerEnd = navWidth * 2 / 3
  
  return !(catVisibleCenter >= centerStart && catVisibleCenter <= centerEnd)
}

// 滚动到选中分类
const scrollToCategory = (catId) => {
  const navEl = navRef.value
  const catEl = categoryRefs[catId]
  if (!navEl || !catEl) return
  
  const navWidth = navEl.offsetWidth
  const catLeft = catEl.offsetLeft
  const catWidth = catEl.offsetWidth
  const scrollLeft = catLeft - (navWidth / 2) + (catWidth / 2)
  
  navEl.scrollTo({ left: Math.max(0, scrollLeft), behavior: 'smooth' })
}

const handleSelect = (catId) => {
  const currentIndex = props.categories.findIndex(c => c.id === props.activeCategory)
  const targetIndex = props.categories.findIndex(c => c.id === catId)
  const isSlideLeft = targetIndex > currentIndex
  const totalCount = props.categories.length
  
  // 发送滑动方向
  emit('slide-direction', isSlideLeft ? 'slide-left' : 'slide-right')
  
  // 边缘分类不触发导航栏效果
  const isEdgeCategory = targetIndex < 2 || targetIndex >= totalCount - 2
  
  if (!isEdgeCategory && needsScroll(catId)) {
    slideClass.value = isSlideLeft ? 'nav-slide-left' : 'nav-slide-right'
    setTimeout(() => { slideClass.value = '' }, 150)
    scrollToCategory(catId)
  }
  
  emit('select', catId)
}
</script>

<style lang="scss" scoped>
.category-nav {
  display: flex;
  gap: clamp(14px, 4vw, 28px);
  padding: clamp(8px, 2.5vw, 14px) clamp(10px, 3vw, 20px);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  width: 100%;
  box-sizing: border-box;
  transition: transform 0.1s ease-out;
  
  &.nav-slide-left { animation: nav-nudge-left 0.15s ease-out; }
  &.nav-slide-right { animation: nav-nudge-right 0.15s ease-out; }
  &::-webkit-scrollbar { display: none; }
  
  .cat-item {
    padding: clamp(4px, 1.5vw, 8px) 0;
    font-size: clamp(13px, 4vw, 17px);
    white-space: nowrap;
    cursor: pointer;
    transition: all 0.2s;
    color: rgba(255, 255, 255, 0.6);
    position: relative;
    flex-shrink: 0;
    
    &:hover { color: rgba(255, 255, 255, 0.9); }
    
    &.active {
      color: #fff;
      font-weight: 600;
      
      &::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: clamp(16px, 5vw, 24px);
        height: clamp(2px, 0.8vw, 4px);
        background: linear-gradient(90deg, #a855f7, #6366f1);
        border-radius: 2px;
      }
    }
  }
}

@keyframes nav-nudge-left {
  0% { transform: translateX(0); }
  50% { transform: translateX(-8px); }
  100% { transform: translateX(0); }
}

@keyframes nav-nudge-right {
  0% { transform: translateX(0); }
  50% { transform: translateX(8px); }
  100% { transform: translateX(0); }
}
</style>
