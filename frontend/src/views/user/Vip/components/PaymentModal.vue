<template>
  <div v-if="visible" class="payment-modal" @click.self="$emit('close')">
    <div class="modal-content payment-modal-content">
      <div class="modal-header">
        <span>选择支付方式</span>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>
      <div class="modal-body">
        <div class="payment-methods">
          <div v-for="method in methods" :key="method.type" class="payment-method-item" :class="{ selected: selectedType === method.type }" @click="$emit('update:selectedType', method.type)">
            <span class="method-icon">{{ method.icon }}</span>
            <span class="method-name">{{ method.name }}</span>
            <span class="check-icon" v-if="selectedType === method.type">✓</span>
          </div>
        </div>
        <div class="payment-amount">
          <span>支付金额：</span>
          <span class="amount">¥{{ price }}</span>
        </div>
        <button class="confirm-pay-btn" :disabled="processing" @click="$emit('confirm')">
          {{ processing ? '处理中...' : '确认支付' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  methods: { type: Array, default: () => [] },
  selectedType: { type: String, default: 'alipay' },
  price: { type: [Number, String], default: 0 },
  processing: { type: Boolean, default: false }
})

defineEmits(['close', 'confirm', 'update:selectedType'])
</script>

<style lang="scss" scoped>
.payment-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 20px;
}

.payment-modal-content {
  width: 100%;
  max-width: 360px;
  background: linear-gradient(180deg, #1a1030 0%, #0d0d1a 100%);
  border-radius: 16px;
  border: 1px solid rgba(139, 92, 246, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);

  span { font-size: 18px; font-weight: 600; color: #fff; }

  .close-btn {
    width: 30px;
    height: 30px;
    background: rgba(255, 255, 255, 0.1);
    border: none;
    border-radius: 50%;
    color: #fff;
    font-size: 20px;
    cursor: pointer;
  }
}

.modal-body { padding: 20px; }

.payment-methods {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.payment-method-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;

  &.selected {
    background: rgba(139, 92, 246, 0.2);
    border-color: #a855f7;
  }

  .method-icon { font-size: 24px; }
  .method-name { flex: 1; font-size: 15px; color: #fff; }
  .check-icon { color: #a855f7; font-size: 18px; font-weight: bold; }
}

.payment-amount {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  margin-bottom: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);

  span { color: rgba(255, 255, 255, 0.7); font-size: 14px; }
  .amount { font-size: 22px; font-weight: bold; color: #c084fc; }
}

.confirm-pay-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
  border: none;
  border-radius: 24px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;

  &:active { transform: scale(0.98); opacity: 0.9; }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
}
</style>
