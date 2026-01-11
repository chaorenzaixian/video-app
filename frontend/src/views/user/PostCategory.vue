<template>
  <div class="post-category-page">
    <!-- 顶部导航 -->
    <header class="top-header">
      <div class="back-btn" @click="$router.back()">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </div>
      <h1 class="page-title">{{ topicName }}</h1>
      <div class="header-right"></div>
    </header>

    <!-- 筛选标签 -->
    <div class="filter-tabs">
      <span 
        v-for="filter in filterTabs" 
        :key="filter.value"
        :class="['filter-tab', { active: activeFilter === filter.value }]"
        @click="switchFilter(filter.value)"
      >{{ filter.label }}</span>
    </div>

    <!-- 帖子列表 -->
    <div class="posts-list" ref="listRef" @scroll="handleScroll">
      <div v-for="post in posts" :key="post.id" class="post-card" @click="goToDetail(post.id)">
        <div class="post-header">
          <img :src="getAvatarUrl(post.user?.avatar, post.user?.id)" class="avatar clickable" @click.stop="goToUserProfile(post.user?.id)" />
          <div class="user-info">
            <div class="user-name-row">
              <span class="username clickable" @click.stop="goToUserProfile(post.user?.id)">{{ post.user?.nickname || post.user?.username || '匿名用户' }}</span>
              <img v-if="post.user?.is_vip" :src="getVipIcon(post.user?.vip_level)" class="vip-icon" alt="VIP" />
            </div>
            <span class="time">{{ formatTime(post.created_at) }}</span>
          </div>
        </div>
        <p class="post-text">{{ post.content }}</p>
        <div v-if="post.images && post.images.length" class="post-images">
          <div :class="['images-grid', `grid-${Math.min(post.images.length, 4)}`]">
            <div v-for="(img, idx) in post.images.slice(0, 4)" :key="idx" class="img-item">
              <img :src="img" />
              <span v-if="idx === 3 && post.images.length > 4" class="more-count">+{{ post.images.length - 4 }}</span>
            </div>
          </div>
        </div>
        <div class="post-stats">
          <span class="stat-item"><span class="stat-icon">👁</span> {{ formatCount(post.view_count) }}</span>
          <span class="stat-item"><span class="stat-icon">💬</span> {{ post.comment_count || 0 }}</span>
          <span class="stat-item" @click.stop="likePost(post)"><span class="stat-icon">{{ post.is_liked ? '❤️' : '🤍' }}</span> {{ formatCount(post.like_count) }}</span>
          <span v-if="post.topics && post.topics.length" class="post-topic-tag">#{{ post.topics[0].name }}</span>
        </div>
      </div>
      <div v-if="loading" class="loading">加载中...</div>
      <div v-if="!loading && !hasMore && posts.length" class="no-more">没有更多了</div>
      <div v-if="!loading && !posts.length" class="empty">暂无内容</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '@/utils/api'
import { getAvatarUrl } from '@/utils/avatar'
import { formatCount, formatCommentTime } from '@/utils/format'
import { getVipLevelIcon } from '@/constants/vip'

const router = useRouter()
const route = useRoute()

const topicId = ref(null)
const topicName = ref('')
const posts = ref([])
const loading = ref(false)
const hasMore = ref(true)
const page = ref(1)
const activeFilter = ref('hot_comment')
const listRef = ref(null)

const filterTabs = [
  { label: '最新热评', value: 'hot_comment' },
  { label: '最新上架', value: 'latest' },
  { label: '最多观看', value: 'hot' }
]

const getVipIcon = (level) => getVipLevelIcon(level)
const formatTime = (time) => formatCommentTime(time)

// 获取话题信息
const fetchTopicInfo = async () => {
  try {
    const res = await api.get(`/community/topics/${topicId.value}`)
    topicName.value = res.data?.name || '话题'
  } catch (e) {
    console.error('获取话题信息失败', e)
  }
}

// 获取帖子列表
const fetchPosts = async (reset = false) => {
  if (loading.value) return
  if (reset) {
    page.value = 1
    hasMore.value = true
    posts.value = []
  }
  if (!hasMore.value) return

  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: 20,
      topic_id: topicId.value,
      feed_type: activeFilter.value === 'hot_comment' ? 'recommend' : activeFilter.value
    }
    const res = await api.get('/community/posts', { params })
    const data = res.data || []
    
    if (data.length < 20) hasMore.value = false
    posts.value = reset ? data : [...posts.value, ...data]
    page.value++
  } catch (e) {
    console.error('获取帖子失败', e)
  } finally {
    loading.value = false
  }
}

// 切换筛选
const switchFilter = (filter) => {
  activeFilter.value = filter
  fetchPosts(true)
}

// 点赞
const likePost = async (post) => {
  try {
    const res = await api.post(`/community/posts/${post.id}/like`)
    post.is_liked = res.data.liked
    post.like_count = res.data.like_count
  } catch (e) {
    console.error('点赞失败', e)
  }
}

// 滚动加载
const handleScroll = (e) => {
  const { scrollTop, scrollHeight, clientHeight } = e.target
  if (scrollHeight - scrollTop - clientHeight < 100 && !loading.value && hasMore.value) {
    fetchPosts()
  }
}

const goToDetail = (id) => router.push(`/user/community/post/${id}`)
const goToUserProfile = (userId) => {
  if (userId) router.push(`/user/member/${userId}`)
}

// 监听路由参数变化
watch(() => route.params.id, (newId) => {
  if (newId) {
    topicId.value = parseInt(newId)
    fetchTopicInfo()
    fetchPosts(true)
  }
}, { immediate: true })

onMounted(() => {
  topicId.value = parseInt(route.params.id)
  if (route.query.name) {
    topicName.value = route.query.name
  }
  fetchTopicInfo()
  fetchPosts(true)
})
</script>


<style lang="scss" scoped>
.post-category-page {
  min-height: 100vh;
  background: #0d0d0d;
  display: flex;
  flex-direction: column;
}

/* 顶部导航 */
.top-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #0d0d0d;
  position: sticky;
  top: 0;
  z-index: 100;
}

.back-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.back-icon {
  width: 24px;
  height: 24px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  margin: 0;
}

.header-right {
  width: 36px;
}

/* 筛选标签 */
.filter-tabs {
  display: flex;
  gap: 24px;
  padding: 10px 16px 12px;
  border-bottom: 1px solid #1a1a1a;
  background: #0d0d0d;
  position: sticky;
  top: 60px;
  z-index: 99;
}

.filter-tab {
  color: #666;
  font-size: 14px;
  cursor: pointer;
  padding: 4px 0;
  position: relative;
  white-space: nowrap;
}

.filter-tab.active {
  color: #fff;
  font-weight: 500;
}

.filter-tab.active::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 2px;
  background: #8b5cf6;
  border-radius: 1px;
}

/* 帖子列表 */
.posts-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px 20px;
}

.post-card {
  background: #151515;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}

.post-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  
  &.clickable {
    cursor: pointer;
    transition: transform 0.2s;
    
    &:hover {
      transform: scale(1.05);
    }
  }
}

.user-info {
  margin-left: 12px;
}

.user-name-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.username {
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  
  &.clickable {
    cursor: pointer;
    
    &:hover {
      color: #a855f7;
    }
  }
}

.vip-icon {
  width: 36px;
  height: 18px;
  object-fit: contain;
}

.time {
  color: #666;
  font-size: 12px;
}

.post-text {
  color: #ddd;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 图片网格 */
.post-images {
  margin-bottom: 12px;
}

.images-grid {
  display: grid;
  gap: 4px;
  border-radius: 8px;
  overflow: hidden;
}

.images-grid.grid-1 { grid-template-columns: 1fr; max-width: 70%; }
.images-grid.grid-2 { grid-template-columns: repeat(2, 1fr); }
.images-grid.grid-3 { grid-template-columns: repeat(3, 1fr); }
.images-grid.grid-4 { grid-template-columns: repeat(4, 1fr); }

.img-item {
  position: relative;
  aspect-ratio: 1;
}

.img-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.more-count {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
}

/* 帖子统计 */
.post-stats {
  display: flex;
  align-items: center;
  gap: 20px;
  color: #666;
  font-size: 13px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.stat-icon {
  font-size: 14px;
}

.post-topic-tag {
  margin-left: auto;
  padding: 4px 12px;
  background: transparent;
  border: 1px solid rgba(168, 85, 247, 0.5);
  border-radius: 12px;
  color: #a855f7;
  font-size: 12px;
  cursor: pointer;
}

.loading, .no-more, .empty {
  text-align: center;
  padding: 30px;
  color: #666;
}

/* 响应式 */
@media (min-width: 768px) {
  .post-category-page {
    max-width: 750px;
    margin: 0 auto;
  }
  
  .post-card {
    padding: 20px;
  }
}

@media (min-width: 1024px) {
  .post-category-page {
    max-width: 900px;
  }
}

@media (min-width: 1280px) {
  .post-category-page {
    max-width: 1200px;
  }
}
</style>
