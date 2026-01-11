<template>
  <div class="short-video-page">
    <!-- 顶部导航 -->
    <header class="short-header">
      <div class="back-btn" @click="goBack"><img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" /></div>
      <div class="header-tabs">
        <span 
          :class="['tab-item', { active: activeTab === 'recommend' }]"
          @click="activeTab = 'recommend'"
        >推荐</span>
        <span 
          :class="['tab-item', { active: activeTab === 'follow' }]"
          @click="activeTab = 'follow'"
        >关注</span>
      </div>
      <div class="search-btn" @click="$router.push('/user/search')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <path d="m21 21-4.35-4.35"/>
        </svg>
      </div>
    </header>

    <!-- 视频滑动容器 -->
    <div 
      class="video-swiper"
      ref="swiperRef"
      @touchstart="onTouchStart"
      @touchmove="onTouchMove"
      @touchend="onTouchEnd"
    >
      <div 
        class="video-track"
        :style="{ transform: `translateY(${translateY}px)`, transition: isAnimating ? 'transform 0.3s ease' : 'none' }"
      >
        <div 
          v-for="(video, index) in videos" 
          :key="video.id"
          class="video-slide"
        >
          <!-- 视频播放器 -->
          <video
            :ref="el => setVideoRef(index, el)"
            :src="video.video_url || video.hls_url"
            :poster="video.cover_url"
            class="short-video"
            loop
            playsinline
            webkit-playsinline
            x5-playsinline
            preload="auto"
            @timeupdate="onTimeUpdate(index, $event)"
            @loadedmetadata="onVideoLoaded(index)"
            @canplay="onVideoCanPlay(index)"
            @play="onVideoPlay(index)"
            @pause="onVideoPause(index)"
          />
          
          <!-- 点击区域（用于暂停/播放） -->
          <div 
            class="tap-area"
            @touchstart.passive="onTapStart"
            @touchend="onTapEnd(index, video, $event)"
            @click="onTapClick(index, video, $event)"
          ></div>

          <!-- 持续显示的播放图标（视频暂停时） -->
          <div class="persistent-pause" v-if="currentIndex === index && !isPlaying">
            <svg viewBox="0 0 48 48" fill="none">
              <path d="M16 10.5C16 9.5 16.8 8.5 18 9L38 22c1.5 1 1.5 3 0 4L18 39c-1.2 0.5-2-0.5-2-1.5V10.5z" 
                    fill="white" fill-opacity="0.85" 
                    stroke="white" stroke-width="1" stroke-linejoin="round" stroke-linecap="round"/>
            </svg>
          </div>

          <!-- 双击爱心动画 -->
          <div class="like-animation" v-if="showLikeAnimation && likeAnimationIndex === index">
            <svg class="heart" viewBox="0 0 24 24" fill="#fe2c55">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
            </svg>
          </div>

          <!-- 右侧操作栏 -->
          <div class="action-bar">
            <!-- 作者头像 -->
            <div class="author-avatar" @click.stop="goToProfile(video.uploader_id)">
              <img :src="getAvatarUrl(video.uploader_avatar, video.uploader_id)" alt="" />
              <span class="follow-btn" v-if="!video.is_followed" @click.stop="handleFollow(video)">+</span>
            </div>
            
            <!-- 点赞 -->
            <div class="action-item" @click.stop="handleLike(index)">
              <div :class="['icon-wrapper', { liked: videos[index].is_liked }]">
                <svg viewBox="0 0 24 24" :fill="videos[index].is_liked ? '#fe2c55' : 'white'">
                  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                </svg>
              </div>
              <span class="count">{{ formatCount(videos[index].like_count) }}</span>
            </div>
            
            <!-- 评论 -->
            <div class="action-item" @click.stop="openComments(video)">
              <div class="icon-wrapper">
                <svg viewBox="0 0 48 48" fill="white">
                  <path d="M24 4C12.95 4 4 11.95 4 22c0 5.3 2.55 10.05 6.6 13.35L8 44l10.4-5.2c1.8.5 3.65.8 5.6.8 11.05 0 20-7.95 20-18S35.05 4 24 4z"/>
                </svg>
              </div>
              <span class="count">{{ formatCount(video.comment_count) }}</span>
            </div>
            
            <!-- 收藏 -->
            <div class="action-item" @click.stop="handleFavorite(index)">
              <div :class="['icon-wrapper', { favorited: videos[index].is_favorited }]">
                <svg viewBox="0 0 24 24" :fill="videos[index].is_favorited ? '#ffc107' : 'white'">
                  <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/>
                </svg>
              </div>
              <span class="count">{{ formatCount(videos[index].favorite_count || 0) }}</span>
            </div>
            
            <!-- 分享 -->
            <div class="action-item" @click.stop="handleShare(video)">
              <div class="icon-wrapper">
                <svg viewBox="0 0 24 24" fill="white">
                  <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92s2.92-1.31 2.92-2.92-1.31-2.92-2.92-2.92z"/>
                </svg>
              </div>
              <span class="count">{{ formatCount(video.share_count || 0) }}</span>
            </div>
            
            <!-- 下载 -->
            <div class="action-item" @click.stop="handleDownload(video)">
              <div :class="['icon-wrapper', { 'vip-feature': !isUserVip }]">
                <svg viewBox="0 0 24 24" fill="white">
                  <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
                </svg>
                <span v-if="!isUserVip" class="vip-tag">VIP</span>
              </div>
              <span class="count">下载</span>
            </div>
          </div>

          <!-- 底部信息 -->
          <div class="video-info">
            <!-- VIP提示条：VIP专属视频显示，或需要试看的视频显示 -->
            <div 
              class="vip-tip-bar" 
              v-if="video.is_vip_only || isTrialVideo(video)"
              @click.stop="(isUserVip && video.is_vip_only) ? null : $router.push('/user/vip')"
            >
              <!-- VIP用户观看VIP专属视频：显示已享特权 -->
              <template v-if="isUserVip && video.is_vip_only">
                <span class="vip-icon">👑</span>
                <span class="vip-text">已享VIP免费特权</span>
              </template>
              <!-- 非VIP用户或非VIP专属的付费视频：显示开通提示 -->
              <template v-else>
                <span class="vip-text">开通会员 畅享完整版</span>
                <span class="vip-arrow">›</span>
              </template>
            </div>
            <div class="author-name">@{{ video.uploader_nickname || '用户' }}</div>
            <div class="video-title">{{ video.title }}</div>
            <div class="video-desc" v-if="video.description">{{ video.description }}</div>
          </div>

          <!-- 进度条 -->
          <div class="progress-bar-container" v-if="currentIndex === index">
            <span class="time-display">{{ formatDuration(currentPlayTime) }} / {{ formatDuration(video.duration) }}</span>
            <div 
              class="progress-bar"
              ref="progressBarRef"
              @click.stop="onProgressClick($event, video)"
              @touchstart.stop="onProgressTouchStart"
              @touchmove.stop="onProgressTouchMove($event, video)"
              @touchend.stop="onProgressTouchEnd"
            >
              <div class="progress" :style="{ width: progress + '%' }"></div>
              <div class="progress-thumb" :style="{ left: progress + '%' }"></div>
            </div>
          </div>

          <!-- 试看倒计时提示 -->
          <div 
            class="trial-countdown" 
            v-if="currentIndex === index && isTrialVideo(video) && !isTrialEnded && trialRemaining > 0 && trialRemaining <= 5"
          >
            <span class="countdown-text">试看剩余 {{ trialRemaining }}s</span>
          </div>

          <!-- 试看结束遮罩 -->
          <div class="trial-overlay" v-if="currentIndex === index && isTrialEnded && isTrialVideo(video)">
            <div class="trial-content">
              <h3>试看结束</h3>
              <p class="trial-subtitle">开通VIP 永久免费观看</p>
              
              <!-- 顶部两个并排按钮 -->
              <div class="trial-top-btns">
                <button class="share-btn" @click.stop="handleShare(video)">
                  分享得3日VIP
                </button>
                <button class="vip-btn" @click.stop="$router.push('/user/vip')">
                  开通VIP免费看
                </button>
              </div>
              
              <!-- 分隔符 -->
              <div class="trial-divider">或</div>
              
              <!-- 金币购买按钮 -->
              <button class="coin-purchase-btn" @click.stop="handlePurchase(video)" :disabled="purchasing">
                <span class="coin-icon">🪙</span>
                {{ video.coin_price || 20 }} 金币购买本片
                <span class="arrow">›</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div class="loading-indicator" v-if="loading">
      <span class="spinner"></span>
    </div>

    <!-- 空状态 -->
    <div class="empty-state" v-if="!loading && videos.length === 0">
      <img src="/images/backgrounds/no_data.webp" alt="" />
      <p>暂无短视频内容</p>
    </div>

    <!-- 评论弹窗 -->
    <div class="comments-drawer" v-if="showComments" @click.self="showComments = false">
      <div class="drawer-content">
        <div class="drawer-header">
          <span class="comment-count">{{ currentVideo?.comment_count || 0 }} 条评论</span>
          <span class="close-btn" @click="showComments = false">×</span>
        </div>
        <div class="comments-list">
          <!-- 官方公告 -->
          <div v-if="announcement && announcement.enabled" class="comment-item official-announcement">
            <img :src="announcement.avatar || '/images/avatars/icon_avatar_1.webp'" class="comment-avatar" />
            <div class="comment-body">
              <div class="comment-user">
                <span class="username official-name">{{ announcement.name }}</span>
                <!-- 至尊图标 -->
                <img src="/images/backgrounds/super_vip_blue.webp" class="supreme-vip-icon" />
              </div>
              <div class="comment-text official-text">{{ announcement.content }}</div>
              <div class="comment-meta">
                <span class="time">{{ formatAnnouncementTime(announcement.updated_at) }}</span>
              </div>
            </div>
          </div>
          
          <div v-for="comment in comments" :key="comment.id" class="comment-item">
            <img :src="getAvatarUrl(comment.user_avatar, comment.user_id)" class="comment-avatar clickable" @click="goToProfile(comment.user_id)" />
            <div class="comment-body">
              <div class="comment-user">
                <span class="username clickable" @click="goToProfile(comment.user_id)">{{ comment.user_nickname || comment.user_name }}</span>
                <!-- 显示VIP等级图标 -->
                <img 
                  v-if="comment.user_vip_level > 0" 
                  :src="getVipLevelIcon(comment.user_vip_level)" 
                  class="vip-badge-sm"
                />
              </div>
              <div class="comment-text">{{ comment.content }}</div>
              <!-- 评论图片 -->
              <div v-if="comment.image_url" class="comment-image" @click="previewCommentImage(comment.image_url)">
                <img :src="comment.image_url" alt="comment image" />
              </div>
              <div class="comment-meta">
                <span class="time">{{ formatCommentTime(comment.created_at) }}</span>
                <span class="reply-btn" @click.stop="setReplyTo(comment)">回复</span>
                <span 
                  :class="['like-btn', { liked: comment.is_liked }]" 
                  @click.stop="likeComment(comment)"
                >
                  {{ comment.is_liked ? '❤️' : '🤍' }} {{ comment.like_count || 0 }}
                </span>
              </div>
              
              <!-- 回复列表 -->
              <div v-if="comment.reply_count > 0" class="replies-section">
                <div 
                  v-if="!comment.showReplies" 
                  class="view-replies-btn"
                  @click.stop="loadReplies(comment)"
                >
                  查看 {{ comment.reply_count }} 条回复 ▼
                </div>
                <div v-else class="replies-list">
                  <div v-for="reply in comment.replies" :key="reply.id" class="reply-item">
                    <img :src="getAvatarUrl(reply.user_avatar, reply.user_id)" class="reply-avatar clickable" @click="goToProfile(reply.user_id)" />
                    <div class="reply-body">
                      <div class="reply-user">
                        <span class="username clickable" @click="goToProfile(reply.user_id)">{{ reply.user_nickname || reply.user_name }}</span>
                        <img v-if="reply.user_vip_level > 0" :src="getVipLevelIcon(reply.user_vip_level)" class="vip-badge-xs" />
                      </div>
                      <div class="reply-text">{{ reply.content }}</div>
                      <div v-if="reply.image_url" class="reply-image" @click="previewCommentImage(reply.image_url)">
                        <img :src="reply.image_url" alt="reply image" />
                      </div>
                      <div class="reply-meta">
                        <span class="time">{{ formatCommentTime(reply.created_at) }}</span>
                        <span class="reply-btn" @click.stop="setReplyTo(comment, reply)">回复</span>
                        <span :class="['like-btn', { liked: reply.is_liked }]" @click.stop="likeComment(reply)">
                          {{ reply.is_liked ? '❤️' : '🤍' }} {{ reply.like_count || 0 }}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div class="hide-replies-btn" @click.stop="comment.showReplies = false">
                    收起回复 ▲
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="empty-comments" v-if="comments.length === 0">
            暂无评论，快来抢沙发~
          </div>
        </div>
        <div class="comment-input-bar">
          <!-- 非VIP提示 -->
          <div v-if="!isUserVip" class="vip-comment-tip" @click="$router.push('/user/vip')">
            <span class="tip-icon">👑</span>
            <span class="tip-text">开通VIP即可发表评论</span>
            <span class="tip-btn">立即开通 ›</span>
          </div>
          
          <!-- VIP评论输入区 -->
          <div v-else class="input-area">
            <!-- 回复提示 -->
            <div v-if="replyTo" class="reply-hint">
              <span>回复 @{{ replyTo.user_nickname || replyTo.user_name }}</span>
              <span class="cancel-reply" @click="cancelReply">×</span>
            </div>
            
            <!-- 图片预览 -->
            <div v-if="commentImage" class="image-preview">
              <img :src="commentImagePreview" alt="preview" />
              <span class="remove-image" @click="removeCommentImage">×</span>
            </div>
            
            <div class="input-row">
              <input 
                type="text" 
                v-model="commentText" 
                :placeholder="replyTo ? `回复 @${replyTo.user_nickname || replyTo.user_name}` : '说点什么吧...'"
                @keyup.enter="submitComment"
                ref="commentInputRef"
              />
              <div class="input-actions">
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
            <img :src="shareVideo?.cover_url || '/images/default-cover.webp'" alt="推广图" />
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
            <button class="copy-link-btn" @click="copyShareLink">复制链接</button>
            <button class="save-image-btn" @click="saveShareImage">保存图片</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'
import { useUserStore } from '@/stores/user'
import { useAbortController } from '@/composables/useAbortController'
import { useTimers, useVideoCleanup, useEventListeners } from '@/composables/useCleanup'
import { useDebounce } from '@/composables/useDebounce'
import { formatCount, formatDuration } from '@/utils/format'
import { VIP_LEVEL_ICONS } from '@/constants/vip'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 请求取消控制器
const { signal: abortSignal } = useAbortController()

// 定时器管理
const timers = useTimers()

// 视频资源管理
const videoCleanup = useVideoCleanup()

// 事件监听器管理
const events = useEventListeners()

// 防抖处理
const { debounce } = useDebounce()

// 检查用户是否是VIP（使用 store 的计算属性）
const isUserVip = computed(() => {
  // 同时检查多种可能的VIP标识
  return userStore.isVip || userStore.user?.is_vip === true || (userStore.user?.vip_level && userStore.user.vip_level > 0)
})

// 数据状态
const videos = ref([])
const currentIndex = ref(0)
const loading = ref(false)
const page = ref(1)
const hasMore = ref(true)
const activeTab = ref('recommend')

// 播放状态
const isPlaying = ref(false)
const userPaused = ref(false)  // 用户主动暂停标记
const hasAutoPlayed = ref(false)  // 当前视频是否已自动播放过
const progress = ref(0)
let playTimerId = null  // 延迟播放定时器ID
let lastPauseTime = 0  // 上次暂停时间戳
const videoRefs = ref({})

// 试看相关状态
const isTrialEnded = ref(false)
const trialRemaining = ref(15)
const currentPlayTime = ref(0)

// 滑动状态
const swiperRef = ref(null)
const translateY = ref(0)
const startY = ref(0)
const isDragging = ref(false)
const isAnimating = ref(false)
const slideHeight = ref(0)

// 进度条
const progressBarRef = ref(null)
const isSeeking = ref(false)

// 双击点赞动画
const showLikeAnimation = ref(false)
const likeAnimationIndex = ref(-1)

// 点击区域状态
const tapStartX = ref(0)
const tapStartY = ref(0)
const tapStartTime = ref(0)
const isTapHandled = ref(false)  // 防止 touchend 和 click 重复处理

// 评论
const showComments = ref(false)
const comments = ref([])
const commentText = ref('')
const announcement = ref(null)
const currentVideo = ref(null)

// 分享弹窗相关
const showShareModal = ref(false)
const shareVideo = ref(null)
const userInviteCode = ref('3AUUHR')
const shareBaseUrl = computed(() => window.location.origin.replace(/^https?:\/\//, ''))
const shareFullUrl = computed(() => {
  if (!shareVideo.value) return ''
  return `${window.location.origin}/shorts/${shareVideo.value.id}?ref=${userInviteCode.value}`
})
const shareQrCodeUrl = computed(() => `https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${encodeURIComponent(shareFullUrl.value)}`)

// 评论输入相关
const commentInputRef = ref(null)
const showEmojiPicker = ref(false)
const commentImage = ref(null)
const commentImagePreview = ref('')
const submittingComment = ref(false)
const replyTo = ref(null)  // 回复目标
const replyParentId = ref(null)  // 回复的父评论ID

// 表情列表
const emojiList = [
  '😀', '😂', '🤣', '😊', '😍', '🥰', '😘', '😜', '🤪', '😎',
  '🥳', '😇', '🤩', '😋', '😛', '🤤', '😏', '😒', '😔', '😢',
  '😭', '😤', '😠', '🤬', '😱', '😰', '😥', '🤧', '😷', '🤒',
  '👍', '👎', '👏', '🙏', '💪', '❤️', '💔', '💯', '🔥', '✨',
  '🎉', '🎊', '💎', '🏆', '🥇', '⭐', '🌟', '💫', '🌈', '☀️'
]

// 设置视频引用
const setVideoRef = (index, el) => {
  if (el) {
    videoRefs.value[index] = el
  }
}

// 获取当前视频
const getCurrentVideo = () => videos.value[currentIndex.value]

// 检查是否是试看视频（需要限制观看时长）
const isTrialVideo = (video) => {
  if (!video) return false
  // 如果已购买，不需要试看限制
  if (video.is_purchased) return false
  // 如果有试看时长设置（后端返回 > 0 表示需要试看）
  return (video.trial_seconds && video.trial_seconds > 0)
}

// 获取试看时长
const getTrialSeconds = (video) => {
  if (!video || !isTrialVideo(video)) return 0
  return video.trial_seconds || 15
}

// 获取头像URL（如果没有自定义头像，使用默认头像）
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

const getAvatarUrl = (avatar, userId) => {
  if (avatar) {
    // 如果头像路径是相对路径，添加前缀
    if (avatar.startsWith('/')) return avatar
    if (avatar.startsWith('http')) return avatar
    return '/' + avatar
  }
  // 使用默认头像
  const numericId = parseInt(userId) || 1
  return getDefaultAvatarPath(numericId)
}

// 格式化时间
const formatTime = (time) => {
  const d = new Date(time)
  const now = new Date()
  const diff = (now - d) / 1000
  
  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + '小时前'
  if (diff < 2592000) return Math.floor(diff / 86400) + '天前'
  
  return `${d.getMonth() + 1}/${d.getDate()}`
}

// 获取短视频列表
const fetchVideos = async (reset = false) => {
  if (loading.value || (!hasMore.value && !reset)) return
  
  loading.value = true
  
  try {
    if (reset) {
      page.value = 1
      videos.value = []
      currentIndex.value = 0
      isTrialEnded.value = false
    }
    
    const res = await api.get('/shorts', {
      params: { page: page.value, limit: 10 },
      signal: abortSignal
    })
    
    const data = res.data || res
    if (data.items && data.items.length > 0) {
      videos.value = reset ? data.items : [...videos.value, ...data.items]
      hasMore.value = data.has_more
      page.value++
      
      // 重置后初始化试看状态并自动播放第一个视频
      if (reset && data.items.length > 0) {
        trialRemaining.value = getTrialSeconds(data.items[0])
        userPaused.value = false
        hasAutoPlayed.value = false
        // 等待DOM更新后自动播放
        await nextTick()
        if (playTimerId) {
          timers.clearTimeout(playTimerId)
        }
        playTimerId = timers.setTimeout(() => {
          playTimerId = null
          if (!userPaused.value) {
            playCurrentVideo()
          }
        }, 200)
      }
    } else {
      hasMore.value = false
    }
  } catch (error) {
    if (error.name !== 'CanceledError' && error.name !== 'AbortError') {
      console.error('获取短视频失败:', error)
    }
  } finally {
    loading.value = false
  }
}

// 触摸事件
const onTouchStart = (e) => {
  if (isAnimating.value) return
  startY.value = e.touches[0].clientY
  isDragging.value = true
}

const onTouchMove = (e) => {
  if (!isDragging.value) return
  
  const deltaY = e.touches[0].clientY - startY.value
  const newTranslate = -currentIndex.value * slideHeight.value + deltaY
  
  // 限制滑动范围
  const maxTranslate = 0
  const minTranslate = -(videos.value.length - 1) * slideHeight.value
  
  translateY.value = Math.max(minTranslate - 100, Math.min(maxTranslate + 100, newTranslate))
}

const onTouchEnd = (e) => {
  if (!isDragging.value) return
  isDragging.value = false
  
  const deltaY = e.changedTouches[0].clientY - startY.value
  const threshold = slideHeight.value * 0.2
  
  if (Math.abs(deltaY) > threshold) {
    if (deltaY < 0 && currentIndex.value < videos.value.length - 1) {
      // 向上滑 - 下一个视频
      goToSlide(currentIndex.value + 1)
    } else if (deltaY > 0 && currentIndex.value > 0) {
      // 向下滑 - 上一个视频
      goToSlide(currentIndex.value - 1)
    } else {
      // 回弹
      goToSlide(currentIndex.value)
    }
  } else {
    // 回弹
    goToSlide(currentIndex.value)
  }
  
  // 预加载更多
  if (currentIndex.value >= videos.value.length - 3) {
    fetchVideos()
  }
}

// 跳转到指定视频
const goToSlide = (index) => {
  const isChangingVideo = index !== currentIndex.value
  
  isAnimating.value = true
  translateY.value = -index * slideHeight.value
  
  // 只有真正切换视频时才执行重置逻辑
  if (isChangingVideo) {
    // 暂停所有视频（确保之前的视频停止）
    Object.entries(videoRefs.value).forEach(([idx, video]) => {
      if (video && parseInt(idx) !== index) {
        video.pause()
      }
    })
    
    currentIndex.value = index
    
    // 重置状态 - 切换视频时清除暂停标记
    userPaused.value = false
    hasAutoPlayed.value = false
    isTrialEnded.value = false
    currentPlayTime.value = 0
    const newVideo = videos.value[index]
    trialRemaining.value = getTrialSeconds(newVideo)
    
    // 新视频从头开始播放
    const newVideoEl = videoRefs.value[index]
    if (newVideoEl) {
      newVideoEl.currentTime = 0
    }
    
    // 取消之前的播放定时器
    if (playTimerId) {
      timers.clearTimeout(playTimerId)
      playTimerId = null
    }
    
    playTimerId = timers.setTimeout(() => {
      isAnimating.value = false
      playTimerId = null
      // 只有当用户没有主动暂停时才播放
      if (!userPaused.value) {
        playCurrentVideo()
      }
    }, 300)
  } else {
    // 回弹到当前视频，不重置任何状态
    timers.setTimeout(() => {
      isAnimating.value = false
    }, 300)
  }
}

// 播放当前视频
const playCurrentVideo = () => {
  const videoEl = videoRefs.value[currentIndex.value]
  const timeSincePause = Date.now() - lastPauseTime
  
  // 如果在 500ms 内刚刚暂停过，不自动播放
  if (lastPauseTime > 0 && timeSincePause < 500) {
    return
  }
  
  // 先暂停所有其他视频
  Object.entries(videoRefs.value).forEach(([idx, video]) => {
    if (video && parseInt(idx) !== currentIndex.value) {
      video.pause()
    }
  })
  
  if (videoEl && !userPaused.value) {
    // 不重置 currentTime，让视频从当前位置继续播放
    videoEl.play().catch((err) => {
      // 如果浏览器阻止带声音播放，静音重试
      if (err.name === 'NotAllowedError') {
        videoEl.muted = true
        videoEl.play().catch(() => {})
      }
    })
  }
}

// 视频播放事件
const onVideoPlay = (index) => {
  if (index === currentIndex.value) {
    isPlaying.value = true
  }
}

// 视频暂停事件
const onVideoPause = (index) => {
  if (index === currentIndex.value) {
    isPlaying.value = false
  }
}


// 切换播放/暂停
// 双击检测
let lastTapTime = 0
let lastTapWasPlay = false  // 记录上次单击是否是播放操作

// 点击区域触摸开始
const onTapStart = (e) => {
  if (e.touches && e.touches.length > 0) {
    tapStartX.value = e.touches[0].clientX
    tapStartY.value = e.touches[0].clientY
    tapStartTime.value = Date.now()
    isTapHandled.value = false
  }
}

// 点击区域触摸结束（移动端）
const onTapEnd = (index, video, e) => {
  if (isTapHandled.value) return
  if (!e.changedTouches || e.changedTouches.length === 0) return
  
  const touch = e.changedTouches[0]
  const dx = Math.abs(touch.clientX - tapStartX.value)
  const dy = Math.abs(touch.clientY - tapStartY.value)
  
  // 移动距离大于 15px 视为滑动，不处理
  if (dx > 15 || dy > 15) return
  
  // 标记已处理，防止 click 重复触发
  isTapHandled.value = true
  e.preventDefault()
  doHandleTap()
}

// 点击事件（桌面端）
const onTapClick = (index, video, e) => {
  // 如果已经被 touchend 处理过，跳过
  if (isTapHandled.value) {
    isTapHandled.value = false
    return
  }
  doHandleTap()
}

// 实际处理点击逻辑
const doHandleTap = () => {
  const targetIndex = currentIndex.value
  const targetVideo = videos.value[targetIndex]
  
  const now = Date.now()
  const timeDiff = now - lastTapTime
  
  if (timeDiff < 300 && timeDiff > 0) {
    // 双击 - 点赞
    lastTapTime = 0
    // 撤销单击的播放/暂停操作
    if (lastTapWasPlay) {
      const videoEl = videoRefs.value[targetIndex]
      if (videoEl && !videoEl.paused) {
        userPaused.value = true
        videoEl.pause()
      }
    } else {
      const videoEl = videoRefs.value[targetIndex]
      if (videoEl && videoEl.paused) {
        userPaused.value = false
        hasAutoPlayed.value = true
        videoEl.play().catch(() => {})
      }
    }
    handleDoubleTap(targetVideo)
  } else {
    // 单击 - 立即暂停/播放
    lastTapTime = now
    const videoEl = videoRefs.value[targetIndex]
    lastTapWasPlay = videoEl?.paused ?? false
    togglePlay(targetIndex)
  }
}

const togglePlay = (index) => {
  if (index !== currentIndex.value) return
  
  const videoEl = videoRefs.value[index]
  if (!videoEl) return
  
  // 如果试看已结束，点击不播放
  const video = videos.value[index]
  if (isTrialEnded.value && isTrialVideo(video)) return
  
  // 根据视频实际状态切换
  if (videoEl.paused) {
    // 先暂停所有其他视频
    Object.entries(videoRefs.value).forEach(([idx, v]) => {
      if (v && parseInt(idx) !== index) {
        v.pause()
      }
    })
    
    // 视频已暂停，执行播放
    hasAutoPlayed.value = true
    userPaused.value = false
    lastPauseTime = 0
    
    videoEl.play().catch((err) => {
      // 如果浏览器阻止带声音播放，静音重试
      if (err.name === 'NotAllowedError') {
        videoEl.muted = true
        videoEl.play().catch(() => {})
      }
    })
  } else {
    // 视频正在播放，执行暂停
    userPaused.value = true
    lastPauseTime = Date.now()
    if (playTimerId) {
      timers.clearTimeout(playTimerId)
      playTimerId = null
    }
    videoEl.pause()
  }
  
}

// 双击点赞
const handleDoubleTap = (video) => {
  if (!video.is_liked) {
    handleLike(video)
  }
  
  // 显示爱心动画
  likeAnimationIndex.value = currentIndex.value
  showLikeAnimation.value = true
  timers.setTimeout(() => {
    showLikeAnimation.value = false
  }, 1000)
}

// 点赞
// 操作锁，防止重复点击
const actionLocks = ref({})

// 点赞
const handleLike = async (index) => {
  const video = videos.value[index]
  if (!video) return
  
  const lockKey = `like_${video.id}`
  if (actionLocks.value[lockKey]) return
  actionLocks.value[lockKey] = true
  
  // 保存原始状态
  const wasLiked = video.is_liked
  const oldCount = video.like_count || 0
  
  // 立即更新UI
  video.is_liked = !wasLiked
  video.like_count = wasLiked ? Math.max(0, oldCount - 1) : oldCount + 1
  
  try {
    const res = await api.post(`/shorts/${video.id}/like`)
    const data = res.data || res
    video.is_liked = data.liked
    video.like_count = data.like_count
  } catch (error) {
    // 回滚
    video.is_liked = wasLiked
    video.like_count = oldCount
    ElMessage.error('操作失败')
  } finally {
    actionLocks.value[lockKey] = false
  }
}

// 收藏
const handleFavorite = async (index) => {
  const video = videos.value[index]
  if (!video) return
  
  const lockKey = `favorite_${video.id}`
  if (actionLocks.value[lockKey]) return
  actionLocks.value[lockKey] = true
  
  // 保存原始状态
  const wasFavorited = video.is_favorited
  const oldCount = video.favorite_count || 0
  
  // 立即更新UI
  video.is_favorited = !wasFavorited
  video.favorite_count = wasFavorited ? Math.max(0, oldCount - 1) : oldCount + 1
  
  try {
    const res = await api.post(`/shorts/${video.id}/favorite`)
    const data = res.data || res
    video.is_favorited = data.favorited
    video.favorite_count = data.favorite_count
    ElMessage.success(data.favorited ? '收藏成功' : '已取消收藏')
  } catch (error) {
    // 回滚
    video.is_favorited = wasFavorited
    video.favorite_count = oldCount
    ElMessage.error('操作失败')
  } finally {
    actionLocks.value[lockKey] = false
  }
}

// 关注（带防抖）
const handleFollow = async (video) => {
  const uploaderId = video.uploader_id
  if (!uploaderId) return
  
  const lockKey = `follow_${uploaderId}`
  if (actionLocks.value[lockKey]) return
  actionLocks.value[lockKey] = true
  
  try {
    await api.post(`/users/${uploaderId}/follow`)
    video.is_followed = true
    ElMessage.success('关注成功')
  } catch (error) {
    if (error.response?.status === 401) {
      ElMessage.warning('请先登录')
    } else if (error.response?.status === 400) {
      // 已关注或不能关注自己
      video.is_followed = true  // 更新状态
    } else {
      ElMessage.error(error.response?.data?.detail || '关注失败')
    }
  } finally {
    timers.setTimeout(() => {
      actionLocks.value[lockKey] = false
    }, 500)
  }
}

// 分享
const handleShare = (video) => {
  shareVideo.value = video
  showShareModal.value = true
}

// 下载视频
const handleDownload = async (video) => {
  // 检查VIP权限
  if (!isUserVip.value) {
    ElMessage.warning('下载功能仅限VIP会员使用')
    router.push('/user/vip')
    return
  }
  
  try {
    // 先获取下载信息
    const infoRes = await api.get(`/shorts/${video.id}/download-info`, { signal: abortSignal })
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
      id: `short_${video.id}_${Date.now()}`,
      videoId: video.id,
      title: video.title,
      thumbnail: video.cover_url,
      duration: video.duration,
      views: video.view_count,
      fileSize: fileSize,
      type: 'short',
      status: 'completed',
      downloadTime: Date.now()
    })
    
    // 开始下载
    const downloadUrl = `/api/v1/shorts/${video.id}/download`
    
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
    } else if (error.response?.status === 429) {
      ElMessage.warning(error.response?.data?.detail || '今日下载次数已达上限')
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

// 复制分享链接
const copyShareLink = () => {
  navigator.clipboard.writeText(shareFullUrl.value).then(() => {
    ElMessage.success('分享链接已复制，分享给好友注册后可获得3日VIP')
  }).catch(() => {
    ElMessage.info('请复制链接分享：' + shareFullUrl.value)
  })
}

// 保存分享图片
const saveShareImage = () => {
  ElMessage.info('长按图片保存到相册')
}

// 购买中状态
const purchasing = ref(false)

// 购买视频
const handlePurchase = async (video) => {
  // 防止重复点击
  if (purchasing.value) return
  
  // 如果已购买，直接播放
  if (video.is_purchased) {
    isTrialEnded.value = false
    playCurrentVideo()
    return
  }
  
  const coinPrice = video.coin_price || 20
  
  // 快速通道：缓存余额已获取且明显不足时直接跳转（不等API）
  if (userCoinsBalance.value >= 0 && userCoinsBalance.value < coinPrice) {
    ElMessage.warning('金币不足，请先充值')
    router.push('/user/coins')
    return
  }
  
  // 余额充足或未知，调用购买API（后端会做最终校验）
  purchasing.value = true
  try {
    await api.post(`/coins/purchase/video/${video.id}`)
    ElMessage.success('购买成功！')
    video.is_purchased = true
    isTrialEnded.value = false
    trialRemaining.value = getTrialSeconds(video)
    // 更新缓存余额
    userCoinsBalance.value = Math.max(0, userCoinsBalance.value - coinPrice)
    // 重新播放
    playCurrentVideo()
  } catch (error) {
    const detail = error.response?.data?.detail
    if (detail === '您已购买过此视频') {
      video.is_purchased = true
      isTrialEnded.value = false
      playCurrentVideo()
      ElMessage.success('视频已解锁')
    } else if (detail === '此视频无需购买') {
      isTrialEnded.value = false
      playCurrentVideo()
    } else if (detail === '金币余额不足') {
      // 后端确认余额不足，更新缓存并跳转
      userCoinsBalance.value = 0
      ElMessage.warning('金币不足，请先充值')
      router.push('/user/coins')
    } else if (detail) {
      ElMessage.error(detail)
    } else {
      ElMessage.error('购买失败，请重试')
    }
  } finally {
    purchasing.value = false
  }
}

// 重新试看
const replayTrial = (index) => {
  const videoEl = videoRefs.value[index]
  if (videoEl) {
    videoEl.currentTime = 0
    isTrialEnded.value = false
    userPaused.value = false  // 重置暂停状态
    const currentVideo = videos.value[index]
    trialRemaining.value = getTrialSeconds(currentVideo)
    videoEl.play().catch((err) => {
      if (err.name !== 'AbortError') {
        console.warn('Replay failed:', err.message)
      }
    })
  }
}

// 计算进度条点击位置对应的时间
const getSeekTimeFromEvent = (event, video) => {
  const progressBar = event.currentTarget
  const rect = progressBar.getBoundingClientRect()
  const clickX = event.clientX || (event.touches && event.touches[0]?.clientX) || 0
  const offsetX = clickX - rect.left
  const percentage = Math.max(0, Math.min(1, offsetX / rect.width))
  const duration = video.duration || 0
  
  // 如果是试看视频，限制最大时间
  if (isTrialVideo(video)) {
    const maxTime = getTrialSeconds(video)
    return Math.min(percentage * duration, maxTime)
  }
  
  return percentage * duration
}

// 进度条点击跳转
const onProgressClick = (event, video) => {
  const videoEl = videoRefs.value[currentIndex.value]
  if (!videoEl || !video.duration) return
  
  const seekTime = getSeekTimeFromEvent(event, video)
  videoEl.currentTime = seekTime
  currentPlayTime.value = seekTime
  progress.value = (seekTime / video.duration) * 100
  
  // 如果视频暂停，点击进度条后开始播放
  if (videoEl.paused && !isTrialEnded.value) {
    userPaused.value = false  // 用户操作进度条，重置暂停状态
    videoEl.play().catch((err) => {
      if (err.name !== 'AbortError') {
        console.warn('Play after seek failed:', err.message)
      }
    })
  }
}

// 进度条触摸开始
const onProgressTouchStart = () => {
  isSeeking.value = true
}

// 进度条触摸移动
const onProgressTouchMove = (event, video) => {
  if (!isSeeking.value) return
  
  const videoEl = videoRefs.value[currentIndex.value]
  if (!videoEl || !video.duration) return
  
  const seekTime = getSeekTimeFromEvent(event, video)
  videoEl.currentTime = seekTime
  currentPlayTime.value = seekTime
  progress.value = (seekTime / video.duration) * 100
}

// 进度条触摸结束
const onProgressTouchEnd = () => {
  isSeeking.value = false
}

// 打开评论
const openComments = async (video) => {
  currentVideo.value = video
  showComments.value = true
  
  try {
    // 同时获取评论和公告
    const [commentsRes, announcementRes] = await Promise.all([
      api.get(`/comments/video/${video.id}`),
      api.get('/settings/comment-announcement').catch(() => null)
    ])
    comments.value = commentsRes.data?.items || commentsRes.data || []
    if (announcementRes) {
      announcement.value = announcementRes.data || announcementRes
    }
  } catch (error) {
    console.error('获取评论失败:', error)
  }
}

// 提交评论
const submitComment = async () => {
  if ((!commentText.value.trim() && !commentImage.value) || !currentVideo.value) return
  if (submittingComment.value) return
  
  // 检查VIP权限
  if (!isUserVip.value) {
    ElMessage.warning('请先开通VIP会员才能发表评论')
    return
  }
  
  submittingComment.value = true
  
  try {
    // 如果有图片，先上传图片
    let imageUrl = null
    if (commentImage.value) {
      const formData = new FormData()
      formData.append('file', commentImage.value)
      
      const uploadRes = await api.post('/comments/upload-image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      imageUrl = uploadRes.data?.url || uploadRes.url
    }
    
    const commentData = {
      content: commentText.value,
      video_id: currentVideo.value.id,
      image_url: imageUrl
    }
    
    // 如果是回复，添加 parent_id
    if (replyParentId.value) {
      commentData.parent_id = replyParentId.value
    }
    
    await api.post('/comments', commentData)
    ElMessage.success(replyParentId.value ? '回复成功' : '评论成功')
    commentText.value = ''
    commentImage.value = null
    commentImagePreview.value = ''
    showEmojiPicker.value = false
    
    // 清除回复状态
    cancelReply()
    
    currentVideo.value.comment_count++
    
    // 重新获取评论
    const res = await api.get(`/comments/video/${currentVideo.value.id}`)
    comments.value = res.data?.items || res.data || []
  } catch (error) {
    const errorMsg = error.response?.data?.detail || '评论失败'
    ElMessage.error(errorMsg)
  } finally {
    submittingComment.value = false
  }
}

// 设置回复目标
const setReplyTo = (comment, reply = null) => {
  if (reply) {
    // 回复某条回复，但 parent_id 仍然是顶级评论
    replyTo.value = reply
    replyParentId.value = comment.id
  } else {
    // 回复顶级评论
    replyTo.value = comment
    replyParentId.value = comment.id
  }
  // 聚焦输入框
  nextTick(() => {
    commentInputRef.value?.focus()
  })
}

// 取消回复
const cancelReply = () => {
  replyTo.value = null
  replyParentId.value = null
}

// 加载回复列表
const loadReplies = async (comment) => {
  try {
    const res = await api.get(`/comments/replies/${comment.id}`)
    comment.replies = res.data?.items || res.data || []
    comment.showReplies = true
  } catch (error) {
    console.error('加载回复失败:', error)
    ElMessage.error('加载回复失败')
  }
}

// 插入表情
const insertEmoji = (emoji) => {
  commentText.value += emoji
  showEmojiPicker.value = false
  commentInputRef.value?.focus()
}

// 选择图片
const handleImageSelect = (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  // 检查文件大小（最大5MB）
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.warning('图片大小不能超过5MB')
    return
  }
  
  // 检查文件类型
  if (!file.type.startsWith('image/')) {
    ElMessage.warning('请选择图片文件')
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

// 获取VIP等级图标（使用统一常量）
const getVipLevelIcon = (level) => {
  return VIP_LEVEL_ICONS[level] || ''
}

// 评论点赞
const likeComment = async (comment) => {
  try {
    const res = await api.post(`/comments/${comment.id}/like`)
    const data = res.data || res
    
    comment.is_liked = !comment.is_liked
    comment.like_count = data.like_count
  } catch (error) {
    console.error('点赞失败:', error)
    if (error.response?.status === 401) {
      ElMessage.warning('请先登录后再点赞')
    }
  }
}

// 格式化评论时间
const formatCommentTime = (date) => {
  if (!date) return ''
  const d = new Date(date)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const diffMinutes = Math.floor(diff / 60000)
  const diffHours = Math.floor(diff / 3600000)
  const diffDays = Math.floor(diff / 86400000)
  
  if (diffMinutes < 1) return '刚刚'
  if (diffMinutes < 60) return `${diffMinutes}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`
  
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 预览评论图片
const previewCommentImage = (url) => {
  window.open(url, '_blank')
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

// 视频时间更新
const onTimeUpdate = (index, e) => {
  if (index !== currentIndex.value) return
  if (isSeeking.value) return  // 拖动时不更新
  
  const videoEl = e.target
  if (!videoEl.duration) return
  
  // 更新进度条
  progress.value = (videoEl.currentTime / videoEl.duration) * 100
  currentPlayTime.value = videoEl.currentTime
  
  // 试看逻辑
  const currentVideo = videos.value[index]
  if (isTrialVideo(currentVideo) && !isTrialEnded.value) {
    const trialLimit = getTrialSeconds(currentVideo)
    trialRemaining.value = Math.max(0, Math.ceil(trialLimit - videoEl.currentTime))
    
    // 试看时间到
    if (videoEl.currentTime >= trialLimit) {
      isTrialEnded.value = true
      videoEl.pause()
      isPlaying.value = false
    }
  }
}

// 视频元数据加载完成
const onVideoLoaded = (index) => {
  // 只在首次加载时自动播放，且用户没有主动暂停，且还没有自动播放过
  if (index === currentIndex.value && !userPaused.value && !hasAutoPlayed.value) {
    hasAutoPlayed.value = true
    playCurrentVideo()
  }
}

// 视频可以播放
const onVideoCanPlay = (index) => {
  // 只在首次加载时自动播放，且用户没有主动暂停，且还没有自动播放过
  if (index === currentIndex.value && !isTrialEnded.value && !userPaused.value && !hasAutoPlayed.value) {
    const videoEl = videoRefs.value[index]
    if (videoEl && videoEl.paused) {
      hasAutoPlayed.value = true  // 标记已自动播放，后续不再自动播放
      playCurrentVideo()
    }
  }
}

// 返回
const goBack = () => {
  router.back()
}

// 跳转用户主页
const goToProfile = (userId) => {
  if (!userId) return
  router.push(`/user/member/${userId}`)
}

// 初始化
// 窗口大小变化处理函数
const handleResize = () => {
  slideHeight.value = window.innerHeight
  translateY.value = -currentIndex.value * slideHeight.value
}

// 用户金币余额缓存 (-1表示未获取)
const userCoinsBalance = ref(-1)

// 获取用户金币余额
const fetchCoinsBalance = async () => {
  try {
    const res = await api.get('/coins/balance', { signal: abortSignal })
    userCoinsBalance.value = res.data?.balance || res.balance || 0
  } catch (e) {
    if (e.name !== 'CanceledError' && e.name !== 'AbortError') {
      userCoinsBalance.value = -1  // 获取失败，标记为未知
    }
  }
}

onMounted(async () => {
  // 刷新用户数据（确保VIP状态最新）
  if (userStore.token) {
    await userStore.fetchUser()
    // 预加载金币余额
    fetchCoinsBalance()
  }
  
  // 计算滑动高度
  slideHeight.value = window.innerHeight
  
  // 如果有指定视频ID（从query或params获取），先获取该视频
  const targetVideoId = route.query.id || route.params.id
  if (targetVideoId) {
    try {
      // 先获取指定视频
      const res = await api.get(`/shorts/${targetVideoId}`, { signal: abortSignal })
      const targetVideo = res.data || res
      if (targetVideo && targetVideo.id) {
        // 将目标视频放在列表第一个位置
        videos.value = [targetVideo]
        currentIndex.value = 0
        trialRemaining.value = getTrialSeconds(targetVideo)
        userPaused.value = false
        hasAutoPlayed.value = false
        
        // 等待DOM更新后自动播放
        await nextTick()
        if (playTimerId) {
          timers.clearTimeout(playTimerId)
        }
        playTimerId = timers.setTimeout(() => {
          playTimerId = null
          if (!userPaused.value) {
            playCurrentVideo()
          }
        }, 200)
        
        // 然后在后台加载更多视频
        page.value = 1
        const moreRes = await api.get('/shorts', { params: { page: 1, limit: 10 }, signal: abortSignal })
        const moreData = moreRes.data || moreRes
        if (moreData.items && moreData.items.length > 0) {
          // 过滤掉已存在的目标视频，添加其他视频
          const otherVideos = moreData.items.filter(v => v.id !== parseInt(targetVideoId))
          videos.value = [targetVideo, ...otherVideos]
          hasMore.value = moreData.has_more
          page.value = 2
        }
        
        loading.value = false
        // 监听窗口大小变化（使用事件管理器）
        events.addEventListener(window, 'resize', handleResize)
        return
      }
    } catch (error) {
      if (error.name !== 'CanceledError' && error.name !== 'AbortError') {
        console.error('获取指定短视频失败:', error)
      }
    }
  }
  
  fetchVideos(true)
  
  // 监听窗口大小变化（使用事件管理器）
  events.addEventListener(window, 'resize', handleResize)
})

// 停止所有视频播放
const stopAllVideos = () => {
  try {
    // 清除播放定时器
    if (playTimerId) {
      timers.clearTimeout(playTimerId)
      playTimerId = null
    }
    
    // 暂停所有视频
    Object.values(videoRefs.value).forEach(video => {
      try {
        if (video) {
          video.pause()
          video.removeAttribute('src')
          video.load()  // 触发重新加载空源，完全停止
        }
      } catch (e) {
        console.warn('停止视频失败:', e)
      }
    })
    
    // 清空引用
    videoRefs.value = {}
  } catch (e) {
    console.warn('清理视频失败:', e)
  }
}

// 路由离开前暂停视频
onBeforeRouteLeave((to, from, next) => {
  stopAllVideos()
  next()
})

onBeforeUnmount(() => {
  stopAllVideos()
})

// 资源清理由 composables 自动处理
onUnmounted(() => {
  stopAllVideos()
})

// 监听标签切换
watch(activeTab, () => {
  fetchVideos(true)
})

// 监听路由变化，离开页面时停止视频
watch(() => route.path, (newPath, oldPath) => {
  if (oldPath && oldPath.includes('/short') && !newPath.includes('/short')) {
    stopAllVideos()
  }
})
</script>

<style lang="scss" scoped>
.short-video-page {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #000;
  overflow: hidden;
  z-index: 100;
}

// 顶部导航
.short-header {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  padding-top: calc(env(safe-area-inset-top) + 16px);
  z-index: 20;
  background: linear-gradient(to bottom, rgba(0,0,0,0.5), transparent);
  
  .back-btn {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    color: #fff;
    cursor: pointer;
  }
  
  .header-tabs {
    display: flex;
    gap: 24px;
    
    .tab-item {
      font-size: 15px;
      color: rgba(255,255,255,0.6);
      cursor: pointer;
      
      &.active {
        color: #fff;
        font-weight: 600;
      }
    }
  }
  
  .search-btn {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    
    svg {
      width: 22px;
      height: 22px;
      color: #fff;
    }
  }
}

// 视频滑动容器
.video-swiper {
  width: 100%;
  height: 100%;
  overflow: hidden;
  touch-action: pan-y;
}

.video-track {
  width: 100%;
}

.video-slide {
  width: 100%;
  height: 100vh;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
  
  .short-video {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  // 点击区域
  .tap-area {
    position: absolute;
    top: 60px; // 留出顶部导航空间
    left: 0;
    right: 80px; // 留出右侧操作栏空间
    bottom: 150px; // 留出底部信息空间
    z-index: 8; // 在 video 上方但不阻挡操作栏
    cursor: pointer;
    touch-action: manipulation; // 允许滑动，禁用双击缩放
    // 调试：取消注释下面这行可以看到点击区域
    // background: rgba(255, 0, 0, 0.1);
    // border: 2px solid red;
  }
}

// 持续显示的播放图标（视频暂停时）
.persistent-pause {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) translateX(3px);
  pointer-events: none;
  z-index: 15;
  
  svg {
    width: 80px;
    height: 80px;
    filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.4));
  }
}

// 双击爱心动画
.like-animation {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
  
  .heart {
    width: 120px;
    height: 120px;
    animation: like-pop 1s ease-out forwards;
    filter: drop-shadow(0 0 20px rgba(254, 44, 85, 0.6));
  }
}

@keyframes like-pop {
  0% {
    transform: scale(0);
    opacity: 1;
  }
  50% {
    transform: scale(1.2);
    opacity: 1;
  }
  100% {
    transform: scale(1);
    opacity: 0;
  }
}

// 右侧操作栏
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
      box-shadow: 0 2px 4px rgba(0,0,0,0.3);
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
      
      &.liked {
        animation: like-bounce 0.3s ease;
        
        svg {
          filter: drop-shadow(0 0 8px rgba(254, 44, 85, 0.5));
        }
      }
      
      &.favorited svg {
        filter: drop-shadow(0 0 8px rgba(255, 193, 7, 0.5));
      }
      
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
      
      &:active {
        transform: scale(0.9);
      }
    }
    
    .count {
      font-size: 11px;
      color: #fff;
      margin-top: 0;
      font-weight: 500;
      text-shadow: 0 1px 2px rgba(0,0,0,0.5);
      line-height: 1.2;
    }
  }
}

@keyframes like-bounce {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.2); }
}

// 底部信息
.video-info {
  position: absolute;
  left: 16px;
  right: 80px;
  bottom: 100px;
  z-index: 10;
  
  // VIP提示条
  .vip-tip-bar {
    display: inline-flex;
    align-items: center;
    background: linear-gradient(90deg, rgba(255, 215, 0, 0.85) 0%, rgba(255, 165, 0, 0.85) 100%);
    padding: 4px 10px;
    border-radius: 12px;
    margin-bottom: 8px;
    cursor: pointer;
    
    .vip-icon {
      margin-right: 3px;
      font-size: 11px;
    }
    
    .vip-text {
      font-size: 11px;
      font-weight: 500;
      color: #8B4513;
    }
    
    .vip-arrow {
      margin-left: 2px;
      font-size: 12px;
      font-weight: bold;
      color: #8B4513;
    }
    
    &:active {
      transform: scale(0.98);
    }
  }
  
  .author-name {
    font-size: 16px;
    font-weight: 500;
    color: #fff;
    margin-bottom: 15px;
  }
  
  .video-title {
    font-size: 14px;
    color: #fff;
    margin-bottom: 6px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  
  .video-desc {
    font-size: 13px;
    color: rgba(255,255,255,0.7);
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
}

// 进度条容器
.progress-bar-container {
  position: absolute;
  left: 12px;
  right: 12px;
  bottom: 20px;
  z-index: 15;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  
  .time-display {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.9);
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
    background: rgba(0, 0, 0, 0.3);
    padding: 2px 8px;
    border-radius: 10px;
  }
}

// 进度条
.progress-bar {
  position: relative;
  width: 100%;
  height: 24px;  // 扩大触摸区域
  cursor: pointer;
  display: flex;
  align-items: center;
  
  // 进度条背景轨道
  &::before {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    height: 4px;
    background: rgba(255, 255, 255, 0.3);
    border-radius: 2px;
  }
  
  .progress {
    position: absolute;
    left: 0;
    height: 4px;
    background: linear-gradient(90deg, #ff6b9d, #ff4757);
    border-radius: 2px;
    pointer-events: none;
  }
  
  .progress-thumb {
    position: absolute;
    top: 50%;
    transform: translate(-50%, -50%);
    width: 16px;
    height: 16px;
    background: #fff;
    border-radius: 50%;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
    pointer-events: none;
    transition: transform 0.15s ease;
  }
  
  &:active .progress-thumb {
    transform: translate(-50%, -50%) scale(1.3);
  }
}

// 试看倒计时
.trial-countdown {
  position: absolute;
  top: 100px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.7);
  padding: 8px 16px;
  border-radius: 20px;
  z-index: 15;
  
  .countdown-text {
    color: #ff6b6b;
    font-size: 14px;
    font-weight: 600;
  }
}

// 试看结束遮罩
.trial-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.92);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 15;
  backdrop-filter: blur(6px);
  
  .trial-content {
    text-align: center;
    padding: 20px 16px;
    width: 100%;
    max-width: 280px;
    
    h3 {
      font-size: 14px;
      font-weight: 600;
      color: #fff;
      margin-bottom: 14px;
    }
    
    .trial-subtitle {
      font-size: 14px;
      color: #fff;
      margin-bottom: 18px;
    }
    
    // 顶部两个并排按钮
    .trial-top-btns {
      display: flex;
      gap: 14px;
      margin-bottom: 12px;
      
      button {
        flex: 1;
        padding: 6px 20px;
        border-radius: 50px;
        border: none;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        white-space: nowrap;
        
        &:active {
          transform: scale(0.97);
        }
      }
      
      .share-btn {
        background: linear-gradient(90deg, #FF8C00 0%, #FFA500 100%);
        color: #fff;
      }
      
      .vip-btn {
        background: linear-gradient(90deg, #8B5CF6 0%, #A855F7 100%);
        color: #fff;
      }
    }
    
    // 分隔符
    .trial-divider {
      font-size: 11px;
      color: rgba(255, 255, 255, 0.4);
      margin-bottom: 12px;
    }
    
    // 金币购买按钮
    .coin-purchase-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 5px;
      width: 100%;
      padding: 8px 16px;
      border-radius: 20px;
      border: none;
      background: rgba(50, 50, 50, 0.95);
      color: #fff;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
      
      .coin-icon {
        font-size: 14px;
      }
      
      .arrow {
        font-size: 16px;
        margin-left: 3px;
        color: rgba(255, 255, 255, 0.6);
      }
      
      &:active {
        transform: scale(0.97);
      }
    }
  }
}

// 加载状态
.loading-indicator {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 20;
  
  .spinner {
    display: block;
    width: 40px;
    height: 40px;
    border: 3px solid rgba(255,255,255,0.2);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

// 空状态
.empty-state {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  
  img {
    width: 150px;
    margin-bottom: 16px;
  }
  
  p {
    color: rgba(255,255,255,0.5);
    font-size: 14px;
  }
}

// 评论抽屉
.comments-drawer {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  z-index: 200;
  display: flex;
  align-items: flex-end;
  
  .drawer-content {
    width: 100%;
    height: 70vh;
    min-height: 70vh;
    background: #0a0a0a;
    border-radius: 16px 16px 0 0;
    display: flex;
    flex-direction: column;
  }
  
  .drawer-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    
    .comment-count {
      font-size: 15px;
      color: #fff;
    }
    
    .close-btn {
      font-size: 24px;
      color: rgba(255,255,255,0.6);
      cursor: pointer;
    }
  }
  
  .comments-list {
    flex: 1;
    overflow-y: auto;
    padding: 16px 20px;
    
    .comment-item {
      display: flex;
      gap: 10px;
      padding: 16px 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      
      .comment-avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        object-fit: cover;
        flex-shrink: 0;
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
        }
        
        @keyframes vip-badge-glow {
          0%, 100% {
            filter: drop-shadow(0 0 3px rgba(255, 215, 0, 0.5));
          }
          50% {
            filter: drop-shadow(0 0 8px rgba(255, 215, 0, 0.8));
          }
        }
        
        .comment-text {
          font-size: 14px;
          color: rgba(255, 255, 255, 0.9);
          line-height: 1.6;
          margin: 0 0 10px;
          word-break: break-word;
        }
        
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
        }
        
        .comment-meta {
          display: flex;
          gap: 20px;
          align-items: center;
          
          .time {
            font-size: 12px;
            color: rgba(255, 255, 255, 0.35);
          }
          
          .reply-btn {
            font-size: 12px;
            color: rgba(255, 255, 255, 0.5);
            cursor: pointer;
            
            &:hover {
              color: #fe2c55;
            }
          }
          
          .like-btn {
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
        }
        
        // 回复列表
        .replies-section {
          margin-top: 10px;
          padding-left: 0;
          
          .view-replies-btn, .hide-replies-btn {
            font-size: 12px;
            color: #fe2c55;
            cursor: pointer;
            padding: 5px 0;
          }
          
          .replies-list {
            .reply-item {
              display: flex;
              gap: 10px;
              padding: 10px 0;
              border-bottom: 1px solid rgba(255, 255, 255, 0.05);
              
              &:last-of-type {
                border-bottom: none;
              }
              
              .reply-avatar {
                width: 28px;
                height: 28px;
                border-radius: 50%;
                object-fit: cover;
                flex-shrink: 0;
                
                &.clickable {
                  cursor: pointer;
                }
              }
              
              .reply-body {
                flex: 1;
                min-width: 0;
                
                .reply-user {
                  display: flex;
                  align-items: center;
                  gap: 4px;
                  margin-bottom: 4px;
                  
                  .username {
                    font-size: 12px;
                    color: rgba(255, 255, 255, 0.6);
                    
                    &.clickable {
                      cursor: pointer;
                    }
                  }
                  
                  .vip-badge-xs {
                    height: 12px;
                    width: auto;
                  }
                }
                
                .reply-text {
                  font-size: 13px;
                  color: rgba(255, 255, 255, 0.9);
                  line-height: 1.5;
                  word-break: break-word;
                }
                
                .reply-image {
                  margin-top: 8px;
                  
                  img {
                    max-width: 120px;
                    max-height: 120px;
                    border-radius: 6px;
                    cursor: pointer;
                  }
                }
                
                .reply-meta {
                  display: flex;
                  gap: 15px;
                  align-items: center;
                  margin-top: 6px;
                  
                  .time {
                    font-size: 11px;
                    color: rgba(255, 255, 255, 0.3);
                  }
                  
                  .reply-btn {
                    font-size: 11px;
                    color: rgba(255, 255, 255, 0.5);
                    cursor: pointer;
                    
                    &:hover {
                      color: #fe2c55;
                    }
                  }
                  
                  .like-btn {
                    font-size: 11px;
                    color: rgba(255, 255, 255, 0.4);
                    cursor: pointer;
                    
                    &.liked {
                      color: #ff6b6b;
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    
    .empty-comments {
      text-align: center;
      padding: 40px;
      color: rgba(255,255,255,0.5);
    }
    
    // 官方公告样式
    .official-announcement {
      .comment-user {
        .official-name {
          font-size: 13px;
          font-weight: 600;
          background: linear-gradient(90deg, #a855f7, #c084fc, #e879f9);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        
        .supreme-vip-icon {
          height: 18px;
          width: auto;
          margin-left: 2px;
          vertical-align: middle;
          filter: drop-shadow(0 0 6px rgba(168, 85, 247, 0.8));
          animation: supreme-glow 1.5s ease-in-out infinite;
        }
      }
      
      .official-text {
        font-size: 14px;
        line-height: 1.8;
        color: #c084fc;
      }
    }
    
    @keyframes supreme-glow {
      0%, 100% {
        filter: drop-shadow(0 0 4px rgba(168, 85, 247, 0.6)) drop-shadow(0 0 8px rgba(59, 130, 246, 0.4));
      }
      50% {
        filter: drop-shadow(0 0 10px rgba(168, 85, 247, 1)) drop-shadow(0 0 20px rgba(59, 130, 246, 0.8));
      }
    }
  }
  
  // 评论输入框
  .comment-input-bar {
    background: linear-gradient(180deg, rgba(10, 10, 10, 0.95) 0%, rgba(5, 5, 5, 1) 100%);
    padding: 12px 16px;
    padding-bottom: calc(12px + env(safe-area-inset-bottom, 0px));
    border-top: 1px solid rgba(255, 255, 255, 0.06);
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
      .reply-hint {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 12px;
        margin-bottom: 8px;
        background: rgba(254, 44, 85, 0.1);
        border-radius: 8px;
        font-size: 12px;
        color: #fe2c55;
        
        .cancel-reply {
          width: 18px;
          height: 18px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 50%;
          cursor: pointer;
          font-size: 14px;
          
          &:hover {
            background: rgba(255, 255, 255, 0.2);
          }
        }
      }
      
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
          }
        }
      }
      
      // 表情选择器
      .emoji-picker {
        margin-top: 12px;
        background: rgba(30, 30, 50, 0.95);
        border-radius: 12px;
        padding: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        
        .emoji-grid {
          display: grid;
          grid-template-columns: repeat(10, 1fr);
          gap: 8px;
          max-height: 150px;
          overflow-y: auto;
          
          .emoji-item {
            font-size: 20px;
            cursor: pointer;
            text-align: center;
            padding: 4px;
            border-radius: 6px;
            transition: all 0.2s;
            
            &:hover {
              background: rgba(255, 255, 255, 0.1);
              transform: scale(1.2);
            }
          }
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
    border-radius: 14px;
    width: 100%;
    max-width: 300px;
    padding: 18px 16px;
    position: relative;
    
    .share-modal-close {
      position: absolute;
      top: 8px;
      right: 8px;
      width: 24px;
      height: 24px;
      border: none;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 50%;
      font-size: 16px;
      color: rgba(255, 255, 255, 0.7);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      line-height: 1;
      
      &:hover {
        background: rgba(255, 255, 255, 0.2);
      }
    }
    
    .share-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 10px;
      
      .share-logo {
        width: 32px;
        height: 32px;
        border-radius: 6px;
        object-fit: cover;
      }
      
      .share-title-info {
        .share-site-name {
          font-size: 14px;
          font-weight: 600;
          color: #fff;
          margin: 0 0 2px 0;
        }
        
        .share-site-desc {
          font-size: 11px;
          color: rgba(255, 255, 255, 0.6);
          margin: 0;
        }
      }
    }
    
    .share-promo-image {
      width: 100%;
      border-radius: 10px;
      overflow: hidden;
      margin-bottom: 12px;
      
      img {
        width: 100%;
        height: 380px;
        object-fit: cover;
        display: block;
      }
    }
    
    .share-qr-section {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 14px;
      
      .share-qrcode {
        flex-shrink: 0;
        background: #fff;
        padding: 4px;
        border-radius: 6px;
        
        img {
          width: 70px;
          height: 70px;
          border-radius: 4px;
          display: block;
        }
      }
      
      .share-invite-info {
        .invite-code {
          font-size: 13px;
          color: #fff;
          margin-bottom: 6px;
          
          span {
            font-weight: 700;
            color: #a855f7;
            margin-left: 4px;
          }
        }
        
        .official-url {
          font-size: 11px;
          color: rgba(255, 255, 255, 0.6);
          word-break: break-all;
        }
      }
    }
    
    .share-actions {
      display: flex;
      gap: 10px;
      
      .copy-link-btn, .save-image-btn {
        flex: 1;
        padding: 10px 12px;
        border-radius: 50px;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        transition: opacity 0.2s;
        
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
</style>




