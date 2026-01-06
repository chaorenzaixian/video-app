<template>
  <div class="detail-page">
    <!-- 顶部导航 -->
    <div class="top-bar">
      <span class="back" @click="$router.back()">
        <svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
          <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
        </svg>
      </span>
      <span class="title">帖子详情</span>
      <span class="placeholder"></span>
    </div>

    <!-- 帖子内容 -->
    <div v-if="post" class="post-content-wrapper">
      <!-- 用户信息行 -->
      <div class="user-row">
        <img :src="getAvatarUrl(post.user?.avatar, post.user?.id)" class="avatar" @click="goProfile(post.user?.id)" />
        <div class="user-meta">
          <span class="username" @click="goProfile(post.user?.id)">{{ post.user?.nickname || post.user?.username }}</span>
          <span class="date">{{ formatDate(post.created_at) }}</span>
        </div>
        <button 
          v-if="!post.is_followed && post.user?.id !== currentUserId"
          class="follow-btn"
          @click="followUser"
        >
          <span>+</span> 关注
        </button>
      </div>

      <!-- 标题 -->
      <h1 class="post-title" v-if="post.title">{{ post.title }}</h1>

      <!-- 阅读量 -->
      <div class="view-count">{{ formatCount(post.view_count) }}阅读</div>

      <!-- 话题标签 -->
      <div class="topic-tags" v-if="post.topics && post.topics.length">
        <span class="topic-tag" v-for="topic in post.topics" :key="topic.id">#{{ topic.name }}</span>
      </div>

      <!-- 分隔线 -->
      <div class="divider-line"></div>

      <!-- 正文内容 -->
      <div class="post-body">
        <p class="content-text">{{ post.content }}</p>
      </div>

      <!-- 图片列表 -->
      <div class="images-list" v-if="post.images && post.images.length">
        <img 
          v-for="(img, idx) in post.images" 
          :key="idx" 
          :src="img" 
          class="post-image"
          @click="previewImage(idx)" 
        />
      </div>

      <!-- 视频 -->
      <div v-if="post.video_url" class="video-wrapper">
        <video :src="post.video_url" controls playsinline></video>
      </div>
    </div>

    <!-- 评论区 -->
    <div class="comments-section">
      <div class="comments-header">
        <span class="comments-count">{{ post?.comment_count || 0 }}条评论</span>
        <div class="sort-tabs">
          <span :class="{ active: sortBy === 'hot' }" @click="sortBy = 'hot'">推荐</span>
          <span class="divider">|</span>
          <span :class="{ active: sortBy === 'new' }" @click="sortBy = 'new'">最新</span>
        </div>
      </div>

      <!-- 评论列表 -->
      <div class="comments-list">
        <div v-for="comment in comments" :key="comment.id" class="comment-item">
          <img :src="getAvatarUrl(comment.user?.avatar, comment.user?.id)" class="comment-avatar" @click="goProfile(comment.user?.id)" />
          <div class="comment-content">
            <div class="comment-user">
              <span class="comment-username">{{ comment.user?.nickname || comment.user?.username }}</span>
              <img v-if="comment.user?.vip_level" :src="getVipIcon(comment.user.vip_level)" class="vip-badge" />
            </div>
            <p class="comment-text">{{ comment.content }}</p>
            <!-- 评论图片 -->
            <div v-if="comment.images && comment.images.length" class="comment-images">
              <img v-for="(img, idx) in comment.images" :key="idx" :src="img" class="comment-img" />
            </div>
            <div class="comment-meta">
              <span class="comment-time">{{ formatDate(comment.created_at) }}</span>
              <span class="comment-like" @click="likeComment(comment)">
                <span class="heart">{{ comment.is_liked ? '❤️' : '♡' }}</span>
                {{ comment.like_count || 0 }}
              </span>
              <span class="comment-reply-btn" @click="replyTo(comment)">💬</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="loadingComments" class="loading">加载中...</div>
      <div v-if="!loadingComments && !hasMoreComments && comments.length" class="no-more">— 没有更多评论了 —</div>
      <div v-if="!loadingComments && comments.length === 0" class="empty-comments">暂无评论，快来抢沙发~</div>
    </div>

    <!-- 底部操作栏 -->
    <div class="bottom-bar">
      <div class="input-wrapper" @click="openCommentInput">
        <span class="input-placeholder">请输入评论</span>
      </div>
      <div class="action-btns">
        <span class="action-item" @click="sharePost">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92s2.92-1.31 2.92-2.92-1.31-2.92-2.92-2.92z"/></svg>
          分享
        </span>
        <span class="action-item" @click="collectPost">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>
          {{ formatCount(post?.collect_count || post?.view_count || 0) }}
        </span>
        <span class="action-item" :class="{ liked: post?.is_liked }" @click="likePost">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
          {{ formatCount(post?.like_count || 0) }}
        </span>
      </div>
    </div>

    <!-- 评论输入弹窗 -->
    <div class="comment-modal" v-if="showCommentInput" @click.self="showCommentInput = false">
      <div class="comment-modal-content">
        <div class="modal-header">
          <span>{{ replyTarget ? `回复 @${replyTarget.user?.nickname || replyTarget.user?.username}` : '发表评论' }}</span>
          <span class="close-btn" @click="showCommentInput = false">×</span>
        </div>
        <textarea 
          ref="commentTextarea"
          v-model="commentText" 
          placeholder="说点什么..."
          rows="4"
        ></textarea>
        <div class="modal-footer">
          <button class="cancel-btn" @click="showCommentInput = false">取消</button>
          <button class="submit-btn" @click="submitComment" :disabled="!commentText.trim()">发送</button>
        </div>
      </div>
    </div>

    <!-- 图片预览 -->
    <div class="image-preview" v-if="previewVisible" @click="previewVisible = false">
      <img :src="previewImageUrl" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'
import { getAvatarUrl } from '@/utils/avatar'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// VIP等级图标映射
const VIP_LEVEL_ICONS = {
  1: '/images/backgrounds/vip_gold.webp',
  2: '/images/backgrounds/vip_1.webp',
  3: '/images/backgrounds/vip_2.webp',
  4: '/images/backgrounds/vip_3.webp',
  5: '/images/backgrounds/super_vip_red.webp',
  6: '/images/backgrounds/super_vip_blue.webp'
}

const getVipIcon = (level) => VIP_LEVEL_ICONS[level] || VIP_LEVEL_ICONS[1]

const postId = computed(() => route.params.id)
const currentUserId = computed(() => userStore.user?.id)

const post = ref(null)
const comments = ref([])
const commentText = ref('')
const replyTarget = ref(null)
const loadingComments = ref(false)
const hasMoreComments = ref(true)
const commentPage = ref(1)
const sortBy = ref('hot')
const showCommentInput = ref(false)
const commentTextarea = ref(null)

// 图片预览
const previewVisible = ref(false)
const previewImageUrl = ref('')

// 获取动态详情
const fetchPost = async () => {
  try {
    const res = await api.get(`/community/posts/${postId.value}`)
    post.value = res.data
  } catch (e) {
    console.error('获取动态失败', e)
  }
}

// 获取评论
const fetchComments = async (reset = false) => {
  if (loadingComments.value) return
  if (reset) {
    commentPage.value = 1
    hasMoreComments.value = true
    comments.value = []
  }
  if (!hasMoreComments.value) return

  loadingComments.value = true
  try {
    const res = await api.get(`/community/posts/${postId.value}/comments`, {
      params: { page: commentPage.value, page_size: 20 }
    })
    const data = res.data || []
    if (data.length < 20) hasMoreComments.value = false
    comments.value = reset ? data : [...comments.value, ...data]
    commentPage.value++
  } catch (e) {
    console.error('获取评论失败', e)
  } finally {
    loadingComments.value = false
  }
}

// 点赞动态
const likePost = async () => {
  try {
    const res = await api.post(`/community/posts/${postId.value}/like`)
    post.value.is_liked = res.data.liked
    post.value.like_count = res.data.like_count
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

// 收藏
const collectPost = async () => {
  ElMessage.info('收藏功能开发中')
}

// 分享
const sharePost = () => {
  ElMessage.info('分享功能开发中')
}

// 关注用户
const followUser = async () => {
  try {
    await api.post(`/users/${post.value.user.id}/follow`)
    post.value.is_followed = true
    ElMessage.success('关注成功')
  } catch (e) {
    ElMessage.error('关注失败')
  }
}

// 点赞评论
const likeComment = async (comment) => {
  try {
    const res = await api.post(`/community/comments/${comment.id}/like`)
    comment.is_liked = res.data.liked
    comment.like_count = res.data.like_count
  } catch (e) {
    console.error('点赞失败', e)
  }
}

// 打开评论输入
const openCommentInput = () => {
  replyTarget.value = null
  showCommentInput.value = true
  nextTick(() => commentTextarea.value?.focus())
}

// 回复评论
const replyTo = (comment) => {
  replyTarget.value = comment
  showCommentInput.value = true
  nextTick(() => commentTextarea.value?.focus())
}

// 提交评论
const submitComment = async () => {
  if (!commentText.value.trim()) return
  
  try {
    const payload = {
      content: commentText.value,
      images: []
    }
    if (replyTarget.value) {
      payload.parent_id = replyTarget.value.parent_id || replyTarget.value.id
      payload.reply_to_user_id = replyTarget.value.user.id
    }
    
    await api.post(`/community/posts/${postId.value}/comments`, payload)
    commentText.value = ''
    replyTarget.value = null
    showCommentInput.value = false
    post.value.comment_count++
    ElMessage.success('评论成功')
    fetchComments(true)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '评论失败')
  }
}

// 格式化日期
const formatDate = (time) => {
  if (!time) return ''
  const d = new Date(time)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`
}

// 格式化数量
const formatCount = (count) => {
  if (!count) return '0'
  if (count >= 10000) return (count / 10000).toFixed(1) + 'W'
  if (count >= 1000) return (count / 1000).toFixed(1) + 'K'
  return count.toString()
}

const goProfile = (id) => {
  if (id) router.push(`/user/member/${id}`)
}

const previewImage = (idx) => {
  if (post.value?.images?.[idx]) {
    previewImageUrl.value = post.value.images[idx]
    previewVisible.value = true
  }
}

onMounted(() => {
  fetchPost()
  fetchComments(true)
})
</script>

<style lang="scss" scoped>
.detail-page {
  min-height: 100vh;
  background: #0d0d0d;
  padding-bottom: 70px;
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #0d0d0d;
  position: sticky;
  top: 0;
  z-index: 100;

  .back {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    cursor: pointer;
  }

  .title {
    color: #fff;
    font-size: 17px;
    font-weight: 500;
  }

  .placeholder {
    width: 32px;
  }
}

.post-content-wrapper {
  padding: 0 16px;
}

.user-row {
  display: flex;
  align-items: center;
  padding: 16px 0;

  .avatar {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    object-fit: cover;
    cursor: pointer;
  }

  .user-meta {
    flex: 1;
    margin-left: 12px;
    display: flex;
    flex-direction: column;
    gap: 4px;

    .username {
      color: #fff;
      font-size: 15px;
      font-weight: 500;
      cursor: pointer;
    }

    .date {
      color: #666;
      font-size: 12px;
    }
  }

  .follow-btn {
    padding: 6px 16px;
    background: transparent;
    border: 1px solid #a855f7;
    border-radius: 16px;
    color: #a855f7;
    font-size: 13px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 2px;

    &:active {
      opacity: 0.8;
    }
  }
}

.post-title {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  line-height: 1.5;
  margin: 0 0 12px;
}

.view-count {
  color: #666;
  font-size: 13px;
  margin-bottom: 16px;
}

.topic-tags {
  margin-bottom: 16px;

  .topic-tag {
    display: inline-block;
    padding: 6px 16px;
    background: transparent;
    border: 1px solid rgba(168, 85, 247, 0.5);
    border-radius: 16px;
    color: #a855f7;
    font-size: 13px;
  }
}

.divider-line {
  height: 1px;
  background: linear-gradient(90deg, transparent, #333, transparent);
  margin-bottom: 16px;
}

.post-body {
  margin-bottom: 16px;

  .content-text {
    color: #ddd;
    font-size: 15px;
    line-height: 1.8;
    white-space: pre-wrap;
    word-break: break-word;
  }
}

.images-list {
  .post-image {
    width: 100%;
    border-radius: 8px;
    margin-bottom: 8px;
    cursor: pointer;
  }
}

.video-wrapper {
  video {
    width: 100%;
    border-radius: 8px;
  }
}

// 评论区
.comments-section {
  margin-top: 16px;
  padding: 0 16px;
  border-top: 8px solid #1a1a1a;
}

.comments-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;

  .comments-count {
    color: #fff;
    font-size: 15px;
  }

  .sort-tabs {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #666;
    font-size: 13px;

    span {
      cursor: pointer;

      &.active {
        color: #fff;
      }

      &.divider {
        cursor: default;
      }
    }
  }
}

.comment-item {
  display: flex;
  padding: 12px 0;
  border-bottom: 1px solid #1a1a1a;

  .comment-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    object-fit: cover;
    cursor: pointer;
    flex-shrink: 0;
  }

  .comment-content {
    flex: 1;
    margin-left: 12px;
  }

  .comment-user {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 6px;

    .comment-username {
      color: #888;
      font-size: 14px;
    }

    .vip-badge {
      width: 32px;
      height: 16px;
      object-fit: contain;
    }
  }

  .comment-text {
    color: #eee;
    font-size: 14px;
    line-height: 1.6;
    margin: 0 0 8px;
  }

  .comment-images {
    display: flex;
    gap: 8px;
    margin-bottom: 8px;

    .comment-img {
      width: 120px;
      height: 120px;
      object-fit: cover;
      border-radius: 8px;
    }
  }

  .comment-meta {
    display: flex;
    align-items: center;
    gap: 20px;

    .comment-time {
      color: #555;
      font-size: 12px;
    }

    .comment-like, .comment-reply-btn {
      color: #666;
      font-size: 13px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 4px;
    }
  }
}

.loading, .no-more, .empty-comments {
  text-align: center;
  padding: 30px;
  color: #555;
  font-size: 13px;
}

// 底部操作栏
.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  padding: 10px 16px;
  background: #111;
  border-top: 1px solid #222;
  gap: 12px;

  .input-wrapper {
    flex: 1;
    padding: 10px 16px;
    background: #222;
    border-radius: 20px;
    cursor: pointer;

    .input-placeholder {
      color: #666;
      font-size: 14px;
    }
  }

  .action-btns {
    display: flex;
    align-items: center;
    gap: 16px;

    .action-item {
      display: flex;
      align-items: center;
      gap: 4px;
      color: #888;
      font-size: 13px;
      cursor: pointer;

      svg {
        width: 20px;
        height: 20px;
      }

      &.liked {
        color: #ff4757;
      }
    }
  }
}

// 评论弹窗
.comment-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: flex-end;
  z-index: 200;

  .comment-modal-content {
    width: 100%;
    background: #1a1a1a;
    border-radius: 16px 16px 0 0;
    padding: 16px;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    color: #fff;
    font-size: 16px;

    .close-btn {
      font-size: 24px;
      cursor: pointer;
      color: #888;
    }
  }

  textarea {
    width: 100%;
    background: #222;
    border: none;
    border-radius: 8px;
    padding: 12px;
    color: #fff;
    font-size: 14px;
    resize: none;
    outline: none;

    &::placeholder {
      color: #666;
    }
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 16px;

    button {
      padding: 10px 24px;
      border-radius: 20px;
      font-size: 14px;
      cursor: pointer;
    }

    .cancel-btn {
      background: #333;
      border: none;
      color: #888;
    }

    .submit-btn {
      background: linear-gradient(135deg, #a855f7, #7c3aed);
      border: none;
      color: #fff;

      &:disabled {
        opacity: 0.5;
      }
    }
  }
}

// 图片预览
.image-preview {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 300;

  img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
  }
}
</style>
