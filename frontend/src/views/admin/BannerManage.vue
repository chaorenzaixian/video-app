<template>
  <div class="banner-manage">
    <div class="page-header">
      <h1>轮播图管理</h1>
      <el-button type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>
        添加轮播图
      </el-button>
    </div>

    <!-- 筛选 -->
    <div class="filter-bar">
      <el-select v-model="filters.position" placeholder="位置" clearable @change="fetchBanners">
        <el-option label="首页" value="home" />
        <el-option label="短视频" value="short" />
        <el-option label="棋牌" value="chess" />
        <el-option label="VIP" value="vip" />
      </el-select>
      <el-select v-model="filters.is_active" placeholder="状态" clearable @change="fetchBanners">
        <el-option label="启用" :value="true" />
        <el-option label="禁用" :value="false" />
      </el-select>
    </div>

    <!-- 轮播图列表 -->
    <el-table :data="banners" v-loading="loading" border stripe>
      <el-table-column label="图片" width="200">
        <template #default="{ row }">
          <el-image 
            :src="row.image_url" 
            :preview-src-list="[row.image_url]"
            fit="cover"
            style="width: 160px; height: 80px; border-radius: 4px;"
          />
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="150" />
      <el-table-column prop="position" label="位置" width="100">
        <template #default="{ row }">
          <el-tag>{{ positionMap[row.position] || row.position }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="link_type" label="链接类型" width="100">
        <template #default="{ row }">
          {{ linkTypeMap[row.link_type] || row.link_type }}
        </template>
      </el-table-column>
      <el-table-column prop="sort_order" label="排序" width="80" />
      <el-table-column label="展示" width="90">
        <template #default="{ row }">
          {{ formatCount(row.impression_count || 0) }}
        </template>
      </el-table-column>
      <el-table-column label="点击" width="90">
        <template #default="{ row }">
          {{ formatCount(row.click_count || 0) }}
        </template>
      </el-table-column>
      <el-table-column label="CTR" width="80">
        <template #default="{ row }">
          {{ calcCTR(row) }}%
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="80">
        <template #default="{ row }">
          <el-switch 
            v-model="row.is_active" 
            @change="toggleStatus(row)"
          />
        </template>
      </el-table-column>
      <el-table-column label="有效期" width="180">
        <template #default="{ row }">
          <div v-if="row.start_time || row.end_time" class="time-range">
            <div v-if="row.start_time">开始: {{ formatDate(row.start_time) }}</div>
            <div v-if="row.end_time">结束: {{ formatDate(row.end_time) }}</div>
          </div>
          <span v-else class="text-muted">永久有效</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="editBanner(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="deleteBanner(row)">删除</el-button>
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
        @size-change="fetchBanners"
        @current-change="fetchBanners"
      />
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? '编辑轮播图' : '添加轮播图'"
      width="600px"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" placeholder="请输入标题" />
        </el-form-item>
        <el-form-item label="图片" required>
          <div class="upload-area">
            <el-upload
              class="banner-uploader"
              :action="uploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="handleUploadSuccess"
              :before-upload="beforeUpload"
              accept="image/*"
            >
              <img v-if="form.image_url" :src="form.image_url" class="preview-image" />
              <el-icon v-else class="upload-icon"><Plus /></el-icon>
            </el-upload>
            <div class="upload-tip">建议尺寸: 750 x 320 像素</div>
          </div>
        </el-form-item>
        <el-form-item label="位置" required>
          <el-select v-model="form.position" placeholder="请选择位置">
            <el-option label="首页" value="home" />
            <el-option label="短视频" value="short" />
            <el-option label="棋牌" value="chess" />
            <el-option label="VIP" value="vip" />
          </el-select>
        </el-form-item>
        <el-form-item label="链接类型">
          <el-select v-model="form.link_type" placeholder="请选择链接类型">
            <el-option label="无链接" value="none" />
            <el-option label="内部页面" value="internal" />
            <el-option label="外部链接" value="external" />
            <el-option label="视频详情" value="video" />
          </el-select>
        </el-form-item>
        <el-form-item label="链接地址" v-if="form.link_type && form.link_type !== 'none'">
          <el-input v-model="form.link_value" placeholder="请输入链接地址或视频ID" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="有效期">
          <el-date-picker
            v-model="form.timeRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          {{ isEdit ? '保存' : '添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '@/utils/api'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const loading = ref(false)
const banners = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const editingId = ref(null)

const filters = reactive({
  position: '',
  is_active: null
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const form = reactive({
  title: '',
  image_url: '',
  position: 'home',
  link_type: 'none',
  link_value: '',
  sort_order: 0,
  timeRange: null,
  is_active: true
})

const positionMap = {
  home: '首页',
  short: '短视频',
  chess: '棋牌',
  vip: 'VIP'
}

const linkTypeMap = {
  none: '无链接',
  internal: '内部页面',
  external: '外部链接',
  video: '视频详情'
}

const uploadUrl = computed(() => '/api/v1/ads/upload/image')
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${userStore.token}`
}))

onMounted(() => {
  fetchBanners()
})

const fetchBanners = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    if (filters.position) params.position = filters.position
    if (filters.is_active !== null && filters.is_active !== '') {
      params.is_active = filters.is_active
    }
    
    const res = await api.get('/admin/content/banners', { params })
    const data = res.data || res
    banners.value = data.items || []
    pagination.total = data.total || 0
  } catch (error) {
    console.error('获取轮播图失败:', error)
    ElMessage.error('获取轮播图失败')
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  isEdit.value = false
  editingId.value = null
  Object.assign(form, {
    title: '',
    image_url: '',
    position: 'home',
    link_type: 'none',
    link_value: '',
    sort_order: 0,
    timeRange: null,
    is_active: true
  })
  dialogVisible.value = true
}

const editBanner = (row) => {
  isEdit.value = true
  editingId.value = row.id
  Object.assign(form, {
    title: row.title,
    image_url: row.image_url,
    position: row.position,
    link_type: row.link_type || 'none',
    link_value: row.link_url || '',
    sort_order: row.sort_order,
    timeRange: row.start_time && row.end_time ? [row.start_time, row.end_time] : null,
    is_active: row.is_active
  })
  dialogVisible.value = true
}

const beforeUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB!')
    return false
  }
  return true
}

const handleUploadSuccess = (response) => {
  if (response.url) {
    form.image_url = response.url
    ElMessage.success('图片上传成功')
  } else {
    ElMessage.error('图片上传失败')
  }
}

const submitForm = async () => {
  if (!form.title) {
    ElMessage.error('请输入标题')
    return
  }
  if (!form.image_url) {
    ElMessage.error('请上传图片')
    return
  }

  submitting.value = true
  try {
    const data = {
      title: form.title,
      image_url: form.image_url,
      position: form.position,
      link_type: form.link_type,
      link_value: form.link_value,
      sort_order: form.sort_order,
      is_active: form.is_active,
      start_time: form.timeRange ? form.timeRange[0] : null,
      end_time: form.timeRange ? form.timeRange[1] : null
    }

    if (isEdit.value) {
      await api.put(`/admin/content/banners/${editingId.value}`, data)
      ElMessage.success('更新成功')
    } else {
      await api.post('/admin/content/banners', data)
      ElMessage.success('添加成功')
    }
    
    dialogVisible.value = false
    fetchBanners()
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error('提交失败')
  } finally {
    submitting.value = false
  }
}

const toggleStatus = async (row) => {
  try {
    await api.put(`/admin/content/banners/${row.id}`, {
      is_active: row.is_active
    })
    ElMessage.success('状态更新成功')
  } catch (error) {
    row.is_active = !row.is_active
    ElMessage.error('状态更新失败')
  }
}

const deleteBanner = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这个轮播图吗?', '提示', {
      type: 'warning'
    })
    
    await api.delete(`/admin/content/banners/${row.id}`)
    ElMessage.success('删除成功')
    fetchBanners()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const formatCount = (num) => {
  if (num >= 10000) return (num / 10000).toFixed(1) + 'w'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k'
  return num
}

const calcCTR = (row) => {
  const impressions = row.impression_count || 0
  const clicks = row.click_count || 0
  if (impressions === 0) return '0.00'
  return ((clicks / impressions) * 100).toFixed(2)
}
</script>

<style lang="scss" scoped>
.banner-manage {
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
  }
  
  .filter-bar {
    display: flex;
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
  
  .time-range {
    font-size: 12px;
    line-height: 1.6;
  }
  
  .text-muted {
    color: #999;
  }
}

.upload-area {
  .banner-uploader {
    :deep(.el-upload) {
      width: 200px;
      height: 100px;
      border: 1px dashed #d9d9d9;
      border-radius: 6px;
      cursor: pointer;
      position: relative;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      
      &:hover {
        border-color: #409eff;
      }
    }
  }
  
  .preview-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  .upload-icon {
    font-size: 28px;
    color: #8c939d;
  }
  
  .upload-tip {
    font-size: 12px;
    color: #999;
    margin-top: 8px;
  }
}
</style>





