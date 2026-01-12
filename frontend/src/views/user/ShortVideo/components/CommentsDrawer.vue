<template>
  <div class="comments-drawer" v-if="visible" @click.self="$emit('close')">
    <div class="drawer-content">
      <div class="drawer-header">
        <span class="comment-count">{{ video?.comment_count || 0 }} 条评论</span>
        <span class="close-btn" @click="$emit('close')">×</span>
      </div>
      
      <div class="comments-list">
        <!-- 官方公告 -->
        <div v-if="announcement?.enabled" class="comment-item official-announcement">
          <img :src="announcement.avatar || '/images/avatars/icon_avatar_1.webp'" class="comment-avatar" />
          <div class="comment-body">
            <div class="comment-user">
              <span class="username official-name">{{ announcement.name }}</span>
              <img src="/images/backgrounds/super_vip_blue.webp" class="supreme-vip-icon" />
            </div>
            <div class="comment-text official-text">{{ announcement.content }}</div>
            <div class="comment-meta">
              <span class="time">{{ formatAnnouncementTime(announcement.updated_at) }}</span>
            </div>
          </div>
        </div>
        
        <div v-for="comment in comments" :key="comment.id" class="comment-item">
          <img :src="getAvatarUrl(comment.user_avatar, comment.user_id)" class="comment-avatar clickable" @click="$emit('go-profile', comment.user_id)" />
          <div class="comment-body">
            <div class="comment-user">
              <span class="username clickable" @click="$emit('go-profile', comment.user_id)">{{ comment.user_nickname || comment.user_name }}</span>
              <img v-if="comment.user_vip_level > 0" :src="getVipLevelIcon(comment.user_vip_level)" class="vip-badge-sm" />
            </div>
            <div class="comment-text">{{ comment.content }}</div>
            <div v-if="comment.image_url" class="comment-image" @click="previewImage(comment.image_url)">
              <img :src="comment.image_url" alt="comment image" />
            </div>
            <div class="comment-meta">
              <span class="time">{{ formatCommentTime(comment.created_at) }}</span>
              <span class="reply-btn" @click.stop="setReplyTo(comment)">回复</span>
              <span :class="['like-btn', { liked: comment.is_liked }]" @click.stop="likeComment(comment)">
                {{ comment.is_liked ? '❤️' : '🤍' }} {{ comment.like_count || 0 }}
              </span>
            </div>
            
            <!-- 回复列表 -->
            <div v-if="comment.reply_count > 0" class="replies-section">
              <div v-if="!comment.showReplies" class="view-replies-btn" @click.stop="loadReplies(comment)">
                查看 {{ comment.reply_count }} 条回复 ▼
              </div>
              <div v-else class="replies-list">
                <div v-for="reply in comment.replies" :key="reply.id" class="reply-item">
                  <img :src="getAvatarUrl(reply.user_avatar, reply.user_id)" class="reply-avatar clickable" @click="$emit('go-profile', reply.user_id)" />
                  <div class="reply-body">
                    <div class="reply-user">
                      <span class="username clickable" @click="$emit('go-profile', reply.user_id)">{{ reply.user_nickname || reply.user_name }}</span>
                      <img v-if="reply.user_vip_level > 0" :src="getVipLevelIcon(reply.user_vip_level)" class="vip-badge-xs" />
                    </div>
                    <div class="reply-text">{{ reply.content }}</div>
                    <div v-if="reply.image_url" class="reply-image" @click="previewImage(reply.image_url)">
                      <img :src="reply.image_url" alt="reply image" />
                    </div>
                    <div class="reply-meta">
                      <span class="time">{{ formatCommentTime(reply.created_at) }}</span>
                      <span class="reply-btn" @click.stop="setReplyTo(comment, reply)">回复</span>
                      <span :class="['like-btn', { liked: reply.is_liked }]" @click.stop="likeComment(reply)">
                        {{ reply.is_liked ? '❤️' : '🤍' }} {{ reply.like_count || 0 }}
                      </span>
                    </div>
                  </div>
                </div>
                <div class="hide-replies-btn" @click.stop="comment.showReplies = false">收起回复 ▲</div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="empty-comments" v-if="comments.length === 0">暂无评论，快来抢沙发~</div>
      </div>
      
      <!-- 评论输入区 -->
      <div class="comment-input-bar">
        <div v-if="!isVip" class="vip-comment-tip" @click="$emit('go-vip')">
          <span class="tip-icon">👑</span>
          <span class="tip-text">开通VIP即可发表评论</span>
          <span class="tip-btn">立即开通 ›</span>
        </div>
        
        <div v-else class="input-area">
          <div v-if="replyTo" class="reply-hint">
            <span>回复 @{{ replyTo.user_nickname || replyTo.user_name }}</span>
            <span class="cancel-reply" @click="cancelReply">×</span>
          </div>
          
          <div v-if="commentImage" class="image-preview">
            <img :src="commentImagePreview" alt="preview" />
            <span class="remove-image" @click="removeImage">×</span>
          </div>
          
          <div class="input-row">
            <input type="text" v-model="commentText" :placeholder="replyTo ? `回复 @${replyTo.user_nickname || replyTo.user_name}` : '说点什么吧...'" @keyup.enter="submitComment" ref="inputRef" />
            <div class="input-actions">
              <span class="emoji-btn" @click="showEmojiPicker = !showEmojiPicker">😊</span>
              <label class="image-btn">
                <input type="file" accept="image/*" @change="handleImageSelect" hidden />🖼️
              </label>
              <span class="send-btn" @click="submitComment" :class="{ disabled: submitting }">
                <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
              </span>
            </div>
          </div>
          
          <div v-if="showEmojiPicker" class="emoji-picker">
            <div class="emoji-grid">
              <span v-for="emoji in emojiList" :key="emoji" class="emoji-item" @click="insertEmoji(emoji)">{{ emoji }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'
import { VIP_LEVEL_ICONS } from '@/constants/vip'

const props = defineProps({
  visible: { type: Boolean, default: false },
  video: { type: Object, default: null },
  isVip: { type: Boolean, default: false }
})

const emit = defineEmits(['close', 'go-profile', 'go-vip', 'comment-added'])

const comments = ref([])
const announcement = ref(null)
const commentText = ref('')
const commentImage = ref(null)
const commentImagePreview = ref('')
const submitting = ref(false)
const replyTo = ref(null)
const replyParentId = ref(null)
const showEmojiPicker = ref(false)
const inputRef = ref(null)

const emojiList = ['😀', '😂', '🤣', '😊', '😍', '🥰', '😘', '😜', '🤪', '😎', '🥳', '😇', '🤩', '😋', '😛', '🤤', '😏', '😒', '😔', '😢', '😭', '😤', '😠', '🤬', '😱', '😰', '😥', '🤧', '😷', '🤒', '👍', '👎', '👏', '🙏', '💪', '❤️', '💔', '💯', '🔥', '✨', '🎉', '🎊', '💎', '🏆', '🥇', '⭐', '🌟', '💫', '🌈', '☀️']

// 加载评论
const loadComments = async () => {
  if (!props.video) return
  try {
    const [commentsRes, announcementRes] = await Promise.all([
      api.get(`/comments/video/${props.video.id}`),
      api.get('/settings/comment-announcement').catch(() => null)
    ])
    comments.value = commentsRes.data?.items || commentsRes.data || []
    if (announcementRes) announcement.value = announcementRes.data || announcementRes
  } catch (error) {
    console.error('获取评论失败:', error)
  }
}

// 提交评论
const submitComment = async () => {
  if ((!commentText.value.trim() && !commentImage.value) || !props.video) return
  if (submitting.value) return
  if (!props.isVip) {
    ElMessage.warning('请先开通VIP会员才能发表评论')
    return
  }
  
  submitting.value = true
  try {
    let imageUrl = null
    if (commentImage.value) {
      const formData = new FormData()
      formData.append('file', commentImage.value)
      const uploadRes = await api.post('/comments/upload-image', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
      imageUrl = uploadRes.data?.url || uploadRes.url
    }
    
    const commentData = { content: commentText.value, video_id: props.video.id, image_url: imageUrl }
    if (replyParentId.value) commentData.parent_id = replyParentId.value
    
    await api.post('/comments', commentData)
    ElMessage.success(replyParentId.value ? '回复成功' : '评论成功')
    commentText.value = ''
    commentImage.value = null
    commentImagePreview.value = ''
    showEmojiPicker.value = false
    cancelReply()
    emit('comment-added')
    await loadComments()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '评论失败')
  } finally {
    submitting.value = false
  }
}

// 点赞评论
const likeComment = async (comment) => {
  try {
    const res = await api.post(`/comments/${comment.id}/like`)
    comment.is_liked = !comment.is_liked
    comment.like_count = res.data?.like_count || res.like_count
  } catch (error) {
    if (error.response?.status === 401) ElMessage.warning('请先登录后再点赞')
  }
}

// 加载回复
const loadReplies = async (comment) => {
  try {
    const res = await api.get(`/comments/replies/${comment.id}`)
    comment.replies = res.data?.items || res.data || []
    comment.showReplies = true
  } catch (error) {
    ElMessage.error('加载回复失败')
  }
}

// 设置回复目标
const setReplyTo = (comment, reply = null) => {
  replyTo.value = reply || comment
  replyParentId.value = comment.id
  nextTick(() => inputRef.value?.focus())
}

const cancelReply = () => { replyTo.value = null; replyParentId.value = null }
const insertEmoji = (emoji) => { commentText.value += emoji; showEmojiPicker.value = false; inputRef.value?.focus() }
const previewImage = (url) => window.open(url, '_blank')

const handleImageSelect = (e) => {
  const file = e.target.files[0]
  if (!file) return
  if (file.size > 5 * 1024 * 1024) { ElMessage.warning('图片大小不能超过5MB'); return }
  if (!file.type.startsWith('image/')) { ElMessage.warning('请选择图片文件'); return }
  commentImage.value = file
  commentImagePreview.value = URL.createObjectURL(file)
}

const removeImage = () => { commentImage.value = null; commentImagePreview.value = '' }
const getVipLevelIcon = (level) => VIP_LEVEL_ICONS[level] || ''

const getAvatarUrl = (avatar, userId) => {
  if (avatar) {
    if (avatar.startsWith('/') || avatar.startsWith('http')) return avatar
    return '/' + avatar
  }
  const index = (parseInt(userId) || 1) % 52
  if (index < 17) return `/images/avatars/icon_avatar_${index + 1}.webp`
  if (index < 32) return `/images/avatars/DM_20251217202131_${String(index - 17 + 1).padStart(3, '0')}.JPEG`
  return `/images/avatars/DM_20251217202341_${String(index - 32 + 1).padStart(3, '0')}.JPEG`
}

const formatCommentTime = (date) => {
  if (!date) return ''
  const d = new Date(date), now = new Date()
  const diff = now.getTime() - d.getTime()
  const mins = Math.floor(diff / 60000), hrs = Math.floor(diff / 3600000), days = Math.floor(diff / 86400000)
  if (mins < 1) return '刚刚'
  if (mins < 60) return `${mins}分钟前`
  if (hrs < 24) return `${hrs}小时前`
  if (days < 7) return `${days}天前`
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const formatAnnouncementTime = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

defineExpose({ loadComments })
</script>

<style lang="scss" scoped>
.comments-drawer {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  z-index: 200;
  display: flex;
  align-items: flex-end;
  
  .drawer-content {
    width: 100%;
    height: 70vh;
    background: #0a0a0a;
    border-radius: 16px 16px 0 0;
    display: flex;
    flex-direction: column;
  }
  
  .drawer-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    
    .comment-count { font-size: 15px; color: #fff; }
    .close-btn { font-size: 24px; color: rgba(255,255,255,0.6); cursor: pointer; }
  }
  
  .comments-list {
    flex: 1;
    overflow-y: auto;
    padding: 16px 20px;
    
    .comment-item {
      display: flex;
      gap: 10px;
      padding: 16px 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      
      .comment-avatar {
        width: 36px; height: 36px; border-radius: 50%; object-fit: cover; flex-shrink: 0;
        &.clickable { cursor: pointer; &:hover { opacity: 0.8; } }
      }
      
      .comment-body {
        flex: 1; min-width: 0;
        
        .comment-user {
          display: flex; align-items: center; gap: 6px; margin-bottom: 8px;
          .username {
            font-size: 13px; font-weight: 600;
            background: linear-gradient(135deg, #ffd700 0%, #ffec8b 50%, #daa520 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            &.clickable { cursor: pointer; &:hover { opacity: 0.8; } }
          }
          .vip-badge-sm { height: 18px; width: auto; }
        }
        
        .comment-text { font-size: 14px; color: rgba(255, 255, 255, 0.9); line-height: 1.6; margin: 0 0 10px; word-break: break-word; }
        .comment-image { margin: 10px 0;
          img { max-width: 200px; max-height: 200px; border-radius: 8px; cursor: pointer; }
        }
        
        .comment-meta {
          display: flex; gap: 20px; align-items: center;
          .time { font-size: 12px; color: rgba(255, 255, 255, 0.35); }
          .reply-btn { font-size: 12px; color: rgba(255, 255, 255, 0.5); cursor: pointer; &:hover { color: #fe2c55; } }
          .like-btn { font-size: 12px; color: rgba(255, 255, 255, 0.45); cursor: pointer; &.liked { color: #ff6b6b; } }
        }
        
        .replies-section {
          margin-top: 10px;
          .view-replies-btn, .hide-replies-btn { font-size: 12px; color: #fe2c55; cursor: pointer; padding: 5px 0; }
          .replies-list {
            .reply-item {
              display: flex; gap: 10px; padding: 10px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05);
              &:last-of-type { border-bottom: none; }
              .reply-avatar { width: 28px; height: 28px; border-radius: 50%; &.clickable { cursor: pointer; } }
              .reply-body {
                flex: 1;
                .reply-user { display: flex; align-items: center; gap: 4px; margin-bottom: 4px;
                  .username { font-size: 12px; color: rgba(255, 255, 255, 0.6); }
                  .vip-badge-xs { height: 12px; }
                }
                .reply-text { font-size: 13px; color: rgba(255, 255, 255, 0.9); line-height: 1.5; }
                .reply-image { margin-top: 8px; img { max-width: 120px; max-height: 120px; border-radius: 6px; cursor: pointer; } }
                .reply-meta { display: flex; gap: 15px; margin-top: 6px;
                  .time { font-size: 11px; color: rgba(255, 255, 255, 0.3); }
                  .reply-btn { font-size: 11px; color: rgba(255, 255, 255, 0.5); cursor: pointer; }
                  .like-btn { font-size: 11px; color: rgba(255, 255, 255, 0.4); &.liked { color: #ff6b6b; } }
                }
              }
            }
          }
        }
      }
    }
    
    .empty-comments { text-align: center; padding: 40px; color: rgba(255,255,255,0.5); }
    
    .official-announcement {
      .comment-user {
        .official-name { background: linear-gradient(90deg, #a855f7, #c084fc, #e879f9); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .supreme-vip-icon { height: 18px; margin-left: 2px; filter: drop-shadow(0 0 6px rgba(168, 85, 247, 0.8)); }
      }
      .official-text { color: #c084fc; }
    }
  }
  
  .comment-input-bar {
    background: linear-gradient(180deg, rgba(10, 10, 10, 0.95) 0%, rgba(5, 5, 5, 1) 100%);
    padding: 12px 16px;
    padding-bottom: calc(12px + env(safe-area-inset-bottom, 0px));
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    
    .vip-comment-tip {
      display: flex; align-items: center; justify-content: center; gap: 10px;
      background: linear-gradient(135deg, rgba(255, 215, 0, 0.15), rgba(255, 165, 0, 0.1));
      border: 1px solid rgba(255, 215, 0, 0.3); border-radius: 25px; padding: 12px 20px; cursor: pointer;
      .tip-icon { font-size: 18px; }
      .tip-text { font-size: 14px; color: rgba(255, 215, 0, 0.9); }
      .tip-btn { font-size: 13px; color: #ffd700; font-weight: 600; }
    }
    
    .input-area {
      .reply-hint {
        display: flex; align-items: center; justify-content: space-between;
        padding: 8px 12px; margin-bottom: 8px; background: rgba(254, 44, 85, 0.1);
        border-radius: 8px; font-size: 12px; color: #fe2c55;
        .cancel-reply { width: 18px; height: 18px; display: flex; align-items: center; justify-content: center; background: rgba(255, 255, 255, 0.1); border-radius: 50%; cursor: pointer; }
      }
      
      .image-preview {
        position: relative; margin-bottom: 10px; display: inline-block;
        img { max-width: 100px; max-height: 100px; border-radius: 8px; }
        .remove-image { position: absolute; top: -8px; right: -8px; width: 20px; height: 20px; background: #ff4757; color: #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; }
      }
      
      .input-row {
        display: flex; align-items: center; gap: 10px;
        background: rgba(255, 255, 255, 0.06); border-radius: 20px; padding: 6px 12px;
        input { flex: 1; background: transparent; border: none; color: #fff; font-size: 14px; outline: none; &::placeholder { color: rgba(255, 255, 255, 0.35); } }
        .input-actions {
          display: flex; align-items: center; gap: 8px;
          .emoji-btn, .image-btn { font-size: 18px; cursor: pointer; opacity: 0.7; &:hover { opacity: 1; } }
          .send-btn { color: #a855f7; cursor: pointer; display: flex; &.disabled { opacity: 0.5; cursor: not-allowed; } }
        }
      }
      
      .emoji-picker {
        margin-top: 12px; background: rgba(30, 30, 50, 0.95); border-radius: 12px; padding: 12px;
        .emoji-grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 8px; max-height: 150px; overflow-y: auto;
          .emoji-item { font-size: 20px; cursor: pointer; text-align: center; padding: 4px; border-radius: 6px; &:hover { background: rgba(255, 255, 255, 0.1); } }
        }
      }
    }
  }
}
</style>
