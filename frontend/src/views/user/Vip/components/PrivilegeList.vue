<template>
  <div class="privileges-section">
    <div class="privileges-list">
      <div v-for="privilege in privileges" :key="privilege.id" class="privilege-item">
        <div class="privilege-icon">
          <img :src="privilege.icon" alt="" />
        </div>
        <div class="privilege-info">
          <div class="privilege-name">{{ privilege.name }}</div>
          <div class="privilege-desc">{{ privilege.description }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  privileges: { type: Array, default: () => [] }
})
</script>

<style lang="scss" scoped>
.privileges-section {
  background: url('/images/backgrounds/vip_recommend.webp') no-repeat center top;
  background-size: 100% auto;
  border-radius: 20px 20px 0 0;
  margin: 0 12px;
  padding: 40px 16px 24px;
  position: relative;
}

.privileges-list {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.privilege-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(139, 92, 246, 0.15);

  &:last-child { border-bottom: none; }
}

.privilege-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  img { width: 44px; height: 44px; object-fit: contain; }
}

.privilege-info {
  flex: 1;

  .privilege-name {
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 4px;
    background: linear-gradient(90deg, #e9d5ff 0%, #a855f7 40%, #7c3aed 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .privilege-desc {
    font-size: 12px;
    background: linear-gradient(90deg, #c084fc 0%, #a855f7 50%, #7c3aed 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.4;
  }
}
</style>
