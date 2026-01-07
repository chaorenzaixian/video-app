<template>
  <nav class="bottom-nav">
    <div 
      v-for="item in navItems" 
      :key="item.path"
      :class="['nav-item', { active: isActive(item.path) }]"
      @click="navigateTo(item.path)"
    >
      <div class="nav-icon-img">
        <img :src="isActive(item.path) ? item.activeIcon : item.icon" :alt="item.label" />
      </div>
      <span class="nav-label">{{ item.label }}</span>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

// 导航项配置
const navItems = [
  { 
    path: '/user', 
    label: '首页', 
    icon: '/images/backgrounds/home_0_0.webp', 
    activeIcon: '/images/backgrounds/home_0_1.webp',
    exactMatch: true
  },
  { 
    path: '/user/forbidden', 
    label: '禁区', 
    icon: '/images/backgrounds/home_1_0.webp', 
    activeIcon: '/images/backgrounds/home_1_1.webp' 
  },
  { 
    path: '/user/soul', 
    label: 'Soul', 
    icon: '/images/backgrounds/home_2_0.webp', 
    activeIcon: '/images/backgrounds/home_2_1.webp' 
  },
  { 
    path: '/user/community', 
    label: '广场', 
    icon: '/images/backgrounds/home_3_0.webp', 
    activeIcon: '/images/backgrounds/home_3_1.webp' 
  },
  { 
    path: '/user/profile', 
    label: '自己', 
    icon: '/images/backgrounds/home_4_0.webp', 
    activeIcon: '/images/backgrounds/home_4_1.webp' 
  }
]

// 判断是否激活
const isActive = (path) => {
  const item = navItems.find(i => i.path === path)
  if (item?.exactMatch) {
    return route.path === path
  }
  return route.path === path || route.path.startsWith(path + '/')
}

// 导航
const navigateTo = (path) => {
  if (route.path !== path) {
    router.push(path)
  }
}
</script>

<style lang="scss" scoped>
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 4px 0;
  padding-bottom: calc(4px + env(safe-area-inset-bottom, 0px));
  background: linear-gradient(to top, #0a0a0a 0%, rgba(10, 10, 10, 0.98) 100%);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  width: 100%;
  z-index: 1000;
  
  // 响应式最大宽度 - 与页面内容一致
  @media (min-width: 768px) {
    max-width: 750px;
    left: 50%;
    transform: translateX(-50%);
  }
  
  @media (min-width: 1024px) {
    max-width: 900px;
  }
  
  @media (min-width: 1280px) {
    max-width: 1200px;
  }
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  color: rgba(255, 255, 255, 0.45);
  cursor: pointer;
  transition: all 0.25s ease;
  padding: 2px 14px;
  
  &:hover {
    color: rgba(255, 255, 255, 0.7);
  }
  
  &:active {
    transform: scale(0.95);
  }
  
  .nav-icon-img {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    
    img {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
  }
  
  .nav-label {
    font-size: 12px;
    letter-spacing: 0.5px;
    color: rgba(255, 255, 255, 0.45);
    transition: all 0.25s ease;
  }
  
  &.active {
    .nav-label {
      background: linear-gradient(135deg, #c084fc, #818cf8);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
  }
}

// 平板及以上
@media (min-width: 768px) {
  .nav-item {
    padding: 4px 18px;
    
    .nav-icon-img {
      width: 30px;
      height: 30px;
    }
    
    .nav-label {
      font-size: 13px;
    }
  }
}

// 横屏模式优化
@media (orientation: landscape) and (max-height: 500px) {
  .bottom-nav {
    padding: 2px 0;
    padding-bottom: calc(2px + env(safe-area-inset-bottom, 0px));
  }
  
  .nav-item {
    padding: 2px 10px;
    
    .nav-icon-img {
      width: 24px;
      height: 24px;
    }
    
    .nav-label {
      font-size: 10px;
    }
  }
}
</style>
