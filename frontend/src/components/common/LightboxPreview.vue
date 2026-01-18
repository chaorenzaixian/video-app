<template>
  <Teleport to="body">
    <div v-if="visible" class="lightbox-overlay" @click.self="close">
      <div class="lightbox-container">
        <button class="lightbox-close" @click="close">✕</button>
        <img 
          :src="image" 
          class="lightbox-image"
          :style="{ transform: `scale(${scale})` }"
          @click.stop
        />
        <div class="lightbox-controls">
          <button class="control-btn" @click="zoomOut" title="缩小">
            <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
              <path d="M19 13H5v-2h14v2z"/>
            </svg>
          </button>
          <button class="control-btn" @click="resetZoom" title="重置">
            {{ Math.round(scale * 100) }}%
          </button>
          <button class="control-btn" @click="zoomIn" title="放大">
            <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
              <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  image: { type: String, default: '' }
})

const emit = defineEmits(['update:visible', 'close'])

const scale = ref(1)

watch(() => props.visible, (val) => {
  if (val) scale.value = 1
})

const close = () => {
  emit('update:visible', false)
  emit('close')
}

const zoomIn = () => { scale.value = Math.min(3, scale.value + 0.25) }
const zoomOut = () => { scale.value = Math.max(0.5, scale.value - 0.25) }
const resetZoom = () => { scale.value = 1 }
</script>

<style lang="scss" scoped>
.lightbox-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}

.lightbox-container {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
}

.lightbox-close {
  position: absolute;
  top: -40px;
  right: 0;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: #fff;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  font-size: 18px;
  cursor: pointer;
  
  &:hover { background: rgba(255, 255, 255, 0.2); }
}

.lightbox-image {
  max-width: 90vw;
  max-height: 80vh;
  object-fit: contain;
  transition: transform 0.2s;
}

.lightbox-controls {
  position: absolute;
  bottom: -50px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 12px;
  background: rgba(0, 0, 0, 0.6);
  padding: 8px 16px;
  border-radius: 24px;
  
  .control-btn {
    background: rgba(255, 255, 255, 0.1);
    border: none;
    color: #fff;
    padding: 8px 12px;
    border-radius: 8px;
    cursor: pointer;
    display: flex;
    align-items: center;
    font-size: 12px;
    
    &:hover { background: rgba(255, 255, 255, 0.2); }
  }
}
</style>
