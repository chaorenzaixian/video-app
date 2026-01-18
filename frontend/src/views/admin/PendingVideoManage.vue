<template>
  <div class="pending-video-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>待处理视频</span>
          <div class="header-stats">
            <el-tag type="warning">待处理: {{ pagination.total }}</el-tag>
          </div>
        </div>
      </template>

      <!-- 筛选栏 -->
      <div class="filter-bar">
        <el-input
          v-model="filters.search"
          placeholder="搜索视频标题..."
          clearable
          style="width: 200px"
          @keyup.enter="fetchVideos"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>

        <el-select v-model="filters.videoType" placeholder="视频类型" clearable style="width: 120px">
          <el-option label="全部" value="" />
          <el-option label="长视频" value="long" />
          <el-option label="短视频" value="short" />
        </el-select>

        <el-button type="primary" @click="fetchVideos">
          <el-icon><Search /></el-icon>搜索
        </el-button>

        <el-button @click="resetFilters">重置</el-button>

        <el-button
          type="success"
          :disabled="selectedIds.length === 0"
          @click="batchPublish"
        >
          批量发布 ({{ selectedIds.length }})
        </el-button>
      </div>

      <!-- 视频列表 -->
      <el-table
        :data="videos"
        v-loading="loading"
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" />

        <el-table-column label="封面" width="140">
          <template #default="{ row }">
            <div class="cover-cell" @click="openCoverSelector(row)">
              <el-image
                :src="getCoverUrl(row.cover_url)"
                fit="cover"
                class="video-cover"
              >
                <template #error>
                  <div class="image-error">无封面</div>
                </template>
              </el-image>
              <div class="cover-overlay">
                <el-icon><Picture /></el-icon>
                <span>更换</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="视频信息" min-width="250">
          <template #default="{ row }">
            <div class="video-info">
              <div class="video-title">{{ row.title }}</div>
              <div class="video-meta">
                <el-tag :type="row.is_short ? 'success' : 'primary'" size="small">
                  {{ row.is_short ? '短视频' : '长视频' }}
                </el-tag>
                <span class="duration">{{ formatDuration(row.duration) }}</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="分类" width="120">
          <template #default="{ row }">
            <el-select
              v-model="row.category_id"
              placeholder="选择分类"
              size="small"
              @change="updateField(row, 'category_id', row.category_id)"
            >
              <el-option
                v-for="cat in categories"
                :key="cat.id"
                :label="cat.name"
                :value="cat.id"
              />
            </el-select>
          </template>
        </el-table-column>

        <el-table-column label="付费设置" width="180">
          <template #default="{ row }">
            <div class="price-setting">
              <el-checkbox
                v-model="row.is_vip_only"
                @change="updateField(row, 'is_vip_only', row.is_vip_only)"
              >
                VIP专属
              </el-checkbox>
              <div class="price-input">
                <span>金币:</span>
                <el-input-number
                  v-model="row.coin_price"
                  :min="0"
                  :max="9999"
                  size="small"
                  controls-position="right"
                  @change="updateField(row, 'coin_price', row.coin_price)"
                />
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="推荐" width="70">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_featured"
              size="small"
              @change="updateField(row, 'is_featured', row.is_featured)"
            />
          </template>
        </el-table-column>

        <el-table-column label="上传时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="previewVideo(row)">
              预览
            </el-button>
            <el-button link type="primary" @click="openEditDialog(row)">
              编辑
            </el-button>
            <el-button link type="success" @click="publishSingle(row)">
              发布
            </el-button>
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

    <!-- 封面选择对话框 -->
    <el-dialog v-model="coverDialog.visible" title="选择封面" width="800px">
      <div class="cover-grid" v-loading="coverDialog.loading">
        <div
          v-for="cover in coverDialog.covers"
          :key="cover.index"
          class="cover-item"
          :class="{ active: cover.url === coverDialog.selectedCover }"
          @click="coverDialog.selectedCover = cover.url"
        >
          <el-image :src="getCoverUrl(cover.url)" fit="cover">
            <template #error>
              <div class="cover-error">加载失败</div>
            </template>
          </el-image>
          <div class="cover-index">{{ cover.index }}</div>
          <div v-if="cover.is_current" class="current-badge">当前</div>
        </div>
      </div>
      <template #footer>
        <el-button @click="coverDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="saveCover" :loading="coverDialog.saving">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog v-model="editDialog.visible" title="编辑视频" width="600px">
      <el-form :model="editDialog.form" label-width="100px">
        <el-form-item label="标题">
          <el-input v-model="editDialog.form.title" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editDialog.form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="editDialog.form.category_id" placeholder="选择分类" style="width: 100%">
            <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="VIP专属">
          <el-switch v-model="editDialog.form.is_vip_only" />
        </el-form-item>
        <el-form-item label="金币价格">
          <el-input-number v-model="editDialog.form.coin_price" :min="0" :max="9999" />
          <span style="margin-left: 8px; color: #909399;">0 表示免费</span>
        </el-form-item>
        <el-form-item label="推荐">
          <el-switch v-model="editDialog.form.is_featured" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit(false)" :loading="editDialog.saving">
          仅保存
        </el-button>
        <el-button type="success" @click="saveEdit(true)" :loading="editDialog.saving">
          保存并发布
        </el-button>
      </template>
    </el-dialog>

    <!-- 视频预览对话框 -->
    <el-dialog v-model="previewDialog.visible" title="视频预览" width="800px" destroy-on-close>
      <video
        v-if="previewDialog.video"
        :src="getVideoUrl(previewDialog.video)"
        controls
        style="width: 100%; max-height: 450px;"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Picture } from '@element-plus/icons-vue'
import api from '@/utils/api'
import dayjs from 'dayjs'

const loading = ref(false)
const videos = ref([])
const categories = ref([])
const selectedIds = ref([])

const filters = reactive({
  search: '',
  videoType: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 封面选择对话框
const coverDialog = reactive({
  visible: false,
  loading: false,
  saving: false,
  videoId: null,
  covers: [],
  selectedCover: ''
})

// 编辑对话框
const editDialog = reactive({
  visible: false,
  saving: false,
  videoId: null,
  form: {
    title: '',
    description: '',
    category_id: null,
    coin_price: 0,
    is_vip_only: false,
    is_featured: false
  }
})

// 预览对话框
const previewDialog = reactive({
  visible: false,
  video: null
})

// 获取待处理视频列表
const fetchVideos = async () => {
  loading.value = true
  try {
    const res = await api.get('/admin/videos/pending', {
      params: {
        page: pagination.page,
        page_size: pagination.pageSize,
        video_type: filters.videoType || undefined,
        search: filters.search || undefined
      }
    })
    videos.value = res.data?.items || res.items || []
    pagination.total = res.data?.total || res.total || 0
  } catch (error) {
    console.error('获取待处理视频失败:', error)
    ElMessage.error('获取视频列表失败')
  } finally {
    loading.value = false
  }
}

// 获取分类列表
const fetchCategories = async () => {
  try {
    const res = await api.get('/videos/categories')
    categories.value = res.data || []
  } catch (error) {
    console.error('获取分类失败:', error)
  }
}

// 重置筛选
const resetFilters = () => {
  filters.search = ''
  filters.videoType = ''
  pagination.page = 1
  fetchVideos()
}

// 选择变化
const handleSelectionChange = (selection) => {
  selectedIds.value = selection.map(v => v.id)
}

// 更新单个字段
const updateField = async (row, field, value) => {
  try {
    await api.put(`/admin/videos/${row.id}`, { [field]: value })
  } catch (error) {
    ElMessage.error('更新失败')
  }
}

// 打开封面选择器
const openCoverSelector = async (row) => {
  coverDialog.videoId = row.id
  coverDialog.selectedCover = row.cover_url
  coverDialog.visible = true
  coverDialog.loading = true

  try {
    const res = await api.get(`/admin/videos/${row.id}/covers`)
    coverDialog.covers = res.data?.covers || res.covers || []
    coverDialog.selectedCover = res.data?.current_cover || res.current_cover || ''
  } catch (error) {
    console.error('获取封面列表失败:', error)
    ElMessage.error('获取封面列表失败')
  } finally {
    coverDialog.loading = false
  }
}

// 保存封面
const saveCover = async () => {
  if (!coverDialog.selectedCover) {
    ElMessage.warning('请选择封面')
    return
  }

  coverDialog.saving = true
  try {
    await api.put(`/admin/videos/${coverDialog.videoId}/cover`, null, {
      params: { cover_url: coverDialog.selectedCover }
    })
    ElMessage.success('封面已更新')
    coverDialog.visible = false

    // 更新列表中的封面
    const video = videos.value.find(v => v.id === coverDialog.videoId)
    if (video) {
      video.cover_url = coverDialog.selectedCover
    }
  } catch (error) {
    ElMessage.error('更新封面失败')
  } finally {
    coverDialog.saving = false
  }
}

// 打开编辑对话框
const openEditDialog = (row) => {
  editDialog.videoId = row.id
  editDialog.form = {
    title: row.title,
    description: row.description || '',
    category_id: row.category_id,
    coin_price: row.coin_price || 0,
    is_vip_only: row.is_vip_only || false,
    is_featured: row.is_featured || false
  }
  editDialog.visible = true
}

// 保存编辑
const saveEdit = async (publish) => {
  editDialog.saving = true
  try {
    await api.put(`/admin/videos/${editDialog.videoId}/update-and-publish`, {
      ...editDialog.form,
      publish
    })
    ElMessage.success(publish ? '视频已发布' : '保存成功')
    editDialog.visible = false
    fetchVideos()
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    editDialog.saving = false
  }
}

// 单个发布
const publishSingle = async (row) => {
  try {
    await ElMessageBox.confirm(`确定发布视频 "${row.title}" 吗？`, '确认发布', {
      confirmButtonText: '发布',
      cancelButtonText: '取消',
      type: 'info'
    })

    await api.put(`/admin/videos/${row.id}/update-and-publish`, { publish: true })
    ElMessage.success('视频已发布')
    fetchVideos()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('发布失败')
    }
  }
}

// 批量发布
const batchPublish = async () => {
  if (selectedIds.value.length === 0) return

  try {
    await ElMessageBox.confirm(
      `确定发布选中的 ${selectedIds.value.length} 个视频吗？`,
      '批量发布',
      {
        confirmButtonText: '发布',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    await api.post('/admin/videos/batch-publish', selectedIds.value)
    ElMessage.success(`已发布 ${selectedIds.value.length} 个视频`)
    selectedIds.value = []
    fetchVideos()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量发布失败')
    }
  }
}

// 预览视频
const previewVideo = (row) => {
  previewDialog.video = row
  previewDialog.visible = true
}

// 工具函数
const getCoverUrl = (url) => {
  if (!url) return '/placeholder.webp'
  if (url.startsWith('http') || url.startsWith('/')) return url
  return '/' + url
}

const getVideoUrl = (video) => {
  if (video.is_short) {
    return video.hls_url || video.original_url
  }
  // 长视频使用预览或 HLS
  return video.preview_url || video.hls_url
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

onMounted(() => {
  fetchVideos()
  fetchCategories()
})
</script>

<style lang="scss" scoped>
.pending-video-page {
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

  .cover-cell {
    position: relative;
    cursor: pointer;
    width: 120px;
    height: 68px;
    border-radius: 4px;
    overflow: hidden;

    .video-cover {
      width: 100%;
      height: 100%;
    }

    .cover-overlay {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      color: #fff;
      opacity: 0;
      transition: opacity 0.2s;
      font-size: 12px;

      .el-icon {
        font-size: 20px;
        margin-bottom: 4px;
      }
    }

    &:hover .cover-overlay {
      opacity: 1;
    }
  }

  .video-info {
    .video-title {
      font-weight: 500;
      margin-bottom: 6px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .video-meta {
      display: flex;
      align-items: center;
      gap: 8px;

      .duration {
        font-size: 12px;
        color: #909399;
      }
    }
  }

  .price-setting {
    .price-input {
      display: flex;
      align-items: center;
      gap: 4px;
      margin-top: 4px;
      font-size: 12px;

      .el-input-number {
        width: 100px;
      }
    }
  }

  .image-error {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
    height: 100%;
    background: #f5f7fa;
    color: #909399;
    font-size: 12px;
  }

  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}

// 封面选择网格
.cover-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  min-height: 200px;

  .cover-item {
    position: relative;
    aspect-ratio: 16/9;
    border-radius: 4px;
    overflow: hidden;
    cursor: pointer;
    border: 2px solid transparent;
    transition: all 0.2s;

    &:hover {
      border-color: #409eff;
    }

    &.active {
      border-color: #67c23a;
    }

    .el-image {
      width: 100%;
      height: 100%;
    }

    .cover-index {
      position: absolute;
      bottom: 4px;
      right: 4px;
      background: rgba(0, 0, 0, 0.6);
      color: #fff;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 12px;
    }

    .current-badge {
      position: absolute;
      top: 4px;
      left: 4px;
      background: #67c23a;
      color: #fff;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 10px;
    }

    .cover-error {
      display: flex;
      justify-content: center;
      align-items: center;
      width: 100%;
      height: 100%;
      background: #f5f7fa;
      color: #909399;
      font-size: 12px;
    }
  }
}
</style>
