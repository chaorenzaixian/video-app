<template>
  <div class="comment-item">
    <img :src="getAvatarUrl(comment.user?.avatar, comment.user?.id)" class="comment-avatar" @click="$emit('goProfile', comment.user?.id)" />
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
        <span class="comment-like" @click="$emit('like', comment)">
          <span class="heart">{{ comment.is_liked ? '❤️' : '♡' }}</span>
          {{ comment.like_count || 0 }}
        </span>
        <span class="comment-reply-btn" @click="$emit('reply', comment)">💬</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { getAvatarUrl } from '@/utils/avatar'

const VIP_LEVEL_ICONS = {
  1: '/images/backgrounds/vip_gold.webp',
  2: '/images/backgrounds/vip_1.webp',
  3: '/images/backgrounds/vip_2.webp',
  4: '/images/backgrounds/vip_3.webp',
  5: '/images/backgrounds/super_vip_red.webp',
  6: '/images/backgrounds/super_vip_blue.webp'
}

const getVipIcon = (level) => VIP_LEVEL_ICONS[level] || VIP_LEVEL_ICONS[1]

defineProps({
  comment: { type: Object, required: true }
})

defineEmits(['like', 'reply', 'goProfile'])

const formatDate = (time) => {
  if (!time) return ''
  const d = new Date(time)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<style lang="scss" scoped>
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
</style>
