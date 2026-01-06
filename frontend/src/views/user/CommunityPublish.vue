<template>
  <div class="publish-page">
    <!-- 顶部导航 -->
    <div class="top-bar">
      <span class="back" @click="$router.back()">←</span>
      <span class="title">发布动态</span>
      <button class="publish-btn" :disabled="!canPublish || publishing" @click="publish">
        {{ publishing ? '发布中...' : '发布' }}
      </button>
    </div>

    <!-- 内容输入 -->
    <div class="content-area">
      <textarea 
        v-model="content" 
        placeholder="分享你的想法..."
        maxlength="2000"
      ></textarea>
      <div class="char-count">{{ content.length }}/2000</div>
    </div>

    <!-- 图片上传 -->
    <div class="images-section">
      <div class="images-grid">
        <div v-for="(img, idx) in images" :key="idx" class="image-item">
          <img :src="img" />
          <span class="remove" @click="removeImage(idx)">×</span>
        </div>
        <div v-if="images.length < 9" class="add-image" @click="triggerUpload">
          <span>+</span>
          <span class="text">添加图片</span>
        </div>
      </div>
      <input type="file" ref="fileInput" accept="image/*" multiple @change="handleUpload" hidden />
    </div>

    <!-- 话题选择 -->
    <div class="topics-section">
      <div class="section-title">添加话题</div>
      <div class="topics-list">
        <span 
          v-for="topic in topics" 
          :key="topic.id"
          :class="['topic-item', { selected: selectedTopics.includes(topic.id) }]"
          @click="toggleTopic(topic.id)"
        >
          #{{ topic.name }}
        </span>
      </div>
    </div>

    <!-- 可见性设置 -->
    <div class="visibility-section">
      <div class="section-title">谁可以看</div>
      <div class="visibility-options">
        <label v-for="opt in visibilityOptions" :key="opt.value">
          <input type="radio" v-model="visibility" :value="opt.value" />
          <span>{{ opt.label }}</span>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'

const router = useRouter()

const content = ref('')
const images = ref([])
const selectedTopics = ref([])
const visibility = ref('public')
const topics = ref([])
const publishing = ref(false)
const fileInput = ref(null)

const visibilityOptions = [
  { label: '公开', value: 'public' },
  { label: '仅关注', value: 'followers' },
  { label: '仅自己', value: 'private' }
]

const canPublish = computed(() => content.value.trim() || images.value.length > 0)

// 获取话题
const fetchTopics = async () => {
  try {
    const res = await api.get('/community/topics', { params: { page_size: 20 } })
    topics.value = res.data || []
  } catch (e) {
    console.error('获取话题失败', e)
  }
}

// 上传图片
const triggerUpload = () => fileInput.value?.click()

const handleUpload = async (e) => {
  const files = Array.from(e.target.files)
  if (!files.length) return

  for (const file of files) {
    if (images.value.length >= 9) break
    
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const res = await api.post('/community/upload/image', formData)
      images.value.push(res.data.url)
    } catch (err) {
      console.error('上传失败', err)
    }
  }
  e.target.value = ''
}

const removeImage = (idx) => images.value.splice(idx, 1)

const toggleTopic = (id) => {
  const idx = selectedTopics.value.indexOf(id)
  if (idx > -1) {
    selectedTopics.value.splice(idx, 1)
  } else if (selectedTopics.value.length < 3) {
    selectedTopics.value.push(id)
  }
}

// 发布
const publish = async () => {
  if (!canPublish.value || publishing.value) return
  
  publishing.value = true
  try {
    await api.post('/community/posts', {
      content: content.value,
      images: images.value,
      topic_ids: selectedTopics.value,
      visibility: visibility.value
    })
    router.replace('/user/community')
  } catch (e) {
    alert(e.response?.data?.detail || '发布失败')
  } finally {
    publishing.value = false
  }
}

onMounted(fetchTopics)
</script>

<style scoped>
.publish-page {
  min-height: 100vh;
  background: #0a0a0a;
}

.top-bar {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: #111;
  position: sticky;
  top: 0;
  z-index: 100;
}

.back {
  font-size: 24px;
  color: #fff;
  cursor: pointer;
  margin-right: 16px;
}

.title {
  flex: 1;
  color: #fff;
  font-size: 18px;
  font-weight: 500;
}

.publish-btn {
  padding: 8px 20px;
  background: linear-gradient(135deg, #ff4757, #ff6b81);
  border: none;
  border-radius: 20px;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
}

.publish-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.content-area {
  padding: 16px;
}

.content-area textarea {
  width: 100%;
  min-height: 150px;
  background: transparent;
  border: none;
  color: #fff;
  font-size: 16px;
  line-height: 1.6;
  resize: none;
  outline: none;
}

.char-count {
  text-align: right;
  color: #666;
  font-size: 12px;
}

.images-section {
  padding: 0 16px 16px;
}

.images-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.image-item {
  position: relative;
  aspect-ratio: 1;
}

.image-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 8px;
}

.image-item .remove {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  background: rgba(0,0,0,0.6);
  border-radius: 50%;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.add-image {
  aspect-ratio: 1;
  background: #1a1a1a;
  border: 1px dashed #333;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #666;
}

.add-image span:first-child {
  font-size: 32px;
}

.add-image .text {
  font-size: 12px;
  margin-top: 4px;
}

.topics-section, .visibility-section {
  padding: 16px;
  border-top: 1px solid #222;
}

.section-title {
  color: #888;
  font-size: 14px;
  margin-bottom: 12px;
}

.topics-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.topic-item {
  padding: 6px 14px;
  background: #222;
  border-radius: 20px;
  color: #aaa;
  font-size: 13px;
  cursor: pointer;
}

.topic-item.selected {
  background: linear-gradient(135deg, #ff4757, #ff6b81);
  color: #fff;
}

.visibility-options {
  display: flex;
  gap: 20px;
}

.visibility-options label {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #aaa;
  cursor: pointer;
}

.visibility-options input[type="radio"] {
  accent-color: #ff4757;
}
</style>
