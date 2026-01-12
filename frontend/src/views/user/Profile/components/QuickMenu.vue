<template>
  <div class="quick-menu">
    <div class="quick-item" @click="$router.push('/user/history')">
      <div class="quick-icon-img"><img src="/images/backgrounds/ic_history.webp" alt="观看记录" /></div>
      <span>观看记录</span>
    </div>
    <div class="quick-item" @click="$router.push('/user/favorites')">
      <div class="quick-icon-img"><img src="/images/backgrounds/ic_collect.webp" alt="我的收藏" /></div>
      <span>我的收藏</span>
    </div>
    <div class="quick-item" @click="$router.push('/user/purchases')">
      <div class="quick-icon-img"><img src="/images/backgrounds/ic_buy.webp" alt="我的购买" /></div>
      <span>我的购买</span>
    </div>
    <div class="quick-item" @click="$emit('coming-soon')">
      <div class="quick-icon-img"><img src="/images/backgrounds/ic_ai.webp" alt="AI女友" /></div>
      <span>AI女友</span>
    </div>
  </div>
</template>

<script setup>
defineEmits(['coming-soon'])
</script>

<style lang="scss" scoped>
.quick-menu {
  display: flex;
  justify-content: space-between;
  padding: clamp(8px, 2.5vw, 14px) clamp(14px, 5vw, 24px);
  margin: 0 clamp(12px, 4vw, 20px) clamp(6px, 2vw, 10px);
  background: rgba(255, 255, 255, 0.03);
  border-radius: clamp(10px, 3.5vw, 16px);
}

.quick-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: clamp(6px, 2vw, 10px);
  cursor: pointer;
  transition: transform 0.2s;
  &:hover { transform: scale(1.05); }

  .quick-icon-img {
    width: clamp(36px, 11vw, 50px);
    height: clamp(36px, 11vw, 50px);
    border-radius: clamp(8px, 3vw, 14px);
    overflow: hidden;

    img { width: 100%; height: 100%; object-fit: cover; }
  }

  span {
    font-size: clamp(12px, 3vw, 13px);
    color: rgba(255, 255, 255, 0.85);
  }
}
</style>
