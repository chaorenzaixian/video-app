<template>
  <div class="darkweb-entry">
    <!-- 加载中 -->
    <div v-if="loading" class="loading-screen">
      <div class="loading-spinner"></div>
    </div>
    
    <template v-else>
      <!-- 背景 -->
      <div class="bg-overlay"></div>
      
      <!-- 内容区 -->
      <div class="entry-content">
        <!-- DANGER 图标 -->
        <div class="danger-icon">
          <img src="/images/backgrounds/darkweb_danger.webp" alt="DANGER" />
        </div>
        
        <!-- 系统警告标题 -->
        <h1 class="warning-title">系统警告</h1>
        
        <!-- 警告内容 -->
        <div class="warning-content">
          <p class="highlight">【暗网】含有百万全球禁播封杀资源，全球上流社会权贵的私密丑闻！</p>
          <p class="tags">萝莉岛事件，N号房，暴力重口，巴以/俄乌/中东战争，血腥缅北，呦呦破处，变态恐怖，暗网交易，等稀缺资源！</p>
        </div>
        
        <!-- 进入提示 -->
        <p class="enter-hint">进入世界的黑暗面！</p>
        
        <!-- 开通按钮 -->
        <div class="action-btn" @click="handleEnter">
          <img src="/images/backgrounds/darkweb_btn.webp" alt="开通专属会员" />
        </div>
        
        <!-- 底部警告 -->
        <div class="bottom-warning">
          <p>此板块为黑客破解内容，真实稀缺资源，</p>
          <p>可能会引起极度不适，请谨慎进入</p>
        </div>
      </div>
      
      <!-- 短视频浮动入口 -->
      <div class="short-video-float" @click="$router.push('/shorts')">
        <img src="/images/backgrounds/short_logo.webp" alt="短视频" />
      </div>
      
      <!-- 底部导航 -->
      <BottomNav />
    </template>
  </div>
</template>

<script setup>
defineOptions({ name: 'DarkwebEntry' })

import { ref, onMounted, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import BottomNav from '@/components/common/BottomNav.vue'
import api from '@/utils/api'

const router = useRouter()
const isVip = ref(false)
const userVipLevel = ref(0)
const minVipLevel = ref(0)  // 暗网最低VIP等级要求
const loading = ref(true)
const hasChecked = ref(false)  // 是否已检查过

// 检查VIP状态
const checkVipStatus = async () => {
  // 如果已经检查过且不是loading状态，跳过
  if (hasChecked.value && !loading.value) return
  
  try {
    // 获取暗网访问权限信息
    const res = await api.get('/darkweb/access-check')
    const data = res.data || res
    
    userVipLevel.value = data.user_vip_level || 0
    minVipLevel.value = data.min_vip_level || 0
    isVip.value = userVipLevel.value > 0
    hasChecked.value = true
    
    // 如果用户有访问权限，直接跳转到暗网内容
    if (data.has_access) {
      router.replace('/user/darkweb')
      return
    }
    
    loading.value = false
  } catch (error) {
    console.log('获取访问权限失败')
    loading.value = false
    hasChecked.value = true
  }
}

// 处理进入按钮点击
const handleEnter = () => {
  if (userVipLevel.value >= minVipLevel.value) {
    // 达到等级要求直接进入暗网
    router.push('/user/darkweb')
  } else {
    // 未达到等级要求跳转到VIP开通页
    router.push('/user/vip')
  }
}

// 首次挂载时检查
onMounted(() => {
  checkVipStatus()
})

// keep-alive 激活时，如果还没检查过则检查
onActivated(() => {
  if (!hasChecked.value) {
    checkVipStatus()
  }
})
</script>

<style lang="scss" scoped>
.darkweb-entry {
  min-height: 100vh;
  background: #0a0a0a;
  position: relative;
  padding-bottom: 70px;
}

.loading-screen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #0a0a0a;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  
  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid rgba(255, 68, 68, 0.2);
    border-top-color: #ff4444;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.bg-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(180deg, #0a0a0a 0%, #1a0a0a 50%, #0a0a0a 100%);
  z-index: 0;
}

.entry-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 100px 20px 30px;
}

.danger-icon {
  width: 120px;
  margin-bottom: 25px;
  
  img {
    width: 100%;
    height: auto;
  }
}

.warning-title {
  font-size: 24px;
  font-weight: bold;
  color: #fff;
  margin-bottom: 20px;
  letter-spacing: 4px;
}

.warning-content {
  text-align: center;
  margin-bottom: 30px;
  padding: 0 10px;
  
  .highlight {
    font-size: 16px;
    color: #fff;
    line-height: 1.8;
    margin-bottom: 20px;
  }
  
  .tags {
    font-size: 15px;
    color: #ccc;
    line-height: 1.8;
  }
}

.divider-section {
  width: 200px;
  margin-bottom: 20px;
  
  .divider-img {
    width: 100%;
    height: auto;
  }
}

.enter-hint {
  font-size: 14px;
  color: #888;
  margin-bottom: 25px;
}

.action-btn {
  width: 150px;
  cursor: pointer;
  margin-bottom: 30px;
  transition: transform 0.2s;
  
  img {
    width: 100%;
    height: auto;
  }
  
  &:active {
    transform: scale(0.95);
  }
}

.bottom-warning {
  text-align: center;
  
  p {
    font-size: 12px;
    color: #666;
    line-height: 1.8;
    margin: 0;
  }
}

// 短视频浮动入口
.short-video-float {
  position: fixed;
  right: 16px;
  bottom: calc(100px + env(safe-area-inset-bottom, 0px));
  width: 60px;
  height: 60px;
  border-radius: 50%;
  overflow: hidden;
  z-index: 1000;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4), 0 0 15px rgba(0, 224, 255, 0.3);
  animation: spin-clockwise 8s linear infinite;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  &:hover {
    box-shadow: 0 6px 25px rgba(0, 0, 0, 0.5), 0 0 20px rgba(0, 224, 255, 0.5);
  }
  
  &:active {
    animation-play-state: paused;
    transform: scale(0.95);
  }
}

@keyframes spin-clockwise {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
