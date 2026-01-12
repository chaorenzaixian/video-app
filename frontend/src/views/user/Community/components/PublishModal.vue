<template>
  <div class="publish-modal-overlay" v-if="visible" @click="$emit('close')">
    <div class="publish-modal" @click.stop>
      <div class="modal-handle"></div>
      <h3 class="modal-title">选择发布类型</h3>
      <div class="publish-types">
        <div class="publish-type-item" @click="$emit('publish', 'image')">
          <img src="/images/backgrounds/publish_img_1.webp" alt="图片" class="type-icon" />
          <span class="type-label">图片</span>
        </div>
        <div class="publish-type-item" @click="$emit('publish', 'video')">
          <img src="/images/backgrounds/publish_video.webp" alt="视频" class="type-icon" />
          <span class="type-label">视频</span>
        </div>
        <div class="publish-type-item" @click="$emit('publish', 'text-image')">
          <img src="/images/backgrounds/publish_img_text.webp" alt="图文" class="type-icon" />
          <span class="type-label">图文</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false }
})

defineEmits(['close', 'publish'])
</script>

<style lang="scss" scoped>
.publish-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  z-index: 200;
  display: flex;
  align-items: flex-end;
}

.publish-modal {
  width: 100%;
  background: linear-gradient(180deg, #1a2a4a 0%, #0d1525 100%);
  border-radius: 20px 20px 0 0;
  padding: 16px 24px 40px;
}

.modal-handle {
  width: 40px; height: 4px;
  background: #444; border-radius: 2px;
  margin: 0 auto 20px;
}

.modal-title {
  text-align: center;
  color: #fff; font-size: 16px; font-weight: 500;
  margin: 0 0 24px;
}

.publish-types {
  display: flex;
  justify-content: center;
  gap: 40px;
}

.publish-type-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  
  .type-icon { width: 56px; height: 56px; object-fit: contain; border-radius: 12px; }
  .type-label { color: #fff; font-size: 14px; }
}
</style>
