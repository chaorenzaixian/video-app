<template>
  <div class="comments-section">
    <div class="comments-header">
      <span class="comments-count">{{ commentCount }}条评论</span>
      <div class="sort-tabs">
        <span :class="{ active: sortBy === 'hot' }" @click="changeSortBy('hot')">推荐</span>
        <span class="divider">|</span>
        <span :class="{ active: sortBy === 'new' }" @click="changeSortBy('new')">最新</span>
      </div>
    </div>

    <!-- 评论列表 -->
    <div class="comments-list">
      <CommentItem
        v-for="comment in comments"
        :key="comment.id"
        :comment="comment"
        @like="$emit('likeComment', $event)"
        @reply="$emit('replyComment', $event)"
        @goProfile="$emit('goProfile', $event)"
      />
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-if="!loading && !hasMore && comments.length" class="no-more">— 没有更多评论了 —</div>
    <div v-if="!loading && comments.length === 0" class="empty-comments">暂无评论，快来抢沙发~</div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import CommentItem from './CommentItem.vue'

defineProps({
  comments: { type: Array, default: () => [] },
  commentCount: { type: Number, default: 0 },
  loading: { type: Boolean, default: false },
  hasMore: { type: Boolean, default: true }
})

const emit = defineEmits(['likeComment', 'replyComment', 'goProfile', 'sortChange'])

const sortBy = ref('hot')

const changeSortBy = (val) => {
  sortBy.value = val
  emit('sortChange', val)
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

.loading, .no-more, .empty-comments {
  text-align: center;
  padding: 30px;
  color: #555;
  font-size: 13px;
}
</style>
