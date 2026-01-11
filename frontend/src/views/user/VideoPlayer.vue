<template>
  <div class="video-player-page">
    <!-- 返回按钮 -->
    <div class="back-btn" @click="goBack">
      <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
    </div>

    <!-- 视频播放器 -->
    <div class="player-container">
      <!-- 前贴广告 -->
      <div class="pre-roll-ad" v-if="showPreRollAd && preRollAd">
        <div class="ad-video-container">
          <!-- 视频广告 -->
      <video
            v-if="preRollAd.ad_type === 'video'"
            ref="adVideoRef"
            class="ad-video"
            :src="preRollAd.media_url"
            @timeupdate="onAdTimeUpdate"
            @ended="onAdEnded"
            @canplay="onAdCanPlay"
            autoplay
        playsinline
            muted
          />
          <!-- 图片广告 -->
          <div v-else class="ad-image-wrapper" @click="onAdImageClick">
            <img 
              :src="preRollAd.media_url" 
              class="ad-image"
              @load="onAdImageLoad"
            />
        </div>
          <div class="ad-overlay">
            <!-- 倒计时和关闭按钮在同一位置，互斥显示 -->
            <div class="ad-countdown" v-if="!canSkipAd">
              广告 {{ adCountdown }}s
      </div>
            <div class="ad-close-btn" v-else @click="skipAd">
              关闭广告 ✕
          </div>
            <a 
              v-if="preRollAd.target_url" 
              :href="preRollAd.target_url" 
              target="_blank" 
              class="ad-link"
              @click="onAdClick"
            >
              了解更多
            </a>
          </div>
          <div class="ad-label">广告</div>
        </div>
      </div>

      <!-- ArtPlayer 容器 -->
      <div 
        ref="artPlayerRef" 
        class="artplayer-container"
        :class="{ 'hidden-by-ad': showPreRollAd }"
      ></div>

      <!-- 试看倒计时已移除，只保留试看结束后弹窗 -->

      <!-- 已购买/VIP免费标识 -->
      <div class="access-badge" v-if="hasPurchased || isVipFree">
        <span v-if="isVipFree" class="vip-free-badge">
          <svg viewBox="0 0 24 24" width="14" height="14">
            <path fill="currentColor" d="M5 16L3 5l5.5 5L12 4l3.5 6L21 5l-2 11H5z"/>
            </svg>
          VIP免费
            </span>
        <span v-else class="purchased-badge">✓ 已购买</span>
      </div>

      <!-- 试看结束遮罩 - 新样式 -->
      <div class="trial-ended-overlay" v-if="isTrialEnded && !hasPurchased">
        <div class="trial-ended-content">
          <h2 class="trial-ended-title">试看结束</h2>
          <p class="trial-ended-subtitle">开通VIP 永久免费观看</p>
          <div class="trial-ended-actions">
            <button class="share-btn" @click="handleShare">
              分享得3日VIP
            </button>
          <button class="vip-btn" @click="$router.push('/user/vip')">
              开通VIP免费看
          </button>
        </div>
          <!-- 金币购买选项（如果是付费视频） -->
          <div class="coin-purchase-option" v-if="needsPurchase && video.coin_price > 0">
            <span class="divider-text">或</span>
            <div class="coin-price-info" @click="quickPurchaseVideo">
            <span class="coin-icon">🪙</span>
              <span>{{ displayPrice }} 金币购买本片</span>
              <span class="arrow">›</span>
          </div>
          </div>
        </div>
      </div>
    </div>


    <!-- 分享弹窗 -->
    <Teleport to="body">
      <div class="share-modal-overlay" v-if="showShareModal" @click.self="showShareModal = false">
        <div class="share-modal-content">
          <!-- 关闭按钮 -->
          <button class="share-modal-close" @click="showShareModal = false">×</button>
          
          <!-- Logo 和标题 -->
          <div class="share-header">
            <img src="/images/backgrounds/ic_launcher.webp" alt="Logo" class="share-logo" />
            <div class="share-title-info">
              <h3 class="share-site-name">Soul成人版</h3>
              <p class="share-site-desc">全网最全成人视频平台</p>
          </div>
            </div>
          
          <!-- 推广图片 -->
          <div class="share-promo-image">
            <img :src="video.cover_url || '/images/default-cover.webp'" alt="推广图" />
              </div>
          
          <!-- 二维码和邀请信息 -->
          <div class="share-qr-section">
            <div class="share-qrcode">
              <img :src="shareQrCodeUrl" alt="二维码" />
              </div>
            <div class="share-invite-info">
              <div class="invite-code">邀请码 <span>{{ userInviteCode }}</span></div>
              <div class="official-url">官方网址:{{ shareBaseUrl }}</div>
              </div>
            </div>
          
          <!-- 操作按钮 -->
          <div class="share-actions">
            <button class="copy-link-btn" @click="copyShareLink(shareFullUrl)">复制链接</button>
            <button class="save-image-btn" @click="saveShareImage">保存图片</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 会员推广条 -->
    <div class="vip-promo" @click="$router.push('/user/vip')">
      <!-- 非会员样式 -->
      <template v-if="!isVip">
        <span class="promo-text">开通会员 享专属特权</span>
        <div class="promo-btn">
          开通会员 <span class="arrow">›</span>
        </div>
      </template>
      
      <!-- 已是会员样式 -->
      <template v-else>
        <div class="vip-member-center">
          <img 
            v-if="userVipLevel > 0" 
            :src="userVipLevelIcon" 
            class="vip-icon-promo"
          />
          <span class="vip-expire-text">到期时间：{{ formattedVipExpireDate || '永久' }}</span>
        </div>
        <div class="promo-btn upgrade">
          升级会员 <span class="arrow">›</span>
        </div>
      </template>
    </div>

    <!-- 标签页导航 - 始终固定在播放器下方 -->
    <div class="content-tabs">
      <div 
        :class="['tab-item', { active: activeTab === 'intro' }]"
        @click="activeTab = 'intro'"
      >
        简介
      </div>
      <div 
        :class="['tab-item', { active: activeTab === 'comments' }]"
        @click="activeTab = 'comments'"
      >
        评论 ({{ commentTotal }})
      </div>
      <div class="tab-right" @click="showLineSelect = true">
        <span class="line-icon">⚡</span> 线路{{ currentLine }}
      </div>
    </div>

    <!-- ========== 简介内容区 ========== -->
    <div class="intro-content" v-show="activeTab === 'intro'">
      <!-- 视频信息区 -->
      <div class="intro-section">
        <!-- 视频标题 -->
        <h1 class="video-title">{{ video.title }}</h1>
        
        <!-- 标签 -->
        <div class="video-tags">
          <span 
            v-for="tag in video.tags || defaultTags" 
            :key="tag"
            class="tag-item"
          >
            {{ tag }}
          </span>
        </div>

        <!-- 上传者信息 -->
        <div class="uploader-info">
          <img :src="getAvatarUrl(video.uploader_avatar, video.uploader_id || video.id)" class="avatar clickable" @click="goToUserProfile(video.uploader_id)" />
          <div class="uploader-detail">
            <div class="name-row">
              <span class="name clickable" @click="goToUserProfile(video.uploader_id)">{{ video.uploader_name || '匿名用户' }}</span>
              <img 
                v-if="video.uploader_vip_level > 0" 
                :src="getVipLevelIcon(video.uploader_vip_level)" 
                class="vip-badge"
              />
              <span class="badge" v-if="video.is_verified">🔷 至尊</span>
            </div>
            <div class="stats">{{ uploaderStats }}</div>
          </div>
          <button class="follow-btn" :class="{ followed: isUploaderFollowed }" @click="toggleUploaderFollow">
            {{ isUploaderFollowed ? '已关注' : '+ 关注' }}
          </button>
        </div>

        <!-- 视频统计 -->
        <div class="video-stats">
          <div class="stat-item views">
            <span class="stat-value">{{ formatViewCount(video.view_count) }}观看量</span>
          </div>
          <div class="stat-item clickable" @click="toggleLike">
            <span :class="['stat-icon', 'heart', { active: isLiked }]">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
              </svg>
            </span>
            <span class="stat-value">{{ formatCount(video.like_count) }}</span>
          </div>
          <div class="stat-item clickable" @click="toggleFavorite">
            <span :class="['stat-icon', 'star', { active: isFavorited }]">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/>
              </svg>
            </span>
            <span class="stat-value">{{ video.favorite_count || 0 }}</span>
          </div>
          <div class="stat-item clickable" @click="shareVideo">
            <span class="stat-icon share">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92s2.92-1.31 2.92-2.92-1.31-2.92-2.92-2.92z"/>
              </svg>
            </span>
            <span class="stat-label">分享</span>
          </div>
          <div class="stat-item clickable" @click="downloadVideo">
            <span class="stat-icon download" :class="{ 'vip-feature': !isVip }">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
              </svg>
              <span v-if="!isVip" class="vip-badge">VIP</span>
            </span>
            <span class="stat-label">下载</span>
          </div>
        </div>
      </div>

      <!-- 图标广告位 - 循环滚动 -->
      <div class="ad-icons-section" v-if="iconAds.length > 0">
        <div class="ad-icons-scroll" ref="adIconsScrollRef">
          <div class="ad-icons-track">
            <div 
              v-for="ad in iconAds" 
              :key="'a-' + ad.id" 
              class="ad-icon-item"
              @click="handleAdClick(ad)"
            >
              <div class="icon-wrap">
                <img v-if="ad.image" :src="ad.image" :alt="ad.name" />
                <span v-else class="icon-emoji">{{ ad.icon }}</span>
              </div>
              <span class="icon-name">{{ ad.name }}</span>
            </div>
            <!-- 复制一份用于无缝循环 -->
            <div 
              v-for="ad in iconAds" 
              :key="'b-' + ad.id" 
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

      <!-- 推荐标签 -->
      <div class="recommend-tabs">
        <div 
          v-for="(tab, index) in recommendTabs" 
          :key="index"
          :class="['rec-tab', { active: activeRecTab === index }]"
          @click="activeRecTab = index"
        >
          {{ tab }}
        </div>
      </div>

      <!-- 推荐视频列表 -->
      <div class="recommend-section">
        <div class="video-list double-column">
          <div 
            v-for="rec in recommendVideos" 
            :key="rec.id"
            class="video-card"
            @click="handleVideoClick(rec)"
            @mouseenter="startPreview(rec)"
            @mouseleave="stopPreview(rec)"
            @touchstart.passive="onTouchStart"
          >
            <div class="video-cover">
              <img 
                :src="getCoverUrl(rec.cover_url)" 
                :alt="rec.title"
                :class="{ 'hidden': isPreviewPlaying(rec.id) }"
              />
              <!-- 视频预览 - 禁用预加载避免与主播放器抢资源 -->
              <video
                v-if="rec.preview_url"
                :ref="el => setPreviewRef(rec.id, el)"
                :data-src="getPreviewUrl(rec.preview_url)"
                :class="['preview-video', { 'visible': isPreviewPlaying(rec.id) }]"
                muted
                loop
                playsinline
                preload="none"
              ></video>
              <div class="cover-views">
                <span class="play-icon">▶</span>
                <span>{{ formatViewCount(rec.view_count) }}</span>
              </div>
              <div class="video-duration">{{ formatDuration(rec.duration) }}</div>
            </div>
            <div class="video-info">
              <p class="video-title">{{ rec.title }}</p>
              <div class="video-meta">
                <span class="video-tag" v-if="rec.tags && rec.tags.length > 0">{{ rec.tags[0] }}</span>
                <span class="video-tag" v-else-if="rec.category_name">{{ rec.category_name }}</span>
                <span class="video-tag" v-else>精选</span>
                <span class="video-comments">评论 {{ rec.comment_count || 0 }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ========== 评论内容区 ========== -->
    <div class="comments-content" v-show="activeTab === 'comments'">
      <!-- 评论列表 -->
      <div class="comment-list-wrapper">
        <!-- 官方公告 -->
        <div v-if="announcement && announcement.enabled" class="comment-item official-announcement">
          <img :src="announcement.avatar || '/images/avatars/icon_avatar_1.webp'" class="avatar" />
          <div class="comment-body">
            <div class="comment-user">
              <span class="username official-name">{{ announcement.name }}</span>
              <!-- 至尊图标 -->
              <img src="/images/backgrounds/super_vip_blue.webp" class="supreme-vip-icon" />
            </div>
            <p class="comment-text official-text">{{ announcement.content }}</p>
            <div class="comment-meta">
              <span class="time">{{ formatAnnouncementTime(announcement.updated_at) }}</span>
            </div>
          </div>
        </div>

        <div class="comment-list" v-if="comments.length > 0">
          <div v-for="comment in comments" :key="comment.id" :class="['comment-item', { 'is-pinned': comment.is_pinned, 'is-official': comment.is_official }]">
            <img :src="getAvatarUrl(comment.user_avatar, comment.user_id || comment.id)" class="avatar clickable" @click="goToUserProfile(comment.user_id)" />
            <div class="comment-body">
              <div class="comment-user">
                <span class="username clickable" @click="goToUserProfile(comment.user_id)">{{ comment.user_name }}</span>
                <!-- 显示VIP等级图标 -->
                <img 
                  v-if="comment.user_vip_level > 0" 
                  :src="getVipLevelIcon(comment.user_vip_level)" 
                  class="vip-badge-sm"
                />
                <span v-if="comment.is_pinned" class="pin-badge">📌 置顶</span>
              </div>
              <p class="comment-text">{{ comment.content }}</p>
              <!-- 评论图片 -->
              <div v-if="comment.image_url" class="comment-image" @click="previewImage(comment.image_url)">
                <img :src="comment.image_url" alt="comment image" />
              </div>
              <div class="comment-meta">
                <span class="time">{{ formatCommentTime(comment.created_at) }}</span>
                <span 
                  :class="['like-btn', { liked: comment.is_liked }]" 
                  @click="likeComment(comment)"
                >
                  {{ comment.is_liked ? '❤️' : '🤍' }} {{ comment.like_count || 0 }}
                </span>
                <span class="reply-btn" @click="startReply(comment)">回复</span>
                <span 
                  v-if="canDeleteComment(comment)" 
                  class="delete-btn"
                  @click="deleteComment(comment)"
                >删除</span>
              </div>

              <!-- 回复列表 -->
              <div v-if="comment.replies && comment.replies.length > 0" class="reply-list">
                <div v-for="reply in comment.replies" :key="reply.id" class="reply-item">
                  <img :src="getAvatarUrl(reply.user_avatar, reply.user_id || reply.id)" class="reply-avatar clickable" @click="goToUserProfile(reply.user_id)" />
                  <div class="reply-body">
                    <span class="username clickable" @click="goToUserProfile(reply.user_id)">{{ reply.user_name }}</span>
                    <span v-if="reply.is_official" class="official-badge small">官方</span>
                    <img 
                      v-if="reply.user_vip_level > 0" 
                      :src="getVipLevelIcon(reply.user_vip_level)" 
                      class="vip-badge-tiny"
                    />
                    <p class="reply-text">{{ reply.content }}</p>
                    <!-- 回复图片 -->
                    <div v-if="reply.image_url" class="comment-image small" @click="previewImage(reply.image_url)">
                      <img :src="reply.image_url" alt="reply image" />
                    </div>
                    <div class="reply-meta">
                      <span class="time">{{ formatCommentTime(reply.created_at) }}</span>
                      <span 
                        :class="['like-btn', { liked: reply.is_liked }]" 
                        @click="likeComment(reply)"
                      >{{ reply.is_liked ? '❤️' : '🤍' }} {{ reply.like_count || 0 }}</span>
                      <span class="reply-btn" @click="startReply(comment, reply)">回复</span>
                    </div>
                  </div>
                </div>
                <div 
                  v-if="comment.reply_count > comment.replies.length" 
                  class="more-replies"
                  @click="loadMoreReplies(comment)"
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
        <div class="load-more" v-if="hasMoreComments || loadingComments">
          <button @click="loadMoreComments" :disabled="loadingComments" class="load-more-btn">
            <span v-if="loadingComments" class="loading-spinner">
              <svg viewBox="0 0 24 24" class="spin-icon">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" fill="none" stroke-dasharray="31.4 31.4" />
              </svg>
              加载中...
            </span>
            <span v-else>
              📜 加载更多评论
            </span>
          </button>
        </div>
        
        <!-- 没有更多评论提示 -->
        <div class="no-more-comments" v-if="!hasMoreComments && comments.length > 0 && !loadingComments">
          <span>—— 已加载全部评论 ——</span>
        </div>
      </div>

      <!-- 底部评论输入框 -->
      <div class="comment-input-bar">
        <!-- 非VIP提示 -->
        <div v-if="!isVip" class="vip-comment-tip" @click="$router.push('/user/vip')">
          <span class="tip-icon">👑</span>
          <span class="tip-text">开通VIP即可发表评论</span>
          <span class="tip-btn">立即开通 ›</span>
        </div>
        
        <!-- VIP评论输入区 -->
        <div v-else class="input-area">
          <!-- 图片预览 -->
          <div v-if="commentImage" class="image-preview">
            <img :src="commentImagePreview" alt="preview" />
            <span class="remove-image" @click="removeCommentImage">×</span>
          </div>
          
          <div class="input-row">
            <input 
              v-model="newComment"
              type="text"
              :placeholder="replyTarget ? `回复 @${replyTarget.user_name}` : '说点什么吧...'"
              @keyup.enter="submitComment"
              ref="commentInputRef"
            />
            <div class="input-actions">
              <span v-if="replyTarget" class="cancel-btn" @click="cancelReply">取消</span>
              <span class="emoji-btn" @click="showEmojiPicker = !showEmojiPicker">😊</span>
              <label class="image-btn">
                <input type="file" accept="image/*" @change="handleImageSelect" hidden />
                🖼️
              </label>
              <span class="send-btn" @click="submitComment" :class="{ disabled: submittingComment }">
                <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                </svg>
              </span>
            </div>
          </div>
          
          <!-- 表情选择器 -->
          <div v-if="showEmojiPicker" class="emoji-picker">
            <div class="emoji-grid">
              <span v-for="emoji in emojiList" :key="emoji" class="emoji-item" @click="insertEmoji(emoji)">
                {{ emoji }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 图片灯箱预览 -->
    <Teleport to="body">
      <div v-if="lightboxVisible" class="lightbox-overlay" @click.self="closeLightbox">
        <div class="lightbox-container">
          <!-- 关闭按钮 -->
          <button class="lightbox-close" @click="closeLightbox">✕</button>
          
          <!-- 图片 -->
          <img 
            :src="lightboxImage" 
            class="lightbox-image"
            :style="{ transform: `scale(${lightboxScale})` }"
            @click.stop
          />
          
          <!-- 控制按钮 -->
          <div class="lightbox-controls">
            <button class="control-btn" @click="zoomOut" title="缩小">
              <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
                <path d="M19 13H5v-2h14v2z"/>
              </svg>
            </button>
            <button class="control-btn" @click="resetZoom" title="重置">
              {{ Math.round(lightboxScale * 100) }}%
            </button>
            <button class="control-btn" @click="zoomIn" title="放大">
              <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
                <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/utils/api'
import axios from 'axios'
import Artplayer from 'artplayer'
import Hls from 'hls.js'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'
import { useAbortController } from '@/composables/useAbortController'
import { useTimers, useVideoCleanup, useEventListeners } from '@/composables/useCleanup'
import { formatCount, formatDuration, formatViewCount } from '@/utils/format'
import { VIP_LEVEL_ICONS } from '@/constants/vip'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const route = useRoute()
const router = useRouter()

// 请求取消控制器
const { signal: abortSignal } = useAbortController()

// 定时器管理
const timers = useTimers()

// 视频资源管理
const videoCleanup = useVideoCleanup()

// 事件监听器管理
const events = useEventListeners()

const videoRef = ref(null)  // 保留用于兼容
const artPlayerRef = ref(null)  // ArtPlayer 容器
const commentInputRef = ref(null)
let artInstance = null  // ArtPlayer 实例
const video = ref({})
const comments = ref([])
const recommendVideos = ref([])
const iconAds = ref([])
const newComment = ref('')
const activeTab = ref('intro')
const activeRecTab = ref(0)
const isPlaying = ref(false)
const isLiked = ref(false)
const isFavorited = ref(false)
const isUploaderFollowed = ref(false)
const isVip = ref(false)
const userVipLevel = ref(0)
const userVipLevelNameFromApi = ref('非VIP')  // 从API获取的VIP等级名称
const userVipExpireDate = ref(null)
const currentLine = ref(1)
const showLineSelect = ref(false)

// 付费视频相关
const hasPurchased = ref(false)
const needsPurchase = ref(false)
const isTrialEnded = ref(false)
const showPurchaseModal = ref(false)
const showShareModal = ref(false)  // 分享弹窗
const purchasing = ref(false)
const userCoins = ref(0)
const trialWatchTime = ref(0)
const isVipFree = ref(false)  // VIP免费观看
const currentPlayTime = ref(0)  // 当前播放时间

// 分享相关
const userInviteCode = ref('3AUUHR')  // 用户邀请码
const shareBaseUrl = computed(() => window.location.origin.replace(/^https?:\/\//, ''))
const shareFullUrl = computed(() => `${window.location.origin}/user/video/${video.value.id}?ref=${userInviteCode.value}`)
const shareQrCodeUrl = computed(() => `https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${encodeURIComponent(shareFullUrl.value)}`)

// 前贴广告相关
const adVideoRef = ref(null)
const preRollAd = ref(null)       // 当前广告
const showPreRollAd = ref(false)  // 是否显示广告
const adCountdown = ref(5)        // 广告倒计时
const canSkipAd = ref(false)      // 是否可以跳过广告
const adPlayed = ref(false)       // 广告是否已播放过

// 获取前贴广告
const fetchPreRollAd = async () => {
  // VIP用户不显示广告
  if (isVip.value) {
    console.log('[Ad] VIP user, skip ad')
    return
  }
  
  try {
    const res = await api.get('/ads', {
      params: { position: 'video_pre', limit: 1 }
    })
    const ads = res.data || res || []
    if (ads.length > 0) {
      preRollAd.value = ads[0]
      console.log('[Ad] Loaded pre-roll ad:', preRollAd.value.title)
      
      // 自动开始播放广告
      setTimeout(() => {
        startPreRollAd()
      }, 500)
    }
  } catch (error) {
    console.log('[Ad] Failed to load ad:', error)
  }
}

// 开始播放广告
const startPreRollAd = () => {
  if (!preRollAd.value || adPlayed.value || isVip.value) {
    return false
  }
  
  showPreRollAd.value = true
  adCountdown.value = preRollAd.value.duration || 5
  adPlayed.value = true
  
  console.log('[Ad] Starting pre-roll ad')
  return true
}

// 广告时间更新
const onAdTimeUpdate = () => {
  if (adVideoRef.value) {
    const currentTime = adVideoRef.value.currentTime
    const duration = preRollAd.value?.duration || 5
    const remaining = Math.max(0, Math.ceil(duration - currentTime))
    adCountdown.value = remaining
    
    // 5秒倒计时结束后才显示关闭按钮
    if (remaining <= 0) {
      canSkipAd.value = true
    }
  }
}

// 广告可以播放
const onAdCanPlay = () => {
  if (adVideoRef.value) {
    adVideoRef.value.play().catch(() => {
      // 自动播放被阻止，静音播放
      adVideoRef.value.muted = true
      adVideoRef.value.play()
    })
  }
}

// 广告播放结束（视频广告播完后显示关闭按钮，不自动关闭）
const onAdEnded = () => {
  console.log('[Ad] Ad video ended, show close button')
  canSkipAd.value = true  // 显示关闭按钮
  adCountdown.value = 0
  
  // 视频广告播完后循环播放，直到用户点击关闭
  if (adVideoRef.value && preRollAd.value?.ad_type === 'video') {
    adVideoRef.value.currentTime = 0
    adVideoRef.value.play().catch(() => {})
  }
}

// 关闭广告（用户点击关闭按钮）
const skipAd = () => {
  console.log('[Ad] Close ad by user')
  showPreRollAd.value = false
  
  // 清除广告计时器
  if (adTimerId) {
    timers.clearInterval(adTimerId)
    adTimerId = null
  }
  
  if (adVideoRef.value) {
    adVideoRef.value.pause()
  }
  
  // 开始播放正片
  timers.setTimeout(() => {
    if (artInstance) {
      isPlaying.value = true
      artInstance.play()
    }
  }, 100)
}

// 广告点击
const onAdClick = async () => {
  if (preRollAd.value?.id) {
    try {
      await api.post(`/ads/${preRollAd.value.id}/click`)
    } catch (e) {
      // 忽略错误
    }
  }
}

// 图片广告加载完成，开始倒计时
let adTimerId = null
const onAdImageLoad = () => {
  const duration = preRollAd.value?.duration || 5
  adCountdown.value = duration
  canSkipAd.value = false
  
  // 开始倒计时（只控制关闭按钮显示，不自动关闭）
  adTimerId = timers.setInterval(() => {
    adCountdown.value--
    // 倒计时结束后显示关闭按钮
    if (adCountdown.value <= 0) {
      timers.clearInterval(adTimerId)
      adTimerId = null
      canSkipAd.value = true  // 显示关闭按钮
    }
  }, 1000)
}

// 图片广告点击
const onAdImageClick = () => {
  if (preRollAd.value?.target_url) {
    onAdClick()
    window.open(preRollAd.value.target_url, '_blank')
  }
}

// 试看倒计时相关
const showTrialCountdown = computed(() => {
  // 只有需要购买且未购买、有试看时间、不是VIP免费的情况下显示
  if (!needsPurchase.value || hasPurchased.value || isTrialEnded.value || isVipFree.value) {
    return false
  }
  const trialLimit = video.value.free_preview_seconds || 0
  if (trialLimit <= 0) return false
  // 剩余10秒内开始显示倒计时
  return currentPlayTime.value >= (trialLimit - 10) && currentPlayTime.value < trialLimit
})

const remainingTrialTime = computed(() => {
  const trialLimit = video.value.free_preview_seconds || 30
  const remaining = Math.max(0, Math.ceil(trialLimit - currentPlayTime.value))
  return remaining
})

// 获取VIP等级名称 - 使用后端返回的名称
const userVipLevelName = computed(() => {
  return userVipLevelNameFromApi.value || '会员'
})

// 获取VIP等级图标
const userVipLevelIcon = computed(() => {
  return VIP_LEVEL_ICONS[userVipLevel.value] || ''
})

// 格式化VIP到期时间
const formattedVipExpireDate = computed(() => {
  if (!userVipExpireDate.value) return ''
  const date = new Date(userVipExpireDate.value)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}.${month}.${day}`
})

// 计算实际价格（考虑VIP折扣）
const displayPrice = computed(() => {
  if (!video.value.coin_price) return 0
  if (isVip.value && video.value.vip_discount && video.value.vip_discount < 1) {
    return Math.ceil(video.value.coin_price * video.value.vip_discount)
  }
  return video.value.coin_price
})

// 格式化试看时间
const formatTrialTime = (seconds) => {
  if (!seconds) return '0秒'
  if (seconds < 60) return `${seconds}秒`
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return s > 0 ? `${m}分${s}秒` : `${m}分钟`
}

// 评论相关
const commentTotal = ref(0)
const commentPage = ref(1)
const commentPageSize = ref(10)

// 公告
const announcement = ref(null)
const commentSortBy = ref('newest')
const hasMoreComments = ref(false)
const loadingComments = ref(false)
const submittingComment = ref(false)
const replyTarget = ref(null) // 回复的目标评论
const currentUserId = ref(null) // 当前用户ID
const isAdmin = ref(false) // 是否管理员

// 表情包和图片上传
const showEmojiPicker = ref(false)
const commentImage = ref(null)
const commentImagePreview = ref('')

// 表情包列表
const emojiList = [
  '😀', '😂', '🤣', '😊', '😍', '🥰', '😘', '😜', '🤪', '😎',
  '🥳', '😇', '🤩', '😋', '😛', '🤤', '😏', '😒', '😔', '😢',
  '😭', '😤', '😠', '🤬', '😱', '😰', '😥', '🤧', '😷', '🤒',
  '👍', '👎', '👏', '🙏', '💪', '❤️', '💔', '💯', '🔥', '✨',
  '🎉', '🎊', '💎', '🏆', '🥇', '⭐', '🌟', '💫', '🌈', '☀️',
  '🌙', '⚡', '💥', '💢', '💤', '👻', '💀', '👽', '🤖', '🐶',
  '🐱', '🐰', '🦊', '🐻', '🐼', '🐯', '🦁', '🐮', '🐷', '🐸'
]

const defaultTags = ['主播', '热门']
const recommendTabs = ['视频推荐', '动漫推荐', '漫画推荐']

// 获取默认头像路径（共52个）
const getDefaultAvatarPath = (userId) => {
  const totalAvatars = 52
  const index = (userId % totalAvatars)
  
  if (index < 17) {
    return `/images/avatars/icon_avatar_${index + 1}.webp`
  } else if (index < 32) {
    const num = String(index - 17 + 1).padStart(3, '0')
    return `/images/avatars/DM_20251217202131_${num}.JPEG`
  } else {
    const num = String(index - 32 + 1).padStart(3, '0')
    return `/images/avatars/DM_20251217202341_${num}.JPEG`
  }
}

// 获取当前用户头像
const currentUserAvatar = computed(() => {
  const id = currentUserId.value || 1
  return getDefaultAvatarPath(id)
})

// 预览相关状态
const previewRefs = ref({})
const previewingVideoId = ref(null)
let previewTimerId = null
const isTouchMode = ref(false)

// 设置预览视频引用
const setPreviewRef = (id, el) => {
  if (el) {
    previewRefs.value[id] = el
    videoCleanup.registerVideo(`preview_${id}`, el)
  }
}

// 获取预览视频URL
const getPreviewUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return url
}

// 检查视频是否正在预览
const isPreviewPlaying = (videoId) => {
  return previewingVideoId.value === videoId
}

// 播放预览
const playPreview = (video) => {
  // 停止其他预览并卸载其视频源
  if (previewingVideoId.value && previewingVideoId.value !== video.id) {
    const oldVideoEl = previewRefs.value[previewingVideoId.value]
    if (oldVideoEl) {
      oldVideoEl.pause()
      oldVideoEl.currentTime = 0
      oldVideoEl.src = ''  // 卸载源释放资源
    }
  }
  
  previewingVideoId.value = video.id
  const videoEl = previewRefs.value[video.id]
  if (videoEl) {
    // 懒加载：从 data-src 加载视频源
    if (!videoEl.src && videoEl.dataset.src) {
      videoEl.src = videoEl.dataset.src
    }
    videoEl.currentTime = 0
    videoEl.play().catch(err => {
      console.log('预览播放失败:', err)
    })
  }
}

// 停止当前预览
const stopCurrentPreview = () => {
  if (previewingVideoId.value) {
    const videoEl = previewRefs.value[previewingVideoId.value]
    if (videoEl) {
      videoEl.pause()
      videoEl.currentTime = 0
    }
    previewingVideoId.value = null
  }
}

// 开始预览 (PC鼠标悬停)
const startPreview = (video) => {
  if (!video.preview_url || isTouchMode.value) return
  
  previewingVideoId.value = video.id
  
  if (previewTimerId) timers.clearTimeout(previewTimerId)
  previewTimerId = timers.setTimeout(() => {
    if (previewingVideoId.value === video.id) {
      playPreview(video)
    }
  }, 300)
}

// 停止预览 (PC鼠标离开)
const stopPreview = (video) => {
  if (isTouchMode.value) return
  
  if (previewTimerId) {
    timers.clearTimeout(previewTimerId)
    previewTimerId = null
  }
  
  if (previewingVideoId.value === video.id) {
    previewingVideoId.value = null
    const videoEl = previewRefs.value[video.id]
    if (videoEl) {
      videoEl.pause()
      videoEl.currentTime = 0
      videoEl.src = ''  // 卸载源释放资源
    }
  }
}

// 触摸开始时启用触摸模式
const onTouchStart = () => {
  isTouchMode.value = true
}

// 视频卡片点击处理
const handleVideoClick = (video) => {
  // 触摸模式：第一次点击预览，第二次进入视频
  if (isTouchMode.value && video.preview_url) {
    if (previewingVideoId.value === video.id) {
      // 正在预览，进入视频
      stopCurrentPreview()
      goToVideo(video.id)
    } else {
      // 开始预览
      playPreview(video)
    }
    return
  }
  
  // PC模式：直接进入视频
  goToVideo(video.id)
}

const uploaderStats = computed(() => {
  const videos = video.value.uploader_videos || 0
  const followers = video.value.uploader_followers || 0
  return `${videos} 作品  ${formatCount(followers)} 粉丝`
})

const getVideoUrl = () => {
  if (video.value.hls_url) {
    return video.value.hls_url
  }
  return video.value.original_url || ''
}

const getCoverUrl = (url) => {
  if (!url) return '/placeholder.webp'
  if (url.startsWith('http') || url.startsWith('/')) return url
  return '/' + url
}

// 根据用户ID获取预设头像
const getAvatarUrl = (avatar, userId) => {
  if (avatar) return avatar
  const numericId = parseInt(userId) || 1
  return getDefaultAvatarPath(numericId)
}

// 获取VIP等级图标（使用统一常量）
const getVipLevelIcon = (level) => {
  return VIP_LEVEL_ICONS[level] || ''
}

const fetchVideo = async () => {
  const videoId = route.params.id
  if (!videoId) {
    console.error('视频ID不存在')
    router.replace('/')
    return
  }
  try {
    const res = await api.get(`/videos/${videoId}`, { signal: abortSignal })
    video.value = res.data || res
    
    // 检查是否需要VIP权限
    if (video.value.needs_vip) {
      isVip.value = false
    }
    
    // 检查是否需要付费
    await checkVideoPurchase()
    
    // 检查是否已关注上传者
    if (video.value.uploader_id) {
      try {
        const followRes = await api.get(`/users/${video.value.uploader_id}/follow/status`, { signal: abortSignal })
        isUploaderFollowed.value = followRes.data?.is_followed || false
      } catch (e) {
        // 忽略错误
      }
    }
    
    await api.post(`/videos/${videoId}/view`)
  } catch (error) {
    if (error.name === 'CanceledError' || error.name === 'AbortError') return
    console.error('获取视频失败:', error)
    // 其他错误使用默认数据
    video.value = {
      id: videoId,
      title: '视频加载失败',
      description: '请稍后重试',
      cover_url: '/uploads/thumbnails/3.webp',
      hls_url: '',
      duration: 0,
      view_count: 0,
      like_count: 0,
      favorite_count: 0,
      is_vip_only: false,
      is_verified: false,
      uploader_name: '未知',
      uploader_avatar: '',
      uploader_videos: 0,
      uploader_followers: 0,
      tags: []
    }
  }
}

// 检查视频购买状态
const checkVideoPurchase = async () => {
  const v = video.value
  
  // 重置所有试看/购买状态
  isVipFree.value = false
  isTrialEnded.value = false
  hasPurchased.value = false
  needsPurchase.value = false
  currentPlayTime.value = 0
  trialWatchTime.value = 0
  
  // 免费视频不需要购买
  if (!v.pay_type || v.pay_type === 'free') {
    needsPurchase.value = false
    hasPurchased.value = true
    return
  }
  
  // VIP免费视频
  if (v.pay_type === 'vip_free' && isVip.value) {
    needsPurchase.value = false
    hasPurchased.value = true
    isVipFree.value = true
    return
  }
  
  // 检查VIP等级免费（黄金至尊及以上全免费）
  if (userVipLevel.value >= 5) {
    needsPurchase.value = false
    hasPurchased.value = true
    isVipFree.value = true
    return
  }
  
  // 检查VIP等级免费
  if (v.vip_free_level > 0 && userVipLevel.value >= v.vip_free_level) {
    needsPurchase.value = false
    hasPurchased.value = true
    isVipFree.value = true
    return
  }
  
  // 需要付费，检查是否已购买
  needsPurchase.value = true
  
  try {
    const res = await api.get(`/coins/purchase/video/${v.id}/check`, { signal: abortSignal })
    const data = res.data || res
    hasPurchased.value = data.purchased === true || data.can_watch === true
    
    // 检查是否VIP免费
    if (data.is_vip_free) {
      isVipFree.value = true
      hasPurchased.value = true
      needsPurchase.value = false
    }
  } catch (error) {
    if (error.name !== 'CanceledError' && error.name !== 'AbortError') {
      console.log('检查购买状态失败:', error)
    }
    hasPurchased.value = false
  }
}

// 获取用户金币余额
const fetchUserCoins = async () => {
  try {
    const res = await api.get('/coins/balance', { signal: abortSignal })
    const data = res.data || res
    userCoins.value = data.balance || 0
  } catch (error) {
    if (error.name !== 'CanceledError' && error.name !== 'AbortError') {
      console.log('获取金币余额失败')
    }
    userCoins.value = 0
  }
}

// 快速购买视频（无弹窗）
const quickPurchaseVideo = async () => {
  // 先获取最新余额
  await fetchUserCoins()
  
  // 余额不足，跳转充值页
  if (userCoins.value < displayPrice.value) {
    ElMessage.warning('余额不足，请先充值')
    router.push('/user/coins')
    return
  }
  
  // 余额充足，直接购买
  if (purchasing.value) return
  purchasing.value = true
  
  try {
    const res = await api.post(`/coins/purchase/video/${video.value.id}`)
    const data = res.data || res
    
    if (data.success) {
      hasPurchased.value = true
      isTrialEnded.value = false
      userCoins.value = data.balance_after || (userCoins.value - displayPrice.value)
      
      // 重新加载视频获取完整播放地址
      await fetchVideo()
      await nextTick()
      initArtPlayer()
      
      ElMessage.success('购买成功！')
    } else {
      ElMessage.error(data.message || '购买失败')
    }
  } catch (error) {
    console.error('购买失败:', error)
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('购买失败，请重试')
    }
  } finally {
    purchasing.value = false
  }
}

// 确认购买（保留备用）
const confirmPurchase = async () => {
  if (purchasing.value) return
  
  if (userCoins.value < displayPrice.value) {
    router.push('/user/coins')
    return
  }
  
  purchasing.value = true
  
  try {
    const res = await api.post(`/coins/purchase/video/${video.value.id}`)
    const data = res.data || res
    
    if (data.success) {
      hasPurchased.value = true
      isTrialEnded.value = false
      userCoins.value = data.balance_after || (userCoins.value - displayPrice.value)
      
      // 重新加载视频获取完整播放地址
      await fetchVideo()
      await nextTick()
      initArtPlayer()
      
      alert('购买成功！')
    } else {
      alert(data.message || '购买失败')
    }
  } catch (error) {
    console.error('购买失败:', error)
    if (error.response?.data?.detail) {
      alert(error.response.data.detail)
    } else {
      alert('购买失败，请重试')
    }
  } finally {
    purchasing.value = false
  }
}


// 获取评论区公告
const fetchAnnouncement = async () => {
  try {
    const res = await api.get('/settings/comment-announcement', { signal: abortSignal })
    announcement.value = res.data || res
  } catch (error) {
    if (error.name !== 'CanceledError' && error.name !== 'AbortError') {
      console.log('获取公告失败:', error)
    }
  }
}

// 格式化公告时间
const formatAnnouncementTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

const fetchComments = async (reset = true) => {
  const videoId = route.params.id
  if (!videoId) return
  if (reset) {
    commentPage.value = 1
    loadingComments.value = true
  }
  
  try {
    const res = await api.get(`/comments/video/${videoId}`, {
      params: {
        page: commentPage.value,
        page_size: commentPageSize.value,
        sort_by: commentSortBy.value
      },
      signal: abortSignal
    })
    const data = res.data || res
    
    if (reset) {
      comments.value = data.items || []
    } else {
      comments.value = [...comments.value, ...(data.items || [])]
    }
    
    commentTotal.value = data.total || 0
    hasMoreComments.value = (commentPage.value * commentPageSize.value) < commentTotal.value
  } catch (error) {
    if (error.name !== 'CanceledError' && error.name !== 'AbortError') {
      console.log('获取评论失败:', error)
    }
    if (reset) comments.value = []
  } finally {
    loadingComments.value = false
  }
}

// 加载更多评论
const loadMoreComments = async () => {
  if (loadingComments.value || !hasMoreComments.value) return
  loadingComments.value = true
  commentPage.value++
  await fetchComments(false)
}

// 改变评论排序
const changeCommentSort = async (sortBy) => {
  if (commentSortBy.value === sortBy) return
  commentSortBy.value = sortBy
  await fetchComments(true)
}

// 判断是否可以删除评论（仅管理员）
const canDeleteComment = () => {
  return isAdmin.value
}

// 开始回复
const startReply = (parentComment, replyToComment = null) => {
  replyTarget.value = {
    parent_id: parentComment.id,
    user_name: replyToComment ? replyToComment.user_name : parentComment.user_name
  }
  // 聚焦输入框
  setTimeout(() => {
    commentInputRef.value?.focus()
  }, 100)
}

// 取消回复
const cancelReply = () => {
  replyTarget.value = null
  newComment.value = ''
  commentImage.value = null
  commentImagePreview.value = ''
  showEmojiPicker.value = false
}

// 插入表情
const insertEmoji = (emoji) => {
  newComment.value += emoji
  showEmojiPicker.value = false
  commentInputRef.value?.focus()
}

// 选择图片
const handleImageSelect = (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  // 检查文件大小（最大5MB）
  if (file.size > 5 * 1024 * 1024) {
    alert('图片大小不能超过5MB')
    return
  }
  
  // 检查文件类型
  if (!file.type.startsWith('image/')) {
    alert('请选择图片文件')
    return
  }
  
  commentImage.value = file
  commentImagePreview.value = URL.createObjectURL(file)
}

// 移除图片
const removeCommentImage = () => {
  commentImage.value = null
  commentImagePreview.value = ''
}

// 图片灯箱预览
const lightboxVisible = ref(false)
const lightboxImage = ref('')
const lightboxScale = ref(1)

const previewImage = (url) => {
  lightboxImage.value = url
  lightboxScale.value = 1
  lightboxVisible.value = true
}

const closeLightbox = () => {
  lightboxVisible.value = false
  lightboxImage.value = ''
  lightboxScale.value = 1
}

const zoomIn = () => {
  if (lightboxScale.value < 3) {
    lightboxScale.value += 0.5
  }
}

const zoomOut = () => {
  if (lightboxScale.value > 0.5) {
    lightboxScale.value -= 0.5
  }
}

const resetZoom = () => {
  lightboxScale.value = 1
}

// 加载更多回复
const loadMoreReplies = async (comment) => {
  // TODO: 实现加载更多回复的API
  console.log('加载更多回复:', comment.id)
}

const fetchRecommend = async () => {
  try {
    // 使用随机排序获取推荐视频
    const res = await api.get('/videos', { params: { page: 1, page_size: 12, sort_by: 'random' }, signal: abortSignal })
    const data = res.data || res
    if (data.items && data.items.length > 0) {
      const currentId = parseInt(route.params.id)
      // 过滤当前视频
      recommendVideos.value = data.items.filter(v => v.id !== currentId).slice(0, 10)
    } else {
      loadMockRecommend()
    }
  } catch (error) {
    if (error.name !== 'CanceledError' && error.name !== 'AbortError') {
      loadMockRecommend()
    }
  }
}

const fetchIconAds = async () => {
  try {
    const res = await axios.get('/api/v1/ads/icons', { signal: abortSignal })
    iconAds.value = (res.data || []).filter(ad => ad.is_active !== false)
  } catch (error) {
    if (error.name !== 'CanceledError' && error.name !== 'AbortError') {
      console.log('获取图标广告失败')
    }
  }
}

const loadMockRecommend = () => {
  recommendVideos.value = [
    { id: 101, title: '极品外国女神 超美嫩穴 初下海被操喷水！', cover_url: '/uploads/thumbnails/3.webp', duration: 4099, view_count: 1098000 },
    { id: 102, title: '正宗大学生宿舍直播道具插逼骚话连篇', cover_url: '/uploads/thumbnails/3.webp', duration: 1608, view_count: 1752000 },
    { id: 103, title: '推荐视频3', cover_url: '/uploads/thumbnails/3.webp', duration: 3200, view_count: 12300 },
    { id: 104, title: '推荐视频4', cover_url: '/uploads/thumbnails/3.webp', duration: 1500, view_count: 4500 }
  ]
}

// 初始化 ArtPlayer
const initArtPlayer = () => {
  if (!artPlayerRef.value) return
  
  const videoUrl = getVideoUrl()
  if (!videoUrl) return
  
  // 销毁旧实例
  if (artInstance) {
    artInstance.destroy()
    artInstance = null
  }
  
  // 创建 ArtPlayer 实例
  artInstance = new Artplayer({
    container: artPlayerRef.value,
    url: videoUrl,
    poster: getCoverUrl(video.value.cover_url),
    volume: 0.7,
    isLive: false,
    muted: false,
    autoplay: false,
    pip: true,
    autoSize: false,
    autoMini: true,
    screenshot: false,
    setting: true,
    loop: false,
    flip: true,
    playbackRate: true,
    aspectRatio: true,
    fullscreen: true,
    fullscreenWeb: true,
    subtitleOffset: false,
    miniProgressBar: true,
    mutex: true,
    backdrop: true,
    playsInline: true,
    autoPlayback: true,
    airplay: true,
    theme: '#ec4899',
    lang: 'zh-cn',
    moreVideoAttr: {
      crossOrigin: 'anonymous',
    },
    // HLS 支持 - 优化缓冲设置
    customType: {
      m3u8: function playM3u8(video, url, art) {
        if (Hls.isSupported()) {
          if (art.hls) art.hls.destroy()
          const hls = new Hls({
            // 缓冲优化设置
            maxBufferLength: 30,           // 最大缓冲30秒
            maxMaxBufferLength: 60,        // 最大允许缓冲60秒
            maxBufferSize: 60 * 1000 * 1000, // 60MB缓冲区
            maxBufferHole: 0.5,            // 允许0.5秒的缓冲空洞
            lowLatencyMode: false,         // 关闭低延迟模式（提升稳定性）
            startLevel: -1,                // 自动选择起始画质
            abrEwmaDefaultEstimate: 5000000, // 默认5Mbps带宽估计
            // 启用平滑切换
            abrBandWidthFactor: 0.95,
            abrBandWidthUpFactor: 0.7,
            // 预加载设置
            backBufferLength: 30,          // 保留30秒回看缓冲
          })
          hls.loadSource(url)
          hls.attachMedia(video)
          art.hls = hls
          art.on('destroy', () => hls.destroy())
        } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
          video.src = url
  } else {
          art.notice.show = '不支持播放格式: m3u8'
        }
      },
    },
    // 自定义控制栏
    controls: [
      {
        name: 'fast-rewind',
        position: 'right',
        html: '<svg viewBox="0 0 24 24" width="22" height="22" fill="white"><path d="M11 18V6l-8.5 6 8.5 6zm.5-6l8.5 6V6l-8.5 6z"/></svg>',
        tooltip: '快退10秒',
        click: function() {
          if (artInstance) {
            artInstance.currentTime = Math.max(0, artInstance.currentTime - 10)
          }
        },
      },
      {
        name: 'fast-forward',
        position: 'right',
        html: '<svg viewBox="0 0 24 24" width="22" height="22" fill="white"><path d="M4 18l8.5-6L4 6v12zm9-12v12l8.5-6L13 6z"/></svg>',
        tooltip: '快进10秒',
        click: function() {
          if (artInstance) {
            artInstance.currentTime = Math.min(artInstance.duration, artInstance.currentTime + 10)
          }
        },
      },
    ],
  })
  
  // 保存videoRef引用以兼容旧代码
  videoRef.value = artInstance.video
  
  // 监听播放事件
  artInstance.on('play', () => {
      isPlaying.value = true
  })
  
  artInstance.on('pause', () => {
      isPlaying.value = false
  })
  
  artInstance.on('video:ended', () => {
    isPlaying.value = false
    onVideoEnded()
  })
  
  // 监听时间更新
  artInstance.on('video:timeupdate', () => {
    onTimeUpdate()
  })
  
  // 监听缓冲事件
  artInstance.on('video:waiting', () => {
    artInstance.loading.show = true
  })
  
  artInstance.on('video:canplay', () => {
    artInstance.loading.show = false
  })
}

// 保留旧的 initHls 函数名以兼容
const initHls = initArtPlayer

const togglePlay = () => {
  // 如果有广告且未播放过，先播放广告
  if (preRollAd.value && !adPlayed.value && !isVip.value) {
    startPreRollAd()
    return
  }
  
  if (artInstance) {
    if (artInstance.playing) {
      artInstance.pause()
    } else {
      artInstance.play()
    }
  }
}

const onTimeUpdate = () => {
  if (!artInstance) return
  
  isPlaying.value = artInstance.playing
  currentPlayTime.value = artInstance.currentTime
  
  // 试看时间检查
  if (needsPurchase.value && !hasPurchased.value && !isVipFree.value) {
    const currentTime = artInstance.currentTime
    const trialLimit = video.value.free_preview_seconds || 30
    
    if (currentTime >= trialLimit) {
      artInstance.pause()
      artInstance.currentTime = trialLimit
      isTrialEnded.value = true
      isPlaying.value = false
    }
  }
}

const onVideoEnded = () => {
  isPlaying.value = false
}

const toggleLike = async () => {
  // 乐观更新 - 立即反馈
  const wasLiked = isLiked.value
  const oldCount = video.value.like_count || 0
  isLiked.value = !wasLiked
  video.value.like_count = wasLiked ? Math.max(0, oldCount - 1) : oldCount + 1
  
  try {
    const res = await api.post(`/videos/${video.value.id}/like`)
    const data = res.data || res
    isLiked.value = data.liked
    video.value.like_count = data.like_count
  } catch (error) {
    // 回滚
    isLiked.value = wasLiked
    video.value.like_count = oldCount
    console.error('点赞失败:', error)
    if (error.response?.status === 401) {
      ElMessage.warning('请先登录后再点赞')
    }
  }
}

const toggleFavorite = async () => {
  // 乐观更新 - 立即反馈
  const wasFavorited = isFavorited.value
  const oldCount = video.value.favorite_count || 0
  isFavorited.value = !wasFavorited
  video.value.favorite_count = wasFavorited ? Math.max(0, oldCount - 1) : oldCount + 1
  
  try {
    const res = await api.post(`/videos/${video.value.id}/favorite`)
    const data = res.data || res
    isFavorited.value = data.favorited
    video.value.favorite_count = data.favorite_count
    ElMessage.success(data.favorited ? '收藏成功' : '已取消收藏')
  } catch (error) {
    // 回滚
    isFavorited.value = wasFavorited
    video.value.favorite_count = oldCount
    console.error('收藏失败:', error)
    if (error.response?.status === 401) {
      ElMessage.warning('请先登录后再收藏')
    }
  }
}

const toggleUploaderFollow = async () => {
  const uploaderId = video.value.uploader_id
  if (!uploaderId) return
  
  try {
    if (isUploaderFollowed.value) {
      await api.delete(`/users/${uploaderId}/follow`)
      isUploaderFollowed.value = false
      ElMessage.success('已取消关注')
    } else {
      await api.post(`/users/${uploaderId}/follow`)
      isUploaderFollowed.value = true
      ElMessage.success('关注成功')
    }
  } catch (error) {
    if (error.response?.status === 401) {
      ElMessage.warning('请先登录')
    } else {
      ElMessage.error(error.response?.data?.detail || '操作失败')
    }
  }
}

// 跳转到用户主页
const goToUserProfile = (userId) => {
  if (!userId) return
  router.push(`/user/member/${userId}`)
}

const shareVideo = () => {
  // 打开分享弹窗（分享送3日VIP）
  showShareModal.value = true
}

const downloadVideo = async () => {
  // 检查VIP权限
  if (!isVip.value) {
    ElMessage.warning('下载功能仅限VIP会员使用，请先开通VIP')
    router.push('/user/vip')
    return
  }
  
  try {
    // 先获取下载信息
    const infoRes = await api.get(`/videos/${video.value.id}/download-info`)
    const info = infoRes.data || infoRes
    
    if (!info.can_download) {
      ElMessage.warning(info.message || '无法下载此视频')
      return
    }
    
    // 确认下载
    const fileSize = info.file_size_mb || 0
    ElMessage.info(`正在下载: ${info.title} (${fileSize}MB)`)
    
    // 保存下载记录到localStorage
    saveDownloadRecord({
      id: `video_${video.value.id}_${Date.now()}`,
      videoId: video.value.id,
      title: video.value.title,
      thumbnail: video.value.cover_url || video.value.thumbnail,
      duration: video.value.duration,
      views: video.value.view_count,
      fileSize: fileSize,
      type: 'video',
      status: 'completed',
      downloadTime: Date.now()
    })
    
    // 开始下载
    const downloadUrl = `/api/v1/videos/${video.value.id}/download`
    
    // 创建隐藏的a标签进行下载
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = `${info.title}.mp4`
    link.style.display = 'none'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('下载已开始')
  } catch (error) {
    console.error('下载失败:', error)
    if (error.response?.status === 403) {
      ElMessage.warning('下载功能仅限VIP会员使用')
      router.push('/user/vip')
    } else if (error.response?.status === 404) {
      ElMessage.error('视频文件不存在')
    } else {
      ElMessage.error('下载失败，请稍后重试')
    }
  }
}

// 保存下载记录
const saveDownloadRecord = (record) => {
  try {
    const saved = localStorage.getItem('video_downloads')
    const downloads = saved ? JSON.parse(saved) : []
    // 检查是否已存在相同视频
    const existIndex = downloads.findIndex(d => d.videoId === record.videoId && d.type === record.type)
    if (existIndex > -1) {
      downloads[existIndex] = record // 更新
    } else {
      downloads.unshift(record) // 添加到开头
    }
    // 最多保存100条
    if (downloads.length > 100) {
      downloads.pop()
    }
    localStorage.setItem('video_downloads', JSON.stringify(downloads))
  } catch (e) {
    console.error('保存下载记录失败:', e)
  }
}

const submitComment = async () => {
  if ((!newComment.value.trim() && !commentImage.value) || submittingComment.value) return
  
  // 检查VIP权限
  if (!isVip.value) {
    alert('请先开通VIP会员才能发表评论')
    return
  }
  
  submittingComment.value = true
  
  try {
    let imageUrl = null
    
    // 先上传图片（如果有）
    if (commentImage.value) {
      const formData = new FormData()
      formData.append('file', commentImage.value)
      
      const uploadRes = await api.post('/comments/upload-image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      imageUrl = uploadRes.data?.url || uploadRes.url
    }
    
    const payload = {
      content: newComment.value.trim(),
      video_id: parseInt(route.params.id),
      parent_id: replyTarget.value?.parent_id || replyTarget.value?.id || null,
      image_url: imageUrl
    }
    
    const res = await api.post('/comments', payload)
    const newCommentData = res.data || res
    
    if (replyTarget.value) {
      // 添加到对应父评论的回复列表
      const parentId = replyTarget.value.parent_id || replyTarget.value.id
      const parentComment = comments.value.find(c => c.id === parentId)
      if (parentComment) {
        if (!parentComment.replies) parentComment.replies = []
        parentComment.replies.push(newCommentData)
        parentComment.reply_count = (parentComment.reply_count || 0) + 1
      }
    } else {
      // 添加到评论列表（置顶评论后面）
      const firstNonPinnedIndex = comments.value.findIndex(c => !c.is_pinned)
      if (firstNonPinnedIndex === -1) {
        comments.value.push(newCommentData)
      } else {
        comments.value.splice(firstNonPinnedIndex, 0, newCommentData)
      }
      commentTotal.value++
    }
    
    // 清空输入
    newComment.value = ''
    replyTarget.value = null
    commentImage.value = null
    commentImagePreview.value = ''
    showEmojiPicker.value = false
  } catch (error) {
    console.error('发表评论失败:', error)
    if (error.response?.status === 401) {
      alert('请先登录后再发表评论')
    } else if (error.response?.status === 403) {
      alert('请先开通VIP会员才能发表评论')
    } else {
      alert('发表评论失败，请重试')
    }
  } finally {
    submittingComment.value = false
  }
}

const likeComment = async (comment) => {
  try {
    const res = await api.post(`/comments/${comment.id}/like`)
    const data = res.data || res
    
    comment.is_liked = !comment.is_liked
    comment.like_count = data.like_count
  } catch (error) {
    console.error('点赞失败:', error)
    if (error.response?.status === 401) {
      alert('请先登录后再点赞')
    }
  }
}

const deleteComment = async (comment, parentComment = null) => {
  if (!confirm('确定要删除这条评论吗？')) return
  
  try {
    await api.delete(`/comments/${comment.id}`)
    
    if (parentComment) {
      // 删除回复
      const index = parentComment.replies.findIndex(r => r.id === comment.id)
      if (index > -1) {
        parentComment.replies.splice(index, 1)
        parentComment.reply_count = Math.max(0, (parentComment.reply_count || 1) - 1)
      }
    } else {
      // 删除主评论
      const index = comments.value.findIndex(c => c.id === comment.id)
      if (index > -1) {
        comments.value.splice(index, 1)
        commentTotal.value = Math.max(0, commentTotal.value - 1)
      }
    }
  } catch (error) {
    console.error('删除评论失败:', error)
    alert('删除失败，请重试')
  }
}

// 返回按钮点击计数
let backClickCount = 0

// 返回逻辑：第一次、第二次返回历史页，第三次返回首页
const goBack = () => {
  backClickCount++
  if (backClickCount >= 3) {
    // 第三次点击，直接返回首页
    backClickCount = 0
    router.push('/user')
  } else {
    // 第一次、第二次点击，返回上一页
    router.back()
  }
}

// 重置返回计数（用户进行其他操作时调用）
const resetBackCount = () => {
  backClickCount = 0
}

// 分享得VIP - 打开分享弹窗
const handleShare = () => {
  showShareModal.value = true
}

// 复制分享链接
const copyShareLink = (url) => {
  navigator.clipboard.writeText(url).then(() => {
    ElMessage.success('分享链接已复制，分享给好友注册后可获得3日VIP')
  }).catch(() => {
    ElMessage.info('请复制链接分享：' + url)
  })
}

// 保存分享图片
const saveShareImage = async () => {
  ElMessage.info('长按图片保存到相册')
}

const goToVideo = (id) => {
  resetBackCount() // 重置返回计数
  // 强制刷新页面以加载新视频
  router.push(`/user/video/${id}`).then(() => {
    window.scrollTo(0, 0)
  })
}

const handleAdClick = (ad) => {
  if (ad.link) {
    window.open(ad.link, '_blank')
  }
}

// formatDuration, formatViewCount, formatCount 已从 @/utils/format 导入

const formatTime = (date) => {
  return dayjs(date).fromNow()
}

// 格式化评论时间（更详细）
const formatCommentTime = (date) => {
  const d = dayjs(date)
  const now = dayjs()
  const diffDays = now.diff(d, 'day')
  
  if (diffDays === 0) {
    return d.format('HH:mm')
  } else if (diffDays < 7) {
    return d.fromNow()
  } else {
    return d.format('YYYY-MM-DD HH:mm')
  }
}


// 监听路由参数变化，重新加载视频
watch(() => route.params.id, async (newId, oldId) => {
  if (newId && newId !== oldId) {
    // 销毁旧的 ArtPlayer 实例
    if (artInstance) {
      artInstance.destroy()
      artInstance = null
    }
    
    // 重置广告状态（每个视频都可以显示一次广告）
    adPlayed.value = false
    showPreRollAd.value = false
    preRollAd.value = null
    canSkipAd.value = false
    if (adTimerId) {
      timers.clearInterval(adTimerId)
      adTimerId = null
    }
    
    // 重新加载数据
    await fetchVideo()
    await Promise.all([fetchComments(), fetchRecommend(), fetchIconAds(), fetchPreRollAd()])
    await nextTick()
    initArtPlayer()
  }
})

onMounted(async () => {
  // 重置返回计数
  resetBackCount()
  
  // 尝试获取当前用户信息
  try {
    const userRes = await api.get('/users/me')
    const userData = userRes.data || userRes
    currentUserId.value = userData.id
    isVip.value = userData.is_vip || false
    userVipLevel.value = userData.vip_level || 0
    userVipLevelNameFromApi.value = userData.vip_level_name || '非VIP'
    userVipExpireDate.value = userData.vip_expire_date || null
    isAdmin.value = userData.role === 'admin' || userData.role === 'super_admin'
  } catch (error) {
    console.log('未登录或获取用户信息失败')
  }
  
  await fetchVideo()
  await Promise.all([fetchComments(), fetchRecommend(), fetchIconAds(), fetchAnnouncement(), fetchUserCoins(), fetchPreRollAd()])
  
  await nextTick()
  initArtPlayer()
})

onUnmounted(() => {
  // 销毁 ArtPlayer 实例
  if (artInstance) {
    artInstance.destroy()
    artInstance = null
  }
  // 清除广告计时器
  if (adTimerId) {
    timers.clearInterval(adTimerId)
  }
})
</script>

<style lang="scss" scoped>
.video-player-page {
  min-height: 100vh;
  min-height: 100dvh;
  background: #0a0a0a;
  color: #fff;
  width: 100%;
  max-width: 100vw;
  overflow-x: clip; // 使用clip替代hidden，不影响sticky
  padding-bottom: calc(60px + env(safe-area-inset-bottom, 0px));
}

// 返回按钮
.back-btn {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 100;
  width: 36px;
  height: 36px;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  
  svg {
    width: 28px;
    height: 28px;
    fill: #fff;
    filter: drop-shadow(0 1px 2px rgba(0,0,0,0.5));
  }
}

// 播放器容器 - sticky固定在顶部
.player-container {
  position: sticky;
  top: 0;
  z-index: 50;
  width: 100%;
  aspect-ratio: 16/9;
  background: #000;

  // 前贴广告 - 确保覆盖所有播放器元素
  .pre-roll-ad {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 200;  // 提高z-index确保在最上层
    background: #000;
    
    // 确保广告可以正常交互
    pointer-events: auto;
    
    .ad-video-container {
      position: relative;
      width: 100%;
      height: 100%;
      
      .ad-video {
        width: 100%;
        height: 100%;
        object-fit: contain;
      }
      
      .ad-image-wrapper {
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        
        .ad-image {
          max-width: 100%;
          max-height: 100%;
          object-fit: contain;
        }
      }
      
      .ad-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        padding: 16px;
        pointer-events: none;
        
        > * {
          pointer-events: auto;
        }
      }
      
      .ad-countdown {
        position: absolute;
        top: 12px;
        right: 12px;
        background: rgba(0, 0, 0, 0.7);
        color: #fff;
        padding: 8px 14px;
        border-radius: 4px;
        font-size: 13px;
      }
      
      .ad-close-btn {
        position: absolute;
        top: 12px;
        right: 12px;
        background: rgba(255, 255, 255, 0.95);
        color: #333;
        padding: 8px 14px;
        border-radius: 4px;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        
        &:hover {
          background: #fff;
        }
        
        &:active {
          transform: scale(0.98);
        }
      }
      
      .ad-skip {
        position: absolute;
        bottom: 60px;
        right: 12px;
        background: rgba(255, 255, 255, 0.9);
        color: #333;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        
        &:hover {
          background: #fff;
        }
      }
      
      .ad-link {
        position: absolute;
        bottom: 16px;
        right: 12px;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: #fff;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 13px;
        text-decoration: none;
        
        &:hover {
          opacity: 0.9;
        }
      }
      
      .ad-label {
        position: absolute;
        top: 12px;
        left: 12px;
        background: rgba(255, 193, 7, 0.9);
        color: #000;
        padding: 2px 8px;
        border-radius: 2px;
        font-size: 11px;
        font-weight: 600;
      }
    }
  }
  
  .video-player {
    width: 100%;
    height: 100%;
    object-fit: contain;
  }

  // ArtPlayer 容器
  .artplayer-container {
    width: 100%;
    height: 100%;
    position: relative;
    z-index: 1;
    
    // 广告播放时完全隐藏
    &.hidden-by-ad {
      visibility: hidden;
      pointer-events: none;
      
      // 隐藏所有子元素
      * {
        visibility: hidden !important;
      }
    }
  }

  // ArtPlayer 主题定制
  :deep(.art-video-player) {
    --art-theme: #ec4899;
    --art-progress-color: #ec4899;
    font-family: inherit;
    
    .art-control-progress-inner {
      background: #ec4899 !important;
    }
    
    .art-control-volume-inner {
      background: #ec4899 !important;
    }
    
    .art-setting-panel {
      background: rgba(0, 0, 0, 0.9) !important;
    }
    
    // 暂停时隐藏加载图标
    &.art-loading .art-loading-icon {
      opacity: 0;
      transition: opacity 0.3s;
    }
    
    // 播放时才显示加载图标
    &.art-loading:not(.art-paused) .art-loading-icon {
      opacity: 1;
    }
    
    .art-info-panel {
      background: rgba(0, 0, 0, 0.9) !important;
    }
  }
  
  .player-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    justify-content: center;
    align-items: center;
    background: rgba(0, 0, 0, 0.3);
    cursor: pointer;
    
    .play-btn {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.9);
      display: flex;
      justify-content: center;
      align-items: center;
      
      svg {
        width: 30px;
        height: 30px;
        fill: #333;
        margin-left: 4px;
      }
    }
  }

  // 试看倒计时
  .trial-countdown {
    position: absolute;
    top: 12px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    align-items: center;
    gap: 8px;
    background: linear-gradient(90deg, rgba(255, 69, 0, 0.9), rgba(255, 140, 0, 0.9));
    padding: 8px 16px;
    border-radius: 20px;
    z-index: 30;
    animation: pulse 1s infinite;
    
    .countdown-icon {
      font-size: 16px;
    }
    
    .countdown-text {
      color: #fff;
      font-size: 13px;
      font-weight: 600;
    }
    
    .countdown-vip-btn {
      background: #fff;
      color: #ff4500;
      border: none;
      padding: 4px 10px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 600;
      cursor: pointer;
      
      &:active {
        opacity: 0.8;
      }
    }
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.85; }
  }

  // 已购买/VIP免费标识
  .access-badge {
    position: absolute;
    top: 12px;
    right: 12px;
    z-index: 25;
    
    .vip-free-badge, .purchased-badge {
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 4px 10px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 500;
    }
    
    .vip-free-badge {
      background: linear-gradient(135deg, #ffd700, #ffec8b);
      color: #8b6914;
      
      svg {
        fill: #8b6914;
      }
    }
    
    .purchased-badge {
      background: linear-gradient(135deg, #52c41a, #73d13d);
      color: #fff;
    }
  }
  
  .vip-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.85);
    display: flex;
    justify-content: center;
    align-items: center;
    
    .vip-content {
      text-align: center;
      
      .vip-icon-large {
        width: 60px;
        height: 60px;
        margin: 0 auto 12px;
        
        .crown-svg-large {
          width: 100%;
          height: 100%;
          filter: drop-shadow(0 0 10px rgba(255, 215, 0, 0.8));
          animation: crown-pulse 2s ease-in-out infinite;
        }
      }
      
      @keyframes crown-pulse {
        0%, 100% {
          transform: scale(1);
          filter: drop-shadow(0 0 10px rgba(255, 215, 0, 0.8));
        }
        50% {
          transform: scale(1.1);
          filter: drop-shadow(0 0 20px rgba(255, 215, 0, 1));
        }
      }
      
      h3 {
        font-size: 18px;
        margin-bottom: 8px;
      }
      
      p {
        color: rgba(255, 255, 255, 0.7);
        margin-bottom: 16px;
        font-size: 14px;
      }
      
      .vip-btn {
        background: linear-gradient(90deg, #a855f7, #7c3aed);
        border: none;
        padding: 10px 24px;
        border-radius: 20px;
        color: #fff;
        font-weight: bold;
        cursor: pointer;
      }
    }
  }
}

// VIP 推广条
.vip-promo {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  min-height: 44px;
  background-image: url("/images/backgrounds/count_down_demon_bg.webp");
  background-size: 100% 100%;
  background-position: center;
  background-repeat: no-repeat;
  cursor: pointer;
  
  // 会员信息居中显示
  .vip-member-center {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    flex: 1;
    
    .vip-icon-promo {
      height: 20px;
      width: auto;
      object-fit: contain;
      filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3));
    }
    
    .vip-expire-text {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.85);
    }
  }
  
  .promo-text {
    margin-left: 30%;
    font-size: 12px;
    font-weight: 600;
    background: linear-gradient(135deg, #ffd700 0%, #ffec8b 50%, #daa520 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  .promo-btn {
    background: linear-gradient(135deg, #ffd700 0%, #f0c14b 50%, #daa520 100%);
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 11px;
    color: #3d2a1a;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 3px;
    flex-shrink: 0;
    
    &.upgrade {
      background: linear-gradient(135deg, #fff8e7 0%, #f5e6c8 50%, #e8d5a8 100%);
    }
    
    .arrow {
      font-size: 12px;
    }
  }
}

// 标签页 - sticky固定在播放器下方
.content-tabs {
  display: flex;
  align-items: center;
  padding: 0 15px;
  background: #0a0a0a;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  position: sticky;
  top: calc(100vw * 9 / 16); // 播放器高度
  z-index: 40;
  
  .tab-item {
    padding: 14px 0;
    margin-right: 24px;
    color: rgba(255, 255, 255, 0.6);
    font-size: 15px;
    cursor: pointer;
    position: relative;
    
    &.active {
      color: #fff;
      font-weight: 500;
      
      &::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #a855f7, #6366f1);
        border-radius: 1px;
      }
    }
  }
  
  .tab-right {
    margin-left: auto;
    color: rgba(255, 255, 255, 0.7);
    font-size: 13px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 4px;
    
    .line-icon {
      color: #a855f7;
    }
  }
}

// 内容区
// 简介内容区
.intro-content {
  background: #0a0a0a;
  padding: 0 15px;
}

// 评论内容区
.comments-content {
  background: #0a0a0a;
  min-height: calc(100vh - 350px);
  display: flex;
  flex-direction: column;
  
  .comment-list-wrapper {
    flex: 1;
    padding: 0 15px;
    padding-bottom: 80px;
  }
  
  // 官方公告样式 - 与普通评论相同布局
  .official-announcement {
    // 强制水平布局：头像在左，内容在右
    display: flex !important;
    flex-direction: row !important;
    align-items: flex-start !important;
    gap: 10px !important;
    margin-top: 20px !important;
    
    // 官方头像 - 跟普通用户一样
    > .avatar {
      width: 36px !important;
      height: 36px !important;
      min-width: 36px;
      max-width: 36px;
      min-height: 36px;
      max-height: 36px;
      border-radius: 50%;
      object-fit: cover;
      flex-shrink: 0;
    }
    
    // 内容区域
    > .comment-body {
      flex: 1;
      min-width: 0;
    }
    
    // 官方昵称行
    .comment-user {
      margin-bottom: 7px;
    }
    
    // 官方昵称 - 紫色渐变，大小跟普通用户一样
    .official-name {
      font-size: 13px;
      font-weight: 600;
      background: linear-gradient(90deg, #a855f7, #c084fc, #e879f9);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    
    // 至尊VIP图标 - 跟会员图标一样大小 + 显眼特效
    .supreme-vip-icon {
      height: 18px;
      width: auto;
      margin-left: 6px;
      vertical-align: middle;
      filter: drop-shadow(0 0 6px rgba(168, 85, 247, 0.8));
      animation: supreme-glow 1.5s ease-in-out infinite;
    }
    
    // 官方评论内容 - 紫色（保留emoji原色）
    .official-text {
      font-size: 14px;
      line-height: 1.8;
      color: #c084fc;
    }
    
    // 官方评论时间 - 跟普通评论一样
    .comment-meta {
      display: flex;
      gap: 20px;
      align-items: center;
      margin-top: 8px;
      
      .time {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.35);
      }
    }
  }
  
  // 至尊图标发光动画
  @keyframes supreme-glow {
    0%, 100% {
      filter: drop-shadow(0 0 4px rgba(168, 85, 247, 0.6)) drop-shadow(0 0 8px rgba(59, 130, 246, 0.4));
      transform: scale(1);
    }
    50% {
      filter: drop-shadow(0 0 8px rgba(168, 85, 247, 1)) drop-shadow(0 0 16px rgba(59, 130, 246, 0.8));
      transform: scale(1.1);
    }
  }
  
  // 官方评论内容蓝色
  .is-official {
    .comment-text {
      color: #60a5fa !important;
    }
  }
  
  .comment-list {
    .comment-item {
      display: flex;
      gap: 10px;
      padding: 16px 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      
      // 置顶评论样式
      &.is-pinned {
        background: linear-gradient(135deg, rgba(168, 85, 247, 0.08), rgba(124, 58, 237, 0.05));
        margin: 0 -15px;
        padding: 16px 15px;
        border-radius: 8px;
        border: 1px solid rgba(168, 85, 247, 0.2);
        margin-bottom: 10px;
      }
      
      // 官方评论样式
      &.is-official {
        background: linear-gradient(135deg, rgba(255, 215, 0, 0.08), rgba(255, 165, 0, 0.05));
        margin: 0 -15px;
        padding: 16px 15px;
        border-radius: 8px;
        border: 1px solid rgba(255, 215, 0, 0.2);
        margin-bottom: 10px;
      }
      
      .avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        flex-shrink: 0;
        object-fit: cover;
        background: rgba(255, 255, 255, 0.1);
        
        &.clickable {
          cursor: pointer;
          transition: opacity 0.2s;
          
          &:hover {
            opacity: 0.8;
          }
        }
      }
      
      .comment-body {
        flex: 1;
        min-width: 0;
        
        .comment-user {
          display: flex;
          align-items: center;
          gap: 6px;
          margin-bottom: 8px;
          
          .username {
            font-size: 13px;
            font-weight: 600;
            background: linear-gradient(135deg, #ffd700 0%, #ffec8b 50%, #daa520 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            
            &.clickable {
              cursor: pointer;
              transition: opacity 0.2s;
              
              &:hover {
                opacity: 0.8;
              }
            }
          }
          
          .vip-badge-sm {
            height: 18px;
            width: auto;
            object-fit: contain;
            animation: vip-badge-glow 2s ease-in-out infinite;
          }
          
          .official-badge {
            background: linear-gradient(135deg, #ffd700, #ff9500);
            color: #000;
            font-size: 10px;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 4px;
            
            &.small {
              font-size: 9px;
              padding: 1px 4px;
            }
          }
          
          .pin-badge {
            font-size: 11px;
            color: #a855f7;
          }
        }
        
        @keyframes vip-badge-glow {
          0%, 100% {
            filter: drop-shadow(0 0 3px rgba(255, 215, 0, 0.5));
          }
          50% {
            filter: drop-shadow(0 0 8px rgba(255, 215, 0, 0.8));
          }
        }
        
        // 评论图片
        .comment-image {
          margin: 10px 0;
          
          img {
            max-width: 200px;
            max-height: 200px;
            border-radius: 8px;
            object-fit: cover;
            cursor: pointer;
            transition: transform 0.2s;
            
            &:hover {
              transform: scale(1.02);
            }
          }
          
          &.small img {
            max-width: 120px;
            max-height: 120px;
          }
        }
        
        .comment-text {
          font-size: 14px;
          color: rgba(255, 255, 255, 0.9);
          line-height: 1.6;
          margin: 0 0 10px;
          word-break: break-word;
        }
        
        .comment-meta {
          display: flex;
          gap: 20px;
          align-items: center;
          
          .time {
            font-size: 12px;
            color: rgba(255, 255, 255, 0.35);
          }
          
          .like-btn, .reply-btn {
            font-size: 12px;
            color: rgba(255, 255, 255, 0.45);
            cursor: pointer;
            transition: color 0.2s;
            
            &:hover {
              color: rgba(255, 255, 255, 0.7);
            }
            
            &.liked {
              color: #ff6b6b;
            }
          }
          
          .delete-btn {
            margin-left: auto;
            font-size: 12px;
            color: rgba(255, 100, 100, 0.4);
            cursor: pointer;
            
            &:hover {
              color: #ff6b6b;
            }
          }
        }
        
        .reply-list {
          margin-top: 12px;
          padding: 12px;
          background: rgba(255, 255, 255, 0.03);
          border-radius: 8px;
          
          .reply-item {
            display: flex;
            gap: 8px;
            padding: 10px 0;
            
            &:first-child {
              padding-top: 0;
            }
            
            &:not(:last-child) {
              border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            }
            
            .reply-avatar {
              width: 24px;
              height: 24px;
              border-radius: 50%;
              flex-shrink: 0;
              object-fit: cover;
              
              &.clickable {
                cursor: pointer;
                transition: opacity 0.2s;
                
                &:hover {
                  opacity: 0.8;
                }
              }
            }
            
            .reply-body {
              flex: 1;
              
              .username {
                font-size: 12px;
                font-weight: 500;
                background: linear-gradient(135deg, #ffd700 0%, #ffec8b 50%, #daa520 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-right: 6px;
                
                &.clickable {
                  cursor: pointer;
                  transition: opacity 0.2s;
                  
                  &:hover {
                    opacity: 0.8;
                  }
                }
              }
              
              .vip-badge-tiny {
                height: 14px;
                width: auto;
                object-fit: contain;
                vertical-align: middle;
                margin-left: 4px;
              }
              
              .official-badge.small {
                font-size: 9px;
                padding: 1px 4px;
                background: linear-gradient(135deg, #ffd700, #ff9500);
                color: #000;
                border-radius: 3px;
                margin-left: 4px;
              }
              
              .reply-text {
                font-size: 13px;
                color: rgba(255, 255, 255, 0.85);
                margin: 4px 0 6px;
                line-height: 1.5;
              }
              
              .reply-meta {
                display: flex;
                gap: 16px;
                
                .time, .like-btn, .reply-btn {
                  font-size: 11px;
                  color: rgba(255, 255, 255, 0.35);
                  cursor: pointer;
                  
                  &:hover {
                    color: rgba(255, 255, 255, 0.6);
                  }
                  
                  &.liked {
                    color: #ff6b6b;
                  }
                }
              }
            }
          }
          
          .more-replies {
            font-size: 12px;
            color: #a855f7;
            padding: 10px 0 0;
            cursor: pointer;
            
            &:hover {
              text-decoration: underline;
            }
          }
        }
      }
    }
  }
  
  .empty-comments {
    text-align: center;
    padding: 60px 20px;
    
    p {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.4);
      margin: 0;
    }
  }
  
  .load-more {
    text-align: center;
    padding: 20px 0;
    
    .load-more-btn {
      background: linear-gradient(135deg, rgba(168, 85, 247, 0.2), rgba(124, 58, 237, 0.2));
      border: 1px solid rgba(168, 85, 247, 0.4);
      color: #a855f7;
      padding: 12px 28px;
      border-radius: 25px;
      font-size: 14px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      transition: all 0.3s ease;
      
      &:hover:not(:disabled) {
        background: linear-gradient(135deg, rgba(168, 85, 247, 0.3), rgba(124, 58, 237, 0.3));
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.3);
      }
      
      &:disabled {
        opacity: 0.7;
        cursor: not-allowed;
      }
      
      .loading-spinner {
        display: flex;
        align-items: center;
        gap: 8px;
        
        .spin-icon {
          width: 16px;
          height: 16px;
          animation: spin 1s linear infinite;
        }
      }
    }
  }
  
  .no-more-comments {
    text-align: center;
    padding: 20px 0;
    color: rgba(255, 255, 255, 0.3);
    font-size: 12px;
  }
  
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  
  // 底部评论输入框
  .comment-input-bar {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(180deg, rgba(20, 20, 35, 0.95) 0%, rgba(15, 15, 25, 1) 100%);
    padding: 12px 16px;
    padding-bottom: calc(12px + env(safe-area-inset-bottom, 0px));
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    z-index: 100;
    backdrop-filter: blur(10px);
    
    // VIP评论提示
    .vip-comment-tip {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      background: linear-gradient(135deg, rgba(255, 215, 0, 0.15), rgba(255, 165, 0, 0.1));
      border: 1px solid rgba(255, 215, 0, 0.3);
      border-radius: 25px;
      padding: 12px 20px;
      cursor: pointer;
      transition: all 0.3s ease;
      
      &:hover {
        background: linear-gradient(135deg, rgba(255, 215, 0, 0.25), rgba(255, 165, 0, 0.2));
        transform: translateY(-2px);
      }
      
      .tip-icon {
        font-size: 18px;
      }
      
      .tip-text {
        font-size: 14px;
        color: rgba(255, 215, 0, 0.9);
      }
      
      .tip-btn {
        font-size: 13px;
        color: #ffd700;
        font-weight: 600;
      }
    }
    
    .input-area {
      .image-preview {
        position: relative;
        margin-bottom: 10px;
        display: inline-block;
        
        img {
          max-width: 100px;
          max-height: 100px;
          border-radius: 8px;
          object-fit: cover;
        }
        
        .remove-image {
          position: absolute;
          top: -8px;
          right: -8px;
          width: 20px;
          height: 20px;
          background: #ff4757;
          color: #fff;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 14px;
          cursor: pointer;
          
          &:hover {
            background: #ff6b81;
          }
        }
      }
      
      .input-row {
        display: flex;
        align-items: center;
        gap: 10px;
        background: rgba(255, 255, 255, 0.06);
        border-radius: 20px;
        padding: 6px 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        
        input {
          flex: 1;
          background: transparent;
          border: none;
          color: #fff;
          font-size: 14px;
          outline: none;
          padding: 4px 0;
          
          &::placeholder {
            color: rgba(255, 255, 255, 0.35);
          }
        }
        
        .input-actions {
          display: flex;
          align-items: center;
          gap: 8px;
          
          .cancel-btn {
            font-size: 12px;
            color: #a855f7;
            cursor: pointer;
            padding: 4px 8px;
            background: rgba(168, 85, 247, 0.15);
            border-radius: 12px;
          }
          
          .emoji-btn, .image-btn {
            font-size: 18px;
            cursor: pointer;
            opacity: 0.7;
            transition: all 0.2s;
            
            &:hover {
              opacity: 1;
              transform: scale(1.1);
            }
          }
          
          .send-btn {
            color: #a855f7;
            cursor: pointer;
            display: flex;
            align-items: center;
            padding: 4px;
            transition: all 0.2s;
            
            &:hover:not(.disabled) {
              transform: scale(1.1);
            }
            
            &.disabled {
              opacity: 0.5;
              cursor: not-allowed;
            }
            
            svg {
              width: 20px;
              height: 20px;
            }
          }
        }
      }
      
      // 表情选择器
      .emoji-picker {
        margin-top: 10px;
        background: rgba(30, 30, 50, 0.95);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 12px;
        
        .emoji-grid {
          display: grid;
          grid-template-columns: repeat(10, 1fr);
          gap: 5px;
          max-height: 150px;
          overflow-y: auto;
          
          &::-webkit-scrollbar {
            width: 4px;
          }
          
          &::-webkit-scrollbar-thumb {
            background: rgba(168, 85, 247, 0.5);
            border-radius: 2px;
          }
          
          .emoji-item {
            font-size: 20px;
            padding: 5px;
            cursor: pointer;
            text-align: center;
            border-radius: 6px;
            transition: background 0.2s;
            
            &:hover {
              background: rgba(168, 85, 247, 0.2);
            }
          }
        }
      }
    }
  }
}

// 简介区
.intro-section {
  padding: 15px 0;
  
  .video-title {
    font-size: 15px;
    font-weight: 500;
    line-height: 1.4;
    margin: 0 0 12px;
    color: rgba(255, 255, 255, 0.95);
  }
  
  .video-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 16px;
    
    .tag-item {
      padding: 4px 12px;
      background: rgba(168, 85, 247, 0.15);
      border: 1px solid rgba(168, 85, 247, 0.3);
      border-radius: 4px;
      font-size: 12px;
      color: rgba(255, 255, 255, 0.8);
    }
  }
  
  .uploader-info {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
    
    .avatar {
      width: 44px;
      height: 44px;
      border-radius: 50%;
      object-fit: cover;
      background: rgba(255, 255, 255, 0.1);
    }
    
    .uploader-detail {
      flex: 1;
      
        .name-row {
          display: flex;
          align-items: center;
          gap: 6px;
          margin-bottom: 8px;
        
        .name {
          font-weight: 500;
          font-size: 15px;
          background: linear-gradient(135deg, #ffd700 0%, #ffec8b 30%, #daa520 60%, #ffd700 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        
        .vip-badge {
          height: 22px;
          width: auto;
          object-fit: contain;
          margin-left: 4px;
          animation: vip-glow 2s ease-in-out infinite;
        }
        
        .badge {
          font-size: 11px;
          color: #a855f7;
        }
      }
      
      .stats {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.5);
      }
    }
    
    .follow-btn {
      background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
      border: none;
      padding: 6px 16px;
      border-radius: 4px;
      color: #fff;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
      white-space: nowrap;
      line-height: 1.4;
      
      &:hover {
        opacity: 0.9;
      }
      
      &:active {
        opacity: 0.8;
      }
      
      &.followed {
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.3);
      }
    }
  }
  
  .video-stats {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding: 4px 0;
    gap: 20px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    
    .stat-item {
      display: flex;
      align-items: center;
      gap: 3px;
      
      &.views {
        margin-right: auto;
        
        .stat-value {
          color: rgba(255, 255, 255, 0.7);
        }
      }
      
      &.clickable {
        cursor: pointer;
        transition: opacity 0.2s;
        
        &:hover {
          opacity: 0.8;
        }
      }
      
      .stat-icon {
        width: 18px;
        height: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        
        svg {
          width: 100%;
          height: 100%;
          fill: rgba(255, 255, 255, 0.6);
          transition: all 0.2s ease;
        }
        
        &.heart {
          svg { fill: rgba(255, 255, 255, 0.6); }
          &.active svg { fill: #ff6b81; }
        }
        
        &.star {
          svg { fill: rgba(255, 255, 255, 0.6); }
          &.active svg { fill: #ffd700; }
        }
        
        &.share svg {
          fill: rgba(255, 255, 255, 0.6);
        }
        
        &.download {
          position: relative;
          
          svg {
            fill: rgba(255, 255, 255, 0.6);
          }
          
          .vip-badge {
            position: absolute;
            top: -6px;
            right: -10px;
            background: linear-gradient(135deg, #ffd700, #ff8c00);
            color: #000;
            font-size: 8px;
            font-weight: bold;
            padding: 1px 3px;
            border-radius: 3px;
          }
          
          &.vip-feature svg {
            fill: rgba(255, 255, 255, 0.4);
          }
        }
      }
      
      .stat-value {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.85);
      }
      
      .stat-label {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.7);
      }
    }
  }
}

// 图标广告区 - 循环滚动
.ad-icons-section {
  padding: 10px 0;
  background: #0a0a0a;
  overflow: hidden;
  
  .ad-icons-scroll {
    overflow: hidden;
    width: 100%;
  }
  
  .ad-icons-track {
    display: flex;
    gap: 6px;
    animation: scrollAds 25s linear infinite;
    width: max-content;
    padding: 0 6px;
    
    &:hover {
      animation-play-state: paused;
    }
  }
  
  @keyframes scrollAds {
    0% {
      transform: translateX(0);
    }
    100% {
      transform: translateX(-50%);
    }
  }
  
  .ad-icon-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 5px;
    flex-shrink: 0;
    cursor: pointer;
    padding: 0 2px;
    transition: transform 0.2s;
    
    &:active {
      transform: scale(0.95);
    }
    
    .icon-wrap {
      width: 58px;
      height: 58px;
      border-radius: 14px;
      overflow: hidden;
      background: rgba(255, 255, 255, 0.1);
      display: flex;
      justify-content: center;
      align-items: center;
      
      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
      
      .icon-emoji {
        font-size: 28px;
      }
    }
    
    .icon-name {
      font-size: 11px;
      color: rgba(255, 255, 255, 0.7);
      max-width: 64px;
      text-align: center;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
}

// 推荐标签 - sticky固定在标签页下方
.recommend-tabs {
  display: flex;
  justify-content: space-around;
  padding: 12px 15px;
  background: #0a0a0a;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  position: sticky;
  top: calc(100vw * 9 / 16 + 48px); // 播放器高度 + 简介/评论标签栏高度
  z-index: 35;
  
  .rec-tab {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.5);
    cursor: pointer;
    position: relative;
    padding-bottom: 8px;
    
    &.active {
      color: #fff;
      font-weight: 500;
      
      &::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #a855f7, #6366f1);
        border-radius: 1px;
      }
    }
  }
}

// 推荐视频
.recommend-section {
  padding: 0;
  background: #0a0a0a;
}

// 视频列表样式（与首页一致）
.video-list {
  display: grid;
  gap: clamp(10px, 3vw, 16px) clamp(6px, 2vw, 12px);
  padding: 0 0 20px;
  background: #0a0a0a;
  border-radius: 0;
  
  &.double-column {
    grid-template-columns: repeat(2, 1fr);
    
    @media (min-width: 768px) {
      grid-template-columns: repeat(3, 1fr);
    }
    
    @media (min-width: 1024px) {
      grid-template-columns: repeat(4, 1fr);
    }
    
    @media (min-width: 1440px) {
      grid-template-columns: repeat(5, 1fr);
    }
    
    .video-card {
      width: 100%;
      min-width: 0;
    }
  }
  
  .video-card {
    background: transparent;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
    width: 100%;
    min-width: 0;
    
    &:hover {
      transform: translateY(-3px);
      
      .video-cover img {
        transform: scale(1.03);
      }
    }
    
    .video-cover {
      position: relative;
      width: 100%;
      aspect-ratio: 16/9;
      border-radius: clamp(3px, 1vw, 6px);
      overflow: hidden;
      
      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
        transition: transform 0.3s ease, opacity 0.3s ease;
        
        &.hidden {
          opacity: 0;
        }
      }
      
      .preview-video {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        opacity: 0;
        transition: opacity 0.3s ease;
        pointer-events: none;
        
        &.visible {
          opacity: 1;
        }
      }
      
      .cover-views {
        position: absolute;
        bottom: clamp(6px, 2vw, 10px);
        left: clamp(6px, 2vw, 10px);
        display: flex;
        align-items: center;
        gap: clamp(2px, 1vw, 5px);
        font-size: clamp(11px, 3vw, 13px);
        color: #fff;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8);
        
        .play-icon {
          font-size: clamp(8px, 2.5vw, 11px);
        }
      }
      
      .video-duration {
        position: absolute;
        bottom: clamp(6px, 2vw, 10px);
        right: clamp(6px, 2vw, 10px);
        font-size: clamp(11px, 3vw, 13px);
        color: #fff;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8);
      }
      
      .vip-tag {
        position: absolute;
        top: clamp(6px, 2vw, 10px);
        left: clamp(6px, 2vw, 10px);
        background: linear-gradient(135deg, #ffcc00, #ff9500);
        color: #000;
        padding: clamp(2px, 0.8vw, 4px) clamp(8px, 2.5vw, 12px);
        border-radius: clamp(3px, 1vw, 5px);
        font-size: clamp(9px, 2.5vw, 11px);
        font-weight: bold;
        box-shadow: 0 2px 8px rgba(255, 204, 0, 0.3);
      }
    }
    
    .video-info {
      padding: clamp(2px, 1vw, 6px) clamp(1px, 0.5vw, 4px);
      text-align: left;
      
      .video-title {
        font-size: clamp(12px, 3.5vw, 15px);
        color: rgba(255, 255, 255, 0.92);
        margin: 0 0 4px;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        line-height: 1.5;
        letter-spacing: 0.5px;
        font-weight: 500;
        min-height: calc(clamp(12px, 3.5vw, 15px) * 1.5 * 2);
        text-align: left;
      }
      
      .video-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        
        .video-tag {
          background: linear-gradient(135deg, #a855f7, #7c3aed);
          color: #fff;
          padding: 4px 12px;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 500;
        }
        
        .video-comments {
          font-size: 11px;
          color: rgba(255, 255, 255, 0.5);
        }
      }
    }
  }
}

// ============ 响应式适配 ============
// 断点变量
$bp-md: 600px;
$bp-lg: 768px;
$bp-xl: 1024px;
$bp-xxl: 1280px;
$bp-2k: 1920px;
$bp-4k: 2560px;

@media (min-width: $bp-lg) {
  .video-player-page {
    max-width: 900px;
    margin: 0 auto;
  }
  
  .recommend-section .recommend-list {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .video-info {
    padding: 20px;
  }
}

@media (min-width: $bp-xl) {
  .video-player-page {
    max-width: 1000px;
  }
  
  .recommend-section .recommend-list {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (min-width: $bp-xxl) {
  .video-player-page {
    max-width: 1200px;
  }
  
  .recommend-section .recommend-list {
    grid-template-columns: repeat(5, 1fr);
  }
}

@media (min-width: $bp-2k) {
  .video-player-page {
    max-width: 1400px;
  }
  
  .recommend-section .recommend-list {
    grid-template-columns: repeat(6, 1fr);
    gap: 20px;
  }
  
  .video-title {
    font-size: 24px;
  }
  
  .video-info {
    padding: 28px;
  }
}

@media (min-width: $bp-4k) {
  .video-player-page {
    max-width: 1800px;
  }
  
  .recommend-section .recommend-list {
    grid-template-columns: repeat(7, 1fr);
    gap: 24px;
  }
  
  .video-title {
    font-size: 28px;
  }
}

// 触摸设备优化
@media (hover: none) and (pointer: coarse) {
  .video-card {
    &:hover {
      transform: none !important;
      
      .video-cover img {
        transform: none !important;
      }
    }
    
    &:active {
      transform: scale(0.98);
      opacity: 0.9;
    }
  }
  
  .action-btn:hover {
    background: transparent !important;
  }
  
  .action-btn:active {
    transform: scale(0.95);
  }
}

// 横屏模式优化
@media (orientation: landscape) and (max-height: 500px) {
  .player-container {
    height: 70vh;
    aspect-ratio: unset;
  }
  
  .video-info {
    padding: 10px 16px;
  }
  
  .action-bar {
    padding: 8px 12px;
  }
}

// VIP标志动画
@keyframes vip-glow {
  0%, 100% {
    filter: drop-shadow(0 0 2px rgba(255, 215, 0, 0.5));
    transform: scale(1);
  }
  50% {
    filter: drop-shadow(0 0 6px rgba(255, 215, 0, 0.9));
    transform: scale(1.08);
  }
}

// 付费视频遮罩
.pay-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 20;
  
  .pay-content {
    text-align: center;
    padding: 20px;
    
    .pay-icon {
      font-size: 48px;
      margin-bottom: 12px;
    }
    
    h3 {
      font-size: 18px;
      margin-bottom: 8px;
      color: #fff;
    }
    
    .trial-tip {
      color: rgba(255, 255, 255, 0.7);
      font-size: 13px;
      margin-bottom: 12px;
    }
    
    .price-info {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      margin-bottom: 16px;
      
      .coin-icon {
        font-size: 20px;
      }
      
      .price {
        font-size: 24px;
        font-weight: bold;
        color: #ffd700;
      }
      
      .original {
        font-size: 14px;
        color: rgba(255, 255, 255, 0.5);
        text-decoration: line-through;
      }
    }
    
    .purchase-btn {
      background: linear-gradient(135deg, #ffd700, #ff9500);
      border: none;
      padding: 12px 32px;
      border-radius: 25px;
      color: #000;
      font-weight: bold;
      font-size: 15px;
      cursor: pointer;
      transition: all 0.3s;
      
      &:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.4);
      }
    }
    
    .vip-tip {
      margin-top: 12px;
      font-size: 12px;
      color: #a855f7;
    }
  }
}

// 试看结束遮罩 - 新样式（适配播放器尺寸）
.trial-ended-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 20;
  
  .trial-ended-content {
    text-align: center;
    padding: 15px 12px;
    width: 100%;
    max-width: 320px;
    
    .trial-ended-title {
      font-size: 15px;
      font-weight: 600;
      color: #fff;
      margin-bottom: 4px;
      letter-spacing: 1px;
    }
    
    .trial-ended-subtitle {
      font-size: 11px;
      color: rgba(255, 255, 255, 0.85);
      margin-bottom: 12px;
    }
    
    .trial-ended-actions {
      display: flex;
      justify-content: center;
      gap: 20px;
      flex-wrap: wrap;
      
      .share-btn {
        background: linear-gradient(90deg, #8b5cf6, #a855f7);
        border: none;
        padding: 8px 20px;
        border-radius: 50px;
        color: #fff;
        font-weight: 500;
      font-size: 13px;
        cursor: pointer;
        transition: opacity 0.2s;
        white-space: nowrap;
        min-height: auto !important;
        min-width: auto !important;
        
        &:hover {
          opacity: 0.85;
        }
        
        &:active {
          opacity: 0.75;
        }
      }
      
      .vip-btn {
        background: linear-gradient(90deg, #fbbf24, #f59e0b);
        border: none;
        padding: 8px 20px;
        border-radius: 50px;
        color: #000;
        font-weight: 500;
        font-size: 13px;
        cursor: pointer;
        transition: opacity 0.2s;
        white-space: nowrap;
        min-height: auto !important;
        min-width: auto !important;
        
        &:hover {
          opacity: 0.85;
        }
        
        &:active {
          opacity: 0.75;
        }
      }
    }
    
    .coin-purchase-option {
      margin-top: 14px;
      
      .divider-text {
        display: block;
        font-size: 11px;
        color: rgba(255, 255, 255, 0.5);
        margin-bottom: 8px;
      }
      
      .coin-price-info {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 6px 14px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        cursor: pointer;
        transition: all 0.3s;
        color: rgba(255, 255, 255, 0.8);
        font-size: 12px;
        
        &:hover {
          background: rgba(255, 255, 255, 0.15);
        color: #ffd700;
        }
        
        .coin-icon {
          font-size: 16px;
        }
        
        .arrow {
          font-size: 18px;
          margin-left: 4px;
        }
      }
    }
  }
}

// 分享弹窗
.share-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10000;
  padding: 20px;
  
  .share-modal-content {
    background: #1a1a2e;
    border-radius: 16px;
    width: 100%;
    max-width: 340px;
    padding: 24px 20px;
    position: relative;
    
    .share-modal-close {
      position: absolute;
      top: 12px;
      right: 12px;
      width: 28px;
      height: 28px;
      border: none;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 50%;
      font-size: 20px;
      color: rgba(255, 255, 255, 0.7);
        cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      line-height: 1;
      min-height: auto !important;
      min-width: auto !important;
        
        &:hover {
        background: rgba(255, 255, 255, 0.2);
      }
    }
    
    .share-header {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 14px;
      
      .share-logo {
        width: 40px;
        height: 40px;
        border-radius: 8px;
        object-fit: cover;
      }
      
      .share-title-info {
        .share-site-name {
          font-size: 16px;
          font-weight: 600;
          color: #fff;
          margin: 0 0 2px 0;
        }
        
        .share-site-desc {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.6);
          margin: 0;
        }
      }
    }
    
    .share-promo-image {
      width: 100%;
      border-radius: 12px;
      overflow: hidden;
      margin-bottom: 16px;
      
      img {
        width: 100%;
        height: auto;
        display: block;
      }
    }
    
    .share-qr-section {
      display: flex;
      align-items: center;
      gap: 16px;
      margin-bottom: 20px;
      
      .share-qrcode {
        flex-shrink: 0;
        background: #fff;
        padding: 6px;
        border-radius: 8px;
        
        img {
          width: 90px;
          height: 90px;
          border-radius: 4px;
          display: block;
        }
      }
      
      .share-invite-info {
        .invite-code {
          font-size: 16px;
          color: #fff;
          margin-bottom: 8px;
          
          span {
            font-weight: 700;
        color: #a855f7;
            margin-left: 6px;
          }
        }
        
        .official-url {
          font-size: 13px;
          color: rgba(255, 255, 255, 0.6);
          word-break: break-all;
        }
      }
    }
    
    .share-actions {
      display: flex;
      gap: 12px;
      
      .copy-link-btn, .save-image-btn {
        flex: 1;
        padding: 12px 16px;
        border-radius: 50px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: opacity 0.2s;
        min-height: auto !important;
        min-width: auto !important;
        
        &:hover {
          opacity: 0.85;
        }
      }
      
      .copy-link-btn {
        background: transparent;
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: #fff;
      }
      
      .save-image-btn {
        background: linear-gradient(90deg, #8b5cf6, #a855f7);
        border: none;
        color: #fff;
      }
    }
  }
}

// 购买弹窗
.purchase-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  
  .modal-content {
    background: linear-gradient(180deg, #1a1a2e 0%, #16162a 100%);
    border-radius: 16px;
    width: 90%;
    max-width: 360px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.1);
    
    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 20px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      
      h3 {
        margin: 0;
        font-size: 15px;
        color: #fff;
      }
      
      .close-btn {
        font-size: 24px;
        color: rgba(255, 255, 255, 0.5);
        cursor: pointer;
        
        &:hover {
          color: #fff;
        }
      }
    }
    
    .modal-body {
      padding: 20px;
      
      .video-preview {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 20px;
        
        img {
          width: 80px;
          height: 45px;
          border-radius: 6px;
          object-fit: cover;
        }
        
        .video-title {
          flex: 1;
          font-size: 14px;
          color: rgba(255, 255, 255, 0.9);
          overflow: hidden;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
        }
      }
      
      .price-detail {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 16px;
        
        .price-row {
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
          font-size: 14px;
          color: rgba(255, 255, 255, 0.7);
          
          &.discount {
            color: #67c23a;
            
            .discount-amount {
              color: #67c23a;
            }
          }
          
          &.total {
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            margin-top: 8px;
            padding-top: 12px;
            font-weight: bold;
            
            .total-price {
              font-size: 18px;
              color: #ffd700;
            }
          }
        }
      }
      
      .balance-row {
        display: flex;
        justify-content: space-between;
        font-size: 14px;
        color: rgba(255, 255, 255, 0.6);
        
        .balance {
          color: #ffd700;
          font-weight: bold;
          
          &.insufficient {
            color: #f56c6c;
          }
        }
      }
    }
    
    .modal-footer {
      padding: 16px 20px 24px;
      
      .confirm-btn {
        width: 100%;
        background: linear-gradient(135deg, #ffd700, #ff9500);
        border: none;
        padding: 14px;
        border-radius: 25px;
        color: #000;
        font-weight: bold;
        font-size: 16px;
        cursor: pointer;
        transition: all 0.3s;
        
        &:hover:not(:disabled) {
          transform: scale(1.02);
          box-shadow: 0 4px 15px rgba(255, 215, 0, 0.4);
        }
        
        &:disabled {
          background: linear-gradient(135deg, #666, #444);
          color: rgba(255, 255, 255, 0.5);
          cursor: not-allowed;
        }
      }
    }
  }
}

// ========== 图片灯箱预览样式 ==========
.lightbox-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.95);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: lightbox-fade-in 0.2s ease;
}

@keyframes lightbox-fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.lightbox-container {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.lightbox-close {
  position: fixed;
  top: 20px;
  right: 20px;
  width: 44px;
  height: 44px;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  font-size: 24px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  z-index: 10001;
  
  &:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: scale(1.1);
  }
}

.lightbox-image {
  max-width: 90vw;
  max-height: 85vh;
  object-fit: contain;
  border-radius: 8px;
  transition: transform 0.2s ease;
  cursor: grab;
  
  &:active {
    cursor: grabbing;
  }
}

.lightbox-controls {
  position: fixed;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 12px;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(10px);
  padding: 10px 20px;
  border-radius: 30px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  z-index: 10001;
  
  .control-btn {
    width: 44px;
    height: 44px;
    border: none;
    background: rgba(255, 255, 255, 0.1);
    color: #fff;
    font-size: 14px;
    font-weight: 500;
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
    
    &:hover {
      background: rgba(168, 85, 247, 0.5);
      transform: scale(1.1);
    }
    
    svg {
      width: 20px;
      height: 20px;
    }
  }
}
</style>