<template>
  <div class="comment-input-bar">
    <!-- 非VIP提示 -->
    <div v-if="!isVip" class="vip-comment-tip" @click="$emit('openVip')">
      <span class="tip-icon">👑</span>
      <span class="tip-text">开通VIP即可发表评论</span>
      <span class="tip-btn">立即开通 ›</span>
    </div>
    
    <!-- VIP评论输入区 -->
    <div v-else class="input-area">
      <!-- 图片预览 -->
      <div v-if="imagePreview" class="image-preview">
        <img :src="imagePreview" alt="preview" />
        <span class="remove-image" @click="$emit('removeImage')">×</span>
      </div>
      
      <div class="input-row">
        <input 
          ref="inputRef"
          :value="modelValue"
          @input="$emit('update:modelValue', $event.target.value)"
          type="text"
          :placeholder="replyTarget ? `回复 @${replyTarget.user_name}` : '说点什么吧...'"
          @keyup.enter="$emit('submit')"
        />
        <div class="input-actions">
          <span v-if="replyTarget" class="cancel-btn" @click="$emit('cancelReply')">取消</span>
          <span class="emoji-btn" @click="$emit('toggleEmoji')">😊</span>
          <label class="image-btn">
            <input type="file" accept="image/*" @change="$emit('selectImage', $event)" hidden />
            🖼️
          </label>
          <span class="send-btn" @click="$emit('submit')" :class="{ disabled: submitting }">
            <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          </span>
        </div>
      </div>
      
      <!-- 表情选择器 -->
      <div v-if="showEmoji" class="emoji-picker">
        <div class="emoji-grid">
          <span 
            v-for="emoji in emojiList" 
            :key="emoji" 
            class="emoji-item" 
            @click="$emit('insertEmoji', emoji)"
          >
            {{ emoji }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  isVip: {
    type: Boolean,
    default: false
  },
  modelValue: {
    type: String,
    default: ''
  },
  replyTarget: {
    type: Object,
    default: null
  },
  imagePreview: {
    type: String,
    default: ''
  },
  showEmoji: {
    type: Boolean,
    default: false
  },
  submitting: {
    type: Boolean,
    default: false
  },
  emojiList: {
    type: Array,
    default: () => [
      '😀', '😂', '🤣', '😍', '🥰', '😘', '😋', '🤤',
      '😎', '🤩', '😏', '😒', '😔', '😢', '😭', '😤',
      '🥵', '🥶', '😱', '🤮', '💀', '👻', '👍', '👎',
      '👏', '🙏', '💪', '🔥', '❤️', '💔', '💯', '🎉'
    ]
  }
})

defineEmits([
  'update:modelValue',
  'submit',
  'cancelReply',
  'toggleEmoji',
  'selectImage',
  'removeImage',
  'insertEmoji',
  'openVip'
])

const inputRef = ref(null)

const focus = () => {
  inputRef.value?.focus()
}

defineExpose({ focus })
</script>

<style scoped>
.comment-input-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #1a1a1a;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding: 12px;
  z-index: 100;
}

.vip-comment-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.1), rgba(255, 183, 0, 0.1));
  border-radius: 8px;
  cursor: pointer;
}

.tip-icon {
  font-size: 16px;
}

.tip-text {
  color: #ffd700;
  font-size: 14px;
}

.tip-btn {
  color: #ffd700;
  font-weight: 600;
}

.input-area {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.image-preview {
  position: relative;
  width: 60px;
  height: 60px;
  border-radius: 8px;
  overflow: hidden;
}

.image-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-image {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 18px;
  height: 18px;
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  cursor: pointer;
}

.input-row {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 8px 12px;
}

.input-row input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: #fff;
  font-size: 14px;
}

.input-row input::placeholder {
  color: #888;
}

.input-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cancel-btn {
  color: #888;
  font-size: 12px;
  cursor: pointer;
}

.emoji-btn,
.image-btn {
  font-size: 18px;
  cursor: pointer;
  opacity: 0.8;
}

.emoji-btn:hover,
.image-btn:hover {
  opacity: 1;
}

.send-btn {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #ec4899, #f472b6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.send-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-btn svg {
  color: #fff;
}

.emoji-picker {
  background: #2a2a2a;
  border-radius: 12px;
  padding: 12px;
  margin-top: 8px;
}

.emoji-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 8px;
}

.emoji-item {
  font-size: 20px;
  text-align: center;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
}

.emoji-item:hover {
  background: rgba(255, 255, 255, 0.1);
}
</style>
