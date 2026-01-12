<template>
  <div class="video-card-skeleton">
    <div class="skeleton-cover skeleton-animate"></div>
    <div class="skeleton-info">
      <div class="skeleton-title skeleton-animate"></div>
      <div class="skeleton-meta">
        <div class="skeleton-tag skeleton-animate"></div>
        <div class="skeleton-views skeleton-animate"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.video-card-skeleton {
  background: var(--card-bg, #1a1a2e);
  border-radius: 8px;
  overflow: hidden;
}

.skeleton-cover {
  width: 100%;
  padding-bottom: 56.25%; /* 16:9 */
  background: linear-gradient(90deg, #2a2a3e 25%, #3a3a4e 50%, #2a2a3e 75%);
  background-size: 200% 100%;
}

.skeleton-info {
  padding: 10px;
}

.skeleton-title {
  height: 16px;
  background: linear-gradient(90deg, #2a2a3e 25%, #3a3a4e 50%, #2a2a3e 75%);
  background-size: 200% 100%;
  border-radius: 4px;
  margin-bottom: 8px;
}

.skeleton-meta {
  display: flex;
  gap: 8px;
}

.skeleton-tag {
  width: 40px;
  height: 12px;
  background: linear-gradient(90deg, #2a2a3e 25%, #3a3a4e 50%, #2a2a3e 75%);
  background-size: 200% 100%;
  border-radius: 4px;
}

.skeleton-views {
  width: 60px;
  height: 12px;
  background: linear-gradient(90deg, #2a2a3e 25%, #3a3a4e 50%, #2a2a3e 75%);
  background-size: 200% 100%;
  border-radius: 4px;
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
