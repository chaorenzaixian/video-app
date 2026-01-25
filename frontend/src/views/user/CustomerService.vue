<template>
  <div class="service-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </div>
      <h1 class="page-title">在线客服</h1>
      <div class="header-right">
        <span v-if="connectionStatus === 'connected'" class="status-dot online"></span>
        <span v-else class="status-dot offline"></span>
      </div>
    </header>

    <!-- 聊天区域 -->
    <div class="chat-area" ref="chatAreaRef" @scroll="handleScroll">
      <!-- 加载历史消息 -->
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <span>加载中...</span>
      </div>

      <!-- 消息列表 -->
      <template v-for="(msg, index) in messages" :key="msg.id || index">
        <!-- 系统消息 -->
        <div v-if="msg.message_type === 'system'" class="system-message">
          <span>{{ msg.content }}</span>
        </div>
        
        <!-- 客服消息 -->
        <div v-else-if="!msg.is_from_user" class="message-bubble service-message">
          <div class="avatar-wrapper">
            <img v-if="agentInfo?.avatar" :src="agentInfo.avatar" class="agent-avatar" />
            <div v-else class="agent-avatar default">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 1c-4.97 0-9 4.03-9 9v7c0 1.66 1.34 3 3 3h3v-8H5v-2c0-3.87 3.13-7 7-7s7 3.13 7 7v2h-4v8h3c1.66 0 3-1.34 3-3v-7c0-4.97-4.03-9-9-9z"/>
              </svg>
            </div>
          </div>
          <div class="message-body">
            <div class="sender-name" v-if="agentInfo?.name">{{ agentInfo.name }}</div>
            <div class="message-content">
              <!-- 图片消息 -->
              <img v-if="msg.message_type === 'image'" :src="msg.content" class="message-image" @click="previewImage(msg.content)" />
              <!-- 文本消息 -->
              <p v-else v-html="formatMessage(msg.content)"></p>
            </div>
            <div class="message-meta">
              <span class="message-time">{{ formatTime(msg.created_at) }}</span>
            </div>
          </div>
        </div>
        
        <!-- 用户消息 -->
        <div v-else class="message-bubble user-message">
          <div class="message-body">
            <div class="message-content">
              <!-- 图片消息 -->
              <img v-if="msg.message_type === 'image'" :src="msg.content" class="message-image" @click="previewImage(msg.content)" />
              <!-- 文本消息 -->
              <span v-else>{{ msg.content }}</span>
            </div>
            <div class="message-meta">
              <span class="message-time">{{ formatTime(msg.created_at) }}</span>
              <span class="read-status" :class="{ read: msg.is_read }">
                {{ msg.is_read ? '已读' : '未读' }}
              </span>
            </div>
          </div>
        </div>
      </template>

      <!-- 问题分类（首次显示） -->
      <div v-if="showQuickPanel" class="quick-panel">
        <div class="category-tabs">
          <div 
            v-for="(cat, index) in categories" 
            :key="index"
            :class="['category-tab', { active: activeCategory === index }]"
            @click="activeCategory = index"
          >
            {{ cat.name }}
          </div>
        </div>

        <!-- 快捷问题列表 -->
        <div class="quick-questions">
          <div 
            v-for="(question, index) in currentQuestions" 
            :key="index"
            class="question-item"
            @click="askQuestion(question)"
          >
            {{ index + 1 }}.{{ question.title }}
          </div>
          
          <div class="expand-more" @click="showMoreQuestions = !showMoreQuestions" v-if="hasMoreQuestions">
            <svg viewBox="0 0 24 24" fill="currentColor" :class="{ rotated: showMoreQuestions }">
              <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/>
            </svg>
            <span>{{ showMoreQuestions ? '收起问题' : '展开更多问题' }}</span>
          </div>
        </div>
      </div>

      <!-- 正在输入提示 -->
      <div v-if="agentTyping" class="typing-indicator">
        <span>客服正在输入</span>
        <div class="typing-dots">
          <span></span><span></span><span></span>
            </div>
          </div>
        </div>

    <!-- 图片预览 -->
    <div v-if="previewImageUrl" class="image-preview-modal" @click="previewImageUrl = null">
      <img :src="previewImageUrl" />
      </div>

    <!-- 底部输入框 -->
    <div class="input-area">
      <!-- 冷却提示 -->
      <div v-if="isCooldown" class="cooldown-tip">
        发送太频繁，请等待 {{ cooldownSeconds }} 秒
      </div>
      <template v-else>
        <div class="input-icon" @click="triggerImageUpload">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/>
          </svg>
          <input 
            type="file" 
            ref="imageInputRef" 
            accept="image/*" 
            @change="handleImageUpload" 
            style="display: none"
          />
        </div>
        <input 
          type="text" 
          v-model="inputMessage" 
          placeholder="请在此输入留言"
          @keyup.enter="sendMessage"
          @focus="handleInputFocus"
        />
        <div class="send-btn" @click="sendMessage" :class="{ disabled: !inputMessage.trim() }">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
          </svg>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import api from '@/utils/api'

const userStore = useUserStore()
const chatAreaRef = ref(null)
const imageInputRef = ref(null)

// 状态
const loading = ref(true)
const sessionId = ref(null)
const messages = ref([])
const inputMessage = ref('')
const connectionStatus = ref('disconnected')
const agentTyping = ref(false)
const showQuickPanel = ref(true)
const previewImageUrl = ref(null)
const agentInfo = ref(null)

// 防刷屏
const lastMessageTime = ref(0)
const messageCooldown = 3000 // 3秒冷却时间
const messageCount = ref(0)
const maxMessagesPerMinute = 10 // 每分钟最多10条
const isCooldown = ref(false)
const cooldownSeconds = ref(0)
let cooldownTimer = null

// WebSocket
let ws = null
let reconnectTimer = null
let heartbeatTimer = null

// 问题分类
const categories = ref([
  { name: '账号与权益问题' },
  { name: '播放问题' },
  { name: '支付与订单相关' }
])

const activeCategory = ref(0)
const showMoreQuestions = ref(false)

// 各分类的问题
const questionsByCategory = ref([
  [
    { title: '账号找回', answer: '如需找回账号，请提供您的注册手机号或邮箱，我们会尽快为您处理。' },
    { title: '充值了会员还是无法观看', answer: '请先尝试退出登录后重新登录，如仍无法观看，请提供您的订单号，我们会为您核实。' },
    { title: '绑定不了手机号', answer: '请确保手机号未被其他账号绑定，如已绑定其他账号，需先解绑后才能绑定新账号。' },
    { title: '如何修改密码', answer: '进入个人中心 -> 安全设置 -> 修改密码，按提示操作即可。' },
    { title: '账号被封禁怎么办', answer: '请联系客服说明情况，我们会根据具体违规行为进行处理。' }
  ],
  [
    { title: '视频加载缓慢', answer: '建议检查网络连接，或尝试切换清晰度，降低画质可提升加载速度。' },
    { title: '视频无法播放', answer: '请尝试刷新页面或更换浏览器，如仍有问题请联系客服。' },
    { title: '画面卡顿/黑屏', answer: '建议清除浏览器缓存，或尝试使用其他浏览器观看。' },
    { title: '声音画面不同步', answer: '请尝试刷新页面，如问题持续存在，可能是视频源问题，请反馈给客服。' }
  ],
  [
    { title: '支付成功但未到账', answer: '支付成功后一般即时到账，如未到账请提供订单号，我们会为您核实。' },
    { title: '如何申请退款', answer: '请联系客服说明退款原因，提供订单号，我们会在24小时内处理。' },
    { title: '支付方式有哪些', answer: '目前支持支付宝、微信支付等主流支付方式。推荐使用支付宝，成功率更高。' },
    { title: '会员套餐介绍', answer: '我们提供月卡、季卡、年卡和永久卡，不同套餐享受不同优惠，详情请查看VIP中心。' }
  ]
])

// 当前分类的问题
const currentQuestions = computed(() => {
  const questions = questionsByCategory.value[activeCategory.value] || []
  return showMoreQuestions.value ? questions : questions.slice(0, 3)
})

// 是否有更多问题
const hasMoreQuestions = computed(() => {
  const questions = questionsByCategory.value[activeCategory.value] || []
  return questions.length > 3
})

// 初始化
onMounted(async () => {
  await initSession()
  connectWebSocket()
})

onUnmounted(() => {
  disconnectWebSocket()
})

// 创建或获取会话
const initSession = async () => {
  loading.value = true
  try {
    const res = await api.post('/chat/sessions')
    sessionId.value = res.data?.id || res.id
    
    // 获取会话信息（包含客服头像）
    await loadSessionInfo()
    
    // 获取历史消息
    await loadMessages()
  } catch (error) {
    console.error('初始化会话失败:', error)
    messages.value = [{
      id: 'welcome',
      is_from_user: false,
      message_type: 'system',
      content: '亲亲，请问您需要什么协助呢？\n❣️ 客服小妹推荐您985.fun里面都是精选过的app，新人注册还有优惠，相当划算！❣️\n❣️ 提醒您：由于近期微信支付通道不稳定，推荐使用支付宝支付，成功率高且快速哟 ❣️',
      created_at: new Date().toISOString()
    }]
  } finally {
    loading.value = false
  }
}

// 获取会话信息
const loadSessionInfo = async () => {
  if (!sessionId.value) return
  
  try {
    const res = await api.get(`/chat/sessions/${sessionId.value}/info`)
    const data = res.data || res
    if (data.agent) {
      agentInfo.value = data.agent
    }
  } catch (error) {
    console.error('获取会话信息失败:', error)
  }
}

// 加载历史消息
const loadMessages = async () => {
  if (!sessionId.value) return
  
  try {
    const res = await api.get(`/chat/sessions/${sessionId.value}/messages`)
    let loadedMessages = res.data || res || []
    
    // 如果没有任何消息或者没有客服消息，添加欢迎消息
    const hasAgentMessage = loadedMessages.some(msg => !msg.is_from_user)
    if (!hasAgentMessage) {
      const welcomeMsg = {
        id: 'welcome-auto',
        is_from_user: false,
        message_type: 'text',
        content: '人工客服已上线，您遇到什么问题请详细、清楚描述给客服喔\n请说明问题勿重复发话刷频，避免系统自动关闭，\n并且耐心等候客服给您回覆\n谢谢您。',
        created_at: new Date().toISOString()
      }
      loadedMessages = [welcomeMsg, ...loadedMessages]
    }
    
    messages.value = loadedMessages
    
    if (messages.value.length > 1) {
      showQuickPanel.value = false
    }
    
    await nextTick()
    scrollToBottom()
    
    // 标记消息已读
    markMessagesRead()
  } catch (error) {
    console.error('加载消息失败:', error)
  }
}

// 标记消息已读
const markMessagesRead = async () => {
  if (!sessionId.value) return
  
  try {
    await api.post(`/chat/sessions/${sessionId.value}/read`)
  } catch (error) {
    // 忽略错误
  }
}

// 处理滚动
const handleScroll = () => {
  // 滚动时标记消息已读
  markMessagesRead()
}

// WebSocket连接
const connectWebSocket = () => {
  if (!userStore.user?.id) return
  
  const token = userStore.token || localStorage.getItem('token') || ''
  const wsUrl = `ws://${window.location.hostname}:8000/api/v1/chat/ws/user/${userStore.user.id}?token=${token}`
  
  try {
    ws = new WebSocket(wsUrl)
    
    ws.onopen = () => {
      connectionStatus.value = 'connected'
      console.log('WebSocket已连接')
      startHeartbeat()
    }
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        handleWebSocketMessage(data)
      } catch (e) {
        console.error('解析消息失败:', e)
      }
    }
    
    ws.onclose = () => {
      connectionStatus.value = 'disconnected'
      console.log('WebSocket已断开')
      stopHeartbeat()
      scheduleReconnect()
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket错误:', error)
      connectionStatus.value = 'error'
    }
  } catch (error) {
    console.error('WebSocket连接失败:', error)
  }
}

const disconnectWebSocket = () => {
  if (ws) {
    ws.close()
    ws = null
  }
  stopHeartbeat()
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
}

const scheduleReconnect = () => {
  if (reconnectTimer) return
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null
    connectWebSocket()
  }, 3000)
}

const startHeartbeat = () => {
  heartbeatTimer = setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping' }))
    }
  }, 30000)
}

const stopHeartbeat = () => {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
}

// 处理WebSocket消息
const handleWebSocketMessage = (data) => {
  switch (data.type) {
    case 'pong':
      break
    
    case 'new_message':
      messages.value.push({
        id: data.message.id,
        session_id: data.session_id,
        sender_id: data.message.sender_id,
        is_from_user: data.message.is_from_user,
        message_type: data.message.message_type || 'text',
        content: data.message.content,
        is_read: false,
        created_at: data.message.created_at
      })
      scrollToBottom()
      showQuickPanel.value = false
      
      // 标记为已读
      if (!data.message.is_from_user) {
        markMessagesRead()
      }
      break
    
    case 'agent_joined':
      messages.value.push({
        id: `system-${Date.now()}`,
        message_type: 'system',
        content: `客服 ${data.agent_name} 已接入会话`,
        created_at: new Date().toISOString()
      })
      // 更新客服信息
      agentInfo.value = {
        name: data.agent_name,
        avatar: data.agent_avatar
      }
      scrollToBottom()
      break
    
    case 'session_closed':
      messages.value.push({
        id: `system-${Date.now()}`,
        message_type: 'system',
        content: '会话已结束，感谢您的咨询！',
        created_at: new Date().toISOString()
      })
      scrollToBottom()
      break
    
    case 'messages_read':
      // 更新消息已读状态
      if (data.reader === 'agent') {
        messages.value.forEach(m => {
          if (m.is_from_user) {
            m.is_read = true
          }
        })
      }
      break
    
    case 'typing':
      agentTyping.value = true
      setTimeout(() => { agentTyping.value = false }, 3000)
      break
    
    case 'message_sent':
      break
  }
}

// 发送消息
const sendMessage = async () => {
  const content = inputMessage.value.trim()
  if (!content) return
  
  // 防刷屏检查
  const now = Date.now()
  
  // 检查冷却时间
  if (now - lastMessageTime.value < messageCooldown) {
    const remainingSeconds = Math.ceil((messageCooldown - (now - lastMessageTime.value)) / 1000)
    ElMessage.warning(`发送太快了，请${remainingSeconds}秒后再试`)
    return
  }
  
  // 检查每分钟消息数量
  if (messageCount.value >= maxMessagesPerMinute) {
    ElMessage.warning('发送消息过于频繁，请稍后再试')
    startCooldown(30) // 30秒冷却
    return
  }
  
  // 更新发送时间和计数
  lastMessageTime.value = now
  messageCount.value++
  
  // 1分钟后重置计数
  setTimeout(() => {
    if (messageCount.value > 0) {
      messageCount.value--
    }
  }, 60000)
  
  const tempMsg = {
    id: `temp-${Date.now()}`,
    is_from_user: true,
    message_type: 'text',
    content: content,
    is_read: false,
    created_at: new Date().toISOString()
  }
  messages.value.push(tempMsg)
  inputMessage.value = ''
  showQuickPanel.value = false
  
  await nextTick()
  scrollToBottom()
  
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'message',
      session_id: sessionId.value,
      content: content
    }))
  } else {
    try {
      await api.post('/chat/messages', {
        session_id: sessionId.value,
        content: content
      })
    } catch (error) {
      console.error('发送消息失败:', error)
    }
  }
}

// 开始冷却计时
const startCooldown = (seconds) => {
  isCooldown.value = true
  cooldownSeconds.value = seconds
  
  if (cooldownTimer) clearInterval(cooldownTimer)
  
  cooldownTimer = setInterval(() => {
    cooldownSeconds.value--
    if (cooldownSeconds.value <= 0) {
      isCooldown.value = false
      messageCount.value = 0
      clearInterval(cooldownTimer)
    }
  }, 1000)
}

// 图片上传
const triggerImageUpload = () => {
  imageInputRef.value?.click()
}

const handleImageUpload = async (event) => {
  const file = event.target.files?.[0]
  if (!file) return
  
  // 验证文件类型
  if (!file.type.startsWith('image/')) {
    alert('请选择图片文件')
    return
  }
  
  // 验证文件大小 (5MB)
  if (file.size > 5 * 1024 * 1024) {
    alert('图片大小不能超过5MB')
    return
  }
  
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const res = await api.post('/chat/upload-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    const imageUrl = res.data?.url || res.url
    
    // 发送图片消息
    const tempMsg = {
      id: `temp-${Date.now()}`,
      is_from_user: true,
      message_type: 'image',
      content: imageUrl,
      is_read: false,
      created_at: new Date().toISOString()
    }
    messages.value.push(tempMsg)
    showQuickPanel.value = false
    
    await nextTick()
    scrollToBottom()
    
    // 通过API发送
    await api.post('/chat/messages', {
      session_id: sessionId.value,
      content: imageUrl,
      message_type: 'image'
    })
  } catch (error) {
    console.error('上传图片失败:', error)
    alert('上传图片失败')
  }
  
  // 清空input
  event.target.value = ''
}

// 预览图片
const previewImage = (url) => {
  previewImageUrl.value = url
}

// 点击快捷问题
const askQuestion = async (question) => {
  inputMessage.value = question.title
  await sendMessage()
  
  setTimeout(() => {
    const hasAgentReply = messages.value.some(m => 
      !m.is_from_user && m.message_type !== 'system' && 
      new Date(m.created_at) > new Date(Date.now() - 5000)
    )
    
    if (!hasAgentReply) {
      messages.value.push({
        id: `auto-${Date.now()}`,
        is_from_user: false,
        message_type: 'text',
        content: question.answer,
        is_read: true,
        created_at: new Date().toISOString()
      })
      scrollToBottom()
    }
  }, 1000)
}

// 输入框聚焦
const handleInputFocus = () => {
  setTimeout(() => scrollToBottom(), 300)
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (chatAreaRef.value) {
      chatAreaRef.value.scrollTop = chatAreaRef.value.scrollHeight
    }
  })
}

// 格式化时间
const formatTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${month}-${day} ${hours}:${minutes}`
}

// 格式化消息
const formatMessage = (content) => {
  if (!content) return ''
  return content
    .replace(/\n/g, '<br>')
    .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" class="link">$1</a>')
    .replace(/([a-zA-Z0-9]+\.fun)/g, '<span class="highlight">$1</span>')
}

// 监听消息变化
watch(messages, () => {
  scrollToBottom()
}, { deep: true })
</script>

<style lang="scss" scoped>
.service-page {
  min-height: 100vh;
  background: #0a0a0a;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  padding-top: calc(12px + env(safe-area-inset-top, 0px));
  background: transparent;
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
      color: #fff;
    }
  }
  
  .page-title {
    font-size: 16px;
    font-weight: 600;
    color: #fff;
    margin: 0;
  }
  
  .header-right {
    width: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      
      &.online {
        background: #22c55e;
        box-shadow: 0 0 6px #22c55e;
      }
      
      &.offline {
        background: #6b7280;
      }
    }
  }
}

.chat-area {
  flex: 1;
  padding: 16px;
  padding-bottom: 80px;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.loading-state {
    display: flex;
  flex-direction: column;
    align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: rgba(255, 255, 255, 0.5);
  gap: 12px;

  .loading-spinner {
    width: 28px;
    height: 28px;
    border: 3px solid rgba(255, 255, 255, 0.1);
    border-top-color: #667eea;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.system-message {
  text-align: center;
  padding: 8px 0;
  
  span {
    display: inline-block;
    padding: 6px 14px;
      background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.5);
  }
    }
    
.message-bubble {
      display: flex;
  gap: 10px;
  margin-bottom: 16px;
  
  &.service-message {
    .avatar-wrapper {
      flex-shrink: 0;
      
      .agent-avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        object-fit: cover;
        
        &.default {
          background: linear-gradient(135deg, #667eea, #764ba2);
          display: flex;
          align-items: center;
          justify-content: center;
          
          svg {
            width: 20px;
            height: 20px;
            color: #fff;
          }
        }
      }
    }
    
    .message-body {
      max-width: calc(100% - 50px);
      
      .sender-name {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.5);
        margin-bottom: 4px;
      }
      
      .message-content {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 4px 16px 16px 16px;
        padding: 12px 14px;
        
        p {
          margin: 0;
          font-size: 14px;
          color: rgba(255, 255, 255, 0.9);
          line-height: 1.6;
          word-break: break-word;
        }
        
        .message-image {
          max-width: 200px;
          max-height: 200px;
          border-radius: 8px;
          cursor: pointer;
        }
        
        :deep(.highlight) {
          color: #00b4db;
        }
        
        :deep(.link) {
          color: #00b4db;
          text-decoration: underline;
        }
      }
    }
  }
  
  &.user-message {
    flex-direction: row-reverse;
    
    .message-body {
      max-width: 75%;
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      
      .message-content {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 16px 4px 16px 16px;
        padding: 12px 14px;
        font-size: 14px;
        color: #fff;
        line-height: 1.5;
        word-break: break-word;
        
        .message-image {
          max-width: 200px;
          max-height: 200px;
          border-radius: 8px;
          cursor: pointer;
        }
      }
    }
  }
  
  .message-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 4px;
    
    .message-time {
      font-size: 11px;
      color: rgba(255, 255, 255, 0.4);
    }
    
    .read-status {
      font-size: 10px;
        color: rgba(255, 255, 255, 0.3);
      
      &.read {
        color: #22c55e;
      }
    }
  }
}

.quick-panel {
  margin-top: 16px;
}

.category-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
  
  .category-tab {
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.7);
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.1);
    cursor: pointer;
    transition: all 0.2s;
    
    &:hover {
      background: rgba(255, 255, 255, 0.12);
    }
    
    &.active {
      background: transparent;
      border-color: #00b4db;
      color: #00b4db;
    }
  }
}

.quick-questions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  
  .question-item {
    padding: 12px 16px;
    background: rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.85);
    cursor: pointer;
    transition: all 0.2s;
    
    &:hover {
      background: rgba(255, 255, 255, 0.1);
    }
    
    &:active {
      transform: scale(0.98);
    }
  }
  
  .expand-more {
      display: flex;
      align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 10px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.5);
    cursor: pointer;
    
    svg {
      width: 18px;
      height: 18px;
      transition: transform 0.3s;
      
      &.rotated {
          transform: rotate(180deg);
      }
    }
    
    &:hover {
      color: rgba(255, 255, 255, 0.7);
    }
  }
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  
  .typing-dots {
    display: flex;
    gap: 3px;
    
    span {
      width: 6px;
      height: 6px;
    border-radius: 50%;
      background: rgba(255, 255, 255, 0.5);
      animation: typing 1.4s infinite ease-in-out;
      
      &:nth-child(1) { animation-delay: 0s; }
      &:nth-child(2) { animation-delay: 0.2s; }
      &:nth-child(3) { animation-delay: 0.4s; }
    }
  }
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-4px); }
}

.image-preview-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  cursor: pointer;
  
  img {
    max-width: 90%;
    max-height: 90%;
    object-fit: contain;
  }
}

.input-area {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  padding-bottom: calc(12px + env(safe-area-inset-bottom, 0px));
  background: #0a0a0a;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  
  .cooldown-tip {
    flex: 1;
    text-align: center;
    color: #f56c6c;
    font-size: 14px;
    padding: 10px 0;
  }
  
  .input-icon {
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    cursor: pointer;
    
    svg {
      width: 24px;
      height: 24px;
      color: rgba(255, 255, 255, 0.4);
    }
    
    &:hover svg {
      color: rgba(255, 255, 255, 0.6);
    }
  }
  
  input {
    flex: 1;
    height: 40px;
    background: rgba(255, 255, 255, 0.06);
    border: none;
    border-radius: 20px;
    padding: 0 16px;
    font-size: 14px;
    color: #fff;
    outline: none;
    
    &::placeholder {
      color: rgba(255, 255, 255, 0.3);
    }
  }
  
  .send-btn {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    cursor: pointer;
    
    svg {
      width: 24px;
      height: 24px;
      color: #00b4db;
      transition: color 0.2s;
    }
    
    &:hover svg {
      color: #00d4ff;
    }
    
    &.disabled svg {
      color: rgba(255, 255, 255, 0.2);
    }
  }
}

// 响应式断点
@media (min-width: 768px) {
  .service-page {
    max-width: 768px;
    margin: 0 auto;
  }
  
  .page-header {
    max-width: 768px;
    left: 50%;
    transform: translateX(-50%);
  }
  
  .input-area {
    max-width: 768px;
    left: 50%;
    transform: translateX(-50%);
  }
  
  .message-bubble {
    &.service-message .message-body .message-content .message-image,
    &.user-message .message-body .message-content .message-image {
      max-width: 280px;
      max-height: 280px;
    }
  }
  
  .quick-questions .question-item {
    padding: 14px 18px;
  }
}

@media (min-width: 1024px) {
  .service-page {
    max-width: 800px;
  }
  
  .page-header {
    max-width: 800px;
  }
  
  .input-area {
    max-width: 800px;
  }
  
  .chat-area {
    padding: 20px 24px;
    padding-bottom: 90px;
  }
  
  .message-bubble {
    &.service-message .message-body .message-content .message-image,
    &.user-message .message-body .message-content .message-image {
      max-width: 320px;
      max-height: 320px;
    }
  }
}

// 触摸设备优化
@media (hover: hover) {
  .quick-questions .question-item:hover {
    background: rgba(255, 255, 255, 0.12);
    transform: translateX(4px);
  }
  
  .category-tabs .category-tab:hover {
    background: rgba(255, 255, 255, 0.15);
  }
}

@media (hover: none) {
  .quick-questions .question-item:hover,
  .category-tabs .category-tab:hover,
  .input-icon:hover svg,
  .send-btn:hover svg {
    // 移除触摸设备上的 hover 效果
  }
}
</style>
