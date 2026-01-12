<template>
  <div class="ads-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>广告管理</span>
          <el-button type="primary" @click="openAddDialog">
            <el-icon><Plus /></el-icon>
            新增广告
          </el-button>
        </div>
      </template>

      <!-- 筛选 -->
      <div class="filter-bar">
        <el-select v-model="filters.position" placeholder="广告位置" clearable style="width: 150px" @change="fetchAds">
          <el-option label="首页横幅" value="HOME_BANNER" />
          <el-option label="首页弹窗" value="HOME_POPUP" />
          <el-option label="视频前贴" value="VIDEO_PRE" />
          <el-option label="视频中插" value="VIDEO_MID" />
          <el-option label="视频后贴" value="VIDEO_POST" />
          <el-option label="侧边栏" value="SIDEBAR" />
          <el-option label="信息流" value="FEED" />
        </el-select>
        <el-select v-model="filters.ad_type" placeholder="广告类型" clearable style="width: 120px" @change="fetchAds">
          <el-option label="图片" value="IMAGE" />
          <el-option label="视频" value="VIDEO" />
          <el-option label="HTML" value="HTML" />
        </el-select>
      </div>

      <el-table :data="ads" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="预览" width="120">
          <template #default="{ row }">
            <el-image 
              v-if="row.ad_type === 'image'" 
              :src="row.media_url" 
              style="width: 80px; height: 45px; object-fit: cover; border-radius: 4px;"
              fit="cover"
            />
            <el-tag v-else-if="row.ad_type === 'video'" type="primary" size="small">视频广告</el-tag>
            <el-tag v-else type="info" size="small">HTML</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="150" />
        <el-table-column label="位置" width="100">
          <template #default="{ row }">
            <el-tag :type="getPositionType(row.position)" size="small">
              {{ getPositionLabel(row.position) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="时长(秒)" width="80" />
        <el-table-column prop="impression_count" label="展示" width="80" />
        <el-table-column prop="click_count" label="点击" width="80" />
        <el-table-column label="CTR" width="80">
          <template #default="{ row }">
            {{ row.impression_count > 0 ? ((row.click_count / row.impression_count) * 100).toFixed(2) : 0 }}%
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-switch v-model="row.is_active" @change="toggleStatus(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEditDialog(row)">编辑</el-button>
            <el-button link type="danger" @click="deleteAd(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchAds"
          @current-change="fetchAds"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog 
      v-model="showDialog" 
      :title="isEdit ? '编辑广告' : '新增广告'" 
      width="600px"
      destroy-on-close
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="广告标题" required>
          <el-input v-model="form.title" placeholder="请输入广告标题" />
        </el-form-item>
        <el-form-item label="广告描述">
          <el-input v-model="form.description" type="textarea" rows="2" placeholder="广告描述（可选）" />
        </el-form-item>
        <el-form-item label="广告位置" required>
          <el-select v-model="form.position" style="width: 100%">
            <el-option label="首页横幅" value="HOME_BANNER" />
            <el-option label="首页弹窗" value="HOME_POPUP" />
            <el-option label="视频前贴（5秒）" value="VIDEO_PRE" />
            <el-option label="视频中插" value="VIDEO_MID" />
            <el-option label="视频后贴" value="VIDEO_POST" />
            <el-option label="侧边栏" value="SIDEBAR" />
            <el-option label="信息流" value="FEED" />
          </el-select>
        </el-form-item>
        <el-form-item label="广告类型" required>
          <el-radio-group v-model="form.ad_type">
            <el-radio-button label="IMAGE">图片</el-radio-button>
            <el-radio-button label="VIDEO">视频</el-radio-button>
            <el-radio-button label="HTML">HTML</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="媒体文件" v-if="form.ad_type !== 'html'">
          <el-upload
            class="media-uploader"
            :action="uploadUrl"
            :headers="uploadHeaders"
            :show-file-list="false"
            :on-success="handleUploadSuccess"
            :accept="form.ad_type === 'video' ? 'video/*' : 'image/*'"
          >
            <div v-if="form.media_url" class="media-preview">
              <el-image v-if="form.ad_type === 'image'" :src="form.media_url" fit="cover" />
              <video v-else :src="form.media_url" style="max-width: 100%; max-height: 150px;" />
            </div>
            <div v-else class="upload-placeholder">
              <el-icon><Upload /></el-icon>
              <span>点击上传{{ form.ad_type === 'video' ? '视频' : '图片' }}</span>
            </div>
          </el-upload>
        </el-form-item>
        <el-form-item label="HTML内容" v-if="form.ad_type === 'html'">
          <el-input v-model="form.html_content" type="textarea" rows="4" placeholder="输入HTML代码" />
        </el-form-item>
        <el-form-item label="跳转链接">
          <el-input v-model="form.target_url" placeholder="点击广告跳转的URL" />
        </el-form-item>
        <el-form-item label="展示时长">
          <el-input-number v-model="form.duration" :min="1" :max="60" />
          <span style="margin-left: 8px; color: #909399;">秒</span>
        </el-form-item>
        <el-form-item label="有效期">
          <el-date-picker
            v-model="form.dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="优先级">
          <el-input-number v-model="form.priority" :min="0" :max="100" />
          <span style="margin-left: 8px; color: #909399;">数字越大优先级越高</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveAd" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import api from '@/utils/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload } from '@element-plus/icons-vue'

const loading = ref(false)
const saving = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const ads = ref([])

const filters = reactive({
  position: '',
  ad_type: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const form = reactive({
  id: null,
  title: '',
  description: '',
  ad_type: 'IMAGE',
  media_url: '',
  html_content: '',
  target_url: '',
  position: 'VIDEO_PRE',
  duration: 5,
  priority: 0,
  dateRange: null
})

const uploadUrl = computed(() => '/api/v1/ads/upload/image')
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`
}))

const positionLabels = {
  HOME_BANNER: '首页横幅',
  HOME_POPUP: '首页弹窗',
  VIDEO_PRE: '视频前贴',
  VIDEO_MID: '视频中插',
  VIDEO_POST: '视频后贴',
  SIDEBAR: '侧边栏',
  FEED: '信息流'
}

const positionTypes = {
  VIDEO_PRE: 'danger',
  VIDEO_MID: 'warning',
  VIDEO_POST: 'info',
  HOME_BANNER: 'success',
  HOME_POPUP: 'primary',
  SIDEBAR: '',
  FEED: ''
}

const getPositionLabel = (position) => positionLabels[position] || position
const getPositionType = (position) => positionTypes[position] || ''

const fetchAds = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    if (filters.position) params.position = filters.position
    if (filters.ad_type) params.ad_type = filters.ad_type
    
    const res = await api.get('/ads/admin', { params })
    ads.value = res.data?.items || res.data || []
    pagination.total = res.data?.total || ads.value.length
  } catch (error) {
    console.error('获取广告列表失败:', error)
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.id = null
  form.title = ''
  form.description = ''
  form.ad_type = 'IMAGE'
  form.media_url = ''
  form.html_content = ''
  form.target_url = ''
  form.position = 'VIDEO_PRE'
  form.duration = 5
  form.priority = 0
  form.dateRange = null
}

const openAddDialog = () => {
  resetForm()
  isEdit.value = false
  showDialog.value = true
}

const openEditDialog = (row) => {
  form.id = row.id
  form.title = row.title
  form.description = row.description || ''
  form.ad_type = row.ad_type
  form.media_url = row.media_url || ''
  form.html_content = row.html_content || ''
  form.target_url = row.target_url || ''
  form.position = row.position
  form.duration = row.duration || 5
  form.priority = row.priority || 0
  form.dateRange = row.start_date && row.end_date 
    ? [new Date(row.start_date), new Date(row.end_date)] 
    : null
  isEdit.value = true
  showDialog.value = true
}

const handleUploadSuccess = (response) => {
  form.media_url = response.url
  ElMessage.success('上传成功')
}

const saveAd = async () => {
  if (!form.title || !form.position) {
    ElMessage.warning('请填写广告标题和位置')
    return
  }
  
  saving.value = true
  try {
    const data = {
      title: form.title,
      description: form.description,
      ad_type: form.ad_type,
      media_url: form.media_url,
      html_content: form.html_content,
      target_url: form.target_url,
      position: form.position,
      duration: form.duration,
      priority: form.priority,
      start_date: form.dateRange?.[0]?.toISOString() || null,
      end_date: form.dateRange?.[1]?.toISOString() || null
    }
    
    if (isEdit.value) {
      await api.put(`/ads/admin/${form.id}`, data)
      ElMessage.success('更新成功')
    } else {
      await api.post('/ads/admin', data)
      ElMessage.success('创建成功')
    }
    
    showDialog.value = false
    fetchAds()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const toggleStatus = async (row) => {
  try {
    await api.put(`/ads/admin/${row.id}`, { is_active: row.is_active })
    ElMessage.success(row.is_active ? '已启用' : '已禁用')
  } catch (error) {
    row.is_active = !row.is_active
    ElMessage.error('操作失败')
  }
}

const deleteAd = async (row) => {
  try {
    await ElMessageBox.confirm('确定删除此广告吗？', '提示', {
      type: 'warning'
    })
    await api.delete(`/ads/admin/${row.id}`)
    ElMessage.success('删除成功')
    fetchAds()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchAds()
})
</script>

<style lang="scss" scoped>
.ads-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .filter-bar {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
  }
  
  .pagination {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
  }
  
  .media-uploader {
    .media-preview {
      width: 200px;
      height: 112px;
      border-radius: 4px;
      overflow: hidden;
      
      .el-image {
        width: 100%;
        height: 100%;
      }
    }
    
    .upload-placeholder {
      width: 200px;
      height: 112px;
      border: 1px dashed #dcdfe6;
      border-radius: 4px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      gap: 8px;
      color: #909399;
      cursor: pointer;
      
      &:hover {
        border-color: #409eff;
        color: #409eff;
      }
      
      .el-icon {
        font-size: 24px;
      }
    }
  }
}
</style>