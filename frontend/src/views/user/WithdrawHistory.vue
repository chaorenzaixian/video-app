<template>
  <div class="withdraw-history-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()"><img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" /></div>
      <h1 class="page-title">提现明细</h1>
      <div class="header-right"></div>
    </header>

    <!-- 提现记录列表 -->
    <div class="history-list">
      <div v-if="loading" class="loading-state">加载中...</div>
      <div v-else-if="!records.length" class="empty-state">暂无提现记录</div>
      <template v-else>
        <div 
          v-for="record in records" 
          :key="record.id" 
          class="history-item"
        >
          <div class="item-left">
            <div class="item-method">
              <span class="method-icon">{{ getMethodIcon(record.method) }}</span>
              <span class="method-name">{{ getMethodName(record.method) }}</span>
            </div>
            <div class="item-time">{{ formatTime(record.created_at) }}</div>
          </div>
          <div class="item-right">
            <div class="item-amount">-{{ record.amount }}</div>
            <div :class="['item-status', record.status]">
              {{ getStatusText(record.status) }}
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- 加载更多 -->
    <div v-if="hasMore" class="load-more" @click="loadMore">
      加载更多
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/utils/api'

const loading = ref(false)
const records = ref([])
const page = ref(1)
const hasMore = ref(false)

// 获取提现方式图标
const getMethodIcon = (method) => {
  const icons = {
    bank: '🏦',
    usdt: '₮',
    alipay: '💳',
    wechat: '💬'
  }
  return icons[method] || '💰'
}

// 获取提现方式名称
const getMethodName = (method) => {
  const names = {
    bank: '银行卡',
    usdt: 'USDT',
    alipay: '支付宝',
    wechat: '微信'
  }
  return names[method] || method
}

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    pending: '审核中',
    processing: '处理中',
    success: '已到账',
    failed: '失败',
    rejected: '已拒绝'
  }
  return statusMap[status] || status
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hour}:${minute}`
}

// 获取提现记录
const fetchRecords = async () => {
  loading.value = true
  try {
    const res = await api.get('/promotion/withdraw/records', {
      params: { page: page.value, limit: 20 }
    })
    const data = res.data || res
    if (page.value === 1) {
      records.value = data.items || []
    } else {
      records.value.push(...(data.items || []))
    }
    hasMore.value = (data.items || []).length === 20
  } catch (error) {
    console.error('获取提现记录失败:', error)
  } finally {
    loading.value = false
  }
}

// 加载更多
const loadMore = () => {
  page.value++
  fetchRecords()
}

onMounted(() => {
  fetchRecords()
})
</script>

<style lang="scss" scoped>
.withdraw-history-page {
  min-height: 100vh;
  background: #0a0a12;
  color: #fff;
}

// 顶部导航
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  padding-top: calc(env(safe-area-inset-top, 16px) + 16px);
  
  .back-btn {
    font-size: 28px;
    color: #fff;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
  }
  
  .page-title {
    font-size: 18px;
    font-weight: 600;
    margin: 0;
  }
  
  .header-right {
    width: 40px;
  }
}

// 记录列表
.history-list {
  padding: 0 16px;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 60px 0;
  color: rgba(255, 255, 255, 0.5);
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  margin-bottom: 12px;
  
  .item-left {
    .item-method {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 6px;
      
      .method-icon {
        font-size: 18px;
      }
      
      .method-name {
        font-size: 15px;
        color: #fff;
      }
    }
    
    .item-time {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);
    }
  }
  
  .item-right {
    text-align: right;
    
    .item-amount {
      font-size: 18px;
      font-weight: 600;
      color: #ef4444;
      margin-bottom: 4px;
    }
    
    .item-status {
      font-size: 12px;
      padding: 2px 8px;
      border-radius: 4px;
      
      &.pending {
        background: rgba(234, 179, 8, 0.2);
        color: #eab308;
      }
      
      &.processing {
        background: rgba(59, 130, 246, 0.2);
        color: #3b82f6;
      }
      
      &.success {
        background: rgba(34, 197, 94, 0.2);
        color: #22c55e;
      }
      
      &.failed,
      &.rejected {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
      }
    }
  }
}

// 加载更多
.load-more {
  text-align: center;
  padding: 16px;
  color: #a855f7;
  cursor: pointer;
}
</style>

