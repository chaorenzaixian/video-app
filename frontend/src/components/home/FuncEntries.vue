<template>
  <div class="func-scroll-wrapper">
    <div class="func-scroll">
      <div 
        v-for="func in items" 
        :key="func.id" 
        class="func-item"
        @click="handleClick(func)"
      >
        <div class="func-icon-box" :class="{ 'has-image': func.image && !func.imageError }">
          <img 
            v-if="func.image && !func.imageError" 
            :src="func.image" 
            :alt="func.name" 
            class="func-icon-img"
            @error="func.imageError = true"
          />
          <span v-else class="func-icon-text">{{ getShortName(func.name) }}</span>
        </div>
        <span class="func-name">{{ func.name }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const props = defineProps({
  items: { type: Array, default: () => [] }
})

const router = useRouter()

// 获取简称
const getShortName = (name) => {
  const shortNames = {
    '广场': '广',
    'AI广场': 'A',
    '会员中心': '会',
    '社区广场': '社',
    '分享邀请': '分',
    '排行榜': '排',
    '签到福利': '签'
  }
  return shortNames[name] || name.charAt(0)
}

// 处理点击
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
  
  &::-webkit-scrollbar {
    display: none;
  }
  
  .func-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: clamp(6px, 2vw, 10px);
    cursor: pointer;
    transition: transform 0.2s;
    flex-shrink: 0;
    min-width: clamp(56px, 15vw, 72px);
    
    &:hover {
      transform: scale(1.05);
    }
    
    &:active {
      transform: scale(0.95);
    }
    
    .func-icon-box {
      width: clamp(48px, 13vw, 60px);
      height: clamp(48px, 13vw, 60px);
      display: flex;
      justify-content: center;
      align-items: center;
      border-radius: clamp(12px, 3.5vw, 16px);
      overflow: hidden;
      background: linear-gradient(145deg, #6366f1 0%, #8b5cf6 100%);
      
      &.has-image {
        background: transparent;
      }
      
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
