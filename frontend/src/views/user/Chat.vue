<template>
  <div class="chat-page">
    <!-- 顶部导航 -->
    <div class="chat-header">
      <div class="back-btn" @click="goBack">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </div>
      <div class="user-name">
        <span>{{ targetUser.nickname || '用户' }}</span>
        <img 
          v-if="targetUser.vip_level > 0" 
          :src="getVipLevelIcon(targetUser.vip_level)" 
          class="header-vip-badge"
          alt="VIP"
        />
      </div>
      <div class="user-avatar" @click="goToProfile">
        <img :src="getAvatarUrl(targetUser.avatar, targetUserId)" alt="avatar" />
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="chat-messages" ref="messagesContainer">
      <div class="messages-loading" v-if="loading">
        <div class="loading-spinner"></div>
      </div>
      
      <div class="empty-messages" v-else-if="messages.length === 0">
        <p>暂无消息，快来打个招呼吧~</p>
      </div>
      
      <template v-else>
        <div 
          v-for="message in messages" 
          :key="message.id"
          class="message-item"
          :class="{ 'is-mine': message.is_mine }"
        >
          <div class="message-avatar" v-if="!message.is_mine">
            <img :src="getAvatarUrl(targetUser.avatar, targetUserId)" alt="" />
          </div>
          
          <div class="message-content">
            <!-- 用户昵称 -->
            <div class="message-nickname" v-if="!message.is_mine">
              <span class="nickname-text">{{ targetUser.nickname || '用户' }}</span>
              <img 
                v-if="targetUser.vip_level > 0" 
                :src="getVipLevelIcon(targetUser.vip_level)" 
                class="vip-badge"
                alt="VIP"
              />
            </div>
            <div class="message-nickname is-mine" v-else>
              <span class="nickname-text">{{ currentUser?.nickname || '我' }}</span>
              <img 
                v-if="currentUser?.vip_level > 0" 
                :src="getVipLevelIcon(currentUser?.vip_level)" 
                class="vip-badge"
                alt="VIP"
              />
            </div>
            
            <div class="message-bubble" v-if="message.message_type === 'text'">
              {{ message.content }}
            </div>
            <div class="message-image" v-else-if="message.message_type === 'image'">
              <img :src="message.content" alt="图片" @click="previewImage(message.content)" />
            </div>
            <div class="message-time">{{ formatTime(message.created_at) }}</div>
          </div>
          
          <div class="message-avatar" v-if="message.is_mine">
            <img :src="getAvatarUrl(currentUser?.avatar, currentUser?.id || 1)" alt="" />
          </div>
        </div>
      </template>
    </div>

    <!-- 底部输入区域 -->
    <div class="chat-input-area">
      <div class="input-wrapper">
        <input 
          type="text" 
          v-model="inputMessage"
          :placeholder="'私信需要消费' + messageCost + '金币'"
          @keydown.enter="sendMessage"
          :disabled="sending"
        />
      </div>
      
      <!-- 图片上传按钮 -->
      <div class="action-btn" @click="openImagePicker">
        <img src="/images/backgrounds/下载 (5).webp" alt="上传图片" class="action-icon" />
      </div>
      
      <!-- 发送按钮 -->
      <div class="action-btn send-btn" @click="sendMessage" :class="{ disabled: !canSend }">
        <img src="/images/backgrounds/下载 (4).webp" alt="发送" class="action-icon" />
      </div>
      
      <!-- 隐藏的图片上传 -->
      <input 
        type="file" 
        ref="imageInput" 
        accept="image/*" 
        @change="handleImageSelect"
        style="display: none;"
        capture="environment"
      />
    </div>

    <!-- 图片选择弹窗 -->
    <div class="image-picker-modal" v-if="showImagePicker" @click.self="showImagePicker = false">
      <div class="picker-content">
        <div class="picker-option" @click="selectFromGallery">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
            <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
            <circle cx="8.5" cy="8.5" r="1.5" fill="currentColor"/>
            <path d="M21 15L16 10L5 21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>从相册选择</span>
        </div>
        <div class="picker-option" @click="takePhoto">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
            <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2v11z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="12" cy="13" r="4" stroke="currentColor" stroke-width="2"/>
          </svg>
          <span>拍照</span>
        </div>
        <div class="picker-cancel" @click="showImagePicker = false">取消</div>
      </div>
    </div>

    <!-- 图片预览 -->
    <div class="image-preview-modal" v-if="previewImageUrl" @click="previewImageUrl = null">
      <img :src="previewImageUrl" alt="预览" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import api from '@/utils/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 用户信息
const targetUserId = computed(() => parseInt(route.params.id))
const targetUser = ref({ nickname: '', avatar: null })
const currentUser = computed(() => userStore.user)

// 获取默认头像路径（共52个）
const getDefaultAvatarPath = (userId) => {
  const totalAvatars = 52
  const index = (userId % totalAvatars)
  
  if (index < 17) {
    return `/images/avatars/icon_avatar_${index + 1}.webp`
  } else if (index < 32) {
    const num = String(index - 17 + 1).padStart(3, '0')
    return `/images/avatars/DM_20251217202131_${num}.JPEG`
  } else {
    const num = String(index - 32 + 1).padStart(3, '0')
    return `/images/avatars/DM_20251217202341_${num}.JPEG`
  }
}

// 获取头像URL（处理不同格式）
const getAvatarUrl = (avatar, userId = 1) => {
  if (avatar) {
    if (avatar.startsWith('/')) return avatar
    if (avatar.startsWith('http')) return avatar
    return '/' + avatar
  }
  // 使用默认头像
  const numericId = parseInt(userId) || 1
  return getDefaultAvatarPath(numericId)
}

// VIP等级图标映射（与个人中心保持一致）
const VIP_LEVEL_ICONS = {
  1: '/images/backgrounds/vip_gold.webp',      // 普通VIP
  2: '/images/backgrounds/vip_1.webp',         // VIP1
  3: '/images/backgrounds/vip_2.webp',         // VIP2
  4: '/images/backgrounds/vip_3.webp',         // VIP3
  5: '/images/backgrounds/super_vip_red.webp', // 黄金至尊
}

// 获取VIP等级图标
const getVipLevelIcon = (level) => {
  return VIP_LEVEL_ICONS[level] || VIP_LEVEL_ICONS[1] || ''
}

// 消息数据
const messages = ref([])
const inputMessage = ref('')
const loading = ref(true)
const sending = ref(false)
const messageCost = ref(100) // 消息花费金币

// UI状态
const messagesContainer = ref(null)
const imageInput = ref(null)
const showImagePicker = ref(false)
const previewImageUrl = ref(null)

// 是否可发送
const canSend = computed(() => {
  return inputMessage.value.trim().length > 0 && !sending.value
})

// 获取私信消费金币数
const fetchMessageCost = async () => {
  try {
    const res = await api.get('/social/messages/cost')
    if (res.data?.cost) {
      messageCost.value = res.data.cost
    }
  } catch (error) {
    console.error('获取私信费用失败', error)
  }
}

// 获取用户信息
const fetchTargetUser = async () => {
  try {
    const res = await api.get(`/users/${targetUserId.value}/profile`)
    if (res.data) {
      targetUser.value = res.data
    }
  } catch (error) {
    console.error('获取用户信息失败', error)
    // 尝试从路由query获取
    if (route.query.nickname) {
      targetUser.value.nickname = route.query.nickname
    }
    if (route.query.avatar) {
      targetUser.value.avatar = route.query.avatar
    }
  }
}

// 获取消息记录
const fetchMessages = async () => {
  loading.value = true
  try {
    const res = await api.get(`/social/messages/${targetUserId.value}`)
    messages.value = res.data || res || []
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('获取消息失败', error)
    messages.value = []
  } finally {
    loading.value = false
  }
}

// 发送消息
const sendMessage = async () => {
  if (!canSend.value) return
  
  const content = inputMessage.value.trim()
  if (!content) return
  
  sending.value = true
  try {
    const res = await api.post('/social/messages', {
      receiver_id: targetUserId.value,
      content: content,
      message_type: 'text'
    })
    
    // 添加到消息列表
    messages.value.push({
      id: res.data?.message_id || Date.now(),
      sender_id: currentUser.value?.id,
      content: content,
      message_type: 'text',
      is_mine: true,
      created_at: new Date().toISOString()
    })
    
    inputMessage.value = ''
    await nextTick()
    scrollToBottom()
    
    // 显示消费提示
    ElMessage.success(`发送成功，消费${messageCost.value}金币`)
  } catch (error) {
    console.error('发送失败', error)
    const errorMsg = error.response?.data?.detail || '发送失败，请重试'
    
    // 如果是金币不足，提示充值
    if (errorMsg.includes('金币余额不足')) {
      ElMessageBox.confirm(
        `发送私信需要${messageCost.value}金币，您的余额不足，是否前往充值？`,
        '金币不足',
        {
          confirmButtonText: '去充值',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(() => {
        router.push('/user/coins')
      }).catch(() => {})
    } else {
      ElMessage.error(errorMsg)
    }
  } finally {
    sending.value = false
  }
}

// 打开图片选择器
const openImagePicker = () => {
  showImagePicker.value = true
}

// 从相册选择
const selectFromGallery = () => {
  showImagePicker.value = false
  if (imageInput.value) {
    imageInput.value.removeAttribute('capture')
    imageInput.value.click()
  }
}

// 拍照
const takePhoto = () => {
  showImagePicker.value = false
  if (imageInput.value) {
    imageInput.value.setAttribute('capture', 'environment')
    imageInput.value.click()
  }
}

// 处理图片选择
const handleImageSelect = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  // 检查文件类型
  if (!file.type.startsWith('image/')) {
    ElMessage.error('请选择图片文件')
    return
  }
  
  // 检查文件大小（最大10MB）
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过10MB')
    return
  }
  
  sending.value = true
  try {
    // 上传图片
    const formData = new FormData()
    formData.append('file', file)
    
    const uploadRes = await api.post('/upload/image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    const imageUrl = uploadRes.data?.url || uploadRes.data
    
    // 发送图片消息
    const res = await api.post('/social/messages', {
      receiver_id: targetUserId.value,
      content: imageUrl,
      message_type: 'image'
    })
    
    messages.value.push({
      id: res.data?.message_id || Date.now(),
      sender_id: currentUser.value?.id,
      content: imageUrl,
      message_type: 'image',
      is_mine: true,
      created_at: new Date().toISOString()
    })
    
    await nextTick()
    scrollToBottom()
    
    // 显示消费提示
    ElMessage.success(`发送成功，消费${messageCost.value}金币`)
  } catch (error) {
    console.error('发送图片失败', error)
    const errorMsg = error.response?.data?.detail || '发送图片失败，请重试'
    
    // 如果是金币不足，提示充值
    if (errorMsg.includes('金币余额不足')) {
      ElMessageBox.confirm(
        `发送私信需要${messageCost.value}金币，您的余额不足，是否前往充值？`,
        '金币不足',
        {
          confirmButtonText: '去充值',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(() => {
        router.push('/user/coins')
      }).catch(() => {})
    } else {
      ElMessage.error(errorMsg)
    }
  } finally {
    sending.value = false
    // 重置input
    if (imageInput.value) {
      imageInput.value.value = ''
    }
  }
}

// 预览图片
const previewImage = (url) => {
  previewImageUrl.value = url
}

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 格式化时间
const formatTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  
  const isToday = date.toDateString() === now.toDateString()
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  const isYesterday = date.toDateString() === yesterday.toDateString()
  
  const timeStr = date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  
  if (isToday) {
    return timeStr
  } else if (isYesterday) {
    return `昨天 ${timeStr}`
  } else {
    return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }) + ' ' + timeStr
  }
}

// 返回
const goBack = () => {
  router.back()
}

// 跳转到用户主页
const goToProfile = () => {
  router.push(`/user/member/${targetUserId.value}`)
}

// 标记该会话私信为已读
const markPrivateMessagesAsRead = async () => {
  try {
    await api.post(`/notifications/mark-read?notification_type=private&target_user_id=${targetUserId.value}`)
  } catch (error) {
    console.log('标记私信已读失败:', error)
  }
}

// 初始化
onMounted(async () => {
  if (!userStore.token) {
    ElMessage.warning('请先登录')
    router.push('/user/login')
    return
  }
  
  await fetchMessageCost()
  await fetchTargetUser()
  await fetchMessages()
  
  // 进入聊天页面后标记私信为已读
  markPrivateMessagesAsRead()
})

// 监听路由变化
watch(targetUserId, async (newId) => {
  if (newId) {
    await fetchTargetUser()
    await fetchMessages()
  }
})
</script>

<style lang="scss" scoped>
.chat-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  display: flex;
  flex-direction: column;
  padding-bottom: env(safe-area-inset-bottom);
}

// 顶部导航
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  padding-top: calc(12px + env(safe-area-inset-top));
  background: #0f0f1a;
  position: sticky;
  top: 0;
  z-index: 100;
  
  .back-btn {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    cursor: pointer;
    
    &:active {
      opacity: 0.7;
    }
  }
  
  .user-name {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    font-size: 17px;
    font-weight: 600;
    color: #fff;
    
    .header-vip-badge {
      height: 18px;
      width: auto;
      object-fit: contain;
    }
  }
  
  .user-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    overflow: hidden;
    cursor: pointer;
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }
}

// 消息列表区域
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  
  .messages-loading {
    display: flex;
    justify-content: center;
    padding: 40px;
    
    .loading-spinner {
      width: 32px;
      height: 32px;
      border: 3px solid rgba(255,255,255,0.1);
      border-top-color: #667eea;
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }
  }
  
  .empty-messages {
    text-align: center;
    padding: 60px 20px;
    color: rgba(255,255,255,0.5);
    font-size: 14px;
  }
}

// 消息项
.message-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 16px;
  
  &.is-mine {
    flex-direction: row-reverse;
    
    .message-content {
      align-items: flex-end;
    }
    
    .message-bubble {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: #fff;
    }
  }
  
  .message-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    overflow: hidden;
    flex-shrink: 0;
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }
  
  .message-content {
    display: flex;
    flex-direction: column;
    max-width: 70%;
    gap: 4px;
  }
  
  .message-nickname {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 0 4px;
    margin-bottom: 2px;
    
    .nickname-text {
      font-size: 12px;
      font-weight: 600;
      background: linear-gradient(90deg, #ffd700 0%, #ffb347 50%, #ffd700 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    
    .vip-badge {
      height: 16px;
      width: auto;
      max-width: 50px;
      object-fit: contain;
      filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3));
    }
    
    &.is-mine {
      justify-content: flex-end;
    }
  }
  
  .message-bubble {
    padding: 6px 14px;
    background: rgba(255,255,255,0.1);
    border-radius: 16px;
    color: #fff;
    font-size: 15px;
    line-height: 1.5;
    word-break: break-word;
  }
  
  .message-image {
    max-width: 200px;
    border-radius: 12px;
    overflow: hidden;
    
    img {
      width: 100%;
      display: block;
      cursor: pointer;
    }
  }
  
  .message-time {
    font-size: 11px;
    color: rgba(255,255,255,0.4);
    padding: 0 4px;
  }
}

// 底部输入区域
.chat-input-area {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  padding-bottom: calc(12px + env(safe-area-inset-bottom));
  background: #1e1e32;
  
  .input-wrapper {
    flex: 1;
    
    input {
      width: 100%;
      height: 44px;
      padding: 0 16px;
      background: rgba(255,255,255,0.08);
      border: none;
      border-radius: 22px;
      color: #fff;
      font-size: 15px;
      outline: none;
      
      &::placeholder {
        color: rgba(255,255,255,0.4);
      }
      
      &:focus {
        background: rgba(255,255,255,0.12);
      }
      
      &:disabled {
        opacity: 0.6;
      }
    }
  }
  
  .action-btn {
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    
    &:active {
      opacity: 0.7;
    }
    
    &.disabled {
      opacity: 0.4;
      pointer-events: none;
    }
    
    .action-icon {
      width: 28px;
      height: 28px;
      object-fit: contain;
    }
  }
}

// 图片选择弹窗
.image-picker-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 1000;
  
  .picker-content {
    width: 100%;
    max-width: 500px;
    background: #1e1e32;
    border-radius: 16px 16px 0 0;
    padding: 20px;
    padding-bottom: calc(20px + env(safe-area-inset-bottom));
    
    .picker-option {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 16px;
      color: #fff;
      font-size: 14px;
      cursor: pointer;
      border-radius: 12px;
      transition: background 0.2s;
      
      &:hover {
        background: rgba(255,255,255,0.1);
      }
      
      &:active {
        background: rgba(255,255,255,0.15);
      }
      
      svg {
        color: #667eea;
      }
    }
    
    .picker-cancel {
      margin-top: 12px;
      padding: 16px;
      text-align: center;
      color: rgba(255,255,255,0.6);
      font-size: 16px;
      cursor: pointer;
      border-top: 1px solid rgba(255,255,255,0.1);
      
      &:active {
        background: rgba(255,255,255,0.05);
      }
    }
  }
}

// 图片预览弹窗
.image-preview-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1001;
  cursor: pointer;
  
  img {
    max-width: 95%;
    max-height: 90%;
    object-fit: contain;
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
