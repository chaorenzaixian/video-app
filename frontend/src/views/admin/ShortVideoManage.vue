<template>
  <div class="short-video-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>短视频管理</span>
          <div class="header-actions">
            <el-button type="primary" @click="openUploadDialog">
              <el-icon><Upload /></el-icon>上传短视频
            </el-button>
          </div>
        </div>
      </template>
      
      <!-- 筛选栏 -->
      <div class="filter-bar">
        <el-input 
          v-model="filters.search" 
          placeholder="搜索标题..."
          clearable
          style="width: 200px"
          @keyup.enter="fetchVideos"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        
        <el-select v-model="filters.status" placeholder="状态" clearable style="width: 120px">
          <el-option label="已发布" value="PUBLISHED" />
          <el-option label="处理中" value="PROCESSING" />
          <el-option label="审核中" value="REVIEWING" />
          <el-option label="失败" value="FAILED" />
        </el-select>
        
        <el-select v-model="filters.category" placeholder="分类" clearable style="width: 120px">
          <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
        </el-select>
        
        <el-button @click="fetchVideos">
          <el-icon><Search /></el-icon>搜索
        </el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
      
      <!-- 视频列表 -->
      <el-table :data="videos" v-loading="loading" stripe>
        <el-table-column label="封面" width="100">
          <template #default="{ row }">
            <div class="video-cover" @click="previewVideo(row)">
              <el-image 
                :src="getCoverUrl(row.cover_url)" 
                fit="cover"
                style="width: 80px; height: 100px; border-radius: 6px;"
              >
                <template #error>
                  <div class="image-error">无封面</div>
                </template>
              </el-image>
              <div class="play-icon">▶</div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
        
        <el-table-column label="时长" width="70">
          <template #default="{ row }">
            {{ formatDuration(row.duration) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="view_count" label="播放" width="70" />
        <el-table-column prop="like_count" label="点赞" width="70" />
        
        <el-table-column label="付费" width="100">
          <template #default="{ row }">
            <div>
              <el-tag v-if="row.is_vip_only" type="success" size="small">VIP专属</el-tag>
              <el-tag v-else-if="row.coin_price > 0" type="warning" size="small">
                {{ row.coin_price }}金币
              </el-tag>
              <span v-else>免费</span>
            </div>
            <div v-if="row.is_vip_only && row.coin_price > 0" style="margin-top: 2px;">
              <el-tag type="info" size="small">非VIP {{ row.coin_price }}币</el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag 
              :type="getStatusType(row.status)" 
              size="small"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="上传时间" width="150">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="editVideo(row)">编辑</el-button>
            <el-button 
              v-if="row.status === 'PUBLISHED'" 
              link 
              type="primary" 
              @click="previewVideo(row)"
            >
              预览
            </el-button>
            <el-popconfirm title="确定删除这个短视频吗？" @confirm="deleteVideo(row)">
              <template #reference>
                <el-button link type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchVideos"
          @current-change="fetchVideos"
        />
      </div>
    </el-card>
    
    <!-- 上传对话框 -->
    <el-dialog v-model="uploadDialogVisible" title="上传短视频" width="600px" :close-on-click-modal="false">
      <el-form :model="uploadForm" label-width="80px">
        <el-form-item label="视频文件" required>
          <el-upload
            ref="uploadRef"
            :action="uploadUrl"
            :headers="uploadHeaders"
            :with-credentials="true"
            :before-upload="beforeUpload"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :on-progress="handleUploadProgress"
            :show-file-list="false"
            :disabled="uploading"
            accept="video/*"
          >
            <el-button :loading="uploading">
              {{ uploading ? `上传中 ${uploadProgress}%` : '选择视频文件' }}
            </el-button>
          </el-upload>
          <div class="upload-hint" v-if="uploadedVideoUrl">
            <el-tag type="success">已上传</el-tag>
          </div>
          <div class="upload-tip">支持 MP4、MOV 格式，最大800MB</div>
        </el-form-item>
        
        <el-form-item label="封面" v-if="videoFrames.length > 0 || uploadForm.cover_url">
          <div class="cover-selector">
            <div class="cover-frames">
              <div 
                v-for="(frame, index) in videoFrames" 
                :key="index"
                :class="['frame-item', { active: selectedFrameIndex === index }]"
                @click="selectFrame(index)"
              >
                <img :src="frame" alt="" />
              </div>
            </div>
            <div class="cover-tip">从视频中截取6帧供选择</div>
          </div>
        </el-form-item>
        
        <!-- 隐藏的视频元素用于截帧 -->
        <video 
          ref="hiddenVideoRef" 
          style="display: none;" 
          crossorigin="anonymous"
          @loadedmetadata="onVideoMetadataLoaded"
        />
        
        <el-form-item label="标题" required>
          <el-input v-model="uploadForm.title" placeholder="输入短视频标题" maxlength="100" show-word-limit />
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input v-model="uploadForm.description" type="textarea" :rows="3" placeholder="描述（选填）" maxlength="500" />
        </el-form-item>
        
        <el-form-item label="分类">
          <el-select
            v-model="uploadForm.short_category_id"
            placeholder="选择分类"
            clearable
            style="width: 100%"
          >
            <el-option v-for="cat in categories" :key="cat.id" :label="`${cat.icon || ''} ${cat.name}`" :value="cat.id" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="付费设置">
          <el-radio-group v-model="uploadForm.pay_type">
            <el-radio value="free">免费</el-radio>
            <el-radio value="vip_free">会员免费，非会员付费</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="非会员价格" v-if="uploadForm.pay_type === 'vip_free'">
          <el-input-number v-model="uploadForm.coin_price" :min="1" :max="9999" />
          <span style="margin-left: 8px; color: #909399;">金币</span>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitUpload" :loading="submitting" :disabled="!canSubmit">
          发布
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 编辑对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑短视频" width="500px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="editForm.title" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select
            v-model="editForm.short_category_id"
            placeholder="选择分类"
            clearable
            style="width: 100%"
          >
            <el-option v-for="cat in categories" :key="cat.id" :label="`${cat.icon || ''} ${cat.name}`" :value="cat.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="VIP专属">
          <el-switch v-model="editForm.is_vip_only" />
          <span style="margin-left: 8px; color: #909399;">开启后VIP用户免费观看</span>
        </el-form-item>
        <el-form-item label="付费" v-if="!editForm.is_vip_only">
          <el-input-number v-model="editForm.coin_price" :min="0" :max="9999" />
          <span style="margin-left: 8px; color: #909399;">0 表示免费</span>
        </el-form-item>
        <el-form-item label="非会员价格" v-if="editForm.is_vip_only">
          <el-input-number v-model="editForm.coin_price" :min="0" :max="9999" />
          <span style="margin-left: 8px; color: #909399;">非VIP用户需支付的金币</span>
        </el-form-item>
        <el-form-item label="推荐">
          <el-switch v-model="editForm.is_featured" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
    
    <!-- 预览对话框 -->
    <el-dialog v-model="previewDialogVisible" title="预览" width="400px" destroy-on-close>
      <div class="video-preview">
        <video 
          :src="previewUrl" 
          controls 
          autoplay
          style="width: 100%; max-height: 70vh; border-radius: 8px;"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import api from '@/utils/api'
import { ElMessage } from 'element-plus'
import { Upload, Search, Plus } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)
const submitting = ref(false)
const uploadProgress = ref(0)

const videos = ref([])
const categories = ref([])

const filters = reactive({
  search: '',
  status: '',
  category: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 上传相关
const uploadDialogVisible = ref(false)
const uploadRef = ref(null)
const uploadedVideoUrl = ref('')
const uploadCategoryPath = ref(null)
const uploadForm = reactive({
  title: '',
  description: '',
  short_category_id: null,  // 使用短视频分类
  cover_url: '',
  pay_type: 'free',
  coin_price: 10,
  duration: 0
})

// 封面截帧相关
const hiddenVideoRef = ref(null)
const videoFrames = ref([])
const selectedFrameIndex = ref(0)
const customCoverUrl = ref('')
const localVideoFile = ref(null)

const uploadUrl = '/api/v1/videos/upload-file'
const coverUploadUrl = '/api/v1/ads/upload/image'
const uploadHeaders = computed(() => {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
})

const canSubmit = computed(() => {
  return uploadedVideoUrl.value && uploadForm.title.trim() && (videoFrames.value.length > 0 || uploadForm.cover_url)
})

// 编辑相关
const editDialogVisible = ref(false)
const editCategoryPath = ref(null)
const editForm = reactive({
  id: 0,
  title: '',
  description: '',
  short_category_id: null,  // 使用短视频分类
  coin_price: 0,
  is_vip_only: false,  // VIP专属
  is_featured: false
})

// 预览相关
const previewDialogVisible = ref(false)
const previewUrl = ref('')

// 获取短视频列表
const fetchVideos = async () => {
  loading.value = true
  try {
    const res = await api.get('/admin/videos', {
      params: {
        page: pagination.page,
        page_size: pagination.pageSize,
        search: filters.search || undefined,
        status: filters.status || undefined,
        short_category_id: filters.category || undefined,
        is_short: true
      }
    })
    videos.value = res.data?.items || []
    pagination.total = res.data?.total || 0
  } catch (error) {
    console.error('获取短视频列表失败:', error)
  } finally {
    loading.value = false
  }
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
      categories.value = []
    }
  }
}

const resetFilters = () => {
  filters.search = ''
  filters.status = ''
  filters.category = ''
  pagination.page = 1
  fetchVideos()
}

// 上传对话框
const openUploadDialog = () => {
  uploadForm.title = ''
  uploadForm.description = ''
  uploadForm.short_category_id = null
  uploadForm.cover_url = ''
  uploadForm.pay_type = 'free'
  uploadForm.coin_price = 10
  uploadForm.duration = 0
  uploadedVideoUrl.value = ''
  uploadProgress.value = 0
  // 重置封面相关
  videoFrames.value = []
  selectedFrameIndex.value = 0
  customCoverUrl.value = ''
  localVideoFile.value = null
  uploadDialogVisible.value = true
}

const beforeUpload = (file) => {
  // 检查文件类型
  if (!file.type.startsWith('video/')) {
    ElMessage.error('请选择视频文件')
    return false
  }
  
  // 检查文件大小 (800MB)
  if (file.size > 800 * 1024 * 1024) {
    ElMessage.error('视频文件不能超过800MB')
    return false
  }
  
  // 使用文件名作为默认标题（去掉扩展名）
  if (!uploadForm.title) {
    const fileName = file.name
    const titleWithoutExt = fileName.replace(/\.[^/.]+$/, '')  // 去掉扩展名
    uploadForm.title = titleWithoutExt
  }
  
  // 保存文件用于截帧
  localVideoFile.value = file
  
  // 创建本地URL用于截帧
  const videoUrl = URL.createObjectURL(file)
  if (hiddenVideoRef.value) {
    hiddenVideoRef.value.src = videoUrl
  }
  
  uploading.value = true
  return true
}

// 视频元数据加载完成，开始截帧
const onVideoMetadataLoaded = () => {
  // 保存视频时长
  if (hiddenVideoRef.value) {
    uploadForm.duration = hiddenVideoRef.value.duration || 0
  }
  extractVideoFrames()
}

// 从视频中提取6帧
const extractVideoFrames = async () => {
  const video = hiddenVideoRef.value
  if (!video || !video.duration) return
  
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  const frames = []
  const frameCount = 6
  const interval = video.duration / (frameCount + 1)
  
  const captureFrame = (time) => {
    return new Promise((resolve) => {
      video.currentTime = time
      video.onseeked = () => {
        canvas.width = video.videoWidth
        canvas.height = video.videoHeight
        ctx.drawImage(video, 0, 0)
        frames.push(canvas.toDataURL('image/jpeg', 0.8))
        resolve()
      }
    })
  }
  
  try {
    for (let i = 0; i < frameCount; i++) {
      await captureFrame((i + 1) * interval)
    }
    videoFrames.value = frames
    selectedFrameIndex.value = 0
    uploadForm.cover_url = frames[0]
    video.currentTime = 0
  } catch (e) {
    console.error('截帧失败:', e)
  }
}

// 选择封面帧
const selectFrame = (index) => {
  selectedFrameIndex.value = index
  customCoverUrl.value = ''
  uploadForm.cover_url = videoFrames.value[index]
}

const handleUploadProgress = (event) => {
  uploadProgress.value = Math.round(event.percent || 0)
}

const handleUploadSuccess = (response) => {
  uploading.value = false
  uploadProgress.value = 100
  uploadedVideoUrl.value = response.url || response.data?.url
  ElMessage.success('视频上传成功')
}

const handleUploadError = (error, file, fileList) => {
  uploading.value = false
  console.error('上传错误:', error)
  const message = error?.message || error?.response?.data?.detail || '视频上传失败'
  ElMessage.error(message)
}

const handleCoverSuccess = (response) => {
  const url = response.url || response.data?.url
  customCoverUrl.value = url
  uploadForm.cover_url = url
  selectedFrameIndex.value = -1
}

const submitUpload = async () => {
  if (!canSubmit.value) return
  
  submitting.value = true
  try {
    // 如果封面是 base64 数据，先上传获取 URL
    let coverUrl = uploadForm.cover_url
    if (coverUrl && coverUrl.startsWith('data:')) {
      // 将 base64 转为 Blob
      const coverBlob = await fetch(coverUrl).then(r => r.blob())
      const coverFormData = new FormData()
      coverFormData.append('file', coverBlob, 'cover.webp')
      
      const coverRes = await api.post('/ads/upload/image', coverFormData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      coverUrl = coverRes.data?.url || coverRes.url
    }
    
    await api.post('/admin/shorts', {
      title: uploadForm.title,
      description: uploadForm.description,
      short_category_id: uploadForm.short_category_id || null,
      original_url: uploadedVideoUrl.value,
      cover_url: coverUrl,
      duration: uploadForm.duration || 0,
      pay_type: uploadForm.pay_type === 'vip_free' ? 'coins' : 'free',
      coin_price: uploadForm.pay_type === 'vip_free' ? uploadForm.coin_price : 0,
      is_vip_only: uploadForm.pay_type === 'vip_free'
    })
    
    ElMessage.success('发布成功！')
    uploadDialogVisible.value = false
    fetchVideos()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '发布失败')
  } finally {
    submitting.value = false
  }
}

// 编辑
const editVideo = (row) => {
  editForm.id = row.id
  editForm.title = row.title || ''
  editForm.description = row.description || ''
  editForm.short_category_id = row.short_category_id || row.category_id || null  // 兼容旧数据
  editForm.coin_price = row.coin_price || 0
  editForm.is_vip_only = row.is_vip_only || false
  editForm.is_featured = row.is_featured || false
  editDialogVisible.value = true
}

const saveEdit = async () => {
  saving.value = true
  try {
    await api.put(`/admin/videos/${editForm.id}`, {
      title: editForm.title,
      description: editForm.description,
      short_category_id: editForm.short_category_id,
      coin_price: editForm.coin_price,
      is_vip_only: editForm.is_vip_only,
      is_featured: editForm.is_featured
    })
    ElMessage.success('保存成功')
    editDialogVisible.value = false
    fetchVideos()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 删除
const deleteVideo = async (row) => {
  try {
    await api.delete(`/admin/videos/${row.id}`)
    ElMessage.success('删除成功')
    fetchVideos()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

// 预览
const previewVideo = (row) => {
  previewUrl.value = row.hls_url || row.original_url || ''
  if (previewUrl.value) {
    previewDialogVisible.value = true
  } else {
    ElMessage.warning('视频地址不可用')
  }
}

// 工具函数
const formatDuration = (seconds) => {
  if (!seconds || isNaN(seconds)) return '0:00'
  seconds = Math.floor(seconds)
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

const formatDate = (date) => {
  return dayjs(date).format('MM-DD HH:mm')
}

const getCoverUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('http') || url.startsWith('/')) return url
  return '/' + url
}

const getStatusType = (status) => {
  const map = {
    'PUBLISHED': 'success',
    'PROCESSING': 'warning',
    'REVIEWING': 'info',
    'FAILED': 'danger'
  }
  return map[status] || ''
}

const getStatusText = (status) => {
  const map = {
    'PUBLISHED': '已发布',
    'PROCESSING': '处理中',
    'REVIEWING': '审核中',
    'FAILED': '失败'
  }
  return map[status] || status
}

onMounted(() => {
  fetchVideos()
  fetchCategories()
})
</script>

<style lang="scss" scoped>
.short-video-manage {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .filter-bar {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
    flex-wrap: wrap;
  }
  
  .video-cover {
    position: relative;
    cursor: pointer;
    
    .play-icon {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 30px;
      height: 30px;
      background: rgba(0,0,0,0.6);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-size: 12px;
      opacity: 0;
      transition: opacity 0.2s;
    }
    
    &:hover .play-icon {
      opacity: 1;
    }
  }
  
  .image-error {
    width: 80px;
    height: 100px;
    background: #f5f7fa;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #909399;
    font-size: 12px;
    border-radius: 6px;
  }
  
  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
  
  .upload-hint {
    margin-top: 8px;
  }
  
  .upload-tip {
    font-size: 12px;
    color: #909399;
    margin-top: 4px;
  }
  
  .cover-selector {
    .cover-frames {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      
      .frame-item {
        width: 70px;
        height: 90px;
        border-radius: 6px;
        overflow: hidden;
        cursor: pointer;
        border: 2px solid transparent;
        transition: all 0.2s;
        
        &.active {
          border-color: #409eff;
        }
        
        &:hover {
          border-color: #c0c4cc;
        }
        
        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
        
        &.upload-item {
          background: #f5f7fa;
          display: flex;
          align-items: center;
          justify-content: center;
          
          .upload-placeholder {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: #909399;
            
            .el-icon {
              font-size: 18px;
              margin-bottom: 2px;
            }
            
            span {
              font-size: 11px;
            }
          }
        }
      }
    }
    
    .cover-tip {
      margin-top: 8px;
      font-size: 12px;
      color: #909399;
    }
  }
  
  .custom-cover-upload {
    display: inline-block;
  }
  
  .cover-upload {
    cursor: pointer;
    
    .cover-placeholder {
      width: 80px;
      height: 100px;
      border: 1px dashed #dcdfe6;
      border-radius: 4px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      color: #909399;
      
      .el-icon {
        font-size: 20px;
        margin-bottom: 4px;
      }
      
      span {
        font-size: 12px;
      }
    }
  }
  
  .video-preview {
    text-align: center;
  }
}
</style>



