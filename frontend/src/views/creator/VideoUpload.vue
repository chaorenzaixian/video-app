<template>
  <div class="video-upload-page">
    <div class="nav-header">
      <button class="back-btn" @click="$router.push('/creator/videos')">‹</button>
      <h1>上传视频</h1>
      <div></div>
    </div>

    <div class="upload-form">
      <!-- 视频上传区域 -->
      <div class="upload-section">
        <div class="upload-area" v-if="!videoFile">
          <input type="file" accept="video/*" @change="handleVideoSelect" ref="videoInput" hidden>
          <div class="upload-placeholder" @click="$refs.videoInput.click()">
            <span class="upload-icon">📹</span>
            <p>点击上传视频</p>
            <p class="tip">支持 MP4、MOV 等格式，最大 2GB</p>
          </div>
        </div>
        <div class="upload-preview" v-else>
          <video :src="videoPreview" controls></video>
          <button class="remove-btn" @click="removeVideo">×</button>
        </div>
      </div>

      <!-- 封面上传 -->
      <div class="form-group">
        <label>视频封面</label>
        <div class="cover-upload">
          <input type="file" accept="image/*" @change="handleCoverSelect" ref="coverInput" hidden>
          <div class="cover-preview" v-if="coverPreview" @click="$refs.coverInput.click()">
            <img :src="coverPreview" alt="">
          </div>
          <div class="cover-placeholder" v-else @click="$refs.coverInput.click()">
            <span>📷</span>
            <p>上传封面</p>
          </div>
        </div>
      </div>

      <!-- 视频信息 -->
      <div class="form-group">
        <label>视频标题 *</label>
        <input v-model="form.title" placeholder="请输入视频标题" maxlength="50">
        <span class="char-count">{{ form.title.length }}/50</span>
      </div>

      <div class="form-group">
        <label>视频简介</label>
        <textarea v-model="form.description" placeholder="介绍一下视频内容" rows="4"></textarea>
      </div>

      <div class="form-group">
        <label>视频分类</label>
        <select v-model="form.category_id">
          <option value="">请选择分类</option>
          <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
        </select>
      </div>

      <!-- 付费设置 -->
      <div class="form-group">
        <label>付费设置</label>
        <div class="pay-options">
          <label class="radio-option" :class="{ active: form.pay_type === 'free' }">
            <input type="radio" v-model="form.pay_type" value="free">
            <span>免费</span>
          </label>
          <label class="radio-option" :class="{ active: form.pay_type === 'coins' }">
            <input type="radio" v-model="form.pay_type" value="coins">
            <span>付费</span>
          </label>
          <label class="radio-option" :class="{ active: form.pay_type === 'vip_free' }">
            <input type="radio" v-model="form.pay_type" value="vip_free">
            <span>VIP免费</span>
          </label>
        </div>
      </div>

      <!-- 非会员价格 -->
      <div class="form-group" v-if="form.pay_type !== 'free'">
        <label>非会员价格（金币）</label>
        <input type="number" v-model.number="form.coin_price" placeholder="非会员购买价格" min="1">
        <p class="input-hint">非VIP用户需要支付的金币数量</p>
      </div>

      <!-- VIP会员价格 -->
      <div class="form-group" v-if="form.pay_type === 'coins'">
        <label>VIP会员价格（金币）</label>
        <input type="number" v-model.number="form.vip_coin_price" placeholder="VIP会员优惠价格，0为免费" min="0">
        <p class="input-hint">VIP会员购买时的优惠价格，设为0则VIP免费观看</p>
      </div>

      <div class="form-group" v-if="form.pay_type === 'vip_free'">
        <label>VIP等级要求</label>
        <select v-model.number="form.vip_free_level">
          <option :value="1">普通VIP</option>
          <option :value="2">VIP1</option>
          <option :value="3">VIP2</option>
          <option :value="4">VIP3</option>
          <option :value="5">黄金至尊</option>
        </select>
      </div>

      <!-- 试看时长设置 -->
      <div class="form-group" v-if="form.pay_type !== 'free'">
        <label>试看时长（秒）</label>
        <input type="number" v-model.number="form.free_preview_seconds" placeholder="免费试看时长" min="0" max="300">
        <p class="input-hint">用户可免费试看的时长，设为0则不允许试看</p>
      </div>

      <!-- 提交按钮 -->
      <div class="submit-section">
        <button class="submit-btn" @click="handleSubmit" :disabled="isSubmitting">
          {{ isSubmitting ? '提交中...' : '提交审核' }}
        </button>
        <p class="submit-tip">视频将在审核通过后发布</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const router = useRouter()

const videoFile = ref(null)
const videoPreview = ref('')
const coverFile = ref(null)
const coverPreview = ref('')
const categories = ref([])
const isSubmitting = ref(false)

const form = ref({
  title: '',
  description: '',
  category_id: '',
  pay_type: 'free',
  coin_price: 0,
  vip_coin_price: 0,        // VIP会员价格
  vip_free_level: 1,
  free_preview_seconds: 15  // 试看时长，默认15秒
})

const handleVideoSelect = (e) => {
  const file = e.target.files[0]
  if (file) {
    if (file.size > 2 * 1024 * 1024 * 1024) {
      ElMessage.error('视频大小不能超过2GB')
      return
    }
    videoFile.value = file
    videoPreview.value = URL.createObjectURL(file)
  }
}

const removeVideo = () => {
  videoFile.value = null
  videoPreview.value = ''
}

const handleCoverSelect = (e) => {
  const file = e.target.files[0]
  if (file) {
    coverFile.value = file
    coverPreview.value = URL.createObjectURL(file)
  }
}

const fetchCategories = async () => {
  try {
    const res = await api.get('/videos/categories')
    categories.value = res.data
  } catch (error) {
    console.error('获取分类失败:', error)
  }
}

const handleSubmit = async () => {
  if (!form.value.title) {
    ElMessage.warning('请输入视频标题')
    return
  }
  
  isSubmitting.value = true
  try {
    // 这里实际应该先上传视频文件，再提交视频信息
    // 由于是演示，直接提交表单数据
    await api.post('/creator/videos/upload', form.value)
    ElMessage.success('视频已提交审核')
    router.push('/creator/videos')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '提交失败')
  } finally {
    isSubmitting.value = false
  }
}

onMounted(fetchCategories)
</script>

<style lang="scss" scoped>
.video-upload-page {
  min-height: 100vh;
  background: #0f0f1a;
  padding-bottom: 100px;
}

.nav-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: rgba(0, 0, 0, 0.3);
  
  .back-btn {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.1);
    border: none;
    color: #fff;
    font-size: 24px;
  }
  
  h1 { font-size: 18px; color: #fff; margin: 0; }
}

.upload-form {
  padding: 16px;
}

.upload-section {
  margin-bottom: 20px;
  
  .upload-area, .upload-preview {
    aspect-ratio: 16/9;
    border-radius: 12px;
    overflow: hidden;
  }
  
  .upload-placeholder {
    width: 100%;
    height: 100%;
    background: rgba(255,255,255,0.05);
    border: 2px dashed rgba(255,255,255,0.2);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    
    .upload-icon { font-size: 48px; }
    p { color: rgba(255,255,255,0.6); margin: 8px 0 0; }
    .tip { font-size: 12px; color: rgba(255,255,255,0.3); }
  }
  
  .upload-preview {
    position: relative;
    
    video { width: 100%; height: 100%; object-fit: cover; }
    
    .remove-btn {
      position: absolute;
      top: 8px;
      right: 8px;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: rgba(0,0,0,0.7);
      border: none;
      color: #fff;
      font-size: 20px;
    }
  }
}

.form-group {
  margin-bottom: 20px;
  position: relative;
  
  label {
    display: block;
    color: rgba(255,255,255,0.8);
    font-size: 14px;
    margin-bottom: 8px;
  }
  
  input, textarea, select {
    width: 100%;
    padding: 12px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    color: #fff;
    font-size: 14px;
    
    &::placeholder { color: rgba(255,255,255,0.3); }
  }
  
  .char-count {
    position: absolute;
    right: 12px;
    top: 42px;
    font-size: 12px;
    color: rgba(255,255,255,0.3);
  }
  
  .input-hint {
    margin-top: 6px;
    font-size: 12px;
    color: rgba(255,255,255,0.4);
  }
}

.cover-upload {
  .cover-placeholder, .cover-preview {
    width: 120px;
    height: 80px;
    border-radius: 8px;
    overflow: hidden;
    cursor: pointer;
  }
  
  .cover-placeholder {
    background: rgba(255,255,255,0.05);
    border: 1px dashed rgba(255,255,255,0.2);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    
    span { font-size: 24px; }
    p { font-size: 12px; color: rgba(255,255,255,0.5); margin: 4px 0 0; }
  }
  
  .cover-preview img { width: 100%; height: 100%; object-fit: cover; }
}

.pay-options {
  display: flex;
  gap: 12px;
  
  .radio-option {
    flex: 1;
    padding: 12px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    text-align: center;
    cursor: pointer;
    
    input { display: none; }
    span { color: rgba(255,255,255,0.6); }
    
    &.active {
      border-color: #667eea;
      background: rgba(102, 126, 234, 0.1);
      span { color: #667eea; }
    }
  }
}

.submit-section {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  background: linear-gradient(transparent, #0f0f1a 30%);
  
  .submit-btn {
    width: 100%;
    padding: 14px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    border: none;
    border-radius: 12px;
    color: #fff;
    font-size: 16px;
    font-weight: bold;
    
    &:disabled { opacity: 0.5; }
  }
  
  .submit-tip {
    text-align: center;
    font-size: 12px;
    color: rgba(255,255,255,0.4);
    margin-top: 8px;
  }
}
</style>
