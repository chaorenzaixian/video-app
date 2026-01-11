<template>
  <div class="gallery-detail-page">
    <header class="top-header">
      <button class="back-btn" @click="goBack">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </button>
      <h1 class="page-title">{{ gallery?.title }}({{ gallery?.image_count }}P)</h1>
      <div class="header-right"></div>
    </header>

    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="gallery" class="content-area">
      <div class="images-grid">
        <div v-for="(img, idx) in displayImages" :key="idx" class="image-item" @click="previewImage(idx)">
          <img :src="img" :alt="'图片' + (idx + 1)" />
        </div>
      </div>

      <div v-if="!isVip && gallery.image_count > 5" class="unlock-section">
        <p class="unlock-text">全本完整作品共{{ gallery.image_count }}张</p>
        <a class="unlock-link" @click="goToVip">开通会员解锁</a>
        <div class="unlock-tip">请先解锁即可查看大图</div>
      </div>
    </div>

    <div v-else class="error-state">
      <p>图集不存在或已被删除</p>
      <button class="back-btn-large" @click="goBack">返回</button>
    </div>

    <!-- 底部操作栏 -->
    <div class="action-bar" v-if="gallery">
      <button class="action-btn" :class="{ active: gallery.is_liked }" @click="toggleLike">
        <img :src="gallery.is_liked ? likeRedIcon : likeEmptyIcon" class="action-icon" />
        <span class="action-text">{{ gallery.like_count || 0 }}</span>
      </button>
      <button class="action-btn" @click="openComments">
        <img :src="commentIcon" class="action-icon" />
        <span class="action-text">{{ gallery.comment_count || 0 }}</span>
      </button>
      <button class="action-btn" :class="{ active: gallery.is_collected }" @click="toggleCollect">
        <img :src="gallery.is_collected ? collectRedIcon : collectEmptyIcon" class="action-icon" />
        <span class="action-text">{{ gallery.collect_count || 0 }}</span>
      </button>
      <button class="action-btn" @click="shareGallery">
        <img :src="shareIcon" class="action-icon" />
        <span class="action-text">分享</span>
      </button>
    </div>

    <!-- 图片预览弹窗 -->
    <div v-if="showPreview" class="preview-modal">
      <div class="preview-content">
        <div class="image-container" @dblclick="handleDoubleClick" @wheel.prevent="handleWheel">
          <img :src="previewImages[currentPreviewIndex]" alt="预览" :style="imageStyle" />
        </div>
        <div class="preview-index">{{ currentPreviewIndex + 1 }} / {{ previewImages.length }}</div>
        <button class="close-btn" @click="closePreview">×</button>
        <button class="nav-btn prev" v-if="currentPreviewIndex > 0" @click="prevImage"><img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" /></button>
        <button class="nav-btn next" v-if="currentPreviewIndex < previewImages.length - 1" @click="nextImage">›</button>
        <div class="zoom-hint" v-if="scale > 1">{{ Math.round(scale * 100) }}%</div>
      </div>
    </div>

    <!-- 评论弹窗 -->
    <div v-if="showComments" class="comments-modal" @click.self="closeComments">
      <div class="comments-panel">
        <!-- 拖动条 -->
        <div class="drag-handle"></div>
        
        <!-- 头部 -->
        <div class="comments-header">
          <span class="comment-count">{{ comments.length }}条评论</span>
          <div class="sort-tabs">
            <span class="sort-tab" :class="{ active: sortType === 'hot' }" @click="sortType = 'hot'">推荐</span>
            <span class="sort-divider">|</span>
            <span class="sort-tab" :class="{ active: sortType === 'new' }" @click="sortType = 'new'">最新</span>
          </div>
        </div>
        
        <!-- 评论列表 -->
        <div class="comments-list">
          <!-- 官方公告 -->
          <div v-if="announcement && announcement.enabled" class="comment-item official-announcement">
            <img :src="announcement.avatar || '/images/avatars/icon_avatar_1.webp'" class="comment-avatar" />
            <div class="comment-body">
              <div class="comment-user">
                <span class="official-name">{{ announcement.name }}</span>
                <img src="/images/backgrounds/super_vip_blue.webp" class="supreme-vip-icon" />
              </div>
              <div class="comment-text official-text">{{ announcement.content }}</div>
              <div class="comment-footer">
                <span class="comment-time">{{ formatAnnouncementTime(announcement.updated_at) }}</span>
              </div>
            </div>
          </div>
          
          <div v-if="comments.length === 0 && !(announcement && announcement.enabled)" class="no-comments">暂无评论</div>
          <div v-for="comment in comments" :key="comment.id" class="comment-item">
            <img :src="getAvatarUrl(comment.user_avatar, comment.user_id)" class="comment-avatar clickable" @click="goToUserProfile(comment.user_id)" />
            <div class="comment-body">
              <div class="comment-user">
                <span class="username clickable" @click="goToUserProfile(comment.user_id)">{{ comment.user_nickname || '用户' }}</span>
                <img v-if="comment.user_vip_level > 0" :src="getVipLevelIcon(comment.user_vip_level)" class="vip-badge-sm" />
              </div>
              <div class="comment-text">{{ comment.content }}</div>
              <!-- 评论图片 -->
              <div v-if="comment.image_url" class="comment-image" @click="previewCommentImage(comment.image_url)">
                <img :src="comment.image_url" alt="评论图片" />
              </div>
              <div class="comment-footer">
                <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
                <div class="comment-actions">
                  <span :class="['comment-like', { liked: comment.is_liked }]" @click="likeComment(comment)">
                    {{ comment.is_liked ? '❤️' : '🤍' }} {{ comment.like_count || 0 }}
                  </span>
                  <span class="comment-reply" @click="startReply(comment)">
                    <img :src="replyIcon" class="reply-icon" />
                  </span>
                </div>
              </div>
            </div>
          </div>
          <div v-if="comments.length > 0" class="no-more">没有更多数据了</div>
        </div>
        
        <!-- 简单输入框（点击展开完整输入） -->
        <div class="comment-input-trigger" @click="openInputPanel">
          <span class="input-placeholder">在这里写下你想说的...</span>
          <span class="char-count">0/500</span>
        </div>
        
        <!-- 底部工具栏 -->
        <div class="comment-toolbar">
          <div class="toolbar-left">
            <button class="toolbar-btn" @click="triggerImageUpload">
              <img :src="picIcon" class="toolbar-icon" />
            </button>
            <button class="toolbar-btn" @click="toggleEmojiPanel">
              <span class="emoji-icon">😊</span>
            </button>
          </div>
          <button class="toolbar-send" @click="openInputPanel">
            <img :src="sendIcon" class="send-icon" />
          </button>
        </div>
      </div>
    </div>
    
    <!-- 完整输入弹窗 -->
    <div v-if="showInputPanel" class="input-panel-modal" @click.self="closeInputPanel">
      <div class="input-panel">
        <div class="input-panel-header">
          <button class="cancel-btn" @click="closeInputPanel">取消</button>
          <span class="panel-title">发表评论</span>
          <button class="submit-btn" :disabled="!commentText.trim() && !commentImage" @click="submitComment">发送</button>
        </div>
        <div class="input-panel-body">
          <textarea 
            v-model="commentText" 
            class="full-input" 
            placeholder="在这里写下你想说的..." 
            maxlength="500"
            ref="textareaRef"
          ></textarea>
          <div class="char-counter">{{ commentText.length }}/500</div>
          <!-- 图片预览 -->
          <div v-if="commentImage" class="image-preview">
            <img :src="commentImagePreview" alt="预览" />
            <button class="remove-image" @click="removeCommentImage">×</button>
          </div>
        </div>
        <div class="input-panel-footer">
          <div class="footer-left">
            <button class="footer-btn" @click="triggerImageUpload">
              <img :src="picIcon" class="footer-icon" />
            </button>
            <button class="footer-btn" @click="toggleEmojiPanel">
              <span class="emoji-icon">😊</span>
            </button>
          </div>
        </div>
        <!-- 表情面板 -->
        <div v-if="showEmojiPanel" class="emoji-panel">
          <span v-for="emoji in emojis" :key="emoji" class="emoji-item" @click="insertEmoji(emoji)">{{ emoji }}</span>
        </div>
      </div>
    </div>
    
    <!-- 评论图片预览弹窗 -->
    <div v-if="showCommentImagePreview" class="comment-image-preview-modal" @click="closeCommentImagePreview">
      <div class="comment-image-preview-content">
        <img :src="commentImagePreviewUrl" alt="评论图片" />
        <button class="close-preview-btn" @click.stop="closeCommentImagePreview">×</button>
      </div>
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
            <img :src="gallery?.images?.[0] || '/images/default-cover.webp'" alt="推广图" />
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
    
    <!-- 隐藏的文件上传 -->
    <input type="file" ref="imageInput" accept="image/*" style="display:none" @change="handleImageSelect" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/utils/api'
import { ElMessage } from 'element-plus'

// 图标
import likeEmptyIcon from '@/assets/icons/like_empty.png'
import likeRedIcon from '@/assets/icons/like_red.png'
import collectEmptyIcon from '@/assets/icons/collect_empty.png'
import collectRedIcon from '@/assets/icons/collect_red.png'
import commentIcon from '@/assets/icons/comment.png'
import shareIcon from '@/assets/icons/share_grey.png'
import picIcon from '@/assets/icons/icon_pic_red.webp'
import sendIcon from '@/assets/icons/ic_send_red.webp'
import replyIcon from '@/assets/icons/msg_icon.png'
import { VIP_LEVEL_ICONS } from '@/constants/vip'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const gallery = ref(null)
const images = ref([])
const showPreview = ref(false)
const currentPreviewIndex = ref(0)
const scale = ref(1)
const translateX = ref(0)
const translateY = ref(0)
const freePreviewCount = 5

// 评论相关
const showComments = ref(false)
const comments = ref([])
const commentText = ref('')
const sortType = ref('hot')
const announcement = ref(null)
const showInputPanel = ref(false)
const showEmojiPanel = ref(false)
const commentImage = ref(null)
const commentImagePreview = ref('')
const imageInput = ref(null)
const textareaRef = ref(null)

// 表情列表
const emojis = ['😀', '😂', '🤣', '😍', '🥰', '😘', '😋', '🤤', '😎', '🤩', '😏', '😒', '😞', '😢', '😭', '😤', '😡', '🤬', '😱', '😨', '🥺', '😇', '🤗', '🤔', '🤫', '🤭', '🙄', '😴', '🤮', '🤧', '😷', '🤒', '👍', '👎', '👏', '🙌', '💪', '🤝', '❤️', '💔', '💯', '🔥', '⭐', '🎉', '🎊', '💐', '🌹', '🍀']

const isVip = computed(() => gallery.value?.is_vip === true)
const displayImages = computed(() => {
  const allImages = images.value || []
  return isVip.value ? allImages : allImages.slice(0, freePreviewCount)
})
const previewImages = computed(() => {
  const allImages = images.value || []
  return isVip.value ? allImages : allImages.slice(0, freePreviewCount)
})
const imageStyle = computed(() => ({
  transform: `translate(${translateX.value}px, ${translateY.value}px) scale(${scale.value})`,
  transition: scale.value === 1 ? 'transform 0.3s' : 'none'
}))

const fetchGallery = async () => {
  loading.value = true
  try {
    const id = route.params.id
    const res = await api.get(`/gallery-novel/gallery/${id}`)
    const data = res.data || res
    gallery.value = data
    images.value = data.images || []
  } catch (e) {
    console.error('获取图集详情失败', e)
    ElMessage.error('获取图集详情失败')
  } finally {
    loading.value = false
  }
}

const previewImage = (idx) => {
  if (!isVip.value) {
    ElMessage.warning('请先解锁即可查看大图')
    return
  }
  currentPreviewIndex.value = idx
  showPreview.value = true
  resetZoom()
}

const closePreview = () => { showPreview.value = false; resetZoom() }
const prevImage = () => { if (currentPreviewIndex.value > 0) { currentPreviewIndex.value--; resetZoom() } }
const nextImage = () => { if (currentPreviewIndex.value < previewImages.value.length - 1) { currentPreviewIndex.value++; resetZoom() } }
const resetZoom = () => { scale.value = 1; translateX.value = 0; translateY.value = 0 }
const handleDoubleClick = () => { scale.value > 1 ? resetZoom() : scale.value = 2.5 }
const handleWheel = (e) => { const delta = e.deltaY > 0 ? -0.3 : 0.3; scale.value = Math.max(1, Math.min(5, scale.value + delta)); if (scale.value === 1) resetZoom() }

const toggleLike = async () => {
  try {
    const res = await api.post(`/gallery-novel/gallery/${gallery.value.id}/like`)
    gallery.value.is_liked = res.data.liked
    gallery.value.like_count = res.data.like_count
  } catch (e) { ElMessage.error('操作失败') }
}

const toggleCollect = async () => {
  try {
    const res = await api.post(`/gallery-novel/gallery/${gallery.value.id}/collect`)
    gallery.value.is_collected = res.data.collected
    if (res.data.collected) gallery.value.collect_count = (gallery.value.collect_count || 0) + 1
    else gallery.value.collect_count = Math.max(0, (gallery.value.collect_count || 0) - 1)
    ElMessage.success(res.data.collected ? '收藏成功' : '已取消收藏')
  } catch (e) { ElMessage.error('操作失败') }
}

// 评论功能
const openComments = async () => {
  showComments.value = true
  await Promise.all([fetchComments(), fetchAnnouncement()])
}

const closeComments = () => {
  showComments.value = false
}

const fetchComments = async () => {
  try {
    const res = await api.get(`/gallery-novel/gallery/${gallery.value.id}/comments`)
    comments.value = res.data || []
  } catch (e) {
    comments.value = []
  }
}

// 获取评论区公告
const fetchAnnouncement = async () => {
  try {
    const res = await api.get('/settings/comment-announcement')
    announcement.value = res.data || res
  } catch (e) {
    console.log('获取公告失败:', e)
  }
}

const submitComment = async () => {
  if (!commentText.value.trim() && !commentImage.value) return
  try {
    let response
    if (commentImage.value) {
      // 有图片时使用 FormData
      const formData = new FormData()
      formData.append('content', commentText.value || '')
      formData.append('image', commentImage.value)
      response = await api.post(`/gallery-novel/gallery/${gallery.value.id}/comment`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
    } else {
      // 纯文字使用 JSON
      response = await api.post(`/gallery-novel/gallery/${gallery.value.id}/comment`, {
        content: commentText.value
      })
    }
    commentText.value = ''
    commentImage.value = null
    commentImagePreview.value = ''
    showInputPanel.value = false
    showEmojiPanel.value = false
    await fetchComments()
    gallery.value.comment_count = (gallery.value.comment_count || 0) + 1
    ElMessage.success('评论成功')
  } catch (e) {
    console.error('评论失败:', e)
    ElMessage.error(e.response?.data?.detail || '评论失败')
  }
}

// 输入面板
const openInputPanel = () => {
  showInputPanel.value = true
  showEmojiPanel.value = false
  setTimeout(() => textareaRef.value?.focus(), 100)
}

const closeInputPanel = () => {
  showInputPanel.value = false
  showEmojiPanel.value = false
}

// 表情面板
const toggleEmojiPanel = () => {
  // 如果输入面板没打开，先打开
  if (!showInputPanel.value) {
    showInputPanel.value = true
    setTimeout(() => {
      showEmojiPanel.value = true
    }, 100)
  } else {
    showEmojiPanel.value = !showEmojiPanel.value
  }
}

const insertEmoji = (emoji) => {
  commentText.value += emoji
}

// 图片上传
const triggerImageUpload = () => {
  imageInput.value?.click()
}

const handleImageSelect = (e) => {
  const file = e.target.files?.[0]
  if (file) {
    if (file.size > 5 * 1024 * 1024) {
      ElMessage.warning('图片大小不能超过5MB')
      return
    }
    commentImage.value = file
    commentImagePreview.value = URL.createObjectURL(file)
    if (!showInputPanel.value) {
      openInputPanel()
    }
  }
  e.target.value = ''
}

const removeCommentImage = () => {
  commentImage.value = null
  commentImagePreview.value = ''
}

// 预览评论图片
const commentImagePreviewUrl = ref('')
const showCommentImagePreview = ref(false)

const previewCommentImage = (url) => {
  commentImagePreviewUrl.value = url
  showCommentImagePreview.value = true
}

const closeCommentImagePreview = () => {
  showCommentImagePreview.value = false
  commentImagePreviewUrl.value = ''
}

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = (now - date) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + '小时前'
  return date.toLocaleDateString()
}

// 格式化公告时间
const formatAnnouncementTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const goToVip = () => router.push('/user/vip')

// 返回图集列表页
const goBack = () => {
  router.push('/user/community?tab=gallery')
}

// 分享相关
const showShareModal = ref(false)
const userInviteCode = ref('3AUUHR')
const shareBaseUrl = computed(() => window.location.origin.replace(/^https?:\/\//, ''))
const shareFullUrl = computed(() => `${window.location.origin}/user/gallery/${gallery.value?.id}?ref=${userInviteCode.value}`)
const shareQrCodeUrl = computed(() => `https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${encodeURIComponent(shareFullUrl.value)}`)

const shareGallery = () => {
  showShareModal.value = true
}

const copyShareLink = () => {
  navigator.clipboard.writeText(shareFullUrl.value).then(() => {
    ElMessage.success('分享链接已复制，分享给好友注册后可获得3日VIP')
  }).catch(() => {
    ElMessage.info('请复制链接分享：' + shareFullUrl.value)
  })
}

const saveShareImage = () => {
  ElMessage.info('长按图片保存到相册')
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

// 根据用户ID获取头像
const getAvatarUrl = (avatar, userId) => {
  if (avatar) return avatar
  const numericId = parseInt(userId) || 1
  return getDefaultAvatarPath(numericId)
}

// 获取VIP等级图标
const getVipLevelIcon = (level) => {
  return VIP_LEVEL_ICONS[level] || ''
}

// 评论点赞
const likeComment = async (comment) => {
  try {
    const res = await api.post(`/gallery-novel/comment/${comment.id}/like`)
    comment.is_liked = res.data.liked
    comment.like_count = res.data.like_count
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

// 回复评论
const replyToComment = ref(null)
const startReply = (comment) => {
  replyToComment.value = comment
  commentText.value = `@${comment.user_nickname || '用户'} `
  openInputPanel()
}

// 跳转用户主页
const goToUserProfile = (userId) => {
  if (userId) {
    router.push(`/user/profile/${userId}`)
  }
}

onMounted(() => fetchGallery())
</script>

<style lang="scss" scoped>
.gallery-detail-page { min-height: 100vh; background: #000; padding-bottom: 70px; }
.top-header { display: flex; align-items: center; padding: 12px 16px; background: #000; position: sticky; top: 0; z-index: 100; }
.back-btn { background: none; border: none; color: #fff; font-size: 28px; cursor: pointer; padding: 4px 12px 4px 0; }
.page-title { color: #fff; font-size: 17px; font-weight: 500; flex: 1; }
.header-right { width: 40px; }
.loading-state, .error-state { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 20px; color: #888; }
.loading-spinner { width: 40px; height: 40px; border: 3px solid #1a2a4a; border-top-color: #3b82f6; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.content-area { padding: 0 8px; }
.images-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px; }
.image-item { aspect-ratio: 3/4; border-radius: 4px; overflow: hidden; cursor: pointer; }
.image-item img { width: 100%; height: 100%; object-fit: cover; }
.unlock-section { text-align: center; padding: 30px 20px; }
.unlock-text { color: #8899aa; font-size: 14px; margin-bottom: 12px; }
.unlock-link { display: block; color: #3b82f6; font-size: 15px; cursor: pointer; text-decoration: underline; margin-bottom: 16px; }
.unlock-tip { padding: 12px 24px; background: rgba(255, 255, 255, 0.1); border-radius: 8px; color: #8899aa; font-size: 14px; display: inline-block; }

.action-bar { position: fixed; bottom: 0; left: 0; right: 0; display: flex; justify-content: space-around; padding: 16px 20px; background: #000; border-top: 1px solid #222; }
.action-btn { display: flex; flex-direction: column; align-items: center; gap: 6px; background: none; border: none; color: #999; cursor: pointer; padding: 4px 16px; }
.action-btn.active { color: #f43f5e; }
.action-icon { width: 28px; height: 28px; }
.action-text { font-size: 13px; color: #888; }

.preview-modal { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.95); z-index: 200; }
.preview-content { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; position: relative; }
.image-container { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; overflow: hidden; }
.image-container img { max-width: 100%; max-height: 90vh; object-fit: contain; user-select: none; }
.preview-index { position: absolute; bottom: 40px; left: 50%; transform: translateX(-50%); color: #fff; font-size: 14px; background: rgba(0, 0, 0, 0.5); padding: 6px 16px; border-radius: 20px; }
.close-btn { position: absolute; top: 20px; right: 20px; background: rgba(0, 0, 0, 0.5); border: none; color: #fff; font-size: 28px; width: 44px; height: 44px; border-radius: 50%; cursor: pointer; }
.nav-btn { position: absolute; top: 50%; transform: translateY(-50%); background: rgba(255, 255, 255, 0.2); border: none; color: #fff; font-size: 36px; width: 50px; height: 80px; cursor: pointer; }
.nav-btn.prev { left: 10px; border-radius: 0 8px 8px 0; }
.nav-btn.next { right: 10px; border-radius: 8px 0 0 8px; }
.zoom-hint { position: absolute; top: 20px; left: 50%; transform: translateX(-50%); background: rgba(0, 0, 0, 0.7); color: #fff; padding: 6px 16px; border-radius: 20px; font-size: 14px; }
.back-btn-large { margin-top: 20px; padding: 12px 32px; background: #3b82f6; color: #fff; border: none; border-radius: 8px; cursor: pointer; }

/* 评论弹窗 */
.comments-modal { 
  position: fixed; 
  inset: 0; 
  background: rgba(0, 0, 0, 0.5); 
  z-index: 300; 
  display: flex; 
  align-items: flex-end; 
}
.comments-panel { 
  width: 100%; 
  max-height: 70vh; 
  background: #000; 
  border-radius: 16px 16px 0 0; 
  display: flex; 
  flex-direction: column; 
}
.drag-handle {
  width: 40px;
  height: 4px;
  background: #3a4a5a;
  border-radius: 2px;
  margin: 10px auto;
}
.comments-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  padding: 12px 20px; 
  border-bottom: 1px solid #222; 
}
.comment-count {
  color: #8899aa;
  font-size: 14px;
}
.sort-tabs {
  display: flex;
  align-items: center;
  gap: 8px;
}
.sort-tab {
  color: #556677;
  font-size: 14px;
  cursor: pointer;
  padding: 4px 8px;
}
.sort-tab.active {
  color: #fff;
}
.sort-divider {
  color: #334455;
  font-size: 12px;
}
.comments-list { 
  flex: 1; 
  overflow-y: auto; 
  padding: 16px 20px; 
  min-height: 200px; 
}
.no-comments { 
  text-align: center; 
  color: #556677; 
  padding: 40px 0; 
}
.no-more {
  text-align: center;
  color: #445566;
  font-size: 12px;
  padding: 20px 0;
}
.comment-item { 
  display: flex; 
  gap: 12px; 
  margin-bottom: 20px; 
}
.comment-avatar { 
  width: 40px; 
  height: 40px; 
  border-radius: 50%; 
  object-fit: cover;
  flex-shrink: 0;
}
.clickable {
  cursor: pointer;
}
.comment-body { 
  flex: 1; 
  min-width: 0;
}
.comment-user { 
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px; 
}
.username {
  background: linear-gradient(90deg, #ffd700, #ffaa00);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 13px;
  font-weight: 500;
}
.vip-badge-sm {
  height: 18px;
  width: auto;
  object-fit: contain;
}
.comment-text { 
  color: #fff; 
  font-size: 14px; 
  line-height: 1.5;
  word-break: break-word;
}
.comment-image {
  margin-top: 8px;
  cursor: pointer;
  
  img {
    max-width: 150px;
    max-height: 150px;
    border-radius: 8px;
    object-fit: cover;
  }
}
.comment-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}
.comment-time { 
  color: #556677; 
  font-size: 12px; 
}
.comment-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}
.comment-like, .comment-reply {
  color: #556677;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}
.comment-like.liked {
  color: #f43f5e;
}
.reply-icon {
  width: 16px;
  height: 16px;
  opacity: 0.6;
}

/* 官方公告样式 */
.official-announcement {
  .comment-user {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  
  .official-name {
    color: #ffd700;
    font-weight: 500;
  }
  
  .supreme-vip-icon {
    height: 18px;
    width: auto;
    object-fit: contain;
  }
  
  .official-text {
    color: #a78bfa;
  }
}

/* 评论输入触发区 */
.comment-input-trigger {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #1a1a1a;
  border-radius: 8px;
  margin: 0 16px 12px;
  cursor: pointer;
}
.input-placeholder {
  color: #556677;
  font-size: 14px;
}
.char-count {
  color: #445566;
  font-size: 12px;
}

/* 底部工具栏 */
.comment-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-top: 1px solid #222;
  background: #000;
}
.toolbar-left {
  display: flex;
  gap: 16px;
}
.toolbar-btn {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
}
.toolbar-icon {
  width: 28px;
  height: 28px;
}
.emoji-icon {
  font-size: 24px;
}
.toolbar-send {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
}
.send-icon {
  width: 28px;
  height: 28px;
}

/* 完整输入面板 */
.input-panel-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  z-index: 400;
  display: flex;
  align-items: flex-end;
}
.input-panel {
  width: 100%;
  background: #000;
  border-radius: 16px 16px 0 0;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}
.input-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid #222;
}
.cancel-btn {
  background: none;
  border: none;
  color: #8899aa;
  font-size: 14px;
  cursor: pointer;
}
.panel-title {
  color: #fff;
  font-size: 16px;
  font-weight: 500;
}
.submit-btn {
  background: linear-gradient(135deg, #8b5cf6, #a855f7);
  color: #fff;
  border: none;
  padding: 6px 16px;
  border-radius: 16px;
  font-size: 14px;
  cursor: pointer;
}
.submit-btn:disabled {
  background: #334455;
  color: #667788;
  cursor: not-allowed;
}
.input-panel-body {
  padding: 16px;
  flex: 1;
}
.full-input {
  width: 100%;
  min-height: 120px;
  background: transparent;
  border: none;
  color: #fff;
  font-size: 15px;
  line-height: 1.6;
  resize: none;
  outline: none;
}
.full-input::placeholder {
  color: #556677;
}
.char-counter {
  text-align: right;
  color: #556677;
  font-size: 12px;
  margin-top: 8px;
}
.image-preview {
  position: relative;
  display: inline-block;
  margin-top: 12px;
}
.image-preview img {
  max-width: 120px;
  max-height: 120px;
  border-radius: 8px;
  object-fit: cover;
}
.remove-image {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  background: #e53935;
  color: #fff;
  border: none;
  border-radius: 50%;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.input-panel-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-top: 1px solid #222;
}
.footer-left {
  display: flex;
  gap: 16px;
}
.footer-btn {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
}
.footer-icon {
  width: 28px;
  height: 28px;
}

/* 表情面板 */
.emoji-panel {
  padding: 12px 16px;
  background: #000;
  border-top: 1px solid #222;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
}
.emoji-item {
  font-size: 24px;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background 0.2s;
}
.emoji-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

/* 评论图片预览弹窗 */
.comment-image-preview-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.95);
  z-index: 500;
  display: flex;
  align-items: center;
  justify-content: center;
}
.comment-image-preview-content {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  
  img {
    max-width: 90vw;
    max-height: 90vh;
    object-fit: contain;
  }
}
.close-preview-btn {
  position: absolute;
  top: -40px;
  right: 0;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: #fff;
  font-size: 28px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
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
