<template>
  <Teleport to="body">
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
  </Teleport>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false }
})

defineEmits(['close', 'publish'])
</script>

<style lang="scss">
/* 使用全局样式，因为 Teleport 到 body 后 scoped 不生效 */
.publish-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  z-index: 10000; /* 确保在最顶层 */
  display: flex;
  align-items: flex-end;
}

.publish-modal {
  width: 100%;
  max-width: 750px;
  margin: 0 auto;
  background: linear-gradient(180deg, #1a2a4a 0%, #0d1525 100%);
  border-radius: 20px 20px 0 0;
  padding: 16px 24px calc(80px + var(--safe-area-bottom, 0px));
  
  @media (min-width: 768px) {
    max-width: 750px;
  }
  @media (min-width: 1024px) {
    max-width: 900px;
  }
}

.publish-modal .modal-handle {
  width: 40px;
  height: 4px;
  background: #444;
  border-radius: 2px;
  margin: 0 auto 20px;
}

.publish-modal .modal-title {
  text-align: center;
  color: #fff;
  font-size: 16px;
  font-weight: 500;
  margin: 0 0 24px;
}

.publish-modal .publish-types {
  display: flex;
  justify-content: center;
  gap: 40px;
}

.publish-modal .publish-type-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.publish-modal .publish-type-item .type-icon {
  width: 56px;
  height: 56px;
  object-fit: contain;
  border-radius: 12px;
}

.publish-modal .publish-type-item .type-label {
  color: #fff;
  font-size: 14px;
}
</style>
