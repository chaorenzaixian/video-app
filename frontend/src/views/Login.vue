<template>
  <div class="login-container">
    <div class="login-bg">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
      <div class="shape shape-3"></div>
    </div>
    
    <div class="login-card">
      <div class="login-header">
        <el-icon size="48" color="#6366f1"><VideoPlay /></el-icon>
        <h1>管理后台</h1>
        <p>VOD Platform 管理系统</p>
      </div>
      
      <el-form 
        ref="formRef"
        :model="form" 
        :rules="rules" 
        @submit.prevent="handleLogin"
        class="login-form"
      >
        <el-form-item prop="username">
          <el-input 
            v-model="form.username" 
            placeholder="用户名 / 邮箱 / 手机号"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input 
            v-model="form.password" 
            type="password"
            placeholder="密码"
            size="large"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-form-item>
          <div class="form-options">
            <el-checkbox v-model="rememberMe">记住我</el-checkbox>
            <el-link type="primary" :underline="false">忘记密码？</el-link>
          </div>
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            size="large"
            :loading="loading"
            @click="handleLogin"
            class="login-btn"
          >
            登 录
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <p class="admin-notice">仅限管理员登录</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { User, Lock, VideoPlay } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref(null)
const loading = ref(false)
const rememberMe = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      await userStore.login(form)
      ElMessage.success('登录成功')
      
      const redirect = route.query.redirect || '/admin/dashboard'
      router.push(redirect)
    } catch (error) {
      // 错误已在拦截器中处理
    } finally {
      loading.value = false
    }
  })
}
</script>

<style lang="scss" scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
  
  .login-bg {
    position: absolute;
    inset: 0;
    overflow: hidden;
    
    .shape {
      position: absolute;
      border-radius: 50%;
      opacity: 0.1;
      animation: float 6s ease-in-out infinite;
      
      &.shape-1 {
        width: 500px;
        height: 500px;
        background: #fff;
        top: -200px;
        right: -100px;
      }
      
      &.shape-2 {
        width: 300px;
        height: 300px;
        background: #fff;
        bottom: -100px;
        left: -50px;
        animation-delay: 2s;
      }
      
      &.shape-3 {
        width: 200px;
        height: 200px;
        background: #fff;
        top: 50%;
        left: 20%;
        animation-delay: 4s;
      }
    }
  }
  
  .login-card {
    width: 420px;
    padding: 40px;
    background: rgba(255, 255, 255, 0.95);
    border-radius: 20px;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    backdrop-filter: blur(10px);
    position: relative;
    z-index: 1;
    
    .login-header {
      text-align: center;
      margin-bottom: 32px;
      
      h1 {
        margin: 16px 0 8px;
        font-size: 28px;
        font-weight: 700;
        color: #1f2937;
      }
      
      p {
        color: #6b7280;
        font-size: 14px;
      }
    }
    
    .login-form {
      .form-options {
        width: 100%;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      
      .login-btn {
        width: 100%;
        height: 48px;
        font-size: 16px;
        border-radius: 10px;
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        border: none;
        
        &:hover {
          background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        }
      }
    }
    
    .login-footer {
      text-align: center;
      margin-top: 24px;
      
      p {
        color: #6b7280;
        font-size: 14px;
      }
    }
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(5deg);
  }
}
</style>









