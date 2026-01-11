<template>
  <!-- 评论弹窗 -->
  <div v-if="visible" class="comments-modal" @click.self="$emit('close')">
    <div class="comments-panel">
      <!-- 拖动条 -->
      <div class="drag-handle"></div>
      
      <!-- 头部 -->
      <div class="comments-header">
        <span class="comment-title">{{ replyTarget ? `回复 @${replyTarget.user?.nickname || replyTarget.user?.username}` : '发表评论' }}</span>
        <span class="close-btn" @click="$emit('close')">×</span>
      </div>
      
      <!-- 输入区域 -->
      <div class="input-area">
        <textarea 
          v-model="commentText" 
          class="comment-textarea" 
          :placeholder="replyTarget ? `回复 @${replyTarget.user?.nickname}...` : '在这里写下你想说的...'"
          maxlength="500"
          ref="textareaRef"
          rows="4"
        ></textarea>
        <div class="char-count">{{ commentText.length }}/500</div>
      </div>
      
      <!-- 图片预览 -->
      <div v-if="commentImage" class="image-preview-area">
        <div class="preview-item">
          <img :src="commentImagePreview" alt="预览" />
          <button class="remove-image" @click="removeCommentImage">×</button>
        </div>
      </div>
      
      <!-- 表情面板 -->
      <div v-if="showEmojiPanel" class="emoji-panel">
        <span v-for="emoji in emojis" :key="emoji" class="emoji-item" @click="insertEmoji(emoji)">{{ emoji }}</span>
      </div>
      
      <!-- 底部工具栏 -->
      <div class="comment-toolbar">
        <div class="toolbar-left">
          <button class="toolbar-btn" @click="triggerImageUpload">
            <img :src="picIcon" class="toolbar-icon" />
          </button>
          <button class="toolbar-btn" :class="{ active: showEmojiPanel }" @click="toggleEmojiPanel">
            <span class="emoji-icon">😊</span>
          </button>
        </div>
        <button class="toolbar-send" :disabled="!canSubmit" @click="submitComment">
          <img :src="sendIcon" class="send-icon" />
        </button>
      </div>
    </div>
  </div>
  
  <!-- 隐藏的文件上传 -->
  <input 
    type="file" 
    ref="imageInput" 
    accept="image/*" 
    style="display: none" 
    @change="handleImageSelect"
  />
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue'
import picIcon from '@/assets/icons/icon_pic_red.webp'
import sendIcon from '@/assets/icons/ic_send_red.webp'

const props = defineProps({
  visible: { type: Boolean, default: false },
  replyTarget: { type: Object, default: null }
})

const emit = defineEmits(['close', 'submit'])

const commentText = ref('')
const commentImage = ref(null)
const commentImagePreview = ref('')
const showEmojiPanel = ref(false)
const textareaRef = ref(null)
const imageInput = ref(null)

const emojis = [
  '😀', '😂', '🤣', '😍', '🥰', '😘', '😋', '🤤', '😎', '🤩', 
  '😏', '😒', '😔', '😢', '😭', '😤', '😡', '🤬', '😱', '😨', 
  '🥺', '😇', '🤗', '🤔', '🤫', '🤭', '👍', '👎', '👏', '🙏', 
  '💪', '❤️', '💔', '💯', '🔥', '✨', '🎉', '🎊', '😴', '🤮',
  '🥵', '🥶', '😈', '👻', '💀', '🤡', '👀', '💩', '🐶', '🐱'
]

const canSubmit = computed(() => {
  return commentText.value.trim() || commentImage.value
})

watch(() => props.visible, (val) => {
  if (val) {
    commentText.value = ''
    commentImage.value = null
    commentImagePreview.value = ''
    showEmojiPanel.value = false
    nextTick(() => textareaRef.value?.focus())
  }
})

const toggleEmojiPanel = () => {
  showEmojiPanel.value = !showEmojiPanel.value
}

const insertEmoji = (emoji) => {
  commentText.value += emoji
  textareaRef.value?.focus()
}

const triggerImageUpload = () => {
  imageInput.value?.click()
}

const handleImageSelect = (e) => {
  const file = e.target.files?.[0]
  if (file) {
    if (file.size > 5 * 1024 * 1024) {
      alert('图片大小不能超过5MB')
      return
    }
    commentImage.value = file
    commentImagePreview.value = URL.createObjectURL(file)
  }
  e.target.value = ''
}

const removeCommentImage = () => {
  if (commentImagePreview.value) {
    URL.revokeObjectURL(commentImagePreview.value)
  }
  commentImage.value = null
  commentImagePreview.value = ''
}

const submitComment = () => {
  if (!canSubmit.value) return
  
  emit('submit', {
    content: commentText.value,
    image: commentImage.value,
    replyTarget: props.replyTarget
  })
  
  commentText.value = ''
  removeCommentImage()
  showEmojiPanel.value = false
}
</script>

<style lang="scss" scoped>
.comments-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 9999;
  display: flex;
  align-items: flex-end;
}

.comments-panel {
  width: 100%;
  max-height: 80vh;
  background: #1a1a1a;
  border-radius: 16px 16px 0 0;
  padding-bottom: env(safe-area-inset-bottom);
  display: flex;
  flex-direction: column;
}

.drag-handle {
  width: 40px;
  height: 4px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
  margin: 12px auto;
  flex-shrink: 0;
}

.comments-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 16px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
  
  .comment-title {
    color: #fff;
    font-size: 16px;
    font-weight: 500;
  }
  
  .close-btn {
    font-size: 24px;
    color: rgba(255, 255, 255, 0.5);
    cursor: pointer;
    padding: 4px;
  }
}

.input-area {
  padding: 12px 16px;
  flex-shrink: 0;
  
  .comment-textarea {
    width: 100%;
    min-height: 100px;
    background: rgba(255, 255, 255, 0.05);
    border: none;
    border-radius: 12px;
    padding: 12px;
    color: #fff;
    font-size: 15px;
    line-height: 1.6;
    resize: none;
    outline: none;
    
    &::placeholder {
      color: rgba(255, 255, 255, 0.4);
    }
  }
  
  .char-count {
    text-align: right;
    color: rgba(255, 255, 255, 0.3);
    font-size: 12px;
    margin-top: 6px;
  }
}

.image-preview-area {
  padding: 0 16px 12px;
  flex-shrink: 0;
  
  .preview-item {
    position: relative;
    display: inline-block;
    
    img {
      width: 80px;
      height: 80px;
      object-fit: cover;
      border-radius: 8px;
    }
    
    .remove-image {
      position: absolute;
      top: -8px;
      right: -8px;
      width: 22px;
      height: 22px;
      background: rgba(0, 0, 0, 0.8);
      border: none;
      border-radius: 50%;
      color: #fff;
      font-size: 14px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
    }
  }
}

.emoji-panel {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.03);
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  max-height: 180px;
  overflow-y: auto;
  flex-shrink: 0;
  
  .emoji-item {
    font-size: 26px;
    padding: 6px;
    cursor: pointer;
    border-radius: 8px;
    transition: background 0.2s;
    
    &:hover, &:active {
      background: rgba(255, 255, 255, 0.1);
    }
  }
}

.comment-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
  
  .toolbar-left {
    display: flex;
    gap: 12px;
  }
  
  .toolbar-btn {
    background: none;
    border: none;
    padding: 8px;
    cursor: pointer;
    border-radius: 8px;
    transition: background 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    
    &:hover, &.active {
      background: rgba(255, 255, 255, 0.1);
    }
    
    .toolbar-icon {
      width: 26px;
      height: 26px;
      display: block;
    }
    
    .emoji-icon {
      font-size: 24px;
      display: block;
      line-height: 1;
      width: 26px;
      height: 26px;
      text-align: center;
    }
  }
  
  .toolbar-send {
    background: none;
    border: none;
    padding: 8px;
    cursor: pointer;
    opacity: 1;
    transition: opacity 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    
    &:disabled {
      opacity: 0.3;
    }
    
    .send-icon {
      width: 26px;
      height: 26px;
      display: block;
    }
  }
}
</style>
