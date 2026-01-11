<template>
  <div class="video-upload-page">
    <el-card>
      <template #header>
        <span>上传视频</span>
      </template>
      
      <el-form 
        ref="formRef"
        :model="form" 
        :rules="rules" 
        label-width="100px"
        style="max-width: 800px"
      >
        <el-form-item label="视频文件" prop="file" required>
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-exceed="handleExceed"
            :before-upload="beforeUpload"
            accept="video/*"
            drag
          >
            <div v-if="!form.file" class="upload-area">
              <el-icon class="upload-icon"><UploadFilled /></el-icon>
              <div class="upload-text">拖拽视频到此处，或 <em>点击上传</em></div>
              <div class="upload-tip">支持 MP4、WebM、AVI、MOV、MKV 格式，最大 5GB</div>
            </div>
            <div v-else class="file-info">
              <el-icon size="32" color="#6366f1"><VideoPlay /></el-icon>
              <div class="file-details">
                <div class="file-name">{{ form.file.name }}</div>
                <div class="file-size">{{ formatFileSize(form.file.size) }}</div>
              </div>
              <el-button text type="danger" @click.stop="removeFile">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </el-upload>
        </el-form-item>
        
        <!-- 视频封面设置 -->
        <el-form-item label="视频封面">
          <div class="cover-section">
            <div class="cover-mode-switch">
              <el-radio-group v-model="coverMode" size="small">
                <el-radio-button label="auto">🤖 系统智能选择</el-radio-button>
                <el-radio-button label="select">🎯 手动选择封面</el-radio-button>
                <el-radio-button label="upload">📤 上传自定义</el-radio-button>
              </el-radio-group>
            </div>
            
            <!-- 手动选择封面 -->
            <div v-if="coverMode === 'select'" class="cover-candidates">
              <div v-if="!form.file" class="cover-hint">
                <el-icon><InfoFilled /></el-icon>
                请先选择视频文件
              </div>
              <div v-else-if="extractingCovers" class="cover-loading">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>正在提取视频帧...</span>
              </div>
              <div v-else-if="coverCandidates.length === 0" class="cover-actions">
                <el-button type="primary" @click="extractCovers" :loading="extractingCovers">
                  <el-icon><Picture /></el-icon>
                  提取候选封面
                </el-button>
                <span class="hint-text">从视频中截取6个时间点的画面供您选择</span>
              </div>
              <div v-else class="cover-grid">
                <div 
                  v-for="(cover, index) in coverCandidates" 
                  :key="index"
                  class="cover-item"
                  :class="{ selected: selectedCover === cover.url }"
                  @click="selectCover(cover.url)"
                >
                  <img :src="getFullUrl(cover.url)" :alt="`封面候选 ${index + 1}`" />
                  <div class="cover-info">
                    <span class="time">{{ formatTime(cover.time_point) }}</span>
                    <span class="score" v-if="cover.score">{{ cover.score.toFixed(0) }}分</span>
                  </div>
                  <div class="selected-badge" v-if="selectedCover === cover.url">
                    <el-icon><Check /></el-icon>
                  </div>
                  <div class="best-badge" v-if="index === 0">
                    <span>AI推荐</span>
                  </div>
                </div>
                <div class="cover-item add-more" @click="extractCovers">
                  <el-icon size="24"><Refresh /></el-icon>
                  <span>重新提取</span>
                </div>
              </div>
            </div>
            
            <!-- 上传自定义封面 -->
            <div v-if="coverMode === 'upload'" class="cover-upload">
              <el-upload
                ref="coverUploadRef"
                :auto-upload="true"
                :show-file-list="false"
                :before-upload="beforeCoverUpload"
                :http-request="uploadCustomCover"
                accept="image/*"
              >
                <div v-if="!selectedCover" class="cover-upload-area">
                  <el-icon size="32"><Upload /></el-icon>
                  <div>点击上传封面图片</div>
                  <div class="tip">支持 JPG、PNG、WebP 格式</div>
                </div>
                <div v-else class="cover-preview">
                  <img :src="getFullUrl(selectedCover)" alt="自定义封面" />
                  <div class="cover-overlay">
                    <el-icon size="20"><Edit /></el-icon>
                    <span>更换封面</span>
                  </div>
                </div>
              </el-upload>
            </div>
            
            <!-- 系统智能选择提示 -->
            <div v-if="coverMode === 'auto'" class="cover-auto-hint">
              <el-icon size="20" color="#67c23a"><CircleCheck /></el-icon>
              <span>系统将使用 AI 智能分析，自动选择最佳封面帧</span>
            </div>
          </div>
        </el-form-item>
        
        <el-form-item label="视频标题" prop="title">
          <el-input 
            v-model="form.title" 
            placeholder="请输入视频标题"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="视频描述" prop="description">
          <el-input 
            v-model="form.description" 
            type="textarea"
            placeholder="请输入视频描述"
            :rows="4"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="视频分类" prop="category_id">
          <el-cascader
            v-model="categoryPath"
            :options="categoryOptions"
            :props="{ value: 'id', label: 'name', children: 'children', emitPath: false, checkStrictly: true }"
            placeholder="请选择分类"
            style="width: 100%"
            clearable
            @change="handleCategoryChange"
          />
        </el-form-item>
        
        <el-form-item label="视频标签">
          <el-select
            v-model="form.tags"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入或选择标签"
            style="width: 100%"
          >
            <el-option v-for="tag in popularTags" :key="tag" :label="tag" :value="tag" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="付费设置">
          <el-radio-group v-model="form.pay_type">
            <el-radio-button label="free">免费</el-radio-button>
            <el-radio-button label="coins">金币付费</el-radio-button>
            <el-radio-button label="vip_free">VIP免费</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <!-- 非会员价格 -->
        <el-form-item label="非会员价格" v-if="form.pay_type !== 'free'">
          <el-input-number 
            v-model="form.coin_price" 
            :min="1" 
            :max="99999" 
            placeholder="金币数量"
          />
          <span class="input-tip">非VIP用户需支付的金币数</span>
        </el-form-item>

        <!-- VIP会员价格 -->
        <el-form-item label="VIP会员价格" v-if="form.pay_type === 'coins'">
          <el-input-number 
            v-model="form.vip_coin_price" 
            :min="0" 
            :max="99999"
            placeholder="VIP优惠价格"
          />
          <span class="input-tip">VIP会员优惠价格，0为VIP免费</span>
        </el-form-item>

        <!-- VIP等级要求 -->
        <el-form-item label="VIP等级要求" v-if="form.pay_type === 'vip_free'">
          <el-select v-model="form.vip_free_level" style="width: 200px">
            <el-option :value="1" label="普通VIP" />
            <el-option :value="2" label="VIP1" />
            <el-option :value="3" label="VIP2" />
            <el-option :value="4" label="VIP3" />
            <el-option :value="5" label="黄金至尊" />
          </el-select>
        </el-form-item>

        <!-- 试看时长 -->
        <el-form-item label="试看时长" v-if="form.pay_type !== 'free'">
          <el-input-number 
            v-model="form.free_preview_seconds" 
            :min="0" 
            :max="300" 
            :step="5"
          />
          <span class="input-tip">秒，0表示不允许试看</span>
        </el-form-item>

        <el-form-item label="VIP专享">
          <el-switch v-model="form.is_vip_only" />
          <span class="switch-tip">开启后仅VIP用户可观看（优先于付费设置）</span>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleUpload" :loading="uploading" size="large">
            <el-icon><Upload /></el-icon>
            {{ uploading ? '上传中...' : '开始上传' }}
          </el-button>
          <el-button @click="$router.back()" size="large">取消</el-button>
        </el-form-item>
      </el-form>
      
      <!-- 上传进度 -->
      <div v-if="uploading" class="upload-progress">
        <el-progress 
          :percentage="uploadProgress" 
          :stroke-width="20"
          :text-inside="true"
        />
        <p class="progress-text">{{ progressText }}</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import { ElMessage } from 'element-plus'
import { 
  UploadFilled, VideoPlay, Delete, Upload, Picture, 
  Check, Refresh, Edit, CircleCheck, InfoFilled, Loading 
} from '@element-plus/icons-vue'

const router = useRouter()
const formRef = ref(null)
const uploadRef = ref(null)
const coverUploadRef = ref(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const progressText = ref('')

// 封面相关
const coverMode = ref('auto') // auto, select, upload
const coverCandidates = ref([])
const selectedCover = ref('')
const extractingCovers = ref(false)

const form = reactive({
  file: null,
  title: '',
  description: '',
  category_id: null,
  tags: [],
  is_vip_only: false,
  pay_type: 'free',           // 付费类型: free/coins/vip_free
  coin_price: 10,             // 非会员价格
  vip_coin_price: 0,          // VIP会员价格
  vip_free_level: 1,          // VIP等级要求
  free_preview_seconds: 15    // 试看时长，默认15秒
})

const categoryPath = ref(null)
const categoryOptions = ref([])

const rules = {
  title: [
    { required: true, message: '请输入视频标题', trigger: 'blur' },
    { min: 2, max: 100, message: '标题长度应在2-100个字符之间', trigger: 'blur' }
  ]
}

const handleCategoryChange = (value) => {
  form.category_id = value
}

const categories = ref([])
const popularTags = ref([])

const handleFileChange = (file) => {
  form.file = file.raw
  // 自动填充标题
  if (!form.title) {
    const name = file.name.replace(/\.[^/.]+$/, '')
    form.title = name
  }
  // 清空已提取的封面
  coverCandidates.value = []
  selectedCover.value = ''
}

const handleExceed = () => {
  ElMessage.warning('只能上传一个视频文件')
}

const beforeUpload = (file) => {
  const isVideo = file.type.startsWith('video/')
  const isLt5G = file.size / 1024 / 1024 / 1024 < 5
  
  if (!isVideo) {
    ElMessage.error('只能上传视频文件')
    return false
  }
  if (!isLt5G) {
    ElMessage.error('视频大小不能超过5GB')
    return false
  }
  return true
}

const removeFile = () => {
  form.file = null
  uploadRef.value?.clearFiles()
  coverCandidates.value = []
  selectedCover.value = ''
}

const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(2) + ' MB'
  return (bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB'
}

const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const getFullUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `${import.meta.env.VITE_API_BASE_URL || ''}${url}`
}

// 提取候选封面
const extractCovers = async () => {
  if (!form.file) {
    ElMessage.warning('请先选择视频文件')
    return
  }
  
  extractingCovers.value = true
  try {
    const formData = new FormData()
    formData.append('file', form.file)
    formData.append('num_candidates', 6)
    
    const res = await api.post('/videos/extract-covers', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000, // 5分钟超时（大文件需要更长时间）
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        console.log(`上传进度: ${percentCompleted}%`)
      }
    })
    
    coverCandidates.value = res.data?.candidates || res.candidates || []
    
    if (coverCandidates.value.length > 0) {
      ElMessage.success(`成功提取 ${coverCandidates.value.length} 个候选封面`)
      // 默认选择AI推荐的第一个
      selectedCover.value = coverCandidates.value[0].url
    } else {
      ElMessage.warning('未能提取到候选封面')
    }
  } catch (error) {
    console.error('提取封面失败:', error)
    ElMessage.error('提取封面失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    extractingCovers.value = false
  }
}

// 选择封面
const selectCover = (url) => {
  selectedCover.value = url
}

// 上传自定义封面前检查
const beforeCoverUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt10M = file.size / 1024 / 1024 < 10
  
  if (!isImage) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('图片大小不能超过10MB')
    return false
  }
  return true
}

// 上传自定义封面
const uploadCustomCover = async ({ file }) => {
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const res = await api.post('/videos/upload-custom-cover', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    selectedCover.value = res.data?.url || res.url
    ElMessage.success('封面上传成功')
  } catch (error) {
    console.error('上传封面失败:', error)
    ElMessage.error('上传封面失败')
  }
}

const handleUpload = async () => {
  if (!form.file) {
    ElMessage.warning('请先选择视频文件')
    return
  }
  
  await formRef.value?.validate(async (valid) => {
    if (!valid) return
    
    uploading.value = true
    uploadProgress.value = 0
    progressText.value = '准备上传...'
    
    const formData = new FormData()
    formData.append('file', form.file)
    formData.append('title', form.title)
    formData.append('description', form.description || '')
    if (form.category_id) formData.append('category_id', form.category_id)
    formData.append('is_vip_only', form.is_vip_only)
    if (form.tags && form.tags.length > 0) {
      formData.append('tags', form.tags.join(','))
    }
    
    // 付费设置
    formData.append('pay_type', form.pay_type)
    if (form.pay_type !== 'free') {
      formData.append('coin_price', form.coin_price)
    }
    
    // 如果选择了手动封面或上传封面，传递封面URL
    if (coverMode.value !== 'auto' && selectedCover.value) {
      formData.append('custom_cover_url', selectedCover.value)
    }
    
    try {
      const res = await api.post('/videos/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
          if (e.lengthComputable) {
            uploadProgress.value = Math.round((e.loaded / e.total) * 100)
            progressText.value = `上传中 ${formatFileSize(e.loaded)} / ${formatFileSize(e.total)}`
          }
        }
      })
      
      progressText.value = '上传完成，正在处理视频...'
      ElMessage.success('上传成功，视频正在后台处理中')
      
      setTimeout(() => {
        router.push('/videos')
      }, 1500)
      
    } catch (error) {
      progressText.value = '上传失败'
    } finally {
      uploading.value = false
    }
  })
}

const fetchCategories = async () => {
  try {
    const res = await api.get('/videos/categories')
    const data = res.data || res || []
    categories.value = data
    categoryOptions.value = data
  } catch (error) {
    console.error('获取分类失败:', error)
    const defaultCats = [
      { id: 1, name: '教育', children: [] },
      { id: 2, name: '娱乐', children: [] },
      { id: 3, name: '科技', children: [] },
      { id: 4, name: '生活', children: [] }
    ]
    categories.value = defaultCats
    categoryOptions.value = defaultCats
  }
}

const fetchTags = async () => {
  try {
    const res = await api.get('/admin/tags')
    popularTags.value = (res.data || []).map(tag => tag.name)
  } catch (error) {
    console.error('获取标签失败:', error)
    popularTags.value = ['教程', '入门', '高级', '实战', '技巧', '分享', '原创']
  }
}

onMounted(() => {
  fetchCategories()
  fetchTags()
})
</script>

<style lang="scss" scoped>
.video-upload-page {
  .upload-area {
    padding: 40px;
    text-align: center;
    
    .upload-icon {
      font-size: 48px;
      color: #c0c4cc;
      margin-bottom: 16px;
    }
    
    .upload-text {
      color: #606266;
      margin-bottom: 8px;
      
      em {
        color: #6366f1;
        font-style: normal;
      }
    }
    
    .upload-tip {
      color: #909399;
      font-size: 12px;
    }
  }
  
  .file-info {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px;
    
    .file-details {
      flex: 1;
      text-align: left;
      
      .file-name {
        font-size: 14px;
        color: #303133;
        margin-bottom: 4px;
      }
      
      .file-size {
        font-size: 12px;
        color: #909399;
      }
    }
  }
  
  .cover-section {
    width: 100%;
    
    .cover-mode-switch {
      margin-bottom: 16px;
    }
    
    .cover-hint {
      display: flex;
      align-items: center;
      gap: 8px;
      color: #909399;
      padding: 20px;
      background: #f5f7fa;
      border-radius: 8px;
    }
    
    .cover-loading {
      display: flex;
      align-items: center;
      gap: 8px;
      color: #409eff;
      padding: 20px;
      background: #f0f9ff;
      border-radius: 8px;
    }
    
    .cover-actions {
      display: flex;
      align-items: center;
      gap: 12px;
      
      .hint-text {
        color: #909399;
        font-size: 13px;
      }
    }
    
    .cover-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      
      @media (max-width: 768px) {
        grid-template-columns: repeat(3, 1fr);
      }
      
      .cover-item {
        position: relative;
        aspect-ratio: 16 / 9;
        border-radius: 8px;
        overflow: hidden;
        cursor: pointer;
        border: 2px solid transparent;
        transition: all 0.2s;
        
        &:hover {
          border-color: #6366f1;
          transform: scale(1.02);
        }
        
        &.selected {
          border-color: #6366f1;
          box-shadow: 0 0 12px rgba(99, 102, 241, 0.3);
        }
        
        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
        
        .cover-info {
          position: absolute;
          bottom: 0;
          left: 0;
          right: 0;
          padding: 4px 8px;
          background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
          display: flex;
          justify-content: space-between;
          color: #fff;
          font-size: 11px;
        }
        
        .selected-badge {
          position: absolute;
          top: 8px;
          right: 8px;
          width: 24px;
          height: 24px;
          background: #6366f1;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #fff;
        }
        
        .best-badge {
          position: absolute;
          top: 8px;
          left: 8px;
          padding: 2px 8px;
          background: linear-gradient(135deg, #f59e0b, #f97316);
          border-radius: 4px;
          color: #fff;
          font-size: 10px;
          font-weight: 500;
        }
        
        &.add-more {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          background: #f5f7fa;
          border: 2px dashed #dcdfe6;
          color: #909399;
          gap: 8px;
          
          &:hover {
            border-color: #6366f1;
            color: #6366f1;
            background: #f0f0ff;
          }
        }
      }
    }
    
    .cover-upload {
      .cover-upload-area {
        padding: 40px;
        text-align: center;
        background: #f5f7fa;
        border: 2px dashed #dcdfe6;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
        
        &:hover {
          border-color: #6366f1;
          background: #f0f0ff;
        }
        
        .tip {
          color: #909399;
          font-size: 12px;
          margin-top: 8px;
        }
      }
      
      .cover-preview {
        position: relative;
        width: 320px;
        aspect-ratio: 16 / 9;
        border-radius: 8px;
        overflow: hidden;
        cursor: pointer;
        
        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
        
        .cover-overlay {
          position: absolute;
          inset: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          color: #fff;
          opacity: 0;
          transition: opacity 0.2s;
          gap: 4px;
        }
        
        &:hover .cover-overlay {
          opacity: 1;
        }
      }
    }
    
    .cover-auto-hint {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 16px;
      background: #f0fdf4;
      border-radius: 8px;
      color: #166534;
    }
  }
  
  .switch-tip {
    margin-left: 12px;
    color: #909399;
    font-size: 13px;
  }

  .input-tip {
    margin-left: 12px;
    color: #909399;
    font-size: 13px;
  }
  
  .upload-progress {
    margin-top: 24px;
    padding: 20px;
    background: #f5f7fa;
    border-radius: 8px;
    
    .progress-text {
      text-align: center;
      margin-top: 12px;
      color: #606266;
      font-size: 14px;
    }
  }
}
</style>