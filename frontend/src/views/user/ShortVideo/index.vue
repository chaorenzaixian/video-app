<template>
  <div class="short-video-page">
    <!-- 顶部导航 -->
    <header class="short-header">
      <div class="back-btn" @click="goBack"><img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" /></div>
      <div class="header-tabs">
        <span :class="['tab-item', { active: activeTab === 'recommend' }]" @click="activeTab = 'recommend'">推荐</span>
        <span :class="['tab-item', { active: activeTab === 'follow' }]" @click="activeTab = 'follow'">关注</span>
      </div>
      <div class="search-btn" @click="$router.push('/user/search')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
        </svg>
      </div>
    </header>

    <!-- 视频滑动容器 -->
    <div class="video-swiper" ref="swiperRef" @touchstart="onTouchStart" @touchmove="onTouchMove" @touchend="onTouchEnd">
      <div class="video-track" :style="{ transform: `translateY(${translateY}px)`, transition: isAnimating ? 'transform 0.3s ease' : 'none' }">
        <VideoSlide
          v-for="(video, index) in videos"
          :key="video.id"
          :ref="el => setSlideRef(index, el)"
          :video="video"
          :is-current="currentIndex === index"
          :is-playing="currentIndex === index && isPlaying"
          :is-vip="isUserVip"
          :is-trial-ended="currentIndex === index && isTrialEnded"
          :trial-remaining="trialRemaining"
          :purchasing="purchasing"
          :show-like-animation="showLikeAnimation && likeAnimationIndex === index"
          @like="handleLike(index)"
          @comment="openComments(video)"
          @favorite="handleFavorite(index)"
          @share="handleShare(video)"
          @download="handleDownload(video)"
          @follow="handleFollow(video)"
          @go-profile="goToProfile"
          @go-vip="$router.push('/user/vip')"
          @purchase="handlePurchase(video)"
          @tap="togglePlay(index)"
          @double-tap="handleDoubleTap(index)"
          @time-update="onTimeUpdate(index, $event)"
        />
      </div>
    </div>

    <!-- 加载状态 -->
    <div class="loading-indicator" v-if="loading"><span class="spinner"></span></div>

    <!-- 空状态 -->
    <div class="empty-state" v-if="!loading && videos.length === 0">
      <img src="/images/backgrounds/no_data.webp" alt="" />
      <p>暂无短视频内容</p>
    </div>

    <!-- 评论弹窗 -->
    <CommentsDrawer
      ref="commentsDrawerRef"
      :visible="showComments"
      :video="currentVideo"
      :is-vip="isUserVip"
      @close="showComments = false"
      @go-profile="goToProfile"
      @go-vip="$router.push('/user/vip')"
      @comment-added="currentVideo && currentVideo.comment_count++"
    />

    <!-- 分享弹窗 -->
    <ShareModal
      :visible="showShareModal"
      :video="shareVideo"
      :invite-code="userInviteCode"
      @close="showShareModal = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'
import { useUserStore } from '@/stores/user'
import { useAbortController } from '@/composables/useAbortController'
import { useTimers, useEventListeners } from '@/composables/useCleanup'
import VideoSlide from './components/VideoSlide.vue'
import CommentsDrawer from './components/CommentsDrawer.vue'
import ShareModal from './components/ShareModal.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const { signal: abortSignal } = useAbortController()
const timers = useTimers()
const events = useEventListeners()

// VIP状态
const isUserVip = computed(() => userStore.isVip || userStore.user?.is_vip === true || (userStore.user?.vip_level && userStore.user.vip_level > 0))

// 数据状态
const videos = ref([])
const currentIndex = ref(0)
const loading = ref(false)
const page = ref(1)
const hasMore = ref(true)
const activeTab = ref('recommend')

// 播放状态
const isPlaying = ref(false)
const userPaused = ref(false)
const hasAutoPlayed = ref(false)
const isTrialEnded = ref(false)
const trialRemaining = ref(15)
const slideRefs = ref({})
let playTimerId = null
let lastPauseTime = 0

// 滑动状态
const swiperRef = ref(null)
const translateY = ref(0)
const startY = ref(0)
const isDragging = ref(false)
const isAnimating = ref(false)
const slideHeight = ref(0)

// 双击点赞
const showLikeAnimation = ref(false)
const likeAnimationIndex = ref(-1)

// 评论
const showComments = ref(false)
const currentVideo = ref(null)
const commentsDrawerRef = ref(null)

// 分享
const showShareModal = ref(false)
const shareVideo = ref(null)
const userInviteCode = ref('3AUUHR')

// 购买
const purchasing = ref(false)
const userCoinsBalance = ref(-1)

// 操作锁
const actionLocks = ref({})

// 设置slide引用
const setSlideRef = (index, el) => { if (el) slideRefs.value[index] = el }

// 获取当前视频元素
const getCurrentVideoEl = () => slideRefs.value[currentIndex.value]?.getVideoElement?.()

// 检查是否是试看视频
const isTrialVideo = (video) => {
  if (!video) return false
  if (video.is_purchased) return false
  return (video.trial_seconds && video.trial_seconds > 0)
}

const getTrialSeconds = (video) => {
  if (!video || !isTrialVideo(video)) return 0
  return video.trial_seconds || 15
}

// 获取视频列表
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
    
    const res = await api.get('/shorts', { params: { page: page.value, limit: 10 }, signal: abortSignal })
    const data = res.data || res
    
    if (data.items?.length > 0) {
      videos.value = reset ? data.items : [...videos.value, ...data.items]
      hasMore.value = data.has_more
      page.value++
      
      if (reset && data.items.length > 0) {
        trialRemaining.value = getTrialSeconds(data.items[0])
        userPaused.value = false
        hasAutoPlayed.value = false
        await nextTick()
        schedulePlay()
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

// 延迟播放
const schedulePlay = () => {
  if (playTimerId) timers.clearTimeout(playTimerId)
  playTimerId = timers.setTimeout(() => {
    playTimerId = null
    if (!userPaused.value) playCurrentVideo()
  }, 200)
}

// 播放当前视频
const playCurrentVideo = () => {
  const timeSincePause = Date.now() - lastPauseTime
  if (lastPauseTime > 0 && timeSincePause < 500) return
  
  // 暂停其他视频
  Object.entries(slideRefs.value).forEach(([idx, slide]) => {
    if (parseInt(idx) !== currentIndex.value) slide?.pause?.()
  })
  
  const currentSlide = slideRefs.value[currentIndex.value]
  if (currentSlide && !userPaused.value) {
    const videoEl = currentSlide.getVideoElement?.()
    if (videoEl) {
      videoEl.play().catch(err => {
        if (err.name === 'NotAllowedError') {
          videoEl.muted = true
          videoEl.play().catch(() => {})
        }
      })
    }
  }
}

// 切换播放/暂停
const togglePlay = (index) => {
  if (index !== currentIndex.value) return
  const video = videos.value[index]
  if (isTrialEnded.value && isTrialVideo(video)) return
  
  const videoEl = getCurrentVideoEl()
  if (!videoEl) return
  
  if (videoEl.paused) {
    Object.entries(slideRefs.value).forEach(([idx, slide]) => {
      if (parseInt(idx) !== index) slide?.pause?.()
    })
    hasAutoPlayed.value = true
    userPaused.value = false
    lastPauseTime = 0
    videoEl.play().catch(err => {
      if (err.name === 'NotAllowedError') {
        videoEl.muted = true
        videoEl.play().catch(() => {})
      }
    })
  } else {
    userPaused.value = true
    lastPauseTime = Date.now()
    if (playTimerId) { timers.clearTimeout(playTimerId); playTimerId = null }
    videoEl.pause()
  }
}

// 双击点赞
const handleDoubleTap = (index) => {
  const video = videos.value[index]
  if (!video.is_liked) handleLike(index)
  likeAnimationIndex.value = index
  showLikeAnimation.value = true
  timers.setTimeout(() => { showLikeAnimation.value = false }, 1000)
}

// 时间更新
const onTimeUpdate = (index, { currentTime, duration }) => {
  if (index !== currentIndex.value) return
  const video = videos.value[index]
  
  if (isTrialVideo(video) && !isTrialEnded.value) {
    const trialLimit = getTrialSeconds(video)
    trialRemaining.value = Math.max(0, Math.ceil(trialLimit - currentTime))
    
    if (currentTime >= trialLimit) {
      isTrialEnded.value = true
      getCurrentVideoEl()?.pause()
      isPlaying.value = false
    }
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
      goToSlide(currentIndex.value + 1)
    } else if (deltaY > 0 && currentIndex.value > 0) {
      goToSlide(currentIndex.value - 1)
    } else {
      goToSlide(currentIndex.value)
    }
  } else {
    goToSlide(currentIndex.value)
  }
  
  if (currentIndex.value >= videos.value.length - 3) fetchVideos()
}

// 跳转到指定视频
const goToSlide = (index) => {
  const isChanging = index !== currentIndex.value
  isAnimating.value = true
  translateY.value = -index * slideHeight.value
  
  if (isChanging) {
    Object.entries(slideRefs.value).forEach(([idx, slide]) => {
      if (parseInt(idx) !== index) slide?.pause?.()
    })
    
    currentIndex.value = index
    userPaused.value = false
    hasAutoPlayed.value = false
    isTrialEnded.value = false
    const newVideo = videos.value[index]
    trialRemaining.value = getTrialSeconds(newVideo)
    
    const newSlide = slideRefs.value[index]
    newSlide?.seek?.(0)
    
    if (playTimerId) { timers.clearTimeout(playTimerId); playTimerId = null }
    playTimerId = timers.setTimeout(() => {
      isAnimating.value = false
      playTimerId = null
      if (!userPaused.value) playCurrentVideo()
    }, 300)
  } else {
    timers.setTimeout(() => { isAnimating.value = false }, 300)
  }
}
</script>

// 点赞
const handleLike = async (index) => {
  const video = videos.value[index]
  if (!video) return
  
  const lockKey = `like_${video.id}`
  if (actionLocks.value[lockKey]) return
  actionLocks.value[lockKey] = true
  
  const wasLiked = video.is_liked
  const oldCount = video.like_count || 0
  video.is_liked = !wasLiked
  video.like_count = wasLiked ? Math.max(0, oldCount - 1) : oldCount + 1
  
  try {
    const res = await api.post(`/shorts/${video.id}/like`)
    const data = res.data || res
    video.is_liked = data.liked
    video.like_count = data.like_count
  } catch (error) {
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
  
  const wasFavorited = video.is_favorited
  const oldCount = video.favorite_count || 0
  video.is_favorited = !wasFavorited
  video.favorite_count = wasFavorited ? Math.max(0, oldCount - 1) : oldCount + 1
  
  try {
    const res = await api.post(`/shorts/${video.id}/favorite`)
    const data = res.data || res
    video.is_favorited = data.favorited
    video.favorite_count = data.favorite_count
    ElMessage.success(data.favorited ? '收藏成功' : '已取消收藏')
  } catch (error) {
    video.is_favorited = wasFavorited
    video.favorite_count = oldCount
    ElMessage.error('操作失败')
  } finally {
    actionLocks.value[lockKey] = false
  }
}

// 关注
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
      video.is_followed = true
    } else {
      ElMessage.error(error.response?.data?.detail || '关注失败')
    }
  } finally {
    timers.setTimeout(() => { actionLocks.value[lockKey] = false }, 500)
  }
}

// 分享
const handleShare = (video) => {
  shareVideo.value = video
  showShareModal.value = true
}

// 下载
const handleDownload = async (video) => {
  if (!isUserVip.value) {
    ElMessage.warning('下载功能仅限VIP会员使用')
    router.push('/user/vip')
    return
  }
  
  try {
    const infoRes = await api.get(`/shorts/${video.id}/download-info`, { signal: abortSignal })
    const info = infoRes.data || infoRes
    
    if (!info.can_download) {
      ElMessage.warning(info.message || '无法下载此视频')
      return
    }
    
    ElMessage.info(`正在下载: ${info.title} (${info.file_size_mb || 0}MB)`)
    
    // 保存下载记录
    const saved = localStorage.getItem('video_downloads')
    const downloads = saved ? JSON.parse(saved) : []
    const record = {
      id: `short_${video.id}_${Date.now()}`,
      videoId: video.id,
      title: video.title,
      thumbnail: video.cover_url,
      duration: video.duration,
      type: 'short',
      status: 'completed',
      downloadTime: Date.now()
    }
    const existIndex = downloads.findIndex(d => d.videoId === record.videoId && d.type === record.type)
    if (existIndex > -1) downloads[existIndex] = record
    else downloads.unshift(record)
    if (downloads.length > 100) downloads.pop()
    localStorage.setItem('video_downloads', JSON.stringify(downloads))
    
    const link = document.createElement('a')
    link.href = `/api/v1/shorts/${video.id}/download`
    link.download = `${info.title}.mp4`
    link.style.display = 'none'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('下载已开始')
  } catch (error) {
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

// 购买
const handlePurchase = async (video) => {
  if (purchasing.value) return
  if (video.is_purchased) {
    isTrialEnded.value = false
    playCurrentVideo()
    return
  }
  
  const coinPrice = video.coin_price || 20
  if (userCoinsBalance.value >= 0 && userCoinsBalance.value < coinPrice) {
    ElMessage.warning('金币不足，请先充值')
    router.push('/user/coins')
    return
  }
  
  purchasing.value = true
  try {
    await api.post(`/coins/purchase/video/${video.id}`)
    ElMessage.success('购买成功！')
    video.is_purchased = true
    isTrialEnded.value = false
    trialRemaining.value = getTrialSeconds(video)
    userCoinsBalance.value = Math.max(0, userCoinsBalance.value - coinPrice)
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
      userCoinsBalance.value = 0
      ElMessage.warning('金币不足，请先充值')
      router.push('/user/coins')
    } else {
      ElMessage.error(detail || '购买失败，请重试')
    }
  } finally {
    purchasing.value = false
  }
}

// 打开评论
const openComments = async (video) => {
  currentVideo.value = video
  showComments.value = true
  await nextTick()
  commentsDrawerRef.value?.loadComments()
}

// 导航
const goBack = () => router.back()
const goToProfile = (userId) => { if (userId) router.push(`/user/member/${userId}`) }

// 停止所有视频
const stopAllVideos = () => {
  if (playTimerId) { timers.clearTimeout(playTimerId); playTimerId = null }
  Object.values(slideRefs.value).forEach(slide => {
    try {
      const videoEl = slide?.getVideoElement?.()
      if (videoEl) {
        videoEl.pause()
        videoEl.removeAttribute('src')
        videoEl.load()
      }
    } catch (e) {}
  })
  slideRefs.value = {}
}

// 窗口大小变化
const handleResize = () => {
  slideHeight.value = window.innerHeight
  translateY.value = -currentIndex.value * slideHeight.value
}

// 获取金币余额
const fetchCoinsBalance = async () => {
  try {
    const res = await api.get('/coins/balance', { signal: abortSignal })
    userCoinsBalance.value = res.data?.balance || res.balance || 0
  } catch (e) {
    if (e.name !== 'CanceledError' && e.name !== 'AbortError') userCoinsBalance.value = -1
  }
}

// 生命周期
onMounted(async () => {
  if (userStore.token) {
    await userStore.fetchUser()
    fetchCoinsBalance()
  }
  
  slideHeight.value = window.innerHeight
  
  const targetVideoId = route.query.id || route.params.id
  if (targetVideoId) {
    try {
      const res = await api.get(`/shorts/${targetVideoId}`, { signal: abortSignal })
      const targetVideo = res.data || res
      if (targetVideo?.id) {
        videos.value = [targetVideo]
        currentIndex.value = 0
        trialRemaining.value = getTrialSeconds(targetVideo)
        userPaused.value = false
        hasAutoPlayed.value = false
        await nextTick()
        schedulePlay()
        
        page.value = 1
        const moreRes = await api.get('/shorts', { params: { page: 1, limit: 10 }, signal: abortSignal })
        const moreData = moreRes.data || moreRes
        if (moreData.items?.length > 0) {
          const otherVideos = moreData.items.filter(v => v.id !== parseInt(targetVideoId))
          videos.value = [targetVideo, ...otherVideos]
          hasMore.value = moreData.has_more
          page.value = 2
        }
        
        loading.value = false
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
  events.addEventListener(window, 'resize', handleResize)
})

onBeforeRouteLeave((to, from, next) => { stopAllVideos(); next() })
onBeforeUnmount(() => stopAllVideos())
onUnmounted(() => stopAllVideos())

watch(activeTab, () => fetchVideos(true))
watch(() => route.path, (newPath, oldPath) => {
  if (oldPath?.includes('/short') && !newPath?.includes('/short')) stopAllVideos()
})

// 监听视频播放状态
watch(() => slideRefs.value[currentIndex.value]?.getVideoElement?.()?.paused, (paused) => {
  if (paused !== undefined) isPlaying.value = !paused
}, { deep: true })
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

.video-swiper {
  width: 100%;
  height: 100%;
  overflow: hidden;
  touch-action: pan-y;
}

.video-track {
  width: 100%;
}

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
</style>
