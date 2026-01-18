<template>
  <div class="messages-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </div>
      <h1 class="page-title">我的消息</h1>
      <div class="header-right"></div>
    </header>

    <!-- 标签栏 -->
    <div class="tabs-bar">
      <div 
        class="tab-item" 
        :class="{ active: activeTab === 'private' }"
        @click="activeTab = 'private'"
      >
        私信
        <span v-if="unreadCounts.private > 0" class="tab-badge">{{ unreadCounts.private }}</span>
      </div>
      <div class="tab-divider">|</div>
      <div 
        class="tab-item" 
        :class="{ active: activeTab === 'comment' }"
        @click="activeTab = 'comment'"
      >
        评论
        <span v-if="unreadCounts.comment > 0" class="tab-badge">{{ unreadCounts.comment }}</span>
      </div>
      <div class="tab-divider">|</div>
      <div 
        class="tab-item" 
        :class="{ active: activeTab === 'like' }"
        @click="activeTab = 'like'"
      >
        点赞
        <span v-if="unreadCounts.like > 0" class="tab-badge">{{ unreadCounts.like }}</span>
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="message-list">
      <!-- 私信列表 -->
      <template v-if="activeTab === 'private'">
        <div 
          v-for="item in privateMessages" 
          :key="item.id" 
          class="message-item"
          @click="goToChat(item)"
        >
          <div class="avatar-wrapper">
            <img :src="getAvatarUrl(item.avatar, item.user_id)" class="avatar" />
            <span v-if="item.unread_count > 0" class="unread-dot"></span>
          </div>
          <div class="message-content">
            <div class="nickname-row">
              <span class="nickname">{{ item.nickname || item.username }}</span>
              <img 
                v-if="item.vip_level > 0" 
                :src="getVipLevelIcon(item.vip_level)" 
                class="vip-badge"
                alt="VIP"
              />
            </div>
            <span class="preview">{{ item.last_message || '暂无消息' }}</span>
          </div>
          <span class="time">{{ formatTime(item.last_time) }}</span>
        </div>
        <div v-if="privateMessages.length === 0" class="empty-state">
          <span>暂无私信消息</span>
        </div>
      </template>

      <!-- 评论列表 -->
      <template v-if="activeTab === 'comment'">
        <div 
          v-for="item in commentMessages" 
          :key="item.id" 
          class="message-item"
          @click="goToTarget(item)"
        >
          <div class="avatar-wrapper">
            <img :src="getAvatarUrl(item.avatar, item.user_id)" class="avatar" />
          </div>
          <div class="message-content">
            <div class="nickname-row">
              <span class="nickname">{{ item.nickname || item.username }}</span>
              <img 
                v-if="item.vip_level > 0" 
                :src="getVipLevelIcon(item.vip_level)" 
                class="vip-badge"
                alt="VIP"
              />
            </div>
            <span class="preview">
              {{ getCommentText(item) }}：{{ item.content }}
            </span>
          </div>
          <span class="time">{{ formatTime(item.created_at) }}</span>
        </div>
        <div v-if="commentMessages.length === 0" class="empty-state">
          <span>暂无评论消息</span>
        </div>
      </template>

      <!-- 点赞列表 -->
      <template v-if="activeTab === 'like'">
        <div 
          v-for="item in likeMessages" 
          :key="item.id" 
          class="message-item"
          @click="goToTarget(item)"
        >
          <div class="avatar-wrapper">
            <img :src="getAvatarUrl(item.avatar, item.user_id)" class="avatar" />
          </div>
          <div class="message-content">
            <div class="nickname-row">
              <span class="nickname">{{ item.nickname || item.username }}</span>
              <img 
                v-if="item.vip_level > 0" 
                :src="getVipLevelIcon(item.vip_level)" 
                class="vip-badge"
                alt="VIP"
              />
            </div>
            <span class="preview">
              {{ getLikeText(item) }}
              <template v-if="item.content">：{{ item.content }}</template>
            </span>
          </div>
          <span class="time">{{ formatTime(item.created_at) }}</span>
        </div>
        <div v-if="likeMessages.length === 0" class="empty-state">
          <span>暂无点赞消息</span>
        </div>
      </template>
    </div>

    <!-- 底部提示 -->
    <div class="list-footer">
      <span>—— 没有更多数据了 ——</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'

const router = useRouter()

const activeTab = ref('private')
const privateMessages = ref([])
const commentMessages = ref([])
const likeMessages = ref([])
const loading = ref(false)

const unreadCounts = ref({
  private: 0,
  comment: 0,
  like: 0
})

// VIP等级图标映射
const VIP_LEVEL_ICONS = {
  1: '/images/backgrounds/vip_gold.webp',
  2: '/images/backgrounds/vip_1.webp',
  3: '/images/backgrounds/vip_2.webp',
  4: '/images/backgrounds/vip_3.webp',
  5: '/images/backgrounds/super_vip_red.webp',
  6: '/images/backgrounds/super_vip_blue.webp'
}

// 获取VIP等级图标
const getVipLevelIcon = (level) => {
  return VIP_LEVEL_ICONS[level] || VIP_LEVEL_ICONS[1]
}

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

// 获取头像URL - 有自定义头像显示自定义头像，否则显示系统默认头像
const getAvatarUrl = (avatar, id) => {
  // 有设置头像则显示
  if (avatar) {
    if (avatar.startsWith('http')) {
      return avatar
    }
    return avatar.startsWith('/') ? avatar : `/${avatar}`
  }
  // 没设置则根据用户ID分配系统默认头像
  const numericId = parseInt(id) || 1
  return getDefaultAvatarPath(numericId)
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  
  // 今天
  if (diff < 86400000 && date.getDate() === now.getDate()) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  // 昨天
  if (diff < 172800000) {
    return '昨天'
  }
  // 今年内
  if (date.getFullYear() === now.getFullYear()) {
    return `${date.getMonth() + 1}-${date.getDate()}`
  }
  // 更早
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

// 获取私信会话列表
const fetchPrivateMessages = async () => {
  try {
    const res = await api.get('/social/messages/conversations')
    // 转换数据结构
    privateMessages.value = (res.data || []).map(item => ({
      id: item.id,
      user_id: item.other_user?.id,
      nickname: item.other_user?.nickname,
      username: item.other_user?.nickname,
      avatar: item.other_user?.avatar,
      is_vip: item.other_user?.is_vip || false,
      vip_level: item.other_user?.vip_level || 0,
      last_message: item.last_message,
      last_time: item.last_message_at,
      unread_count: item.unread_count || 0
    }))
    // 计算未读数
    unreadCounts.value.private = privateMessages.value.reduce((sum, item) => sum + (item.unread_count || 0), 0)
  } catch (error) {
    console.log('获取私信列表失败')
  }
}

// 获取评论消息
const fetchCommentMessages = async () => {
  try {
    const res = await api.get('/notifications/comments')
    console.log('评论消息API响应:', res.data)
    commentMessages.value = res.data?.items || []
    unreadCounts.value.comment = res.data?.unread_count || 0
  } catch (error) {
    console.log('获取评论消息失败', error)
    console.log('错误详情:', error.response?.data)
    commentMessages.value = []
  }
}

// 获取点赞消息
const fetchLikeMessages = async () => {
  try {
    const res = await api.get('/notifications/likes')
    console.log('点赞消息API响应:', res.data)
    likeMessages.value = res.data?.items || []
    unreadCounts.value.like = res.data?.unread_count || 0
  } catch (error) {
    console.log('获取点赞消息失败', error)
    likeMessages.value = []
  }
}

// 跳转到聊天页面
const goToChat = (item) => {
  router.push({
    name: 'PrivateChat',
    params: { id: item.user_id },
    query: {
      nickname: item.nickname || item.username,
      avatar: item.avatar
    }
  })
}

// 获取评论文本
const getCommentText = (item) => {
  const typeMap = {
    'video': '视频',
    'short': '短视频',
    'post': '帖子',
    'gallery': '图集',
    'novel': '小说'
  }
  const targetName = typeMap[item.target_type] || '内容'
  
  if (item.notification_type === 'reply') {
    return '回复了你的评论'
  }
  return `评论了你的${targetName}`
}

// 获取点赞文本
const getLikeText = (item) => {
  const typeMap = {
    'video': '视频',
    'short': '短视频',
    'post': '帖子',
    'gallery': '图集',
    'novel': '小说',
    'video_comment': '评论',
    'post_comment': '评论',
    'gallery_comment': '评论'
  }
  const targetName = typeMap[item.target_type] || '内容'
  return `赞了你的${targetName}`
}

// 跳转到目标页面
const goToTarget = (item) => {
  const targetType = item.target_type
  const targetId = item.target_id
  
  if (!targetId) return
  
  switch (targetType) {
    case 'video':
      router.push(`/user/video/${targetId}`)
      break
    case 'short':
      router.push(`/shorts?id=${targetId}`)
      break
    case 'post':
      router.push(`/user/community/${targetId}`)
      break
    case 'gallery':
      router.push(`/gallery/${targetId}`)
      break
    case 'novel':
      router.push(`/novel/${targetId}`)
      break
    case 'video_comment':
      router.push(`/user/video/${targetId}`)
      break
    case 'post_comment':
      router.push(`/user/community/${targetId}`)
      break
    case 'gallery_comment':
      router.push(`/gallery/${targetId}`)
      break
    default:
      break
  }
}

onMounted(async () => {
  loading.value = true
  
  // 先获取未读数量
  try {
    const countRes = await api.get('/notifications/unread-count')
    unreadCounts.value = {
      private: countRes.data?.private_messages || 0,
      comment: countRes.data?.comments || 0,
      like: countRes.data?.likes || 0
    }
  } catch (e) {
    console.log('获取未读数量失败')
  }
  
  await Promise.all([
    fetchPrivateMessages(),
    fetchCommentMessages(),
    fetchLikeMessages()
  ])
  loading.value = false
  
  // 标记所有通知为已读
  try {
    await api.post('/notifications/mark-read?notification_type=all')
    // 清空未读数量
    unreadCounts.value = { private: 0, comment: 0, like: 0 }
  } catch (e) {
    console.log('标记已读失败')
  }
})
</script>

<style lang="scss" scoped>
$breakpoint-lg: 768px;
$breakpoint-xl: 1024px;

.messages-page {
  min-height: 100vh;
  background: #0a0a0a;
  color: #fff;
  padding-bottom: 20px;
  
  @media (min-width: $breakpoint-lg) {
    max-width: 650px;
    margin: 0 auto;
  }
  @media (min-width: $breakpoint-xl) {
    max-width: 750px;
  }
}

// 顶部导航
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
    font-size: 18px;
    font-weight: 600;
    margin: 0;
  }
  
  .header-right {
    width: 32px;
  }
}

// 标签栏
.tabs-bar {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  gap: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  
  .tab-item {
    font-size: 15px;
    color: rgba(255, 255, 255, 0.6);
    cursor: pointer;
    position: relative;
    transition: color 0.2s;
    display: flex;
    align-items: center;
    gap: 4px;
    
    &.active {
      color: #fff;
      font-weight: 600;
    }
    
    .tab-badge {
      background: #ff4757;
      color: #fff;
      font-size: 10px;
      min-width: 16px;
      height: 16px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0 4px;
    }
  }
  
  .tab-divider {
    color: rgba(255, 255, 255, 0.2);
    font-size: 14px;
  }
}

// 消息列表
.message-list {
  padding: 8px 12px;
}

.message-item {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  background: rgba(30, 35, 50, 0.6);
  border-radius: 12px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: background 0.2s;
  
  @media (hover: hover) {
    &:hover {
      background: rgba(40, 45, 60, 0.8);
    }
  }
  
  &:active {
    background: rgba(40, 45, 60, 0.8);
  }
  
  .avatar-wrapper {
    position: relative;
    flex-shrink: 0;
    
    .avatar {
      width: 50px;
      height: 50px;
      border-radius: 50%;
      object-fit: cover;
      background: #1a1a1a;
    }
    
    .unread-dot {
      position: absolute;
      top: 0;
      right: 0;
      width: 10px;
      height: 10px;
      background: #ff4757;
      border-radius: 50%;
      border: 2px solid #0a0a0a;
    }
  }
  
  .message-content {
    flex: 1;
    margin-left: 12px;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 4px;
    
    .nickname-row {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    
    .nickname {
      font-size: 13px;
      font-weight: 600;
      background: linear-gradient(135deg, #ffd700 0%, #ffec8b 30%, #daa520 60%, #ffd700 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    
    .vip-badge {
      height: 16px;
      width: auto;
      max-width: 45px;
      object-fit: contain;
    }
    
    .preview {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.5);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
  
  .time {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.4);
    flex-shrink: 0;
    margin-left: 12px;
  }
}

// 空状态
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 14px;
}

// 底部提示
.list-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  color: rgba(255, 255, 255, 0.3);
  font-size: 13px;
}
</style>



