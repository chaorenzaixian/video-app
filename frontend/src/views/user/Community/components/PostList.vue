<template>
  <div class="posts-list">
    <div v-for="post in posts" :key="post.id" class="post-card" @click="$emit('detail', post.id)">
      <div class="post-header">
        <img :src="getAvatarUrl(post.user?.avatar, post.user?.id)" class="avatar clickable" @click.stop="$emit('profile', post.user?.id)" />
        <div class="user-info">
          <div class="user-name-row">
            <span class="username clickable" @click.stop="$emit('profile', post.user?.id)">{{ post.user?.nickname || post.user?.username || '匿名用户' }}</span>
            <img v-if="post.user?.is_vip" :src="getVipLevelIcon(post.user?.vip_level)" class="vip-icon" alt="VIP" />
          </div>
          <span class="time">{{ formatCommentTime(post.created_at) }}</span>
        </div>
      </div>
      <p class="post-text">{{ post.content }}</p>
      <div v-if="post.images?.length" class="post-images">
        <div :class="['images-grid', `grid-${Math.min(post.images.length, 4)}`]">
          <div v-for="(img, idx) in post.images.slice(0, 4)" :key="idx" class="img-item">
            <img :src="img" />
            <span v-if="idx === 3 && post.images.length > 4" class="more-count">+{{ post.images.length - 4 }}</span>
          </div>
        </div>
      </div>
      <div class="post-stats">
        <span>👁 {{ formatCount(post.view_count) }}</span>
        <span>💬 {{ post.comment_count || 0 }}</span>
        <span @click.stop="$emit('like', post)">{{ post.is_liked ? '❤️' : '🤍' }} {{ formatCount(post.like_count) }}</span>
        <span v-if="post.topics?.length" class="post-topic-tag">#{{ post.topics[0].name }}</span>
      </div>
    </div>
    <div v-if="loading" class="loading">加载中...</div>
    <div v-if="!loading && !hasMore && posts.length" class="no-more">没有更多了</div>
    <div v-if="!loading && !posts.length" class="empty">暂无内容</div>
  </div>
</template>

<script setup>
import { getAvatarUrl } from '@/utils/avatar'
import { formatCount, formatCommentTime } from '@/utils/format'
import { getVipLevelIcon } from '@/constants/vip'

defineProps({
  posts: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  hasMore: { type: Boolean, default: true }
})

defineEmits(['detail', 'profile', 'like'])
</script>

<style lang="scss" scoped>
.posts-list { padding: 0; min-height: calc(100vh - 200px); }

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
  width: 40px; height: 40px; border-radius: 50%; object-fit: cover;
  &.clickable { cursor: pointer; &:hover { transform: scale(1.05); } }
}

.user-info { margin-left: 12px; }
.user-name-row { display: flex; align-items: center; gap: 6px; }
.username { color: #fff; font-size: 14px; font-weight: 500;
  &.clickable { cursor: pointer; &:hover { color: #a855f7; } }
}
.vip-icon { width: 36px; height: 18px; object-fit: contain; }
.time { color: #666; font-size: 12px; }

.post-text {
  color: #ddd; font-size: 14px; line-height: 1.6; margin-bottom: 12px;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
}

.post-images { margin-bottom: 12px; }
.images-grid { display: grid; gap: 4px; border-radius: 8px; overflow: hidden; }
.images-grid.grid-1 { grid-template-columns: 1fr; max-width: 70%; }
.images-grid.grid-2 { grid-template-columns: repeat(2, 1fr); }
.images-grid.grid-3 { grid-template-columns: repeat(3, 1fr); }
.images-grid.grid-4 { grid-template-columns: repeat(4, 1fr); }

.img-item { position: relative; aspect-ratio: 1; }
.img-item img { width: 100%; height: 100%; object-fit: cover; }
.more-count {
  position: absolute; inset: 0; background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center; color: #fff; font-size: 18px;
}

.post-stats { display: flex; align-items: center; gap: 20px; color: #666; font-size: 13px; }
.post-stats span { cursor: pointer; }
.post-topic-tag {
  margin-left: auto; padding: 4px 12px; background: transparent;
  border: 1px solid rgba(168, 85, 247, 0.5); border-radius: 12px; color: #a855f7; font-size: 12px;
}

.loading, .no-more, .empty { text-align: center; padding: 30px; color: #666; }
</style>
