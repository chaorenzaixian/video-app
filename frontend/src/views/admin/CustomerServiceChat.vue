<template>
  <div class="chat-manage">
    <div class="chat-container">
      <!-- 左侧会话列表 -->
      <div class="session-list">
        <div class="list-header">
          <h3>客服会话</h3>
          <div class="status-tabs">
            <span :class="{ active: statusFilter === '' }" @click="statusFilter = ''">全部</span>
            <span :class="{ active: statusFilter === 'waiting' }" @click="statusFilter = 'waiting'">
              等待中
              <em v-if="waitingCount > 0">{{ waitingCount }}</em>
            </span>
            <span :class="{ active: statusFilter === 'active' }" @click="statusFilter = 'active'">进行中</span>
          </div>
        </div>
        
        <div class="session-items">
          <div 
            v-for="session in filteredSessions" 
            :key="session.id"
            :class="['session-item', { active: currentSession?.id === session.id }]"
            @click="selectSession(session)"
          >
            <div class="user-avatar" :class="{ 'is-vip': session.is_vip }">
              <img v-if="session.avatar" :src="session.avatar" />
              <span v-else>{{ (session.nickname || session.username || '用户')[0] }}</span>
              <img v-if="session.is_vip && session.vip_level" class="vip-badge" :src="getVipIcon(session.vip_level)" />
            </div>
            <div class="session-info">
              <div class="session-top">
                <span class="username">{{ session.nickname || session.username || `用户${session.user_id}` }}</span>
                <img v-if="session.is_vip && session.vip_level" class="vip-icon" :src="getVipIcon(session.vip_level)" />
                <span class="time">{{ formatTime(session.updated_at) }}</span>
              </div>
              <div class="session-bottom">
                <span class="title">{{ session.title || '新会话' }}</span>
                <span v-if="session.unread_count > 0" class="unread">{{ session.unread_count }}</span>
              </div>
            </div>
            <div class="session-status">
              <span :class="['status-tag', session.status]">
                {{ statusText[session.status] || session.status }}
              </span>
            </div>
          </div>
          
          <div v-if="filteredSessions.length === 0" class="empty-list">
            暂无会话
          </div>
        </div>
      </div>

      <!-- 右侧聊天区域 -->
      <div class="chat-area">
        <template v-if="currentSession">
          <!-- 聊天头部 -->
          <div class="chat-header">
            <div class="user-info">
              <div class="user-avatar-header" :class="{ 'is-vip': currentSession.is_vip }">
                <img v-if="currentSession.avatar" :src="currentSession.avatar" />
                <span v-else>{{ (currentSession.nickname || currentSession.username || '用户')[0] }}</span>
              </div>
              <div class="user-details">
                <div class="name-row">
                  <span class="name">{{ currentSession.nickname || currentSession.username || `用户${currentSession.user_id}` }}</span>
                  <img v-if="currentSession.is_vip && currentSession.vip_level" class="vip-icon-header" :src="getVipIcon(currentSession.vip_level)" />
                </div>
                <span class="status">{{ statusText[currentSession.status] }}</span>
              </div>
            </div>
            <div class="header-actions">
              <el-button 
                v-if="currentSession.status === 'waiting'" 
                type="primary" 
                size="small"
                @click="claimSession"
              >
                接入会话
              </el-button>
              <el-button 
                v-if="currentSession.status === 'active'" 
                type="danger" 
                size="small"
                @click="closeSession"
              >
                结束会话
              </el-button>
            </div>
          </div>

          <!-- 消息列表 -->
          <div class="message-list" ref="messageListRef">
            <div 
              v-for="msg in currentMessages" 
              :key="msg.id"
              :class="['message-item', { 'from-user': msg.is_from_user, 'from-agent': !msg.is_from_user }]"
            >
              <div v-if="msg.message_type === 'system'" class="system-msg">
                {{ msg.content }}
              </div>
              <template v-else>
                <div class="message-avatar" :class="{ 'user-avatar': msg.is_from_user }">
                  <img v-if="msg.is_from_user && currentSession?.user_avatar" :src="currentSession.user_avatar" />
                  <img v-else-if="!msg.is_from_user && userStore.user?.avatar" :src="userStore.user.avatar" />
                  <span v-else>{{ msg.is_from_user ? '用' : '客' }}</span>
                </div>
                <div class="message-content">
                  <!-- 图片消息 -->
                  <div v-if="msg.message_type === 'image'" class="message-bubble image-bubble">
                    <img :src="msg.content" class="msg-image" @click="previewImage(msg.content)" />
                  </div>
                  <!-- 文本消息 -->
                  <div v-else class="message-bubble">{{ msg.content }}</div>
                  <div class="message-meta">
                    <span class="message-time">{{ formatDateTime(msg.created_at) }}</span>
                    <span v-if="!msg.is_from_user" class="read-status" :class="{ read: msg.is_read }">
                      {{ msg.is_read ? '已读' : '未读' }}
                    </span>
                  </div>
                </div>
              </template>
            </div>
          </div>

          <!-- 图片预览 -->
          <div v-if="previewImageUrl" class="image-preview" @click="previewImageUrl = null">
            <img :src="previewImageUrl" />
          </div>

          <!-- 输入区域 -->
          <div class="input-area" v-if="currentSession.status === 'active'">
            <div class="quick-replies" v-if="showQuickReplies">
              <div 
                v-for="reply in quickReplies" 
                :key="reply.id"
                class="quick-reply-item"
                @click="useQuickReply(reply)"
              >
                {{ reply.title }}
              </div>
            </div>
            <div class="input-box">
              <el-button size="small" @click="showQuickReplies = !showQuickReplies">
                快捷回复
              </el-button>
              <el-input
                v-model="inputMessage"
                placeholder="输入消息..."
                @keyup.enter="sendMessage"
              />
              <el-button type="primary" @click="sendMessage" :disabled="!inputMessage.trim()">
                发送
              </el-button>
            </div>
          </div>
        </template>
        
        <div v-else class="no-session">
          <el-empty description="请选择一个会话" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const messageListRef = ref(null)

// VIP等级图标映射
const VIP_LEVEL_ICONS = {
  1: '/images/backgrounds/vip_gold.webp',      // 普通VIP
  2: '/images/backgrounds/vip_1.webp',         // VIP1
  3: '/images/backgrounds/vip_2.webp',         // VIP2
  4: '/images/backgrounds/vip_3.webp',         // VIP3
  5: '/images/backgrounds/super_vip_red.webp', // 黄金至尊
  6: '/images/backgrounds/super_vip_blue.webp' // 紫色限定至尊
}

// 获取VIP图标
const getVipIcon = (level) => {
  return VIP_LEVEL_ICONS[level] || ''
}

// 状态
const sessions = ref([])
const currentSession = ref(null)
const currentMessages = ref([])
const inputMessage = ref('')
const statusFilter = ref('')
const showQuickReplies = ref(false)
const quickReplies = ref([])
const previewImageUrl = ref(null)

// 预览图片
const previewImage = (url) => {
  previewImageUrl.value = url
}

// WebSocket
let ws = null
let heartbeatTimer = null

const statusText = {
  waiting: '等待接入',
  active: '进行中',
  closed: '已结束'
}

// 计算等待中的会话数
const waitingCount = computed(() => {
  return sessions.value.filter(s => s.status === 'waiting').length
})

// 过滤后的会话列表
const filteredSessions = computed(() => {
  if (!statusFilter.value) return sessions.value
  return sessions.value.filter(s => s.status === statusFilter.value)
})

// 初始化
onMounted(async () => {
  await loadSessions()
  await loadQuickReplies()
  connectWebSocket()
})

onUnmounted(() => {
  disconnectWebSocket()
})

// 加载会话列表
const loadSessions = async () => {
  try {
    const res = await api.get('/chat/admin/sessions')
    sessions.value = res.data || res || []
  } catch (error) {
    console.error('加载会话失败:', error)
  }
}

// 加载快捷回复
const loadQuickReplies = async () => {
  try {
    const res = await api.get('/chat/quick-replies')
    quickReplies.value = res.data || res || []
  } catch (error) {
    console.error('加载快捷回复失败:', error)
  }
}

// 选择会话
const selectSession = async (session) => {
  currentSession.value = session
  await loadMessages(session.id)
}

// 加载消息
const loadMessages = async (sessionId) => {
  try {
    const res = await api.get(`/chat/sessions/${sessionId}/messages`)
    currentMessages.value = res.data || res || []
    
    await nextTick()
    scrollToBottom()
    
    // 标记消息已读
    markMessagesRead(sessionId)
  } catch (error) {
    console.error('加载消息失败:', error)
  }
}

// 标记消息已读
const markMessagesRead = async (sessionId) => {
  if (!sessionId) return
  
  try {
    await api.post(`/chat/sessions/${sessionId}/read`)
    
    // 更新本地状态
    const session = sessions.value.find(s => s.id === sessionId)
    if (session) {
      session.unread_count = 0
    }
  } catch (error) {
    // 忽略错误
  }
}

// 接入会话
const claimSession = async () => {
  try {
    await api.post(`/chat/admin/sessions/${currentSession.value.id}/claim`)
    currentSession.value.status = 'active'
    currentSession.value.agent_id = userStore.user?.id
    ElMessage.success('已接入会话')
    await loadMessages(currentSession.value.id)
  } catch (error) {
    ElMessage.error('接入失败')
  }
}

// 结束会话
const closeSession = async () => {
  try {
    await ElMessageBox.confirm('确定要结束此会话吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.post(`/chat/admin/sessions/${currentSession.value.id}/close`)
    currentSession.value.status = 'closed'
    ElMessage.success('会话已结束')
    await loadMessages(currentSession.value.id)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

// 发送消息
const sendMessage = async () => {
  const content = inputMessage.value.trim()
  if (!content || !currentSession.value) return
  
  try {
    // 通过WebSocket发送
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'message',
        session_id: currentSession.value.id,
        content: content
      }))
      
      // 本地添加消息
      currentMessages.value.push({
        id: `temp-${Date.now()}`,
        session_id: currentSession.value.id,
        sender_id: userStore.user?.id,
        is_from_user: false,
        message_type: 'text',
        content: content,
        created_at: new Date().toISOString()
      })
    } else {
      // 通过API发送
      const res = await api.post('/chat/admin/messages', {
        session_id: currentSession.value.id,
        content: content
      })
      currentMessages.value.push(res.data || res)
    }
    
    inputMessage.value = ''
    await nextTick()
    scrollToBottom()
  } catch (error) {
    ElMessage.error('发送失败')
  }
}

// 使用快捷回复
const useQuickReply = (reply) => {
  inputMessage.value = reply.content
  showQuickReplies.value = false
}

// WebSocket连接
const connectWebSocket = () => {
  if (!userStore.user?.id) return
  
  const token = userStore.token || localStorage.getItem('token') || ''
  const wsUrl = `ws://${window.location.hostname}:8000/api/v1/chat/ws/agent/${userStore.user.id}?token=${token}`
  
  try {
    ws = new WebSocket(wsUrl)
    
    ws.onopen = () => {
      console.log('客服WebSocket已连接')
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
      console.log('客服WebSocket已断开')
      stopHeartbeat()
      // 3秒后重连
      setTimeout(connectWebSocket, 3000)
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket错误:', error)
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
    
    case 'new_session':
      // 新会话
      loadSessions()
      ElMessage.info(`新用户 ${data.nickname || data.username || '用户'} 发起咨询`)
      break
    
    case 'new_message':
      // 新消息
      if (currentSession.value?.id === data.session_id) {
        currentMessages.value.push({
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
        
        // 自动标记已读
        if (data.message.is_from_user) {
          markMessagesRead(data.session_id)
        }
      }
      
      // 更新会话列表
      const session = sessions.value.find(s => s.id === data.session_id)
      if (session) {
        session.updated_at = data.message.created_at
        session.unread_count = (session.unread_count || 0) + 1
        if (data.message.is_from_user && !session.title) {
          session.title = data.message.content.substring(0, 50)
        }
      } else {
        loadSessions()
      }
      break
    
    case 'messages_read':
      // 用户已读消息
      if (data.reader === 'user' && currentSession.value?.id === data.session_id) {
        currentMessages.value.forEach(m => {
          if (!m.is_from_user) {
            m.is_read = true
          }
        })
      }
      break
    
    case 'message_sent':
      break
  }
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

// 格式化时间
const formatTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  
  return `${date.getMonth() + 1}/${date.getDate()}`
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}-${date.getDate()} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

// 监听消息变化
watch(currentMessages, () => {
  scrollToBottom()
}, { deep: true })
</script>

<style lang="scss" scoped>
.chat-manage {
  height: calc(100vh - 120px);
  padding: 20px;
}

.chat-container {
  display: flex;
  height: 100%;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.session-list {
  width: 320px;
  border-right: 1px solid #eee;
  display: flex;
  flex-direction: column;
  
  .list-header {
    padding: 16px;
    border-bottom: 1px solid #eee;
    
    h3 {
      margin: 0 0 12px;
      font-size: 16px;
    }
    
    .status-tabs {
      display: flex;
      gap: 12px;
      
      span {
        font-size: 13px;
        color: #666;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 4px;
        position: relative;
        
        &:hover {
          background: #f5f5f5;
        }
        
        &.active {
          color: #409eff;
          background: #ecf5ff;
        }
        
        em {
          position: absolute;
          top: -4px;
          right: -8px;
          min-width: 16px;
          height: 16px;
          background: #f56c6c;
          color: #fff;
          font-size: 10px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-style: normal;
        }
      }
    }
  }
  
  .session-items {
    flex: 1;
    overflow-y: auto;
  }
  
  .session-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    cursor: pointer;
    border-bottom: 1px solid #f5f5f5;
    
    &:hover {
      background: #f9f9f9;
    }
    
    &.active {
      background: #ecf5ff;
    }
    
    .user-avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      flex-shrink: 0;
      position: relative;
      overflow: visible;
      
      img:first-child {
        width: 100%;
        height: 100%;
        border-radius: 50%;
        object-fit: cover;
      }
      
      &.is-vip {
        background: linear-gradient(135deg, #ffd700, #ffaa00);
        box-shadow: 0 0 8px rgba(255, 215, 0, 0.4);
      }
      
      .vip-badge {
        position: absolute;
        bottom: -4px;
        right: -4px;
        width: 24px;
        height: 24px;
        object-fit: contain;
      }
    }
    
    .session-info {
      flex: 1;
      min-width: 0;
      
      .session-top {
        display: flex;
        align-items: center;
        gap: 4px;
        margin-bottom: 4px;
        
        .username {
          font-size: 14px;
          font-weight: 500;
        }
        
        .vip-icon {
          width: 28px;
          height: 18px;
          object-fit: contain;
          flex-shrink: 0;
        }
        
        .time {
          font-size: 11px;
          color: #999;
          margin-left: auto;
        }
      }
      
      .session-bottom {
        display: flex;
        align-items: center;
        gap: 8px;
        
        .title {
          flex: 1;
          font-size: 12px;
          color: #666;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        
        .unread {
          min-width: 18px;
          height: 18px;
          background: #f56c6c;
          color: #fff;
          font-size: 10px;
          border-radius: 9px;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 0 5px;
        }
      }
    }
    
    .session-status {
      .status-tag {
        font-size: 11px;
        padding: 2px 6px;
        border-radius: 4px;
        
        &.waiting {
          background: #fef0f0;
          color: #f56c6c;
        }
        
        &.active {
          background: #e1f3d8;
          color: #67c23a;
        }
        
        &.closed {
          background: #f5f5f5;
          color: #999;
        }
      }
    }
  }
  
  .empty-list {
    padding: 40px;
    text-align: center;
    color: #999;
    font-size: 14px;
  }
}

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  
  .chat-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px;
    border-bottom: 1px solid #eee;
    
    .user-info {
      display: flex;
      align-items: center;
      gap: 12px;
      
      .user-avatar-header {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: #fff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        flex-shrink: 0;
        overflow: hidden;
        
        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
        
        &.is-vip {
          background: linear-gradient(135deg, #ffd700, #ffaa00);
          box-shadow: 0 0 8px rgba(255, 215, 0, 0.4);
        }
      }
      
      .user-details {
        display: flex;
        flex-direction: column;
        gap: 4px;
        
        .name-row {
          display: flex;
          align-items: center;
          gap: 6px;
          
          .name {
            font-size: 16px;
            font-weight: 500;
          }
          
          .vip-icon-header {
            width: 36px;
            height: 22px;
            object-fit: contain;
          }
        }
        
        .status {
          font-size: 12px;
          color: #999;
        }
      }
    }
  }
  
  .message-list {
    flex: 1;
    padding: 16px;
    overflow-y: auto;
    background: #f5f5f5;
  }
  
  .message-item {
    display: flex;
    gap: 10px;
    margin-bottom: 16px;
    
    &.from-user {
      .message-avatar {
        background: linear-gradient(135deg, #667eea, #764ba2);
      }
    }
    
    &.from-agent {
      flex-direction: row-reverse;
      
      .message-content {
        align-items: flex-end;
        
        .message-bubble {
          background: #409eff !important;
          color: #fff !important;
        }
      }
    }
    
    .message-avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: #ddd;
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      flex-shrink: 0;
      overflow: hidden;
      
      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
      
      &.user-avatar {
        background: linear-gradient(135deg, #667eea, #764ba2);
      }
    }
    
    .message-content {
      display: flex;
      flex-direction: column;
      max-width: 60%;
      
      .message-bubble {
        padding: 10px 14px;
        background: #fff;
        border-radius: 8px;
        font-size: 14px;
        line-height: 1.5;
        word-break: break-word;
        
        &.image-bubble {
          padding: 4px;
          background: transparent;
        }
        
        .msg-image {
          max-width: 200px;
          max-height: 200px;
          border-radius: 8px;
          cursor: pointer;
          
          &:hover {
            opacity: 0.9;
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
          color: #999;
        }
        
        .read-status {
          font-size: 10px;
          color: #999;
          
          &.read {
            color: #67c23a;
          }
        }
      }
    }
    
    .system-msg {
      width: 100%;
      text-align: center;
      font-size: 12px;
      color: #999;
      padding: 8px 0;
    }
  }
  
  .image-preview {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
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
    border-top: 1px solid #eee;
    
    .quick-replies {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      padding: 12px 16px;
      border-bottom: 1px solid #eee;
      background: #fafafa;
      
      .quick-reply-item {
        padding: 6px 12px;
        background: #fff;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 12px;
        cursor: pointer;
        
        &:hover {
          border-color: #409eff;
          color: #409eff;
        }
      }
    }
    
    .input-box {
      display: flex;
      gap: 12px;
      padding: 16px;
      
      .el-input {
        flex: 1;
      }
    }
  }
  
  .no-session {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}
</style>
