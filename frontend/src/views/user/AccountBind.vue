<template>
  <div class="account-bind-page">
    <header class="page-header">
      <div class="back-btn" @click="$router.back()">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
        </svg>
      </div>
      <h1 class="page-title">账号绑定</h1>
    </header>
    
    <div class="bind-content">
      <div class="bind-item">
        <div class="bind-icon">📱</div>
        <div class="bind-info">
          <span class="bind-label">手机号</span>
          <span class="bind-status">{{ user.phone || '未绑定' }}</span>
        </div>
        <button class="bind-btn">{{ user.phone ? '更换' : '绑定' }}</button>
      </div>
      
      <div class="bind-item">
        <div class="bind-icon">📧</div>
        <div class="bind-info">
          <span class="bind-label">邮箱</span>
          <span class="bind-status">{{ user.email || '未绑定' }}</span>
        </div>
        <button class="bind-btn">{{ user.email ? '更换' : '绑定' }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const user = computed(() => userStore.user || {})
</script>

<style lang="scss" scoped>
.account-bind-page {
  min-height: 100vh;
  background: #0a0a0f;
  color: #fff;
}

.page-header {
  display: flex;
  align-items: center;
  padding: 16px;
  background: rgba(255, 255, 255, 0.05);
  
  .back-btn {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    
    svg {
      width: 24px;
      height: 24px;
    }
  }
  
  .page-title {
    flex: 1;
    text-align: center;
    font-size: 18px;
    font-weight: 600;
    margin-right: 32px;
  }
}

.bind-content {
  padding: 20px 16px;
}

.bind-item {
  display: flex;
  align-items: center;
  padding: 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  margin-bottom: 12px;
  
  .bind-icon {
    font-size: 24px;
    margin-right: 12px;
  }
  
  .bind-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    
    .bind-label {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.6);
    }
    
    .bind-status {
      font-size: 16px;
      margin-top: 4px;
    }
  }
  
  .bind-btn {
    padding: 8px 16px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    border-radius: 20px;
    color: #fff;
    font-size: 14px;
    cursor: pointer;
  }
}
</style>





