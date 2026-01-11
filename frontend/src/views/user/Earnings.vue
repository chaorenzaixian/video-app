<template>
  <div class="earnings-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()"><img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" /></div>
      <h1 class="page-title">收益明细</h1>
      <div class="placeholder"></div>
    </header>

    <!-- 内容区域 -->
    <div class="content">
      <!-- 空状态 -->
      <div class="empty-state">
        <img src="/images/backgrounds/no_data.webp" alt="暂无数据" class="empty-image" />
        <p class="empty-text">当前页面暂无内容～</p>
      </div>
    </div>
  </div>
</template>

<script setup>
// 暂无需要的逻辑
</script>

<style lang="scss" scoped>
.earnings-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #0d0d15 0%, #0a0a12 100%);
  color: #fff;
}

// 顶部导航
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  padding-top: calc(env(safe-area-inset-top) + 16px);
  background: #000;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  
  .back-btn {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    color: #fff;
    cursor: pointer;
  }
  
  .page-title {
    font-size: 15px;
    font-weight: 600;
    margin: 0;
  }
  
  .placeholder {
    width: 32px;
  }
}

// 内容区域
.content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 80px);
  padding: 20px;
}

// 空状态
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  
  .empty-image {
    width: 180px;
    height: auto;
    margin-bottom: 24px;
    opacity: 0.9;
  }
  
  .empty-text {
    font-size: 14px;
    color: #7c3aed;
    margin: 0;
    letter-spacing: 1px;
  }
}
</style>



