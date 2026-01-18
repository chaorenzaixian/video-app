<template>
  <div class="detail-page">
    <!-- 顶部导航 -->
    <div class="top-bar">
      <div class="back-btn" @click="goBack">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </div>
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
        <video 
          v-if="canPlayVideo" 
          ref="videoRef"
          :src="post.video_url" 
          controls 
          playsinline
        ></video>
        <div v-else class="video-locked">
          <div class="video-cover">
            <img :src="post.images?.[0] || '/images/default-cover.webp'" alt="封面" />
            <div class="video-overlay">
              <div class="vip-lock-text">本视频需要开通 VIP 预览</div>
              <div class="vip-buttons">
                <button class="buy-vip-btn" @click="goToVip">前往开通VIP</button>
                <button class="share-vip-btn" @click="shareForVip">邀请好友得VIP</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 评论区 -->
    <CommentsList
      :comments="comments"
      :comment-count="post?.comment_count || 0"
      :loading="loadingComments"
      :has-more="hasMoreComments"
      :post-id="postId"
      @like-comment="likeComment"
      @reply-comment="replyTo"
      @go-profile="goProfile"
      @preview-image="previewCommentImage"
    />

    <!-- 底部操作栏 -->
    <div class="bottom-bar">
      <div class="input-wrapper" @click="openCommentInput">
        <img :src="commentIcon" class="input-icon" />
        <span class="input-placeholder">请输入评论</span>
      </div>
      <div class="action-btns">
        <span class="action-item" @click="sharePost">
          <img :src="shareIcon" class="action-icon" />
          <span class="action-text">分享</span>
        </span>
        <span class="action-item" :class="{ active: post?.is_collected }" @click="collectPost">
          <img :src="post?.is_collected ? collectRedIcon : collectEmptyIcon" class="action-icon" />
          <span class="action-text">{{ formatCount(post?.collect_count || 0) }}</span>
        </span>
        <span class="action-item" :class="{ active: post?.is_liked }" @click="likePost">
          <img :src="post?.is_liked ? likeRedIcon : likeEmptyIcon" class="action-icon" />
          <span class="action-text">{{ formatCount(post?.like_count || 0) }}</span>
        </span>
      </div>
    </div>

    <!-- 评论输入弹窗 -->
    <CommentInput
      :visible="showCommentInput"
      :reply-target="replyTarget"
      @close="showCommentInput = false"
      @submit="submitComment"
    />

    <!-- 图片预览 -->
    <div class="image-preview" v-if="previewVisible" @click="previewVisible = false">
      <img :src="previewImageUrl" />
    </div>

    <!-- 分享弹窗 -->
    <Teleport to="body">
      <div class="share-modal-overlay" v-if="showShareModal" @click.self="showShareModal = false">
        <div class="share-modal-content">
          <button class="share-modal-close" @click="showShareModal = false">×</button>
          
          <div class="share-header">
            <img src="/images/backgrounds/ic_launcher.webp" alt="Logo" class="share-logo" />
            <div class="share-title-info">
              <h3 class="share-site-name">Soul成人版</h3>
              <p class="share-site-desc">全网最全成人视频平台</p>
            </div>
          </div>
          
          <div class="share-promo-image">
            <img :src="post?.images?.[0] || '/images/default-cover.webp'" alt="推广图" />
          </div>
          
          <div class="share-qr-section">
            <div class="share-qrcode">
              <img :src="shareQrCodeUrl" alt="二维码" />
            </div>
            <div class="share-invite-info">
              <div class="invite-code">邀请码 <span>{{ userInviteCode }}</span></div>
              <div class="official-url">官方网址:{{ shareBaseUrl }}</div>
            </div>
          </div>
          
          <div class="share-actions">
            <button class="copy-link-btn" @click="copyShareLink">复制链接</button>
            <button class="save-image-btn" @click="saveShareImage">保存图片</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'
import { getAvatarUrl } from '@/utils/avatar'
import CommentsList from '@/components/community/CommentsList.vue'
import CommentInput from '@/components/community/CommentInput.vue'

// 图标导入
import likeEmptyIcon from '@/assets/icons/like_empty.png'
import likeRedIcon from '@/assets/icons/like_red.png'
import collectEmptyIcon from '@/assets/icons/collect_empty.png'
import collectRedIcon from '@/assets/icons/collect_red.png'
import commentIcon from '@/assets/icons/comment.png'
import shareIcon from '@/assets/icons/share_grey.png'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 用于取消请求
const abortController = new AbortController()

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
const videoRef = ref(null)

// 判断用户是否是VIP
const isUserVip = computed(() => userStore.user?.is_vip || userStore.user?.vip_level > 0)

// 判断是否已购买该帖子视频
const hasPurchased = computed(() => post.value?.has_purchased || false)

// 判断是否可以播放视频
const canPlayVideo = computed(() => {
  // 如果没有视频，不需要判断
  if (!post.value?.video_url) return false
  // 如果是VIP用户，可以播放
  if (isUserVip.value) return true
  // 如果已购买，可以播放
  if (hasPurchased.value) return true
  // 默认不能播放（需要VIP）
  return false
})
const comments = ref([])
const replyTarget = ref(null)
const loadingComments = ref(false)
const hasMoreComments = ref(true)
const commentPage = ref(1)
const showCommentInput = ref(false)

// 分享相关
const showShareModal = ref(false)
const userInviteCode = ref('3AUUHR')
const shareBaseUrl = computed(() => window.location.origin.replace(/^https?:\/\//, ''))
const shareFullUrl = computed(() => `${window.location.origin}/user/community/${postId.value}?ref=${userInviteCode.value}`)
const shareQrCodeUrl = computed(() => `https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${encodeURIComponent(shareFullUrl.value)}`)

// 图片预览
const previewVisible = ref(false)
const previewImageUrl = ref('')

// 预览评论图片
const previewCommentImage = (url) => {
  previewImageUrl.value = url
  previewVisible.value = true
}

// 获取动态详情
const fetchPost = async () => {
  try {
    const res = await api.get(`/community/posts/${postId.value}`, {
      signal: abortController.signal
    })
    post.value = res.data
  } catch (e) {
    if (e.name !== 'AbortError') {
      console.error('获取动态失败', e)
    }
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
      params: { page: commentPage.value, page_size: 20 },
      signal: abortController.signal
    })
    const data = res.data || []
    if (data.length < 20) hasMoreComments.value = false
    comments.value = reset ? data : [...comments.value, ...data]
    commentPage.value++
  } catch (e) {
    if (e.name !== 'AbortError') {
      console.error('获取评论失败', e)
    }
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
  try {
    const res = await api.post(`/community/posts/${postId.value}/collect`)
    post.value.is_collected = res.data.collected
    post.value.collect_count = res.data.collect_count
    ElMessage.success(res.data.collected ? '收藏成功' : '已取消收藏')
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

// 分享
const sharePost = () => {
  showShareModal.value = true
}

// 复制分享链接
const copyShareLink = () => {
  navigator.clipboard.writeText(shareFullUrl.value).then(() => {
    ElMessage.success('分享链接已复制，分享给好友注册后可获得3日VIP')
  }).catch(() => {
    ElMessage.info('请复制链接分享：' + shareFullUrl.value)
  })
}

// 保存分享图片
const saveShareImage = () => {
  ElMessage.info('长按图片保存到相册')
}

// 返回上一页
const goBack = () => {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/user/community')
  }
}

// 分享获得VIP
const shareForVip = () => {
  showShareModal.value = true
}

// 跳转VIP页面
const goToVip = () => {
  router.push('/user/vip')
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
  if (comment._liking) return // 防止重复点击
  comment._liking = true
  try {
    const res = await api.post(`/community/comments/${comment.id}/like`)
    comment.is_liked = res.data.liked
    comment.like_count = res.data.like_count
  } catch (e) {
    console.error('点赞失败', e)
  } finally {
    comment._liking = false
  }
}

// 打开评论输入
const openCommentInput = () => {
  replyTarget.value = null
  showCommentInput.value = true
}

// 回复评论
const replyTo = (comment) => {
  console.log('replyTo called:', comment)
  replyTarget.value = comment
  showCommentInput.value = true
}

// 提交评论
const submitComment = async ({ content, image, replyTarget: target }) => {
  try {
    let imageUrl = null
    
    // 如果有图片，先上传
    if (image) {
      const formData = new FormData()
      formData.append('file', image)
      const uploadRes = await api.post('/community/upload/image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      imageUrl = uploadRes.data?.url || uploadRes.url
    }
    
    const payload = {
      content: content,
      images: imageUrl ? [imageUrl] : []
    }
    if (target) {
      payload.parent_id = target.parent_id || target.id
      payload.reply_to_user_id = target.user?.id
    }
    
    await api.post(`/community/posts/${postId.value}/comments`, payload)
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

// 组件卸载时取消所有请求
onBeforeUnmount(() => {
  abortController.abort()
})
</script>

<style lang="scss" scoped>
$breakpoint-lg: 768px;
$breakpoint-xl: 1024px;
$breakpoint-xxl: 1280px;

.detail-page {
  min-height: 100vh;
  background: #0d0d0d;
  padding-bottom: 70px;
  max-width: 100%;
  
  @media (min-width: $breakpoint-lg) {
    max-width: 650px;
    margin: 0 auto;
  }
  @media (min-width: $breakpoint-xl) {
    max-width: 750px;
  }
  @media (min-width: $breakpoint-xxl) {
    max-width: 850px;
  }
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
  
  @media (min-width: $breakpoint-lg) {
    max-width: 650px;
    margin: 0 auto;
  }
  @media (min-width: $breakpoint-xl) {
    max-width: 750px;
  }
  @media (min-width: $breakpoint-xxl) {
    max-width: 850px;
  }

  .title {
    color: #fff;
    font-size: 17px;
    font-weight: 500;
  }

  .placeholder {
    width: 36px;
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
  
  @media (min-width: $breakpoint-lg) {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    
    .post-image {
      margin-bottom: 0;
      aspect-ratio: 1;
      object-fit: cover;
    }
  }
}

.video-wrapper {
  position: relative;
  
  video {
    width: 100%;
    border-radius: 8px;
  }
  
  .video-locked {
    position: relative;
    border-radius: 8px;
    overflow: hidden;
    
    .video-cover {
      position: relative;
      
      img {
        width: 100%;
        height: auto;
        min-height: 200px;
        object-fit: cover;
        filter: blur(6px) brightness(0.6);
      }
      
      .video-overlay {
        position: absolute;
        inset: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 20px;
        
        .vip-lock-text {
          color: #fff;
          font-size: 16px;
          font-weight: 500;
        }
        
        .vip-buttons {
          display: flex;
          gap: 20px;
          
          button {
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            border: none;
          }
          
          .buy-vip-btn {
            background: linear-gradient(90deg, #f59e0b, #fbbf24);
            color: #000;
          }
          
          .share-vip-btn {
            background: linear-gradient(90deg, #8b5cf6, #a855f7);
            color: #fff;
          }
        }
      }
    }
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
  padding-bottom: calc(10px + env(safe-area-inset-bottom));
  background: #111;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  gap: 12px;
  
  @media (min-width: $breakpoint-lg) {
    max-width: 650px;
    left: 50%;
    transform: translateX(-50%);
  }
  @media (min-width: $breakpoint-xl) {
    max-width: 750px;
  }
  @media (min-width: $breakpoint-xxl) {
    max-width: 850px;
  }

  .input-wrapper {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    background: rgba(255, 255, 255, 0.06);
    border-radius: 20px;
    cursor: pointer;

    .input-icon {
      width: 20px;
      height: 20px;
      opacity: 0.6;
    }

    .input-placeholder {
      color: rgba(255, 255, 255, 0.4);
      font-size: 14px;
    }
  }

  .action-btns {
    display: flex;
    align-items: center;
    gap: 16px;

    .action-item {
      display: flex;
      flex-direction: row;
      align-items: center;
      gap: 4px;
      cursor: pointer;

      .action-icon {
        width: 26px;
        height: 26px;
      }

      .action-text {
        color: rgba(255, 255, 255, 0.5);
        font-size: 13px;
      }

      &.active .action-text {
        color: #ff6b6b;
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

/* 分享弹窗 */
.share-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10000;
  padding: 20px;
}

.share-modal-content {
  background: #1a1a2e;
  border-radius: 16px;
  width: 100%;
  max-width: 340px;
  padding: 24px 20px;
  position: relative;
}

.share-modal-close {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 28px;
  height: 28px;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  font-size: 20px;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  
  &:hover {
    background: rgba(255, 255, 255, 0.2);
  }
}

.share-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.share-logo {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  object-fit: cover;
}

.share-title-info {
  .share-site-name {
    font-size: 16px;
    font-weight: 600;
    color: #fff;
    margin: 0 0 2px 0;
  }
  .share-site-desc {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.6);
    margin: 0;
  }
}

.share-promo-image {
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 16px;
  
  img {
    width: 100%;
    height: auto;
    max-height: 200px;
    object-fit: cover;
    display: block;
  }
}

.share-qr-section {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.share-qrcode {
  flex-shrink: 0;
  background: #fff;
  padding: 6px;
  border-radius: 8px;
  
  img {
    width: 90px;
    height: 90px;
    border-radius: 4px;
    display: block;
  }
}

.share-invite-info {
  .invite-code {
    font-size: 16px;
    color: #fff;
    margin-bottom: 8px;
    
    span {
      font-weight: 700;
      color: #a855f7;
      margin-left: 6px;
    }
  }
  .official-url {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.6);
    word-break: break-all;
  }
}

.share-actions {
  display: flex;
  gap: 12px;
}

.copy-link-btn, .save-image-btn {
  flex: 1;
  padding: 12px 16px;
  border-radius: 50px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
  
  &:hover {
    opacity: 0.85;
  }
}

.copy-link-btn {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: #fff;
}

.save-image-btn {
  background: linear-gradient(90deg, #8b5cf6, #a855f7);
  border: none;
  color: #fff;
}
</style>
