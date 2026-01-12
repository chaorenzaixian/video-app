<template>
  <div class="action-bar">
    <!-- 作者头像 -->
    <div class="author-avatar" @click.stop="$emit('go-profile', video.uploader_id)">
      <img :src="getAvatarUrl(video.uploader_avatar, video.uploader_id)" alt="" />
      <span class="follow-btn" v-if="!video.is_followed" @click.stop="$emit('follow', video)">+</span>
    </div>
    
    <!-- 点赞 -->
    <div class="action-item" @click.stop="$emit('like')">
      <div :class="['icon-wrapper', { liked: video.is_liked }]">
        <svg viewBox="0 0 24 24" :fill="video.is_liked ? '#fe2c55' : 'white'">
          <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
        </svg>
      </div>
      <span class="count">{{ formatCount(video.like_count) }}</span>
    </div>
    
    <!-- 评论 -->
    <div class="action-item" @click.stop="$emit('comment')">
      <div class="icon-wrapper">
        <svg viewBox="0 0 48 48" fill="white">
          <path d="M24 4C12.95 4 4 11.95 4 22c0 5.3 2.55 10.05 6.6 13.35L8 44l10.4-5.2c1.8.5 3.65.8 5.6.8 11.05 0 20-7.95 20-18S35.05 4 24 4z"/>
        </svg>
      </div>
      <span class="count">{{ formatCount(video.comment_count) }}</span>
    </div>
    
    <!-- 收藏 -->
    <div class="action-item" @click.stop="$emit('favorite')">
      <div :class="['icon-wrapper', { favorited: video.is_favorited }]">
        <svg viewBox="0 0 24 24" :fill="video.is_favorited ? '#ffc107' : 'white'">
          <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/>
        </svg>
      </div>
      <span class="count">{{ formatCount(video.favorite_count || 0) }}</span>
    </div>
    
    <!-- 分享 -->
    <div class="action-item" @click.stop="$emit('share')">
      <div class="icon-wrapper">
        <svg viewBox="0 0 24 24" fill="white">
          <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92s2.92-1.31 2.92-2.92-1.31-2.92-2.92-2.92z"/>
        </svg>
      </div>
      <span class="count">{{ formatCount(video.share_count || 0) }}</span>
    </div>
    
    <!-- 下载 -->
    <div class="action-item" @click.stop="$emit('download')">
      <div :class="['icon-wrapper', { 'vip-feature': !isVip }]">
        <svg viewBox="0 0 24 24" fill="white">
          <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
        </svg>
        <span v-if="!isVip" class="vip-tag">VIP</span>
      </div>
      <span class="count">下载</span>
    </div>
  </div>
</template>

<script setup>
import { formatCount } from '@/utils/format'

defineProps({
  video: { type: Object, required: true },
  isVip: { type: Boolean, default: false }
})

defineEmits(['like', 'comment', 'favorite', 'share', 'download', 'follow', 'go-profile'])

// 获取头像URL
const getAvatarUrl = (avatar, userId) => {
  if (avatar) {
    if (avatar.startsWith('/') || avatar.startsWith('http')) return avatar
    return '/' + avatar
  }
  const numericId = parseInt(userId) || 1
  const index = numericId % 52
  if (index < 17) return `/images/avatars/icon_avatar_${index + 1}.webp`
  if (index < 32) return `/images/avatars/DM_20251217202131_${String(index - 17 + 1).padStart(3, '0')}.JPEG`
  return `/images/avatars/DM_20251217202341_${String(index - 32 + 1).padStart(3, '0')}.JPEG`
}
</script>

<style lang="scss" scoped>
.action-bar {
  position: absolute;
  right: 12px;
  bottom: 70px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  z-index: 10;
  
  .author-avatar {
    position: relative;
    width: 46px;
    height: 46px;
    margin-bottom: 2px;
    
    img {
      width: 100%;
      height: 100%;
      border-radius: 50%;
      border: 2px solid #fff;
      object-fit: cover;
    }
    
    .follow-btn {
      position: absolute;
      bottom: -8px;
      left: 50%;
      transform: translateX(-50%);
      width: 22px;
      height: 22px;
      background: #fe2c55;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-size: 16px;
      font-weight: bold;
    }
  }
  
  .action-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    cursor: pointer;
    
    .icon-wrapper {
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: transform 0.2s ease;
      
      svg {
        width: 26px;
        height: 26px;
        filter: drop-shadow(0 1px 2px rgba(0,0,0,0.3));
      }
      
      &.liked svg { filter: drop-shadow(0 0 8px rgba(254, 44, 85, 0.5)); }
      &.favorited svg { filter: drop-shadow(0 0 8px rgba(255, 193, 7, 0.5)); }
      
      &.vip-feature {
        position: relative;
        .vip-tag {
          position: absolute;
          top: -4px;
          right: -8px;
          font-size: 8px;
          color: #fff;
          background: linear-gradient(135deg, #ffd700, #ff8c00);
          padding: 1px 4px;
          border-radius: 4px;
          font-weight: 600;
        }
      }
      
      &:active { transform: scale(0.9); }
    }
    
    .count {
      font-size: 11px;
      color: #fff;
      font-weight: 500;
      text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    }
  }
}
</style>
