<template>
  <div class="video-list-skeleton" :class="{ 'double-column': columns === 2 }">
    <VideoCardSkeleton v-for="i in count" :key="i" />
  </div>
</template>

<script setup>
import VideoCardSkeleton from './VideoCardSkeleton.vue'

defineProps({
  count: {
    type: Number,
    default: 6
  },
  columns: {
    type: Number,
    default: 2
  }
})
</script>

<style scoped>
.video-list-skeleton {
  display: grid;
  gap: 12px;
  padding: 12px;
}

.video-list-skeleton.double-column {
  grid-template-columns: repeat(2, 1fr);
}
</style>
