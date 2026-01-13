import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

export function useVipPayment() {
  const showPaymentModal = ref(false)
  const selectedPayType = ref('alipay')
  const isProcessing = ref(false)

  const paymentMethods = [
    { type: 'alipay', name: '支付宝', icon: '/images/icons/ic_alipay.png' },
    { type: 'wxpay', name: '微信', icon: '/images/icons/ic_wechat.png' }
  ]

  // 根据VIP等级获取订单类型
  const getOrderType = (level) => {
    const typeMap = {
      1: 'VIP_MONTHLY',
      2: 'VIP_QUARTERLY',
      3: 'VIP_YEARLY',
      4: 'VIP_YEARLY',
      5: 'VIP_LIFETIME',
      6: 'VIP_LIFETIME',
      7: 'VIP_LIFETIME'
    }
    return typeMap[level] || 'VIP_MONTHLY'
  }

  // 发起支付
  const handlePay = (selectedCard) => {
    if (!selectedCard) {
      ElMessage.warning('请选择会员卡')
      return
    }
    showPaymentModal.value = true
  }

  // 确认支付
  const confirmPay = async (selectedCard) => {
    if (!selectedCard) return

    isProcessing.value = true
    showPaymentModal.value = false

    try {
      const res = await api.post('/payments/epay/create', {
        order_type: getOrderType(selectedCard.level)
      }, {
        params: { pay_type: selectedPayType.value }
      })

      if (res.data?.payment_url) {
        window.location.href = res.data.payment_url
      } else if (res.data?.qr_code) {
        ElMessage.info('请使用手机扫码支付')
      } else {
        ElMessage.error('获取支付链接失败')
      }
    } catch (error) {
      console.error('支付失败:', error)
      ElMessage.error(error.response?.data?.detail || '支付失败，请重试')
    } finally {
      isProcessing.value = false
    }
  }

  return {
    showPaymentModal,
    selectedPayType,
    isProcessing,
    paymentMethods,
    handlePay,
    confirmPay
  }
}
