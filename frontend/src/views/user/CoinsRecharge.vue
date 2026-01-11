<template>
  <div class="coins-recharge-page">
    <!-- 顶部导航 -->
    <div class="nav-header">
      <button class="back-btn" @click="$router.back()">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </button>
      <h1>金币充值</h1>
      <button class="history-btn" @click="showHistory = true">充值记录</button>
    </div>

    <!-- 余额卡片 -->
    <div class="balance-section">
    <div class="balance-card">
        <img src="/images/backgrounds/rg_header_bg.webp" alt="" class="card-bg" />
        <div class="card-content">
      <div class="balance-info">
            <div class="balance-header">
              <span class="label">我的金币余额</span>
              <button class="detail-btn" @click="showHistory = true">明细</button>
            </div>
            <div class="balance-amount">{{ coinBalance.balance || 0 }}</div>
          </div>
          <img src="/images/backgrounds/ic_coin.webp" alt="金币" class="coin-icon" />
      </div>
      </div>
    </div>

    <!-- 充值套餐 -->
    <div class="packages-section">
      <div class="section-header">
        <span class="title">余额充值</span>
        <span class="subtitle">多充多送</span>
      </div>
      
      <div class="packages-grid">
        <div 
          v-for="pkg in packages" 
          :key="pkg.id"
          class="package-card"
          :class="{ 'selected': selectedPackage?.id === pkg.id }"
          @click="selectedPackage = pkg"
        >
          <!-- 赠送标签 -->
          <div class="bonus-tag" v-if="pkg.bonus_coins > 0">
            <img src="/images/backgrounds/ic_gift.webp" alt="" class="gift-icon" />
            <span>赠送{{ pkg.bonus_coins }}金币</span>
          </div>
          
          <!-- 金币图标 -->
          <div class="coin-icon-wrapper">
            <img src="/images/backgrounds/ic_coin.webp" alt="" class="pkg-coin-icon" />
    </div>

          <!-- 金币数量 -->
          <div class="coins-amount">{{ pkg.coins }}金币</div>
          
          <!-- 价格 -->
          <div class="price">{{ pkg.price }}RMB</div>
        </div>
      </div>
    </div>

    <!-- 底部区域 -->
    <div class="bottom-section">
      <p class="tips">
        *如提示【交易失败】【账户风险】等，可重新发起订单，或在15分钟后重试支付。如支付未到账，请
        <a href="javascript:;" class="link">反馈客服订单号</a>
      </p>
      
      <button 
        class="pay-btn"
        :disabled="!selectedPackage || isProcessing"
        @click="handleRecharge"
      >
        <span v-if="isProcessing">处理中...</span>
        <span v-else-if="selectedPackage">¥{{ selectedPackage.price }}/立即支付</span>
        <span v-else>请选择充值套餐</span>
      </button>
      
      <p class="support-text">
        支付问题反馈，点击联系 <a href="javascript:;" class="link">在线客服</a>
      </p>
    </div>

    <!-- 交易记录弹窗 -->
    <div v-if="showHistory" class="history-modal" @click.self="showHistory = false">
      <div class="modal-content">
        <div class="modal-header">
          <span>金币明细</span>
          <button class="close-btn" @click="showHistory = false">×</button>
        </div>
        <div class="modal-tabs">
          <span 
            :class="{ active: historyTab === 'all' }"
            @click="historyTab = 'all'"
          >全部</span>
          <span 
            :class="{ active: historyTab === 'recharge' }"
            @click="historyTab = 'recharge'"
          >充值</span>
          <span 
            :class="{ active: historyTab === 'purchase' }"
            @click="historyTab = 'purchase'"
          >消费</span>
        </div>
        <div class="modal-body">
          <div 
            v-for="record in filteredTransactions" 
            :key="record.id" 
            class="record-item"
          >
            <div class="record-info">
              <span class="record-type">{{ getTransactionTypeName(record.transaction_type) }}</span>
              <span class="record-desc">{{ record.description }}</span>
              <span class="record-time">{{ formatTime(record.created_at) }}</span>
            </div>
            <span 
              class="record-amount"
              :class="record.amount > 0 ? 'positive' : 'negative'"
            >
              {{ record.amount > 0 ? '+' : '' }}{{ record.amount }}
            </span>
          </div>
          <div v-if="filteredTransactions.length === 0" class="empty-state">
            暂无记录
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const router = useRouter()

const coinBalance = ref({
  balance: 0,
  total_recharged: 0,
  total_spent: 0,
  total_earned: 0,
  frozen: 0
})
const packages = ref([])
const selectedPackage = ref(null)
const isProcessing = ref(false)
const showHistory = ref(false)
const historyTab = ref('all')
const transactions = ref([])

const filteredTransactions = computed(() => {
  if (historyTab.value === 'all') return transactions.value
  if (historyTab.value === 'recharge') {
    return transactions.value.filter(t => t.amount > 0)
  }
  return transactions.value.filter(t => t.amount < 0)
})

const getTransactionTypeName = (type) => {
  const types = {
    'recharge': '充值',
    'purchase': '购买视频',
    'tip': '打赏',
    'earn': '收益',
    'refund': '退款',
    'withdraw': '提现',
    'admin': '系统调整'
  }
  return types[type] || type
}

const formatTime = (time) => {
  const d = new Date(time)
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

const fetchBalance = async () => {
  try {
    const res = await api.get('/coins/balance')
    coinBalance.value = res.data
  } catch (error) {
    console.error('获取余额失败:', error)
  }
}

const fetchPackages = async () => {
  try {
    const res = await api.get('/coins/packages')
    packages.value = res.data
    // 默认选中第三个（如图所示）
    if (packages.value.length >= 3) {
      selectedPackage.value = packages.value[2]
    } else if (packages.value.length > 0) {
      selectedPackage.value = packages.value[0]
    }
  } catch (error) {
    console.error('获取套餐失败:', error)
  }
}

const fetchTransactions = async () => {
  try {
    const res = await api.get('/coins/transactions')
    transactions.value = res.data
  } catch (error) {
    console.error('获取交易记录失败:', error)
  }
}

const handleRecharge = async () => {
  if (!selectedPackage.value) {
    ElMessage.warning('请选择充值套餐')
    return
  }
  
  isProcessing.value = true
  try {
    // 创建订单
    const res = await api.post('/coins/recharge', {
      package_id: selectedPackage.value.id,
      payment_method: 'alipay'
    })
    
    // 模拟支付(开发测试)
    const payRes = await api.post(`/coins/pay/${res.data.order_no}/simulate`)
    
    ElMessage.success(payRes.data.message || '充值成功')
    await fetchBalance()
    await fetchTransactions()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '充值失败')
  } finally {
    isProcessing.value = false
  }
}

onMounted(() => {
  fetchBalance()
  fetchPackages()
  fetchTransactions()
})
</script>

<style lang="scss" scoped>
.coins-recharge-page {
  min-height: 100vh;
  min-height: 100dvh;
  background: linear-gradient(180deg, #1a0a2e 0%, #0d0d1a 50%, #0a0a0a 100%);
  padding-bottom: env(safe-area-inset-bottom);
  display: flex;
  flex-direction: column;
}

// 顶部导航
.nav-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  padding-top: calc(env(safe-area-inset-top, 10px) + 10px);
  
  .back-btn {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: transparent;
    border: none;
    color: #fff;
    font-size: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
  }
  
  h1 {
    font-size: 16px;
    color: #fff;
    margin: 0;
    font-weight: 500;
  }
  
  .history-btn {
    background: none;
    border: none;
    color: rgba(255, 255, 255, 0.7);
    font-size: 12px;
    cursor: pointer;
  }
}

// 余额卡片区域
.balance-section {
  padding: 0 12px;
  margin-bottom: 14px;
}

.balance-card {
  position: relative;
  border-radius: 12px;
  overflow: visible;
  
  .card-bg {
    width: 100%;
    height: auto;
    display: block;
    border-radius: 12px;
  }
  
  .card-content {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 1;
  display: flex;
    justify-content: space-between;
  align-items: center;
    padding: 14px 18px;
  }
  
  .balance-info {
    .balance-header {
    display: flex;
    align-items: center;
      gap: 10px;
      margin-bottom: 6px;
    
    .label {
        font-size: 13px;
        color: rgba(255, 255, 255, 0.9);
      }
      
      .detail-btn {
        background: rgba(255, 255, 255, 0.25);
        border: none;
        color: #fff;
        font-size: 11px;
        padding: 3px 10px;
        border-radius: 10px;
        cursor: pointer;
        backdrop-filter: blur(4px);
      }
    }
    
    .balance-amount {
      font-size: 36px;
      font-weight: 300;
      color: #fff;
      line-height: 1;
    }
  }
  
  .coin-icon {
    width: 60px;
    height: 60px;
    object-fit: contain;
    filter: drop-shadow(0 3px 8px rgba(255, 200, 0, 0.4));
  }
}

// 充值套餐区域
.packages-section {
  flex: 1;
  padding: 0 12px;
  
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    
    .title {
      font-size: 14px;
      color: #e6a23c;
      font-weight: 500;
    }
    
    .subtitle {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);
    }
  }
}

.packages-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.package-card {
  background: linear-gradient(180deg, rgba(30, 27, 75, 0.8) 0%, rgba(20, 18, 50, 0.9) 100%);
  border: 2px solid rgba(100, 80, 180, 0.3);
  border-radius: 10px;
  padding: 8px 6px 12px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  
  &.selected {
    border-color: #6366f1;
    background: linear-gradient(180deg, rgba(99, 102, 241, 0.2) 0%, rgba(30, 27, 75, 0.9) 100%);
    box-shadow: 0 0 16px rgba(99, 102, 241, 0.3);
  }
  
  &:active {
    transform: scale(0.98);
  }
  
  .bonus-tag {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 3px;
    background: linear-gradient(90deg, rgba(168, 85, 247, 0.9) 0%, rgba(139, 92, 246, 0.9) 100%);
    color: #fff;
    font-size: 9px;
    padding: 2px 6px;
    border-radius: 8px;
    margin: -8px auto 6px;
    width: fit-content;
    position: relative;
    top: 0;
    
    .gift-icon {
      width: 12px;
      height: 12px;
      object-fit: contain;
    }
  }
  
  .coin-icon-wrapper {
    margin: 8px auto;
    
    .pkg-coin-icon {
      width: 36px;
      height: 36px;
      object-fit: contain;
      filter: drop-shadow(0 2px 6px rgba(255, 200, 0, 0.3));
    }
  }
  
  .coins-amount {
    font-size: 13px;
    font-weight: 600;
      color: #fff;
    margin-bottom: 4px;
    }
    
    .price {
    font-size: 12px;
    color: #e6a23c;
    font-weight: 500;
  }
}

// 底部区域
.bottom-section {
  padding: 16px 12px;
  padding-bottom: calc(env(safe-area-inset-bottom) + 16px);
  margin-top: auto;
  
  .tips {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.5);
    line-height: 1.5;
    margin-bottom: 12px;
    
    .link {
      color: #6366f1;
      text-decoration: none;
    }
  }
  
  .pay-btn {
    width: 100%;
    padding: 10px;
    background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
    border: none;
    border-radius: 22px;
    color: #fff;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 3px 16px rgba(99, 102, 241, 0.4);
    
    &:active {
      transform: scale(0.98);
    }
    
    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
  
  .support-text {
    text-align: center;
    font-size: 11px;
    color: rgba(255, 255, 255, 0.5);
    margin-top: 10px;
    
    .link {
      color: #6366f1;
      text-decoration: none;
    }
  }
}

// 交易记录弹窗
.history-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: flex-end;
  z-index: 200;
  
  .modal-content {
    width: 100%;
    max-height: 70vh;
    background: #1a1a2e;
    border-radius: 16px 16px 0 0;
    display: flex;
    flex-direction: column;
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    
    span {
      font-size: 15px;
      font-weight: bold;
      color: #fff;
    }
    
    .close-btn {
      width: 26px;
      height: 26px;
      background: rgba(255, 255, 255, 0.1);
      border: none;
      border-radius: 50%;
      color: #fff;
      font-size: 16px;
      cursor: pointer;
    }
  }
  
  .modal-tabs {
    display: flex;
    padding: 10px 16px;
    gap: 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    
    span {
      color: rgba(255, 255, 255, 0.5);
      font-size: 12px;
      cursor: pointer;
      padding-bottom: 6px;
      
      &.active {
        color: #6366f1;
        border-bottom: 2px solid #6366f1;
      }
    }
  }
  
  .modal-body {
    flex: 1;
    overflow-y: auto;
    padding: 0 16px;
  }
  
  .record-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    
    .record-info {
      display: flex;
      flex-direction: column;
      gap: 3px;
      
      .record-type {
        font-size: 12px;
        color: #fff;
      }
      
      .record-desc {
        font-size: 11px;
        color: rgba(255, 255, 255, 0.5);
      }
      
      .record-time {
        font-size: 10px;
        color: rgba(255, 255, 255, 0.3);
      }
    }
    
    .record-amount {
      font-size: 15px;
      font-weight: bold;
      
      &.positive {
        color: #52c41a;
      }
      
      &.negative {
        color: #ff6b6b;
      }
    }
  }
  
  .empty-state {
    text-align: center;
    padding: 30px;
    color: rgba(255, 255, 255, 0.4);
    font-size: 12px;
  }
}

// ============ 响应式适配 ============
@media (max-width: 374px) {
  .packages-grid {
    gap: 6px;
  }
  
  .package-card {
    padding: 6px 4px 10px;
    
    .bonus-tag {
      font-size: 8px;
      padding: 2px 5px;
    }
    
    .coin-icon-wrapper .pkg-coin-icon {
      width: 32px;
      height: 32px;
    }
    
    .coins-amount {
      font-size: 11px;
    }
    
    .price {
      font-size: 10px;
    }
  }
}

@media (min-width: 768px) {
  .coins-recharge-page {
    max-width: 500px;
    margin: 0 auto;
  }
  
  .balance-card {
    .balance-info .balance-amount {
      font-size: 42px;
    }
    
    .coin-icon {
      width: 70px;
      height: 70px;
    }
  }
  
  .packages-grid {
    gap: 10px;
  }
  
  .package-card {
    padding: 10px 8px 14px;
    
    .coin-icon-wrapper .pkg-coin-icon {
      width: 42px;
      height: 42px;
    }
    
    .coins-amount {
      font-size: 14px;
    }
    
    .price {
      font-size: 13px;
    }
  }
}

@media (min-width: 1024px) {
  .coins-recharge-page {
    max-width: 560px;
  }
}

// 触摸设备优化
@media (hover: none) and (pointer: coarse) {
  .package-card:hover {
    transform: none;
  }
}
</style>
