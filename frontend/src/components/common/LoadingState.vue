<template>
  <!-- 加载中 -->
  <div v-if="loading" class="loading-state">
    <div class="spinner"></div>
    <span v-if="loadingText">{{ loadingText }}</span>
  </div>
  
  <!-- 空状态 -->
  <div v-else-if="empty" class="empty-state">
    <img v-if="emptyImage" :src="emptyImage" class="empty-image" />
    <div v-else class="empty-icon">{{ emptyIcon }}</div>
    <p class="empty-text">{{ emptyText }}</p>
    <button v-if="showRetry" class="retry-btn" @click="$emit('retry')">
      {{ retryText }}
    </button>
  </div>
  
  <!-- 错误状态 -->
  <div v-else-if="error" class="error-state">
    <div class="error-icon">⚠️</div>
    <p class="error-text">{{ errorText }}</p>
    <button class="retry-btn" @click="$emit('retry')">
      重新加载
    </button>
  </div>
  
  <!-- 没有更多 -->
  <div v-else-if="noMore" class="no-more-state">
    <span>{{ noMoreText }}</span>
  </div>
  
  <!-- 默认插槽 -->
  <slot v-else></slot>
</template>

<script setup>
defineProps({
  loading: {
    type: Boolean,
    default: false
  },
  loadingText: {
    type: String,
    default: '加载中...'
  },
  empty: {
    type: Boolean,
    default: false
  },
  emptyText: {
    type: String,
    default: '暂无数据'
  },
  emptyIcon: {
    type: String,
    default: '📭'
  },
  emptyImage: {
    type: String,
    default: ''
  },
  error: {
    type: Boolean,
    default: false
  },
  errorText: {
    type: String,
    default: '加载失败，请重试'
  },
  noMore: {
    type: Boolean,
    default: false
  },
  noMoreText: {
    type: String,
    default: '—— 没有更多了 ——'
  },
  showRetry: {
    type: Boolean,
    default: false
  },
  retryText: {
    type: String,
    default: '点击重试'
  }
})

defineEmits(['retry'])
</script>

<style lang="scss" scoped>
.loading-state,
.empty-state,
.error-state,
.no-more-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: rgba(255, 255, 255, 0.5);
}

.loading-state {
  gap: 12px;
  
  .spinner {
    width: 32px;
    height: 32px;
    border: 3px solid rgba(139, 92, 246, 0.2);
    border-top-color: #8b5cf6;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  
  span {
    font-size: 14px;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty-state {
  gap: 12px;
  
  .empty-image {
    width: 120px;
    height: 120px;
    object-fit: contain;
    opacity: 0.6;
  }
  
  .empty-icon {
    font-size: 48px;
    opacity: 0.6;
  }
  
  .empty-text {
    font-size: 14px;
    margin: 0;
  }
}

.error-state {
  gap: 12px;
  
  .error-icon {
    font-size: 48px;
  }
  
  .error-text {
    font-size: 14px;
    margin: 0;
    color: #ff6b6b;
  }
}

.retry-btn {
  margin-top: 8px;
  padding: 8px 24px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  border-radius: 20px;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    transform: scale(1.05);
  }
  
  &:active {
    transform: scale(0.95);
  }
}

.no-more-state {
  span {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.3);
  }
}
</style>
