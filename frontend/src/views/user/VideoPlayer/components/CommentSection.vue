<template>
  <div class="comments-content">
    <!-- 评论列表 -->
    <div class="comment-list-wrapper">
      <!-- 官方公告 -->
      <div v-if="announcement?.enabled" class="comment-item official-announcement">
        <img :src="announcement.avatar || '/images/avatars/icon_avatar_1.webp'" class="avatar" />
        <div class="comment-body">
          <div class="comment-user">
            <span class="username official-name">{{ announcement.name }}</span>
            <img src="/images/backgrounds/super_vip_blue.webp" class="supreme-vip-icon" />
          </div>
          <p class="comment-text official-text">{{ announcement.content }}</p>
          <div class="comment-meta">
            <span class="time">{{ formatTime(announcement.updated_at) }}</span>
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
            :src="getAvatarUrl(comment.user_avatar, comment.user_id)" 
            class="avatar clickable" 
            @click="$emit('userClick', comment.user_id)" 
          />
          <div class="comment-body">
            <div class="comment-user">
              <span class="username clickable" @click="$emit('userClick', comment.user_id)">
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
                @click="$emit('like', comment)"
              >
                {{ comment.is_liked ? '❤️' : '🤍' }} {{ comment.like_count || 0 }}
              </span>
              <span class="reply-btn" @click="$emit('reply', comment)">回复</span>
              <span 
                v-if="canDelete" 
                class="delete-btn"
                @click="$emit('delete', comment)"
              >删除</span>
            </div>

            <!-- 回复列表 -->
            <div v-if="comment.replies?.length > 0" class="reply-list">
              <div v-for="reply in comment.replies" :key="reply.id" class="reply-item">
                <img 
                  :src="getAvatarUrl(reply.user_avatar, reply.user_id)" 
                  class="reply-avatar clickable" 
                  @click="$emit('userClick', reply.user_id)" 
                />
                <div class="reply-body">
                  <span class="username clickable" @click="$emit('userClick', reply.user_id)">
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
                      @click="$emit('like', reply)"
                    >{{ reply.is_liked ? '❤️' : '🤍' }} {{ reply.like_count || 0 }}</span>
                    <span class="reply-btn" @click="$emit('reply', comment, reply)">回复</span>
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
      
      <div class="no-more-comments" v-if="!hasMore && comments.length > 0 && !loading">
        <span>—— 已加载全部评论 ——</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'
import { VIP_LEVEL_ICONS } from '@/constants/vip'
import { getDefaultAvatarPath } from '@/utils/avatar'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

defineProps({
  comments: {
    type: Array,
    default: () => []
  },
  announcement: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  hasMore: {
    type: Boolean,
    default: false
  },
  canDelete: {
    type: Boolean,
    default: false
  }
})

defineEmits(['like', 'reply', 'delete', 'loadMore', 'loadMoreReplies', 'userClick', 'previewImage'])

const getAvatarUrl = (avatar, userId) => {
  if (avatar) return avatar
  return getDefaultAvatarPath(parseInt(userId) || 1)
}

const getVipLevelIcon = (level) => {
  return VIP_LEVEL_ICONS[level] || ''
}

const formatCommentTime = (dateStr) => {
  if (!dateStr) return ''
  return dayjs(dateStr).fromNow()
}

const formatTime = (dateStr) => {
  if (!dateStr) return ''
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}
</script>

<style scoped>
.comments-content {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 80px;
}

.comment-list-wrapper {
  padding: 0 12px;
}

.comment-item {
  display: flex;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.comment-item.is-pinned {
  background: rgba(236, 72, 153, 0.05);
  margin: 0 -12px;
  padding: 12px;
  border-radius: 8px;
}

.comment-item.official-announcement {
  background: linear-gradient(135deg, rgba(236, 72, 153, 0.1), rgba(139, 92, 246, 0.1));
  margin: 0 -12px 12px;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid rgba(236, 72, 153, 0.2);
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.avatar.clickable {
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
  margin-bottom: 4px;
}

.username {
  color: #fff;
  font-size: 13px;
  font-weight: 500;
}

.username.clickable {
  cursor: pointer;
}

.username.clickable:hover {
  color: #ec4899;
}

.official-name {
  color: #ec4899;
}

.vip-badge-sm,
.vip-badge-tiny {
  height: 14px;
}

.supreme-vip-icon {
  height: 16px;
}

.god-badge {
  height: 14px;
}

.pin-badge {
  font-size: 10px;
  color: #ec4899;
}

.comment-text {
  color: #ddd;
  font-size: 14px;
  line-height: 1.5;
  margin: 0 0 8px;
  word-break: break-word;
}

.official-text {
  color: #fff;
}

.comment-image {
  max-width: 200px;
  margin-bottom: 8px;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
}

.comment-image.small {
  max-width: 120px;
}

.comment-image img {
  width: 100%;
  display: block;
}

.comment-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 12px;
  color: #888;
}

.like-btn,
.reply-btn,
.delete-btn {
  cursor: pointer;
}

.like-btn:hover,
.reply-btn:hover {
  color: #ec4899;
}

.like-btn.liked {
  color: #ec4899;
}

.delete-btn {
  color: #f87171;
}

.reply-list {
  margin-top: 12px;
  padding-left: 12px;
  border-left: 2px solid rgba(255, 255, 255, 0.1);
}

.reply-item {
  display: flex;
  gap: 8px;
  padding: 8px 0;
}

.reply-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  object-fit: cover;
}

.reply-body {
  flex: 1;
}

.reply-text {
  color: #ccc;
  font-size: 13px;
  margin: 4px 0;
}

.reply-meta {
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: #888;
}

.more-replies {
  color: #ec4899;
  font-size: 12px;
  padding: 8px 0;
  cursor: pointer;
}

.empty-comments {
  text-align: center;
  padding: 40px 0;
  color: #666;
}

.load-more {
  text-align: center;
  padding: 16px 0;
}

.load-more-btn {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: #fff;
  padding: 10px 24px;
  border-radius: 20px;
  font-size: 13px;
  cursor: pointer;
}

.load-more-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-spinner {
  display: flex;
  align-items: center;
  gap: 8px;
}

.spin-icon {
  width: 16px;
  height: 16px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.no-more-comments {
  text-align: center;
  padding: 16px 0;
  color: #666;
  font-size: 12px;
}
</style>
