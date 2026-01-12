<template>
  <div class="vip-promo" @click="$emit('click')">
    <!-- 非会员样式 -->
    <template v-if="!isVip">
      <span class="promo-text">开通会员 享专属特权</span>
      <div class="promo-btn">
        开通会员 <span class="arrow">›</span>
      </div>
    </template>
    
    <!-- 已是会员样式 -->
    <template v-else>
      <div class="vip-member-center">
        <img 
          v-if="vipLevel > 0" 
          :src="vipLevelIcon" 
          class="vip-icon-promo"
        />
        <span class="vip-expire-text">到期时间：{{ expireDate || '永久' }}</span>
      </div>
      <div class="promo-btn upgrade">
        升级会员 <span class="arrow">›</span>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { VIP_LEVEL_ICONS } from '@/constants/vip'

const props = defineProps({
  isVip: {
    type: Boolean,
    default: false
  },
  vipLevel: {
    type: Number,
    default: 0
  },
  expireDate: {
    type: String,
    default: ''
  }
})

defineEmits(['click'])

const vipLevelIcon = computed(() => {
  return VIP_LEVEL_ICONS[props.vipLevel] || ''
})
</script>

<style scoped>
.vip-promo {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  padding: 12px 16px;
  cursor: pointer;
}

.promo-text {
  color: #ffd700;
  font-size: 14px;
  font-weight: 500;
}

.promo-btn {
  background: linear-gradient(135deg, #ffd700, #ffb700);
  color: #1a1a2e;
  padding: 6px 16px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
}

.promo-btn.upgrade {
  background: linear-gradient(135deg, #ec4899, #f472b6);
  color: #fff;
}

.arrow {
  margin-left: 4px;
}

.vip-member-center {
  display: flex;
  align-items: center;
  gap: 8px;
}

.vip-icon-promo {
  width: 20px;
  height: 20px;
}

.vip-expire-text {
  color: #ffd700;
  font-size: 13px;
}
</style>
