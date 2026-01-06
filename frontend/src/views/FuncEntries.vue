<template>
  <div class="func-entries-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>功能入口管理</span>
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            添加入口
          </el-button>
        </div>
      </template>

      <el-table :data="entries" style="width: 100%" v-loading="loading" border>
        <el-table-column label="排序" prop="sort_order" width="70" align="center" />
        <el-table-column label="图标" width="80" align="center">
          <template #default="{ row }">
            <div class="icon-preview">
              <img v-if="row.image" :src="row.image" alt="icon" />
              <span v-else class="placeholder">{{ row.name?.charAt(0) || '?' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="名称" prop="name" width="120" />
        <el-table-column label="图片URL" min-width="200">
          <template #default="{ row }">
            <el-tooltip v-if="row.image" :content="row.image" placement="top">
              <span class="url-text">{{ row.image }}</span>
            </el-tooltip>
            <span v-else class="text-muted">未设置</span>
          </template>
        </el-table-column>
        <el-table-column label="跳转链接" min-width="200">
          <template #default="{ row }">
            <el-tooltip v-if="row.link" :content="row.link" placement="top">
              <span class="url-text">{{ row.link }}</span>
            </el-tooltip>
            <span v-else class="text-muted">未设置</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="editEntry(row)">编辑</el-button>
            <el-button size="small" type="success" link @click="showUploadDialog(row)">上传图片</el-button>
            <el-popconfirm title="确定删除吗？" @confirm="deleteEntry(row)">
              <template #reference>
                <el-button size="small" type="danger" link>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="入口名称" />
        </el-form-item>
        <el-form-item label="图标图片">
          <div class="upload-inline">
            <el-input v-model="form.image" placeholder="图片URL或上传图片" style="flex: 1" />
            <el-upload
              :action="uploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="handleInlineUploadSuccess"
              accept="image/*"
            >
              <el-button type="primary">上传</el-button>
            </el-upload>
          </div>
          <div v-if="form.image" class="image-preview">
            <img :src="form.image" alt="预览" />
          </div>
        </el-form-item>
        <el-form-item label="跳转链接">
          <el-input v-model="form.link" placeholder="点击跳转链接" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEntry" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 上传图片对话框 -->
    <el-dialog v-model="uploadDialogVisible" title="上传图标图片" width="450px">
      <el-upload
        class="upload-area"
        drag
        :action="uploadUrl"
        :headers="uploadHeaders"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :before-upload="beforeUpload"
        accept="image/*"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽图片到此处，或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            建议尺寸：100x100px，支持 PNG/JPG/GIF/WEBP，大小不超过2MB
          </div>
        </template>
      </el-upload>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, UploadFilled } from '@element-plus/icons-vue'
import api from '@/utils/api'

const loading = ref(false)
const saving = ref(false)
const entries = ref([])
const dialogVisible = ref(false)
const uploadDialogVisible = ref(false)
const currentEntry = ref(null)

const form = ref({
  name: '',
  image: '',
  link: '',
  sort_order: 0,
  is_active: true
})

const dialogTitle = computed(() => currentEntry.value ? '编辑功能入口' : '添加功能入口')

// 上传API地址
const uploadUrl = '/api/v1/ads/upload/image'

const uploadHeaders = computed(() => {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
})

const fetchEntries = async () => {
  loading.value = true
  try {
    const res = await api.get('/ads/func-entries/admin')
    entries.value = res.data || res || []
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  currentEntry.value = null
  form.value = {
    name: '',
    image: '',
    link: '',
    sort_order: entries.value.length + 1,
    is_active: true
  }
  dialogVisible.value = true
}

const editEntry = (row) => {
  currentEntry.value = row
  form.value = { ...row }
  dialogVisible.value = true
}

const saveEntry = async () => {
  if (!form.value.name) {
    ElMessage.warning('请输入名称')
    return
  }
  
  saving.value = true
  try {
    if (currentEntry.value) {
      await api.put(`/ads/func-entries/${currentEntry.value.id}`, form.value)
      ElMessage.success('更新成功')
    } else {
      await api.post('/ads/func-entries', form.value)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    fetchEntries()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const deleteEntry = async (row) => {
  try {
    await api.delete(`/ads/func-entries/${row.id}`)
    ElMessage.success('删除成功')
    fetchEntries()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

const showUploadDialog = (row) => {
  currentEntry.value = row
  uploadDialogVisible.value = true
}

// 上传前验证
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

// 编辑弹窗内的上传成功
const handleInlineUploadSuccess = (response) => {
  if (response.url) {
    form.value.image = response.url
    ElMessage.success('图片上传成功')
  }
}

// 上传弹窗的上传成功
const handleUploadSuccess = async (response) => {
  if (response.url) {
    try {
      await api.put(`/ads/func-entries/${currentEntry.value.id}`, {
        ...currentEntry.value,
        image: response.url
      })
      ElMessage.success('图片上传成功')
      uploadDialogVisible.value = false
      fetchEntries()
    } catch (error) {
      ElMessage.error('更新失败')
    }
  }
}

const handleUploadError = () => {
  ElMessage.error('上传失败，请检查网络或重试')
}

onMounted(() => {
  fetchEntries()
})
</script>

<style lang="scss" scoped>
.func-entries-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  span {
    font-size: 16px;
    font-weight: 600;
  }
}

.icon-preview {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    border-radius: 8px;
  }
  
  .placeholder {
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 16px;
    font-weight: bold;
  }
}

.url-text {
  color: #606266;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
  display: inline-block;
}

.text-muted {
  color: #999;
  font-size: 12px;
}

.upload-inline {
  display: flex;
  gap: 10px;
}

.image-preview {
  margin-top: 10px;
  
  img {
    max-width: 100px;
    max-height: 100px;
    border-radius: 8px;
    border: 1px solid #eee;
  }
}

.upload-area {
  width: 100%;
  
  :deep(.el-upload) {
    width: 100%;
  }
  
  :deep(.el-upload-dragger) {
    width: 100%;
  }
}
</style>


