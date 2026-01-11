<template>
  <div class="comments-section">
    <div class="comments-header">
      <span class="comments-count">{{ commentCount }}条评论</span>
      <div class="sort-tabs">
        <span class="sort-tab" :class="{ active: sortBy === 'hot' }" @click="changeSortBy('hot')">推荐</span>
        <span class="sort-divider">|</span>
        <span class="sort-tab" :class="{ active: sortBy === 'new' }" @click="changeSortBy('new')">最新</span>
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
      
      <CommentItem
        v-for="comment in comments"
        :key="comment.id"
        :comment="comment"
        :post-id="postId"
        @like="$emit('like-comment', $event)"
        @reply="$emit('reply-comment', $event)"
        @goProfile="$emit('go-profile', $event)"
        @previewImage="$emit('preview-image', $event)"
      />
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-if="!loading && !hasMore && comments.length" class="no-more">— 没有更多评论了 —</div>
    <div v-if="!loading && comments.length === 0 && !(announcement && announcement.enabled)" class="empty-comments">暂无评论，快来抢沙发~</div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import CommentItem from './CommentItem.vue'

defineProps({
  comments: { type: Array, default: () => [] },
  commentCount: { type: Number, default: 0 },
  loading: { type: Boolean, default: false },
  hasMore: { type: Boolean, default: true },
  announcement: { type: Object, default: null },
  postId: { type: [Number, String], required: true }
})

const emit = defineEmits(['like-comment', 'reply-comment', 'go-profile', 'sort-change', 'preview-image'])

const sortBy = ref('hot')

const changeSortBy = (val) => {
  sortBy.value = val
  emit('sort-change', val)
}

const formatAnnouncementTime = (time) => {
  if (!time) return ''
  const d = new Date(time)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
</script>

<style lang="scss" scoped>
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
    font-weight: 500;
  }

  .sort-tabs {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .sort-tab {
      color: rgba(255, 255, 255, 0.5);
      font-size: 13px;
      cursor: pointer;
      
      &.active {
        color: #fff;
      }
    }
    
    .sort-divider {
      color: rgba(255, 255, 255, 0.3);
    }
  }
}

.comment-item.official-announcement {
  display: flex;
  padding: 14px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.1), rgba(124, 58, 237, 0.05));
  margin: 0 -16px;
  padding: 14px 16px;
  
  .comment-avatar {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    object-fit: cover;
    flex-shrink: 0;
  }
  
  .comment-body {
    flex: 1;
    margin-left: 12px;
  }
  
  .comment-user {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 6px;
    
    .official-name {
      color: #a855f7;
      font-size: 13px;
      font-weight: 500;
    }
    
    .supreme-vip-icon {
      height: 16px;
      width: auto;
    }
  }
  
  .comment-text.official-text {
    color: rgba(255, 255, 255, 0.9);
    font-size: 14px;
    line-height: 1.6;
  }
  
  .comment-footer {
    margin-top: 8px;
    
    .comment-time {
      color: rgba(255, 255, 255, 0.4);
      font-size: 12px;
    }
  }
}

.loading, .no-more, .empty-comments {
  text-align: center;
  padding: 30px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 13px;
}
</style>
