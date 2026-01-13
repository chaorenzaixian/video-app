<template>
  <div class="func-scroll-wrapper" v-if="hasVisibleItems">
    <div class="func-scroll">
      <div 
        v-for="func in items" 
        :key="func.id" 
        class="func-item"
        :class="{ hidden: func._imgError }"
        @click="handleClick(func)"
      >
        <div class="func-icon-box">
          <img 
            :src="func.image" 
            :alt="func.name" 
            class="func-icon-img"
            @error="func._imgError = true"
          />
        </div>
        <span class="func-name">{{ func.name }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  items: { type: Array, default: () => [] }
})

const router = useRouter()

// 检查是否有可见项目
const hasVisibleItems = computed(() => props.items.some(item => !item._imgError))

const handleClick = (func) => {
  if (func.link) {
    if (func.link.startsWith('http')) {
      window.open(func.link, '_blank')
    } else {
      router.push(func.link)
    }
  }
}
</script>

<style lang="scss" scoped>
.func-scroll-wrapper {
  width: 100%;
  overflow: hidden;
  padding: clamp(6px, 2vw, 12px) 0;
}

.func-scroll {
  display: flex;
  gap: clamp(12px, 4vw, 20px);
  padding: 0 clamp(12px, 4vw, 16px);
  overflow-x: auto;
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  
  &::-webkit-scrollbar { display: none; }
  
  .func-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: clamp(6px, 2vw, 10px);
    cursor: pointer;
    transition: transform 0.2s;
    flex-shrink: 0;
    min-width: clamp(56px, 15vw, 72px);
    
    &:hover { transform: scale(1.05); }
    &:active { transform: scale(0.95); }
    
    &.hidden { display: none; }
    
    .func-icon-box {
      width: clamp(48px, 13vw, 60px);
      height: clamp(48px, 13vw, 60px);
      display: flex;
      justify-content: center;
      align-items: center;
      border-radius: clamp(12px, 3.5vw, 16px);
      overflow: hidden;
      background: transparent;
      
      .func-icon-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
      
      .func-icon-text {
        font-size: clamp(18px, 5vw, 24px);
        font-weight: 500;
        color: #fff;
      }
    }
    
    .func-name {
      font-size: clamp(12px, 3.2vw, 14px);
      color: rgba(255, 255, 255, 0.85);
      white-space: nowrap;
      text-align: center;
    }
  }
}
</style>
