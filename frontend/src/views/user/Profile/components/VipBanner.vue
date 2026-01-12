<template>
  <div class="vip-banner" @click="$router.push('/user/vip')">
    <div class="vip-stars">
      <span class="star s1">✦</span><span class="star s2">✦</span><span class="star s3">✦</span><span class="star s4">✦</span>
    </div>
    <template v-if="!isVip">
      <div class="vip-left">
        <span class="vip-text"><span class="text-gradient">开通会员</span><span class="text-gradient-light">享专属特权</span></span>
      </div>
      <div class="vip-btn"><span>开通会员</span><div class="arrow-circle"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/></svg></div></div>
    </template>
    <template v-else>
      <div class="vip-left">
        <div class="vip-member-content">
          <img v-if="vipLevel > 0" :src="vipLevelIcon" class="vip-icon-inline" :alt="vipLevelName" />
          <span class="vip-expire-inline">到期时间：{{ expireDate || '永久' }}</span>
        </div>
      </div>
      <div class="vip-btn" @click.stop="$router.push('/user/vip')"><span>升级会员</span><div class="arrow-circle"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/></svg></div></div>
    </template>
  </div>
</template>

<script setup>
defineProps({
  isVip: { type: Boolean, default: false },
  vipLevel: { type: Number, default: 0 },
  vipLevelIcon: { type: String, default: '' },
  vipLevelName: { type: String, default: '' },
  expireDate: { type: String, default: '' }
})
</script>

<style lang="scss" scoped>
.vip-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: clamp(6px, 2vw, 10px) clamp(12px, 4vw, 20px);
  padding: clamp(12px, 3.5vw, 16px) clamp(12px, 4vw, 20px);
  min-height: clamp(60px, 18vw, 80px);
  background-image: url("/images/backgrounds/vipbg.webp");
  background-size: 100% 100%;
  background-position: center;
  background-repeat: no-repeat;
  border-radius: clamp(10px, 3.5vw, 16px);
  cursor: pointer;
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 0 15px rgba(255, 255, 255, 0.15), 0 8px 20px rgba(0, 0, 0, 0.3);
  transition: transform 0.3s ease, box-shadow 0.3s ease;

  &:hover { transform: translateY(-2px); }
}

.vip-stars {
  position: absolute;
  inset: 0;
  pointer-events: none;

  .star {
    position: absolute;
    color: rgba(255, 200, 150, 0.7);
    animation: star-twinkle 2s ease-in-out infinite;
    &.s1 { top: 12%; right: 12%; font-size: clamp(8px, 2.5vw, 12px); animation-delay: 0s; }
    &.s2 { top: 50%; right: 8%; font-size: clamp(6px, 2vw, 10px); animation-delay: 0.5s; }
    &.s3 { top: 70%; right: 15%; font-size: clamp(10px, 3vw, 14px); animation-delay: 1s; }
    &.s4 { top: 30%; right: 5%; font-size: clamp(5px, 1.5vw, 8px); animation-delay: 1.5s; }
  }
}

.vip-left {
  display: flex;
  align-items: center;
  position: relative;
  z-index: 1;
  margin-left: 15%;

  .vip-text {
    font-size: clamp(10px, 3vw, 13px);
    font-weight: 600;
    display: flex;
    gap: clamp(3px, 1vw, 5px);

    .text-gradient, .text-gradient-light {
      background: linear-gradient(135deg, #ffd700 0%, #ffec8b 50%, #daa520 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
  }
}

.vip-btn {
  display: flex;
  align-items: center;
  gap: clamp(3px, 1vw, 5px);
  padding: clamp(5px, 1.5vw, 8px) clamp(10px, 3vw, 14px) clamp(5px, 1.5vw, 8px) clamp(12px, 3.5vw, 16px);
  background: linear-gradient(135deg, #ffd700 0%, #f0c14b 50%, #daa520 100%);
  border-radius: clamp(16px, 5vw, 24px);
  font-size: clamp(11px, 3vw, 14px);
  color: #3d2a1a;
  font-weight: 600;
  position: relative;
  z-index: 1;
  box-shadow: 0 2px 8px rgba(255, 215, 0, 0.3);

  .arrow-circle {
    width: clamp(14px, 4vw, 18px);
    height: clamp(14px, 4vw, 18px);
    background: rgba(61, 42, 26, 0.15);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;

    svg { width: clamp(8px, 2.5vw, 12px); height: clamp(8px, 2.5vw, 12px); fill: #5a4a3a; }
  }
}

.vip-member-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: clamp(4px, 1.5vw, 6px);

  .vip-icon-inline {
    height: clamp(22px, 6vw, 30px);
    width: auto;
    object-fit: contain;
    filter: drop-shadow(0 1px 3px rgba(0, 0, 0, 0.3));
  }

  .vip-expire-inline {
    font-size: clamp(11px, 3vw, 13px);
    background: linear-gradient(135deg, #ffd700 0%, #ffec8b 50%, #daa520 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    white-space: nowrap;
    font-weight: 600;
  }
}

@keyframes star-twinkle {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.2); }
}
</style>
