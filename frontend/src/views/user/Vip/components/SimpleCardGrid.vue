<template>
  <div class="simple-cards-section">
    <div class="simple-cards-grid">
      <div v-for="(card, index) in cards" :key="'simple-' + card.id" class="simple-card" :class="{ selected: selectedId === card.id }" @click="$emit('select', card)">
        <div class="simple-badge" :class="getBadgeColorClass(index)" v-if="card.badge_text">{{ card.badge_text }}</div>
        <div class="simple-card-name">{{ card.name }}</div>
        <div class="simple-card-price">
          <span class="currency">¥</span>
          <span class="amount">{{ card.price }}</span>
        </div>
        <div class="simple-card-desc">{{ card.duration_days === 0 ? '永久解锁' : card.duration_days + '天' }}{{ card.description || getLevelBenefit(card.level) }}</div>
        <div class="simple-daily-cost" v-if="card.duration_days > 0">每日仅需{{ (card.price / card.duration_days).toFixed(1) }}元</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { VIP_LEVEL_BENEFITS } from '@/constants/vip'

defineProps({
  cards: { type: Array, default: () => [] },
  selectedId: { type: [Number, String], default: null }
})

defineEmits(['select'])

const getBadgeColorClass = (index) => {
  const colors = ['badge-red', 'badge-orange', 'badge-purple', 'badge-blue', 'badge-green', 'badge-pink']
  return colors[index % colors.length]
}

const getLevelBenefit = (level) => VIP_LEVEL_BENEFITS[level] || 'VIP特权'
</script>

<style lang="scss" scoped>
.simple-cards-section {
  padding: 12px;
  background: linear-gradient(180deg, #1a0a2e 0%, #0d0d1a 100%);
}

.simple-cards-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
}

.simple-card {
  background: linear-gradient(180deg, #2d1b4e 0%, #1a1030 100%);
  border-radius: 8px;
  padding: 10px 4px 8px;
  text-align: center;
  position: relative;
  cursor: pointer;
  border: 1px solid rgba(139, 92, 246, 0.2);
  transition: all 0.3s ease;

  &.selected {
    border-color: #a855f7;
    background: linear-gradient(180deg, #3d2560 0%, #251540 100%);
    box-shadow: 0 0 16px rgba(168, 85, 247, 0.35);
  }

  &:active { transform: scale(0.98); }
}

.simple-badge {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(90deg, #a855f7, #7c3aed);
  color: #fff;
  font-size: 8px;
  font-weight: 600;
  padding: 1px 8px;
  border-radius: 0 0 5px 5px;
  white-space: nowrap;

  &.badge-red { background: linear-gradient(90deg, #ef4444, #dc2626); }
  &.badge-orange { background: linear-gradient(90deg, #f97316, #ea580c); }
  &.badge-purple { background: linear-gradient(90deg, #a855f7, #7c3aed); }
  &.badge-blue { background: linear-gradient(90deg, #3b82f6, #2563eb); }
  &.badge-green { background: linear-gradient(90deg, #22c55e, #16a34a); }
  &.badge-pink { background: linear-gradient(90deg, #ec4899, #db2777); }
}

.simple-card-name {
  font-size: 12px;
  color: #fff;
  font-weight: 600;
  margin-top: 10px;
  margin-bottom: 6px;
}

.simple-card-price {
  display: flex;
  align-items: baseline;
  justify-content: center;
  margin-bottom: 4px;

  .currency { font-size: 12px; color: #c084fc; font-weight: 500; }
  .amount { font-size: 26px; font-weight: 700; color: #c084fc; line-height: 1; }
}

.simple-card-desc {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 4px;
  line-height: 1.3;
}

.simple-daily-cost {
  font-size: 9px;
  color: rgba(192, 132, 252, 0.7);
  margin-top: 2px;
}
</style>
