<template>
  <div class="earnings-page">
    <div class="nav-header">
      <button class="back-btn" @click="$router.push('/creator')">‹</button>
      <h1>收益明细</h1>
      <div></div>
    </div>

    <!-- 收益概览 -->
    <div class="overview-card">
      <div class="overview-item">
        <span class="value">{{ totalEarnings }}</span>
        <span class="label">累计收益(金币)</span>
      </div>
      <div class="overview-item">
        <span class="value">{{ availableCoins }}</span>
        <span class="label">可提现</span>
      </div>
      <div class="overview-item">
        <span class="value">{{ frozenCoins }}</span>
        <span class="label">冻结中</span>
      </div>
    </div>

    <!-- 收益类型筛选 -->
    <div class="filter-tabs">
      <span :class="{ active: filter === 'all' }" @click="filter = 'all'">全部</span>
      <span :class="{ active: filter === 'video_sale' }" @click="filter = 'video_sale'">视频销售</span>
      <span :class="{ active: filter === 'tip' }" @click="filter = 'tip'">打赏收入</span>
    </div>

    <!-- 收益列表 -->
    <div class="earnings-list">
      <div v-for="item in filteredEarnings" :key="item.id" class="earning-item">
        <div class="earning-icon">
          {{ item.earning_type === 'tip' ? '🎁' : '💰' }}
        </div>
        <div class="earning-info">
          <span class="earning-desc">{{ item.description }}</span>
          <span class="earning-time">{{ formatTime(item.created_at) }}</span>
        </div>
        <div class="earning-amount">
          <span class="net">+{{ item.net_amount }}</span>
          <span class="fee" v-if="item.platform_fee > 0">平台费 -{{ item.platform_fee }}</span>
        </div>
      </div>

      <div v-if="filteredEarnings.length === 0" class="empty-state">
        暂无收益记录
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/utils/api'

const earnings = ref([])
const filter = ref('all')
const totalEarnings = ref(0)
const availableCoins = ref(0)
const frozenCoins = ref(0)

const filteredEarnings = computed(() => {
  if (filter.value === 'all') return earnings.value
  return earnings.value.filter(e => e.earning_type === filter.value)
})

const formatTime = (time) => {
  const d = new Date(time)
  return `${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}`
}

const fetchData = async () => {
  try {
    const [dashRes] = await Promise.all([
      api.get('/creator/dashboard')
    ])
    totalEarnings.value = dashRes.data.total_coins_earned
    availableCoins.value = dashRes.data.available_coins
    frozenCoins.value = dashRes.data.frozen_coins
    // TODO: 获取收益列表
  } catch (error) {
    console.error('获取数据失败:', error)
  }
}

onMounted(fetchData)
</script>

<style lang="scss" scoped>
.earnings-page {
  min-height: 100vh;
  background: #0f0f1a;
}

.nav-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: rgba(0, 0, 0, 0.3);
  
  .back-btn {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.1);
    border: none;
    color: #fff;
    font-size: 24px;
  }
  
  h1 { font-size: 18px; color: #fff; margin: 0; }
}

.overview-card {
  margin: 16px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 16px;
  display: flex;
  justify-content: space-around;
  
  .overview-item {
    text-align: center;
    
    .value {
      display: block;
      font-size: 24px;
      font-weight: bold;
      color: #fff;
    }
    
    .label {
      font-size: 12px;
      color: rgba(255,255,255,0.7);
    }
  }
}

.filter-tabs {
  display: flex;
  padding: 12px 16px;
  gap: 16px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  
  span {
    color: rgba(255,255,255,0.5);
    font-size: 14px;
    cursor: pointer;
    
    &.active { color: #667eea; }
  }
}

.earnings-list {
  padding: 16px;
}

.earning-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(255,255,255,0.05);
  border-radius: 12px;
  margin-bottom: 10px;
  
  .earning-icon { font-size: 24px; }
  
  .earning-info {
    flex: 1;
    
    .earning-desc {
      display: block;
      color: #fff;
      font-size: 14px;
    }
    
    .earning-time {
      font-size: 12px;
      color: rgba(255,255,255,0.4);
    }
  }
  
  .earning-amount {
    text-align: right;
    
    .net {
      display: block;
      color: #52c41a;
      font-size: 16px;
      font-weight: bold;
    }
    
    .fee {
      font-size: 11px;
      color: rgba(255,255,255,0.4);
    }
  }
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: rgba(255,255,255,0.4);
}
</style>

