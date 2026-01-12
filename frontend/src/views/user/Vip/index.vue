<template>
  <div class="vip-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <button class="back-btn" @click="$router.back()"><img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" /></button>
      <h1>会员中心</h1>
      <button class="record-btn" @click="showRecords = true">充值记录</button>
    </header>

    <!-- 用户信息 -->
    <div class="user-info-section">
      <div class="avatar-wrapper">
        <div :class="['avatar-container', { 'is-vip': user.is_vip }]">
          <img :src="avatarUrl" class="user-avatar" />
        </div>
      </div>
      <div class="user-details">
        <div class="nickname-row">
          <span class="username">{{ user.nickname || user.username || '未登录' }}</span>
          <img v-if="user.vip_level > 0" :src="vipLevelIcon" class="vip-level-badge" />
        </div>
        <div class="vip-status">
          <span v-if="!user.is_vip">您还不是会员</span>
          <span v-else>{{ user.vip_level_name }} · 到期：{{ formatDate(user.vip_expire_date) }}</span>
          <a href="javascript:;" class="open-vip-link" v-if="!user.is_vip">开通会员</a>
          <span class="benefit-text">畅享特权</span>
        </div>
      </div>
    </div>

    <!-- VIP卡片轮播 -->
    <VipCardSlider ref="cardSlider" :cards="vipCards" :selected-id="selectedCard?.id" @select="handleSelectCard" />

    <!-- 简洁卡片网格 -->
    <SimpleCardGrid :cards="vipCards" :selected-id="selectedCard?.id" @select="handleSelectCard" />

    <!-- 会员特权 -->
    <PrivilegeList :privileges="currentPrivileges" />

    <!-- 提示文字 -->
    <div class="tips-section">
      <p class="tips">*如提示【交易失败】【账户风险】等，可重新发起订单，或在15分钟后重试支付。如支付未到账，请<a href="javascript:;" class="link">反馈客服订单号</a></p>
    </div>

    <!-- 底部支付 -->
    <div class="pay-section">
      <button class="pay-btn" :disabled="!selectedCard || isProcessing" @click="handlePay(selectedCard)">
        <span v-if="isProcessing">处理中...</span>
        <span v-else-if="selectedCard">¥{{ selectedCard.price }}/立即支付</span>
        <span v-else>请选择会员卡</span>
      </button>
      <p class="support-text">支付问题反馈，点击联系 <a href="javascript:;" class="link">在线客服</a></p>
    </div>

    <!-- 支付方式弹窗 -->
    <PaymentModal :visible="showPaymentModal" :methods="paymentMethods" v-model:selected-type="selectedPayType" :price="selectedCard?.price" :processing="isProcessing" @close="showPaymentModal = false" @confirm="confirmPay(selectedCard)" />

    <!-- 充值记录弹窗 -->
    <RecordsModal :visible="showRecords" :records="paymentRecords" @close="showRecords = false" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useAbortController } from '@/composables/useAbortController'
import { VIP_LEVEL_ICONS } from '@/constants/vip'
import VipCardSlider from './components/VipCardSlider.vue'
import SimpleCardGrid from './components/SimpleCardGrid.vue'
import PrivilegeList from './components/PrivilegeList.vue'
import PaymentModal from './components/PaymentModal.vue'
import RecordsModal from './components/RecordsModal.vue'
import { useVipData } from './composables/useVipData'
import { useVipPayment } from './composables/useVipPayment'

const userStore = useUserStore()
const { signal } = useAbortController()

const user = computed(() => userStore.user || {})
const cardSlider = ref(null)
const showRecords = ref(false)

// 头像URL
const avatarUrl = computed(() => {
  if (user.value.avatar) return user.value.avatar
  const numericId = parseInt(user.value.id) || 1
  const totalAvatars = 52
  const index = numericId % totalAvatars
  if (index < 17) return `/images/avatars/icon_avatar_${index + 1}.webp`
  else if (index < 32) return `/images/avatars/DM_20251217202131_${String(index - 17 + 1).padStart(3, '0')}.JPEG`
  else return `/images/avatars/DM_20251217202341_${String(index - 32 + 1).padStart(3, '0')}.JPEG`
})

// VIP等级图标
const vipLevelIcon = computed(() => VIP_LEVEL_ICONS[user.value.vip_level] || '')

// 使用composables
const { vipCards, selectedCard, paymentRecords, currentPrivileges, fetchVipCards, fetchPrivileges, fetchRecords, selectCard } = useVipData(signal)
const { showPaymentModal, selectedPayType, isProcessing, paymentMethods, handlePay, confirmPay } = useVipPayment()

// 选择卡片
const handleSelectCard = (card) => {
  selectCard(card, cardSlider.value?.cardsScrollRef)
}

const formatDate = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

onMounted(() => {
  fetchVipCards()
  fetchPrivileges()
  fetchRecords()
})
</script>

<style lang="scss" scoped>
.vip-page {
  min-height: 100vh;
  min-height: 100dvh;
  background: url('/images/backgrounds/wallet_coin_bg_1.webp') no-repeat center top / 100% auto, linear-gradient(180deg, #1a0a2e 0%, #0d0d1a 30%, #0a0a0a 100%);
  padding-bottom: calc(env(safe-area-inset-bottom) + 180px);
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  padding-top: calc(env(safe-area-inset-top, 12px) + 12px);

  .back-btn {
    width: 32px;
    height: 32px;
    background: transparent;
    border: none;
    color: #fff;
    font-size: 28px;
    cursor: pointer;
  }

  h1 { font-size: 18px; color: #fff; margin: 0; font-weight: 500; }

  .record-btn {
    background: none;
    border: none;
    color: rgba(255, 255, 255, 0.7);
    font-size: 14px;
    cursor: pointer;
  }
}

.user-info-section {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;

  .avatar-wrapper {
    flex-shrink: 0;

    .avatar-container {
      width: 56px;
      height: 56px;
      border-radius: 50%;
      padding: 3px;
      background: linear-gradient(135deg, rgba(139, 92, 246, 0.5), rgba(99, 102, 241, 0.5));
      display: flex;
      align-items: center;
      justify-content: center;

      &.is-vip {
        background: linear-gradient(135deg, #fbbf24, #f59e0b, #d97706);
        box-shadow: 0 0 12px rgba(251, 191, 36, 0.4);
      }

      .user-avatar {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        object-fit: cover;
        background: #1a1a2e;
      }
    }
  }

  .user-details {
    flex: 1;

    .nickname-row {
      display: flex;
      align-items: center;
      gap: 8px;

      .username {
        font-size: 16px;
        font-weight: 600;
        background: linear-gradient(135deg, #ffd700 0%, #ffec8b 30%, #daa520 60%, #ffd700 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }

      .vip-level-badge { height: 18px; width: auto; }
    }

    .vip-status {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.6);
      margin-top: 4px;

      .open-vip-link { color: #a855f7; margin-left: 8px; text-decoration: none; }
      .benefit-text { margin-left: 8px; color: rgba(255, 255, 255, 0.5); }
    }
  }
}

.tips-section {
  padding: 16px;
  margin-bottom: 120px;

  .tips {
    font-size: 13px;
    color: #fff;
    line-height: 1.7;

    .link { color: #c084fc; text-decoration: none; font-weight: 500; }
  }
}

.pay-section {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px 16px;
  padding-bottom: calc(env(safe-area-inset-bottom) + 12px);
  background: transparent;
  z-index: 100;

  .pay-btn {
    width: 80%;
    margin: 0 auto;
    display: block;
    padding: 12px;
    background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
    border: none;
    border-radius: 24px;
    color: #fff;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;

    &:active { transform: scale(0.98); opacity: 0.9; }
    &:disabled { opacity: 0.5; cursor: not-allowed; }
  }

  .support-text {
    text-align: center;
    font-size: 14px;
    color: #fff;
    margin-top: 14px;

    .link { color: #c084fc; text-decoration: none; font-weight: 500; }
  }
}

@media (min-width: 768px) {
  .vip-page { max-width: 600px; margin: 0 auto; }
}
</style>
