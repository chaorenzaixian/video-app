<template>
  <div class="promotion-data-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()">‹</div>
      <h1 class="page-title">推广数据</h1>
      <div class="header-right" @click="$router.push('/user/earnings')">收益明细</div>
    </header>

    <!-- 钱包余额卡片 -->
    <div class="wallet-card">
      <div class="wallet-row">
        <div class="wallet-item">
          <span class="wallet-label">钱包余额</span>
          <span class="wallet-value">{{ Math.floor(walletBalance) }}</span>
        </div>
        <div class="wallet-item">
          <span class="wallet-label">累积收益</span>
          <span class="wallet-value">{{ totalEarnings.toFixed(2) }}</span>
        </div>
      </div>
      <button class="withdraw-btn" @click="showWithdrawDialog = true">提现</button>
    </div>

    <!-- 数据统计卡片 -->
    <div class="stats-card">
      <div class="stats-row">
        <div class="stat-item">
          <span class="stat-value">{{ monthEarnings.toFixed(2) }}</span>
          <span class="stat-label">当月收益(金币)</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-value">{{ monthPromotions }}</span>
          <span class="stat-label">当月推广数</span>
        </div>
      </div>
      <div class="stats-row">
        <div class="stat-item">
          <span class="stat-value">{{ todayEarnings.toFixed(2) }}</span>
          <span class="stat-label">今日收益(金币)</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-value">{{ todayPromotions }}</span>
          <span class="stat-label">今日推广数</span>
        </div>
      </div>
    </div>

    <!-- 直推总统计 -->
    <div class="direct-stats-section">
      <h3 class="section-title">直推总统计</h3>
      <div class="direct-stats-list">
        <div class="direct-stat-row">
          <span class="stat-name">直推用户数</span>
          <span class="stat-num">{{ directUsers }}</span>
        </div>
        <div class="direct-stat-row">
          <span class="stat-name">直推付费用户</span>
          <span class="stat-num">{{ directPaidUsers }}</span>
        </div>
      </div>
    </div>

    <!-- 提现弹窗 -->
    <div class="withdraw-dialog" v-if="showWithdrawDialog" @click.self="showWithdrawDialog = false">
      <div class="dialog-content">
        <h3>申请提现</h3>
        <div class="form-group">
          <label>提现金额</label>
          <input type="number" v-model="withdrawAmount" placeholder="最低50元起提" />
        </div>
        <div class="form-group">
          <label>收款方式</label>
          <select v-model="withdrawMethod">
            <option value="alipay">支付宝</option>
            <option value="wechat">微信</option>
            <option value="bank">银行卡</option>
          </select>
        </div>
        <div class="form-group">
          <label>收款账号</label>
          <input type="text" v-model="withdrawAccount" placeholder="请输入收款账号" />
        </div>
        <div class="dialog-buttons">
          <button class="btn-cancel" @click="showWithdrawDialog = false">取消</button>
          <button class="btn-confirm" @click="submitWithdraw">确认提现</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/utils/api'

// 数据
const walletBalance = ref(0)
const totalEarnings = ref(0)
const monthEarnings = ref(0)
const monthPromotions = ref(0)
const todayEarnings = ref(0)
const todayPromotions = ref(0)
const directUsers = ref(0)
const directPaidUsers = ref(0)

// 提现弹窗
const showWithdrawDialog = ref(false)
const withdrawAmount = ref('')
const withdrawMethod = ref('alipay')
const withdrawAccount = ref('')

// 获取推广数据
const fetchPromotionData = async () => {
  try {
    const res = await api.get('/promotion/agent/info')
    const data = res.data || res
    walletBalance.value = data.available_balance || 0
    totalEarnings.value = data.total_commission || 0
    monthEarnings.value = data.month_commission || 0
    monthPromotions.value = data.month_invites || 0
    todayEarnings.value = data.today_commission || 0
    todayPromotions.value = data.today_invites || 0
    directUsers.value = data.direct_invites || 0
    directPaidUsers.value = data.direct_paid_users || 0
  } catch (error) {
    console.error('获取推广数据失败:', error)
  }
}

// 提交提现
const submitWithdraw = async () => {
  if (!withdrawAmount.value || withdrawAmount.value < 50) {
    alert('提现金额最低50元')
    return
  }
  if (!withdrawAccount.value) {
    alert('请输入收款账号')
    return
  }
  
  try {
    await api.post('/promotion/withdraw', {
      amount: parseFloat(withdrawAmount.value),
      method: withdrawMethod.value,
      account: withdrawAccount.value
    })
    alert('提现申请已提交，请等待审核')
    showWithdrawDialog.value = false
    fetchPromotionData()
  } catch (error) {
    alert(error.response?.data?.detail || '提现失败')
  }
}

onMounted(() => {
  fetchPromotionData()
})
</script>

<style lang="scss" scoped>
.promotion-data-page {
  min-height: 100vh;
  background: #0a0a12;
  color: #fff;
  padding-bottom: 40px;
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
    font-size: 14px;
    color: rgba(255, 255, 255, 0.7);
    cursor: pointer;
  }
}

// 钱包余额卡片
.wallet-card {
  margin: 0 16px 16px;
  background: linear-gradient(135deg, rgba(30, 25, 40, 0.95), rgba(20, 18, 30, 0.95));
  border: 1px solid rgba(138, 92, 246, 0.3);
  border-radius: 16px;
  padding: 24px 20px;
  
  .wallet-row {
    display: flex;
    justify-content: space-around;
    margin-bottom: 20px;
  }
  
  .wallet-item {
    text-align: center;
    
    .wallet-label {
      display: block;
      font-size: 14px;
      color: rgba(255, 255, 255, 0.6);
      margin-bottom: 8px;
    }
    
    .wallet-value {
      display: block;
      font-size: 32px;
      font-weight: 700;
      color: #fff;
    }
  }
  
  .withdraw-btn {
    display: block;
    width: 140px;
    margin: 0 auto;
    padding: 10px 0;
    background: linear-gradient(135deg, #a855f7, #7c3aed);
    border: none;
    border-radius: 20px;
    color: #fff;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
  }
}

// 数据统计卡片
.stats-card {
  margin: 0 16px 16px;
  background: rgba(30, 25, 40, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  overflow: hidden;
  
  .stats-row {
    display: flex;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    
    &:last-child {
      border-bottom: none;
    }
  }
  
  .stat-item {
    flex: 1;
    text-align: center;
    padding: 20px 16px;
    
    .stat-value {
      display: block;
      font-size: 24px;
      font-weight: 600;
      font-style: italic;
      color: #fff;
      margin-bottom: 6px;
    }
    
    .stat-label {
      display: block;
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);
    }
  }
  
  .stat-divider {
    width: 1px;
    height: 50px;
    background: rgba(255, 255, 255, 0.1);
  }
}

// 直推总统计
.direct-stats-section {
  margin: 0 16px;
  
  .section-title {
    font-size: 16px;
    font-weight: 600;
    color: #fff;
    margin-bottom: 12px;
  }
  
  .direct-stats-list {
    background: rgba(30, 25, 40, 0.9);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    overflow: hidden;
  }
  
  .direct-stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    
    &:last-child {
      border-bottom: none;
    }
    
    .stat-name {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.8);
    }
    
    .stat-num {
      font-size: 16px;
      font-weight: 600;
      color: #fff;
    }
  }
}

// 提现弹窗
.withdraw-dialog {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  
  .dialog-content {
    background: #1a1520;
    border: 1px solid rgba(138, 92, 246, 0.3);
    border-radius: 16px;
    padding: 24px;
    width: 90%;
    max-width: 350px;
    
    h3 {
      text-align: center;
      color: #fff;
      font-size: 18px;
      margin-bottom: 24px;
    }
    
    .form-group {
      margin-bottom: 16px;
      
      label {
        display: block;
        font-size: 14px;
        color: rgba(255, 255, 255, 0.7);
        margin-bottom: 8px;
      }
      
      input, select {
        width: 100%;
        padding: 12px;
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(138, 92, 246, 0.3);
        border-radius: 8px;
        color: #fff;
        font-size: 14px;
        
        &::placeholder {
          color: rgba(255, 255, 255, 0.4);
        }
      }
      
      select {
        appearance: none;
        cursor: pointer;
      }
    }
    
    .dialog-buttons {
      display: flex;
      gap: 12px;
      margin-top: 24px;
      
      button {
        flex: 1;
        padding: 12px;
        border-radius: 25px;
        font-size: 14px;
        cursor: pointer;
      }
      
      .btn-cancel {
        background: transparent;
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: rgba(255, 255, 255, 0.7);
      }
      
      .btn-confirm {
        background: linear-gradient(135deg, #a855f7, #7c3aed);
        border: none;
        color: #fff;
        font-weight: 600;
      }
    }
  }
}
</style>

