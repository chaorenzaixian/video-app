<template>
  <div class="video-player-page">
    <!-- 返回按钮 -->
    <div class="back-btn" @click="goBack">
      <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
    </div>

    <!-- 视频播放器区域 -->
    <div class="player-container">
      <!-- 前贴广告 -->
      <PreRollAd
        v-if="showPreRollAd && preRollAd"
        :ad="preRollAd"
        :is-vip="isVip"
        @skip="onAdSkip"
        @click="onAdClick"
      />

      <!-- ArtPlayer 容器 -->
      <div 
        ref="artPlayerRef" 
        class="artplayer-container"
        :class="{ 'hidden-by-ad': showPreRollAd }"
      ></div>

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

      <!-- 试看结束遮罩 -->
      <TrialEndedOverlay
        v-if="isTrialEnded && !hasPurchased"
        :video="video"
        :needs-purchase="needsPurchase"
        @share="handleShare"
        @purchase="quickPurchaseVideo"
      />
    </div>

    <!-- 分享弹窗 -->
    <ShareModal
      v-model:visible="showShareModal"
      :video="video"
      :invite-code="userInviteCode"
    />

    <!-- 会员推广条 -->
    <VipPromoBar
      :is-vip="isVip"
      :vip-level="userVipLevel"
      :expire-date="userVipExpireDate"
    />

    <!-- 标签页导航 -->
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

    <!-- 简介内容区 -->
    <VideoIntro
      v-show="activeTab === 'intro'"
      :video="video"
      :is-vip="isVip"
      :is-liked="isLiked"
      :is-favorited="isFavorited"
      :is-uploader-followed="isUploaderFollowed"
      :recommend-videos="recommendVideos"
      :icon-ads="iconAds"
      @like="toggleLike"
      @favorite="toggleFavorite"
      @follow="toggleUploaderFollow"
      @share="shareVideo"
      @download="downloadVideo"
      @video-click="handleVideoClick"
    />

    <!-- 评论内容区 -->
    <CommentSection
      v-show="activeTab === 'comments'"
      :video-id="video.id"
      :is-vip="isVip"
      :comments="comments"
      :comment-total="commentTotal"
      :has-more="hasMoreComments"
      :loading="loadingComments"
      @load-more="loadMoreComments"
      @submit="submitComment"
      @like="likeComment"
      @reply="startReply"
      @delete="deleteComment"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

// 子组件
import PreRollAd from './components/PreRollAd.vue'
import TrialEndedOverlay from './components/TrialEndedOverlay.vue'
import ShareModal from './components/ShareModal.vue'
import VipPromoBar from './components/VipPromoBar.vue'
import VideoIntro from './components/VideoIntro.vue'
import CommentSection from './components/CommentSection.vue'

// Composables
import { useVideoPlayer } from './composables/useVideoPlayer'
import { useComments } from './composables/useComments'
import { usePreRollAd } from './composables/usePreRollAd'
import { usePurchase } from './composables/usePurchase'

// Utils
import api from '@/utils/api'
import { useAbortController } from '@/composables/useAbortController'
import { useTimers } from '@/composables/useCleanup'

const route = useRoute()
const router = useRouter()

// 请求取消控制器
const { signal: abortSignal } = useAbortController()
const timers = useTimers()

// ========== 视频播放器 ==========
const {
  artPlayerRef,
  isPlaying,
  currentPlayTime,
  initArtPlayer,
  play,
  pause,
  destroy: destroyPlayer
} = useVideoPlayer()

// ========== 评论 ==========
const {
  comments,
  commentTotal,
  hasMoreComments,
  loadingComments,
  loadComments,
  loadMoreComments,
  submitComment,
  likeComment,
  deleteComment,
  startReply
} = useComments()

// ========== 前贴广告 ==========
const {
  preRollAd,
  showPreRollAd,
  fetchPreRollAd,
  startPreRollAd,
  skipAd
} = usePreRollAd()

// ========== 购买 ==========
const {
  hasPurchased,
  needsPurchase,
  isTrialEnded,
  isVipFree,
  checkPurchaseStatus,
  quickPurchaseVideo
} = usePurchase()

// ========== 状态 ==========
const video = ref({})
const recommendVideos = ref([])
const iconAds = ref([])
const activeTab = ref('intro')
const currentLine = ref(1)
const showLineSelect = ref(false)
const showShareModal = ref(false)

// 用户状态
const isVip = ref(false)
const userVipLevel = ref(0)
const userVipExpireDate = ref(null)
const userInviteCode = ref('')

// 交互状态
const isLiked = ref(false)
const isFavorited = ref(false)
const isUploaderFollowed = ref(false)

// ========== 计算属性 ==========
const videoId = computed(() => route.params.id)

// ========== 方法 ==========
const goBack = () => {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/')
  }
}

const fetchVideo = async () => {
  try {
    const res = await api.get(`/videos/${videoId.value}`, { signal: abortSignal })
    video.value = res.data || res
    
    // 初始化播放器
    initArtPlayer(video.value, {
      onPlay: () => { isPlaying.value = true },
      onPause: () => { isPlaying.value = false },
      onTimeUpdate: (time) => {
        currentPlayTime.value = time
        checkTrialEnd(time)
      }
    })
    
    // 检查购买状态
    await checkPurchaseStatus(video.value)
    
    // 加载评论
    loadComments(videoId.value)
    
    // 加载推荐视频
    fetchRecommendations()
    
    // 非VIP加载广告
    if (!isVip.value) {
      fetchPreRollAd()
    }
  } catch (error) {
    console.error('Failed to fetch video:', error)
  }
}

const fetchUserInfo = async () => {
  try {
    const res = await api.get('/users/me', { signal: abortSignal })
    const user = res.data || res
    isVip.value = user.is_vip || false
    userVipLevel.value = user.vip_level || 0
    userVipExpireDate.value = user.vip_expire_date
    userInviteCode.value = user.invite_code || ''
  } catch (error) {
    // 未登录
    isVip.value = false
  }
}

const fetchRecommendations = async () => {
  try {
    const res = await api.get(`/videos/${videoId.value}/recommendations`, {
      params: { limit: 10 },
      signal: abortSignal
    })
    recommendVideos.value = res.data || res || []
  } catch (error) {
    console.log('Failed to fetch recommendations')
  }
}

const checkTrialEnd = (time) => {
  if (!needsPurchase.value || hasPurchased.value || isVipFree.value) return
  
  const trialLimit = video.value.free_preview_seconds || 30
  if (time >= trialLimit) {
    isTrialEnded.value = true
    pause()
  }
}

const toggleLike = async () => {
  try {
    await api.post(`/videos/${videoId.value}/like`)
    isLiked.value = !isLiked.value
    video.value.like_count += isLiked.value ? 1 : -1
  } catch (error) {
    console.error('Failed to toggle like')
  }
}

const toggleFavorite = async () => {
  try {
    await api.post(`/videos/${videoId.value}/favorite`)
    isFavorited.value = !isFavorited.value
    video.value.favorite_count += isFavorited.value ? 1 : -1
  } catch (error) {
    console.error('Failed to toggle favorite')
  }
}

const toggleUploaderFollow = async () => {
  try {
    await api.post(`/users/${video.value.uploader_id}/follow`)
    isUploaderFollowed.value = !isUploaderFollowed.value
  } catch (error) {
    console.error('Failed to toggle follow')
  }
}

const shareVideo = () => {
  showShareModal.value = true
}

const handleShare = () => {
  showShareModal.value = true
}

const downloadVideo = () => {
  if (!isVip.value) {
    router.push('/user/vip')
    return
  }
  // 下载逻辑
  window.open(video.value.original_url || video.value.hls_url, '_blank')
}

const handleVideoClick = (rec) => {
  router.push(`/user/video/${rec.id}`)
}

const onAdSkip = () => {
  skipAd()
  play()
}

const onAdClick = () => {
  // 广告点击统计
  if (preRollAd.value?.id) {
    api.post(`/ads/${preRollAd.value.id}/click`).catch(() => {})
  }
}

// ========== 生命周期 ==========
onMounted(async () => {
  await fetchUserInfo()
  await fetchVideo()
})

onUnmounted(() => {
  destroyPlayer()
})

// 监听路由变化
watch(videoId, async (newId, oldId) => {
  if (newId && newId !== oldId) {
    destroyPlayer()
    await fetchVideo()
  }
})
</script>

<style scoped>
.video-player-page {
  min-height: 100vh;
  background: #0a0a0a;
  padding-bottom: 60px;
}

.back-btn {
  position: fixed;
  top: 10px;
  left: 10px;
  z-index: 100;
  width: 36px;
  height: 36px;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.back-icon {
  width: 20px;
  height: 20px;
}

.player-container {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #000;
}

.artplayer-container {
  width: 100%;
  height: 100%;
}

.artplayer-container.hidden-by-ad {
  visibility: hidden;
}

.access-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 10;
}

.vip-free-badge,
.purchased-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: linear-gradient(135deg, #ffd700, #ff8c00);
  color: #000;
  font-size: 12px;
  font-weight: 600;
  border-radius: 4px;
}

.purchased-badge {
  background: linear-gradient(135deg, #4caf50, #2e7d32);
  color: #fff;
}

.content-tabs {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: #111;
  border-bottom: 1px solid #222;
}

.tab-item {
  padding: 8px 16px;
  color: #888;
  font-size: 14px;
  cursor: pointer;
  transition: color 0.2s;
}

.tab-item.active {
  color: #fff;
  font-weight: 600;
}

.tab-right {
  margin-left: auto;
  color: #ec4899;
  font-size: 13px;
  cursor: pointer;
}

.line-icon {
  margin-right: 4px;
}
</style>
