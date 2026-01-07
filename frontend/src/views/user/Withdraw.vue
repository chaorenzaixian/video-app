<template>
  <div class="withdraw-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()">‹</div>
      <h1 class="page-title">立即提现</h1>
      <div class="header-right" @click="goToHistory">明细</div>
    </header>

    <!-- 余额卡片 -->
    <div class="balance-card">
      <div class="balance-label">
        <span class="label-icon"></span>
        <span class="label-text">余额(金币)</span>
      </div>
      <div class="balance-value">
        <img src="/images/backgrounds/ic_coin.webp" alt="coin" class="coin-icon" />
        <span class="value-num gradient-gold">{{ Math.floor(availableBalance) }}</span>
      </div>
      <div class="balance-cash" v-if="withdrawType === 'creator'">
        ≈ ¥{{ (availableBalance * 0.01).toFixed(2) }}
      </div>
    </div>

    <!-- 提现表单 -->
    <div class="withdraw-form">
      <!-- 提现币类 -->
      <div class="form-row">
        <span class="row-label">提现币类：</span>
        <span class="row-value">人民币</span>
      </div>

      <!-- 提现金额 -->
      <div class="form-row">
        <span class="row-label">{{ withdrawType === 'creator' ? '提现金币：' : '提现金额：' }}</span>
        <input 
          type="number" 
          v-model="withdrawAmount" 
          class="amount-input"
          :placeholder="amountPlaceholder"
        />
      </div>
      
      <!-- 兑换比例提示（创作者模式） -->
      <div class="exchange-tip" v-if="withdrawType === 'creator'">
        兑换比例: 100金币 = 1元，预计到账 ¥{{ ((withdrawAmount || 0) * 0.01).toFixed(2) }}
      </div>

      <!-- 提现方式 -->
      <div class="form-row method-row">
        <span class="row-label">提现方式：</span>
        <div class="method-options">
          <!-- 代理模式显示银行卡和USDT -->
          <template v-if="withdrawType === 'agent'">
            <div 
              :class="['method-item', { active: withdrawMethod === 'bank' }]"
              @click="withdrawMethod = 'bank'"
            >
              <img src="/images/backgrounds/ic_union_pay.webp" alt="银行卡" class="method-icon" />
              <span>银行卡</span>
              <div class="check-circle">
                <img v-if="withdrawMethod === 'bank'" src="/images/backgrounds/mine_withdraw_sel.webp" alt="selected" class="check-img" />
              </div>
            </div>
            <div 
              :class="['method-item', { active: withdrawMethod === 'usdt' }]"
              @click="withdrawMethod = 'usdt'"
            >
              <img src="/images/backgrounds/ic_usdt.webp" alt="USDT" class="method-icon" />
              <span>USDT</span>
              <div class="check-circle">
                <img v-if="withdrawMethod === 'usdt'" src="/images/backgrounds/mine_withdraw_sel.webp" alt="selected" class="check-img" />
              </div>
            </div>
          </template>
          
          <!-- 创作者模式显示支付宝、微信、银行卡 -->
          <template v-else>
            <div 
              :class="['method-item', { active: withdrawMethod === 'alipay' }]"
              @click="withdrawMethod = 'alipay'"
            >
              <div class="method-icon-text alipay">支</div>
              <span>支付宝</span>
              <div class="check-circle">
                <img v-if="withdrawMethod === 'alipay'" src="/images/backgrounds/mine_withdraw_sel.webp" alt="selected" class="check-img" />
              </div>
            </div>
            <div 
              :class="['method-item', { active: withdrawMethod === 'wechat' }]"
              @click="withdrawMethod = 'wechat'"
            >
              <div class="method-icon-text wechat">微</div>
              <span>微信</span>
              <div class="check-circle">
                <img v-if="withdrawMethod === 'wechat'" src="/images/backgrounds/mine_withdraw_sel.webp" alt="selected" class="check-img" />
              </div>
            </div>
            <div 
              :class="['method-item', { active: withdrawMethod === 'bank' }]"
              @click="withdrawMethod = 'bank'"
            >
              <img src="/images/backgrounds/ic_union_pay.webp" alt="银行卡" class="method-icon" />
              <span>银行卡</span>
              <div class="check-circle">
                <img v-if="withdrawMethod === 'bank'" src="/images/backgrounds/mine_withdraw_sel.webp" alt="selected" class="check-img" />
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- 银行卡信息（当选择银行卡时） -->
      <template v-if="withdrawMethod === 'bank'">
        <div class="form-row">
          <span class="row-label">银行卡号：</span>
          <input 
            type="text" 
            v-model="bankCardNo"
            class="text-input"
            placeholder="请输入银行卡号"
          />
        </div>
        <div class="form-row">
          <span class="row-label">开户姓名：</span>
          <input 
            type="text" 
            v-model="bankName"
            class="text-input"
            placeholder="请输入开户姓名"
          />
        </div>
        <div class="form-row">
          <span class="row-label">开户银行：</span>
          <input 
            type="text" 
            v-model="bankBranch"
            class="text-input"
            placeholder="请输入开户银行"
          />
        </div>
      </template>

      <!-- USDT地址（当选择USDT时） -->
      <div class="form-row" v-if="withdrawMethod === 'usdt'">
        <span class="row-label">USDT地址：</span>
        <input 
          type="text" 
          v-model="usdtAddress"
          class="text-input"
          placeholder="请输入USDT地址"
        />
      </div>
      
      <!-- 支付宝/微信账号（创作者模式） -->
      <template v-if="withdrawType === 'creator' && (withdrawMethod === 'alipay' || withdrawMethod === 'wechat')">
        <div class="form-row">
          <span class="row-label">收款账号：</span>
          <input 
            type="text" 
            v-model="paymentAccount"
            class="text-input"
            :placeholder="withdrawMethod === 'alipay' ? '请输入支付宝账号' : '请输入微信账号'"
          />
        </div>
        <div class="form-row">
          <span class="row-label">收款姓名：</span>
          <input 
            type="text" 
            v-model="paymentName"
            class="text-input"
            placeholder="请输入真实姓名"
          />
        </div>
      </template>

      <!-- 手续费信息（仅代理模式） -->
      <div class="fee-info" v-if="withdrawType === 'agent'">
        <span class="fee-rate">手续费率：<em>{{ feeRate }}%</em></span>
        <span class="actual-amount">实际到账金额: <em>{{ actualAmount }}</em></span>
      </div>

      <!-- 提现规则 -->
      <div class="withdraw-rules">
        <h4>提现规则：</h4>
        <template v-if="withdrawType === 'creator'">
          <p>1、每次提现最低{{ minAmount }}金币起，且为整数。</p>
          <p>2、兑换比例: 100金币 = 1元人民币。</p>
          <p>3、支持支付宝、微信、银行卡提现，到账时间不超72小时。</p>
          <p>4、申请提现后请随时关注收款账户进款通知，长时间未到账，请及时联系客服。</p>
        </template>
        <template v-else-if="rules.length">
          <p v-for="(rule, index) in rules" :key="index">{{ index + 1 }}、{{ rule }}</p>
        </template>
        <template v-else>
          <p>1、每次提现金额最低{{ minAmount }}元起，单笔提现最大{{ maxAmount }}元，且为整数。</p>
          <p>2、每次提现收取{{ feeRate }}%手续费。</p>
          <p>3、支持银行卡或USDT提现，收款账户卡号与姓名一致，到账时间不超72小时内</p>
          <p>4、申请提现后请随时关注收款账户进款通知，长时间未到账，请及时联系客服</p>
        </template>
      </div>
    </div>

    <!-- 底部提交按钮 -->
    <div class="submit-section">
      <button class="submit-btn" @click="submitWithdraw" :disabled="isSubmitting">
        {{ isSubmitting ? '提交中...' : '立即提现' }}
      </button>
      <p class="contact-tip">
        提现中如有问题，请联系 <span class="link" @click="contactService">在线客服</span>
      </p>
    </div>
    
    <!-- 提现记录弹窗（创作者模式） -->
    <div v-if="showHistoryModal" class="history-modal" @click.self="showHistoryModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <span>提现记录</span>
          <button @click="showHistoryModal = false">×</button>
        </div>
        <div class="modal-body">
          <div v-for="record in withdrawalRecords" :key="record.id" class="record-item">
            <div class="record-info">
              <span class="record-amount">{{ record.coins_amount || record.amount }}{{ withdrawType === 'creator' ? '金币' : '元' }}</span>
              <span class="record-cash" v-if="record.cash_amount">¥{{ record.cash_amount }}</span>
              <span class="record-time">{{ formatTime(record.created_at) }}</span>
            </div>
            <span class="record-status" :class="record.status">
              {{ getStatusText(record.status) }}
            </span>
          </div>
          <div v-if="withdrawalRecords.length === 0" class="empty">暂无记录</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const router = useRouter()
const route = useRoute()

// 提现类型：agent(代理) 或 creator(创作者)
const withdrawType = computed(() => route.query.type || 'agent')

// 数据
const availableBalance = ref(0)
const withdrawAmount = ref('')
const withdrawMethod = ref('')
const bankCardNo = ref('')
const bankName = ref('')
const bankBranch = ref('')
const usdtAddress = ref('')
const paymentAccount = ref('')
const paymentName = ref('')
const feeRate = ref(20)
const minAmount = ref(250)
const maxAmount = ref(10000)
const rules = ref([])
const isSubmitting = ref(false)
const showHistoryModal = ref(false)
const withdrawalRecords = ref([])

// 设置默认提现方式
onMounted(() => {
  if (withdrawType.value === 'creator') {
    withdrawMethod.value = 'alipay'
    minAmount.value = 1000 // 创作者最低1000金币
  } else {
    withdrawMethod.value = 'usdt'
  }
})

// 金额输入占位符
const amountPlaceholder = computed(() => {
  if (withdrawType.value === 'creator') {
    return `最低提现${minAmount.value}金币`
  }
  return `单笔提现金额范围${minAmount.value}-${maxAmount.value}元`
})

// 计算实际到账金额（仅代理模式）
const actualAmount = computed(() => {
  const amount = parseFloat(withdrawAmount.value) || 0
  if (amount <= 0) return 0
  const fee = amount * (feeRate.value / 100)
  return (amount - fee).toFixed(2)
})

// 状态文本
const getStatusText = (status) => {
  const texts = {
    'pending': '待处理',
    'processing': '处理中',
    'completed': '已完成',
    'rejected': '已拒绝',
    'approved': '已通过'
  }
  return texts[status] || status
}

// 格式化时间
const formatTime = (time) => {
  const d = new Date(time)
  return `${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}`
}

// 跳转到历史记录
const goToHistory = () => {
  if (withdrawType.value === 'creator') {
    showHistoryModal.value = true
    fetchWithdrawalRecords()
  } else {
    router.push('/user/withdraw-history')
  }
}

// 获取提现配置（代理模式）
const fetchWithdrawConfig = async () => {
  if (withdrawType.value !== 'agent') return
  
  try {
    const res = await api.get('/config/withdraw')
    const data = res.data || res
    feeRate.value = data.fee_rate || 20
    minAmount.value = data.min_amount || 250
    maxAmount.value = data.max_amount || 10000
    rules.value = data.rules || []
  } catch (error) {
    if (error.response?.status !== 404) {
      console.error('获取提现配置失败:', error)
    }
  }
}

// 获取余额
const fetchBalance = async () => {
  try {
    if (withdrawType.value === 'creator') {
      const res = await api.get('/creator/dashboard')
      const data = res.data || res
      availableBalance.value = data.available_coins || 0
    } else {
      const res = await api.get('/promotion/agent/info')
      const data = res.data || res
      availableBalance.value = data.available_balance || 0
    }
  } catch (error) {
    // 404 表示用户还不是创作者/代理，默认余额为0
    if (error.response?.status !== 404) {
      console.error('获取余额失败:', error)
    }
    availableBalance.value = 0
  }
}

// 获取提现记录（创作者模式）
const fetchWithdrawalRecords = async () => {
  if (withdrawType.value !== 'creator') return
  
  try {
    const res = await api.get('/creator/withdrawals')
    withdrawalRecords.value = res.data || []
  } catch (error) {
    // 404 表示用户还不是创作者，忽略
    if (error.response?.status !== 404) {
      console.error('获取提现记录失败:', error)
    }
  }
}

// 提交提现
const submitWithdraw = async () => {
  const amount = parseFloat(withdrawAmount.value)
  
  // 验证金额
  if (!amount || amount < minAmount.value) {
    ElMessage.warning(`提现${withdrawType.value === 'creator' ? '金币' : '金额'}最低${minAmount.value}${withdrawType.value === 'creator' ? '金币' : '元'}`)
    return
  }
  if (withdrawType.value === 'agent' && amount > maxAmount.value) {
    ElMessage.warning(`单笔提现最大${maxAmount.value}元`)
    return
  }
  if (amount > availableBalance.value) {
    ElMessage.warning('余额不足')
    return
  }
  
  // 验证账户信息
  if (withdrawMethod.value === 'bank') {
    if (!bankCardNo.value) {
      ElMessage.warning('请输入银行卡号')
      return
    }
    if (!bankName.value) {
      ElMessage.warning('请输入开户姓名')
      return
    }
    if (!bankBranch.value) {
      ElMessage.warning('请输入开户银行')
      return
    }
  } else if (withdrawMethod.value === 'usdt') {
    if (!usdtAddress.value) {
      ElMessage.warning('请输入USDT地址')
      return
    }
  } else if (withdrawMethod.value === 'alipay' || withdrawMethod.value === 'wechat') {
    if (!paymentAccount.value) {
      ElMessage.warning('请输入收款账号')
      return
    }
    if (!paymentName.value) {
      ElMessage.warning('请输入收款人姓名')
      return
    }
  }
  
  isSubmitting.value = true
  
  try {
    if (withdrawType.value === 'creator') {
      // 创作者提现
      await api.post('/creator/withdraw', {
        coins_amount: amount,
        payment_method: withdrawMethod.value,
        payment_account: withdrawMethod.value === 'bank' 
          ? `${bankCardNo.value}|${bankName.value}|${bankBranch.value}`
          : paymentAccount.value,
        payment_name: withdrawMethod.value === 'bank' ? bankName.value : paymentName.value
      })
    } else {
      // 代理提现
      await api.post('/promotion/withdraw/apply', {
        amount: amount,
        method: withdrawMethod.value,
        account: withdrawMethod.value === 'bank' 
          ? `${bankCardNo.value}|${bankName.value}|${bankBranch.value}`
          : usdtAddress.value,
        fee_rate: feeRate.value
      })
    }
    
    ElMessage.success('提现申请已提交，请等待审核')
    router.back()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '提现失败')
  } finally {
    isSubmitting.value = false
  }
}

// 联系客服
const contactService = () => {
  ElMessage.info('请联系在线客服')
}

onMounted(() => {
  fetchWithdrawConfig()
  fetchBalance()
})
</script>

<style lang="scss" scoped>
.withdraw-page {
  min-height: 100vh;
  background: #0a0a12;
  color: #fff;
  padding-bottom: 120px;
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
    font-size: 16px;
    font-weight: 600;
    margin: 0;
  }
  
  .header-right {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.7);
    cursor: pointer;
  }
}

// 余额卡片
.balance-card {
  margin: 0 16px 20px;
  background: linear-gradient(135deg, rgba(30, 25, 40, 0.95), rgba(20, 18, 30, 0.95));
  border: 1px solid rgba(138, 92, 246, 0.3);
  border-radius: 16px;
  padding: 20px;
  
  .balance-label {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    
    .label-icon {
      width: 4px;
      height: 16px;
      background: linear-gradient(180deg, #a855f7, #7c3aed);
      border-radius: 2px;
    }
    
    .label-text {
      font-size: 14px;
      color: #a855f7;
    }
  }
  
  .balance-value {
    display: flex;
    align-items: center;
    gap: 10px;
    
    .coin-icon {
      width: 28px;
      height: 28px;
      object-fit: contain;
    }
    
    .value-num {
      font-size: 32px;
      font-weight: 700;
      
      &.gradient-gold {
        background: linear-gradient(135deg, #f5d77a 0%, #d4af37 50%, #b8962e 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }
    }
  }
  
  .balance-cash {
    margin-top: 8px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.5);
  }
}

// 提现表单
.withdraw-form {
  margin: 0 16px;
}

.form-row {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  
  .row-label {
    width: 90px;
    flex-shrink: 0;
    font-size: 14px;
    color: #fff;
  }
  
  .row-value {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.8);
  }
  
  .amount-input,
  .text-input {
    flex: 1;
    background: rgba(255, 255, 255, 0.08);
    border: none;
    border-radius: 8px;
    padding: 14px 16px;
    color: #fff;
    font-size: 14px;
    
    &::placeholder {
      color: rgba(255, 255, 255, 0.4);
    }
  }
}

.exchange-tip {
  font-size: 12px;
  color: #ffd700;
  margin: -12px 0 20px 90px;
}

.method-row {
  align-items: flex-start;
  flex-wrap: wrap;
  
  .method-options {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }
  
  .method-item {
    display: flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    padding: 8px 12px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    border: 1px solid transparent;
    transition: all 0.2s;
    
    &.active {
      border-color: #a855f7;
      background: rgba(168, 85, 247, 0.1);
    }
    
    .method-icon {
      width: 24px;
      height: 24px;
      object-fit: contain;
    }
    
    .method-icon-text {
      width: 24px;
      height: 24px;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      font-weight: 600;
      color: #fff;
      
      &.alipay {
        background: #1677FF;
      }
      
      &.wechat {
        background: #07C160;
      }
    }
    
    span {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.8);
    }
    
    .check-circle {
      width: 18px;
      height: 18px;
      border-radius: 50%;
      border: 2px solid rgba(255, 255, 255, 0.3);
      display: flex;
      align-items: center;
      justify-content: center;
      margin-left: 4px;
      
      .check-img {
        width: 18px;
        height: 18px;
        object-fit: contain;
      }
    }
    
    &.active {
      .check-circle {
        border: none;
      }
    }
  }
}

// 手续费信息
.fee-info {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
  padding: 12px 0;
  
  .fee-rate,
  .actual-amount {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.6);
    
    em {
      font-style: normal;
      color: #fff;
    }
  }
}

// 提现规则
.withdraw-rules {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  padding: 16px;
  
  h4 {
    font-size: 14px;
    font-weight: 600;
    color: #fff;
    margin: 0 0 12px;
  }
  
  p {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.6);
    line-height: 1.8;
    margin: 0 0 8px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
}

// 底部提交
.submit-section {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  padding-bottom: calc(env(safe-area-inset-bottom, 16px) + 16px);
  background: #0a0a12;
  
  .submit-btn {
    width: 70%;
    margin: 0 auto;
    display: block;
    padding: 11px;
    background: linear-gradient(135deg, #a855f7, #7c3aed, #6d28d9);
    border: none;
    border-radius: 20px;
    color: #fff;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    
    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  }
  
  .contact-tip {
    text-align: center;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.5);
    margin-top: 12px;
    
    .link {
      color: #a855f7;
      cursor: pointer;
    }
  }
}

// 提现记录弹窗
.history-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: flex-end;
  z-index: 200;
  
  .modal-content {
    width: 100%;
    max-height: 60vh;
    background: #1a1a2e;
    border-radius: 20px 20px 0 0;
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    
    span {
      color: #fff;
      font-size: 16px;
      font-weight: bold;
    }
    
    button {
      background: none;
      border: none;
      color: #fff;
      font-size: 24px;
      cursor: pointer;
    }
  }
  
  .modal-body {
    padding: 16px;
    max-height: 50vh;
    overflow-y: auto;
  }
  
  .record-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    
    .record-info {
      .record-amount {
        display: block;
        color: #fff;
        font-size: 14px;
      }
      
      .record-cash {
        color: #ffd700;
        font-size: 12px;
        margin-left: 8px;
      }
      
      .record-time {
        display: block;
        font-size: 11px;
        color: rgba(255, 255, 255, 0.4);
        margin-top: 4px;
      }
    }
    
    .record-status {
      font-size: 12px;
      padding: 4px 8px;
      border-radius: 4px;
      
      &.pending {
        background: #faad14;
        color: #000;
      }
      
      &.processing {
        background: #1890ff;
        color: #fff;
      }
      
      &.completed,
      &.approved {
        background: #52c41a;
        color: #fff;
      }
      
      &.rejected {
        background: #ff4d4f;
        color: #fff;
      }
    }
  }
  
  .empty {
    text-align: center;
    padding: 40px;
    color: rgba(255, 255, 255, 0.4);
  }
}
</style>