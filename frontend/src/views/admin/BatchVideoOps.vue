<template>
  <div class="batch-video-ops">
    <div class="page-header">
      <h1>视频批量操作</h1>
      <div class="header-actions">
        <el-button type="primary" :disabled="!selectedVideos.length" @click="showBatchStatusDialog">
          批量修改状态 ({{ selectedVideos.length }})
        </el-button>
        <el-button type="warning" :disabled="!selectedVideos.length" @click="showBatchCategoryDialog">
          批量修改分类 ({{ selectedVideos.length }})
        </el-button>
        <el-button type="danger" :disabled="!selectedVideos.length" @click="batchDelete">
          批量删除 ({{ selectedVideos.length }})
        </el-button>
      </div>
    </div>

    <!-- 筛选 -->
    <div class="filter-bar">
      <el-input 
        v-model="filters.keyword" 
        placeholder="搜索视频标题" 
        clearable 
        style="width: 200px;"
        @keyup.enter="fetchVideos"
      />
      <el-select v-model="filters.category_id" placeholder="分类" clearable @change="fetchVideos">
        <el-option 
          v-for="cat in categories" 
          :key="cat.id" 
          :label="cat.name" 
          :value="cat.id" 
        />
      </el-select>
      <el-select v-model="filters.status" placeholder="状态" clearable @change="fetchVideos">
        <el-option label="正常" value="active" />
        <el-option label="待审核" value="pending" />
        <el-option label="已禁用" value="disabled" />
        <el-option label="处理中" value="processing" />
      </el-select>
      <el-select v-model="filters.is_vip" placeholder="VIP" clearable @change="fetchVideos">
        <el-option label="VIP视频" :value="true" />
        <el-option label="免费视频" :value="false" />
      </el-select>
      <el-button type="primary" @click="fetchVideos">搜索</el-button>
      <el-button @click="resetFilters">重置</el-button>
    </div>

    <!-- 视频列表 -->
    <el-table 
      :data="videos" 
      v-loading="loading" 
      border 
      stripe
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="50" />
      <el-table-column label="封面" width="120">
        <template #default="{ row }">
          <el-image 
            :src="row.thumbnail || row.cover_url" 
            fit="cover"
            style="width: 100px; height: 60px; border-radius: 4px;"
          >
            <template #error>
              <div class="image-placeholder">
                <el-icon><VideoCamera /></el-icon>
              </div>
            </template>
          </el-image>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="category_name" label="分类" width="100" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)">
            {{ statusMap[row.status] || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="VIP" width="80">
        <template #default="{ row }">
          <el-tag v-if="row.is_vip" type="warning">VIP</el-tag>
          <span v-else class="text-muted">免费</span>
        </template>
      </el-table-column>
      <el-table-column prop="view_count" label="播放量" width="100" />
      <el-table-column prop="like_count" label="点赞" width="80" />
      <el-table-column label="创建时间" width="170">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @size-change="fetchVideos"
        @current-change="fetchVideos"
      />
    </div>

    <!-- 批量修改状态对话框 -->
    <el-dialog v-model="statusDialogVisible" title="批量修改状态" width="400px">
      <el-form label-width="80px">
        <el-form-item label="新状态">
          <el-select v-model="batchStatus" placeholder="请选择状态">
            <el-option label="正常" value="active" />
            <el-option label="待审核" value="pending" />
            <el-option label="已禁用" value="disabled" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="statusDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmBatchStatus" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 批量修改分类对话框 -->
    <el-dialog v-model="categoryDialogVisible" title="批量修改分类" width="400px">
      <el-form label-width="80px">
        <el-form-item label="新分类">
          <el-select v-model="batchCategory" placeholder="请选择分类">
            <el-option 
              v-for="cat in categories" 
              :key="cat.id" 
              :label="cat.name" 
              :value="cat.id" 
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="categoryDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmBatchCategory" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoCamera } from '@element-plus/icons-vue'
import api from '@/utils/api'

const loading = ref(false)
const videos = ref([])
const categories = ref([])
const selectedVideos = ref([])
const submitting = ref(false)

const statusDialogVisible = ref(false)
const categoryDialogVisible = ref(false)
const batchStatus = ref('')
const batchCategory = ref(null)

const filters = reactive({
  keyword: '',
  category_id: null,
  status: '',
  is_vip: null
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const statusMap = {
  active: '正常',
  pending: '待审核',
  disabled: '已禁用',
  processing: '处理中',
  failed: '处理失败'
}

onMounted(() => {
  fetchCategories()
  fetchVideos()
})

const fetchCategories = async () => {
  try {
    const res = await api.get('/videos/categories')
    categories.value = res.data || res || []
  } catch (error) {
    console.error('获取分类失败:', error)
  }
}

const fetchVideos = async () => {
  loading.value = true
  selectedVideos.value = []
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.category_id) params.category_id = filters.category_id
    if (filters.status) params.status = filters.status
    if (filters.is_vip !== null && filters.is_vip !== '') {
      params.is_vip = filters.is_vip
    }
    
    const res = await api.get('/admin/videos', { params })
    const data = res.data || res
    videos.value = data.items || data.videos || []
    pagination.total = data.total || 0
  } catch (error) {
    console.error('获取视频列表失败:', error)
    ElMessage.error('获取视频列表失败')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.keyword = ''
  filters.category_id = null
  filters.status = ''
  filters.is_vip = null
  pagination.page = 1
  fetchVideos()
}

const handleSelectionChange = (selection) => {
  selectedVideos.value = selection
}

const statusTagType = (status) => {
  const types = {
    active: 'success',
    pending: 'warning',
    disabled: 'danger',
    processing: 'info',
    failed: 'danger'
  }
  return types[status] || 'info'
}

const showBatchStatusDialog = () => {
  batchStatus.value = ''
  statusDialogVisible.value = true
}

const showBatchCategoryDialog = () => {
  batchCategory.value = null
  categoryDialogVisible.value = true
}

const confirmBatchStatus = async () => {
  if (!batchStatus.value) {
    ElMessage.warning('请选择状态')
    return
  }

  submitting.value = true
  try {
    let successCount = 0
    let failCount = 0
    
    for (const video of selectedVideos.value) {
      try {
        await api.put(`/admin/videos/${video.id}/status`, {
          status: batchStatus.value
        })
        successCount++
      } catch {
        failCount++
      }
    }
    
    statusDialogVisible.value = false
    ElMessage.success(`批量修改完成: 成功 ${successCount} 个, 失败 ${failCount} 个`)
    fetchVideos()
  } catch (error) {
    console.error('批量修改状态失败:', error)
    ElMessage.error('批量修改状态失败')
  } finally {
    submitting.value = false
  }
}

const confirmBatchCategory = async () => {
  if (!batchCategory.value) {
    ElMessage.warning('请选择分类')
    return
  }

  submitting.value = true
  try {
    let successCount = 0
    let failCount = 0
    
    for (const video of selectedVideos.value) {
      try {
        await api.put(`/admin/videos/${video.id}`, {
          category_id: batchCategory.value
        })
        successCount++
      } catch {
        failCount++
      }
    }
    
    categoryDialogVisible.value = false
    ElMessage.success(`批量修改完成: 成功 ${successCount} 个, 失败 ${failCount} 个`)
    fetchVideos()
  } catch (error) {
    console.error('批量修改分类失败:', error)
    ElMessage.error('批量修改分类失败')
  } finally {
    submitting.value = false
  }
}

const batchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedVideos.value.length} 个视频吗? 此操作不可恢复!`,
      '警告',
      { type: 'warning' }
    )

    submitting.value = true
    let successCount = 0
    let failCount = 0
    
    for (const video of selectedVideos.value) {
      try {
        await api.delete(`/admin/videos/${video.id}`)
        successCount++
      } catch {
        failCount++
      }
    }
    
    ElMessage.success(`批量删除完成: 成功 ${successCount} 个, 失败 ${failCount} 个`)
    fetchVideos()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error('批量删除失败')
    }
  } finally {
    submitting.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style lang="scss" scoped>
.batch-video-ops {
  padding: 20px;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    h1 {
      font-size: 24px;
      margin: 0;
    }
    
    .header-actions {
      display: flex;
      gap: 10px;
    }
  }
  
  .filter-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 16px;
    
    .el-select {
      width: 150px;
    }
  }
  
  .pagination {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
  }
  
  .text-muted {
    color: #999;
  }
  
  .image-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f5f5f5;
    color: #999;
    
    .el-icon {
      font-size: 24px;
    }
  }
}
</style>





