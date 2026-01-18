<template>
  <div class="publish-page">
    <!-- 顶部导航 -->
    <div class="top-bar">
      <span class="back" @click="$router.back()">
        <svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
          <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
        </svg>
      </span>
      <span class="title">发布图文</span>
      <span class="rules" @click="showRules = true">规则</span>
    </div>

    <!-- 表单内容 -->
    <div class="form-content">
      <!-- 选择标签 -->
      <div class="form-item select-item" @click="showTopicPicker = true">
        <span class="hash">#</span>
        <span class="placeholder">{{ selectedTopic ? selectedTopic.name : '选择标签' }}</span>
        <span class="arrow">›</span>
      </div>

      <!-- 标题输入 -->
      <div class="form-item">
        <input type="text" v-model="title" placeholder="请填写标题" class="title-input" />
      </div>

      <!-- 内容输入 -->
      <div class="form-item content-item">
        <textarea 
          v-model="content" 
          placeholder="有趣的介绍能让你的逼格提高N个档次！..."
          rows="5"
        ></textarea>
        <span class="char-count">{{ content.length }}/300</span>
      </div>

      <!-- 添加图集 -->
      <div class="upload-section">
        <div class="section-header">
          <span class="section-title">添加图集</span>
          <span class="section-tip">最大每张1M以内 第一张默认为封面</span>
        </div>
        <div class="upload-grid">
          <div 
            v-for="(img, idx) in images" 
            :key="idx" 
            class="upload-item has-image"
          >
            <img :src="img.preview" class="preview-img" />
            <span class="remove-btn" @click="removeImage(idx)">×</span>
          </div>
          <div class="upload-item add-btn" @click="triggerUpload" v-if="images.length < 9">
            <span class="plus">+</span>
            <span class="text">上传图片</span>
          </div>
        </div>
        <input type="file" ref="fileInput" accept="image/*" multiple @change="handleFileSelect" style="display:none" />
      </div>
    </div>

    <!-- 底部发布按钮 -->
    <div class="bottom-bar">
      <button class="submit-btn" :disabled="!canSubmit || submitting" @click="handleSubmit">
        {{ submitting ? '发布中...' : '确定发布' }}
      </button>
    </div>

    <!-- 话题选择弹窗 -->
    <div class="topic-picker" v-if="showTopicPicker" @click.self="showTopicPicker = false">
      <div class="picker-content">
        <div class="picker-header">
          <span>选择话题</span>
          <span class="close" @click="showTopicPicker = false">×</span>
        </div>
        <div class="topic-list">
          <div 
            v-for="topic in topics" 
            :key="topic.id" 
            class="topic-item"
            :class="{ active: selectedTopic?.id === topic.id }"
            @click="selectTopic(topic)"
          >
            #{{ topic.name }}
          </div>
        </div>
      </div>
    </div>

    <!-- 规则弹窗 -->
    <div class="rules-modal" v-if="showRules" @click.self="showRules = false">
      <div class="rules-content">
        <h3>发布规则</h3>
        <ul>
          <li>图片大小不超过1M</li>
          <li>最多上传9张图片</li>
          <li>内容不超过300字</li>
          <li>禁止发布违规内容</li>
        </ul>
        <button @click="showRules = false">我知道了</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const router = useRouter()

const title = ref('')
const content = ref('')
const images = ref([])
const selectedTopic = ref(null)
const topics = ref([])
const showTopicPicker = ref(false)
const showRules = ref(false)
const submitting = ref(false)
const fileInput = ref(null)

const canSubmit = computed(() => {
  return title.value.trim() && content.value.trim()
})

const fetchTopics = async () => {
  try {
    // 获取所有二级分类话题
    const res = await api.get('/community/topics', { params: { level: 2, page_size: 50 } })
    topics.value = res.data || res || []
  } catch (e) {
    console.error('获取话题失败', e)
  }
}

const selectTopic = (topic) => {
  selectedTopic.value = topic
  showTopicPicker.value = false
}

const triggerUpload = () => {
  fileInput.value?.click()
}

const handleFileSelect = (e) => {
  const files = Array.from(e.target.files)
  const remaining = 9 - images.value.length
  const toAdd = files.slice(0, remaining)
  
  toAdd.forEach(file => {
    if (file.size > 1024 * 1024) {
      ElMessage.warning(`${file.name} 超过1M限制`)
      return
    }
    const reader = new FileReader()
    reader.onload = (ev) => {
      images.value.push({
        file,
        preview: ev.target.result
      })
    }
    reader.readAsDataURL(file)
  })
  e.target.value = ''
}

const removeImage = (idx) => {
  images.value.splice(idx, 1)
}

const handleSubmit = async () => {
  if (!canSubmit.value || submitting.value) return
  if (content.value.length > 300) {
    ElMessage.warning('内容不能超过300字')
    return
  }
  
  submitting.value = true
  try {
    // 先上传图片
    const uploadedUrls = []
    for (const img of images.value) {
      const formData = new FormData()
      formData.append('file', img.file)
      const res = await api.post('/community/upload/image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      uploadedUrls.push(res.data?.url || res.url)
    }
    
    // 发布帖子
    await api.post('/community/posts', {
      content: `${title.value}\n\n${content.value}`,
      images: uploadedUrls,
      topic_ids: selectedTopic.value ? [selectedTopic.value.id] : []
    })
    
    ElMessage.success('发布成功')
    router.back()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '发布失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchTopics()
})
</script>

<style lang="scss" scoped>
.publish-page {
  min-height: 100vh;
  background: #0a0a0a;
  padding-bottom: 100px;
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #0a0a0a;
  position: sticky;
  top: 0;
  z-index: 100;

  .back {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    cursor: pointer;
  }

  .title {
    color: #fff;
    font-size: 17px;
    font-weight: 500;
  }

  .rules {
    color: #888;
    font-size: 14px;
    cursor: pointer;
  }
}

.form-content {
  padding: 16px;
}

.form-item {
  background: #1a1a2e;
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 12px;

  &.select-item {
    display: flex;
    align-items: center;
    cursor: pointer;

    .hash {
      color: #a855f7;
      font-size: 16px;
      margin-right: 8px;
    }

    .placeholder {
      flex: 1;
      color: #888;
      font-size: 15px;
    }

    .arrow {
      color: #666;
      font-size: 20px;
    }
  }

  .title-input {
    width: 100%;
    background: transparent;
    border: none;
    color: #fff;
    font-size: 15px;
    outline: none;

    &::placeholder {
      color: #666;
    }
  }

  &.content-item {
    position: relative;

    textarea {
      width: 100%;
      background: transparent;
      border: none;
      color: #fff;
      font-size: 14px;
      line-height: 1.6;
      resize: none;
      outline: none;

      &::placeholder {
        color: #555;
      }
    }

    .char-count {
      position: absolute;
      bottom: 10px;
      right: 12px;
      color: #555;
      font-size: 12px;
    }
  }
}

.upload-section {
  margin-top: 24px;

  .section-header {
    display: flex;
    align-items: baseline;
    gap: 12px;
    margin-bottom: 16px;

    .section-title {
      color: #fff;
      font-size: 16px;
      font-weight: 500;
    }

    .section-tip {
      color: #666;
      font-size: 12px;
    }
  }

  .upload-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }

  .upload-item {
    width: 100px;
    height: 100px;
    border-radius: 8px;
    position: relative;

    &.add-btn {
      border: 1px dashed #444;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      gap: 8px;

      .plus {
        color: #666;
        font-size: 28px;
        line-height: 1;
      }

      .text {
        color: #666;
        font-size: 12px;
      }
    }

    &.has-image {
      .preview-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        border-radius: 8px;
      }

      .remove-btn {
        position: absolute;
        top: -8px;
        right: -8px;
        width: 20px;
        height: 20px;
        background: #ff4757;
        border-radius: 50%;
        color: #fff;
        font-size: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
      }
    }
  }
}

.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px 24px 30px;
  background: #0a0a0a;

  .submit-btn {
    width: 100%;
    padding: 14px;
    background: linear-gradient(135deg, #8b5cf6, #6366f1);
    border: none;
    border-radius: 25px;
    color: #fff;
    font-size: 16px;
    font-weight: 500;
    cursor: pointer;

    &:disabled {
      opacity: 0.5;
    }
  }
}

.topic-picker {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  z-index: 200;
  display: flex;
  align-items: flex-end;

  .picker-content {
    width: 100%;
    max-height: 60vh;
    background: #1a1a2e;
    border-radius: 16px 16px 0 0;
    padding: 16px;
  }

  .picker-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #fff;
    font-size: 16px;
    margin-bottom: 16px;

    .close {
      font-size: 24px;
      cursor: pointer;
      color: #888;
    }
  }

  .topic-list {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    max-height: 50vh;
    overflow-y: auto;
  }

  .topic-item {
    padding: 8px 16px;
    background: #252540;
    border-radius: 16px;
    color: #888;
    font-size: 14px;
    cursor: pointer;

    &.active {
      background: rgba(168, 85, 247, 0.2);
      color: #a855f7;
      border: 1px solid #a855f7;
    }
  }
}

.rules-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;

  .rules-content {
    width: 80%;
    background: #1a1a2e;
    border-radius: 12px;
    padding: 24px;

    h3 {
      color: #fff;
      font-size: 18px;
      margin: 0 0 16px;
      text-align: center;
    }

    ul {
      color: #aaa;
      font-size: 14px;
      line-height: 2;
      padding-left: 20px;
      margin: 0 0 20px;
    }

    button {
      width: 100%;
      padding: 12px;
      background: linear-gradient(135deg, #8b5cf6, #6366f1);
      border: none;
      border-radius: 20px;
      color: #fff;
      font-size: 14px;
      cursor: pointer;
    }
  }
}

// 响应式优化
@media (min-width: 768px) {
  .publish-page {
    max-width: 600px;
    margin: 0 auto;
  }
  
  .top-bar {
    max-width: 600px;
    left: 50%;
    transform: translateX(-50%);
  }
  
  .bottom-bar {
    max-width: 600px;
    left: 50%;
    transform: translateX(-50%);
  }
  
  .upload-grid {
    .upload-item {
      width: 110px;
      height: 110px;
    }
  }
}

@media (min-width: 1024px) {
  .publish-page {
    max-width: 700px;
  }
  
  .top-bar {
    max-width: 700px;
  }
  
  .bottom-bar {
    max-width: 700px;
  }
}

@media (hover: hover) {
  .upload-item.add-btn:hover {
    border-color: #666;
    background: rgba(255, 255, 255, 0.03);
  }
  
  .topic-item:hover {
    background: #303050;
  }
  
  .submit-btn:not(:disabled):hover {
    opacity: 0.9;
  }
}
</style>
