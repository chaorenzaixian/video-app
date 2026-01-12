<template>
  <div class="comment-skeleton">
    <div class="skeleton-avatar skeleton-animate"></div>
    <div class="skeleton-content">
      <div class="skeleton-name skeleton-animate"></div>
      <div class="skeleton-text skeleton-animate"></div>
      <div class="skeleton-text short skeleton-animate"></div>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.comment-skeleton {
  display: flex;
  gap: 12px;
  padding: 12px 0;
}

.skeleton-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(90deg, #2a2a3e 25%, #3a3a4e 50%, #2a2a3e 75%);
  background-size: 200% 100%;
  flex-shrink: 0;
}

.skeleton-content {
  flex: 1;
}

.skeleton-name {
  width: 80px;
  height: 14px;
  background: linear-gradient(90deg, #2a2a3e 25%, #3a3a4e 50%, #2a2a3e 75%);
  background-size: 200% 100%;
  border-radius: 4px;
  margin-bottom: 8px;
}

.skeleton-text {
  height: 14px;
  background: linear-gradient(90deg, #2a2a3e 25%, #3a3a4e 50%, #2a2a3e 75%);
  background-size: 200% 100%;
  border-radius: 4px;
  margin-bottom: 6px;
}

.skeleton-text.short {
  width: 60%;
}

.skeleton-animate {
  animation: skeleton-loading 1.5s infinite;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
