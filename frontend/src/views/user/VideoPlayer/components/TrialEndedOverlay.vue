<template>
  <div class="trial-ended-overlay" v-if="show">
    <div class="trial-ended-content">
      <h2 class="trial-ended-title">试看结束</h2>
      <p class="trial-ended-subtitle">开通VIP 永久免费观看</p>
      <div class="trial-ended-actions">
        <button class="share-btn" @click="$emit('share')">
          分享得3日VIP
        </button>
        <button class="vip-btn" @click="$emit('openVip')">
          开通VIP免费看
        </button>
      </div>
      <!-- 金币购买选项 -->
      <div class="coin-purchase-option" v-if="showCoinPurchase">
        <span class="divider-text">或</span>
        <div class="coin-price-info" @click="$emit('purchase')">
          <span class="coin-icon">🪙</span>
          <span>{{ price }} 金币购买本片</span>
          <span class="arrow">›</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: {
    type: Boolean,
    default: false
  },
  showCoinPurchase: {
    type: Boolean,
    default: false
  },
  price: {
    type: Number,
    default: 0
  }
})

defineEmits(['share', 'openVip', 'purchase'])
</script>

<style scoped>
.trial-ended-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

.trial-ended-content {
  text-align: center;
  color: #fff;
  padding: 20px;
}

.trial-ended-title {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 8px;
}

.trial-ended-subtitle {
  font-size: 14px;
  color: #aaa;
  margin-bottom: 20px;
}

.trial-ended-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 16px;
}

.share-btn,
.vip-btn {
  padding: 12px 24px;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
}

.share-btn {
  background: transparent;
  border: 1px solid #ec4899;
  color: #ec4899;
}

.vip-btn {
  background: linear-gradient(135deg, #ec4899, #f472b6);
  color: #fff;
}

.coin-purchase-option {
  margin-top: 16px;
}

.divider-text {
  color: #666;
  font-size: 12px;
  display: block;
  margin-bottom: 12px;
}

.coin-price-info {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.1);
  padding: 10px 20px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
}

.coin-price-info:hover {
  background: rgba(255, 255, 255, 0.15);
}

.coin-icon {
  font-size: 16px;
}

.arrow {
  color: #888;
}
</style>
