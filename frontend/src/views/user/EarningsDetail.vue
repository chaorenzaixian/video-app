<template>
  <div class="earnings-detail-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </div>
      <h1 class="page-title">业绩明细</h1>
      <div class="header-right"></div>
    </header>

    <!-- 统计卡片 -->
    <div class="stats-card">
      <div class="stats-item">
        <span class="stats-label">累计收益(金币)</span>
        <span class="stats-value">{{ totalEarnings }}</span>
      </div>
      <div class="stats-divider"></div>
      <div class="stats-item">
        <span class="stats-label">本月收益(金币)</span>
        <span class="stats-value">{{ monthlyEarnings }}</span>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div 
        class="filter-item" 
        :class="{ active: filterType === 'all' }"
        @click="filterType = 'all'"
      >全部</div>
      <div 
        class="filter-item" 
        :class="{ active: filterType === 'video_sale' }"
        @click="filterType = 'video_sale'"
      >视频销售</div>
      <div 
        class="filter-item" 
        :class="{ active: filterType === 'tip' }"
        @click="filterType = 'tip'"
      >打赏</div>
      <div 
        class="filter-item" 
        :class="{ active: filterType === 'bonus' }"
        @click="filterType = 'bonus'"
      >奖励</div>
    </div>

    <!-- 收益列表 -->
    <div class="earnings-list">
      <!-- 加载中 -->
      <div class="loading-state" v-if="isLoading">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>

      <!-- 收益记录 -->
      <template v-else-if="filteredEarnings.length > 0">
        <div class="earnings-item" v-for="item in filteredEarnings" :key="item.id">
          <div class="item-icon" :class="item.earning_type">
            <svg v-if="item.earning_type === 'video_sale'" viewBox="0 0 24 24" fill="currentColor">
              <path d="M18 4l2 4h-3l-2-4h-2l2 4h-3l-2-4H8l2 4H7L5 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V4h-4z"/>
            </svg>
            <svg v-else-if="item.earning_type === 'tip'" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="currentColor">
              <path d="M20 6h-2.18c.11-.31.18-.65.18-1 0-1.66-1.34-3-3-3-1.05 0-1.96.54-2.5 1.35l-.5.67-.5-.68C10.96 2.54 10.05 2 9 2 7.34 2 6 3.34 6 5c0 .35.07.69.18 1H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2z"/>
            </svg>
          </div>
          <div class="item-info">
            <div class="item-title">{{ getEarningTypeText(item.earning_type) }}</div>
            <div class="item-desc">{{ item.description || '收益入账' }}</div>
            <div class="item-time">{{ formatTime(item.created_at) }}</div>
          </div>
          <div class="item-amount">
            <span class="amount">+{{ item.net_amount }}</span>
            <span class="unit">金币</span>
          </div>
        </div>
      </template>

      <!-- 空状态 -->
      <div class="empty-state" v-else>
        <img src="/images/backgrounds/no_data.webp" alt="暂无数据" class="empty-image" />
        <p class="empty-text">暂无收益记录</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/utils/api'

const isLoading = ref(true)
const totalEarnings = ref(0)
const monthlyEarnings = ref(0)
const earnings = ref([])
const filterType = ref('all')

// 筛选后的收益列表
const filteredEarnings = computed(() => {
  if (filterType.value === 'all') {
    return earnings.value
  }
  return earnings.value.filter(item => item.earning_type === filterType.value)
})

// 获取收益类型文本
const getEarningTypeText = (type) => {
  const texts = {
    'video_sale': '视频销售',
    'tip': '用户打赏',
    'bonus': '平台奖励',
    'referral': '推荐奖励'
  }
  return texts[type] || type
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return ''
  const d = new Date(time)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hour = String(d.getHours()).padStart(2, '0')
  const minute = String(d.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hour}:${minute}`
}

// 获取数据
const fetchData = async () => {
  isLoading.value = true
  
  try {
    // 获取仪表盘数据
    const dashRes = await api.get('/creator/dashboard')
    if (dashRes.data) {
      totalEarnings.value = dashRes.data.total_coins_earned || 0
    }
    
    // 获取收益明细
    const earningsRes = await api.get('/creator/earnings')
    if (earningsRes.data) {
      earnings.value = Array.isArray(earningsRes.data) ? earningsRes.data : []
      
      // 计算本月收益
      const now = new Date()
      const thisMonth = earnings.value.filter(item => {
        const itemDate = new Date(item.created_at)
        return itemDate.getMonth() === now.getMonth() && 
               itemDate.getFullYear() === now.getFullYear()
      })
      monthlyEarnings.value = thisMonth.reduce((sum, item) => sum + (item.net_amount || 0), 0)
    }
  } catch (error) {
    if (error.response?.status !== 404) {
      console.error('获取收益数据失败:', error)
    }
  } finally {
    isLoading.value = false
  }
}

onMounted(fetchData)
</script>

<style lang="scss" scoped>
.earnings-detail-page {
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

.stats-card {
  display: flex;
  margin: 0 16px 16px;
  padding: 20px;
  background: linear-gradient(135deg, rgba(30, 25, 40, 0.95), rgba(20, 18, 30, 0.95));
  border: 1px solid rgba(138, 92, 246, 0.3);
  border-radius: 12px;
  
  .stats-item {
    flex: 1;
    text-align: center;
    
    .stats-label {
      display: block;
      font-size: 13px;
      color: rgba(255, 255, 255, 0.6);
      margin-bottom: 8px;
    }
    
    .stats-value {
      font-size: 24px;
      font-weight: 700;
      color: #ffd700;
    }
  }
  
  .stats-divider {
    width: 1px;
    background: rgba(255, 255, 255, 0.1);
    margin: 0 16px;
  }
}

.filter-bar {
  display: flex;
  padding: 0 16px;
  margin-bottom: 16px;
  gap: 12px;
  
  .filter-item {
    padding: 6px 14px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.6);
    background: rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    cursor: pointer;
    transition: all 0.2s;
    
    &.active {
      color: #fff;
      background: linear-gradient(135deg, #667eea, #764ba2);
    }
  }
}

.earnings-list {
  padding: 0 16px 20px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 20px;
  
  .loading-spinner {
    width: 36px;
    height: 36px;
    border: 3px solid rgba(102, 126, 234, 0.3);
    border-top-color: #667eea;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  p {
    margin-top: 12px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.6);
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.earnings-item {
  display: flex;
  align-items: center;
  padding: 14px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 10px;
  margin-bottom: 10px;
  min-height: 72px;
  
  .item-icon {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 12px;
    flex-shrink: 0;
    
    svg {
      width: 20px;
      height: 20px;
      fill: #fff;
    }
    
    &.video_sale {
      background: linear-gradient(135deg, #667eea, #764ba2);
    }
    
    &.tip {
      background: linear-gradient(135deg, #f43f5e, #ec4899);
    }
    
    &.bonus, &.referral {
      background: linear-gradient(135deg, #fbbf24, #f59e0b);
    }
  }
  
  .item-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 2px;
    
    .item-title {
      font-size: 13px;
      font-weight: 500;
      color: #fff;
      line-height: 1.4;
    }
    
    .item-desc {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      line-height: 1.4;
    }
    
    .item-time {
      font-size: 11px;
      color: rgba(255, 255, 255, 0.4);
      line-height: 1.4;
    }
  }
  
  .item-amount {
    text-align: right;
    flex-shrink: 0;
    min-width: 70px;
    
    .amount {
      display: block;
      font-size: 16px;
      font-weight: 600;
      color: #4ade80;
      line-height: 1.4;
    }
    
    .unit {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);
    }
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 20px;
  
  .empty-image {
    width: 100px;
    height: auto;
    margin-bottom: 16px;
    opacity: 0.6;
  }
  
  .empty-text {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.5);
    margin: 0;
  }
}

// 响应式优化
@media (min-width: 768px) {
  .earnings-detail-page {
    max-width: 600px;
    margin: 0 auto;
  }
  
  .page-header {
    max-width: 600px;
    left: 50%;
    transform: translateX(-50%);
  }
  
  .stats-card {
    padding: 24px 30px;
    
    .stats-item .stats-value {
      font-size: 28px;
    }
  }
}

@media (min-width: 1024px) {
  .earnings-detail-page {
    max-width: 700px;
  }
  
  .page-header {
    max-width: 700px;
  }
}

@media (hover: hover) {
  .filter-item:hover {
    background: rgba(255, 255, 255, 0.1);
  }
  
  .earnings-item:hover {
    background: rgba(255, 255, 255, 0.06);
  }
}
</style>



