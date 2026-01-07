<template>
  <div class="avatar-select-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
        </svg>
      </div>
      <h1 class="page-title">选择头像</h1>
      <div class="save-btn" @click="saveAvatar" :class="{ disabled: saving }">
        {{ saving ? '保存中...' : '保存' }}
      </div>
    </header>

    <!-- 当前头像预览 -->
    <div class="current-avatar-section">
      <div class="current-avatar">
        <img :src="selectedAvatarUrl" alt="当前头像" />
      </div>
      <span class="current-label">当前头像</span>
    </div>

    <!-- 头像列表 -->
    <div class="avatar-grid">
      <div 
        v-for="(avatar, index) in avatarList" 
        :key="index"
        class="avatar-item"
        :class="{ selected: selectedAvatar === avatar.path }"
        @click="selectAvatar(avatar.path)"
      >
        <img :src="avatar.url" :alt="'头像' + (index + 1)" />
        <div class="selected-mark" v-if="selectedAvatar === avatar.path">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
          </svg>
        </div>
      </div>
    </div>

    <!-- VIP 提示弹窗 -->
    <Teleport to="body">
      <div class="vip-modal-overlay" v-if="showVipModal" @click.self="closeVipModal">
        <div class="vip-modal-content">
          <h2 class="vip-modal-title">温馨提示</h2>
          <p class="vip-modal-text">您还不是VIP无法修改头像!</p>
          <p class="vip-modal-subtext">开通会员 即可解锁继续</p>
          <button class="vip-modal-btn" @click="goToVip">立即开通</button>
        </div>
      </div>
    </Teleport>
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
const user = computed(() => userStore.user)

const saving = ref(false)
const selectedAvatar = ref('')
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

// 生成头像列表 (使用预设头像)
const avatarList = ref([])

// 初始化头像列表
const initAvatarList = () => {
  const list = []
  
  // 原有17个预设头像
  for (let i = 1; i <= 17; i++) {
    const path = `/images/avatars/icon_avatar_${i}.webp`
    list.push({
      path: path,
      url: path
    })
  }
  
  // 新增的DM头像第一批 (15个)
  for (let i = 1; i <= 15; i++) {
    const num = String(i).padStart(3, '0')
    const path = `/images/avatars/DM_20251217202131_${num}.JPEG`
    list.push({
      path: path,
      url: path
    })
  }
  
  // 新增的DM头像第二批 (20个)
  for (let i = 1; i <= 20; i++) {
    const num = String(i).padStart(3, '0')
    const path = `/images/avatars/DM_20251217202341_${num}.JPEG`
    list.push({
      path: path,
      url: path
    })
  }
  
  avatarList.value = list
}

// 获取默认头像路径
const getDefaultAvatarPath = (userId) => {
  const totalAvatars = 52 // 17 + 15 + 20
  const index = (userId % totalAvatars)
  
  if (index < 17) {
    // 原有头像 (0-16)
    return `/images/avatars/icon_avatar_${index + 1}.webp`
  } else if (index < 32) {
    // DM第一批 (17-31)
    const num = String(index - 17 + 1).padStart(3, '0')
    return `/images/avatars/DM_20251217202131_${num}.JPEG`
  } else {
    // DM第二批 (32-51)
    const num = String(index - 32 + 1).padStart(3, '0')
    return `/images/avatars/DM_20251217202341_${num}.JPEG`
  }
}

// 选中的头像URL
const selectedAvatarUrl = computed(() => {
  if (selectedAvatar.value) {
    return selectedAvatar.value
  }
  // 返回当前用户头像
  const avatar = user.value?.avatar
  if (avatar) {
    if (avatar.startsWith('http')) return avatar
    return avatar.startsWith('/') ? avatar : `/${avatar}`
  }
  const userId = user.value?.id || 1
  return getDefaultAvatarPath(userId)
})

// 选择头像
const selectAvatar = (path) => {
  selectedAvatar.value = path
}

// 保存头像
const saveAvatar = async () => {
  if (!selectedAvatar.value) {
    ElMessage.warning('请选择一个头像')
    return
  }
  
  if (saving.value) return
  saving.value = true
  
  try {
    await api.put('/users/me', {
      avatar: selectedAvatar.value
    })
    await userStore.fetchUser()
    ElMessage.success('头像已更新')
    router.back()
  } catch (error) {
    console.error('更新头像失败:', error)
    ElMessage.error('更新失败，请重试')
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
  
  initAvatarList()
  // 设置当前选中的头像
  if (user.value?.avatar) {
    selectedAvatar.value = user.value.avatar
  }
})
</script>

<style lang="scss" scoped>
.avatar-select-page {
  min-height: 100vh;
  background: #0a0a0a;
  color: #fff;
  padding-bottom: env(safe-area-inset-bottom, 20px);
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

.current-avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 30px 20px 20px;
  
  .current-avatar {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    overflow: hidden;
    border: 3px solid rgba(255, 255, 255, 0.1);
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }
  
  .current-label {
    margin-top: 12px;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.5);
  }
}

.avatar-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding: 20px;
}

.avatar-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 50%;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  &:active {
    transform: scale(0.95);
  }
  
  &.selected {
    box-shadow: 0 0 0 3px #ff6b6b;
    
    .selected-mark {
      display: flex;
    }
  }
  
  .selected-mark {
    display: none;
    position: absolute;
    right: -2px;
    bottom: -2px;
    width: 24px;
    height: 24px;
    background: #ff6b6b;
    border-radius: 50%;
    align-items: center;
    justify-content: center;
    
    svg {
      width: 16px;
      height: 16px;
      fill: #fff;
    }
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
</style>



