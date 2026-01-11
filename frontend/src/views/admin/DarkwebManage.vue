<template>
  <div class="darkweb-manage">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>暗网视频管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="showConfigDialog = true">
          <el-icon><Setting /></el-icon> VIP等级配置
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-value">{{ stats.video_count }}</div>
        <div class="stat-label">视频总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.category_count }}</div>
        <div class="stat-label">分类数量</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.tag_count }}</div>
        <div class="stat-label">标签数量</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ formatCount(stats.total_views) }}</div>
        <div class="stat-label">总观看量</div>
      </div>
    </div>

    <!-- 标签页 -->
    <el-tabs v-model="activeTab" class="manage-tabs">
      <!-- 上传视频 -->
      <el-tab-pane label="上传视频" name="upload">
        <el-form ref="uploadFormRef" :model="uploadForm" label-width="100px" style="max-width: 800px">
          <!-- 视频文件上传 -->
          <el-form-item label="视频文件" required>
            <el-upload
              ref="videoUploadRef"
              :auto-upload="false"
              :limit="1"
              :on-change="handleVideoChange"
              :on-exceed="handleVideoExceed"
              accept="video/*"
              drag
            >
              <div v-if="!uploadForm.file" class="upload-area">
                <el-icon class="upload-icon"><UploadFilled /></el-icon>
                <div class="upload-text">拖拽视频到此处，或 <em>点击上传</em></div>
                <div class="upload-tip">支持 MP4、WebM、AVI、MOV、MKV 格式，最大 5GB</div>
              </div>
              <div v-else class="file-info">
                <el-icon size="32" color="#ff4444"><VideoPlay /></el-icon>
                <div class="file-details">
                  <div class="file-name">{{ uploadForm.file.name }}</div>
                  <div class="file-size">{{ formatFileSize(uploadForm.file.size) }}</div>
                </div>
                <el-button text type="danger" @click.stop="removeVideoFile">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </el-upload>
          </el-form-item>

          <!-- 视频封面 -->
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
                <div v-if="!uploadForm.file" class="cover-hint">
                  <el-icon><InfoFilled /></el-icon> 请先选择视频文件
                </div>
                <div v-else-if="extractingCovers" class="cover-loading">
                  <el-icon class="is-loading"><Loading /></el-icon>
                  <span>正在提取视频帧...</span>
                </div>
                <div v-else-if="coverCandidates.length === 0" class="cover-actions">
                  <el-button type="primary" @click="extractCovers" :loading="extractingCovers">
                    <el-icon><Picture /></el-icon> 提取候选封面
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
                    </div>
                    <div class="selected-badge" v-if="selectedCover === cover.url">
                      <el-icon><Check /></el-icon>
                    </div>
                    <div class="best-badge" v-if="index === 0">AI推荐</div>
                  </div>
                </div>
              </div>
              
              <!-- 上传自定义封面 -->
              <div v-if="coverMode === 'upload'" class="cover-upload">
                <el-upload
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

          <el-form-item label="视频标题" required>
            <el-input v-model="uploadForm.title" placeholder="请输入视频标题" maxlength="100" show-word-limit />
          </el-form-item>

          <el-form-item label="视频描述">
            <el-input v-model="uploadForm.description" type="textarea" :rows="4" placeholder="请输入视频描述" maxlength="500" show-word-limit />
          </el-form-item>

          <el-form-item label="视频分类">
            <el-cascader
              v-model="uploadCategoryPath"
              :options="categoryOptions"
              :props="{ value: 'id', label: 'name', children: 'children', emitPath: false, checkStrictly: true }"
              placeholder="请选择分类"
              style="width: 100%"
              clearable
              @change="handleUploadCategoryChange"
            />
          </el-form-item>

          <el-form-item label="视频标签">
            <el-select v-model="uploadForm.tags" multiple filterable allow-create placeholder="输入或选择标签" style="width: 100%">
              <template v-for="tag in tags" :key="tag.id">
                <el-option v-if="tag.name" :label="tag.name" :value="tag.name" />
              </template>
            </el-select>
          </el-form-item>

          <el-form-item label="精选推荐">
            <el-switch v-model="uploadForm.is_featured" />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="handleUpload" :loading="uploading" size="large">
              <el-icon><Upload /></el-icon> {{ uploading ? '上传中...' : '开始上传' }}
            </el-button>
          </el-form-item>
        </el-form>

        <!-- 上传进度 -->
        <div v-if="uploading" class="upload-progress">
          <el-progress :percentage="uploadProgress" :stroke-width="20" :text-inside="true" />
          <p class="progress-text">{{ progressText }}</p>
        </div>
      </el-tab-pane>

      <!-- 视频管理 -->
      <el-tab-pane label="视频管理" name="videos">
        <div class="tab-toolbar">
          <el-input v-model="videoSearch" placeholder="搜索视频标题" style="width: 200px" clearable @keyup.enter="fetchVideos" />
          <el-select v-model="videoCategory" placeholder="选择分类" clearable style="width: 150px" @change="fetchVideos">
            <el-option label="全部分类" value="" />
            <template v-for="cat in allCategories" :key="'cat-' + cat.id">
              <el-option :label="cat.name" :value="cat.id" />
              <template v-for="child in (cat.children || [])" :key="'child-' + child.id">
                <el-option :label="'  └ ' + child.name" :value="child.id" />
              </template>
            </template>
          </el-select>
          <el-select v-model="videoStatus" placeholder="状态" clearable style="width: 120px" @change="fetchVideos">
            <el-option label="全部状态" value="" />
            <el-option label="已发布" value="PUBLISHED" />
            <el-option label="处理中" value="PROCESSING" />
            <el-option label="上传中" value="UPLOADING" />
          </el-select>
        </div>

        <el-table :data="videos" v-loading="loadingVideos" stripe>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column label="封面" width="120">
            <template #default="{ row }">
              <el-image :src="row.cover_url" style="width: 80px; height: 45px; border-radius: 4px" fit="cover" />
            </template>
          </el-table-column>
          <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
          <el-table-column prop="category_name" label="分类" width="100" />
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="view_count" label="播放" width="80" />
          <el-table-column prop="like_count" label="点赞" width="80" />
          <el-table-column label="精选" width="70">
            <template #default="{ row }">
              <el-switch v-model="row.is_featured" @change="updateVideoFeatured(row)" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="showVideoDialog(row)">编辑</el-button>
              <el-button type="danger" link size="small" @click="deleteVideo(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-model:current-page="videoPage"
          v-model:page-size="videoPageSize"
          :total="videoTotal"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchVideos"
          @current-change="fetchVideos"
          style="margin-top: 16px; justify-content: flex-end"
        />
      </el-tab-pane>

      <!-- 分类管理 -->
      <el-tab-pane label="分类管理" name="categories">
        <div class="tab-toolbar">
          <el-button type="primary" @click="showCategoryDialog()">
            <el-icon><Plus /></el-icon> 添加一级分类
          </el-button>
        </div>

        <el-table :data="categories" v-loading="loadingCategories" row-key="id" default-expand-all>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="name" label="分类名称" min-width="150" />
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          <el-table-column prop="sort_order" label="排序" width="80" />
          <el-table-column prop="video_count" label="视频数" width="90" />
          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button v-if="row.level === 1" type="success" link size="small" @click="showCategoryDialog(null, row.id)">添加子分类</el-button>
              <el-button type="primary" link size="small" @click="showCategoryDialog(row)">编辑</el-button>
              <el-button type="danger" link size="small" @click="deleteCategory(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 标签管理 -->
      <el-tab-pane label="标签管理" name="tags">
        <div class="tab-toolbar">
          <el-input v-model="newTagName" placeholder="输入标签名称" style="width: 200px" @keyup.enter="createTag" />
          <el-button type="primary" @click="createTag">添加标签</el-button>
        </div>

        <div class="tags-grid">
          <div v-for="tag in tags" :key="tag.id" class="tag-item">
            <span class="tag-name">{{ tag.name }}</span>
            <span class="tag-count">{{ tag.use_count }}次</span>
            <el-button type="danger" link size="small" @click="deleteTag(tag)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 视频编辑弹窗 -->
    <el-dialog v-model="videoDialogVisible" :title="editingVideo ? '编辑视频' : '添加视频'" width="600px">
      <el-form :model="videoForm" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="videoForm.title" placeholder="视频标题" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="videoForm.description" type="textarea" :rows="3" placeholder="视频描述" />
        </el-form-item>
        <el-form-item label="封面">
          <el-input v-model="videoForm.cover_url" placeholder="封面图片URL" />
        </el-form-item>
        <el-form-item label="HLS地址">
          <el-input v-model="videoForm.hls_url" placeholder="HLS视频流地址" />
        </el-form-item>
        <el-form-item label="预览地址">
          <el-input v-model="videoForm.preview_url" placeholder="预览视频URL" />
        </el-form-item>
        <el-form-item label="时长(秒)">
          <el-input-number v-model="videoForm.duration" :min="0" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="videoForm.category_id" placeholder="选择分类" clearable style="width: 100%">
            <template v-for="cat in allCategories" :key="'vcat-' + cat.id">
              <el-option :label="cat.name" :value="cat.id" />
              <template v-for="child in (cat.children || [])" :key="'vchild-' + child.id">
                <el-option :label="'  └ ' + child.name" :value="child.id" />
              </template>
            </template>
          </el-select>
        </el-form-item>
        <el-form-item label="标签">
          <el-select v-model="videoForm.tags" multiple filterable allow-create placeholder="选择或输入标签" style="width: 100%">
            <template v-for="tag in tags" :key="tag.id">
              <el-option v-if="tag.name" :label="tag.name" :value="tag.name" />
            </template>
          </el-select>
        </el-form-item>
        <el-form-item label="精选">
          <el-switch v-model="videoForm.is_featured" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="videoDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveVideo" :loading="savingVideo">保存</el-button>
      </template>
    </el-dialog>

    <!-- 分类编辑弹窗 -->
    <el-dialog v-model="categoryDialogVisible" :title="editingCategory ? '编辑分类' : (categoryParentId ? '添加二级分类' : '添加一级分类')" width="500px">
      <el-form :model="categoryForm" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="categoryForm.name" placeholder="分类名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="categoryForm.description" type="textarea" :rows="2" placeholder="分类描述" />
        </el-form-item>
        <el-form-item label="图标">
          <el-input v-model="categoryForm.icon" placeholder="图标URL" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="categoryForm.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="状态" v-if="editingCategory">
          <el-switch v-model="categoryForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="categoryDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveCategory" :loading="savingCategory">保存</el-button>
      </template>
    </el-dialog>

    <!-- VIP等级配置弹窗 -->
    <el-dialog v-model="showConfigDialog" title="VIP等级配置" width="400px">
      <el-form label-width="120px">
        <el-form-item label="最低VIP等级">
          <el-select v-model="configForm.min_vip_level" style="width: 100%">
            <el-option label="普通VIP (1)" :value="1" />
            <el-option label="VIP1 (2)" :value="2" />
            <el-option label="VIP2 (3)" :value="3" />
            <el-option label="VIP3 (4)" :value="4" />
            <el-option label="黄金至尊 (5)" :value="5" />
            <el-option label="紫色限定至尊 (6)" :value="6" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <span class="config-tip">只有达到此VIP等级的用户才能访问暗网专区</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showConfigDialog = false">取消</el-button>
        <el-button type="primary" @click="saveConfig" :loading="savingConfig">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, Delete, Setting, Upload, UploadFilled, VideoPlay, 
  Picture, Check, Edit, CircleCheck, InfoFilled, Loading, Refresh 
} from '@element-plus/icons-vue'
import api from '@/utils/api'

// 状态
const activeTab = ref('upload')
const stats = ref({ video_count: 0, category_count: 0, tag_count: 0, total_views: 0 })

// 上传相关
const uploadFormRef = ref(null)
const videoUploadRef = ref(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const progressText = ref('')
const coverMode = ref('auto')
const coverCandidates = ref([])
const selectedCover = ref('')
const extractingCovers = ref(false)
const uploadCategoryPath = ref(null)

const uploadForm = reactive({
  file: null,
  title: '',
  description: '',
  category_id: null,
  tags: [],
  is_featured: false
})

// 视频相关
const videos = ref([])
const videoPage = ref(1)
const videoPageSize = ref(20)
const videoTotal = ref(0)
const videoSearch = ref('')
const videoCategory = ref('')
const videoStatus = ref('')
const loadingVideos = ref(false)
const videoDialogVisible = ref(false)
const editingVideo = ref(null)
const savingVideo = ref(false)
const videoForm = reactive({
  title: '', description: '', cover_url: '', hls_url: '', preview_url: '',
  duration: 0, category_id: '', tags: [], is_featured: false
})

// 分类相关
const categories = ref([])
const allCategories = computed(() => categories.value)
const categoryOptions = computed(() => categories.value)
const loadingCategories = ref(false)
const categoryDialogVisible = ref(false)
const editingCategory = ref(null)
const categoryParentId = ref(null)
const savingCategory = ref(false)
const categoryForm = reactive({ name: '', description: '', icon: '', sort_order: 0, is_active: true })

// 标签相关
const tags = ref([])
const newTagName = ref('')

// 配置相关
const showConfigDialog = ref(false)
const savingConfig = ref(false)
const configForm = reactive({ min_vip_level: 5 })

// 工具函数
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

const formatCount = (count) => {
  if (!count) return '0'
  if (count >= 10000) return (count / 10000).toFixed(1) + 'w'
  return count.toString()
}

const getStatusType = (status) => ({ 'PUBLISHED': 'success', 'PROCESSING': 'warning', 'UPLOADING': 'info', 'FAILED': 'danger' }[status] || 'info')
const getStatusText = (status) => ({ 'PUBLISHED': '已发布', 'PROCESSING': '处理中', 'UPLOADING': '上传中', 'FAILED': '失败' }[status] || status)

// 上传相关方法
const handleVideoChange = (file) => {
  uploadForm.file = file.raw
  if (!uploadForm.title) {
    uploadForm.title = file.name.replace(/\.[^/.]+$/, '')
  }
  coverCandidates.value = []
  selectedCover.value = ''
}

const handleVideoExceed = () => ElMessage.warning('只能上传一个视频文件')

const removeVideoFile = () => {
  uploadForm.file = null
  videoUploadRef.value?.clearFiles()
  coverCandidates.value = []
  selectedCover.value = ''
}

const handleUploadCategoryChange = (value) => {
  uploadForm.category_id = value
}

const extractCovers = async () => {
  if (!uploadForm.file) {
    ElMessage.warning('请先选择视频文件')
    return
  }
  extractingCovers.value = true
  try {
    const formData = new FormData()
    formData.append('file', uploadForm.file)
    formData.append('num_candidates', 6)
    const res = await api.post('/videos/extract-covers', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000
    })
    coverCandidates.value = res.data?.candidates || res.candidates || []
    if (coverCandidates.value.length > 0) {
      ElMessage.success(`成功提取 ${coverCandidates.value.length} 个候选封面`)
      selectedCover.value = coverCandidates.value[0].url
    }
  } catch (error) {
    ElMessage.error('提取封面失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    extractingCovers.value = false
  }
}

const selectCover = (url) => { selectedCover.value = url }

const beforeCoverUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isImage) { ElMessage.error('只能上传图片文件'); return false }
  if (!isLt10M) { ElMessage.error('图片大小不能超过10MB'); return false }
  return true
}

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
    ElMessage.error('上传封面失败')
  }
}

const handleUpload = async () => {
  if (!uploadForm.file) {
    ElMessage.warning('请先选择视频文件')
    return
  }
  if (!uploadForm.title) {
    ElMessage.warning('请输入视频标题')
    return
  }
  
  uploading.value = true
  uploadProgress.value = 0
  progressText.value = '准备上传...'
  
  const formData = new FormData()
  formData.append('file', uploadForm.file)
  formData.append('title', uploadForm.title)
  formData.append('description', uploadForm.description || '')
  if (uploadForm.category_id) formData.append('category_id', uploadForm.category_id)
  if (uploadForm.tags?.length > 0) formData.append('tags', uploadForm.tags.join(','))
  formData.append('is_featured', uploadForm.is_featured)
  if (coverMode.value !== 'auto' && selectedCover.value) {
    formData.append('custom_cover_url', selectedCover.value)
  }
  
  try {
    await api.post('/admin/darkweb/videos/upload', formData, {
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
    // 重置表单
    uploadForm.file = null
    uploadForm.title = ''
    uploadForm.description = ''
    uploadForm.category_id = null
    uploadForm.tags = []
    uploadForm.is_featured = false
    uploadCategoryPath.value = null
    coverCandidates.value = []
    selectedCover.value = ''
    videoUploadRef.value?.clearFiles()
    fetchStats()
    fetchVideos()
  } catch (error) {
    progressText.value = '上传失败'
    ElMessage.error('上传失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    uploading.value = false
  }
}

// 数据获取
const fetchStats = async () => {
  try {
    const res = await api.get('/admin/darkweb/stats')
    const data = res.data || res
    stats.value = data || { video_count: 0, category_count: 0, tag_count: 0, total_views: 0 }
  } catch (error) {
    console.error('获取统计失败:', error)
    stats.value = { video_count: 0, category_count: 0, tag_count: 0, total_views: 0 }
  }
}

const fetchVideos = async () => {
  loadingVideos.value = true
  try {
    const params = { page: videoPage.value, page_size: videoPageSize.value }
    if (videoSearch.value) params.keyword = videoSearch.value
    if (videoCategory.value) params.category_id = videoCategory.value
    if (videoStatus.value) params.status = videoStatus.value
    const res = await api.get('/admin/darkweb/videos', { params })
    const data = res.data || res
    videos.value = data.items || []
    videoTotal.value = data.total || 0
  } catch (error) {
    console.error('获取视频失败:', error)
    videos.value = []
    videoTotal.value = 0
  } finally {
    loadingVideos.value = false
  }
}

const fetchCategories = async () => {
  loadingCategories.value = true
  try {
    const res = await api.get('/admin/darkweb/categories')
    const data = res.data || res
    categories.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('获取分类失败:', error)
    categories.value = []
  } finally {
    loadingCategories.value = false
  }
}

const fetchTags = async () => {
  try {
    const res = await api.get('/admin/darkweb/tags')
    const data = res.data || res
    tags.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('获取标签失败:', error)
    tags.value = []
  }
}

const fetchConfig = async () => {
  try {
    const res = await api.get('/admin/darkweb/config')
    const data = res.data || res
    configForm.min_vip_level = data.min_vip_level || 5
  } catch (error) {
    console.error('获取配置失败:', error)
    configForm.min_vip_level = 5
  }
}

// 视频管理
const showVideoDialog = (video = null) => {
  editingVideo.value = video
  if (video) {
    Object.assign(videoForm, {
      title: video.title, description: video.description || '', cover_url: video.cover_url || '',
      hls_url: video.hls_url || '', preview_url: video.preview_url || '', duration: video.duration || 0,
      category_id: video.category_id || '', tags: video.tags || [], is_featured: video.is_featured
    })
  } else {
    Object.assign(videoForm, {
      title: '', description: '', cover_url: '', hls_url: '', preview_url: '',
      duration: 0, category_id: '', tags: [], is_featured: false
    })
  }
  videoDialogVisible.value = true
}

const saveVideo = async () => {
  if (!videoForm.title) { ElMessage.warning('请输入视频标题'); return }
  savingVideo.value = true
  try {
    if (editingVideo.value) {
      await api.put(`/admin/darkweb/videos/${editingVideo.value.id}`, videoForm)
      ElMessage.success('更新成功')
    } else {
      await api.post('/admin/darkweb/videos', videoForm)
      ElMessage.success('添加成功')
    }
    videoDialogVisible.value = false
    fetchVideos()
    fetchStats()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    savingVideo.value = false
  }
}

const updateVideoFeatured = async (video) => {
  try {
    await api.put(`/admin/darkweb/videos/${video.id}`, { is_featured: video.is_featured })
    ElMessage.success('更新成功')
  } catch (error) {
    video.is_featured = !video.is_featured
    ElMessage.error('更新失败')
  }
}

const deleteVideo = async (video) => {
  try {
    await ElMessageBox.confirm('确定要删除这个视频吗？', '提示', { type: 'warning' })
    await api.delete(`/admin/darkweb/videos/${video.id}`)
    ElMessage.success('删除成功')
    fetchVideos()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

// 分类管理
const showCategoryDialog = (category = null, parentId = null) => {
  editingCategory.value = category
  categoryParentId.value = parentId
  if (category) {
    Object.assign(categoryForm, {
      name: category.name, description: category.description || '',
      icon: category.icon || '', sort_order: category.sort_order || 0, is_active: category.is_active
    })
  } else {
    Object.assign(categoryForm, { name: '', description: '', icon: '', sort_order: 0, is_active: true })
  }
  categoryDialogVisible.value = true
}

const saveCategory = async () => {
  if (!categoryForm.name) { ElMessage.warning('请输入分类名称'); return }
  savingCategory.value = true
  try {
    const data = { ...categoryForm }
    if (categoryParentId.value) data.parent_id = categoryParentId.value
    if (editingCategory.value) {
      await api.put(`/admin/darkweb/categories/${editingCategory.value.id}`, data)
      ElMessage.success('更新成功')
    } else {
      await api.post('/admin/darkweb/categories', data)
      ElMessage.success('添加成功')
    }
    categoryDialogVisible.value = false
    fetchCategories()
    fetchStats()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    savingCategory.value = false
  }
}

const deleteCategory = async (category) => {
  try {
    await ElMessageBox.confirm('确定要删除这个分类吗？', '提示', { type: 'warning' })
    await api.delete(`/admin/darkweb/categories/${category.id}`)
    ElMessage.success('删除成功')
    fetchCategories()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error(error.response?.data?.detail || '删除失败')
  }
}

// 标签管理
const createTag = async () => {
  if (!newTagName.value.trim()) { ElMessage.warning('请输入标签名称'); return }
  try {
    await api.post('/admin/darkweb/tags', { name: newTagName.value.trim() })
    ElMessage.success('添加成功')
    newTagName.value = ''
    fetchTags()
    fetchStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '添加失败')
  }
}

const deleteTag = async (tag) => {
  try {
    await ElMessageBox.confirm('确定要删除这个标签吗？', '提示', { type: 'warning' })
    await api.delete(`/admin/darkweb/tags/${tag.id}`)
    ElMessage.success('删除成功')
    fetchTags()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

// 配置管理
const saveConfig = async () => {
  savingConfig.value = true
  try {
    await api.put('/admin/darkweb/config', configForm)
    ElMessage.success('配置保存成功')
    showConfigDialog.value = false
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    savingConfig.value = false
  }
}

onMounted(() => {
  fetchStats()
  fetchVideos()
  fetchCategories()
  fetchTags()
  fetchConfig()
})
</script>

<style lang="scss" scoped>
.darkweb-manage {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  h2 { margin: 0; color: #ff4444; }
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
  .stat-card {
    background: #fff;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    .stat-value { font-size: 28px; font-weight: bold; color: #ff4444; }
    .stat-label { font-size: 14px; color: #666; margin-top: 8px; }
  }
}

.manage-tabs {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}

.tab-toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.tags-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  .tag-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: #f5f5f5;
    border-radius: 6px;
    .tag-name { font-size: 14px; }
    .tag-count { font-size: 12px; color: #999; }
  }
}

.config-tip { font-size: 12px; color: #999; }

// 上传相关样式
.upload-area {
  padding: 40px;
  text-align: center;
  .upload-icon { font-size: 48px; color: #c0c4cc; margin-bottom: 16px; }
  .upload-text { color: #606266; margin-bottom: 8px; em { color: #ff4444; font-style: normal; } }
  .upload-tip { color: #909399; font-size: 12px; }
}

.file-info {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  .file-details {
    flex: 1;
    text-align: left;
    .file-name { font-size: 14px; color: #303133; margin-bottom: 4px; }
    .file-size { font-size: 12px; color: #909399; }
  }
}

.cover-section {
  width: 100%;
  .cover-mode-switch { margin-bottom: 16px; }
  .cover-hint, .cover-loading {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 20px;
    background: #f5f7fa;
    border-radius: 8px;
  }
  .cover-hint { color: #909399; }
  .cover-loading { color: #409eff; background: #f0f9ff; }
  .cover-actions {
    display: flex;
    align-items: center;
    gap: 12px;
    .hint-text { color: #909399; font-size: 13px; }
  }
  .cover-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    .cover-item {
      position: relative;
      aspect-ratio: 16 / 9;
      border-radius: 8px;
      overflow: hidden;
      cursor: pointer;
      border: 2px solid transparent;
      transition: all 0.2s;
      &:hover { border-color: #ff4444; transform: scale(1.02); }
      &.selected { border-color: #ff4444; box-shadow: 0 0 12px rgba(255, 68, 68, 0.3); }
      img { width: 100%; height: 100%; object-fit: cover; }
      .cover-info {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 4px 8px;
        background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
        color: #fff;
        font-size: 11px;
      }
      .selected-badge {
        position: absolute;
        top: 8px;
        right: 8px;
        width: 24px;
        height: 24px;
        background: #ff4444;
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
      &:hover { border-color: #ff4444; background: #fff5f5; }
      .tip { color: #909399; font-size: 12px; margin-top: 8px; }
    }
    .cover-preview {
      position: relative;
      width: 320px;
      aspect-ratio: 16 / 9;
      border-radius: 8px;
      overflow: hidden;
      cursor: pointer;
      img { width: 100%; height: 100%; object-fit: cover; }
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
      &:hover .cover-overlay { opacity: 1; }
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

.upload-progress {
  margin-top: 24px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  .progress-text { text-align: center; margin-top: 12px; color: #606266; font-size: 14px; }
}
</style>