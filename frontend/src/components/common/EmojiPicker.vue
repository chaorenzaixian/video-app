<template>
  <div class="emoji-picker" v-if="visible">
    <div class="emoji-tabs">
      <span 
        v-for="(tab, idx) in tabs" 
        :key="idx"
        :class="['tab-item', { active: activeTab === idx }]"
        @click="activeTab = idx"
      >
        {{ tab.icon }}
      </span>
    </div>
    <div class="emoji-grid">
      <span 
        v-for="emoji in currentEmojis" 
        :key="emoji" 
        class="emoji-item"
        @click="selectEmoji(emoji)"
      >
        {{ emoji }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['select'])

const activeTab = ref(0)

// 表情分类
const tabs = [
  {
    icon: '😀',
    name: '表情',
    emojis: [
      '😀', '😂', '🤣', '😊', '😍', '🥰', '😘', '😜', '🤪', '😎',
      '🥳', '😇', '🤩', '😋', '😛', '🤤', '😏', '😒', '😔', '😢',
      '😭', '😤', '😠', '🤬', '😱', '😰', '😥', '🤧', '😷', '🤒',
      '🤕', '🤢', '🤮', '🥴', '😵', '🤯', '🤠', '🥸', '😈', '👿'
    ]
  },
  {
    icon: '👍',
    name: '手势',
    emojis: [
      '👍', '👎', '👏', '🙏', '💪', '🤝', '✌️', '🤞', '🤟', '🤘',
      '👌', '🤌', '👈', '👉', '👆', '👇', '☝️', '✋', '🤚', '🖐️',
      '🖖', '👋', '🤙', '💅', '🖕', '✊', '👊', '🤛', '🤜', '👐'
    ]
  },
  {
    icon: '❤️',
    name: '符号',
    emojis: [
      '❤️', '💔', '💯', '🔥', '✨', '🎉', '🎊', '💎', '🏆', '🥇',
      '⭐', '🌟', '💫', '🌈', '☀️', '🌙', '⚡', '💥', '💢', '💦',
      '💤', '🎵', '🎶', '💰', '💵', '🎁', '🎀', '🏅', '🎯', '🔔'
    ]
  },
  {
    icon: '🐱',
    name: '动物',
    emojis: [
      '🐱', '🐶', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐨', '🐯',
      '🦁', '🐮', '🐷', '🐸', '🐵', '🐔', '🐧', '🐦', '🐤', '🦆',
      '🦅', '🦉', '🦇', '🐺', '🐗', '🐴', '🦄', '🐝', '🐛', '🦋'
    ]
  },
  {
    icon: '🍔',
    name: '食物',
    emojis: [
      '🍔', '🍕', '🍟', '🌭', '🍿', '🧂', '🥓', '🥚', '🍳', '🧇',
      '🥞', '🧈', '🍞', '🥐', '🥖', '🥨', '🧀', '🥗', '🥙', '🥪',
      '🌮', '🌯', '🫔', '🥫', '🍝', '🍜', '🍲', '🍛', '🍣', '🍱'
    ]
  }
]

// 当前分类的表情
const currentEmojis = computed(() => {
  return tabs[activeTab.value]?.emojis || []
})

// 选择表情
const selectEmoji = (emoji) => {
  emit('select', emoji)
}
</script>

<style lang="scss" scoped>
.emoji-picker {
  background: #1a1a2e;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.emoji-tabs {
  display: flex;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 8px;
  gap: 4px;
  
  .tab-item {
    flex: 1;
    text-align: center;
    padding: 8px;
    font-size: 18px;
    cursor: pointer;
    border-radius: 8px;
    transition: background 0.2s;
    
    &:hover {
      background: rgba(255, 255, 255, 0.1);
    }
    
    &.active {
      background: rgba(139, 92, 246, 0.3);
    }
  }
}

.emoji-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 4px;
  padding: 12px;
  max-height: 200px;
  overflow-y: auto;
  
  &::-webkit-scrollbar {
    width: 4px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 2px;
  }
  
  .emoji-item {
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    padding: 6px;
    cursor: pointer;
    border-radius: 6px;
    transition: all 0.2s;
    
    &:hover {
      background: rgba(255, 255, 255, 0.1);
      transform: scale(1.2);
    }
    
    &:active {
      transform: scale(0.9);
    }
  }
}

// 移动端适配
@media (max-width: 480px) {
  .emoji-grid {
    grid-template-columns: repeat(6, 1fr);
    
    .emoji-item {
      font-size: 20px;
      padding: 4px;
    }
  }
}
</style>
