<template>
  <div class="video-info-section">
    <!-- 视频标题 -->
    <h1 class="video-title">{{ video.title }}</h1>
    
    <!-- 标签 -->
    <div class="video-tags">
      <span 
        v-for="tag in displayTags" 
        :key="tag"
        class="tag-item"
      >
        {{ tag }}
      </span>
    </div>

    <!-- 上传者信息 -->
    <div class="uploader-info">
      <img 
        :src="uploaderAvatar" 
        class="avatar clickable" 
        @click="$emit('goToUser', video.uploader_id)" 
      />
      <div class="uploader-detail">
        <div class="name-row">
          <span class="name clickable" @click="$emit('goToUser', video.uploader_id)">
            {{ video.uploader_name || '匿名用户' }}
          </span>
          <img 
            v-if="video.uploader_vip_level > 0" 
            :src="getVipLevelIcon(video.uploader_vip_level)" 
            class="vip-badge"
          />
          <span class="badge" v-if="video.is_verified">🔷 至尊</span>
        </div>
        <div class="stats">{{ uploaderStats }}</div>
      </div>
      <button 
        class="follow-btn" 
        :class="{ followed: isFollowed }" 
        @click="$emit('toggleFollow')"
      >
        {{ isFollowed ? '已关注' : '+ 关注' }}
      </button>
    </div>

    <!-- 视频统计 -->
    <div class="video-stats">
      <div class="stat-item views">
        <span class="stat-value">{{ formatViewCount(video.view_count) }}观看量</span>
      </div>
      <div class="stat-item clickable" @click="$emit('toggleLike')">
        <span :class="['stat-icon', 'heart', { active: isLiked }]">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
          </svg>
        </span>
        <span class="stat-value">{{ formatCount(video.like_count) }}</span>
      </div>
      <div class="stat-item clickable" @click="$emit('toggleFavorite')">
        <span :class="['stat-icon', 'star', { active: isFavorited }]">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/>
          </svg>
        </span>
        <span class="stat-value">{{ video.favorite_count || 0 }}</span>
      </div>
      <div class="stat-item clickable" @click="$emit('share')">
        <span class="stat-icon share">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92s2.92-1.31 2.92-2.92-1.31-2.92-2.92-2.92z"/>
          </svg>
        </span>
        <span class="stat-label">分享</span>
      </div>
      <div class="stat-item clickable" @click="$emit('download')">
        <span class="stat-icon download" :class="{ 'vip-feature': !isVip }">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
          </svg>
          <span v-if="!isVip" class="vip-badge-small">VIP</span>
        </span>
        <span class="stat-label">下载</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  video: { type: Object, required: true },
  isLiked: { type: Boolean, default: false },
  isFavorited: { type: Boolean, default: false },
  isFollowed: { type: Boolean, default: false },
  isVip: { type: Boolean, default: false },
  uploaderStats: { type: String, default: '' }
})

defineEmits(['goToUser', 'toggleFollow', 'toggleLike', 'toggleFavorite', 'share', 'download'])

// 默认标签
const defaultTags = ['精选', '热门']

// 显示的标签
const displayTags = computed(() => {
  return props.video.tags?.length > 0 ? props.video.tags : defaultTags
})

// 上传者头像
const uploaderAvatar = computed(() => {
  const avatar = props.video.uploader_avatar
  if (avatar && avatar.startsWith('http')) return avatar
  if (avatar) return avatar
  const id = props.video.uploader_id || props.video.id || 1
  const index = id % 10 + 1
  return `/images/avatars/icon_avatar_${index}.webp`
})

// 获取VIP等级图标
const getVipLevelIcon = (level) => {
  if (level >= 1 && level <= 5) {
    return `/images/vip/vip_level_${level}.webp`
  }
  return ''
}

// 格式化观看数
const formatViewCount = (count) => {
  if (!count) return '0'
  if (count >= 10000) return (count / 10000).toFixed(1) + 'w'
  if (count >= 1000) return (count / 1000).toFixed(1) + 'k'
  return count.toString()
}

// 格式化数量
const formatCount = (count) => {
  if (!count) return '0'
  if (count >= 10000) return (count / 10000).toFixed(1) + 'w'
  return count.toString()
}
</script>

<style lang="scss" scoped>
.video-info-section {
  padding: 16px;
}

.video-title {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 12px;
  line-height: 1.4;
}

.video-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
  
  .tag-item {
    background: rgba(139, 92, 246, 0.2);
    color: #a78bfa;
    padding: 4px 12px;
    border-radius: 16px;
    font-size: 12px;
  }
}

.uploader-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  
  .avatar {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    object-fit: cover;
    
    &.clickable {
      cursor: pointer;
    }
  }
  
  .uploader-detail {
    flex: 1;
    min-width: 0;
    
    .name-row {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 4px;
      
      .name {
        font-size: 15px;
        font-weight: 500;
        color: #fff;
        
        &.clickable {
          cursor: pointer;
          
          &:hover {
            color: #a78bfa;
          }
        }
      }
      
      .vip-badge {
        height: 18px;
        width: auto;
      }
      
      .badge {
        font-size: 11px;
        color: #60a5fa;
      }
    }
    
    .stats {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);
    }
  }
  
  .follow-btn {
    padding: 8px 20px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    border: none;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #fff;
    
    &:hover {
      transform: scale(1.02);
    }
    
    &.followed {
      background: rgba(255, 255, 255, 0.1);
      color: rgba(255, 255, 255, 0.7);
    }
  }
}

.video-stats {
  display: flex;
  justify-content: space-around;
  padding: 16px 0;
  
  .stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    
    &.clickable {
      cursor: pointer;
      
      &:hover .stat-icon {
        transform: scale(1.1);
      }
    }
    
    .stat-icon {
      width: 24px;
      height: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: rgba(255, 255, 255, 0.6);
      transition: all 0.2s;
      position: relative;
      
      svg {
        width: 100%;
        height: 100%;
      }
      
      &.heart.active {
        color: #ef4444;
      }
      
      &.star.active {
        color: #fbbf24;
      }
      
      &.vip-feature {
        .vip-badge-small {
          position: absolute;
          top: -4px;
          right: -8px;
          font-size: 8px;
          background: linear-gradient(135deg, #ffd700, #ffb700);
          color: #000;
          padding: 1px 3px;
          border-radius: 3px;
          font-weight: 600;
        }
      }
    }
    
    .stat-value, .stat-label {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.6);
    }
  }
}
</style>
