<template>
  <div class="email-bind-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </div>
      <h1 class="page-title">绑定邮箱</h1>
      <div class="header-right"></div>
    </header>

    <!-- 已绑定提示 -->
    <div class="info-banner success" v-if="userEmail">
      <div class="info-icon">✅</div>
      <div class="info-text">
        <span>您已绑定邮箱</span>
        <span class="email">{{ maskedEmail }}</span>
      </div>
    </div>

    <!-- 表单区域 -->
    <div class="form-section">
      <!-- 新邮箱 -->
      <div class="form-item">
        <span class="form-label">邮箱</span>
        <input 
          type="email" 
          v-model="email"
          :placeholder="userEmail ? '请输入新邮箱地址' : '请输入邮箱地址'"
        />
      </div>
      
      <!-- 验证码 -->
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
      
      <!-- 绑定按钮 -->
      <button class="bind-btn" @click="bindEmail" :disabled="!canBind || binding">
        {{ binding ? '绑定中...' : (userEmail ? '更换绑定' : '立即绑定') }}
      </button>

      <!-- 调试模式提示 -->
      <div class="debug-tip" v-if="debugCode">
        <div class="debug-icon">🔧</div>
        <div class="debug-text">
          <span>调试模式 - 验证码已自动填入</span>
          <span class="debug-code">{{ debugCode }}</span>
        </div>
      </div>

      <!-- 说明 -->
      <div class="tips">
        <p>📧 绑定邮箱后可通过邮箱找回账号</p>
        <p>🔒 验证码将发送到您输入的邮箱地址</p>
        <p>⏰ 验证码有效期10分钟</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const router = useRouter()
const userStore = useUserStore()

const email = ref('')
const code = ref('')
const countdown = ref(0)
const binding = ref(false)
const sendingCode = ref(false)
let timer = null

// 当前绑定的邮箱
const userEmail = computed(() => userStore.user?.email)

// 隐藏部分邮箱显示
const maskedEmail = computed(() => {
  const emailVal = userEmail.value
  if (!emailVal) return ''
  const atIndex = emailVal.indexOf('@')
  if (atIndex <= 2) return emailVal
  return emailVal.slice(0, 2) + '***' + emailVal.slice(atIndex - 1)
})

// 验证邮箱格式
const isEmailValid = computed(() => {
  return /^[\w.-]+@[\w.-]+\.\w+$/.test(email.value)
})

// 是否可以绑定
const canBind = computed(() => {
  return isEmailValid.value && code.value.length >= 4
})

// 调试模式验证码
const debugCode = ref('')

// 发送验证码
const sendCode = async () => {
  if (countdown.value > 0 || !isEmailValid.value || sendingCode.value) return
  
  sendingCode.value = true
  debugCode.value = ''
  
  try {
    const res = await api.post('/auth/email/send-code', null, {
      params: {
        email: email.value,
        code_type: 'bind'
      }
    })
    
    // 调试模式：显示验证码
    if (res.data?.code) {
      debugCode.value = res.data.code
      // 自动填充验证码
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

// 绑定邮箱
const bindEmail = async () => {
  if (!canBind.value || binding.value) return
  binding.value = true
  
  try {
    // 先验证验证码
    await api.post('/auth/email/verify-code', null, {
      params: {
        email: email.value,
        code: code.value,
        code_type: 'bind'
      }
    })
    
    // 验证通过后更新用户邮箱
    await api.put('/users/me', {
      email: email.value
    })
    
    await userStore.fetchUser()
    ElMessage.success('邮箱绑定成功')
    router.back()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '绑定失败，请重试')
  } finally {
    binding.value = false
  }
}

onMounted(() => {
  userStore.fetchUser()
})
</script>

<style lang="scss" scoped>
.email-bind-page {
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

.info-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 20px;
  padding: 14px 16px;
  background: rgba(102, 126, 234, 0.15);
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 10px;
  
  &.success {
    background: rgba(76, 175, 80, 0.15);
    border-color: rgba(76, 175, 80, 0.3);
  }
  
  .info-icon {
    font-size: 20px;
  }
  
  .info-text {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.8);
    
    .email {
      font-weight: 600;
      color: #4caf50;
    }
  }
}

.form-section {
  padding: 30px 20px;
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

.bind-btn {
  width: 100%;
  height: 48px;
  margin-top: 40px;
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

// 响应式断点
@media (min-width: 768px) {
  .email-bind-page {
    max-width: 500px;
    margin: 0 auto;
  }
  
  .page-header {
    max-width: 500px;
    left: 50%;
    transform: translateX(-50%);
  }
  
  .bind-btn {
    width: 60%;
    margin-left: auto;
    margin-right: auto;
    display: block;
  }
}

@media (min-width: 1024px) {
  .email-bind-page {
    max-width: 600px;
  }
  
  .page-header {
    max-width: 600px;
  }
}
</style>



