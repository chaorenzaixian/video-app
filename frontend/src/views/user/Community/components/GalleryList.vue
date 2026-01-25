<template>
  <div class="gallery-list">
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="!items.length" class="empty">暂无图集</div>
    <div v-else class="gallery-grid">
      <div v-for="item in items" :key="item.id" class="gallery-item" @click="$emit('detail', item.id)">
        <div class="gallery-cover">
          <img :src="item.cover" :alt="item.title" />
          <div class="gallery-info">
            <span class="views">👁 {{ formatCount(item.views) }}</span>
            <span class="count">📷 {{ item.count }}</span>
          </div>
          <div class="gallery-status" v-if="item.status === 'ongoing'">连载中</div>
        </div>
        <p class="gallery-title">{{ item.title }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { formatCount } from '@/utils/format'

defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
})

defineEmits(['detail'])
</script>

<style lang="scss" scoped>
.gallery-list { padding: 8px 0 0; }

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px 8px;
}

.gallery-item { 
  cursor: pointer;
  width: 100%;
  min-width: 0;
  overflow: hidden;
}

.gallery-cover {
  position: relative;
  width: 100%;
  height: 0 !important;
  padding-top: 133.33% !important; /* 3:4比例 = 4/3 * 100% */
  border-radius: 8px;
  overflow: hidden;
  background: #1a1a1a;
  
  img { 
    position: absolute !important; 
    top: 0 !important; 
    left: 0 !important; 
    width: 100% !important; 
    height: 100% !important; 
    object-fit: cover !important; 
  }
}

.gallery-info {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  padding: 6px 8px;
  background: linear-gradient(transparent, rgba(0,0,0,0.8));
  display: flex; justify-content: space-between;
  font-size: 11px; color: #fff;
}

.gallery-status {
  position: absolute; top: 6px; right: 6px;
  background: rgba(139, 92, 246, 0.9);
  color: #fff; font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 500;
}

.gallery-title {
  color: #eee; font-size: 13px; font-weight: 500;
  margin: 8px 2px 4px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; line-height: 1.3;
}

.loading, .empty { text-align: center; padding: 30px; color: #666; }

@media (min-width: 480px) { .gallery-grid { grid-template-columns: repeat(4, 1fr); gap: 16px; } }
@media (min-width: 768px) { .gallery-grid { grid-template-columns: repeat(5, 1fr); gap: 20px; } .gallery-title { font-size: 14px; } }
@media (min-width: 1024px) { .gallery-grid { grid-template-columns: repeat(6, 1fr); } }
</style>
