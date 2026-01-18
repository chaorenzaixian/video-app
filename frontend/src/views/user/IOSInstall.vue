<template>
  <div class="ios-install-page">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
    </div>

    <div class="container">
      <!-- Logo -->
      <div class="app-icon">
        <div class="icon-inner">
          <span>S</span>
        </div>
      </div>

      <!-- 标题 -->
      <h1 class="title">{{ appConfig.name || 'Soul' }}</h1>
      <p class="subtitle">{{ appConfig.description || '精彩内容尽在掌握' }}</p>

      <!-- 安装按钮 -->
      <a 
        :href="profileUrl" 
        class="install-btn"
        @click="handleInstallClick"
      >
        <i class="icon-download"></i>
        <span>安装到主屏幕</span>
      </a>

      <!-- 安装步骤 -->
      <div class="steps-section">
        <h3 class="section-title">
          <span class="icon">📖</span>
          安装步骤
        </h3>
        
        <div class="steps">
          <div 
            v-for="(step, index) in installSteps" 
            :key="index" 
            class="step"
            :class="{ 'step-active': currentStep === index }"
          >
            <div class="step-num">{{ index + 1 }}</div>
            <div class="step-content">
              <span class="step-text" v-html="step.text"></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 提示信息 -->
      <div class="info-card">
        <div class="info-icon">💡</div>
        <div class="info-text">
          <p>描述文件仅用于添加主屏幕快捷方式，不会收集任何个人信息。</p>
          <p class="secondary">如需卸载：设置 → 通用 → VPN与设备管理 → 删除描述文件</p>
        </div>
      </div>

      <!-- 已安装提示 -->
      <div v-if="isInstalled" class="installed-notice">
        <span class="check-icon">✅</span>
        <span>您似乎已经安装了描述文件，可以在主屏幕找到应用图标</span>
      </div>

      <!-- 底部链接 -->
      <div class="footer-links">
        <router-link to="/" class="link">返回首页</router-link>
        <span class="divider">|</span>
        <a href="javascript:;" @click="showHelp = true" class="link">遇到问题？</a>
      </div>
    </div>

    <!-- 帮助弹窗 -->
    <transition name="fade">
      <div v-if="showHelp" class="help-modal" @click.self="showHelp = false">
        <div class="help-content">
          <div class="help-header">
            <h3>常见问题</h3>
            <button class="close-btn" @click="showHelp = false">×</button>
          </div>
          <div class="help-body">
            <div class="faq-item">
              <h4>Q: 下载后没有提示安装？</h4>
              <p>A: 请打开"设置"App，在顶部查看"已下载描述文件"，点击进入安装。</p>
            </div>
            <div class="faq-item">
              <h4>Q: 提示"无法连接到服务器"？</h4>
              <p>A: 请检查网络连接，或尝试切换Wi-Fi/移动数据后重试。</p>
            </div>
            <div class="faq-item">
              <h4>Q: 安装后找不到图标？</h4>
              <p>A: 请滑动主屏幕查找，或在App资源库中搜索"{{ appConfig.name }}"。</p>
            </div>
            <div class="faq-item">
              <h4>Q: 如何卸载？</h4>
              <p>A: 设置 → 通用 → VPN与设备管理 → 找到描述文件 → 删除</p>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/utils/api'

const appConfig = ref({
  name: 'Soul',
  description: '精彩内容尽在掌握'
})

const showHelp = ref(false)
const currentStep = ref(-1)
const isInstalled = ref(false)

// 描述文件下载地址
const profileUrl = computed(() => {
  // 使用相对路径，让浏览器自动处理
  return '/api/v1/ios/profile.mobileconfig'
})

// 安装步骤
const installSteps = [
  { text: '点击上方 <strong>"安装到主屏幕"</strong> 按钮' },
  { text: '在弹出的提示中选择 <strong>"允许"</strong>' },
  { text: '打开 <strong>设置</strong> App → 点击顶部 <strong>"已下载描述文件"</strong>' },
  { text: '点击右上角 <strong>"安装"</strong> → 输入密码确认' },
  { text: '安装完成，返回主屏幕即可看到应用图标 🎉' }
]

// 检测是否是iOS设备
const isIOS = computed(() => {
  return /iPad|iPhone|iPod/.test(navigator.userAgent)
})

// 检测是否standalone模式（已安装）
const checkIfInstalled = () => {
  if (window.navigator.standalone === true) {
    isInstalled.value = true
  }
}

// 处理安装按钮点击
const handleInstallClick = () => {
  // 开始动画步骤
  currentStep.value = 0
  const timer = setInterval(() => {
    if (currentStep.value < installSteps.length - 1) {
      currentStep.value++
    } else {
      clearInterval(timer)
      setTimeout(() => {
        currentStep.value = -1
      }, 5000)
    }
  }, 2000)
}

// 加载配置
const loadConfig = async () => {
  try {
    const response = await api.get('/ios/config')
    if (response.data) {
      appConfig.value = {
        name: response.data.app_name || 'Soul',
        description: response.data.description || '精彩内容尽在掌握'
      }
    }
  } catch (error) {
    console.log('使用默认配置')
  }
}

onMounted(() => {
  checkIfInstalled()
  loadConfig()
})
</script>

<style scoped>
.ios-install-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
  position: relative;
  overflow: hidden;
  padding: 40px 20px 60px;
}

/* 背景装饰 */
.bg-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.1;
  animation: float 20s ease-in-out infinite;
}

.circle-1 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  top: -100px;
  right: -100px;
}

.circle-2 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, #06b6d4, #3b82f6);
  bottom: 20%;
  left: -80px;
  animation-delay: -7s;
}

.circle-3 {
  width: 200px;
  height: 200px;
  background: linear-gradient(135deg, #f472b6, #8b5cf6);
  bottom: 10%;
  right: -50px;
  animation-delay: -14s;
}

@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-30px) rotate(10deg); }
}

.container {
  max-width: 400px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

/* App图标 */
.app-icon {
  width: 120px;
  height: 120px;
  margin: 0 auto 30px;
  perspective: 500px;
}

.icon-inner {
  width: 100%;
  height: 100%;
  border-radius: 28px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a78bfa 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 
    0 15px 40px rgba(99, 102, 241, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  font-size: 52px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  animation: iconPulse 3s ease-in-out infinite;
}

@keyframes iconPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.02); }
}

/* 标题 */
.title {
  text-align: center;
  font-size: 34px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 12px;
  letter-spacing: 1px;
}

.subtitle {
  text-align: center;
  font-size: 16px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 40px;
}

/* 安装按钮 */
.install-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  width: 100%;
  padding: 18px 30px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  border-radius: 16px;
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  text-decoration: none;
  box-shadow: 
    0 10px 30px rgba(99, 102, 241, 0.4),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  transition: all 0.3s ease;
}

.install-btn:active {
  transform: scale(0.98);
  box-shadow: 0 5px 20px rgba(99, 102, 241, 0.3);
}

.icon-download {
  display: inline-block;
  width: 24px;
  height: 24px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='white' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4'/%3E%3C/svg%3E");
  background-size: contain;
}

/* 步骤部分 */
.steps-section {
  margin-top: 50px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 20px;
}

.section-title .icon {
  font-size: 20px;
}

.steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  transition: all 0.3s ease;
}

.step-active {
  background: rgba(99, 102, 241, 0.15);
  border-color: rgba(99, 102, 241, 0.3);
  transform: scale(1.02);
}

.step-num {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(139, 92, 246, 0.3));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  color: #a78bfa;
  flex-shrink: 0;
}

.step-active .step-num {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
}

.step-content {
  flex: 1;
  padding-top: 4px;
}

.step-text {
  font-size: 15px;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.85);
}

.step-text :deep(strong) {
  color: #a78bfa;
  font-weight: 600;
}

/* 信息卡片 */
.info-card {
  display: flex;
  gap: 14px;
  margin-top: 30px;
  padding: 18px;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 14px;
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.info-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.info-text {
  font-size: 13px;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.75);
}

.info-text p {
  margin: 0;
}

.info-text .secondary {
  margin-top: 8px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
}

/* 已安装提示 */
.installed-notice {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 20px;
  padding: 14px 18px;
  background: rgba(34, 197, 94, 0.15);
  border-radius: 12px;
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #4ade80;
  font-size: 14px;
}

.check-icon {
  font-size: 18px;
}

/* 底部链接 */
.footer-links {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
  margin-top: 40px;
}

.link {
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
  text-decoration: none;
  transition: color 0.2s;
}

.link:active {
  color: #a78bfa;
}

.divider {
  color: rgba(255, 255, 255, 0.2);
}

/* 帮助弹窗 */
.help-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  z-index: 1000;
  backdrop-filter: blur(5px);
}

.help-content {
  width: 100%;
  max-width: 380px;
  max-height: 80vh;
  background: #1a1a2e;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.help-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.help-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  color: rgba(255, 255, 255, 0.7);
  font-size: 20px;
  cursor: pointer;
}

.help-body {
  padding: 20px;
  overflow-y: auto;
  max-height: 60vh;
}

.faq-item {
  margin-bottom: 20px;
}

.faq-item:last-child {
  margin-bottom: 0;
}

.faq-item h4 {
  font-size: 14px;
  font-weight: 600;
  color: #a78bfa;
  margin-bottom: 8px;
}

.faq-item p {
  font-size: 13px;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
}

/* 动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式优化 */
@media (min-width: 768px) {
  .ios-install-page {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 60px 20px;
  }
  
  .container {
    max-width: 450px;
  }
  
  .app-icon {
    width: 140px;
    height: 140px;
  }
  
  .icon-inner {
    font-size: 60px;
    border-radius: 32px;
  }
  
  .title {
    font-size: 38px;
  }
  
  .install-btn {
    padding: 20px 36px;
    font-size: 19px;
  }
}

@media (min-width: 1024px) {
  .container {
    max-width: 500px;
  }
}

@media (hover: hover) {
  .install-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 15px 40px rgba(99, 102, 241, 0.5);
  }
  
  .step:hover {
    background: rgba(255, 255, 255, 0.08);
  }
  
  .link:hover {
    color: #a78bfa;
  }
  
  .close-btn:hover {
    background: rgba(255, 255, 255, 0.2);
  }
}
</style>






