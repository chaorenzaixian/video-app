<template>
  <div class="novel-detail-page">
    <!-- 顶部导航 -->
    <header class="top-header">
      <button class="back-btn" @click="goBack">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </button>
      <div class="header-right">
        <button class="collect-btn" :class="{ active: novel?.is_collected }" @click="toggleCollect">
          <span>{{ novel?.is_collected ? '已收藏' : '+ 收藏' }}</span>
        </button>
      </div>
    </header>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <!-- 内容区域 -->
    <div v-else-if="novel" class="content-area">
      <!-- 小说信息头部 - 带背景 -->
      <div class="novel-header" :style="{ backgroundImage: `url(${novel.cover})` }">
        <div class="header-overlay"></div>
        <div class="header-content">
          <img :src="novel.cover" :alt="novel.title" class="novel-cover" />
          <div class="novel-info">
            <h2 class="novel-title">{{ novel.title }}</h2>
            <p class="novel-meta">共{{ novel.chapter_count }}话 / {{ novel.status === 'ongoing' ? '连载中' : '已完结' }}</p>
          </div>
        </div>
      </div>

      <!-- 简介区域 -->
      <div class="desc-section">
        <p class="novel-desc" :class="{ expanded: descExpanded }">{{ novel.description || '暂无简介' }}</p>
        <div class="expand-btn" @click="descExpanded = !descExpanded">
          {{ descExpanded ? '收起' : '更多简介' }} <span class="arrow-down" :class="{ up: descExpanded }"></span>
        </div>
      </div>

      <!-- 章节区域 -->
      <div class="chapters-section">
        <div class="section-header">
          <span class="chapter-count">共{{ chapters.length }}章</span>
          <button class="catalog-btn" @click="showCatalog = true">目录 <span class="arrow-right"></span></button>
        </div>
        
        <!-- 章节列表（显示前几章） -->
        <div class="chapters-preview">
          <div 
            v-for="chapter in displayChapters" 
            :key="chapter.id" 
            class="chapter-item"
            :class="{ current: novel.read_progress?.chapter_id === chapter.id }"
            @click="readChapter(chapter)"
          >
            <span class="chapter-title">第{{ chapter.num }}章 {{ chapter.title }}</span>
            <span v-if="isNewChapter(chapter)" class="new-tag">new</span>
            <span v-if="!chapter.is_free && !novel.is_vip" class="lock-icon">🔒</span>
            <span v-else class="arrow-right"></span>
          </div>
        </div>
      </div>

      <!-- 相关推荐 & 互动点评 Tab -->
      <div class="tabs-section">
        <div class="tabs-header">
          <span class="tab-item" :class="{ active: activeTab === 'recommend' }" @click="activeTab = 'recommend'">相关推荐</span>
          <span class="tab-item" :class="{ active: activeTab === 'comments' }" @click="activeTab = 'comments'">互动点评({{ commentCount }})</span>
        </div>
        
        <!-- 相关推荐 -->
        <div v-if="activeTab === 'recommend'" class="recommend-list">
          <div v-for="item in recommendNovels" :key="item.id" class="recommend-item" @click="goToNovel(item.id)">
            <div class="recommend-cover-wrap">
              <img :src="item.cover" :alt="item.title" class="recommend-cover" />
            </div>
            <p class="recommend-title">{{ item.title }}</p>
          </div>
          <div v-if="recommendNovels.length === 0" class="no-data">暂无推荐</div>
        </div>
        
        <!-- 互动点评 -->
        <div v-if="activeTab === 'comments'" class="comments-preview">
          <div v-if="comments.length === 0" class="no-data">暂无评论</div>
          <div v-for="comment in comments.slice(0, 3)" :key="comment.id" class="comment-item">
            <img :src="getAvatarUrl(comment.user_avatar, comment.user_id)" class="comment-avatar" @error="(e) => e.target.src = '/images/avatars/icon_avatar_1.webp'" />
            <div class="comment-body">
              <span class="comment-user">{{ comment.user_nickname }}</span>
              <p class="comment-text">{{ comment.content }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 错误状态 -->
    <div v-else class="error-state">
      <p>小说不存在或已被删除</p>
      <button class="back-btn-large" @click="goBack">返回</button>
    </div>

    <!-- 底部操作栏 -->
    <div class="action-bar" v-if="novel">
      <button class="action-btn" :class="{ active: novel.is_liked }" @click="toggleLike">
        <img :src="novel.is_liked ? likeRedIcon : likeEmptyIcon" class="action-icon" />
        <span class="action-text">{{ novel.like_count || 0 }}</span>
      </button>
      <button class="action-btn" @click="openComments">
        <img :src="commentIcon" class="action-icon" />
        <span class="action-text">{{ commentCount }}</span>
      </button>
      <button class="read-btn" @click="continueReading">
        {{ novel.read_progress ? '继续阅读' : '开始阅读' }}
      </button>
    </div>

    <!-- 目录弹窗 -->
    <div v-if="showCatalog" class="catalog-modal" @click.self="showCatalog = false">
      <div class="catalog-panel">
        <!-- 拖动条 -->
        <div class="drag-handle"></div>
        
        <!-- 头部 -->
        <div class="catalog-header">
          <span class="catalog-title">{{ novel?.title }}</span>
          <div class="sort-tabs">
            <span class="sort-tab" :class="{ active: catalogSort === 'asc' }" @click="catalogSort = 'asc'">正序</span>
            <span class="sort-divider">/</span>
            <span class="sort-tab" :class="{ active: catalogSort === 'desc' }" @click="catalogSort = 'desc'">倒序</span>
          </div>
        </div>
        
        <!-- 章节列表 -->
        <div class="catalog-list">
          <div 
            v-for="chapter in sortedChapters" 
            :key="chapter.id" 
            class="catalog-item"
            :class="{ 
              current: novel.read_progress?.chapter_id === chapter.id,
              locked: !chapter.is_free && !novel.is_vip
            }"
            @click="readChapter(chapter)"
          >
            <span class="catalog-chapter-title">第{{ chapter.num }}章 {{ chapter.title }}</span>
            <span v-if="!chapter.is_free && !novel.is_vip" class="lock-icon">🔒</span>
            <span v-else class="arrow-right" :class="{ active: novel.read_progress?.chapter_id === chapter.id }"></span>
          </div>
          <div v-if="chapters.length > 0" class="no-more-data">没有更多数据了</div>
        </div>
      </div>
    </div>

    <!-- 文字阅读器 -->
    <div v-if="showReader" class="reader-modal">
      <div class="reader-header">
        <button class="back-btn" @click="closeReader">
          <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
        </button>
        <span class="chapter-name">{{ currentChapter?.title }}</span>
        <button class="setting-btn" @click="showSettings = !showSettings">⚙️</button>
      </div>
      
      <!-- 阅读设置面板 -->
      <div v-if="showSettings" class="settings-panel">
        <div class="setting-item">
          <span>字体大小</span>
          <div class="font-sizes">
            <button v-for="size in [14, 16, 18, 20, 22]" :key="size" 
              :class="{ active: fontSize === size }" @click="fontSize = size">
              {{ size }}
            </button>
          </div>
        </div>
      </div>
      
      <div class="reader-content" ref="readerContent" :style="{ fontSize: fontSize + 'px' }" @scroll="onScroll">
        <div v-if="chapterLoading" class="loading-state">
          <div class="loading-spinner"></div>
        </div>
        <div v-else class="chapter-content" v-html="formatContent(currentChapter?.content)"></div>
      </div>
      
      <div class="reader-footer">
        <button class="nav-btn" :disabled="!currentChapter?.prev_chapter" @click="prevChapter">上一章</button>
        <span class="progress">{{ currentChapterIndex + 1 }} / {{ chapters.length }}</span>
        <button class="nav-btn" :disabled="!currentChapter?.next_chapter" @click="nextChapter">下一章</button>
      </div>
    </div>

    <!-- 有声小说播放器 -->
    <div v-if="showAudioPlayer" class="audio-player-modal">
      <div class="player-header">
        <button class="back-btn" @click="closeAudioPlayer">
          <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
        </button>
        <span class="chapter-name">{{ currentChapter?.title }}</span>
        <div class="header-right"></div>
      </div>
      
      <div class="player-content">
        <div class="cover-area">
          <img :src="novel.cover" :alt="novel.title" class="player-cover" />
          <div class="playing-animation" v-if="isPlaying">
            <span></span><span></span><span></span><span></span>
          </div>
        </div>
        
        <div class="audio-info">
          <h3 class="audio-title">{{ novel.title }}</h3>
          <p class="audio-chapter">{{ currentChapter?.title }}</p>
        </div>
        
        <!-- 进度条 -->
        <div class="progress-bar">
          <span class="time current">{{ formatTime(audioCurrentTime) }}</span>
          <input type="range" class="progress-slider" 
            :value="audioCurrentTime" :max="audioDuration" 
            @input="seekAudio($event.target.value)" />
          <span class="time total">{{ formatTime(audioDuration) }}</span>
        </div>
        
        <!-- 控制按钮 -->
        <div class="player-controls">
          <button class="control-btn" @click="prevChapter" :disabled="!currentChapter?.prev_chapter">⏮️</button>
          <button class="control-btn rewind" @click="seekRelative(-15)">-15s</button>
          <button class="control-btn play-btn" @click="togglePlay">{{ isPlaying ? '⏸️' : '▶️' }}</button>
          <button class="control-btn forward" @click="seekRelative(15)">+15s</button>
          <button class="control-btn" @click="nextChapter" :disabled="!currentChapter?.next_chapter">⏭️</button>
        </div>
        
        <!-- 倍速和定时 -->
        <div class="player-options">
          <button class="option-btn" @click="cycleSpeed">{{ playbackRate }}x</button>
          <button class="option-btn" @click="showTimerModal = true">
            {{ sleepTimer ? `${sleepTimer}分钟后关闭` : '定时关闭' }}
          </button>
          <button class="option-btn" :class="{ active: autoNext }" @click="autoNext = !autoNext">
            {{ autoNext ? '连播中' : '单章' }}
          </button>
        </div>
      </div>
      
      <!-- 章节列表 -->
      <div class="player-chapters">
        <div class="chapters-header"><span>章节列表</span></div>
        <div class="chapters-scroll">
          <div v-for="chapter in chapters" :key="chapter.id" 
            class="chapter-item" 
            :class="{ active: currentChapter?.id === chapter.id, locked: !chapter.is_free && !novel.is_vip }"
            @click="readChapter(chapter)">
            <span>{{ chapter.title }}</span>
            <span v-if="!chapter.is_free && !novel.is_vip">🔒</span>
          </div>
        </div>
      </div>
      
      <audio ref="audioPlayer" 
        @timeupdate="onTimeUpdate" 
        @loadedmetadata="onLoadedMetadata"
        @ended="onAudioEnded"
        @play="isPlaying = true"
        @pause="isPlaying = false">
      </audio>
    </div>

    <!-- 定时关闭弹窗 -->
    <div v-if="showTimerModal" class="timer-modal" @click.self="showTimerModal = false">
      <div class="timer-content">
        <h3>定时关闭</h3>
        <div class="timer-options">
          <button v-for="min in [15, 30, 45, 60, 90]" :key="min" @click="setSleepTimer(min)">{{ min }}分钟</button>
          <button @click="setSleepTimer(0)">取消定时</button>
        </div>
      </div>
    </div>

    <!-- 评论弹窗 -->
    <div v-if="showComments" class="comments-modal" @click.self="closeComments">
      <div class="comments-panel">
        <!-- 拖动条 -->
        <div class="drag-handle"></div>
        
        <!-- 头部 -->
        <div class="comments-header">
          <span class="comment-count">{{ comments.length }}条评论</span>
          <div class="sort-tabs">
            <span class="sort-tab" :class="{ active: sortType === 'hot' }" @click="sortType = 'hot'">推荐</span>
            <span class="sort-divider">|</span>
            <span class="sort-tab" :class="{ active: sortType === 'new' }" @click="sortType = 'new'">最新</span>
          </div>
        </div>
        
        <!-- 评论列表 -->
        <div class="comments-list">
          <!-- 官方公告 -->
          <div v-if="announcement && announcement.enabled" class="comment-item official-announcement">
            <img :src="announcement.avatar || '/images/avatars/icon_avatar_1.webp'" class="comment-avatar" />
            <div class="comment-body">
              <div class="comment-user">
                <span class="official-name">{{ announcement.name }}</span>
                <img src="/images/backgrounds/super_vip_blue.webp" class="supreme-vip-icon" />
              </div>
              <div class="comment-text official-text">{{ announcement.content }}</div>
              <div class="comment-footer">
                <span class="comment-time">{{ formatAnnouncementTime(announcement.updated_at) }}</span>
              </div>
            </div>
          </div>
          
          <div v-if="comments.length === 0 && !(announcement && announcement.enabled)" class="no-comments">暂无评论</div>
          <div v-for="comment in comments" :key="comment.id" class="comment-item">
            <img :src="getAvatarUrl(comment.user_avatar, comment.user_id)" class="comment-avatar clickable" @click="goToUserProfile(comment.user_id)" @error="(e) => e.target.src = '/images/avatars/icon_avatar_1.webp'" />
            <div class="comment-body">
              <div class="comment-user">
                <span class="username clickable" @click="goToUserProfile(comment.user_id)">{{ comment.user_nickname || '用户' }}</span>
                <img v-if="comment.user_vip_level > 0" :src="getVipLevelIcon(comment.user_vip_level)" class="vip-badge-sm" />
              </div>
              <div class="comment-text">{{ comment.content }}</div>
              <!-- 评论图片 -->
              <div v-if="comment.image_url" class="comment-image" @click="previewCommentImage(comment.image_url)">
                <img :src="comment.image_url" alt="评论图片" />
              </div>
              <div class="comment-footer">
                <span class="comment-time">{{ formatCommentTime(comment.created_at) }}</span>
                <div class="comment-actions">
                  <span :class="['comment-like', { liked: comment.is_liked }]" @click="likeComment(comment)">
                    {{ comment.is_liked ? '❤️' : '🤍' }} {{ comment.like_count || 0 }}
                  </span>
                  <span class="comment-reply" @click="startReply(comment)">
                    <img :src="replyIcon" class="reply-icon" />
                  </span>
                </div>
              </div>
            </div>
          </div>
          <div v-if="comments.length > 0" class="no-more">没有更多数据了</div>
        </div>
        
        <!-- 简单输入框（点击展开完整输入） -->
        <div class="comment-input-trigger" @click="openInputPanel">
          <span class="input-placeholder">在这里写下你想说的...</span>
          <span class="char-count">0/500</span>
        </div>
        
        <!-- 底部工具栏 -->
        <div class="comment-toolbar">
          <div class="toolbar-left">
            <button class="toolbar-btn" @click="triggerImageUpload">
              <img :src="picIcon" class="toolbar-icon" />
            </button>
            <button class="toolbar-btn" @click="toggleEmojiPanel">
              <span class="emoji-icon">😊</span>
            </button>
          </div>
          <button class="toolbar-send" @click="openInputPanel">
            <img :src="sendIcon" class="send-icon" />
          </button>
        </div>
      </div>
    </div>
    
    <!-- 完整输入弹窗 -->
    <div v-if="showInputPanel" class="input-panel-modal" @click.self="closeInputPanel">
      <div class="input-panel">
        <div class="input-panel-header">
          <button class="cancel-btn" @click="closeInputPanel">取消</button>
          <span class="panel-title">发表评论</span>
          <button class="submit-btn" :disabled="!commentText.trim() && !commentImage" @click="submitComment">发送</button>
        </div>
        <div class="input-panel-body">
          <textarea 
            v-model="commentText" 
            class="full-input" 
            placeholder="在这里写下你想说的..." 
            maxlength="500"
            ref="textareaRef"
          ></textarea>
          <div class="char-counter">{{ commentText.length }}/500</div>
          <!-- 图片预览 -->
          <div v-if="commentImage" class="image-preview">
            <img :src="commentImagePreview" alt="预览" />
            <button class="remove-image" @click="removeCommentImage">×</button>
          </div>
        </div>
        <div class="input-panel-footer">
          <div class="footer-left">
            <button class="footer-btn" @click="triggerImageUpload">
              <img :src="picIcon" class="footer-icon" />
            </button>
            <button class="footer-btn" @click="toggleEmojiPanel">
              <span class="emoji-icon">😊</span>
            </button>
          </div>
        </div>
        <!-- 表情面板 -->
        <div v-if="showEmojiPanel" class="emoji-panel">
          <span v-for="emoji in emojis" :key="emoji" class="emoji-item" @click="insertEmoji(emoji)">{{ emoji }}</span>
        </div>
      </div>
    </div>
    
    <!-- 评论图片预览弹窗 -->
    <div v-if="showCommentImagePreview" class="comment-image-preview-modal" @click="closeCommentImagePreview">
      <div class="comment-image-preview-content">
        <img :src="commentImagePreviewUrl" alt="评论图片" />
        <button class="close-preview-btn" @click.stop="closeCommentImagePreview">×</button>
      </div>
    </div>
    
    <!-- 隐藏的文件上传 -->
    <input type="file" ref="imageInput" accept="image/*" style="display:none" @change="handleImageSelect" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/utils/api'
import { ElMessage } from 'element-plus'

// 图标
import likeEmptyIcon from '@/assets/icons/like_empty.png'
import likeRedIcon from '@/assets/icons/like_red.png'
import commentIcon from '@/assets/icons/comment.png'
import picIcon from '@/assets/icons/icon_pic_red.webp'
import sendIcon from '@/assets/icons/ic_send_red.webp'
import replyIcon from '@/assets/icons/msg_icon.png'
import { VIP_LEVEL_ICONS } from '@/constants/vip'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const novel = ref(null)
const chapters = ref([])
const descExpanded = ref(false)
const activeTab = ref('recommend')
const showCatalog = ref(false)
const catalogSort = ref('asc')
const recommendNovels = ref([])
const comments = ref([])
const commentCount = ref(0)

// 评论相关
const showComments = ref(false)
const sortType = ref('hot')
const announcement = ref(null)
const showInputPanel = ref(false)
const showEmojiPanel = ref(false)
const commentText = ref('')
const commentImage = ref(null)
const commentImagePreview = ref('')
const imageInput = ref(null)
const textareaRef = ref(null)
const commentImagePreviewUrl = ref('')
const showCommentImagePreview = ref(false)
const replyToComment = ref(null)

// 表情列表
const emojis = ['😀', '😂', '🤣', '😍', '🥰', '😘', '😋', '🤤', '😎', '🤩', '😏', '😒', '😞', '😢', '😭', '😤', '😡', '🤬', '😱', '😨', '🥺', '😇', '🤗', '🤔', '🤫', '🤭', '🙄', '😴', '🤮', '🤧', '😷', '🤒', '👍', '👎', '👏', '🙌', '💪', '🤝', '❤️', '💔', '💯', '🔥', '⭐', '🎉', '🎊', '💐', '🌹', '🍀']

// 阅读器相关
const showReader = ref(false)
const showAudioPlayer = ref(false)
const currentChapter = ref(null)
const currentChapterIndex = ref(0)
const chapterLoading = ref(false)
const fontSize = ref(16)
const showSettings = ref(false)
const readerContent = ref(null)
const scrollPosition = ref(0)
let saveProgressTimer = null

// 有声小说相关
const audioPlayer = ref(null)
const isPlaying = ref(false)
const audioCurrentTime = ref(0)
const audioDuration = ref(0)
const playbackRate = ref(1)
const autoNext = ref(true)
const sleepTimer = ref(0)
const showTimerModal = ref(false)
let sleepTimerInterval = null

// 显示前4章
const displayChapters = computed(() => chapters.value.slice(0, 4))

// 排序后的章节列表
const sortedChapters = computed(() => {
  if (catalogSort.value === 'desc') {
    return [...chapters.value].reverse()
  }
  return chapters.value
})

// 判断是否新章节（7天内）
const isNewChapter = (chapter) => {
  if (!chapter.created_at) return false
  const created = new Date(chapter.created_at)
  const now = new Date()
  return (now - created) < 7 * 24 * 60 * 60 * 1000
}

// 获取小说详情
const fetchNovel = async () => {
  loading.value = true
  try {
    const id = route.params.id
    const res = await api.get(`/gallery-novel/novel/${id}`)
    novel.value = res.data
    chapters.value = res.data.chapters || []
    // 获取推荐和评论
    fetchRecommend()
    fetchComments()
  } catch (e) {
    console.error('获取小说详情失败', e)
    ElMessage.error('获取小说详情失败')
  } finally {
    loading.value = false
  }
}

// 获取推荐小说
const fetchRecommend = async () => {
  try {
    const res = await api.get('/gallery-novel/novel/list', { params: { page_size: 6 } })
    recommendNovels.value = (res.data || []).filter(n => n.id !== novel.value?.id).slice(0, 5)
  } catch (e) {
    recommendNovels.value = []
  }
}

// 获取评论
const fetchComments = async () => {
  try {
    const res = await api.get(`/gallery-novel/novel/${novel.value.id}/comments`)
    comments.value = res.data || []
    commentCount.value = comments.value.length
  } catch (e) {
    comments.value = []
    commentCount.value = 0
  }
}

// 评论功能
const openComments = async () => {
  showComments.value = true
  await Promise.all([fetchComments(), fetchAnnouncement()])
}

const closeComments = () => {
  showComments.value = false
}

// 获取评论区公告
const fetchAnnouncement = async () => {
  try {
    const res = await api.get('/settings/comment-announcement')
    announcement.value = res.data || res
  } catch (e) {
    console.log('获取公告失败:', e)
  }
}

const submitComment = async () => {
  if (!commentText.value.trim() && !commentImage.value) return
  try {
    let response
    if (commentImage.value) {
      const formData = new FormData()
      formData.append('content', commentText.value || '')
      formData.append('image', commentImage.value)
      response = await api.post(`/gallery-novel/novel/${novel.value.id}/comment`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
    } else {
      response = await api.post(`/gallery-novel/novel/${novel.value.id}/comment`, {
        content: commentText.value
      })
    }
    commentText.value = ''
    commentImage.value = null
    commentImagePreview.value = ''
    showInputPanel.value = false
    showEmojiPanel.value = false
    await fetchComments()
    ElMessage.success('评论成功')
  } catch (e) {
    console.error('评论失败:', e)
    ElMessage.error(e.response?.data?.detail || '评论失败')
  }
}

// 输入面板
const openInputPanel = () => {
  showInputPanel.value = true
  showEmojiPanel.value = false
  setTimeout(() => textareaRef.value?.focus(), 100)
}

const closeInputPanel = () => {
  showInputPanel.value = false
  showEmojiPanel.value = false
}

// 表情面板
const toggleEmojiPanel = () => {
  if (!showInputPanel.value) {
    showInputPanel.value = true
    setTimeout(() => { showEmojiPanel.value = true }, 100)
  } else {
    showEmojiPanel.value = !showEmojiPanel.value
  }
}

const insertEmoji = (emoji) => {
  commentText.value += emoji
}

// 图片上传
const triggerImageUpload = () => {
  imageInput.value?.click()
}

const handleImageSelect = (e) => {
  const file = e.target.files?.[0]
  if (file) {
    if (file.size > 5 * 1024 * 1024) {
      ElMessage.warning('图片大小不能超过5MB')
      return
    }
    commentImage.value = file
    commentImagePreview.value = URL.createObjectURL(file)
    if (!showInputPanel.value) {
      openInputPanel()
    }
  }
  e.target.value = ''
}

const removeCommentImage = () => {
  commentImage.value = null
  commentImagePreview.value = ''
}

// 预览评论图片
const previewCommentImage = (url) => {
  commentImagePreviewUrl.value = url
  showCommentImagePreview.value = true
}

const closeCommentImagePreview = () => {
  showCommentImagePreview.value = false
  commentImagePreviewUrl.value = ''
}

// 评论点赞
const likeComment = async (comment) => {
  try {
    const res = await api.post(`/gallery-novel/novel-comment/${comment.id}/like`)
    comment.is_liked = res.data.liked
    comment.like_count = res.data.like_count
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

// 回复评论
const startReply = (comment) => {
  replyToComment.value = comment
  commentText.value = `@${comment.user_nickname || '用户'} `
  openInputPanel()
}

// 跳转用户主页
const goToUserProfile = (userId) => {
  if (userId) {
    router.push(`/user/profile/${userId}`)
  }
}

// 格式化评论时间
const formatCommentTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = (now - date) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + '小时前'
  return date.toLocaleDateString()
}

// 格式化公告时间
const formatAnnouncementTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 获取VIP等级图标
const getVipLevelIcon = (level) => {
  return VIP_LEVEL_ICONS[level] || ''
}

// 跳转小说
const goToNovel = (id) => {
  if (id === novel.value?.id) return
  // 使用 replace 避免历史记录堆积
  router.replace(`/user/novel/${id}`)
}

// 返回小说列表页
const goBack = () => {
  router.push('/user/community?tab=novel')
}

// 继续阅读
const continueReading = () => {
  if (novel.value.read_progress) {
    const chapter = chapters.value.find(c => c.id === novel.value.read_progress.chapter_id)
    if (chapter) {
      readChapter(chapter)
      return
    }
  }
  if (chapters.value.length > 0) {
    readChapter(chapters.value[0])
  }
}

// 阅读章节
const readChapter = async (chapter) => {
  if (!chapter.is_free && !novel.value.is_vip) {
    ElMessage.warning('此章节需要VIP才能阅读')
    return
  }
  
  showCatalog.value = false
  currentChapterIndex.value = chapters.value.findIndex(c => c.id === chapter.id)
  
  if (novel.value.novel_type === 'audio') {
    showAudioPlayer.value = true
  } else {
    showReader.value = true
  }
  
  await loadChapterContent(chapter.id)
  
  // 恢复阅读位置
  if (novel.value.read_progress?.chapter_id === chapter.id) {
    await nextTick()
    if (novel.value.novel_type === 'audio') {
      if (audioPlayer.value && novel.value.read_progress.audio_position > 0) {
        audioPlayer.value.currentTime = novel.value.read_progress.audio_position
      }
    } else {
      if (readerContent.value && novel.value.read_progress.scroll_position > 0) {
        const maxScroll = readerContent.value.scrollHeight - readerContent.value.clientHeight
        readerContent.value.scrollTop = maxScroll * (novel.value.read_progress.scroll_position / 100)
      }
    }
  }
}

// 加载章节内容
const loadChapterContent = async (chapterId) => {
  chapterLoading.value = true
  try {
    const res = await api.get(`/gallery-novel/novel/${novel.value.id}/chapter/${chapterId}`)
    currentChapter.value = res.data
    
    if (novel.value.novel_type === 'audio' && res.data.audio_url) {
      await nextTick()
      if (audioPlayer.value) {
        audioPlayer.value.src = res.data.audio_url
        audioPlayer.value.playbackRate = playbackRate.value
        audioPlayer.value.load()
      }
    }
  } catch (e) {
    if (e.response?.status === 403) {
      ElMessage.warning('此章节需要VIP才能阅读')
      showReader.value = false
      showAudioPlayer.value = false
    } else {
      ElMessage.error('加载章节失败')
    }
  } finally {
    chapterLoading.value = false
  }
}

// 上一章/下一章
const prevChapter = () => {
  if (currentChapter.value?.prev_chapter) {
    const chapter = chapters.value.find(c => c.id === currentChapter.value.prev_chapter.id)
    if (chapter) readChapter(chapter)
  }
}

const nextChapter = () => {
  if (currentChapter.value?.next_chapter) {
    const chapter = chapters.value.find(c => c.id === currentChapter.value.next_chapter.id)
    if (chapter) {
      if (!chapter.is_free && !novel.value.is_vip) {
        ElMessage.warning('下一章需要VIP才能阅读')
        return
      }
      readChapter(chapter)
    }
  }
}

// 关闭阅读器
const closeReader = () => {
  saveProgress()
  showReader.value = false
  currentChapter.value = null
}

const closeAudioPlayer = () => {
  saveProgress()
  if (audioPlayer.value) audioPlayer.value.pause()
  showAudioPlayer.value = false
  currentChapter.value = null
}

// 保存阅读进度
const saveProgress = async () => {
  if (!currentChapter.value) return
  try {
    await api.post(`/gallery-novel/novel/${novel.value.id}/progress`, {
      chapter_id: currentChapter.value.id,
      chapter_num: currentChapter.value.chapter_num,
      scroll_position: scrollPosition.value,
      audio_position: audioCurrentTime.value
    })
  } catch (e) {
    console.error('保存进度失败', e)
  }
}

// 滚动事件
const onScroll = () => {
  if (!readerContent.value) return
  const maxScroll = readerContent.value.scrollHeight - readerContent.value.clientHeight
  scrollPosition.value = maxScroll > 0 ? (readerContent.value.scrollTop / maxScroll) * 100 : 0
  clearTimeout(saveProgressTimer)
  saveProgressTimer = setTimeout(saveProgress, 2000)
}

// 格式化内容
const formatContent = (content) => {
  if (!content) return ''
  return content.replace(/\n/g, '<br/>')
}

// 音频播放器相关
const togglePlay = () => {
  if (!audioPlayer.value) return
  isPlaying.value ? audioPlayer.value.pause() : audioPlayer.value.play()
}

const onTimeUpdate = () => {
  if (audioPlayer.value) audioCurrentTime.value = audioPlayer.value.currentTime
}

const onLoadedMetadata = () => {
  if (audioPlayer.value) audioDuration.value = audioPlayer.value.duration
}

const onAudioEnded = () => {
  saveProgress()
  if (autoNext.value && currentChapter.value?.next_chapter) {
    nextChapter()
    setTimeout(() => { if (audioPlayer.value) audioPlayer.value.play() }, 500)
  }
}

const seekAudio = (time) => {
  if (audioPlayer.value) audioPlayer.value.currentTime = parseFloat(time)
}

const seekRelative = (seconds) => {
  if (audioPlayer.value) {
    audioPlayer.value.currentTime = Math.max(0, Math.min(audioDuration.value, audioCurrentTime.value + seconds))
  }
}

const cycleSpeed = () => {
  const speeds = [0.75, 1, 1.25, 1.5, 2]
  const idx = speeds.indexOf(playbackRate.value)
  playbackRate.value = speeds[(idx + 1) % speeds.length]
  if (audioPlayer.value) audioPlayer.value.playbackRate = playbackRate.value
}

const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const setSleepTimer = (minutes) => {
  showTimerModal.value = false
  sleepTimer.value = minutes
  if (sleepTimerInterval) { clearInterval(sleepTimerInterval); sleepTimerInterval = null }
  if (minutes > 0) {
    sleepTimerInterval = setInterval(() => {
      sleepTimer.value--
      if (sleepTimer.value <= 0) {
        clearInterval(sleepTimerInterval)
        if (audioPlayer.value) audioPlayer.value.pause()
        ElMessage.info('定时关闭已生效')
      }
    }, 60000)
  }
}

// 点赞/收藏
const toggleLike = async () => {
  try {
    const res = await api.post(`/gallery-novel/novel/${novel.value.id}/like`)
    novel.value.is_liked = res.data.liked
    novel.value.like_count = res.data.like_count
  } catch (e) { ElMessage.error('操作失败') }
}

const toggleCollect = async () => {
  try {
    const res = await api.post(`/gallery-novel/novel/${novel.value.id}/collect`)
    novel.value.is_collected = res.data.collected
    ElMessage.success(res.data.collected ? '收藏成功' : '已取消收藏')
  } catch (e) { ElMessage.error('操作失败') }
}

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

// 根据用户ID获取头像
const getAvatarUrl = (avatar, userId) => {
  if (avatar) return avatar
  const numericId = parseInt(userId) || 1
  return getDefaultAvatarPath(numericId)
}

// 监听路由变化
watch(() => route.params.id, (newId, oldId) => {
  if (newId && newId !== oldId) {
    fetchNovel()
  }
})

onMounted(() => { fetchNovel() })

onUnmounted(() => {
  if (saveProgressTimer) clearTimeout(saveProgressTimer)
  if (sleepTimerInterval) clearInterval(sleepTimerInterval)
  if (audioPlayer.value) audioPlayer.value.pause()
})
</script>

<style lang="scss" scoped>
.novel-detail-page {
  min-height: 100vh;
  background: #0a0a0f;
  padding-bottom: 80px;
}

.top-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
}

.back-btn {
  background: none;
  border: none;
  padding: 8px;
  cursor: pointer;
  .back-icon { width: 24px; height: 24px; }
}

.collect-btn {
  background: rgba(139, 92, 246, 0.9);
  border: none;
  color: #fff;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 13px;
  cursor: pointer;
  &.active { background: rgba(100, 100, 100, 0.8); }
}

.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 20px;
  color: #888;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #333;
  border-top-color: #8b5cf6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* 小说头部 - 带模糊背景 */
.novel-header {
  position: relative;
  padding: 60px 20px 30px;
  background-size: cover;
  background-position: center;
}

.header-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(10, 10, 15, 0.3) 0%, rgba(10, 10, 15, 0.95) 100%);
  backdrop-filter: blur(20px);
}

.header-content {
  position: relative;
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.novel-cover {
  width: 100px;
  height: 140px;
  border-radius: 8px;
  object-fit: cover;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.novel-info {
  flex: 1;
  padding-top: 10px;
}

.novel-title {
  color: #fff;
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 10px;
  line-height: 1.3;
}

.novel-meta {
  color: #8899aa;
  font-size: 13px;
}

/* 简介区域 */
.desc-section {
  padding: 16px 20px;
  border-bottom: 1px solid #1a1a25;
}

.novel-desc {
  color: #8899aa;
  font-size: 14px;
  line-height: 1.8;
  max-height: 60px;
  overflow: hidden;
  transition: max-height 0.3s;
  &.expanded { max-height: 500px; }
}

.expand-btn {
  color: #8899aa;
  font-size: 13px;
  text-align: center;
  padding-top: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

/* 箭头样式 */
.arrow-down {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-right: 2.5px solid #8899aa;
  border-bottom: 2.5px solid #8899aa;
  transform: rotate(45deg);
  margin-top: -4px;
  transition: transform 0.3s;
  &.up {
    transform: rotate(-135deg);
    margin-top: 4px;
  }
}

.arrow-right {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-right: 2.5px solid #8899aa;
  border-bottom: 2.5px solid #8899aa;
  transform: rotate(-45deg);
  margin-left: 4px;
}

/* 章节区域 */
.chapters-section {
  padding: 16px 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chapter-count {
  color: #fff;
  font-size: 16px;
  font-weight: 500;
}

.catalog-btn {
  background: none;
  border: none;
  color: #8899aa;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.chapters-preview {
  .chapter-item {
    display: flex;
    align-items: center;
    padding: 14px 0;
    border-bottom: 1px solid #1a1a25;
    cursor: pointer;
    &.current { .chapter-title { color: #8b5cf6; } }
  }
  
  .chapter-title {
    flex: 1;
    color: #ddd;
    font-size: 14px;
  }
  
  .new-tag {
    background: #f43f5e;
    color: #fff;
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 4px;
    margin-right: 8px;
  }
  
  .lock-icon { font-size: 14px; margin-right: 8px; }
}

/* Tab区域 */
.tabs-section {
  padding: 0 20px 20px;
}

.tabs-header {
  display: flex;
  justify-content: center;
  gap: 40px;
  padding: 20px 0;
  border-bottom: 1px solid #1a1a25;
}

.tab-item {
  color: #556677;
  font-size: 15px;
  cursor: pointer;
  padding-bottom: 8px;
  border-bottom: 2px solid transparent;
  &.active {
    color: #fff;
    border-bottom-color: #8b5cf6;
  }
}

.recommend-list {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  padding: 16px 0;
}

.recommend-item {
  cursor: pointer;
}

.recommend-cover-wrap {
  width: 100%;
  aspect-ratio: 3/4;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 8px;
}

.recommend-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.recommend-title {
  color: #ccc;
  font-size: 13px;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  margin: 0;
}

.comments-preview {
  padding: 16px 0;
}

.comment-item {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.comment-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
}

.comment-body { flex: 1; }
.comment-user { color: #8899aa; font-size: 13px; margin-bottom: 4px; }
.comment-text { color: #ddd; font-size: 14px; line-height: 1.5; }

.no-data {
  text-align: center;
  color: #556677;
  padding: 40px 0;
  font-size: 14px;
}

/* 底部操作栏 */
.action-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  background: #0a0a0f;
  border-top: 1px solid #1a1a25;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: 1px solid #333;
  color: #888;
  padding: 5px 14px;
  border-radius: 20px;
  cursor: pointer;
  &.active { color: #f43f5e; border-color: #f43f5e; }
}

.action-icon { width: 16px; height: 16px; }
.action-text { font-size: 12px; }

.read-btn {
  flex: 1;
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  border: none;
  color: #fff;
  padding: 8px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

/* 目录弹窗 */
.catalog-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  z-index: 200;
  display: flex;
  align-items: flex-end;
}

.catalog-panel {
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

.catalog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px 20px;
}

.catalog-title { 
  color: #fff; 
  font-size: 18px; 
  font-weight: 600; 
}

.catalog-header .sort-tabs {
  display: flex;
  align-items: center;
  gap: 4px;
}

.catalog-header .sort-tab {
  color: #556677;
  font-size: 14px;
  cursor: pointer;
  padding: 2px 4px;
}

.catalog-header .sort-tab.active {
  color: #a78bfa;
}

.catalog-header .sort-divider {
  color: #445566;
  font-size: 14px;
}

.catalog-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 20px 20px;
}

.catalog-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid rgba(100, 120, 150, 0.2);
  cursor: pointer;
  
  .catalog-chapter-title {
    color: #aaa;
    font-size: 15px;
  }
  
  &.current {
    .catalog-chapter-title {
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
}

.no-more-data {
  text-align: center;
  color: #445566;
  font-size: 13px;
  padding: 30px 0;
}

/* 文字阅读器 */
.reader-modal {
  position: fixed;
  inset: 0;
  background: #1a1a1a;
  z-index: 300;
  display: flex;
  flex-direction: column;
}

.reader-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #0d0d0d;
  border-bottom: 1px solid #222;
}

.chapter-name {
  color: #fff;
  font-size: 16px;
  flex: 1;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.setting-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
}

.settings-panel {
  background: #222;
  padding: 16px;
  border-bottom: 1px solid #333;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #fff;
}

.font-sizes {
  display: flex;
  gap: 8px;
  button {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border: 1px solid #444;
    background: #333;
    color: #fff;
    cursor: pointer;
    &.active { background: #8b5cf6; border-color: #8b5cf6; }
  }
}

.reader-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px 16px;
}

.chapter-content {
  color: #ddd;
  line-height: 2;
  text-align: justify;
}

.reader-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #0d0d0d;
  border-top: 1px solid #222;
}

.nav-btn {
  background: #333;
  border: none;
  color: #fff;
  padding: 10px 20px;
  border-radius: 20px;
  cursor: pointer;
  &:disabled { opacity: 0.5; cursor: not-allowed; }
}

.progress { color: #888; font-size: 13px; }

/* 有声小说播放器 */
.audio-player-modal {
  position: fixed;
  inset: 0;
  background: linear-gradient(180deg, #1a1a2e 0%, #0d0d0d 100%);
  z-index: 300;
  display: flex;
  flex-direction: column;
}

.player-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
}

.player-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
}

.cover-area {
  position: relative;
  margin-bottom: 30px;
}

.player-cover {
  width: 200px;
  height: 200px;
  border-radius: 16px;
  object-fit: cover;
  box-shadow: 0 10px 40px rgba(0,0,0,0.5);
}

.playing-animation {
  position: absolute;
  bottom: -20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 4px;
  span {
    width: 4px;
    height: 20px;
    background: #8b5cf6;
    border-radius: 2px;
    animation: wave 0.5s ease-in-out infinite;
    &:nth-child(2) { animation-delay: 0.1s; }
    &:nth-child(3) { animation-delay: 0.2s; }
    &:nth-child(4) { animation-delay: 0.3s; }
  }
}

@keyframes wave {
  0%, 100% { height: 10px; }
  50% { height: 25px; }
}

.audio-info { text-align: center; margin-bottom: 30px; }
.audio-title { color: #fff; font-size: 20px; margin-bottom: 8px; }
.audio-chapter { color: #888; font-size: 14px; }

.progress-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  max-width: 350px;
  margin-bottom: 30px;
}

.time { color: #888; font-size: 12px; min-width: 45px; &.current { text-align: right; } }

.progress-slider {
  flex: 1;
  height: 4px;
  -webkit-appearance: none;
  background: #333;
  border-radius: 2px;
  &::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 16px;
    height: 16px;
    background: #8b5cf6;
    border-radius: 50%;
    cursor: pointer;
  }
}

.player-controls {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
}

.control-btn {
  background: none;
  border: none;
  color: #fff;
  font-size: 24px;
  cursor: pointer;
  &:disabled { opacity: 0.3; }
  &.play-btn {
    width: 64px;
    height: 64px;
    background: #8b5cf6;
    border-radius: 50%;
    font-size: 28px;
  }
  &.rewind, &.forward { font-size: 14px; color: #888; }
}

.player-options {
  display: flex;
  gap: 16px;
}

.option-btn {
  background: #222;
  border: none;
  color: #aaa;
  padding: 8px 16px;
  border-radius: 16px;
  font-size: 13px;
  cursor: pointer;
  &.active { background: #8b5cf6; color: #fff; }
}

.player-chapters {
  background: #151515;
  border-top: 1px solid #222;
  max-height: 200px;
}

.chapters-header {
  padding: 12px 16px;
  color: #fff;
  font-size: 14px;
  border-bottom: 1px solid #222;
}

.chapters-scroll {
  max-height: 150px;
  overflow-y: auto;
}

.player-chapters .chapter-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 16px;
  color: #aaa;
  font-size: 14px;
  border-bottom: 1px solid #1a1a1a;
  cursor: pointer;
  &.active { color: #8b5cf6; background: rgba(139, 92, 246, 0.1); }
  &.locked { opacity: 0.5; }
}

/* 定时弹窗 */
.timer-modal {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 400;
}

.timer-content {
  background: #222;
  border-radius: 16px;
  padding: 24px;
  width: 280px;
  h3 { color: #fff; text-align: center; margin-bottom: 20px; }
}

.timer-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  button {
    background: #333;
    border: none;
    color: #fff;
    padding: 14px;
    border-radius: 8px;
    font-size: 15px;
    cursor: pointer;
    &:hover { background: #8b5cf6; }
  }
}

.back-btn-large {
  margin-top: 20px;
  padding: 12px 32px;
  background: #8b5cf6;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

/* 底部操作栏图标 */
.action-icon { width: 28px; height: 28px; }

/* 评论弹窗 */
.comments-modal { 
  position: fixed; 
  inset: 0; 
  background: rgba(0, 0, 0, 0.5); 
  z-index: 300; 
  display: flex; 
  align-items: flex-end; 
}
.comments-panel { 
  width: 100%; 
  max-height: 70vh; 
  background: #000; 
  border-radius: 16px 16px 0 0; 
  display: flex; 
  flex-direction: column; 
}
.drag-handle {
  width: 40px;
  height: 4px;
  background: #3a4a5a;
  border-radius: 2px;
  margin: 10px auto;
}
.comments-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  padding: 12px 20px; 
  border-bottom: 1px solid #222; 
}
.comment-count {
  color: #8899aa;
  font-size: 14px;
}
.sort-tabs {
  display: flex;
  align-items: center;
  gap: 8px;
}
.sort-tab {
  color: #556677;
  font-size: 14px;
  cursor: pointer;
  padding: 4px 8px;
}
.sort-tab.active {
  color: #fff;
}
.sort-divider {
  color: #334455;
  font-size: 12px;
}
.comments-list { 
  flex: 1; 
  overflow-y: auto; 
  padding: 16px 20px; 
  min-height: 200px; 
}
.no-comments { 
  text-align: center; 
  color: #556677; 
  padding: 40px 0; 
}
.no-more {
  text-align: center;
  color: #445566;
  font-size: 12px;
  padding: 20px 0;
}
.comments-list .comment-item { 
  display: flex; 
  gap: 12px; 
  margin-bottom: 20px; 
}
.comments-list .comment-avatar { 
  width: 40px; 
  height: 40px; 
  border-radius: 50%; 
  object-fit: cover;
  flex-shrink: 0;
}
.clickable {
  cursor: pointer;
}
.comments-list .comment-body { 
  flex: 1; 
  min-width: 0;
}
.comments-list .comment-user { 
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px; 
}
.comments-list .username {
  background: linear-gradient(90deg, #ffd700, #ffaa00);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 13px;
  font-weight: 500;
}
.vip-badge-sm {
  height: 18px;
  width: auto;
  object-fit: contain;
}
.comments-list .comment-text { 
  color: #fff; 
  font-size: 14px; 
  line-height: 1.5;
  word-break: break-word;
}
.comment-image {
  margin-top: 8px;
  cursor: pointer;
  
  img {
    max-width: 150px;
    max-height: 150px;
    border-radius: 8px;
    object-fit: cover;
  }
}
.comments-list .comment-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}
.comments-list .comment-time { 
  color: #556677; 
  font-size: 12px; 
}
.comment-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}
.comment-like, .comment-reply {
  color: #556677;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}
.comment-like.liked {
  color: #f43f5e;
}
.reply-icon {
  width: 16px;
  height: 16px;
  opacity: 0.6;
}

/* 官方公告样式 */
.official-announcement {
  .comment-user {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  
  .official-name {
    color: #ffd700;
    font-weight: 500;
  }
  
  .supreme-vip-icon {
    height: 18px;
    width: auto;
    object-fit: contain;
  }
  
  .official-text {
    color: #a78bfa;
  }
}

/* 评论输入触发区 */
.comment-input-trigger {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #1a1a1a;
  border-radius: 8px;
  margin: 0 16px 12px;
  cursor: pointer;
}
.input-placeholder {
  color: #556677;
  font-size: 14px;
}
.char-count {
  color: #445566;
  font-size: 12px;
}

/* 底部工具栏 */
.comment-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-top: 1px solid #222;
  background: #000;
}
.toolbar-left {
  display: flex;
  gap: 16px;
}
.toolbar-btn {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
}
.toolbar-icon {
  width: 28px;
  height: 28px;
}
.emoji-icon {
  font-size: 24px;
}
.toolbar-send {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
}
.send-icon {
  width: 28px;
  height: 28px;
}

/* 完整输入面板 */
.input-panel-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  z-index: 400;
  display: flex;
  align-items: flex-end;
}
.input-panel {
  width: 100%;
  background: #000;
  border-radius: 16px 16px 0 0;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}
.input-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid #222;
}
.cancel-btn {
  background: none;
  border: none;
  color: #8899aa;
  font-size: 14px;
  cursor: pointer;
}
.panel-title {
  color: #fff;
  font-size: 16px;
  font-weight: 500;
}
.submit-btn {
  background: linear-gradient(135deg, #8b5cf6, #a855f7);
  color: #fff;
  border: none;
  padding: 6px 16px;
  border-radius: 16px;
  font-size: 14px;
  cursor: pointer;
}
.submit-btn:disabled {
  background: #334455;
  color: #667788;
  cursor: not-allowed;
}
.input-panel-body {
  padding: 16px;
  flex: 1;
}
.full-input {
  width: 100%;
  min-height: 120px;
  background: transparent;
  border: none;
  color: #fff;
  font-size: 15px;
  line-height: 1.6;
  resize: none;
  outline: none;
}
.full-input::placeholder {
  color: #556677;
}
.char-counter {
  text-align: right;
  color: #556677;
  font-size: 12px;
  margin-top: 8px;
}
.image-preview {
  position: relative;
  display: inline-block;
  margin-top: 12px;
}
.image-preview img {
  max-width: 120px;
  max-height: 120px;
  border-radius: 8px;
  object-fit: cover;
}
.remove-image {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  background: #e53935;
  color: #fff;
  border: none;
  border-radius: 50%;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.input-panel-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-top: 1px solid #222;
}
.footer-left {
  display: flex;
  gap: 16px;
}
.footer-btn {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
}
.footer-icon {
  width: 28px;
  height: 28px;
}

/* 表情面板 */
.emoji-panel {
  padding: 12px 16px;
  background: #000;
  border-top: 1px solid #222;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
}
.emoji-item {
  font-size: 24px;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background 0.2s;
}
.emoji-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

/* 评论图片预览弹窗 */
.comment-image-preview-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.95);
  z-index: 500;
  display: flex;
  align-items: center;
  justify-content: center;
}
.comment-image-preview-content {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  
  img {
    max-width: 90vw;
    max-height: 90vh;
    object-fit: contain;
  }
}
.close-preview-btn {
  position: absolute;
  top: -40px;
  right: 0;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: #fff;
  font-size: 28px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
