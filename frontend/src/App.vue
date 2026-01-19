<template>
  <!-- 开屏广告 -->
  <div v-if="showSplash" class="splash-screen" @click="handleSplashClick">
    <img 
      :src="splashAd?.image_url || '/images/splash.webp'" 
      alt="开屏广告" 
      class="splash-image" 
    />
    <button class="skip-btn" @click.stop="skipSplash">跳过 {{ countdown }}s</button>
  </div>
  
  <!-- 主内容 -->
  <router-view v-else v-slot="{ Component }">
    <keep-alive :include="cachedPages">
      <component :is="Component" />
    </keep-alive>
  </router-view>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import sessionChecker from '@/utils/sessionChecker'

// 需要缓存的页面组件名
const cachedPages = ['UserHome', 'Dating', 'UserProfile', 'DarkwebEntry', 'Community']
import axios from 'axios'

const userStore = useUserStore()
const route = useRoute()

// 开屏相关
const showSplash = ref(false)
const splashAd = ref(null)
const countdown = ref(3)
let splashTimer = null

// 获取开屏广告
const fetchSplashAd = async () => {
  try {
    const res = await axios.get('/api/v1/ads/splash')
    if (res.data) {
      splashAd.value = res.data
      // 使用广告配置的时长，默认3秒
      countdown.value = res.data.duration || 3
    }
  } catch (e) {
    // 获取失败使用默认图片
    console.log('获取开屏广告失败，使用默认图片')
  }
}

// 检查是否需要显示开屏
const checkShowSplash = async () => {
  const isUserPage = window.location.pathname.startsWith('/user') || 
                     window.location.pathname === '/' ||
                     window.location.hash.startsWith('#/user') ||
                     window.location.hash.startsWith('#/shorts')
  
  if (isUserPage) {
    // 先获取开屏广告
    await fetchSplashAd()
    showSplash.value = true
    startCountdown()
  }
}

const startCountdown = () => {
  splashTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      skipSplash()
    }
  }, 1000)
}

const skipSplash = () => {
  if (splashTimer) {
    clearInterval(splashTimer)
    splashTimer = null
  }
  showSplash.value = false
}

// 点击开屏广告
const handleSplashClick = () => {
  if (splashAd.value?.target_url) {
    // 记录点击
    recordAdClick()
    // 跳转链接
    window.open(splashAd.value.target_url, '_blank')
  }
  skipSplash()
}

// 记录广告点击
const recordAdClick = async () => {
  if (!splashAd.value?.id) return
  try {
    await axios.post(`/api/v1/ads/${splashAd.value.id}/click`)
  } catch (e) {
    // 忽略错误
  }
}

// 根据路由设置body主题
const updateTheme = () => {
  const isUserPage = window.location.pathname.startsWith('/user') || 
                     window.location.hash.startsWith('#/user') ||
                     window.location.hash.startsWith('#/shorts')
  if (isUserPage) {
    document.body.classList.add('user-theme')
  } else {
    document.body.classList.remove('user-theme')
  }
}

onMounted(async () => {
  updateTheme()
  
  // 判断是否是用户端页面
  const isUserPage = window.location.pathname.startsWith('/user') || 
                     window.location.pathname === '/' ||
                     window.location.hash.startsWith('#/user') ||
                     window.location.hash.startsWith('#/shorts') ||
                     window.location.pathname.startsWith('/shorts')
  
  if (isUserPage) {
    // 检查URL中的邀请码参数
    const urlParams = new URLSearchParams(window.location.search)
    const inviteCode = urlParams.get('invite')
    if (inviteCode) {
      // 保存邀请码到 localStorage，注册时使用
      localStorage.setItem('invite_code', inviteCode)
    }
    
    // 并行执行：开屏广告 + 自动注册（不阻塞页面渲染）
    checkShowSplash()
    
    // 先检查当前用户是否是管理员
    if (userStore.token) {
      await userStore.fetchUser()
      if (userStore.isAdmin) {
        return
      }
    }
    // 非管理员或无token，执行游客注册（后台执行，不阻塞）
    if (!userStore.token) {
      userStore.autoRegisterGuest()
    }
    
    // 启动会话检测
    if (userStore.token) {
      sessionChecker.start()
    }
  } else {
    // 后台页面
    if (userStore.token) {
      await userStore.fetchUser()
    }
  }
})

onUnmounted(() => {
  // 停止会话检测
  sessionChecker.stop()
})

// 监听路由变化更新主题
watch(() => route.path, () => {
  updateTheme()
})

// 监听用户登录状态
watch(() => userStore.token, (newToken) => {
  if (newToken) {
    sessionChecker.start()
  } else {
    sessionChecker.stop()
  }
})
</script>

<style scoped>
/* 开屏页样式 */
.splash-screen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 99999;
  background: #000;
  display: flex;
  justify-content: center;
  align-items: center;
}

.splash-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.skip-btn {
  position: absolute;
  top: env(safe-area-inset-top, 50px);
  right: 20px;
  margin-top: 10px;
  padding: 8px 16px;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
  backdrop-filter: blur(10px);
}

.skip-btn:active {
  background: rgba(255, 255, 255, 0.2);
}
</style>
