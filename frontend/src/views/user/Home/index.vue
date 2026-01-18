<template>
  <div class="app-container" ref="scrollContainer">
    <!-- 固定头部 -->
    <header class="fixed-header">
      <div class="header-top">
        <div class="header-left">
          <div class="welfare-icon" @click="$router.push('/user/tasks')">
            <img src="/images/backgrounds/fuli.webp" alt="福利" class="fuli-img" />
          </div>
        </div>
        <div class="header-center">
          <img :src="siteSettings.logo || '/images/icons/default_logo.webp'" alt="Logo" class="logo-img" />
        </div>
        <div class="header-right">
          <router-link to="/user/search" class="header-icon search-icon">
            <img src="/images/backgrounds/ic_search.webp" alt="搜索" class="search-img" />
          </router-link>
          <div class="header-icon menu-icon" @click="showNavDrawer = true">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
      <CategoryNav 
        :categories="categories" 
        :active-category="activeCategory"
        @select="handleCategorySelect"
        @slide-direction="slideDirection = $event"
      />
    </header>
    
    <div class="header-placeholder"></div>

    <!-- 离线提示条 -->
    <transition name="slide-down">
      <div class="offline-banner" v-if="isOffline && hasCache">
        <svg class="offline-icon" viewBox="0 0 24 24" fill="none">
          <path d="M1 1l22 22M9 9a3 3 0 0 0 4.24 4.24M5.64 5.64A9 9 0 0 0 3 12c0 2.21.8 4.24 2.12 5.82M8.11 8.11A6 6 0 0 0 6 12c0 1.66.67 3.16 1.76 4.24M12 20h.01M16.24 7.76A6 6 0 0 1 18 12M19.07 4.93A10 10 0 0 1 21 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <span>离线模式 · 显示缓存内容</span>
        <button class="retry-btn-small" @click="retryLoad">重试</button>
      </div>
    </transition>

    <!-- 无网络空状态 - 显示骨架屏 -->
    <div class="offline-skeleton" v-if="isOffline && !hasCache && !loadingVideos">
      <HomePageSkeleton />
      <div class="skeleton-overlay">
        <div class="retry-card">
          <svg class="wifi-icon" viewBox="0 0 24 24" fill="none">
            <path d="M1 1l22 22" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M5 12.55a11 11 0 0 1 14.08 0" stroke="currentColor" stroke-width="2" stroke-linecap="round" opacity="0.3"/>
            <path d="M8.53 16.11a6 6 0 0 1 6.95 0" stroke="currentColor" stroke-width="2" stroke-linecap="round" opacity="0.5"/>
            <circle cx="12" cy="20" r="1.5" fill="currentColor"/>
          </svg>
          <p class="retry-text">网络连接失败</p>
          <button class="retry-btn" @click="retryLoad">
            <svg viewBox="0 0 24 24" fill="none" class="retry-icon">
              <path d="M1 4v6h6M23 20v-6h-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            点击重试
          </button>
        </div>
      </div>
    </div>

    <!-- 轮播广告 -->
    <BannerCarousel v-if="!isOffline || hasCache" :banners="banners" />

    <!-- 页面内容 -->
    <transition :name="slideDirection" mode="out-in">
      <div class="page-content" :key="activeCategory" v-if="!isOffline || hasCache">
        <!-- 图标广告位 -->
        <IconAdsGrid :row1="adRow1" :row2="adRow2" />

        <!-- 功能入口 - 只在有数据时显示 -->
        <FuncEntries v-if="funcItems.length > 0" :items="funcItems" />

        <!-- 二级分类 -->
        <div class="hot-section" v-if="currentSubCategories.length > 0">
          <div class="tag-cloud">
            <span 
              v-for="subCat in currentSubCategories" 
              :key="subCat.id" 
              class="tag-item"
              @click="$router.push(`/user/category/${subCat.id}`)"
            >{{ subCat.name }}</span>
          </div>
        </div>

        <!-- 视频筛选 -->
        <div class="filter-bar">
          <div class="filter-tabs">
            <span 
              v-for="(filter, index) in videoFilters" 
              :key="filter.key"
              :class="['filter-item', { active: activeVideoFilter === index }]"
              @click="changeVideoFilter(index)"
            >{{ filter.label }}</span>
          </div>
          <div class="view-toggle" @click="gridMode = gridMode === 1 ? 2 : 1">
            <span class="toggle-label">切换</span>
            <span class="toggle-icon" v-if="gridMode === 1"><i></i><i></i><i></i></span>
            <span class="toggle-icon grid" v-else><i></i><i></i><i></i><i></i></span>
          </div>
        </div>

        <!-- 视频列表 -->
        <VideoList
          :videos="videos"
          :loading="loadingVideos"
          :grid-mode="gridMode"
          :previewing-video-id="previewingVideoId"
          @video-click="handleVideoClick"
          @preview-start="startPreview"
          @preview-stop="stopPreview"
          @touch-start="onTouchStart"
          @set-preview-ref="setPreviewRef"
        />
      </div>
    </transition>

    <!-- 底部提示条 -->
    <div class="bottom-promo" v-if="showPromo">
      <div class="promo-icon">
        <svg viewBox="0 0 24 24" fill="none">
          <path d="M11 5L6 9H2v6h4l5 4V5z" fill="#7c3aed"/>
          <path d="M15.54 8.46a5 5 0 0 1 0 7.07" stroke="#7c3aed" stroke-width="2.5" stroke-linecap="round"/>
          <path d="M19.07 4.93a10 10 0 0 1 0 14.14" stroke="#7c3aed" stroke-width="2.5" stroke-linecap="round"/>
        </svg>
      </div>
      <div class="promo-text">
        <span class="scroll-text">{{ announcementText }} 🔸 {{ announcementText }}</span>
      </div>
      <span class="close-btn" @click="showPromo = false">✕</span>
    </div>

    <!-- 短视频浮动入口 -->
    <div class="short-video-float" @click="$router.push('/shorts')">
      <img src="/images/backgrounds/short_logo.webp" alt="短视频" />
    </div>

    <BottomNav />
    
    <!-- 导航抽屉 -->
    <div class="nav-drawer-mask" v-if="showNavDrawer" @click="showNavDrawer = false"></div>
    <transition name="drawer-slide">
      <div class="nav-drawer" v-if="showNavDrawer">
        <div class="drawer-header"><h3>导航列表</h3></div>
        <div class="drawer-grid">
          <div 
            v-for="cat in categories.filter(c => c.id !== 0)" 
            :key="cat.id"
            :class="['drawer-item', { active: activeCategory === cat.id }]"
            @click="showNavDrawer = false; handleCategorySelect(cat.id)"
          >{{ cat.name }}</div>
        </div>
      </div>
    </transition>
    
    <!-- 弹窗广告 -->
    <PopupAd />
  </div>
</template>

<script setup>
defineOptions({ name: 'UserHome' })

import { ref, onMounted, onUnmounted, onActivated, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAbortController } from '@/composables/useAbortController'
import { useTimers, useVideoCleanup } from '@/composables/useCleanup'
import BottomNav from '@/components/common/BottomNav.vue'
import IconAdsGrid from '@/components/common/IconAdsGrid.vue'
import BannerCarousel from './components/BannerCarousel.vue'
import CategoryNav from './components/CategoryNav.vue'
import VideoList from './components/VideoList.vue'
import FuncEntries from './components/FuncEntries.vue'
import PopupAd from '@/components/PopupAd.vue'
import HomePageSkeleton from '@/components/Skeleton/HomePageSkeleton.vue'
import { useHomeData } from './composables/useHomeData'
import { useVideoPreview } from './composables/useVideoPreview'

const router = useRouter()
const { signal: abortSignal } = useAbortController()
const scrollContainer = ref(null)
const timers = useTimers()
const videoCleanup = useVideoCleanup()

// 首页数据
const {
  siteSettings, categories, activeCategory, currentSubCategories,
  funcItems, adRow1, adRow2, announcementText, banners,
  videos, loadingVideos, isOffline, hasCache, videoFilters, activeVideoFilter,
  fetchHomeInit, changeVideoFilter, selectCategory, retryLoad
} = useHomeData(abortSignal)

// 视频预览
const {
  previewingVideoId, setPreviewRef, startPreview, stopPreview, onTouchStart, handleVideoClick: previewHandleClick
} = useVideoPreview(videoCleanup, timers)

// UI状态
const showPromo = ref(true)
const showNavDrawer = ref(false)
const slideDirection = ref('slide-right')
const gridMode = ref(2)

// 分类选择
const handleCategorySelect = (catId) => {
  selectCategory(catId)
}

// 视频点击
const handleVideoClick = (video) => {
  previewHandleClick(video, (id) => router.push(`/user/video/${id}`))
}

// 设置固定头部高度 CSS 变量
const updateHeaderHeight = () => {
  const header = document.querySelector('.fixed-header')
  if (header) {
    const rect = header.getBoundingClientRect()
    const height = Math.floor(rect.bottom)
    document.documentElement.style.setProperty('--header-height', `${height}px`)
  }
}

onMounted(() => {
  fetchHomeInit()
  
  // 初始化头部高度
  updateHeaderHeight()
  // DOM 渲染完成后再次更新
  setTimeout(updateHeaderHeight, 100)
  // 监听窗口大小变化
  window.addEventListener('resize', updateHeaderHeight)
})

// keep-alive 激活时滚动到顶部
onActivated(async () => {
  await nextTick()
  // 滚动容器到顶部
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = 0
  }
  // 重新计算头部高度
  updateHeaderHeight()
})

onUnmounted(() => {
  window.removeEventListener('resize', updateHeaderHeight)
})
</script>


<style lang="scss" scoped>
$breakpoint-lg: 768px;
$breakpoint-xl: 1024px;
$breakpoint-xxl: 1280px;

.app-container {
  height: 100vh;
  height: 100dvh;
  background: #0a0a0a;
  color: #fff;
  padding-bottom: calc(60px + env(safe-area-inset-bottom, 0px));
  padding-left: env(safe-area-inset-left, 0px);
  padding-right: env(safe-area-inset-right, 0px);
  width: 100%;
  max-width: 100vw;
  margin: 0 auto;
  overflow-x: hidden;
  overflow-y: auto;
  
  @media (min-width: $breakpoint-lg) { max-width: 750px; }
  @media (min-width: $breakpoint-xl) { max-width: 900px; }
  @media (min-width: $breakpoint-xxl) { max-width: 1200px; }
}

.fixed-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: #0a0a0a;
  width: 100%;
  max-width: 100vw;
  margin: 0 auto;
  padding-top: env(safe-area-inset-top, 10px);
  box-sizing: border-box;
  
  @media (min-width: $breakpoint-lg) {
    max-width: 750px;
    left: 50%;
    transform: translateX(-50%);
  }
  @media (min-width: $breakpoint-xl) { max-width: 900px; }
  @media (min-width: $breakpoint-xxl) { max-width: 1200px; }
  
  .header-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: clamp(8px, 2vw, 14px) clamp(10px, 3vw, 20px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }
  
  .header-left {
    flex: 1;
    .welfare-icon {
      cursor: pointer;
      width: fit-content;
      .fuli-img { width: 32px; height: 32px; object-fit: contain; }
    }
  }
  
  .header-center {
    flex: 2;
    display: flex;
    justify-content: center;
    .logo-img { height: 30px; max-width: 100px; object-fit: contain; }
    .logo-text {
      font-size: 26px;
      font-weight: 300;
      font-family: 'Georgia', serif;
      font-style: italic;
      background: linear-gradient(90deg, #fff 0%, #fff 60%, #a855f7 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
  }
  
  .header-right {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 12px;
    
    .header-icon {
      width: 28px;
      height: 28px;
      display: flex;
      justify-content: center;
      align-items: center;
      cursor: pointer;
      &.search-icon .search-img { width: 28px; height: 28px; object-fit: contain; }
    }
    
    .menu-icon {
      flex-direction: column;
      gap: 5px;
      span { width: 20px; height: 2px; background: rgba(255, 255, 255, 0.8); border-radius: 1px; }
    }
  }
}

.header-placeholder {
  height: clamp(100px, 28vw, 130px);
  height: calc(clamp(100px, 28vw, 130px) + env(safe-area-inset-top, 0px));
}

// 离线提示条
.offline-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(99, 102, 241, 0.15) 100%);
  border-bottom: 1px solid rgba(168, 85, 247, 0.2);
  font-size: 13px;
  color: rgba(255, 255, 255, 0.85);
  
  .offline-icon {
    width: 16px;
    height: 16px;
    color: #a855f7;
  }
  
  .retry-btn-small {
    margin-left: 8px;
    padding: 4px 12px;
    background: rgba(168, 85, 247, 0.3);
    border: 1px solid rgba(168, 85, 247, 0.5);
    border-radius: 12px;
    color: #a855f7;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s;
    
    &:hover {
      background: rgba(168, 85, 247, 0.4);
    }
    
    &:active {
      transform: scale(0.95);
    }
  }
}

// 离线骨架屏
.offline-skeleton {
  position: relative;
  
  .skeleton-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(10, 10, 10, 0.7);
    backdrop-filter: blur(4px);
    z-index: 10;
  }
  
  .retry-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 32px 48px;
    background: rgba(26, 26, 46, 0.95);
    border-radius: 20px;
    border: 1px solid rgba(168, 85, 247, 0.2);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    
    .wifi-icon {
      width: 48px;
      height: 48px;
      color: rgba(168, 85, 247, 0.8);
      margin-bottom: 16px;
    }
    
    .retry-text {
      font-size: 16px;
      color: rgba(255, 255, 255, 0.85);
      margin: 0 0 20px;
    }
    
    .retry-btn {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 28px;
      background: linear-gradient(135deg, #a855f7 0%, #7c3aed 100%);
      border: none;
      border-radius: 22px;
      color: #fff;
      font-size: 15px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.3s;
      box-shadow: 0 4px 16px rgba(168, 85, 247, 0.4);
      
      .retry-icon {
        width: 16px;
        height: 16px;
      }
      
      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(168, 85, 247, 0.5);
      }
      
      &:active {
        transform: translateY(0) scale(0.98);
      }
    }
  }
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.slide-down-enter-active, .slide-down-leave-active {
  transition: all 0.3s ease;
}
.slide-down-enter-from, .slide-down-leave-to {
  opacity: 0;
  transform: translateY(-100%);
}

.page-content { width: 100%; }

.hot-section {
  padding: clamp(8px, 2.5vw, 14px) clamp(10px, 3vw, 16px);
}

.tag-cloud {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: clamp(6px, 2vw, 12px);
  
  @media (min-width: $breakpoint-lg) {
    grid-template-columns: repeat(5, 1fr);
  }
  @media (min-width: $breakpoint-xl) {
    grid-template-columns: repeat(6, 1fr);
  }
  @media (min-width: $breakpoint-xxl) {
    grid-template-columns: repeat(8, 1fr);
  }
  
  .tag-item {
    padding: clamp(6px, 2vw, 10px) clamp(2px, 1vw, 6px);
    background: rgba(255, 255, 255, 0.08);
    border-radius: clamp(4px, 1.5vw, 8px);
    font-size: clamp(12px, 3.5vw, 14px);
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    color: rgba(255, 255, 255, 0.75);
    font-weight: 500;
    
    &:hover {
      background: linear-gradient(135deg, #a855f7, #7c3aed);
      transform: translateY(-1px);
    }
    
    @media (hover: none) {
      &:active {
        background: linear-gradient(135deg, #a855f7, #7c3aed);
        transform: translateY(-1px);
      }
    }
  }
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: clamp(8px, 2.5vw, 14px) clamp(6px, 2vw, 12px);
  background: #0a0a0a;
  margin: 0 clamp(4px, 1.5vw, 10px);
  border-radius: clamp(8px, 3vw, 14px) clamp(8px, 3vw, 14px) 0 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  position: sticky;
  top: var(--header-height, 100px);
  z-index: 40;
  
  // 用 box-shadow 向上延伸背景色，覆盖可能的缝隙
  box-shadow: 0 -10px 0 0 #0a0a0a;
  
  .filter-tabs {
    display: flex;
    gap: clamp(10px, 3vw, 24px);
    
    .filter-item {
      font-size: clamp(12px, 3.5vw, 15px);
      color: rgba(255, 255, 255, 0.5);
      cursor: pointer;
      padding: clamp(4px, 1.5vw, 8px) 0;
      position: relative;
      white-space: nowrap;
      
      &:hover { color: rgba(255, 255, 255, 0.8); }
      
      &.active {
        color: #fff;
        font-weight: 600;
        &::after {
          content: '';
          position: absolute;
          bottom: 0;
          left: 0;
          right: 0;
          height: 2px;
          background: linear-gradient(90deg, #a855f7, #7c3aed);
          border-radius: 1px;
        }
      }
    }
  }
  
  .view-toggle {
    display: flex;
    align-items: center;
    gap: clamp(3px, 1vw, 6px);
    cursor: pointer;
    padding: clamp(3px, 1vw, 6px) clamp(5px, 1.5vw, 10px);
    border-radius: clamp(3px, 1vw, 5px);
    
    &:hover { background: rgba(255, 255, 255, 0.08); }
    
    .toggle-label { font-size: clamp(11px, 3vw, 14px); color: rgba(255, 255, 255, 0.7); }
    
    .toggle-icon {
      display: flex;
      flex-direction: column;
      gap: 2px;
      width: clamp(14px, 4vw, 20px);
      height: clamp(14px, 4vw, 20px);
      justify-content: center;
      align-items: center;
      
      i { width: clamp(12px, 4vw, 18px); height: 2px; background: rgba(255, 255, 255, 0.8); border-radius: 1px; }
      
      &.grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: clamp(2px, 0.8vw, 4px);
        i { width: clamp(5px, 1.5vw, 8px); height: clamp(5px, 1.5vw, 8px); }
      }
    }
  }
}

.bottom-promo {
  position: fixed;
  bottom: calc(52px + env(safe-area-inset-bottom, 0px));
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  background: rgba(30, 15, 45, 0.85);
  backdrop-filter: blur(8px);
  z-index: 99;
  
  @media (min-width: $breakpoint-lg) {
    max-width: 750px;
    left: 50%;
    transform: translateX(-50%);
  }
  @media (min-width: $breakpoint-xl) {
    max-width: 900px;
  }
  @media (min-width: $breakpoint-xxl) {
    max-width: 1200px;
  }
  
  .promo-icon { width: 28px; height: 28px; svg { width: 100%; height: 100%; } }
  
  .promo-text {
    flex: 1;
    overflow: hidden;
    height: 22px;
    
    .scroll-text {
      display: inline-block;
      font-size: 13px;
      font-weight: 500;
      color: rgba(255, 255, 255, 0.85);
      white-space: nowrap;
      animation: scroll-promo 25s linear infinite;
    }
  }
  
  .close-btn { padding: 4px 8px; cursor: pointer; opacity: 0.6; font-size: 14px; &:hover { opacity: 1; } }
}

@keyframes scroll-promo {
  0% { transform: translateX(100%); }
  100% { transform: translateX(-100%); }
}

.short-video-float {
  position: fixed;
  right: 16px;
  bottom: calc(100px + env(safe-area-inset-bottom, 0px));
  width: 60px;
  height: 60px;
  border-radius: 50%;
  overflow: hidden;
  z-index: 1000;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4), 0 0 15px rgba(0, 224, 255, 0.3);
  transition: transform 0.3s ease;
  
  @media (min-width: $breakpoint-lg) {
    width: 70px;
    height: 70px;
    right: calc(50% - 375px + 16px);
  }
  @media (min-width: $breakpoint-xl) {
    right: calc(50% - 450px + 16px);
  }
  @media (min-width: $breakpoint-xxl) {
    right: calc(50% - 600px + 20px);
  }
  
  img { width: 100%; height: 100%; object-fit: cover; }
  
  @media (hover: hover) {
    &:hover { transform: scale(1.1); }
  }
  &:active { transform: scale(0.95); }
}

.nav-drawer-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
}

.nav-drawer {
  position: fixed;
  top: 0;
  right: 0;
  width: 55%;
  max-width: 260px;
  height: 100%;
  background: rgba(26, 26, 26, 0.6);
  backdrop-filter: blur(10px);
  z-index: 1000;
  padding: 20px;
  padding-top: 60px;
  box-sizing: border-box;
  overflow-y: auto;
  
  .drawer-header { margin-bottom: 20px; h3 { font-size: 18px; font-weight: 600; margin: 0; color: #fff; } }
  
  .drawer-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
  
  .drawer-item {
    padding: 8px 12px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    text-align: center;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.85);
    cursor: pointer;
    transition: all 0.2s;
    
    &:hover { background: rgba(255, 255, 255, 0.1); }
    &.active { background: linear-gradient(135deg, #a855f7, #7c3aed); color: #fff; font-weight: 500; }
  }
}

.drawer-slide-enter-active, .drawer-slide-leave-active { transition: transform 0.3s ease; }
.drawer-slide-enter-from, .drawer-slide-leave-to { transform: translateX(100%); }

.slide-left-enter-active, .slide-left-leave-active { transition: all 0.1s ease-out; }
.slide-left-enter-from { opacity: 0; transform: translateX(100%); }
.slide-left-leave-to { opacity: 0; transform: translateX(-100%); }

.slide-right-enter-active, .slide-right-leave-active { transition: all 0.1s ease-out; }
.slide-right-enter-from { opacity: 0; transform: translateX(-100%); }
.slide-right-leave-to { opacity: 0; transform: translateX(100%); }
</style>
