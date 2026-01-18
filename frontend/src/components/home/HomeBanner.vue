<template>
  <div class="banner-carousel" v-if="banners.length > 0">
    <div class="banner-wrapper">
      <div 
        class="banner-track" 
        :style="{ transform: `translateX(-${currentIndex * 100}%)` }"
      >
        <div 
          v-for="banner in banners" 
          :key="banner.id" 
          class="banner-slide"
          @click="handleClick(banner)"
        >
          <img :src="banner.image_url" :alt="banner.title" class="banner-image" />
        </div>
      </div>
      <!-- 指示点 -->
      <div class="banner-dots" v-if="banners.length > 1">
        <span 
          v-for="(_, index) in banners" 
          :key="index"
          :class="['dot', { active: currentIndex === index }]"
          @click="currentIndex = index"
        ></span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  banners: { type: Array, default: () => [] },
  autoPlay: { type: Boolean, default: true },
  interval: { type: Number, default: 4000 }
})

const router = useRouter()
const currentIndex = ref(0)
let timer = null

// 自动播放
const startAutoPlay = () => {
  if (!props.autoPlay || props.banners.length <= 1) return
  stopAutoPlay()
  timer = setInterval(() => {
    currentIndex.value = (currentIndex.value + 1) % props.banners.length
  }, props.interval)
}

const stopAutoPlay = () => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

// 处理点击
const handleClick = (banner) => {
  if (!banner.link_url) return
  
  const linkType = banner.link_type || 'url'
  if (linkType === 'video' && banner.link_url) {
    router.push(`/user/video/${banner.link_url}`)
  } else if (linkType === 'vip') {
    router.push('/user/vip')
  } else if (linkType === 'url' && banner.link_url) {
    if (banner.link_url.startsWith('http')) {
      window.open(banner.link_url, '_blank')
    } else {
      router.push(banner.link_url)
    }
  }
}

watch(() => props.banners, (newVal) => {
  if (newVal.length > 1) {
    startAutoPlay()
  }
}, { immediate: true })

onMounted(() => {
  if (props.banners.length > 1) {
    startAutoPlay()
  }
})

onBeforeUnmount(() => {
  stopAutoPlay()
})
</script>

<style lang="scss" scoped>
.banner-carousel {
  margin: 10px 12px;
  border-radius: 12px;
  overflow: hidden;
  
  .banner-wrapper {
    position: relative;
    width: 100%;
    aspect-ratio: 750 / 300;
    background: #1a1a1a;
    border-radius: 12px;
    overflow: hidden;
  }
  
  .banner-track {
    display: flex;
    width: 100%;
    height: 100%;
    transition: transform 0.5s ease-in-out;
  }
  
  .banner-slide {
    flex: 0 0 100%;
    width: 100%;
    height: 100%;
    cursor: pointer;
    
    .banner-image {
      width: 100%;
      height: 100%;
      object-fit: fill;
    }
  }
  
  .banner-dots {
    position: absolute;
    bottom: 10px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 6px;
    
    .dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.4);
      cursor: pointer;
      transition: all 0.3s;
      
      &.active {
        width: 18px;
        border-radius: 3px;
        background: #fff;
      }
    }
  }
}
</style>
