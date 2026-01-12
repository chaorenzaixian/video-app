<template>
  <header class="page-header">
    <div class="header-left">
      <div class="notification-wrapper" @click="$router.push('/user/messages')">
        <img src="/images/backgrounds/mine_notification.webp" class="header-icon-img" alt="通知" />
        <span v-if="unreadCount > 0" class="notification-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
      </div>
    </div>
    <div class="header-right">
      <img src="/images/backgrounds/ic_service.webp" class="header-icon-img" alt="客服" @click="$router.push('/user/customer-service')" />
      <img src="/images/backgrounds/ic_setting.webp" class="header-icon-img" alt="设置" @click="$router.push('/user/settings')" />
    </div>
  </header>
</template>

<script setup>
defineProps({
  unreadCount: { type: Number, default: 0 }
})
</script>

<style lang="scss" scoped>
.page-header {
  position: relative;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: clamp(12px, 4vw, 20px) clamp(14px, 5vw, 24px);
  padding-top: calc(clamp(12px, 4vw, 20px) + env(safe-area-inset-top, 0px));

  .header-left, .header-right {
    display: flex;
    align-items: center;
    gap: clamp(14px, 4vw, 20px);
  }

  .header-icon-img {
    width: clamp(22px, 6vw, 28px);
    height: clamp(22px, 6vw, 28px);
    object-fit: contain;
    cursor: pointer;
    transition: transform 0.2s;
    &:hover { transform: scale(1.1); }
  }

  .notification-wrapper {
    position: relative;
    display: inline-flex;
    cursor: pointer;

    .notification-badge {
      position: absolute;
      top: -6px;
      right: -8px;
      min-width: 18px;
      height: 18px;
      padding: 0 5px;
      background: #ff4757;
      color: #fff;
      font-size: 11px;
      font-weight: 600;
      border-radius: 9px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 2px 6px rgba(255, 71, 87, 0.4);
    }
  }
}
</style>
