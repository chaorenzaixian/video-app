<template>
  <div class="comment-item">
    <img :src="getAvatarUrl(comment.user?.avatar, comment.user?.id)" class="comment-avatar clickable" @click="$emit('goProfile', comment.user?.id)" />
    <div class="comment-body">
      <div class="comment-user">
        <span class="username clickable" @click="$emit('goProfile', comment.user?.id)">{{ comment.user?.nickname || comment.user?.username || '用户' }}</span>
        <img v-if="comment.user?.vip_level > 0" :src="getVipIcon(comment.user.vip_level)" class="vip-badge-sm" />
      </div>
      <!-- 回复目标 -->
      <div v-if="comment.reply_to_user" class="reply-to">
        回复 <span class="reply-to-name">@{{ comment.reply_to_user.nickname || comment.reply_to_user.username }}</span>
      </div>
      <div class="comment-text">{{ comment.content }}</div>
      <!-- 评论图片 -->
      <div v-if="comment.images && comment.images.length" class="comment-images">
        <img 
          v-for="(img, idx) in comment.images" 
          :key="idx" 
          :src="img" 
          class="comment-img" 
          @click="$emit('previewImage', img)"
        />
      </div>
      <!-- 单张图片兼容 -->
      <div v-else-if="comment.image_url" class="comment-images">
        <img 
          :src="comment.image_url" 
          class="comment-img" 
          @click="$emit('previewImage', comment.image_url)"
        />
      </div>
      <div class="comment-footer">
        <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
        <div class="comment-actions">
          <span :class="['comment-like', { liked: comment.is_liked }]" @click="$emit('like', comment)">
            {{ comment.is_liked ? '❤️' : '🤍' }} {{ comment.like_count || 0 }}
          </span>
          <span class="comment-reply" @click.stop="$emit('reply', comment)">
            <img :src="replyIcon" class="reply-icon" />
          </span>
        </div>
      </div>
      
      <!-- 查看回复 -->
      <div v-if="comment.reply_count > 0 && !showReplies" class="view-replies" @click="loadReplies">
        查看{{ comment.reply_count }}条回复 <span class="arrow">▼</span>
      </div>
      
      <!-- 回复列表 -->
      <div v-if="showReplies && replies.length" class="replies-list">
        <div v-for="reply in replies" :key="reply.id" class="reply-item">
          <img :src="getAvatarUrl(reply.user?.avatar, reply.user?.id)" class="reply-avatar" @click="$emit('goProfile', reply.user?.id)" />
          <div class="reply-body">
            <div class="reply-user">
              <span class="username">{{ reply.user?.nickname || reply.user?.username }}</span>
              <span v-if="reply.reply_to_user" class="reply-to-text">
                回复 <span class="reply-to-name">@{{ reply.reply_to_user.nickname || reply.reply_to_user.username }}</span>
              </span>
            </div>
            <div class="reply-text">{{ reply.content }}</div>
            <!-- 回复图片 -->
            <div v-if="reply.images && reply.images.length" class="reply-images">
              <img 
                v-for="(img, idx) in reply.images" 
                :key="idx" 
                :src="img" 
                class="reply-img" 
                @click="$emit('previewImage', img)"
              />
            </div>
            <div class="reply-footer">
              <span class="reply-time">{{ formatTime(reply.created_at) }}</span>
              <span :class="['reply-like', { liked: reply.is_liked }]" @click="$emit('like', reply)">
                {{ reply.is_liked ? '❤️' : '🤍' }} {{ reply.like_count || 0 }}
              </span>
              <span class="reply-btn" @click.stop="$emit('reply', reply)">回复</span>
            </div>
          </div>
        </div>
        <div v-if="loadingReplies" class="loading-replies">加载中...</div>
        <div v-if="hasMoreReplies" class="load-more-replies" @click="loadMoreReplies">加载更多回复</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { getAvatarUrl } from '@/utils/avatar'
import api from '@/utils/api'
import replyIcon from '@/assets/icons/msg_icon.png'

const VIP_LEVEL_ICONS = {
  1: '/images/backgrounds/vip_gold.webp',
  2: '/images/backgrounds/vip_1.webp',
  3: '/images/backgrounds/vip_2.webp',
  4: '/images/backgrounds/vip_3.webp',
  5: '/images/backgrounds/super_vip_red.webp',
  6: '/images/backgrounds/super_vip_blue.webp'
}

const getVipIcon = (level) => VIP_LEVEL_ICONS[level] || VIP_LEVEL_ICONS[1]

const props = defineProps({
  comment: { type: Object, required: true },
  postId: { type: [Number, String], required: true }
})

defineEmits(['like', 'reply', 'goProfile', 'previewImage'])

const showReplies = ref(false)
const replies = ref([])
const loadingReplies = ref(false)
const hasMoreReplies = ref(true)
const replyPage = ref(1)

const loadReplies = async () => {
  if (loadingReplies.value) return
  loadingReplies.value = true
  showReplies.value = true
  replyPage.value = 1
  
  try {
    const res = await api.get(`/community/posts/${props.postId}/comments`, {
      params: { parent_id: Number(props.comment.id), page: 1, page_size: 10 }
    })
    replies.value = res.data || []
    hasMoreReplies.value = replies.value.length >= 10
  } catch (e) {
    console.error('加载回复失败', e)
  } finally {
    loadingReplies.value = false
  }
}

const loadMoreReplies = async () => {
  if (loadingReplies.value || !hasMoreReplies.value) return
  loadingReplies.value = true
  replyPage.value++
  
  try {
    const res = await api.get(`/community/posts/${props.postId}/comments`, {
      params: { parent_id: Number(props.comment.id), page: replyPage.value, page_size: 10 }
    })
    const data = res.data || []
    replies.value = [...replies.value, ...data]
    hasMoreReplies.value = data.length >= 10
  } catch (e) {
    console.error('加载更多回复失败', e)
  } finally {
    loadingReplies.value = false
  }
}

const formatTime = (time) => {
  if (!time) return ''
  const now = new Date()
  const d = new Date(time)
  const diff = now - d
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  
  return `${d.getMonth() + 1}-${d.getDate()}`
}
</script>

<style lang="scss" scoped>
.comment-item {
  display: flex;
  padding: 14px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);

  .comment-avatar {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    object-fit: cover;
    flex-shrink: 0;
    
    &.clickable {
      cursor: pointer;
    }
  }

  .comment-body {
    flex: 1;
    margin-left: 12px;
    min-width: 0;
  }

  .comment-user {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 6px;

    .username {
      color: rgba(255, 255, 255, 0.6);
      font-size: 13px;
      
      &.clickable {
        cursor: pointer;
      }
    }

    .vip-badge-sm {
      height: 14px;
      width: auto;
      object-fit: contain;
    }
  }

  .reply-to {
    color: rgba(255, 255, 255, 0.5);
    font-size: 12px;
    margin-bottom: 4px;
    
    .reply-to-name {
      color: #a855f7;
    }
  }

  .comment-text {
    color: rgba(255, 255, 255, 0.9);
    font-size: 14px;
    line-height: 1.6;
    word-break: break-word;
  }

  .comment-images {
    display: flex;
    gap: 8px;
    margin-top: 10px;
    flex-wrap: wrap;

    .comment-img {
      width: 100px;
      height: 100px;
      object-fit: cover;
      border-radius: 8px;
      cursor: pointer;
    }
  }

  .comment-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 10px;

    .comment-time {
      color: rgba(255, 255, 255, 0.4);
      font-size: 12px;
    }

    .comment-actions {
      display: flex;
      align-items: center;
      gap: 20px;
    }

    .comment-like {
      color: rgba(255, 255, 255, 0.5);
      font-size: 13px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 4px;
      
      &.liked {
        color: #ff6b6b;
      }
    }

    .comment-reply {
      cursor: pointer;
      display: flex;
      align-items: center;
      padding: 8px;
      margin: -8px;
      
      .reply-icon {
        width: 18px;
        height: 18px;
        opacity: 0.6;
      }
    }
  }

  .view-replies {
    margin-top: 12px;
    color: #a855f7;
    font-size: 13px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 4px;
    
    .arrow {
      font-size: 10px;
    }
  }

  .replies-list {
    margin-top: 12px;
    padding-left: 0;
    
    .reply-item {
      display: flex;
      padding: 10px 0;
      border-top: 1px solid rgba(255, 255, 255, 0.04);
      
      .reply-avatar {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        object-fit: cover;
        flex-shrink: 0;
        cursor: pointer;
      }
      
      .reply-body {
        flex: 1;
        margin-left: 10px;
        min-width: 0;
      }
      
      .reply-user {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 4px;
        flex-wrap: wrap;
        
        .username {
          color: rgba(255, 255, 255, 0.6);
          font-size: 12px;
        }
        
        .reply-to-text {
          color: rgba(255, 255, 255, 0.4);
          font-size: 12px;
          
          .reply-to-name {
            color: #a855f7;
          }
        }
      }
      
      .reply-text {
        color: rgba(255, 255, 255, 0.85);
        font-size: 13px;
        line-height: 1.5;
        word-break: break-word;
      }
      
      .reply-images {
        display: flex;
        gap: 6px;
        margin-top: 8px;
        flex-wrap: wrap;
        
        .reply-img {
          width: 80px;
          height: 80px;
          object-fit: cover;
          border-radius: 6px;
          cursor: pointer;
        }
      }
      
      .reply-footer {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-top: 8px;
        
        .reply-time {
          color: rgba(255, 255, 255, 0.4);
          font-size: 11px;
        }
        
        .reply-like {
          color: rgba(255, 255, 255, 0.5);
          font-size: 12px;
          cursor: pointer;
          
          &.liked {
            color: #ff6b6b;
          }
        }
        
        .reply-btn {
          color: rgba(255, 255, 255, 0.5);
          font-size: 12px;
          cursor: pointer;
        }
      }
    }
    
    .loading-replies {
      text-align: center;
      padding: 10px;
      color: rgba(255, 255, 255, 0.4);
      font-size: 12px;
    }
    
    .load-more-replies {
      text-align: center;
      padding: 10px;
      color: #a855f7;
      font-size: 12px;
      cursor: pointer;
    }
  }
}
</style>
