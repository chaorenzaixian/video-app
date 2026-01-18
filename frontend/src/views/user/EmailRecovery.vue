<template>
  <div class="email-recovery-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </div>
      <h1 class="page-title">邮箱找回</h1>
      <div class="header-right"></div>
    </header>

    <!-- 说明区域 -->
    <div class="info-section">
      <div class="info-icon">📧</div>
      <h2>通过邮箱验证码登录</h2>
      <p>输入您绑定的邮箱，验证后直接登录账号</p>
    </div>

    <!-- 表单区域 -->
    <div class="form-section">
      <div class="form-item">
        <span class="form-label">邮箱</span>
        <input 
          type="email" 
          v-model="email"
          placeholder="请输入您绑定的邮箱"
        />
      </div>
      
      <div class="form-item">
        <span class="form-label">验证码</span>
        <input 
          type="text" 
          v-model="code"
          placeholder="请输入邮箱验证码"
          maxlength="6"
        />
        <div 
          class="code-btn" 
          @click="sendCode"
          :class="{ disabled: countdown > 0 || !isEmailValid || sendingCode }"
        >
          {{ sendingCode ? '发送中...' : (countdown > 0 ? `${countdown}s` : '获取验证码') }}
        </div>
      </div>

      <!-- 调试模式提示 -->
      <div class="debug-tip" v-if="debugCode">
        <div class="debug-icon">🔧</div>
        <div class="debug-text">
          <span>调试模式 - 验证码已自动填入</span>
          <span class="debug-code">{{ debugCode }}</span>
        </div>
      </div>
      
      <button class="submit-btn" @click="loginWithCode" :disabled="!canVerify || logging">
        {{ logging ? '登录中...' : '验证并登录' }}
      </button>

      <div class="tips">
        <p>💡 验证码将发送到您输入的邮箱</p>
        <p>⏰ 验证码有效期10分钟</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const userStore = useUserStore()

const email = ref('')
const code = ref('')
const debugCode = ref('')
const countdown = ref(0)
const sendingCode = ref(false)
const logging = ref(false)

let timer = null

// 验证邮箱格式
const isEmailValid = computed(() => {
  return /^[\w.-]+@[\w.-]+\.\w+$/.test(email.value)
})

// 是否可以验证
const canVerify = computed(() => {
  return isEmailValid.value && code.value.length >= 4
})

// 发送验证码
const sendCode = async () => {
  if (countdown.value > 0 || !isEmailValid.value || sendingCode.value) return
  
  sendingCode.value = true
  debugCode.value = ''
  
  try {
    // 使用 axios 直接调用，不需要登录
    const res = await axios.post('/api/v1/auth/email/send-code', null, {
      params: {
        email: email.value,
        code_type: 'login'
      }
    })
    
    // 调试模式：自动填充验证码
    if (res.data?.code) {
      debugCode.value = res.data.code
      code.value = res.data.code
      ElMessage({
        message: `调试模式：验证码 ${res.data.code} 已自动填入`,
        type: 'success',
        duration: 5000
      })
    } else {
      ElMessage.success(res.data?.message || '验证码已发送')
    }
    
    // 开始倒计时
    countdown.value = 60
    timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) {
        clearInterval(timer)
      }
    }, 1000)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '发送失败，请重试')
  } finally {
    sendingCode.value = false
  }
}

// 验证并登录
const loginWithCode = async () => {
  if (!canVerify.value || logging.value) return
  logging.value = true
  
  try {
    // 验证验证码并直接登录
    const res = await axios.post('/api/v1/auth/recovery/login', null, {
      params: {
        email: email.value,
        code: code.value
      }
    })
    
    // 保存token并登录
    if (res.data.access_token) {
      localStorage.setItem('token', res.data.access_token)
      // 获取用户信息
      await userStore.fetchUser()
      ElMessage.success('登录成功！')
      // 跳转到个人中心
      router.push('/user/profile')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '验证失败，请检查验证码')
  } finally {
    logging.value = false
  }
}
</script>

<style lang="scss" scoped>
.email-recovery-page {
  min-height: 100vh;
  background: #0a0a0a;
  color: #fff;
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

.info-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px 20px;
  text-align: center;
  
  .info-icon {
    font-size: 48px;
    margin-bottom: 16px;
  }
  
  h2 {
    font-size: 18px;
    font-weight: 600;
    margin: 0 0 8px;
  }
  
  p {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.6);
    margin: 0;
  }
}

.form-section {
  padding: 20px;
}

.form-item {
  display: flex;
  align-items: center;
  padding: 18px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  
  .form-label {
    font-size: 14px;
    color: #fff;
    width: 70px;
    flex-shrink: 0;
  }
  
  input {
    flex: 1;
    background: none;
    border: none;
    outline: none;
    color: #fff;
    font-size: 14px;
    
    &::placeholder {
      color: rgba(255, 255, 255, 0.3);
    }
  }
  
  .code-btn {
    font-size: 14px;
    color: #667eea;
    cursor: pointer;
    padding: 6px 12px;
    white-space: nowrap;
    
    &.disabled {
      color: rgba(255, 255, 255, 0.3);
      pointer-events: none;
    }
    
    &:active {
      opacity: 0.7;
    }
  }
}

.debug-tip {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 20px;
  padding: 14px 16px;
  background: rgba(255, 193, 7, 0.15);
  border: 1px solid rgba(255, 193, 7, 0.4);
  border-radius: 10px;
  
  .debug-icon {
    font-size: 20px;
  }
  
  .debug-text {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.8);
    
    .debug-code {
      font-size: 24px;
      font-weight: bold;
      color: #ffc107;
      letter-spacing: 4px;
      font-family: 'Courier New', monospace;
    }
  }
}

.submit-btn {
  width: 100%;
  height: 48px;
  margin-top: 30px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  border-radius: 24px;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.2s;
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  &:not(:disabled):active {
    transform: scale(0.98);
  }
}

.tips {
  margin-top: 30px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  
  p {
    margin: 0;
    padding: 6px 0;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.6);
    
    &:first-child {
      padding-top: 0;
    }
    
    &:last-child {
      padding-bottom: 0;
    }
  }
}

// 响应式优化
@media (min-width: 768px) {
  .email-recovery-page {
    max-width: 500px;
    margin: 0 auto;
  }
  
  .page-header {
    max-width: 500px;
    left: 50%;
    transform: translateX(-50%);
  }
  
  .info-section {
    padding-top: 60px;
    
    .info-icon {
      font-size: 56px;
    }
    
    h2 {
      font-size: 20px;
    }
  }
}

@media (min-width: 1024px) {
  .email-recovery-page {
    max-width: 550px;
  }
  
  .page-header {
    max-width: 550px;
  }
}

@media (hover: hover) {
  .code-btn:not(.disabled):hover {
    opacity: 0.8;
  }
  
  .submit-btn:not(:disabled):hover {
    opacity: 0.9;
  }
}
</style>


