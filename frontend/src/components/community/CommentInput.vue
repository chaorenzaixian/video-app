<template>
  <div class="comment-modal" v-if="visible" @click.self="$emit('close')">
    <div class="comment-modal-content">
      <div class="modal-header">
        <span>{{ replyTarget ? `回复 @${replyTarget.user?.nickname || replyTarget.user?.username}` : '发表评论' }}</span>
        <span class="close-btn" @click="$emit('close')">×</span>
      </div>
      <textarea 
        ref="textareaRef"
        v-model="text" 
        placeholder="说点什么..."
        rows="4"
      ></textarea>
      <div class="modal-footer">
        <button class="cancel-btn" @click="$emit('close')">取消</button>
        <button class="submit-btn" @click="submit" :disabled="!text.trim() || submitting">
          {{ submitting ? '发送中...' : '发送' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  replyTarget: { type: Object, default: null }
})

const emit = defineEmits(['close', 'submit'])

const text = ref('')
const submitting = ref(false)
const textareaRef = ref(null)

watch(() => props.visible, (val) => {
  if (val) {
    text.value = ''
    nextTick(() => textareaRef.value?.focus())
  }
})

const submit = async () => {
  if (!text.value.trim() || submitting.value) return
  submitting.value = true
  try {
    emit('submit', {
      content: text.value,
      replyTarget: props.replyTarget
    })
    text.value = ''
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
.comment-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: flex-end;
  z-index: 200;

  .comment-modal-content {
    width: 100%;
    background: #1a1a1a;
    border-radius: 16px 16px 0 0;
    padding: 16px;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    color: #fff;
    font-size: 16px;

    .close-btn {
      font-size: 24px;
      cursor: pointer;
      color: #888;
    }
  }

  textarea {
    width: 100%;
    background: #222;
    border: none;
    border-radius: 8px;
    padding: 12px;
    color: #fff;
    font-size: 14px;
    resize: none;
    outline: none;

    &::placeholder {
      color: #666;
    }
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 16px;

    button {
      padding: 10px 24px;
      border-radius: 20px;
      font-size: 14px;
      cursor: pointer;
    }

    .cancel-btn {
      background: #333;
      border: none;
      color: #888;
    }

    .submit-btn {
      background: linear-gradient(135deg, #a855f7, #7c3aed);
      border: none;
      color: #fff;

      &:disabled {
        opacity: 0.5;
      }
    }
  }
}
</style>
