<template>
  <div class="login-page">
    <!-- 返回按钮 -->
    <div class="back-btn" @click="$router.push('/user')">
      <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
    </div>

    <!-- Logo -->
    <div class="logo-section">
      <div class="logo">Soul</div>
      <p class="slogan">发现精彩，享受生活</p>
    </div>

    <!-- 登录表单 -->
    <div class="form-section" v-if="!isRegister">
      <div class="form-title">登录账号</div>
      
      <div class="input-group">
        <span class="input-icon">📱</span>
        <input 
          v-model="loginForm.username" 
          type="text" 
          placeholder="请输入邮箱/用户名"
        />
      </div>
      
      <div class="input-group">
        <span class="input-icon">🔒</span>
        <input 
          v-model="loginForm.password" 
          :type="showPassword ? 'text' : 'password'" 
          placeholder="请输入密码"
        />
        <span class="toggle-pwd" @click="showPassword = !showPassword">
          {{ showPassword ? '👁' : '👁‍🗨' }}
        </span>
      </div>

      <div class="form-options">
        <label class="remember-me">
          <input type="checkbox" v-model="rememberMe" />
          <span>记住密码</span>
        </label>
        <a class="forgot-pwd" @click="forgotPassword">忘记密码？</a>
      </div>

      <button class="submit-btn" @click="handleLogin" :disabled="loading">
        {{ loading ? '登录中...' : '登 录' }}
      </button>

      <div class="switch-mode">
        还没有账号？<a @click="isRegister = true">立即注册</a>
      </div>
    </div>

    <!-- 注册表单 -->
    <div class="form-section" v-else>
      <div class="form-title">注册账号</div>
      
      <div class="input-group">
        <span class="input-icon">👤</span>
        <input 
          v-model="registerForm.username" 
          type="text" 
          placeholder="请输入用户名"
        />
      </div>

      <div class="input-group">
        <span class="input-icon">📧</span>
        <input 
          v-model="registerForm.email" 
          type="email" 
          placeholder="请输入邮箱"
        />
      </div>
      
      <div class="input-group">
        <span class="input-icon">🔒</span>
        <input 
          v-model="registerForm.password" 
          :type="showPassword ? 'text' : 'password'" 
          placeholder="请输入密码 (至少6位)"
        />
        <span class="toggle-pwd" @click="showPassword = !showPassword">
          {{ showPassword ? '👁' : '👁‍🗨' }}
        </span>
      </div>

      <div class="input-group">
        <span class="input-icon">🔒</span>
        <input 
          v-model="registerForm.confirmPassword" 
          type="password" 
          placeholder="请确认密码"
        />
      </div>

      <div class="input-group">
        <span class="input-icon">🎁</span>
        <input 
          v-model="registerForm.inviteCode" 
          type="text" 
          placeholder="邀请码 (选填，送7天VIP)"
        />
      </div>

      <div class="agreement">
        <input type="checkbox" v-model="agreeTerms" />
        <span>我已阅读并同意 <a>《用户协议》</a> 和 <a>《隐私政策》</a></span>
      </div>

      <button class="submit-btn" @click="handleRegister" :disabled="loading || !agreeTerms">
        {{ loading ? '注册中...' : '注 册' }}
      </button>

      <div class="switch-mode">
        已有账号？<a @click="isRegister = false">立即登录</a>
      </div>
    </div>

    <!-- 第三方登录 -->
    <div class="third-party">
      <div class="divider">
        <span>其他登录方式</span>
      </div>
      <div class="third-party-icons">
        <div class="icon-item wechat">
          <span>💚</span>
        </div>
        <div class="icon-item qq">
          <span>🐧</span>
        </div>
        <div class="icon-item weibo">
          <span>🔴</span>
        </div>
      </div>
    </div>

    <!-- 底部提示 -->
    <div class="footer-tip">
      <p>登录即表示同意 Soul 的服务条款</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const router = useRouter()
const userStore = useUserStore()

const isRegister = ref(false)
const showPassword = ref(false)
const loading = ref(false)
const rememberMe = ref(false)
const agreeTerms = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  inviteCode: ''
})

const handleLogin = async () => {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }

  loading.value = true
  try {
    await userStore.login({
      username: loginForm.username,
      password: loginForm.password
    })
    
    ElMessage.success('登录成功')
    router.push('/user')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  if (!registerForm.username || !registerForm.email || !registerForm.password) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  if (registerForm.password !== registerForm.confirmPassword) {
    ElMessage.warning('两次密码不一致')
    return
  }
  
  if (registerForm.password.length < 6) {
    ElMessage.warning('密码至少6位')
    return
  }

  loading.value = true
  try {
    await api.post('/auth/register', {
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password,
      invite_code: registerForm.inviteCode || undefined
    })
    
    ElMessage.success('注册成功，请登录')
    isRegister.value = false
    loginForm.username = registerForm.username
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}

const forgotPassword = () => {
  ElMessage.info('请联系客服重置密码')
}
</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  min-height: 100dvh;
  background: linear-gradient(135deg, #0d0d1a 0%, #1a1a2e 50%, #16213e 100%);
  color: #fff;
  padding: 20px;
  padding-bottom: calc(20px + env(safe-area-inset-bottom, 0px));
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 100vw;
  overflow-x: hidden;
}

.back-btn {
  width: 36px;
  height: 36px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 20px;
  opacity: 0.7;
  cursor: pointer;
  
  &:hover {
    opacity: 1;
  }
}

.logo-section {
  text-align: center;
  padding: 40px 0;
  
  .logo {
    font-size: 48px;
    font-weight: bold;
    font-style: italic;
    background: linear-gradient(90deg, #a855f7, #ec4899, #f43f5e);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 4px;
  }
  
  .slogan {
    margin-top: 10px;
    color: rgba(255, 255, 255, 0.5);
    font-size: 14px;
  }
}

.form-section {
  flex: 1;
  max-width: 400px;
  margin: 0 auto;
  width: 100%;
  
  .form-title {
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 30px;
    text-align: center;
  }
  
  .input-group {
    display: flex;
    align-items: center;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 0 16px;
    margin-bottom: 16px;
    border: 1px solid transparent;
    transition: all 0.3s;
    
    &:focus-within {
      border-color: #a855f7;
      background: rgba(168, 85, 247, 0.1);
    }
    
    .input-icon {
      font-size: 18px;
      margin-right: 12px;
    }
    
    input {
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      color: #fff;
      font-size: 16px;
      padding: 16px 0;
      
      &::placeholder {
        color: rgba(255, 255, 255, 0.4);
      }
    }
    
    .toggle-pwd {
      cursor: pointer;
      font-size: 18px;
      opacity: 0.6;
    }
  }
  
  .form-options {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    font-size: 14px;
    
    .remember-me {
      display: flex;
      align-items: center;
      gap: 6px;
      color: rgba(255, 255, 255, 0.6);
      cursor: pointer;
      
      input {
        accent-color: #a855f7;
      }
    }
    
    .forgot-pwd {
      color: #ec4899;
      cursor: pointer;
    }
  }
  
  .agreement {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    margin-bottom: 24px;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.6);
    
    input {
      margin-top: 2px;
      accent-color: #a855f7;
    }
    
    a {
      color: #ec4899;
      cursor: pointer;
    }
  }
  
  .submit-btn {
    width: 100%;
    padding: 16px;
    background: linear-gradient(90deg, #a855f7, #ec4899);
    border: none;
    border-radius: 12px;
    color: #fff;
    font-size: 18px;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 10px 30px rgba(168, 85, 247, 0.4);
    }
    
    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
      transform: none;
    }
  }
  
  .switch-mode {
    text-align: center;
    margin-top: 20px;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.6);
    
    a {
      color: #ec4899;
      cursor: pointer;
      font-weight: bold;
    }
  }
}

.third-party {
  padding: 30px 0;
  
  .divider {
    display: flex;
    align-items: center;
    margin-bottom: 24px;
    
    &::before, &::after {
      content: '';
      flex: 1;
      height: 1px;
      background: rgba(255, 255, 255, 0.1);
    }
    
    span {
      padding: 0 16px;
      color: rgba(255, 255, 255, 0.4);
      font-size: 12px;
    }
  }
  
  .third-party-icons {
    display: flex;
    justify-content: center;
    gap: 30px;
    
    .icon-item {
      width: 50px;
      height: 50px;
      border-radius: 50%;
      display: flex;
      justify-content: center;
      align-items: center;
      font-size: 24px;
      cursor: pointer;
      transition: transform 0.3s;
      
      &:hover {
        transform: scale(1.1);
      }
      
      &.wechat {
        background: rgba(7, 193, 96, 0.2);
      }
      
      &.qq {
        background: rgba(0, 149, 246, 0.2);
      }
      
      &.weibo {
        background: rgba(230, 22, 45, 0.2);
      }
    }
  }
}

.footer-tip {
  text-align: center;
  padding: 20px;
  
  p {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.3);
  }
}

// ============ 响应式断点变量 ============
$bp-lg: 768px;
$bp-xl: 1024px;
$bp-xxl: 1280px;
$bp-2k: 1920px;
$bp-4k: 2560px;

// ============ 响应式适配 ============

// 平板及以上居中显示
@media (min-width: $bp-lg) {
  .login-page {
    justify-content: center;
    align-items: center;
    padding: 40px;
  }
  
  .back-btn {
    position: fixed;
    top: 30px;
    left: 30px;
    width: 44px;
    height: 44px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 50%;
  }
  
  .logo-section {
    .logo {
      font-size: 56px;
    }
    
    .slogan {
      font-size: 16px;
    }
  }
  
  .form-section {
    background: rgba(255, 255, 255, 0.05);
    padding: 40px;
    border-radius: 24px;
    backdrop-filter: blur(10px);
  }
  
  .third-party {
    width: 100%;
    max-width: 400px;
  }
}

// 小屏手机
@media (max-width: 374px) {
  .login-page {
    padding: 15px;
  }
  
  .logo-section {
    padding: 30px 0;
    
    .logo {
      font-size: 40px;
    }
  }
  
  .form-section {
    .form-title {
      font-size: 20px;
    }
    
    .input-group {
      padding: 0 12px;
      
      input {
        font-size: 14px;
        padding: 14px 0;
      }
    }
    
    .submit-btn {
      padding: 14px;
      font-size: 16px;
    }
  }
  
  .third-party .third-party-icons {
    gap: 20px;
    
    .icon-item {
      width: 44px;
      height: 44px;
      font-size: 20px;
    }
  }
}

// ============ 超大屏幕优化 ============
@media (min-width: $bp-xl) {
  .login-page {
    .form-section {
      max-width: 500px;
    }
  }
}

@media (min-width: $bp-2k) {
  .login-page {
    .form-section {
      max-width: 550px;
      padding: 50px;
    }
  }
  
  .logo-section .logo {
    font-size: 64px;
  }
  
  .form-section .form-title {
    font-size: 28px;
  }
  
  .input-group input {
    font-size: 18px;
    padding: 18px 0;
  }
  
  .submit-btn {
    font-size: 20px;
    padding: 18px;
  }
}

@media (min-width: $bp-4k) {
  .login-page {
    .form-section {
      max-width: 650px;
      padding: 60px;
    }
  }
  
  .logo-section .logo {
    font-size: 72px;
  }
  
  .form-section .form-title {
    font-size: 32px;
  }
  
  .input-group input {
    font-size: 20px;
    padding: 20px 0;
  }
  
  .submit-btn {
    font-size: 22px;
    padding: 20px;
  }
}

// ============ 触摸设备优化 ============
@media (hover: none) and (pointer: coarse) {
  .submit-btn:hover,
  .icon-item:hover {
    transform: none !important;
    background: inherit !important;
  }
  
  .submit-btn:active {
    transform: scale(0.98);
    opacity: 0.9;
  }
  
  .icon-item:active {
    transform: scale(0.95);
    opacity: 0.8;
  }
}
</style>
