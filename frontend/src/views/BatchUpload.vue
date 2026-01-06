<template>
  <div class="batch-upload-page">
    <div class="page-header">
      <h1>批量上传视频</h1>
      <p class="subtitle">支持同时上传多个视频，统一设置分类和标签</p>
    </div>

    <!-- 批量设置区域 -->
    <el-card class="settings-card">
      <template #header>
        <span class="card-title">📋 批量设置</span>
      </template>
      
      <el-form :model="batchSettings" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="视频分类">
              <el-select v-model="batchSettings.category_id" placeholder="选择分类" clearable style="width: 100%">
                <el-option 
                  v-for="cat in categories" 
                  :key="cat.id" 
                  :label="cat.name" 
                  :value="cat.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="视频标签">
              <el-select 
                v-model="batchSettings.tags" 
                multiple 
                filterable
                allow-create
                placeholder="选择或输入标签"
                style="width: 100%"
              >
                <el-option 
                  v-for="tag in availableTags" 
                  :key="tag.id" 
                  :label="tag.name" 
                  :value="tag.name"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="标题前缀">
              <el-input v-model="batchSettings.title_prefix" placeholder="可选，如：【新品】" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="VIP专属">
              <el-switch v-model="batchSettings.is_vip_only" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 上传区域 -->
    <el-card class="upload-card">
      <template #header>
        <div class="upload-header">
          <span class="card-title">📁 选择视频文件</span>
          <el-button type="primary" :disabled="!canUpload" @click="startUpload" :loading="uploading">
            <el-icon><Upload /></el-icon>
            开始上传 ({{ selectedFiles.length }} 个文件)
          </el-button>
        </div>
      </template>

      <el-upload
        ref="uploadRef"
        class="upload-area"
        drag
        multiple
        :auto-upload="false"
        :on-change="handleFileChange"
        :on-remove="handleFileRemove"
        accept="video/*"
        :file-list="fileList"
      >
        <el-icon class="el-icon--upload"><Upload /></el-icon>
        <div class="el-upload__text">
          拖拽视频文件到此处，或 <em>点击选择</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 MP4、WebM、AVI、MOV、MKV 格式，单个文件最大 2GB
          </div>
        </template>
      </el-upload>
    </el-card>

    <!-- 上传进度 -->
    <el-card v-if="uploadResults.length > 0" class="progress-card">
      <template #header>
        <div class="progress-header">
          <span class="card-title">📊 上传进度</span>
          <div class="progress-stats">
            <el-tag type="success">成功: {{ successCount }}</el-tag>
            <el-tag type="danger" v-if="failedCount > 0">失败: {{ failedCount }}</el-tag>
            <el-tag type="info">总计: {{ uploadResults.length }}</el-tag>
          </div>
        </div>
      </template>

      <el-table :data="uploadResults" style="width: 100%">
        <el-table-column prop="title" label="文件名" min-width="200" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : row.status === 'error' ? 'danger' : 'warning'">
              {{ row.status === 'success' ? '成功' : row.status === 'error' ? '失败' : '处理中' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="消息" min-width="200" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button 
              v-if="row.video_id" 
              type="primary" 
              link 
              @click="goToVideo(row.video_id)"
            >
              查看视频
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import api from '@/utils/api'

const router = useRouter()

// 批量设置
const batchSettings = ref({
  category_id: null,
  tags: [],
  title_prefix: '',
  is_vip_only: false
})

// 分类和标签选项
const categories = ref([])
const availableTags = ref([])

// 文件相关
const uploadRef = ref(null)
const fileList = ref([])
const selectedFiles = ref([])
const uploading = ref(false)
const uploadResults = ref([])

// 计算属性
const canUpload = computed(() => selectedFiles.value.length > 0 && !uploading.value)
const successCount = computed(() => uploadResults.value.filter(r => r.status === 'success').length)
const failedCount = computed(() => uploadResults.value.filter(r => r.status === 'error').length)

// 获取分类列表
const fetchCategories = async () => {
  try {
    const res = await api.get('/videos/categories')
    categories.value = res.data || []
  } catch (e) {
    console.error('获取分类失败', e)
  }
}

// 获取标签列表
const fetchTags = async () => {
  try {
    const res = await api.get('/admin/tags')
    availableTags.value = res.data || []
  } catch (e) {
    console.error('获取标签失败', e)
  }
}

// 文件选择变化
const handleFileChange = (file, files) => {
  selectedFiles.value = files.map(f => f.raw || f)
  fileList.value = files
}

// 文件移除
const handleFileRemove = (file, files) => {
  selectedFiles.value = files.map(f => f.raw || f)
  fileList.value = files
}

// 开始上传
const startUpload = async () => {
  if (selectedFiles.value.length === 0) {
    ElMessage.warning('请先选择视频文件')
    return
  }

  uploading.value = true
  uploadResults.value = []

  try {
    const formData = new FormData()
    
    // 添加所有文件
    selectedFiles.value.forEach(file => {
      formData.append('files', file)
    })
    
    // 添加设置
    if (batchSettings.value.category_id) {
      formData.append('category_id', batchSettings.value.category_id)
    }
    formData.append('is_vip_only', batchSettings.value.is_vip_only)
    if (batchSettings.value.tags.length > 0) {
      formData.append('tags', batchSettings.value.tags.join(','))
    }
    if (batchSettings.value.title_prefix) {
      formData.append('title_prefix', batchSettings.value.title_prefix)
    }

    const res = await api.post('/videos/batch-upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 0 // 无超时限制
    })

    uploadResults.value = res.data.results || []
    
    if (res.data.success > 0) {
      ElMessage.success(`成功上传 ${res.data.success} 个视频`)
    }
    if (res.data.failed > 0) {
      ElMessage.warning(`${res.data.failed} 个视频上传失败`)
    }

    // 清空已选文件
    selectedFiles.value = []
    fileList.value = []
    if (uploadRef.value) {
      uploadRef.value.clearFiles()
    }

  } catch (e) {
    console.error('批量上传失败', e)
    ElMessage.error('批量上传失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    uploading.value = false
  }
}

// 跳转到视频详情
const goToVideo = (videoId) => {
  router.push(`/videos/${videoId}`)
}

onMounted(() => {
  fetchCategories()
  fetchTags()
})
</script>

<style lang="scss" scoped>
.batch-upload-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
  
  h1 {
    font-size: 24px;
    font-weight: 600;
    margin: 0 0 8px;
  }
  
  .subtitle {
    color: #909399;
    margin: 0;
  }
}

.settings-card,
.upload-card,
.progress-card {
  margin-bottom: 20px;
}

.card-title {
  font-size: 16px;
  font-weight: 500;
}

.upload-header,
.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-stats {
  display: flex;
  gap: 8px;
}

.upload-area {
  width: 100%;
  
  :deep(.el-upload) {
    width: 100%;
  }
  
  :deep(.el-upload-dragger) {
    width: 100%;
    height: 200px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }
}

.el-icon--upload {
  font-size: 48px;
  color: #c0c4cc;
  margin-bottom: 16px;
}

:deep(.el-upload-list) {
  max-height: 300px;
  overflow-y: auto;
}
</style>


