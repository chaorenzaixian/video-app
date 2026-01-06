<template>
  <div class="short-upload-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="handleBack">×</div>
      <h1 class="page-title">发布短视频</h1>
      <button 
        class="publish-btn" 
        :disabled="!canPublish || uploading"
        @click="handlePublish"
      >
        {{ uploading ? '发布中...' : '发布' }}
      </button>
    </header>

    <div class="upload-content">
      <!-- 视频上传区 -->
      <div class="video-upload-section">
        <div class="upload-area" v-if="!videoFile" @click="triggerUpload">
          <input 
            type="file" 
            ref="fileInput"
            accept="video/*"
            @change="handleFileSelect"
            hidden
          />
          <div class="upload-icon">📹</div>
          <p class="upload-text">点击上传短视频</p>
          <p class="upload-hint">支持 MP4、MOV 格式，最大800MB</p>
        </div>

        <div class="video-preview" v-else>
          <video 
            ref="previewVideo"
            :src="videoPreviewUrl"
            controls
            playsinline
          />
          <div class="video-info">
            <span class="duration">{{ formatDuration(videoDuration) }}</span>
            <span class="size">{{ formatSize(videoFile.size) }}</span>
          </div>
          <button class="remove-btn" @click="removeVideo">×</button>
        </div>
      </div>

      <!-- 封面选择 -->
      <div class="cover-section">
        <div class="section-header">
          <span class="label">选择封面</span>
          <span class="hint">从视频中截取6帧供选择</span>
        </div>
        <div class="cover-options">
          <div 
            v-for="(frame, index) in videoFrames" 
            :key="index"
            :class="['cover-item', { active: selectedCoverIndex === index }]"
            @click="selectCover(index)"
          >
            <img :src="frame" alt="" />
          </div>
        </div>
      </div>

      <!-- 视频信息 -->
      <div class="info-section">
        <div class="form-group">
          <label>标题</label>
          <input 
            type="text" 
            v-model="form.title"
            placeholder="添加标题，让更多人看到你的作品"
            maxlength="100"
          />
          <span class="char-count">{{ form.title.length }}/100</span>
        </div>

        <div class="form-group">
          <label>描述</label>
          <textarea 
            v-model="form.description"
            placeholder="添加描述（选填）"
            maxlength="500"
            rows="3"
          ></textarea>
          <span class="char-count">{{ form.description.length }}/500</span>
        </div>

        <div class="form-group">
          <label>分类</label>
          <select v-model="form.short_category_id">
            <option :value="null">选择分类</option>
            <option v-for="cat in categories" :key="cat.id" :value="cat.id">
              {{ cat.icon }} {{ cat.name }}
            </option>
          </select>
        </div>
      </div>

      <!-- 付费设置 -->
      <div class="pay-section">
        <div class="section-header">
          <span class="label">付费设置</span>
        </div>
        <div class="pay-options">
          <label class="pay-option">
            <input type="radio" v-model="form.pay_type" value="free" />
            <span class="option-text">免费</span>
          </label>
          <label class="pay-option">
            <input type="radio" v-model="form.pay_type" value="vip_free" />
            <span class="option-text">会员免费，非会员付费</span>
          </label>
        </div>
        <div class="price-input" v-if="form.pay_type === 'vip_free'">
          <label>非会员价格</label>
          <input 
            type="number" 
            v-model.number="form.coin_price"
            placeholder="输入金币数量"
            min="1"
            max="9999"
          />
          <span class="unit">金币</span>
        </div>
      </div>
    </div>

    <!-- 上传进度 -->
    <div class="upload-progress" v-if="uploading">
      <div class="progress-bar">
        <div class="progress" :style="{ width: uploadProgress + '%' }"></div>
      </div>
      <span class="progress-text">上传中 {{ uploadProgress }}%</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'

const router = useRouter()

// 文件相关
const fileInput = ref(null)
const previewVideo = ref(null)
const videoFile = ref(null)
const videoPreviewUrl = ref('')
const videoDuration = ref(0)
const videoFrames = ref([])
const selectedCoverIndex = ref(0)

// 表单数据
const form = ref({
  title: '',
  description: '',
  short_category_id: null,  // 使用短视频分类
  pay_type: 'free',
  coin_price: 10
})

// 分类列表
const categories = ref([])

// 上传状态
const uploading = ref(false)
const uploadProgress = ref(0)

// 是否可以发布
const canPublish = computed(() => {
  return videoFile.value && form.value.title.trim()
})

// 触发上传
const triggerUpload = () => {
  fileInput.value?.click()
}

// 处理文件选择
const handleFileSelect = async (e) => {
  const file = e.target.files[0]
  if (!file) return

  // 验证文件类型
  if (!file.type.startsWith('video/')) {
    ElMessage.error('请选择视频文件')
    return
  }

  // 验证文件大小 (最大800MB)
  if (file.size > 800 * 1024 * 1024) {
    ElMessage.error('视频文件不能超过800MB')
    return
  }

  videoFile.value = file
  videoPreviewUrl.value = URL.createObjectURL(file)

  // 等待视频加载完成后获取时长和帧
  setTimeout(() => {
    if (previewVideo.value) {
      previewVideo.value.onloadedmetadata = () => {
        videoDuration.value = previewVideo.value.duration
        
        // 提取视频帧作为封面选项
        extractVideoFrames()
      }
    }
  }, 100)
}

// 提取视频帧
const extractVideoFrames = () => {
  const video = previewVideo.value
  if (!video) return

  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  
  const frames = []
  const frameCount = 6
  const interval = video.duration / (frameCount + 1)

  const captureFrame = (time, index) => {
    return new Promise((resolve) => {
      video.currentTime = time
      video.onseeked = () => {
        canvas.width = video.videoWidth
        canvas.height = video.videoHeight
        ctx.drawImage(video, 0, 0)
        frames[index] = canvas.toDataURL('image/jpeg', 0.8)
        resolve()
      }
    })
  }

  const captureAll = async () => {
    for (let i = 0; i < frameCount; i++) {
      await captureFrame((i + 1) * interval, i)
    }
    videoFrames.value = frames
    video.currentTime = 0
  }

  captureAll()
}

// 选择封面
const selectCover = (index) => {
  selectedCoverIndex.value = index
}

// 移除视频
const removeVideo = () => {
  if (videoPreviewUrl.value) {
    URL.revokeObjectURL(videoPreviewUrl.value)
  }
  videoFile.value = null
  videoPreviewUrl.value = ''
  videoDuration.value = 0
  videoFrames.value = []
  selectedCoverIndex.value = 0
  fileInput.value.value = ''
}

// 格式化时长
const formatDuration = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 格式化文件大小
const formatSize = (bytes) => {
  if (bytes < 1024 * 1024) {
    return (bytes / 1024).toFixed(1) + ' KB'
  }
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// 获取分类 - 使用独立的短视频分类API
const fetchCategories = async () => {
  try {
    // 优先使用新的独立短视频分类API
    const res = await api.get('/shorts/categories')
    categories.value = res.data || []
  } catch (error) {
    // 回退到旧的分类API
    try {
      const res = await api.get('/videos/categories/by-type', {
        params: { category_type: 'short' }
      })
      categories.value = res.data || []
    } catch (e) {
      console.error('获取分类失败:', e)
    }
  }
}

// 发布
const handlePublish = async () => {
  if (!canPublish.value || uploading.value) return

  uploading.value = true
  uploadProgress.value = 0

  try {
    // 1. 上传视频文件
    const videoFormData = new FormData()
    videoFormData.append('file', videoFile.value)
    
    const videoRes = await api.post('/videos/upload-file', videoFormData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        uploadProgress.value = Math.round((e.loaded / e.total) * 80)
      }
    })

    const videoUrl = videoRes.data?.url || videoRes.url

    // 2. 上传封面
    let coverUrl = ''
    const coverData = videoFrames.value[selectedCoverIndex.value]
    if (coverData) {
      // 将 base64 转为 Blob
      const coverBlob = await fetch(coverData).then(r => r.blob())
      const coverFormData = new FormData()
      coverFormData.append('file', coverBlob, 'cover.jpg')
      
      const coverRes = await api.post('/ads/upload/image', coverFormData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      coverUrl = coverRes.data?.url || coverRes.url
    }

    uploadProgress.value = 90

    // 3. 创建短视频记录
    const videoData = {
      title: form.value.title,
      description: form.value.description,
      short_category_id: form.value.short_category_id,
      original_url: videoUrl,
      cover_url: coverUrl,
      duration: videoDuration.value,
      is_short: true,
      pay_type: form.value.pay_type === 'vip_free' ? 'coins' : 'free',
      coin_price: form.value.pay_type === 'vip_free' ? form.value.coin_price : 0,
      is_vip_only: form.value.pay_type === 'vip_free'
    }

    await api.post('/creator/videos', videoData)

    uploadProgress.value = 100
    ElMessage.success('发布成功！')
    
    setTimeout(() => {
      router.push('/shorts')
    }, 500)
  } catch (error) {
    console.error('发布失败:', error)
    ElMessage.error(error.response?.data?.detail || '发布失败，请重试')
  } finally {
    uploading.value = false
  }
}

// 返回确认
const handleBack = async () => {
  if (videoFile.value || form.value.title) {
    try {
      await ElMessageBox.confirm('确定要放弃编辑吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
      router.back()
    } catch {
      // 取消
    }
  } else {
    router.back()
  }
}

onMounted(() => {
  fetchCategories()
})
</script>

<style lang="scss" scoped>
.short-upload-page {
  min-height: 100vh;
  background: #0d0d15;
  color: #fff;
}

// 顶部导航
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  padding-top: calc(env(safe-area-inset-top) + 16px);
  background: #1a1a2e;
  
  .back-btn {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    color: #fff;
    cursor: pointer;
  }
  
  .page-title {
    font-size: 17px;
    font-weight: 600;
    margin: 0;
  }
  
  .publish-btn {
    background: linear-gradient(135deg, #a855f7, #7c3aed);
    border: none;
    padding: 8px 20px;
    border-radius: 20px;
    color: #fff;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    
    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
}

.upload-content {
  padding: 20px;
}

// 视频上传区
.video-upload-section {
  margin-bottom: 24px;
  
  .upload-area {
    background: rgba(255,255,255,0.05);
    border: 2px dashed rgba(255,255,255,0.2);
    border-radius: 16px;
    padding: 60px 20px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s;
    
    &:hover {
      border-color: #a855f7;
      background: rgba(168,85,247,0.1);
    }
    
    .upload-icon {
      font-size: 48px;
      margin-bottom: 16px;
    }
    
    .upload-text {
      font-size: 16px;
      color: #fff;
      margin-bottom: 8px;
    }
    
    .upload-hint {
      font-size: 13px;
      color: rgba(255,255,255,0.5);
    }
  }
  
  .video-preview {
    position: relative;
    border-radius: 16px;
    overflow: hidden;
    
    video {
      width: 100%;
      max-height: 300px;
      object-fit: contain;
      background: #000;
    }
    
    .video-info {
      position: absolute;
      bottom: 12px;
      left: 12px;
      display: flex;
      gap: 12px;
      
      span {
        background: rgba(0,0,0,0.7);
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
      }
    }
    
    .remove-btn {
      position: absolute;
      top: 12px;
      right: 12px;
      width: 32px;
      height: 32px;
      background: rgba(0,0,0,0.7);
      border: none;
      border-radius: 50%;
      color: #fff;
      font-size: 18px;
      cursor: pointer;
    }
  }
}

// 封面选择
.cover-section {
  margin-bottom: 24px;
  
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    
    .label {
      font-size: 15px;
      font-weight: 500;
    }
    
    .hint {
      font-size: 12px;
      color: rgba(255,255,255,0.5);
    }
  }
  
  .cover-options {
    display: flex;
    gap: 10px;
    overflow-x: auto;
    padding-bottom: 8px;
    
    &::-webkit-scrollbar {
      display: none;
    }
    
    .cover-item {
      flex-shrink: 0;
      width: 80px;
      height: 120px;
      border-radius: 8px;
      overflow: hidden;
      cursor: pointer;
      border: 2px solid transparent;
      
      &.active {
        border-color: #a855f7;
      }
      
      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
      
      &.upload {
        background: rgba(255,255,255,0.1);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        
        .plus {
          font-size: 24px;
          margin-bottom: 4px;
        }
        
        .text {
          font-size: 12px;
          color: rgba(255,255,255,0.6);
        }
      }
    }
  }
}

// 信息表单
.info-section {
  margin-bottom: 24px;
  
  .form-group {
    position: relative;
    margin-bottom: 20px;
    
    label {
      display: block;
      font-size: 14px;
      color: rgba(255,255,255,0.7);
      margin-bottom: 8px;
    }
    
    input, textarea, select {
      width: 100%;
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 10px;
      padding: 12px 16px;
      color: #fff;
      font-size: 15px;
      
      &::placeholder {
        color: rgba(255,255,255,0.4);
      }
      
      &:focus {
        border-color: #a855f7;
        outline: none;
      }
    }
    
    textarea {
      resize: none;
    }
    
    select {
      appearance: none;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23fff' d='M2 4l4 4 4-4z'/%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: right 12px center;
    }
    
    .char-count {
      position: absolute;
      right: 12px;
      bottom: 12px;
      font-size: 12px;
      color: rgba(255,255,255,0.4);
    }
  }
}

// 付费设置
.pay-section {
  background: rgba(255,255,255,0.05);
  border-radius: 12px;
  padding: 16px;
  
  .section-header {
    margin-bottom: 16px;
    
    .label {
      font-size: 15px;
      font-weight: 500;
    }
  }
  
  .pay-options {
    display: flex;
    gap: 20px;
    margin-bottom: 16px;
    
    .pay-option {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      
      input {
        accent-color: #a855f7;
      }
      
      .option-text {
        font-size: 14px;
      }
    }
  }
  
  .price-input {
    display: flex;
    align-items: center;
    gap: 12px;
    
    label {
      font-size: 14px;
      color: rgba(255,255,255,0.7);
      flex-shrink: 0;
    }
    
    input {
      flex: 1;
      max-width: 120px;
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 8px;
      padding: 10px 14px;
      color: #fff;
      font-size: 15px;
      
      &:focus {
        border-color: #a855f7;
        outline: none;
      }
    }
    
    .unit {
      font-size: 14px;
      color: rgba(255,255,255,0.6);
    }
  }
}

// 上传进度
.upload-progress {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #1a1a2e;
  padding: 16px 20px;
  padding-bottom: calc(env(safe-area-inset-bottom) + 16px);
  
  .progress-bar {
    height: 4px;
    background: rgba(255,255,255,0.1);
    border-radius: 2px;
    overflow: hidden;
    margin-bottom: 8px;
    
    .progress {
      height: 100%;
      background: linear-gradient(90deg, #a855f7, #ec4899);
      transition: width 0.3s;
    }
  }
  
  .progress-text {
    font-size: 13px;
    color: rgba(255,255,255,0.7);
    text-align: center;
    display: block;
  }
}
</style>




