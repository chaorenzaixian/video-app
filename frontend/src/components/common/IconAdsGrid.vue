<template>
  <div class="icon-ads-container" v-if="hasAds">
    <!-- 第一行：固定5个图标 -->
    <div class="ads-row-fixed">
      <div 
        v-for="ad in row1Ads" 
        :key="ad.id" 
        class="ad-item"
        :class="{ hidden: ad._imgError }"
        @click="handleClick(ad)"
      >
        <div class="ad-icon">
          <img :src="ad.image" :alt="ad.name" @error="handleImgError($event, ad)" />
        </div>
        <span class="ad-name">{{ ad.name }}</span>
      </div>
    </div>

    <!-- 第二行：自动循环滚动 -->
    <div class="ads-row-scroll" v-if="row2Ads.length > 0">
      <div class="scroll-track">
        <div 
          v-for="(ad, index) in scrollAds" 
          :key="`${ad.id}-${index}`" 
          class="ad-item"
          :class="{ hidden: ad._imgError }"
          @click="handleClick(ad)"
        >
          <div class="ad-icon">
            <img :src="ad.image" :alt="ad.name" @error="handleImgError($event, ad)" />
          </div>
          <span class="ad-name">{{ ad.name }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // 支持两种传参方式
  ads: { type: Array, default: () => [] },        // 单数组，自动分割
  row1: { type: Array, default: () => [] },       // 第一行数据
  row2: { type: Array, default: () => [] }        // 第二行数据
})

// 计算第一行广告（固定5个）
const row1Ads = computed(() => {
  if (props.row1.length > 0) return props.row1.slice(0, 5)
  return props.ads.slice(0, 5)
})

// 计算第二行广告（滚动）
const row2Ads = computed(() => {
  if (props.row2.length > 0) return props.row2
  return props.ads.slice(5)
})

// 滚动广告（复制一份实现无缝滚动）
const scrollAds = computed(() => [...row2Ads.value, ...row2Ads.value])

// 是否有广告
const hasAds = computed(() => row1Ads.value.length > 0)

// 点击处理
const handleClick = (ad) => {
  const link = ad.link || ad.target_url
  if (link) window.open(link, '_blank')
}

// 图片加载失败 - 使用响应式触发重新渲染
const handleImgError = (e, ad) => {
  ad._imgError = true
}
</script>

<style lang="scss" scoped>
.icon-ads-container {
  padding: 6px 4px;
}

// 第一行：固定5个，两边有边距，图标紧凑
.ads-row-fixed {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 6px;
  padding: 0 2px;
  
  .ad-item {
    min-width: 66px;
    
    .ad-icon {
      width: 62px;
      height: 62px;
    }
  }
}

// 第二行：快速滚动
.ads-row-scroll {
  overflow: hidden;
  
  .scroll-track {
    display: flex;
    gap: 2px;
    width: max-content;
    animation: scroll-loop 8s linear infinite;
    
    &:hover {
      animation-play-state: paused;
    }
  }
}

@keyframes scroll-loop {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

// 广告项
.ad-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  min-width: 62px;
  transition: transform 0.2s;
  
  &.hidden {
    display: none;
  }
  
  &:active {
    transform: scale(0.95);
  }
  
  .ad-icon {
    width: 56px;
    height: 56px;
    border-radius: 12px;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }
  
  .ad-name {
    font-size: 12px;
    background: linear-gradient(135deg, #a855f7, #6366f1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    max-width: 62px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-weight: 600;
  }
}

// 响应式
@media (min-width: 400px) {
  .ad-item {
    min-width: 66px;
    
    .ad-icon {
      width: 60px;
      height: 60px;
    }
    
    .ad-name {
      font-size: 13px;
      max-width: 66px;
    }
  }
}

@media (min-width: 768px) {
  .icon-ads-container {
    padding: 8px 8px;
  }
  
  .ad-item {
    min-width: 72px;
    
    .ad-icon {
      width: 64px;
      height: 64px;
      border-radius: 14px;
    }
    
    .ad-name {
      font-size: 14px;
      max-width: 72px;
    }
  }
}
</style>
