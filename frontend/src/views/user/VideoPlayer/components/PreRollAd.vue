<template>
  <div class="pre-roll-ad" v-if="show && ad">
    <div class="ad-video-container">
      <!-- 视频广告 -->
      <video
        v-if="ad.ad_type === 'video'"
        ref="adVideoRef"
        class="ad-video"
        :src="ad.media_url"
        @timeupdate="$emit('timeupdate', $event)"
        @ended="$emit('ended')"
        @canplay="$emit('canplay')"
        autoplay
        playsinline
        muted
      />
      <!-- 图片广告 -->
      <div v-else class="ad-image-wrapper" @click="$emit('imageClick')">
        <img 
          :src="ad.media_url" 
          class="ad-image"
          @load="$emit('imageLoad')"
        />
      </div>
      <div class="ad-overlay">
        <div class="ad-countdown" v-if="!canSkip">
          广告 {{ countdown }}s
        </div>
        <div class="ad-close-btn" v-else @click="$emit('skip')">
          关闭广告 ✕
        </div>
        <a 
          v-if="ad.target_url" 
          :href="ad.target_url" 
          target="_blank" 
          class="ad-link"
          @click="$emit('click')"
        >
          了解更多
        </a>
      </div>
      <div class="ad-label">广告</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  show: {
    type: Boolean,
    default: false
  },
  ad: {
    type: Object,
    default: null
  },
  countdown: {
    type: Number,
    default: 5
  },
  canSkip: {
    type: Boolean,
    default: false
  }
})

defineEmits(['timeupdate', 'ended', 'canplay', 'imageClick', 'imageLoad', 'skip', 'click'])

const adVideoRef = ref(null)

defineExpose({
  adVideoRef
})
</script>

<style scoped>
.pre-roll-ad {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 100;
  background: #000;
}

.ad-video-container {
  position: relative;
  width: 100%;
  height: 100%;
}

.ad-video,
.ad-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.ad-image-wrapper {
  width: 100%;
  height: 100%;
  cursor: pointer;
}

.ad-overlay {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.ad-countdown,
.ad-close-btn {
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
}

.ad-close-btn {
  cursor: pointer;
}

.ad-close-btn:hover {
  background: rgba(0, 0, 0, 0.9);
}

.ad-link {
  background: linear-gradient(135deg, #ec4899, #f472b6);
  color: #fff;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  text-decoration: none;
}

.ad-label {
  position: absolute;
  top: 10px;
  left: 10px;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  padding: 2px 8px;
  border-radius: 2px;
  font-size: 10px;
}
</style>
