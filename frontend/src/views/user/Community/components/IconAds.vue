<template>
  <div v-if="ads.length">
    <!-- 固定广告位 -->
    <div class="promo-grid-fixed">
      <div v-for="ad in ads.slice(0, 5)" :key="ad.id" class="promo-item" @click="openLink(ad)">
        <div class="promo-icon-wrap">
          <img v-if="ad.image" :src="ad.image" :alt="ad.name" class="promo-img" />
          <span v-else class="fallback-icon">{{ ad.icon || '📦' }}</span>
        </div>
        <span class="promo-name">{{ ad.name }}</span>
      </div>
    </div>
    
    <!-- 滚动广告位 -->
    <div class="promo-scroll-container" v-if="ads.length > 5">
      <div class="promo-grid-scroll">
        <div v-for="ad in [...ads.slice(5), ...ads.slice(5)]" :key="ad.id + '-' + Math.random()" class="promo-item" @click="openLink(ad)">
          <div class="promo-icon-wrap">
            <img v-if="ad.image" :src="ad.image" :alt="ad.name" class="promo-img" />
            <span v-else class="fallback-icon">{{ ad.icon || '📦' }}</span>
          </div>
          <span class="promo-name">{{ ad.name }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  ads: { type: Array, default: () => [] }
})

const openLink = (ad) => {
  if (ad.link) window.open(ad.link, '_blank')
}
</script>

<style lang="scss" scoped>
.promo-grid-fixed {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 4px;
  padding: 8px 8px 4px;
}

.promo-scroll-container {
  overflow: hidden;
  padding: 4px 0;
  
  .promo-grid-scroll {
    display: flex;
    gap: 8px;
    padding: 0 8px;
    width: max-content;
    animation: scroll-ads 20s linear infinite;
  }
}

@keyframes scroll-ads {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

.promo-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  min-width: 56px;
  transition: transform 0.2s;
  
  &:hover { transform: scale(1.05); }
  
  .promo-icon-wrap {
    width: 56px; height: 56px;
    border-radius: 12px;
    display: flex; justify-content: center; align-items: center;
    background: linear-gradient(135deg, #667eea, #764ba2);
    overflow: hidden;
    
    .promo-img { width: 100%; height: 100%; border-radius: 12px; object-fit: cover; }
    .fallback-icon { font-size: 24px; display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; }
  }
  
  .promo-name {
    font-size: 11px; color: rgba(255, 255, 255, 0.7);
    text-align: center; max-width: 54px;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }
}
</style>
