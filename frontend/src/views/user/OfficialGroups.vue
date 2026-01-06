<template>
  <div class="official-groups-page">
    <!-- 顶部导航 -->
    <div class="header">
      <div class="back-btn" @click="router.back()">
        <span class="icon">&lt;</span>
      </div>
      <div class="title">加群开车</div>
      <div class="placeholder"></div>
    </div>

    <!-- 内容区域 -->
    <div class="content">
      <!-- 官方社群 -->
      <div class="section" v-if="communityGroups.length > 0">
        <div class="section-header">
          <h2 class="section-title">官方社群</h2>
          <p class="section-subtitle">一起看片一起分享心得</p>
        </div>
        <div class="group-list">
          <div class="group-item" v-for="group in communityGroups" :key="group.id">
            <div class="group-icon" :style="getIconStyle(group)">
              <span class="icon-emoji">{{ getIconEmoji(group.icon_type) }}</span>
            </div>
            <div class="group-name">{{ group.name }}</div>
            <button class="join-btn" @click="joinGroup(group)">立即加入</button>
          </div>
        </div>
      </div>

      <!-- 商务合作 -->
      <div class="section" v-if="businessGroups.length > 0">
        <div class="section-header">
          <h2 class="section-title">商务合作</h2>
          <p class="section-subtitle">代理合作/商务合作</p>
        </div>
        <div class="group-list">
          <div class="group-item" v-for="group in businessGroups" :key="group.id">
            <div class="group-icon" :style="getIconStyle(group)">
              <span class="icon-emoji">{{ getIconEmoji(group.icon_type) }}</span>
            </div>
            <div class="group-name">{{ group.name }}</div>
            <button class="join-btn" @click="joinGroup(group)">立即加入</button>
          </div>
        </div>
      </div>

      <!-- 加载中 -->
      <div class="loading" v-if="loading">
        <span>加载中...</span>
      </div>

      <!-- 空状态 -->
      <div class="empty" v-if="!loading && groups.length === 0">
        <span>暂无群组</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'

const router = useRouter()
const loading = ref(true)
const groups = ref([])

// 分类群组
const communityGroups = computed(() => 
  groups.value.filter(g => g.group_type === 'community')
)
const businessGroups = computed(() => 
  groups.value.filter(g => g.group_type === 'business')
)

// 获取图标样式
const getIconStyle = (group) => {
  if (group.icon_bg) {
    return { background: group.icon_bg }
  }
  // 默认渐变
  const defaultGradients = {
    rocket: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    telegram: 'linear-gradient(135deg, #0088cc 0%, #00a2e8 100%)',
    briefcase: 'linear-gradient(135deg, #4a90d9 0%, #2b5876 100%)',
    heart: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  }
  return { background: defaultGradients[group.icon_type] || defaultGradients.rocket }
}

// 获取图标emoji
const getIconEmoji = (iconType) => {
  const icons = {
    rocket: '🚀',
    telegram: '✈️',
    briefcase: '💼',
    heart: '💙',
    potato: '🥔'
  }
  return icons[iconType] || '🔗'
}

// 加入群组
const joinGroup = (group) => {
  if (group.url) {
    window.open(group.url, '_blank')
  }
}

// 获取群组列表
const fetchGroups = async () => {
  try {
    const res = await api.get('/ads/groups')
    groups.value = res.data || []
  } catch (error) {
    console.log('获取群组列表失败', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchGroups()
})
</script>

<style lang="scss" scoped>
.official-groups-page {
  min-height: 100vh;
  background: #0a0a0a;
  color: #fff;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: #0a0a0a;
  position: sticky;
  top: 0;
  z-index: 100;
  
  .back-btn {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    
    .icon {
      font-size: 20px;
      color: #fff;
    }
  }
  
  .title {
    font-size: 18px;
    font-weight: 600;
  }
  
  .placeholder {
    width: 40px;
  }
}

.content {
  padding: 0 16px 20px;
}

.section {
  margin-bottom: 24px;
  
  .section-header {
    margin-bottom: 16px;
    
    .section-title {
      font-size: 18px;
      font-weight: 600;
      color: #fff;
      margin: 0 0 4px;
    }
    
    .section-subtitle {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.5);
      margin: 0;
    }
  }
}

.group-list {
  background: #1a1a1a;
  border-radius: 12px;
  overflow: hidden;
}

.group-item {
  display: flex;
  align-items: center;
  padding: 16px;
  
  &:not(:last-child) {
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  }
  
  .group-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 12px;
    flex-shrink: 0;
    
    .icon-emoji {
      font-size: 24px;
    }
  }
  
  .group-name {
    flex: 1;
    font-size: 15px;
    font-weight: 500;
    color: #fff;
  }
  
  .join-btn {
    padding: 8px 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    border-radius: 20px;
    color: #fff;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: transform 0.2s, opacity 0.2s;
    
    &:active {
      transform: scale(0.95);
      opacity: 0.9;
    }
  }
}

.loading,
.empty {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 60px 20px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
}
</style>
