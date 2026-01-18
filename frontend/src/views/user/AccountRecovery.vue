<template>
  <div class="account-recovery-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </div>
      <h1 class="page-title">找回账号</h1>
      <div class="header-right"></div>
    </header>

    <!-- 选项列表 -->
    <div class="recovery-card">
      <div class="recovery-item" @click="goToEmailRecovery">
        <span class="item-label">邮箱找回</span>
        <svg class="arrow-icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
        </svg>
      </div>
      
      <div class="recovery-item" @click="goToCredentialRecovery">
        <span class="item-label">凭证找回</span>
        <svg class="arrow-icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
        </svg>
      </div>
      
      <div class="recovery-item" @click="contactService">
        <span class="item-label">联系客服</span>
        <svg class="arrow-icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
        </svg>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'

import { useRouter } from 'vue-router'
const router = useRouter()

// 邮箱找回
const goToEmailRecovery = () => {
  router.push('/user/settings/recovery/email')
}

// 凭证找回
const goToCredentialRecovery = () => {
  router.push('/user/settings/recovery/credential')
}

// 联系客服
const contactService = () => {
  // 这里可以跳转到客服页面或打开客服链接
  ElMessage.info('客服功能即将上线')
}
</script>

<style lang="scss" scoped>
.account-recovery-page {
  min-height: 100vh;
  background: #0a0a0a;
  color: #fff;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  padding-top: calc(16px + env(safe-area-inset-top, 0px));
  background: #0a0a0a;
  position: sticky;
  top: 0;
  z-index: 100;
  
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
      fill: #fff;
    }
  }
  
  .page-title {
    font-size: 16px;
    font-weight: 600;
    margin: 0;
  }
  
  .header-right {
    width: 32px;
  }
}

.recovery-card {
  margin: 12px;
  background: rgba(25, 30, 45, 0.8);
  border-radius: 16px;
  overflow: hidden;
}

.recovery-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  cursor: pointer;
  transition: background 0.2s;
  
  &:last-child {
    border-bottom: none;
  }
  
  &:active {
    background: rgba(255, 255, 255, 0.05);
  }
  
  .item-label {
    font-size: 14px;
    color: #fff;
  }
  
  .arrow-icon {
    width: 20px;
    height: 20px;
    fill: rgba(255, 255, 255, 0.3);
  }
}

// 响应式优化
@media (min-width: 768px) {
  .account-recovery-page {
    max-width: 500px;
    margin: 0 auto;
  }
  
  .page-header {
    max-width: 500px;
    left: 50%;
    transform: translateX(-50%);
  }
}

@media (min-width: 1024px) {
  .account-recovery-page {
    max-width: 550px;
  }
  
  .page-header {
    max-width: 550px;
  }
}

@media (hover: hover) {
  .recovery-item:hover {
    background: rgba(255, 255, 255, 0.05);
  }
}
</style>



