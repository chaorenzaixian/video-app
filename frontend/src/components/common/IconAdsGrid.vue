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
  padding: clamp(4px, 1.5vw, 8px) clamp(2px, 1vw, 8px);
}

// 第一行：固定5个，自适应间距
.ads-row-fixed {
  display: flex;
  justify-content: space-between;
  margin-bottom: clamp(4px, 1.5vw, 8px);
  padding: 0 clamp(2px, 1vw, 8px);
}

// 第二行：快速滚动
.ads-row-scroll {
  overflow: hidden;
  margin: 0 clamp(2px, 1vw, 8px);
  
  .scroll-track {
    display: flex;
    gap: clamp(2px, 0.8vw, 6px);
    width: max-content;
    animation: scroll-loop 12s linear infinite;
    
    &:hover {
      animation-play-state: paused;
    }
  }
}

@keyframes scroll-loop {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

// 广告项 - 使用 clamp 实现平滑响应式
.ad-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: clamp(3px, 1vw, 6px);
  cursor: pointer;
  min-width: clamp(54px, 15vw, 72px);
  transition: transform 0.2s;
  
  &.hidden {
    display: none;
  }
  
  &:active {
    transform: scale(0.95);
  }
  
  .ad-icon {
    width: clamp(48px, 13vw, 64px);
    height: clamp(48px, 13vw, 64px);
    border-radius: clamp(10px, 3vw, 14px);
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
    font-size: clamp(11px, 3vw, 14px);
    color: rgba(255, 255, 255, 0.75);
    text-align: center;
    max-width: clamp(54px, 15vw, 72px);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-weight: 500;
  }
}

// 第一行的广告项稍大一点
.ads-row-fixed .ad-item {
  min-width: clamp(58px, 16vw, 76px);
  
  .ad-icon {
    width: clamp(52px, 14vw, 68px);
    height: clamp(52px, 14vw, 68px);
  }
  
  .ad-name {
    max-width: clamp(58px, 16vw, 76px);
  }
}
</style>
