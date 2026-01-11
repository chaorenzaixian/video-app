<template>
  <div class="promotion-page" ref="pageRef">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="goBack">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </div>
      <h1 class="page-title">分享推广</h1>
      <div class="header-right" @click="goToRecords">邀请记录</div>
    </header>

    <!-- 主卡片区域 -->
    <div class="promo-card">
      <!-- 卡片背景图片 -->
      <img class="card-bg-img" src="/images/backgrounds/app_mine_jelly_share_qr_bg-Photoroom.webp" alt="" />
      
      <!-- 卡片主体内容 -->
      <div class="card-body">
        <!-- 网站Logo -->
        <div class="site-logo">
          <img src="/images/backgrounds/walfare_logo.webp" alt="Logo" />
        </div>
        <!-- 累计邀请 -->
        <div class="invite-count">
          累计邀请 <span class="count-num">{{ stats.total_invites }}</span>人
        </div>
        
        <!-- 二维码 -->
        <div class="qr-section">
          <div class="qr-code">
            <img 
              v-if="inviteUrl"
              :src="`https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(inviteUrl)}`" 
              alt="二维码" 
            />
            <div v-else class="qr-placeholder">加载中...</div>
          </div>
        </div>
        
        <!-- 推广码 -->
        <div class="promo-code">
          我的推广码<span class="code-text">{{ inviteCode }}</span>
        </div>
        
        <!-- 提示文字 -->
        <p class="promo-tip">{{ promoTip }}</p>
      </div>
      
      <!-- 操作按钮 -->
      <div class="action-buttons">
        <button class="btn-save" @click="saveImage">
          <span>保存图片</span>
        </button>
        <button class="btn-copy" @click="copyInviteLink">
          <span>复制推广链接</span>
        </button>
      </div>
    </div>

    <!-- 规则说明 -->
    <div class="rules-section">
      <h3 class="section-title">规则说明</h3>
      <div class="rules-content">
        <p class="rule-item">
          <span class="rule-num">1.</span>邀请<span class="highlight-blue">1名好友</span>成功注册即可获得<span class="highlight-blue">3天VIP</span>
        </p>
        <p class="rule-item">
          <span class="rule-num">2.</span>邀请好友产生充值可获<span class="highlight-gold">充值最高70%返利收益</span>
          <br><span class="rule-example">如:邀请好友A,A充值<span class="highlight-gold">100元年卡VIP</span>,即可获得<span class="highlight-gold">70元收益,可提现!</span></span>
        </p>
        <p class="rule-item">
          <span class="rule-num">3.</span>邀请说明:点击【保存二维码】或【复制推广连接】,获取专属推广链接,推荐分享给他其他人下载即可
        </p>
      </div>
    </div>

    <!-- 邀请步骤 - 使用图片 -->
    <div class="steps-section">
      <img class="steps-img" src="/images/backgrounds/mine_share_img.webp" alt="邀请步骤" />
      
      <!-- 去查看链接 -->
      <div class="go-check" @click="goToAgent">
        <span class="go-text">去查看</span>
        <span class="go-arrow">»</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onActivated, nextTick, onBeforeMount } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
// 二维码使用在线API生成，最稳定可靠

const router = useRouter()

// 页面引用
const pageRef = ref(null)

// 强制滚动到顶部 - 多种方式确保生效
const forceScrollToTop = () => {
  // 方式1: window.scrollTo
  window.scrollTo(0, 0)
  
  // 方式2: documentElement
  document.documentElement.scrollTop = 0
  
  // 方式3: body
  document.body.scrollTop = 0
  
  // 方式4: 页面容器
  if (pageRef.value) {
    pageRef.value.scrollTop = 0
  }
  
  // 方式5: 滚动到页面顶部元素
  const header = document.querySelector('.page-header')
  if (header) {
    header.scrollIntoView({ behavior: 'instant', block: 'start' })
  }
}

// 数据
const inviteCode = ref('')
const inviteUrl = ref('')
const siteName = ref('Soul成人版')
const siteSlogan = ref('最大原创平台')
const promoTip = ref('分享好友后使用 手机自带,uc,夸克,火狐,谷歌浏览扫码后复制链接打开,勿用微信QQ扫码。')
const stats = ref({
  total_invites: 0,
  valid_invites: 0,
  total_reward_days: 0,
  pending_rewards: 0
})

// 获取邀请码
const fetchInviteCode = async () => {
  try {
    const res = await api.get('/promotion/invite-code')
    inviteCode.value = res.data?.invite_code || res.invite_code || ''
    inviteUrl.value = res.data?.invite_url || res.invite_url || ''
  } catch (error) {
    console.error('获取邀请码失败:', error)
  }
}

// 获取统计数据
const fetchStats = async () => {
  try {
    const res = await api.get('/promotion/invite-stats')
    stats.value = res.data || res
  } catch (error) {
    console.error('获取统计失败:', error)
  }
}

// 获取系统配置
const fetchConfig = async () => {
  try {
    const res = await api.get('/config/credential')
    if (res.data) {
      siteName.value = res.data.site_name || siteName.value
      siteSlogan.value = res.data.site_slogan || siteSlogan.value
      promoTip.value = res.data.promo_tip || promoTip.value
    }
  } catch (error) {
    console.error('获取配置失败:', error)
  }
}

// 保存图片
const saveImage = () => {
  alert('请长按二维码图片保存到相册')
}

// 复制邀请链接
const copyInviteLink = async () => {
  try {
    await navigator.clipboard.writeText(inviteUrl.value)
    alert('推广链接已复制')
  } catch {
    // 降级方案
    const input = document.createElement('input')
    input.value = inviteUrl.value
    document.body.appendChild(input)
    input.select()
    document.execCommand('copy')
    document.body.removeChild(input)
    alert('推广链接已复制')
  }
}

// 导航
const goBack = () => {
  router.back()
}

const goToRecords = () => {
  router.push('/user/invite-records')
}

const goToAgent = () => {
  router.push('/user/agent')
}

// 组件挂载前就开始滚动
onBeforeMount(() => {
  forceScrollToTop()
})

onMounted(() => {
  // 立即滚动
  forceScrollToTop()
  
  // DOM更新后再滚动
  nextTick(() => {
    forceScrollToTop()
  })
  
  // 延迟滚动确保所有资源加载完成
  setTimeout(forceScrollToTop, 0)
  setTimeout(forceScrollToTop, 50)
  setTimeout(forceScrollToTop, 100)
  setTimeout(forceScrollToTop, 200)
  
  fetchInviteCode()
  fetchStats()
  fetchConfig()
})

// 页面激活时也滚动到顶部（处理keep-alive缓存情况）
onActivated(() => {
  forceScrollToTop()
  nextTick(forceScrollToTop)
})
</script>

<style lang="scss" scoped>
.promotion-page {
  min-height: 100vh;
  background: #0a0a12;
  background-image: url('/images/backgrounds/app_share_up_bg.webp');
  background-size: 100% auto;
  background-position: top center;
  background-repeat: no-repeat;
  background-attachment: fixed;
  color: #fff;
  padding-bottom: calc(40px + env(safe-area-inset-bottom, 0px));
  padding-top: 0;
}

// 顶部导航
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  padding-top: calc(env(safe-area-inset-top, 0px) + 16px);
  position: sticky;
  top: 0;
  z-index: 100;
  background: transparent;
  
  .back-btn {
    font-size: 32px;
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
  }
  
  .header-right {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.8);
    cursor: pointer;
  }
}

// 主卡片 - 缩小15%
.promo-card {
  margin: 16px 28px 18px;
  border-radius: 16px;
  overflow: hidden;
  position: relative;
  min-height: 440px;
  
  // 背景图片
  .card-bg-img {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: fill;
    z-index: 0;
  }
  
  // 卡片主体
  .card-body {
    position: relative;
    z-index: 1;
    padding: 22px 22px 10px;
    text-align: center;
  }
  
  .site-logo {
    margin-bottom: 5px;
    display: flex;
    justify-content: center;
    
    img {
      max-width: 144px;
      height: auto;
    }
  }
  
  .invite-count {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.85);
    margin-top: 15px;
    margin-bottom: 15px;
    
    .count-num {
      background: linear-gradient(53deg, #c084fc, #673AB7);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      font-weight: 700;
      font-size: 14px;
    }
  }
  
  .qr-section {
    display: flex;
    justify-content: center;
    margin-bottom: 12px;
    
    .qr-code {
      width: 140px;
      height: 140px;
      background: #fff;
      border-radius: 8px;
      padding: 5px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
      
      img {
        width: 130px;
        height: 130px;
        display: block;
      }
      
      .qr-placeholder {
        color: #999;
        font-size: 12px;
      }
    }
  }
  
  .promo-code {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.85);
    margin-bottom: 8px;
    display: flex;
    align-items: baseline;
    justify-content: center;
    gap: 4px;
    
    .code-text {
      font-size: 25px;
      font-weight: 700;
      background: linear-gradient(53deg, #c084fc, #673AB7);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      letter-spacing: 1px;
      font-family: 'Arial', sans-serif;
    }
  }
  
  .promo-tip {
    font-size: 11px;
    color: #FF9800;
    line-height: 1.7;
    padding: 0 14px;
    margin-bottom: 0;
  }
  
  // 操作按钮 - 缩小10%
  .action-buttons {
    position: relative;
    z-index: 1;
    display: flex;
    gap: 9px;
    padding: 10px 16px 20px;
    
    button {
      flex: 1;
      height: 36px;
      border-radius: 25px;
      font-size: 15px;
      font-weight: 500;
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .btn-save {
      background: linear-gradient(53deg, #c084fc, #673AB7);
      color: #fff;
      border: none;
    }
    
    .btn-copy {
      background: linear-gradient(53deg, #c084fc, #673AB7);
      color: #fff;
      border: none;
    }
  }
}

// 规则说明
.rules-section {
  margin: 0 16px 24px;
  
  .section-title {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 16px;
    color: #fff;
  }
  
  .rules-content {
    background: rgba(255, 255, 255, 0.03);
    border-radius: 12px;
    padding: 16px;
  }
  
  .rule-item {
    font-size: 14px;
    line-height: 1.8;
    color: rgba(255, 255, 255, 0.8);
    margin-bottom: 12px;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .rule-num {
      color: #fff;
      font-weight: 600;
    }
    
    .highlight-blue {
      color: #c084fc;
      font-weight: 500;
    }
    
    .highlight-gold {
      color: #FF9800;
      font-weight: 500;
    }
    
    .rule-example {
      display: block;
      padding-left: 14px;
      font-size: 13px;
      color: rgba(255, 255, 255, 0.6);
    }
  }
}

// 邀请步骤 - 使用图片
.steps-section {
  margin: 0 16px 24px;
  
  .steps-img {
    width: 100%;
    height: auto;
    border-radius: 12px;
    display: block;
  }
  
  .go-check {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin-top: 32px;
    cursor: pointer;
    
    .go-text {
      font-size: 16px;
      color: #c084fc;
      font-weight: 500;
    }
    
    .go-arrow {
      font-size: 20px;
      color: #c084fc;
    }
  }
}

// 响应式
@media (max-width: 359px) {
  .promo-card {
    margin: 0 12px 20px;
    
    .site-info .site-name {
      font-size: 24px;
    }
    
    .promo-code .code-text {
      font-size: 26px;
    }
    
    .qr-section .qr-code {
      width: 140px;
      height: 140px;
    }
    
    .action-buttons button {
      font-size: 13px;
    }
  }
}

@media (min-width: 768px) {
  .promotion-page {
    max-width: 450px;
    margin: 0 auto;
  }
}
</style>