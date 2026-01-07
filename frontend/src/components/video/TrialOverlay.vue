<template>
  <div class="trial-overlay" v-if="visible">
    <div class="trial-content">
      <h2 class="trial-title">试看结束</h2>
      <p class="trial-subtitle">开通VIP 永久免费观看</p>
      
      <div class="trial-actions">
        <button class="share-btn" @click="$emit('share')">
          分享得3日VIP
        </button>
        <button class="vip-btn" @click="$emit('openVip')">
          开通VIP免费看
        </button>
      </div>
      
      <!-- 金币购买选项 -->
      <div class="coin-purchase-option" v-if="showCoinPurchase && coinPrice > 0">
        <span class="divider-text">或</span>
        <div class="coin-price-info" @click="$emit('purchase')">
          <span class="coin-icon">🪙</span>
          <span>{{ displayPrice }} 金币购买本片</span>
          <span class="arrow">›</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  coinPrice: {
    type: Number,
    default: 0
  },
  vipDiscount: {
    type: Number,
    default: 1
  },
  isVip: {
    type: Boolean,
    default: false
  },
  showCoinPurchase: {
    type: Boolean,
    default: true
  }
})

defineEmits(['share', 'openVip', 'purchase'])

// 计算实际价格（考虑VIP折扣）
const displayPrice = computed(() => {
  if (!props.coinPrice) return 0
  if (props.isVip && props.vipDiscount && props.vipDiscount < 1) {
    return Math.ceil(props.coinPrice * props.vipDiscount)
  }
  return props.coinPrice
})
</script>

<style lang="scss" scoped>
.trial-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

.trial-content {
  text-align: center;
  padding: 30px;
  max-width: 320px;
}

.trial-title {
  font-size: 24px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 8px;
}

.trial-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0 0 24px;
}

.trial-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 20px;
  
  button {
    padding: 12px 24px;
    border-radius: 24px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    border: none;
    
    &:hover {
      transform: scale(1.05);
    }
    
    &:active {
      transform: scale(0.95);
    }
  }
  
  .share-btn {
    background: rgba(255, 255, 255, 0.1);
    color: #fff;
    border: 1px solid rgba(255, 255, 255, 0.3);
  }
  
  .vip-btn {
    background: linear-gradient(135deg, #ffd700, #ffb700);
    color: #000;
  }
}

.coin-purchase-option {
  .divider-text {
    display: block;
    color: rgba(255, 255, 255, 0.4);
    font-size: 13px;
    margin-bottom: 12px;
  }
  
  .coin-price-info {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 12px 20px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 24px;
    cursor: pointer;
    transition: all 0.2s;
    
    &:hover {
      background: rgba(255, 255, 255, 0.15);
    }
    
    .coin-icon {
      font-size: 18px;
    }
    
    span {
      color: #fff;
      font-size: 14px;
    }
    
    .arrow {
      color: rgba(255, 255, 255, 0.5);
    }
  }
}
</style>
