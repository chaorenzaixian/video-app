<template>
  <div class="novel-list">
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="!items.length" class="empty">暂无小说</div>
    <div v-else class="novel-grid">
      <div v-for="item in items" :key="item.id" class="novel-item" @click="$emit('detail', item)">
        <div class="novel-cover-wrap">
          <img :src="item.cover" :alt="item.title" class="novel-cover" />
          <span v-if="isAudio" class="audio-badge">🎧</span>
          <div class="novel-status" v-if="item.status === 'ongoing'">连载中</div>
        </div>
        <div class="novel-info">
          <p class="novel-title">{{ item.title }}</p>
          <p class="novel-author">{{ item.author }}</p>
          <p class="novel-chapters">共{{ item.chapters }}章</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  isAudio: { type: Boolean, default: false }
})

defineEmits(['detail'])
</script>

<style lang="scss" scoped>
.novel-list { padding: 8px 0 0; }

.novel-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px 8px;
  align-items: start;
}

.novel-item { cursor: pointer; display: flex; flex-direction: column; width: 100%; overflow: hidden; }

.novel-cover-wrap {
  position: relative;
  width: 100%;
  height: 0;
  padding-bottom: 133.33%;
  border-radius: 8px;
  overflow: hidden;
  background: #1a1a1a;
}

.novel-cover {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  object-fit: cover;
}

.audio-badge {
  position: absolute; top: 6px; left: 6px;
  background: rgba(0, 0, 0, 0.6);
  padding: 4px 6px; border-radius: 10px; font-size: 12px; z-index: 1;
}

.novel-status {
  position: absolute; top: 6px; right: 6px;
  background: rgba(234, 179, 8, 0.9);
  color: #000; font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 500; z-index: 1;
}

.novel-info { padding: 8px 2px 0; }
.novel-title { color: #eee; font-size: 13px; font-weight: 500; margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; line-height: 1.3; }
.novel-author { color: #888; font-size: 11px; margin-bottom: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.novel-chapters { color: #666; font-size: 11px; }

.loading, .empty { text-align: center; padding: 30px; color: #666; }
</style>
