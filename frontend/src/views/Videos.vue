<template>
  <div class="videos-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>视频列表</span>
          <div class="header-actions">
            <el-button @click="$router.push('/videos/batch-upload')">
              <el-icon><FolderAdd /></el-icon>批量上传
            </el-button>
          <el-button type="primary" @click="$router.push('/videos/upload')">
            <el-icon><Upload /></el-icon>上传视频
          </el-button>
          </div>
        </div>
      </template>
      
      <!-- 搜索筛选 -->
      <div class="filter-bar">
        <el-input 
          v-model="filters.search" 
          placeholder="搜索视频标题..."
          clearable
          style="width: 250px"
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
        
        <el-select v-model="filters.video_type" placeholder="视频类型" clearable style="width: 120px">
          <el-option label="全部" value="" />
          <el-option label="长视频" value="normal" />
          <el-option label="短视频" value="short" />
        </el-select>
        
        <el-button @click="fetchVideos">
          <el-icon><Search /></el-icon>搜索
        </el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
      
      <!-- 视频列表 -->
      <el-table :data="videos" v-loading="loading" stripe>
        <el-table-column label="封面" width="120">
          <template #default="{ row }">
            <el-image 
              :src="getCoverUrl(row.cover_url)" 
              fit="cover"
              style="width: 100px; height: 56px; border-radius: 4px;"
            >
              <template #error>
                <div class="image-error">
                  <el-icon v-if="row.status === 'PROCESSING'"><Loading /></el-icon>
                  <span v-else>无封面</span>
                </div>
              </template>
            </el-image>
          </template>
        </el-table-column>
        
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        
        <el-table-column prop="uploader_name" label="上传者" width="100" />
        
        <el-table-column label="时长" width="80">
          <template #default="{ row }">
            {{ formatDuration(row.duration) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="view_count" label="播放" width="80" />
        
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
        
        <el-table-column label="短视频" width="70">
          <template #default="{ row }">
            <el-switch 
              v-model="row.is_short" 
              @change="toggleShort(row)"
              size="small"
            />
          </template>
        </el-table-column>
        
        <el-table-column label="推荐" width="60">
          <template #default="{ row }">
            <el-switch 
              v-model="row.is_featured" 
              @change="toggleFeatured(row)"
              size="small"
              :disabled="row.status !== 'PUBLISHED'"
            />
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="180">
          <template #default="{ row }">
            <div class="status-cell">
              <!-- 已发布 -->
              <template v-if="row.status === 'PUBLISHED'">
                <div class="published-status">
                  <el-icon class="check-icon"><CircleCheck /></el-icon>
                  <span>已发布</span>
                </div>
              </template>
              
              <!-- 处理中 - 显示进度 -->
              <template v-else-if="row.status === 'PROCESSING'">
                <div class="progress-wrapper">
                  <div class="progress-header">
                    <el-icon class="status-icon is-loading"><Loading /></el-icon>
                    <span>转码中</span>
                    <span class="progress-percent">{{ row._progress || 0 }}%</span>
                  </div>
                  <el-progress 
                    :percentage="row._progress || 0" 
                    :stroke-width="6"
                    :show-text="false"
                    :color="getProgressColor(row._progress)"
                  />
                  <div class="progress-stage">{{ getProgressStage(row._progress) }}</div>
                </div>
              </template>
              
              <!-- 审核中 -->
              <template v-else-if="row.status === 'REVIEWING'">
                <el-tag type="info" size="small">
                  <el-icon class="status-icon"><Clock /></el-icon>
                  审核中
            </el-tag>
              </template>
              
              <!-- 失败 -->
              <template v-else-if="row.status === 'FAILED'">
                <el-tooltip :content="row.error_message || '转码失败'" placement="top">
                  <el-tag type="danger" size="small">
                    <el-icon class="status-icon"><CircleClose /></el-icon>
                    失败
                  </el-tag>
                </el-tooltip>
              </template>
              
              <!-- 其他 -->
              <template v-else>
                <el-tag size="small">{{ row.status }}</el-tag>
              </template>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="上传时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button 
              v-if="row.status === 'PUBLISHED'" 
              link 
              type="primary" 
              @click="viewVideo(row)"
            >
              查看
            </el-button>
            
            <el-button link type="primary" @click="editVideo(row)">编辑</el-button>
            
            <!-- 重新转码按钮 - 失败或处理中都可以重试 -->
            <el-button 
              v-if="row.status === 'FAILED' || row.status === 'PROCESSING'" 
              link 
              type="warning"
              @click="retryTranscode(row)"
              :loading="row._retrying"
            >
              <el-icon><RefreshRight /></el-icon>
              重新转码
            </el-button>
            
            <el-popconfirm title="确定删除这个视频吗？" @confirm="deleteVideo(row)">
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
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchVideos"
          @current-change="fetchVideos"
        />
      </div>
    </el-card>
    
    <!-- 编辑对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑视频" width="550px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="editForm.title" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="分类">
          <el-cascader
            v-model="editCategoryPath"
            :options="categories"
            :props="{ value: 'id', label: 'name', children: 'children', emitPath: false, checkStrictly: true }"
            placeholder="请选择分类"
            style="width: 100%"
            clearable
            @change="handleEditCategoryChange"
          />
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="editForm.tags"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入或选择标签"
            style="width: 100%"
          >
            <el-option v-for="tag in allTags" :key="tag" :label="tag" :value="tag" />
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
        <el-button type="primary" @click="saveVideo" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import api from '@/utils/api'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { 
  Upload, Search, FolderAdd, Loading, CircleCheck, 
  CircleClose, Clock, RefreshRight 
} from '@element-plus/icons-vue'

const loading = ref(false)
const saving = ref(false)
const videos = ref([])
const categories = ref([])
const allTags = ref([])

// 自动刷新定时器
let refreshTimer = null
let progressTimer = null

const filters = reactive({
  search: '',
  status: '',
  category: '',
  video_type: 'normal'  // 默认只显示长视频
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const fetchVideos = async () => {
  loading.value = true
  try {
    const res = await api.get('/admin/videos', {
      params: {
        page: pagination.page,
        page_size: pagination.pageSize,
        search: filters.search || undefined,
        status: filters.status || undefined,
        category_id: filters.category || undefined,
        is_short: filters.video_type === 'short' ? true : (filters.video_type === 'normal' ? false : undefined)
      }
    })
    videos.value = (res.data?.items || []).map(v => ({
      ...v,
      status: (v.status || '').toUpperCase(),
      _retrying: false,
      _progress: 0
    }))
    pagination.total = res.data?.total || 0
    
    // 获取处理中视频的进度
    const processingIds = videos.value
      .filter(v => v.status === 'PROCESSING')
      .map(v => v.id)
    
    if (processingIds.length > 0) {
      await fetchProgress(processingIds)
      
      // 开启进度轮询
      if (!progressTimer) {
        progressTimer = setInterval(() => fetchProgress(processingIds), 2000)
      }
    }
    
    // 如果有处理中的视频，开启状态刷新
    const hasProcessing = processingIds.length > 0
    if (hasProcessing && !refreshTimer) {
      refreshTimer = setInterval(fetchVideos, 10000) // 每10秒刷新状态
    } else if (!hasProcessing) {
      if (refreshTimer) {
        clearInterval(refreshTimer)
        refreshTimer = null
      }
      if (progressTimer) {
        clearInterval(progressTimer)
        progressTimer = null
      }
    }
  } catch (error) {
    console.error('获取视频列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 获取转码进度
const fetchProgress = async (videoIds) => {
  try {
    const res = await api.post('/admin/videos/progress/batch', videoIds)
    const progressData = res.data?.progress || res.progress || {}
    
    // 更新视频进度
    videos.value.forEach(v => {
      if (progressData[v.id] !== undefined) {
        v._progress = progressData[v.id]
      }
    })
  } catch (e) {
    console.error('获取进度失败', e)
  }
}

// 进度颜色
const getProgressColor = (progress) => {
  if (progress < 30) return '#e6a23c'
  if (progress < 70) return '#409eff'
  return '#67c23a'
}

// 进度阶段文字
const getProgressStage = (progress) => {
  if (!progress || progress < 10) return '准备中...'
  if (progress < 20) return '获取信息...'
  if (progress < 30) return '生成封面...'
  if (progress < 40) return '生成预览...'
  if (progress < 80) return '视频转码...'
  if (progress < 100) return 'AI分析...'
  return '即将完成'
}

const fetchCategories = async () => {
  try {
    // 获取树形分类结构（用于 cascader 和 select）
    const res = await api.get('/videos/categories')
    // 过滤只保留普通视频分类
    categories.value = (res.data || []).filter(
      c => !c.category_type || c.category_type === 'video' || c.category_type === 'both'
    )
    console.log('获取分类成功:', categories.value.length, '个')
  } catch (error) {
    console.error('获取分类失败:', error)
    categories.value = []
  }
}

const fetchTags = async () => {
  try {
    const res = await api.get('/admin/tags')
    allTags.value = (res.data || []).map(tag => tag.name)
    console.log('获取标签成功:', allTags.value.length, '个')
  } catch (error) {
    console.error('获取标签失败:', error)
    allTags.value = []
  }
}

const resetFilters = () => {
  filters.search = ''
  filters.status = ''
  filters.category = ''
  filters.video_type = 'normal'  // 重置时仍默认只显示长视频
  pagination.page = 1
  fetchVideos()
}

const toggleFeatured = async (row) => {
  try {
    await api.put(`/admin/videos/${row.id}/featured`)
    ElMessage.success(row.is_featured ? '已设为推荐' : '已取消推荐')
  } catch (error) {
    row.is_featured = !row.is_featured
  }
}

const toggleShort = async (row) => {
  try {
    await api.put(`/admin/videos/${row.id}`, { is_short: row.is_short })
    ElMessage.success(row.is_short ? '已设为短视频' : '已设为长视频')
  } catch (error) {
    row.is_short = !row.is_short
    ElMessage.error('操作失败')
  }
}

const viewVideo = (row) => {
  window.open(`/user/video/${row.id}`, '_blank')
}

// 重新转码
const retryTranscode = async (row) => {
  row._retrying = true
  try {
    await api.post(`/admin/videos/${row.id}/retry-transcode`)
    ElMessage.success('已开始重新转码')
    row.status = 'PROCESSING'
    
    // 开启自动刷新
    if (!refreshTimer) {
      refreshTimer = setInterval(fetchVideos, 5000)
    }
  } catch (error) {
    ElMessage.error('重新转码失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    row._retrying = false
  }
}

// 编辑相关
const editDialogVisible = ref(false)
const editCategoryPath = ref(null)
const editForm = reactive({
  id: 0,
  title: '',
  description: '',
  category_id: null,
  tags: [],
  coin_price: 0,
  is_vip_only: false,
  is_featured: false
})

const handleEditCategoryChange = (value) => {
  editForm.category_id = value
}

const editVideo = async (row) => {
  editForm.id = row.id
  editForm.title = row.title || ''
  editForm.description = row.description || ''
  editForm.category_id = row.category_id || null
  editCategoryPath.value = row.category_id || null
  editForm.tags = row.tags || []
  editForm.coin_price = row.coin_price || 0
  editForm.is_vip_only = row.is_vip_only || false
  editForm.is_featured = row.is_featured || false
  editDialogVisible.value = true
}

const saveVideo = async () => {
  saving.value = true
  try {
    await api.put(`/admin/videos/${editForm.id}`, {
      title: editForm.title,
      description: editForm.description,
      category_id: editForm.category_id,
      tags: editForm.tags,
      coin_price: editForm.coin_price,
      is_vip_only: editForm.is_vip_only,
      is_featured: editForm.is_featured
    })
    ElMessage.success('保存成功')
    editDialogVisible.value = false
    fetchVideos()
  } catch (error) {
    // 错误已处理
  } finally {
    saving.value = false
  }
}

const deleteVideo = async (row) => {
  try {
    await api.delete(`/admin/videos/${row.id}`)
    ElMessage.success('删除成功')
    fetchVideos()
  } catch (error) {
    // 错误已处理
  }
}

const formatDuration = (seconds) => {
  if (!seconds || isNaN(seconds)) return '0:00'
  seconds = Math.floor(seconds)
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  return `${m}:${s.toString().padStart(2, '0')}`
}

const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

const getCoverUrl = (url) => {
  if (!url) return '/placeholder.webp'
  if (url.startsWith('http') || url.startsWith('/')) return url
  return '/' + url
}

onMounted(() => {
  fetchVideos()
  fetchCategories()
  fetchTags()
})

onUnmounted(() => {
  // 清理定时器
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
  if (progressTimer) {
    clearInterval(progressTimer)
    progressTimer = null
  }
})
</script>

<style lang="scss" scoped>
.videos-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .header-actions {
      display: flex;
      gap: 8px;
    }
  }
  
  .filter-bar {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
    flex-wrap: wrap;
  }
  
  .status-cell {
    .published-status {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 12px;
      background: linear-gradient(135deg, rgba(103, 194, 58, 0.1), rgba(103, 194, 58, 0.05));
      border: 1px solid rgba(103, 194, 58, 0.3);
      border-radius: 16px;
      color: #67c23a;
      font-size: 13px;
      font-weight: 500;
      
      .check-icon {
        font-size: 14px;
        color: #67c23a;
      }
    }
    
    .el-tag {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      
      .status-icon {
        font-size: 12px;
        
        &.is-loading {
          animation: rotating 2s linear infinite;
        }
      }
    }
    
    .progress-wrapper {
      width: 100%;
      
      .progress-header {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;
        color: #e6a23c;
        margin-bottom: 4px;
        
        .status-icon {
          font-size: 12px;
          
          &.is-loading {
            animation: rotating 2s linear infinite;
          }
        }
        
        .progress-percent {
          margin-left: auto;
          font-weight: 600;
          color: #409eff;
        }
      }
      
      .progress-stage {
        font-size: 11px;
        color: #909399;
        margin-top: 2px;
      }
      
      :deep(.el-progress-bar__outer) {
        background-color: rgba(0, 0, 0, 0.1);
      }
    }
  }
  
  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
  
  .image-error {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100px;
    height: 56px;
    background: #f5f7fa;
    color: #909399;
    font-size: 12px;
    
    .el-icon {
      font-size: 20px;
      animation: rotating 2s linear infinite;
    }
  }
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>