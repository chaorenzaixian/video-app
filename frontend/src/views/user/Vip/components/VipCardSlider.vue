<template>
  <div class="vip-cards-section">
    <div class="cards-scroll" ref="cardsScrollRef">
      <div v-for="card in cards" :key="card.id" class="vip-card" :class="{ selected: selectedId === card.id }" @click="$emit('select', card)">
        <img :src="card.background_image" class="card-bg" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, defineExpose } from 'vue'

defineProps({
  cards: { type: Array, default: () => [] },
  selectedId: { type: [Number, String], default: null }
})

defineEmits(['select'])

const cardsScrollRef = ref(null)

defineExpose({ cardsScrollRef })
</script>

<style lang="scss" scoped>
.vip-cards-section {
  padding: 0 0 0 12px;
  margin-bottom: 12px;
}

.cards-scroll {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-right: 12px;
  padding-bottom: 8px;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
  &::-webkit-scrollbar { display: none; }
}

.vip-card {
  flex-shrink: 0;
  width: 160px;
  height: 220px;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
  cursor: pointer;
  scroll-snap-align: start;
  transition: all 0.3s ease;
  border: 2px solid transparent;

  &.selected {
    border-color: #a855f7;
    box-shadow: 0 0 16px rgba(168, 85, 247, 0.4);
  }

  .card-bg {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}
</style>
