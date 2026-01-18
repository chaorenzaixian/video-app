<template>
  <div class="nickname-edit-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </div>
      <h1 class="page-title">修改昵称</h1>
      <div class="save-btn" @click="saveNickname" :class="{ disabled: saving || !nickname.trim() }">
        {{ saving ? '保存中...' : '保存' }}
      </div>
    </header>

    <!-- 输入区域 -->
    <div class="input-section">
      <div class="input-wrapper">
        <input 
          type="text" 
          v-model="nickname"
          placeholder="请输入昵称"
          maxlength="20"
          ref="inputRef"
        />
        <div class="clear-btn" v-if="nickname" @click="nickname = ''">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.47 2 2 6.47 2 12s4.47 10 10 10 10-4.47 10-10S17.53 2 12 2zm5 13.59L15.59 17 12 13.41 8.41 17 7 15.59 10.59 12 7 8.41 8.41 7 12 10.59 15.59 7 17 8.41 13.41 12 17 15.59z"/>
          </svg>
        </div>
      </div>
      <p class="input-tip">注意*诱导性昵称会被投诉封号</p>
    </div>

    <!-- VIP 提示弹窗 -->
    <Teleport to="body">
      <div class="vip-modal-overlay" v-if="showVipModal" @click.self="closeVipModal">
        <div class="vip-modal-content">
          <h2 class="vip-modal-title">温馨提示</h2>
          <p class="vip-modal-text">您还不是VIP无法修改昵称!</p>
          <p class="vip-modal-subtext">开通会员 即可解锁继续</p>
          <button class="vip-modal-btn" @click="goToVip">立即开通</button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const router = useRouter()
const userStore = useUserStore()

const nickname = ref('')
const saving = ref(false)
const inputRef = ref(null)
const showVipModal = ref(false)

// 检查是否是VIP
const isVip = computed(() => {
  return userStore.user?.is_vip === true || userStore.user?.vip_level > 0
})

// 关闭VIP弹窗
const closeVipModal = () => {
  showVipModal.value = false
  router.back()
}

// 跳转到VIP页面
const goToVip = () => {
  showVipModal.value = false
  router.push('/user/vip')
}

// 保存昵称
const saveNickname = async () => {
  if (!nickname.value.trim()) {
    ElMessage.warning('请输入昵称')
    return
  }
  
  if (nickname.value.trim().length < 2) {
    ElMessage.warning('昵称至少2个字符')
    return
  }
  
  if (saving.value) return
  saving.value = true
  
  try {
    await api.put('/users/me', {
      nickname: nickname.value.trim()
    })
    await userStore.fetchUser()
    ElMessage.success('昵称已更新')
    router.back()
  } catch (error) {
    console.error('更新昵称失败:', error)
    ElMessage.error(error.response?.data?.detail || '更新失败，请重试')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  // 确保用户数据是最新的
  await userStore.fetchUser()
  
  // 检查VIP状态
  if (!isVip.value) {
    showVipModal.value = true
    return
  }
  
  // 设置当前昵称
  nickname.value = userStore.user?.nickname || ''
  // 聚焦输入框
  await nextTick()
  inputRef.value?.focus()
})
</script>

<style lang="scss" scoped>
.nickname-edit-page {
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

.input-section {
  padding: 30px 20px;
  
  .input-wrapper {
    display: flex;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.15);
    padding-bottom: 12px;
    
    input {
      flex: 1;
      background: none;
      border: none;
      outline: none;
      color: #fff;
      font-size: 18px;
      padding: 0;
      
      &::placeholder {
        color: rgba(255, 255, 255, 0.3);
      }
    }
    
    .clear-btn {
      width: 24px;
      height: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      
      svg {
        width: 20px;
        height: 20px;
        fill: rgba(255, 255, 255, 0.4);
      }
      
      &:active {
        opacity: 0.7;
      }
    }
  }
  
  .input-tip {
    margin-top: 12px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.4);
  }
}

// VIP 弹窗样式
.vip-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

.vip-modal-content {
  background: linear-gradient(180deg, #1a1a2e 0%, #0f0f1a 100%);
  border-radius: 16px;
  padding: 30px 24px;
  width: 100%;
  max-width: 300px;
  text-align: center;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
}

.vip-modal-title {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 20px 0;
}

.vip-modal-text {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 8px 0;
}

.vip-modal-subtext {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0 0 24px 0;
}

.vip-modal-btn {
  width: 100%;
  height: 44px;
  border: none;
  border-radius: 22px;
  background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  
  &:active {
    transform: scale(0.98);
  }
  
  &:hover {
    box-shadow: 0 4px 20px rgba(139, 92, 246, 0.4);
  }
}

// 响应式断点
@media (min-width: 768px) {
  .nickname-edit-page {
    max-width: 500px;
    margin: 0 auto;
  }
  
  .page-header {
    max-width: 500px;
    left: 50%;
    transform: translateX(-50%);
  }
}

@media (min-width: 1024px) {
  .nickname-edit-page {
    max-width: 600px;
  }
  
  .page-header {
    max-width: 600px;
  }
}
</style>



