<template>
  <div class="faq-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </div>
      <h1 class="page-title">常见问题</h1>
      <div class="header-right"></div>
    </header>

    <!-- FAQ列表 -->
    <div class="faq-list">
      <div 
        v-for="(item, index) in faqList" 
        :key="index"
        class="faq-item"
      >
        <div class="faq-question" @click="toggleFaq(index)">
          <span class="question-text">{{ item.question }}</span>
          <svg 
            class="arrow-icon" 
            :class="{ expanded: expandedIndex === index }"
            viewBox="0 0 24 24" 
            fill="currentColor"
          >
            <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/>
          </svg>
        </div>
        <div class="faq-answer" v-show="expandedIndex === index">
          {{ item.answer }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const expandedIndex = ref(0) // 默认展开第一个

const faqList = ref([
  {
    question: '描述文件安装失败?',
    answer: '若提示【新的MDM有效负载与旧的有效负载不匹配】，请移除移动设备管理步骤：【设置-通用-设备管理-移动设备管理-移除管理】'
  },
  {
    question: '怎么找回账号?',
    answer: '您可以通过以下方式找回账号：1. 使用绑定的邮箱找回；2. 使用账号凭证找回；3. 联系客服协助找回。建议您提前绑定邮箱或保存账号凭证以便找回。'
  },
  {
    question: '怎么支付不成功?',
    answer: '支付不成功可能由以下原因导致：1. 网络连接不稳定，请检查网络后重试；2. 支付渠道维护中，请稍后再试或更换支付方式；3. 银行卡余额不足或限额，请确认账户状态。如问题持续，请联系客服。'
  },
  {
    question: '收到手机报毒提醒?',
    answer: '部分手机安全软件可能会误报，这是正常现象。我们的APP经过严格安全检测，不会收集用户隐私信息。您可以选择忽略提醒或将APP添加到信任列表中继续使用。'
  },
  {
    question: '联系方式?',
    answer: '如有任何问题，您可以通过以下方式联系我们：1. APP内客服功能；2. 官方Telegram群组；3. 官方邮箱。我们会尽快为您处理。'
  }
])

const toggleFaq = (index) => {
  if (expandedIndex.value === index) {
    expandedIndex.value = -1
  } else {
    expandedIndex.value = index
  }
}
</script>

<style lang="scss" scoped>
.faq-page {
  min-height: 100vh;
  background: #0a0a0a;
  color: #fff;
  padding-bottom: env(safe-area-inset-bottom, 20px);
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

.faq-list {
  padding: 10px 16px;
}

.faq-item {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  
  &:last-child {
    border-bottom: none;
  }
}

.faq-question {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 0;
  cursor: pointer;
  
  .question-text {
    font-size: 14px;
    color: #fff;
    flex: 1;
    padding-right: 12px;
  }
  
  .arrow-icon {
    width: 24px;
    height: 24px;
    fill: rgba(255, 255, 255, 0.4);
    transition: transform 0.3s;
    flex-shrink: 0;
    
    &.expanded {
      transform: rotate(180deg);
    }
  }
}

.faq-answer {
  padding: 0 0 18px;
  font-size: 14px;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.6);
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>



