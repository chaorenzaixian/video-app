<template>
  <div class="comments-content">
    <!-- 评论列表 -->
    <div class="comment-list-wrapper">
      <!-- 官方公告 -->
      <div v-if="announcement && announcement.enabled" class="comment-item official-announcement">
        <img :src="announcement.avatar || '/images/avatars/icon_avatar_1.webp'" class="avatar" />
        <div class="comment-body">
          <div class="comment-user">
            <span class="username official-name">{{ announcement.name }}</span>
            <img src="/images/backgrounds/super_vip_blue.webp" class="supreme-vip-icon" />
          </div>
          <p class="comment-text official-text">{{ announcement.content }}</p>
          <div class="comment-meta">
            <span class="time">{{ formatAnnouncementTime(announcement.updated_at) }}</span>
          </div>
        </div>
      </div>

      <div class="comment-list" v-if="comments.length > 0">
        <div 
          v-for="comment in comments" 
          :key="comment.id" 
          :class="['comment-item', { 'is-pinned': comment.is_pinned, 'is-official': comment.is_official }]"
        >
          <img 
            :src="getAvatarUrl(comment.user_avatar, comment.user_id || comment.id)" 
            class="avatar clickable" 
            @click="$emit('goToUser', comment.user_id)" 
          />
          <div class="comment-body">
            <div class="comment-user">
              <span class="username clickable" @click="$emit('goToUser', comment.user_id)">
                {{ comment.user_name }}
              </span>
              <img 
                v-if="comment.user_vip_level > 0" 
                :src="getVipLevelIcon(comment.user_vip_level)" 
                class="vip-badge-sm"
              />
              <img v-if="comment.is_god" src="/images/god_comment.webp" class="god-badge" title="神评" />
              <span v-if="comment.is_pinned" class="pin-badge">📌 置顶</span>
            </div>
            <p class="comment-text">{{ comment.content }}</p>
            <div v-if="comment.image_url" class="comment-image" @click="$emit('previewImage', comment.image_url)">
              <img :src="comment.image_url" alt="comment image" />
            </div>
            <div class="comment-meta">
              <span class="time">{{ formatCommentTime(comment.created_at) }}</span>
              <span 
                :class="['like-btn', { liked: comment.is_liked }]" 
                @click="$emit('likeComment', comment)"
              >
                {{ comment.is_liked ? '❤️' : '🤍' }} {{ comment.like_count || 0 }}
              </span>
              <span class="reply-btn" @click="$emit('startReply', comment)">回复</span>
              <span 
                v-if="canDeleteComment(comment)" 
                class="delete-btn"
                @click="$emit('deleteComment', comment)"
              >删除</span>
            </div>

            <!-- 回复列表 -->
            <div v-if="comment.replies && comment.replies.length > 0" class="reply-list">
              <div v-for="reply in comment.replies" :key="reply.id" class="reply-item">
                <img 
                  :src="getAvatarUrl(reply.user_avatar, reply.user_id || reply.id)" 
                  class="reply-avatar clickable" 
                  @click="$emit('goToUser', reply.user_id)" 
                />
                <div class="reply-body">
                  <span class="username clickable" @click="$emit('goToUser', reply.user_id)">
                    {{ reply.user_name }}
                  </span>
                  <span v-if="reply.is_official" class="official-badge small">官方</span>
                  <img 
                    v-if="reply.user_vip_level > 0" 
                    :src="getVipLevelIcon(reply.user_vip_level)" 
                    class="vip-badge-tiny"
                  />
                  <p class="reply-text">{{ reply.content }}</p>
                  <div v-if="reply.image_url" class="comment-image small" @click="$emit('previewImage', reply.image_url)">
                    <img :src="reply.image_url" alt="reply image" />
                  </div>
                  <div class="reply-meta">
                    <span class="time">{{ formatCommentTime(reply.created_at) }}</span>
                    <span 
                      :class="['like-btn', { liked: reply.is_liked }]" 
                      @click="$emit('likeComment', reply)"
                    >{{ reply.is_liked ? '❤️' : '🤍' }} {{ reply.like_count || 0 }}</span>
                    <span class="reply-btn" @click="$emit('startReply', comment, reply)">回复</span>
                  </div>
                </div>
              </div>
              <div 
                v-if="comment.reply_count > comment.replies.length" 
                class="more-replies"
                @click="$emit('loadMoreReplies', comment)"
              >
                展开更多 {{ comment.reply_count - comment.replies.length }} 条回复 ›
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 空评论 -->
      <div v-else class="empty-comments">
        <p>还没有评论，快来抢沙发吧~</p>
      </div>

      <!-- 加载更多 -->
      <div class="load-more" v-if="hasMore || loading">
        <button @click="$emit('loadMore')" :disabled="loading" class="load-more-btn">
          <span v-if="loading" class="loading-spinner">
            <svg viewBox="0 0 24 24" class="spin-icon">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" fill="none" stroke-dasharray="31.4 31.4" />
            </svg>
            加载中...
          </span>
          <span v-else>📜 加载更多评论</span>
        </button>
      </div>
      
      <!-- 没有更多评论提示 -->
      <div class="no-more-comments" v-if="!hasMore && comments.length > 0 && !loading">
        <span>—— 已加载全部评论 ——</span>
      </div>
    </div>

    <!-- 底部评论输入框 -->
    <div class="comment-input-bar">
      <!-- 非VIP提示 -->
      <div v-if="!isVip" class="vip-comment-tip" @click="$emit('goToVip')">
        <span class="tip-icon">👑</span>
        <span class="tip-text">开通VIP即可发表评论</span>
        <span class="tip-btn">立即开通 ›</span>
      </div>
      
      <!-- VIP评论输入区 -->
      <div v-else class="input-area">
        <!-- 图片预览 -->
        <div v-if="imagePreview" class="image-preview">
          <img :src="imagePreview" alt="preview" />
          <span class="remove-image" @click="$emit('removeImage')">×</span>
        </div>
        
        <div class="input-row">
          <input 
            type="text"
            v-model="inputText"
            :placeholder="replyPlaceholder"
            @keyup.enter="submitComment"
            ref="inputRef"
          />
          <div class="input-actions">
            <span v-if="replyTo" class="cancel-btn" @click="$emit('cancelReply')">取消</span>
            <span class="emoji-btn" @click="showEmoji = !showEmoji">😊</span>
            <label class="image-btn">
              <input type="file" accept="image/*" @change="handleImageSelect" hidden />
              🖼️
            </label>
            <span class="send-btn" @click="submitComment" :class="{ disabled: !canSubmit }">
              <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
              </svg>
            </span>
          </div>
        </div>
        
        <!-- 表情选择器 -->
        <div v-if="showEmoji" class="emoji-picker">
          <div class="emoji-grid">
            <span v-for="emoji in emojiList" :key="emoji" class="emoji-item" @click="insertEmoji(emoji)">
              {{ emoji }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  comments: { type: Array, default: () => [] },
  announcement: { type: Object, default: null },
  hasMore: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  isVip: { type: Boolean, default: false },
  currentUserId: { type: Number, default: null },
  replyTo: { type: Object, default: null },
  imagePreview: { type: String, default: '' }
})

const emit = defineEmits([
  'loadMore', 'likeComment', 'startReply', 'deleteComment', 
  'loadMoreReplies', 'goToUser', 'goToVip', 'previewImage',
  'submit', 'imageSelect', 'removeImage', 'cancelReply'
])

const inputText = ref('')
const inputRef = ref(null)
const showEmoji = ref(false)

// 表情列表
const emojiList = [
  '😀', '😂', '🤣', '😊', '😍', '🥰', '😘', '😜', '🤪', '😎',
  '🥳', '😇', '🤩', '😋', '😛', '🤤', '😏', '😒', '😔', '😢',
  '😭', '😤', '😠', '🤬', '😱', '😰', '😥', '🤧', '😷', '🤒',
  '👍', '👎', '👏', '🙏', '💪', '❤️', '💔', '💯', '🔥', '✨',
  '🎉', '🎊', '💎', '🏆', '🥇', '⭐', '🌟', '💫', '🌈', '☀️'
]

// 回复占位符
const replyPlaceholder = computed(() => {
  if (props.replyTo) {
    return `回复 @${props.replyTo.user_name}`
  }
  return '说点什么吧...'
})

// 是否可以提交
const canSubmit = computed(() => {
  return inputText.value.trim() || props.imagePreview
})

// 插入表情
const insertEmoji = (emoji) => {
  inputText.value += emoji
  showEmoji.value = false
}

// 获取头像URL
const getAvatarUrl = (avatar, id) => {
  if (avatar && avatar.startsWith('http')) return avatar
  if (avatar) return avatar
  const index = (id || 1) % 10 + 1
  return `/images/avatars/icon_avatar_${index}.webp`
}

// 获取VIP等级图标
const getVipLevelIcon = (level) => {
  if (level >= 1 && level <= 5) {
    return `/images/vip/vip_level_${level}.webp`
  }
  return ''
}

// 格式化评论时间
const formatCommentTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  
  return `${date.getMonth() + 1}-${date.getDate()}`
}

// 格式化公告时间
const formatAnnouncementTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

// 是否可以删除评论
const canDeleteComment = (comment) => {
  return props.currentUserId && comment.user_id === props.currentUserId
}

// 提交评论
const submitComment = () => {
  if (!canSubmit.value) return
  emit('submit', inputText.value)
  inputText.value = ''
}

// 处理图片选择
const handleImageSelect = (e) => {
  const file = e.target.files?.[0]
  if (file) {
    emit('imageSelect', file)
  }
  e.target.value = ''
}
</script>


<style lang="scss" scoped>
.comments-content {
  padding-bottom: 70px;
}

.comment-list-wrapper {
  padding: 0 12px;
}

.comment-item {
  display: flex;
  gap: 12px;
  padding: 16px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  
  &.is-pinned {
    background: rgba(255, 215, 0, 0.05);
    margin: 0 -12px;
    padding: 16px 12px;
  }
  
  &.is-official {
    background: rgba(139, 92, 246, 0.05);
    margin: 0 -12px;
    padding: 16px 12px;
  }
  
  &.official-announcement {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(99, 102, 241, 0.1));
    margin: 0 -12px 12px;
    padding: 16px 12px;
    border-radius: 12px;
    border: 1px solid rgba(139, 92, 246, 0.2);
  }
  
  .avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    object-fit: cover;
    flex-shrink: 0;
    
    &.clickable {
      cursor: pointer;
    }
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
    flex-wrap: wrap;
    
    .username {
      font-size: 14px;
      font-weight: 500;
      color: #fff;
      
      &.clickable {
        cursor: pointer;
        
        &:hover {
          color: #a78bfa;
        }
      }
      
      &.official-name {
        color: #a78bfa;
      }
    }
    
    .vip-badge-sm {
      height: 16px;
      width: auto;
    }
    
    .god-badge {
      height: 18px;
      width: auto;
    }
    
    .pin-badge {
      font-size: 11px;
      color: #ffd700;
    }
    
    .supreme-vip-icon {
      height: 18px;
      width: auto;
    }
  }
  
  .comment-text {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.85);
    line-height: 1.5;
    margin: 0 0 8px;
    word-break: break-word;
    
    &.official-text {
      color: rgba(255, 255, 255, 0.9);
    }
  }
  
  .comment-image {
    max-width: 200px;
    margin-bottom: 8px;
    border-radius: 8px;
    overflow: hidden;
    cursor: pointer;
    
    img {
      width: 100%;
      display: block;
    }
    
    &.small {
      max-width: 120px;
    }
  }
  
  .comment-meta {
    display: flex;
    align-items: center;
    gap: 16px;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.4);
    
    .like-btn, .reply-btn, .delete-btn {
      cursor: pointer;
      transition: color 0.2s;
      
      &:hover {
        color: rgba(255, 255, 255, 0.8);
      }
    }
    
    .like-btn.liked {
      color: #ef4444;
    }
    
    .delete-btn {
      color: rgba(255, 100, 100, 0.6);
      
      &:hover {
        color: #ef4444;
      }
    }
  }
}

.reply-list {
  margin-top: 12px;
  padding-left: 12px;
  border-left: 2px solid rgba(255, 255, 255, 0.1);
  
  .reply-item {
    display: flex;
    gap: 10px;
    padding: 10px 0;
    
    &:not(:last-child) {
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    }
  }
  
  .reply-avatar {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    object-fit: cover;
    flex-shrink: 0;
    
    &.clickable {
      cursor: pointer;
    }
  }
  
  .reply-body {
    flex: 1;
    min-width: 0;
    
    .username {
      font-size: 13px;
      font-weight: 500;
      color: #fff;
      margin-right: 6px;
      
      &.clickable {
        cursor: pointer;
        
        &:hover {
          color: #a78bfa;
        }
      }
    }
    
    .official-badge.small {
      font-size: 10px;
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      color: #fff;
      padding: 1px 4px;
      border-radius: 3px;
      margin-right: 4px;
    }
    
    .vip-badge-tiny {
      height: 14px;
      width: auto;
      margin-right: 4px;
    }
    
    .reply-text {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.8);
      line-height: 1.4;
      margin: 4px 0;
      word-break: break-word;
    }
    
    .reply-meta {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 11px;
      color: rgba(255, 255, 255, 0.4);
      
      .like-btn, .reply-btn {
        cursor: pointer;
        
        &:hover {
          color: rgba(255, 255, 255, 0.8);
        }
      }
      
      .like-btn.liked {
        color: #ef4444;
      }
    }
  }
  
  .more-replies {
    font-size: 12px;
    color: #a78bfa;
    cursor: pointer;
    padding: 8px 0;
    
    &:hover {
      color: #c4b5fd;
    }
  }
}

.empty-comments {
  text-align: center;
  padding: 40px 20px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 14px;
}

.load-more {
  padding: 16px;
  text-align: center;
  
  .load-more-btn {
    background: rgba(255, 255, 255, 0.08);
    border: none;
    color: rgba(255, 255, 255, 0.7);
    padding: 10px 24px;
    border-radius: 20px;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s;
    
    &:hover:not(:disabled) {
      background: rgba(255, 255, 255, 0.12);
    }
    
    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    
    .loading-spinner {
      display: flex;
      align-items: center;
      gap: 6px;
      
      .spin-icon {
        width: 16px;
        height: 16px;
        animation: spin 1s linear infinite;
      }
    }
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.no-more-comments {
  text-align: center;
  padding: 16px;
  color: rgba(255, 255, 255, 0.3);
  font-size: 12px;
}

.comment-input-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #1a1a1a;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding: 12px 16px;
  padding-bottom: calc(12px + env(safe-area-inset-bottom, 0px));
  z-index: 100;
  
  .vip-comment-tip {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 10px;
    background: linear-gradient(135deg, rgba(255, 215, 0, 0.1), rgba(255, 165, 0, 0.1));
    border-radius: 24px;
    cursor: pointer;
    
    .tip-icon {
      font-size: 16px;
    }
    
    .tip-text {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.8);
    }
    
    .tip-btn {
      font-size: 13px;
      color: #ffd700;
      font-weight: 500;
    }
  }
  
  .input-area {
    .image-preview {
      position: relative;
      display: inline-block;
      margin-bottom: 8px;
      
      img {
        max-height: 60px;
        border-radius: 6px;
      }
      
      .remove-image {
        position: absolute;
        top: -6px;
        right: -6px;
        width: 20px;
        height: 20px;
        background: rgba(0, 0, 0, 0.7);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        font-size: 14px;
        cursor: pointer;
      }
    }
    
    .input-row {
      display: flex;
      align-items: center;
      gap: 10px;
      
      input {
        flex: 1;
        background: rgba(255, 255, 255, 0.08);
        border: none;
        border-radius: 20px;
        padding: 10px 16px;
        color: #fff;
        font-size: 14px;
        outline: none;
        
        &::placeholder {
          color: rgba(255, 255, 255, 0.4);
        }
      }
      
      .input-actions {
        display: flex;
        align-items: center;
        gap: 8px;
        
        .cancel-btn {
          font-size: 13px;
          color: rgba(255, 255, 255, 0.6);
          cursor: pointer;
          
          &:hover {
            color: #fff;
          }
        }
        
        .emoji-btn, .image-btn {
          font-size: 20px;
          cursor: pointer;
          padding: 4px;
          transition: transform 0.2s;
          
          &:hover {
            transform: scale(1.1);
          }
        }
        
        .send-btn {
          width: 36px;
          height: 36px;
          background: linear-gradient(135deg, #6366f1, #8b5cf6);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.2s;
          
          &:hover:not(.disabled) {
            transform: scale(1.05);
          }
          
          &.disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
          
          svg {
            color: #fff;
          }
        }
      }
    }
    
    .emoji-picker {
      margin-top: 10px;
      background: rgba(30, 30, 30, 0.95);
      border-radius: 12px;
      padding: 12px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      
      .emoji-grid {
        display: grid;
        grid-template-columns: repeat(10, 1fr);
        gap: 4px;
        
        .emoji-item {
          font-size: 20px;
          padding: 6px;
          text-align: center;
          cursor: pointer;
          border-radius: 6px;
          transition: background 0.2s;
          
          &:hover {
            background: rgba(255, 255, 255, 0.1);
          }
        }
      }
    }
  }
}
</style>
