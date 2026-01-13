<template>
  <Teleport to="body">
    <Transition name="slide-up">
      <div v-if="visible" class="payment-sheet-overlay" @click.self="$emit('close')">
        <div class="payment-sheet">
          <!-- 拖动条 -->
          <div class="sheet-handle"></div>
          
          <!-- 标题 -->
          <h3 class="sheet-title">选择支付方式</h3>
          
          <!-- 支付方式列表 -->
          <div class="payment-methods">
            <div 
              v-for="method in methods" 
              :key="method.type" 
              class="payment-method-item"
              @click="$emit('update:selectedType', method.type)"
            >
              <img :src="method.icon" :alt="method.name" class="method-icon" />
              <span class="method-name">{{ method.name }}</span>
              <div class="radio-circle" :class="{ checked: selectedType === method.type }">
                <span v-if="selectedType === method.type" class="check-mark">✓</span>
              </div>
            </div>
          </div>
          
          <!-- 支付小贴士 -->
          <div class="tips-section">
            <h4 class="tips-title">支付小贴士：</h4>
            <p class="tips-item">1.因超时支付无法到账，请重新发起。</p>
            <p class="tips-item">2.每天发起支付不能超过5次，连续发起且未支付，账号可能被加入黑名单。</p>
          </div>
          
          <!-- 支付按钮 -->
          <button class="pay-btn" :disabled="processing" @click="$emit('confirm')">
            <span v-if="processing">处理中...</span>
            <span v-else>¥{{ price }}/立即支付</span>
          </button>
          
          <!-- 客服链接 -->
          <p class="support-text">
            支付中如有问题，请咨询 <a href="javascript:;" class="link">在线客服</a>
          </p>
        </div>
      </div>
    </Transition>
  </Teleport>
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
.payment-sheet-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 1000;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.payment-sheet {
  width: 100%;
  max-width: 500px;
  background: #fff;
  border-radius: 16px 16px 0 0;
  padding: 12px 20px 32px;
  padding-bottom: calc(env(safe-area-inset-bottom) + 32px);
}

.sheet-handle {
  width: 40px;
  height: 4px;
  background: #ddd;
  border-radius: 2px;
  margin: 0 auto 16px;
}

.sheet-title {
  font-size: 17px;
  font-weight: 600;
  color: #333;
  text-align: center;
  margin: 0 0 20px;
}

.payment-methods {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.payment-method-item {
  display: flex;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  
  &:last-child {
    border-bottom: none;
  }
  
  .method-icon {
    width: 36px;
    height: 36px;
    object-fit: contain;
    margin-right: 12px;
  }
  
  .method-name {
    flex: 1;
    font-size: 16px;
    color: #333;
    font-weight: 500;
  }
  
  .radio-circle {
    width: 22px;
    height: 22px;
    border: 2px solid #ddd;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
    
    &.checked {
      background: #1890ff;
      border-color: #1890ff;
    }
    
    .check-mark {
      color: #fff;
      font-size: 12px;
      font-weight: bold;
    }
  }
}

.tips-section {
  margin: 20px 0;
  
  .tips-title {
    font-size: 14px;
    font-weight: 600;
    color: #333;
    margin: 0 0 8px;
  }
  
  .tips-item {
    font-size: 13px;
    color: #999;
    line-height: 1.6;
    margin: 0;
  }
}

.pay-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
  border: none;
  border-radius: 24px;
  color: #fff;
  font-size: 17px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  
  &:active {
    transform: scale(0.98);
    opacity: 0.9;
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.support-text {
  text-align: center;
  font-size: 14px;
  color: #999;
  margin: 16px 0 0;
  
  .link {
    color: #1890ff;
    text-decoration: none;
    font-weight: 500;
  }
}

/* 动画 */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-active .payment-sheet,
.slide-up-leave-active .payment-sheet {
  transition: transform 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
}

.slide-up-enter-from .payment-sheet,
.slide-up-leave-to .payment-sheet {
  transform: translateY(100%);
}
</style>
