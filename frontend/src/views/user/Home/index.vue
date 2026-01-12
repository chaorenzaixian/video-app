<template>
  <div class="app-container">
    <!-- 固定头部 -->
    <header class="fixed-header">
      <div class="header-top">
        <div class="header-left">
          <div class="welfare-icon" @click="$router.push('/user/vip')">
            <img src="/images/backgrounds/fuli.webp" alt="福利" class="fuli-img" />
          </div>
        </div>
        <div class="header-center">
          <img v-if="siteSettings.logo" :src="siteSettings.logo" alt="Logo" class="logo-img" />
          <span v-else class="logo-text">Soul</span>
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

    <!-- 轮播广告 -->
    <BannerCarousel :banners="banners" />

    <!-- 页面内容 -->
    <transition :name="slideDirection" mode="out-in">
      <div class="page-content" :key="activeCategory">
        <!-- 广告位 -->
        <PromoGrid :ad-row1="adRow1" :ad-row2="adRow2" />

        <!-- 功能入口 -->
        <FuncEntries :items="funcItems" />

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

import { ref, onMounted, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import { useAbortController } from '@/composables/useAbortController'
import { useTimers, useVideoCleanup } from '@/composables/useCleanup'
import BottomNav from '@/components/common/BottomNav.vue'
import BannerCarousel from './components/BannerCarousel.vue'
import CategoryNav from './components/CategoryNav.vue'
import VideoList from './components/VideoList.vue'
import PromoGrid from './components/PromoGrid.vue'
import FuncEntries from './components/FuncEntries.vue'
import PopupAd from '@/components/PopupAd.vue'
import { useHomeData } from './composables/useHomeData'
import { useVideoPreview } from './composables/useVideoPreview'

const router = useRouter()
const { signal: abortSignal } = useAbortController()
const timers = useTimers()
const videoCleanup = useVideoCleanup()

// 首页数据
const {
  siteSettings, categories, activeCategory, currentSubCategories,
  funcItems, adRow1, adRow2, announcementText, banners,
  videos, loadingVideos, videoFilters, activeVideoFilter,
  fetchHomeInit, fetchBanners, changeVideoFilter, selectCategory
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

onMounted(() => {
  fetchHomeInit()
  fetchBanners()
})

// keep-alive 激活时滚动到顶部
onActivated(() => {
  window.scrollTo(0, 0)
})
</script>


<style lang="scss" scoped>
$breakpoint-lg: 768px;
$breakpoint-xl: 1024px;
$breakpoint-xxl: 1280px;

.app-container {
  min-height: 100vh;
  min-height: 100dvh;
  background: #0a0a0a;
  color: #fff;
  padding-bottom: calc(60px + env(safe-area-inset-bottom, 0px));
  padding-left: env(safe-area-inset-left, 0px);
  padding-right: env(safe-area-inset-right, 0px);
  width: 100%;
  max-width: 100vw;
  margin: 0 auto;
  overflow-x: clip;
  
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
  }
  
  .header-left {
    flex: 1;
    .welfare-icon {
      cursor: pointer;
      width: fit-content;
      .fuli-img { width: 36px; height: 36px; object-fit: contain; }
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

.page-content { width: 100%; }

.hot-section {
  padding: clamp(8px, 2.5vw, 14px) clamp(10px, 3vw, 16px);
}

.tag-cloud {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: clamp(6px, 2vw, 12px);
  
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
  top: calc(clamp(100px, 28vw, 130px) + env(safe-area-inset-top, 0px) - 1px);
  z-index: 40;
  
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
  
  img { width: 100%; height: 100%; object-fit: cover; }
  &:hover { transform: scale(1.1); }
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
