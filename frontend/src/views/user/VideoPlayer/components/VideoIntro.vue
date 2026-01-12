<template>
  <div class="intro-content">
    <!-- 视频信息区 -->
    <div class="intro-section">
      <!-- 视频标题 -->
      <h1 class="video-title">{{ video.title }}</h1>
      
      <!-- 标签 -->
      <div class="video-tags">
        <span 
          v-for="tag in videoTags" 
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
          @click="goToUserProfile" 
        />
        <div class="uploader-detail">
          <div class="name-row">
            <span class="name clickable" @click="goToUserProfile">
              {{ video.uploader_name || '匿名用户' }}
            </span>
            <img 
              v-if="video.uploader_vip_level > 0" 
              :src="getVipLevelIcon(video.uploader_vip_level)" 
              class="vip-badge"
            />
          </div>
          <div class="stats">{{ uploaderStats }}</div>
        </div>
        <button 
          class="follow-btn" 
          :class="{ followed: isUploaderFollowed }" 
          @click="$emit('follow')"
        >
          {{ isUploaderFollowed ? '已关注' : '+ 关注' }}
        </button>
      </div>

      <!-- 视频统计 -->
      <div class="video-stats">
        <div class="stat-item views">
          <span class="stat-value">{{ formatViewCount(video.view_count) }}观看量</span>
        </div>
        <div class="stat-item clickable" @click="$emit('like')">
          <span :class="['stat-icon', 'heart', { active: isLiked }]">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
            </svg>
          </span>
          <span class="stat-value">{{ formatCount(video.like_count) }}</span>
        </div>
        <div class="stat-item clickable" @click="$emit('favorite')">
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

    <!-- 图标广告位 -->
    <div class="ad-icons-section" v-if="iconAds.length > 0">
      <div class="ad-icons-scroll">
        <div class="ad-icons-track">
          <div 
            v-for="ad in iconAds" 
            :key="ad.id" 
            class="ad-icon-item"
            @click="handleAdClick(ad)"
          >
            <div class="icon-wrap">
              <img v-if="ad.image" :src="ad.image" :alt="ad.name" />
              <span v-else class="icon-emoji">{{ ad.icon }}</span>
            </div>
            <span class="icon-name">{{ ad.name }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 推荐视频列表 -->
    <div class="recommend-section">
      <h3 class="section-title">推荐视频</h3>
      <div class="video-list">
        <div 
          v-for="rec in recommendVideos" 
          :key="rec.id"
          class="video-card"
          @click="$emit('video-click', rec)"
        >
          <div class="video-cover">
            <img :src="getCoverUrl(rec.cover_url)" :alt="rec.title" />
            <div class="cover-views">
              <span class="play-icon">▶</span>
              <span>{{ formatViewCount(rec.view_count) }}</span>
            </div>
            <div class="video-duration">{{ formatDuration(rec.duration) }}</div>
          </div>
          <div class="video-info">
            <p class="video-title">{{ rec.title }}</p>
            <div class="video-meta">
              <span class="video-tag">{{ rec.category_name || '精选' }}</span>
              <span class="video-comments">评论 {{ rec.comment_count || 0 }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { formatCount, formatDuration, formatViewCount } from '@/utils/format'
import { VIP_LEVEL_ICONS } from '@/constants/vip'

const props = defineProps({
  video: { type: Object, default: () => ({}) },
  isVip: { type: Boolean, default: false },
  isLiked: { type: Boolean, default: false },
  isFavorited: { type: Boolean, default: false },
  isUploaderFollowed: { type: Boolean, default: false },
  recommendVideos: { type: Array, default: () => [] },
  iconAds: { type: Array, default: () => [] }
})

defineEmits(['like', 'favorite', 'follow', 'share', 'download', 'video-click'])

const router = useRouter()

const videoTags = computed(() => {
  return props.video.tags || ['精选']
})

const uploaderAvatar = computed(() => {
  return props.video.uploader_avatar || '/images/avatars/default.webp'
})

const uploaderStats = computed(() => {
  const followers = props.video.uploader_followers || 0
  const videos = props.video.uploader_video_count || 0
  return `${followers} 粉丝 · ${videos} 视频`
})

const getVipLevelIcon = (level) => {
  return VIP_LEVEL_ICONS[level] || ''
}

const getCoverUrl = (url) => {
  if (!url) return '/placeholder.webp'
  if (url.startsWith('http') || url.startsWith('/')) return url
  return '/' + url
}

const goToUserProfile = () => {
  if (props.video.uploader_id) {
    router.push(`/user/profile/${props.video.uploader_id}`)
  }
}

const handleAdClick = (ad) => {
  if (ad.target_url) {
    window.open(ad.target_url, '_blank')
  }
}
</script>

<style scoped>
.intro-content {
  padding: 16px;
}

.intro-section {
  margin-bottom: 20px;
}

.video-title {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 12px;
  line-height: 1.4;
}

.video-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.tag-item {
  padding: 4px 10px;
  background: #222;
  color: #888;
  font-size: 12px;
  border-radius: 4px;
}

.uploader-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  object-fit: cover;
}

.uploader-detail {
  flex: 1;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.name {
  font-size: 14px;
  font-weight: 500;
  color: #fff;
}

.vip-badge {
  height: 16px;
}

.stats {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.follow-btn {
  padding: 6px 16px;
  background: #ec4899;
  color: #fff;
  border: none;
  border-radius: 20px;
  font-size: 13px;
  cursor: pointer;
}

.follow-btn.followed {
  background: #333;
  color: #888;
}

.video-stats {
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #888;
  font-size: 13px;
}

.stat-item.clickable {
  cursor: pointer;
}

.stat-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon svg {
  width: 18px;
  height: 18px;
}

.stat-icon.heart.active {
  color: #ec4899;
}

.stat-icon.star.active {
  color: #ffd700;
}

.recommend-section {
  margin-top: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 12px;
}

.video-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.video-card {
  cursor: pointer;
}

.video-cover {
  position: relative;
  aspect-ratio: 16 / 9;
  border-radius: 8px;
  overflow: hidden;
}

.video-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-views {
  position: absolute;
  bottom: 6px;
  left: 6px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
  font-size: 11px;
  border-radius: 4px;
}

.video-duration {
  position: absolute;
  bottom: 6px;
  right: 6px;
  padding: 2px 6px;
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
  font-size: 11px;
  border-radius: 4px;
}

.video-info {
  padding: 8px 0;
}

.video-info .video-title {
  font-size: 13px;
  color: #fff;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.video-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: #666;
}

.video-tag {
  padding: 2px 6px;
  background: #222;
  border-radius: 2px;
}
</style>
