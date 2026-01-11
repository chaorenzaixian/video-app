<template>
  <div class="audio-novel-player">
    <!-- 顶部导航 -->
    <header class="top-header">
      <button class="back-btn" @click="goBack">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </button>
      <h1 class="title">{{ novel?.title || '有声小说' }}</h1>
      <button class="collect-btn" :class="{ active: novel?.is_collected }" @click="toggleCollect">
        <span>{{ novel?.is_collected ? '已收藏' : '+ 收藏' }}</span>
      </button>
    </header>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
    </div>

    <!-- 主内容 -->
    <div v-else-if="novel" class="player-content">
      <!-- 封面区域 -->
      <div class="cover-section">
        <div class="cover-wrapper">
          <img :src="novel.cover" :alt="novel.title" class="cover-image" />
        </div>
      </div>

      <!-- 当前播放信息 -->
      <div class="playing-info">
        <span>正在播放：第{{ currentChapterIndex + 1 }}集</span>
      </div>

      <!-- 进度条区域 -->
      <div class="progress-section">
        <button class="skip-btn" @click="seekRelative(-10)">
          <svg class="skip-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M1 4v6h6" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="skip-num">10</span>
        </button>
        
        <div class="progress-bar-wrapper">
          <input 
            type="range" 
            class="progress-slider" 
            :value="currentTime" 
            :max="duration || 100"
            @input="seekTo($event.target.value)"
          />
        </div>
        
        <button class="skip-btn" @click="seekRelative(10)">
          <svg class="skip-icon forward" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M23 4v6h-6" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="skip-num">10</span>
        </button>
      </div>

      <!-- 时间显示 -->
      <div class="time-display">
        <span class="current-time">{{ formatTime(currentTime) }}</span>
        <span class="total-time">{{ formatTime(duration) }}</span>
      </div>

      <!-- 播放控制 -->
      <div class="controls-section">
        <button class="control-btn mode-btn" @click="cyclePlayMode">
          <svg class="mode-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 1l4 4-4 4" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M3 11V9a4 4 0 0 1 4-4h14" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M7 23l-4-4 4-4" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M21 13v2a4 4 0 0 1-4 4H3" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="mode-text">{{ playModeText }}</span>
        </button>
        
        <button class="control-btn nav-btn" @click="prevChapter" :disabled="currentChapterIndex <= 0">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 6h2v12H6V6zm3.5 6l8.5 6V6l-8.5 6z"/>
          </svg>
        </button>
        
        <button class="control-btn play-btn" @click="togglePlay">
          <svg v-if="isPlaying" class="play-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
          </svg>
          <svg v-else class="play-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8 5v14l11-7L8 5z"/>
          </svg>
        </button>
        
        <button class="control-btn nav-btn" @click="nextChapter" :disabled="currentChapterIndex >= chapters.length - 1">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 18l8.5-6L6 6v12zm10-12v12h2V6h-2z"/>
          </svg>
        </button>
        
        <button class="control-btn list-btn" @click="showPlaylist = true">
          <svg class="list-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="8" y1="6" x2="21" y2="6" stroke-linecap="round"/>
            <line x1="8" y1="12" x2="21" y2="12" stroke-linecap="round"/>
            <line x1="8" y1="18" x2="21" y2="18" stroke-linecap="round"/>
            <line x1="3" y1="6" x2="3.01" y2="6" stroke-linecap="round"/>
            <line x1="3" y1="12" x2="3.01" y2="12" stroke-linecap="round"/>
            <line x1="3" y1="18" x2="3.01" y2="18" stroke-linecap="round"/>
          </svg>
          <span class="list-text">播放列表</span>
        </button>
      </div>

      <!-- 相关推荐 -->
      <div class="recommend-section">
        <h3 class="section-title">相关推荐</h3>
        <div class="recommend-grid">
          <div 
            v-for="item in recommendNovels" 
            :key="item.id" 
            class="recommend-item"
            @click="goToNovel(item.id)"
          >
            <div class="recommend-cover-wrap">
              <img :src="item.cover" :alt="item.title" class="recommend-cover" />
              <span class="audio-badge">🎧</span>
            </div>
            <p class="recommend-title">{{ item.title }}</p>
            <p class="recommend-meta">共{{ item.chapter_count }}话 · {{ item.status === 'completed' ? '已完结' : '连载中' }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 播放列表弹窗 -->
    <div v-if="showPlaylist" class="playlist-modal" @click.self="showPlaylist = false">
      <div class="playlist-panel">
        <!-- 拖动条 -->
        <div class="drag-handle"></div>
        
        <!-- 头部 -->
        <div class="playlist-header">
          <span class="playlist-title">{{ novel?.title }}</span>
          <div class="sort-tabs">
            <span class="sort-tab" :class="{ active: playlistSort === 'asc' }" @click="playlistSort = 'asc'">正序</span>
            <span class="sort-divider">/</span>
            <span class="sort-tab" :class="{ active: playlistSort === 'desc' }" @click="playlistSort = 'desc'">倒序</span>
          </div>
        </div>
        
        <!-- 章节列表 -->
        <div class="playlist-content">
          <div 
            v-for="(chapter, idx) in sortedChapters" 
            :key="chapter.id"
            class="playlist-item"
            :class="{ active: chapter.id === chapters[currentChapterIndex]?.id, locked: !chapter.is_free && !novel?.is_vip }"
            @click="playChapterById(chapter.id)"
          >
            <span class="chapter-title-text">第{{ chapter.num || (playlistSort === 'asc' ? idx + 1 : chapters.length - idx) }}章 {{ chapter.title }}</span>
            <span v-if="!chapter.is_free && !novel?.is_vip" class="lock-icon">🔒</span>
            <span v-else class="arrow-right" :class="{ active: chapter.id === chapters[currentChapterIndex]?.id }"></span>
          </div>
          <div v-if="chapters.length > 0" class="no-more-data">没有更多数据了</div>
        </div>
      </div>
    </div>

    <!-- 隐藏的音频元素 -->
    <audio 
      ref="audioRef"
      @timeupdate="onTimeUpdate"
      @loadedmetadata="onLoadedMetadata"
      @ended="onEnded"
      @play="isPlaying = true"
      @pause="isPlaying = false"
      @error="onError"
    ></audio>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/utils/api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()

// 状态
const loading = ref(true)
const novel = ref(null)
const chapters = ref([])
const currentChapterIndex = ref(0)
const currentChapter = ref(null)
const recommendNovels = ref([])
const showPlaylist = ref(false)
const playlistSort = ref('asc')

// 播放器状态
const audioRef = ref(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const playMode = ref('list') // list, loop, single

// 播放模式
const playModeIcon = computed(() => {
  switch (playMode.value) {
    case 'loop': return '🔁'
    case 'single': return '🔂'
    default: return '📋'
  }
})

const playModeText = computed(() => {
  switch (playMode.value) {
    case 'loop': return '列表循环'
    case 'single': return '单集循环'
    default: return '多集循环'
  }
})

// 排序后的章节列表
const sortedChapters = computed(() => {
  if (playlistSort.value === 'desc') {
    return [...chapters.value].reverse()
  }
  return chapters.value
})

// 获取小说详情
const fetchNovel = async () => {
  loading.value = true
  try {
    const id = route.params.id
    const res = await api.get(`/gallery-novel/novel/${id}`)
    novel.value = res.data
    chapters.value = res.data.chapters || []
    
    // 如果有阅读进度，恢复
    if (res.data.read_progress?.chapter_id) {
      const idx = chapters.value.findIndex(c => c.id === res.data.read_progress.chapter_id)
      if (idx >= 0) currentChapterIndex.value = idx
    }
    
    // 加载第一章
    if (chapters.value.length > 0) {
      await loadChapter(currentChapterIndex.value)
    }
    
    // 获取推荐
    fetchRecommend()
  } catch (e) {
    console.error('获取小说失败', e)
    ElMessage.error('获取小说失败')
  } finally {
    loading.value = false
  }
}

// 获取推荐
const fetchRecommend = async () => {
  try {
    const res = await api.get('/gallery-novel/novel/list', { 
      params: { page_size: 6, novel_type: 'audio' } 
    })
    recommendNovels.value = (res.data || [])
      .filter(n => n.id !== novel.value?.id)
      .slice(0, 3)
  } catch (e) {
    recommendNovels.value = []
  }
}

// 加载章节
const loadChapter = async (idx) => {
  if (idx < 0 || idx >= chapters.value.length) return
  
  const chapter = chapters.value[idx]
  
  // 检查权限
  if (!chapter.is_free && !novel.value?.is_vip) {
    ElMessage.warning('此章节需要VIP才能收听')
    return false
  }
  
  try {
    const res = await api.get(`/gallery-novel/novel/${novel.value.id}/chapter/${chapter.id}`)
    currentChapter.value = res.data
    currentChapterIndex.value = idx
    
    // 设置音频源
    if (audioRef.value && res.data.audio_url) {
      audioRef.value.src = res.data.audio_url
      audioRef.value.load()
      
      // 恢复播放位置
      if (novel.value.read_progress?.chapter_id === chapter.id && 
          novel.value.read_progress?.audio_position > 0) {
        audioRef.value.currentTime = novel.value.read_progress.audio_position
      }
    }
    
    return true
  } catch (e) {
    if (e.response?.status === 403) {
      ElMessage.warning('此章节需要VIP才能收听')
    } else {
      ElMessage.error('加载章节失败')
    }
    return false
  }
}

// 播放指定章节
const playChapter = async (idx) => {
  showPlaylist.value = false
  const success = await loadChapter(idx)
  if (success && audioRef.value) {
    audioRef.value.play()
  }
}

// 通过ID播放章节
const playChapterById = async (chapterId) => {
  const idx = chapters.value.findIndex(c => c.id === chapterId)
  if (idx >= 0) {
    await playChapter(idx)
  }
}

// 播放/暂停
const togglePlay = () => {
  if (!audioRef.value) return
  if (isPlaying.value) {
    audioRef.value.pause()
  } else {
    audioRef.value.play()
  }
}

// 上一章
const prevChapter = async () => {
  if (currentChapterIndex.value > 0) {
    const success = await loadChapter(currentChapterIndex.value - 1)
    if (success && audioRef.value) audioRef.value.play()
  }
}

// 下一章
const nextChapter = async () => {
  if (currentChapterIndex.value < chapters.value.length - 1) {
    const success = await loadChapter(currentChapterIndex.value + 1)
    if (success && audioRef.value) audioRef.value.play()
  }
}

// 快进/快退
const seekRelative = (seconds) => {
  if (!audioRef.value) return
  const newTime = Math.max(0, Math.min(duration.value, currentTime.value + seconds))
  audioRef.value.currentTime = newTime
}

// 跳转到指定时间
const seekTo = (time) => {
  if (audioRef.value) {
    audioRef.value.currentTime = parseFloat(time)
  }
}

// 切换播放模式
const cyclePlayMode = () => {
  const modes = ['list', 'loop', 'single']
  const idx = modes.indexOf(playMode.value)
  playMode.value = modes[(idx + 1) % modes.length]
}

// 音频事件
const onTimeUpdate = () => {
  if (audioRef.value) {
    currentTime.value = audioRef.value.currentTime
  }
}

const onLoadedMetadata = () => {
  if (audioRef.value) {
    duration.value = audioRef.value.duration
  }
}

const onEnded = async () => {
  // 保存进度
  saveProgress()
  
  // 根据播放模式处理
  if (playMode.value === 'single') {
    // 单集循环
    if (audioRef.value) {
      audioRef.value.currentTime = 0
      audioRef.value.play()
    }
  } else if (playMode.value === 'loop' || playMode.value === 'list') {
    // 列表循环或多集循环
    if (currentChapterIndex.value < chapters.value.length - 1) {
      await nextChapter()
    } else if (playMode.value === 'loop') {
      // 循环到第一集
      const success = await loadChapter(0)
      if (success && audioRef.value) audioRef.value.play()
    }
  }
}

const onError = () => {
  ElMessage.error('音频加载失败')
}

// 格式化时间
const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 保存进度
const saveProgress = async () => {
  if (!currentChapter.value || !novel.value) return
  try {
    await api.post(`/gallery-novel/novel/${novel.value.id}/progress`, {
      chapter_id: currentChapter.value.id,
      chapter_num: currentChapter.value.chapter_num,
      audio_position: currentTime.value
    })
  } catch (e) {
    console.error('保存进度失败', e)
  }
}

// 收藏
const toggleCollect = async () => {
  if (!novel.value) return
  try {
    const res = await api.post(`/gallery-novel/novel/${novel.value.id}/collect`)
    novel.value.is_collected = res.data.collected
    ElMessage.success(res.data.collected ? '收藏成功' : '已取消收藏')
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

// 返回有声小说列表页
const goBack = () => {
  saveProgress()
  router.push('/user/community?tab=novel&type=audio')
}

// 跳转小说
const goToNovel = (id) => {
  saveProgress()
  router.push(`/user/audio-novel/${id}`)
}

// 定时保存进度
let saveTimer = null

onMounted(() => {
  fetchNovel()
  saveTimer = setInterval(saveProgress, 30000) // 每30秒保存一次
})

onUnmounted(() => {
  if (saveTimer) clearInterval(saveTimer)
  if (audioRef.value) audioRef.value.pause()
  saveProgress()
})
</script>


<style lang="scss" scoped>
.audio-novel-player {
  min-height: 100vh;
  background: #0d0d0d;
  color: #fff;
}

/* 顶部导航 */
.top-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: #0d0d0d;
}

.back-btn {
  background: none;
  border: none;
  padding: 8px;
  cursor: pointer;
}

.back-icon {
  width: 24px;
  height: 24px;
}

.title {
  flex: 1;
  text-align: center;
  font-size: 17px;
  font-weight: 500;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 0 10px;
}

.collect-btn {
  background: rgba(139, 92, 246, 0.9);
  border: none;
  color: #fff;
  padding: 5px 14px;
  border-radius: 20px;
  font-size: 12px;
  cursor: pointer;
  
  &.active {
    background: rgba(80, 80, 80, 0.8);
  }
}

/* 加载状态 */
.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 50vh;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #333;
  border-top-color: #8b5cf6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 主内容 */
.player-content {
  padding: 0 20px 100px;
}

/* 封面区域 */
.cover-section {
  display: flex;
  justify-content: center;
  padding: 20px 0 30px;
}

.cover-wrapper {
  width: 200px;
  height: 260px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(139, 92, 246, 0.3);
}

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 播放信息 */
.playing-info {
  text-align: center;
  color: #aaa;
  font-size: 14px;
  margin-bottom: 24px;
}

/* 进度条区域 */
.progress-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  padding: 0 10px;
}

.skip-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  padding: 4px;
  width: 40px;
  height: 40px;
  
  .skip-icon {
    width: 32px;
    height: 32px;
  }
  
  .skip-num {
    position: absolute;
    font-size: 9px;
    font-weight: 600;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    margin-top: 1px;
  }
}

.progress-bar-wrapper {
  flex: 1;
}

.progress-slider {
  width: 100%;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: #333;
  border-radius: 2px;
  outline: none;
  cursor: pointer;
  
  &::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 16px;
    height: 16px;
    background: #8b5cf6;
    border-radius: 50%;
    cursor: pointer;
  }
  
  &::-moz-range-thumb {
    width: 16px;
    height: 16px;
    background: #8b5cf6;
    border-radius: 50%;
    cursor: pointer;
    border: none;
  }
}

/* 时间显示 */
.time-display {
  display: flex;
  justify-content: space-between;
  color: #666;
  font-size: 12px;
  margin-bottom: 30px;
}

/* 播放控制 */
.controls-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  margin-bottom: 40px;
}

.control-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: none;
  border: none;
  color: #fff;
  cursor: pointer;
  padding: 8px;
  
  &:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }
}

.mode-btn, .list-btn {
  .mode-icon, .list-icon {
    width: 24px;
    height: 24px;
    margin-bottom: 6px;
  }
  
  .mode-text, .list-text {
    font-size: 11px;
    color: #888;
  }
}

.nav-btn {
  .nav-icon {
    width: 28px;
    height: 28px;
  }
}

.play-btn {
  width: 48px;
  height: 48px;
  background: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  
  .play-icon {
    width: 36px;
    height: 36px;
    color: #0d0d0d;
    margin-left: 2px;
  }
}

/* 相关推荐 */
.recommend-section {
  margin-top: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 16px;
}

.recommend-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.recommend-item {
  cursor: pointer;
}

.recommend-cover-wrap {
  position: relative;
  width: 100%;
  height: 0;
  padding-bottom: 133%;
  border-radius: 8px;
  overflow: hidden;
  background: #1a1a1a;
}

.recommend-cover {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.audio-badge {
  position: absolute;
  top: 6px;
  left: 6px;
  background: rgba(0, 0, 0, 0.6);
  padding: 4px 6px;
  border-radius: 10px;
  font-size: 12px;
}

.recommend-title {
  color: #ddd;
  font-size: 13px;
  margin: 8px 0 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recommend-meta {
  color: #666;
  font-size: 11px;
}

/* 播放列表弹窗 */
.playlist-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  z-index: 200;
  display: flex;
  align-items: flex-end;
}

.playlist-panel {
  width: 100%;
  max-height: 80vh;
  background: #0a0e1a;
  border-radius: 16px 16px 0 0;
  display: flex;
  flex-direction: column;
  
  .drag-handle {
    width: 40px;
    height: 4px;
    background: #3a4a5a;
    border-radius: 2px;
    margin: 10px auto;
  }
}

.playlist-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px 20px;
}

.playlist-title {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
}

.playlist-header .sort-tabs {
  display: flex;
  align-items: center;
  gap: 4px;
}

.playlist-header .sort-tab {
  color: #556677;
  font-size: 14px;
  cursor: pointer;
  padding: 2px 4px;
}

.playlist-header .sort-tab.active {
  color: #a78bfa;
}

.playlist-header .sort-divider {
  color: #445566;
  font-size: 14px;
}

.playlist-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 20px 20px;
}

.playlist-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid rgba(100, 120, 150, 0.2);
  cursor: pointer;
  
  .chapter-title-text {
    color: #aaa;
    font-size: 15px;
  }
  
  &.active {
    .chapter-title-text {
      background: linear-gradient(90deg, #8b5cf6, #a855f7);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      font-weight: 500;
    }
    .arrow-right {
      border-color: #a855f7;
    }
  }
  
  &.locked {
    opacity: 0.5;
  }
  
  .arrow-right {
    width: 8px;
    height: 8px;
    border-right: 2px solid #556677;
    border-bottom: 2px solid #556677;
    transform: rotate(-45deg);
    
    &.active {
      border-color: #a855f7;
    }
  }
  
  .lock-icon {
    font-size: 14px;
  }
}

.no-more-data {
  text-align: center;
  color: #445566;
  font-size: 13px;
  padding: 30px 0;
}
</style>
