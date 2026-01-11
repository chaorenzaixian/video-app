<template>
  <div class="records-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="goBack">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </div>
      <h1 class="page-title">邀请记录</h1>
      <div class="header-right" @click="contactService">联系客服</div>
    </header>

    <!-- 内容区域 -->
    <div class="content-area">
      <!-- 空状态 -->
      <div v-if="invitations.length === 0" class="empty-state">
        <img class="empty-img" src="/images/backgrounds/no_data.webp" alt="暂无数据" />
        <p class="empty-text">暂无数据</p>
      </div>
      
      <!-- 邀请列表 -->
      <div v-else class="records-list">
        <div v-for="record in invitations" :key="record.id" class="record-item">
          <div class="record-avatar">
            <img v-if="record.invitee_avatar" :src="record.invitee_avatar" />
            <span v-else class="avatar-placeholder">{{ (record.invitee_username || '用户').charAt(0) }}</span>
          </div>
          <div class="record-info">
            <span class="record-name">{{ record.invitee_username || '匿名用户' }}</span>
            <span class="record-time">{{ formatTime(record.created_at) }}</span>
          </div>
          <div class="record-status">
            <span :class="['status-tag', record.is_valid ? 'valid' : 'invalid']">
              {{ record.is_valid ? '已充值' : '未充值' }}
            </span>
          </div>
        </div>
        
        <div v-if="hasMore" class="load-more" @click="loadMore">
          加载更多
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const router = useRouter()

const invitations = ref([])
const page = ref(1)
const hasMore = ref(true)

const fetchInvitations = async (reset = false) => {
  if (reset) {
    page.value = 1
    invitations.value = []
  }
  
  try {
    const res = await api.get('/promotion/invitations', {
      params: { page: page.value, page_size: 20 }
    })
    const data = res.data || res
    if (data.length < 20) {
      hasMore.value = false
    }
    invitations.value = [...invitations.value, ...data]
  } catch (error) {
    console.error('获取邀请记录失败:', error)
  }
}

const loadMore = () => {
  page.value++
  fetchInvitations()
}

const formatTime = (time) => {
  return dayjs(time).fromNow()
}

const goBack = () => {
  router.back()
}

const contactService = () => {
  // 联系客服逻辑
  alert('请通过Telegram联系客服')
}

onMounted(() => {
  fetchInvitations(true)
})
</script>

<style lang="scss" scoped>
.records-page {
  min-height: 100vh;
  background: #0a0a12;
  color: #fff;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  padding-top: calc(env(safe-area-inset-top, 0px) + 16px);
  
  .back-btn {
    font-size: 28px;
    color: #fff;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
  }
  
  .page-title {
    font-size: 18px;
    font-weight: 600;
  }
  
  .header-right {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.8);
    cursor: pointer;
  }
}

.content-area {
  padding: 0 16px;
  padding-bottom: calc(40px + env(safe-area-inset-bottom, 0px));
}

// 空状态
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-top: 120px;
  
  .empty-img {
    width: 200px;
    height: auto;
    margin-bottom: 20px;
    opacity: 0.8;
  }
  
  .empty-text {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.5);
  }
}

// 邀请列表
.records-list {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  overflow: hidden;
}

.record-item {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  
  &:last-child {
    border-bottom: none;
  }
  
  .record-avatar {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    overflow: hidden;
    margin-right: 12px;
    background: linear-gradient(53deg, #c084fc, #673AB7);
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    
    .avatar-placeholder {
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      font-weight: 600;
      color: #fff;
    }
  }
  
  .record-info {
    flex: 1;
    
    .record-name {
      display: block;
      font-size: 15px;
      font-weight: 500;
      margin-bottom: 4px;
    }
    
    .record-time {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);
    }
  }
  
  .record-status {
    .status-tag {
      font-size: 12px;
      padding: 4px 12px;
      border-radius: 12px;
      
      &.valid {
        background: rgba(34, 197, 94, 0.2);
        color: #22c55e;
      }
      
      &.invalid {
        background: rgba(255, 255, 255, 0.1);
        color: rgba(255, 255, 255, 0.5);
      }
    }
  }
}

.load-more {
  text-align: center;
  padding: 16px;
  color: #c084fc;
  font-size: 14px;
  cursor: pointer;
}
</style>
