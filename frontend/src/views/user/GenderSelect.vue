<template>
  <div class="gender-select-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
        </svg>
      </div>
      <h1 class="page-title">性别</h1>
      <div class="save-btn" @click="saveGender" :class="{ disabled: saving }">
        {{ saving ? '保存中...' : '保存' }}
      </div>
    </header>

    <!-- 选项列表 -->
    <div class="options-list">
      <div 
        class="option-item" 
        @click="selectedGender = 'male'"
      >
        <span class="option-label">男</span>
        <div class="check-mark" v-if="selectedGender === 'male'">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
          </svg>
        </div>
      </div>
      
      <div 
        class="option-item" 
        @click="selectedGender = 'female'"
      >
        <span class="option-label">女</span>
        <div class="check-mark" v-if="selectedGender === 'female'">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
          </svg>
        </div>
      </div>
      
      <div 
        class="option-item" 
        @click="selectedGender = 'secret'"
      >
        <span class="option-label">保密</span>
        <div class="check-mark" v-if="selectedGender === 'secret'">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
          </svg>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const router = useRouter()
const userStore = useUserStore()

const selectedGender = ref('secret')
const saving = ref(false)

// 保存性别
const saveGender = async () => {
  if (saving.value) return
  saving.value = true
  
  try {
    await api.put('/users/me', {
      gender: selectedGender.value
    })
    await userStore.fetchUser()
    ElMessage.success('性别已更新')
    router.back()
  } catch (error) {
    console.error('更新性别失败:', error)
    ElMessage.error('更新失败，请重试')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  // 设置当前性别
  const gender = userStore.user?.gender
  if (gender === 'male' || gender === 'female' || gender === 'secret') {
    selectedGender.value = gender
  } else {
    selectedGender.value = 'secret'
  }
})
</script>

<style lang="scss" scoped>
.gender-select-page {
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
  
  .save-btn {
    font-size: 15px;
    color: rgba(255, 255, 255, 0.7);
    cursor: pointer;
    padding: 6px 12px;
    
    &:active {
      opacity: 0.7;
    }
    
    &.disabled {
      opacity: 0.5;
      pointer-events: none;
    }
  }
}

.options-list {
  padding: 10px 0;
}

.option-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  cursor: pointer;
  transition: background 0.2s;
  
  &:active {
    background: rgba(255, 255, 255, 0.05);
  }
  
  .option-label {
    font-size: 14px;
    color: #fff;
  }
  
  .check-mark {
    width: 24px;
    height: 24px;
    background: linear-gradient(135deg, #7c5ce0, #a855f7);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    
    svg {
      width: 16px;
      height: 16px;
      fill: #fff;
    }
  }
}
</style>



