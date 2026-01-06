<template>
  <div class="group-manage">
    <div class="page-header">
      <h2>官方群组管理</h2>
      <el-button type="primary" @click="showDialog()">
        <el-icon><Plus /></el-icon>
        添加群组
      </el-button>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-select v-model="filterType" placeholder="群组类型" clearable style="width: 150px">
        <el-option label="官方社群" value="community" />
        <el-option label="商务合作" value="business" />
      </el-select>
      <el-button @click="fetchGroups">刷新</el-button>
    </div>

    <!-- 群组列表 -->
    <el-table :data="filteredGroups" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="图标" width="80">
        <template #default="{ row }">
          <div class="icon-preview" :style="{ background: row.icon_bg }">
            <img v-if="row.icon_type === 'custom' && row.icon_image" :src="row.icon_image" class="custom-icon-img" />
            <component v-else :is="getIconComponent(row.icon_type)" />
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="群组名称" min-width="150" />
      <el-table-column label="类型" width="120">
        <template #default="{ row }">
          <el-tag :type="row.group_type === 'community' ? 'primary' : 'warning'">
            {{ row.group_type === 'community' ? '官方社群' : '商务合作' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="url" label="链接" min-width="200" show-overflow-tooltip />
      <el-table-column prop="click_count" label="点击量" width="80" />
      <el-table-column prop="sort_order" label="排序" width="80" />
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-switch v-model="row.is_active" @change="toggleStatus(row)" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="showDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="deleteGroup(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="dialog.visible"
      :title="dialog.isEdit ? '编辑群组' : '添加群组'"
      width="600px"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="群组名称" required>
          <el-input v-model="form.name" placeholder="如：官方土豆群" />
        </el-form-item>

        <el-form-item label="群组类型" required>
          <el-select v-model="form.group_type" style="width: 100%">
            <el-option label="官方社群" value="community" />
            <el-option label="商务合作" value="business" />
          </el-select>
        </el-form-item>

        <el-form-item label="图标类型" required>
          <el-select v-model="form.icon_type" style="width: 100%">
            <el-option label="🚀 火箭" value="rocket" />
            <el-option label="✈️ 飞机(Telegram)" value="telegram" />
            <el-option label="💼 公文包" value="briefcase" />
            <el-option label="❤️ 心形" value="heart" />
            <el-option label="📷 自定义图片" value="custom" />
          </el-select>
        </el-form-item>

        <el-form-item v-if="form.icon_type === 'custom'" label="图标图片">
          <div class="icon-upload-area">
            <el-upload
              class="icon-uploader"
              :action="uploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="handleIconUploadSuccess"
              :before-upload="beforeUpload"
              accept="image/*"
            >
              <img v-if="form.icon_image" :src="form.icon_image" class="uploaded-icon" />
              <div v-else class="upload-placeholder">
                <el-icon><Plus /></el-icon>
                <span>上传图标</span>
              </div>
            </el-upload>
            <div v-if="form.icon_image" class="upload-tips">
              <span>{{ form.icon_image }}</span>
              <el-button type="danger" size="small" text @click="form.icon_image = ''">删除</el-button>
            </div>
            <div class="upload-hint">推荐尺寸: 96x96px，支持 PNG/JPG/GIF/WEBP，最大 2MB</div>
          </div>
        </el-form-item>

        <el-form-item label="图标背景">
          <div class="bg-presets">
            <div
              v-for="(preset, index) in bgPresets"
              :key="index"
              class="bg-preset-item"
              :class="{ active: form.icon_bg === preset }"
              :style="{ background: preset }"
              @click="form.icon_bg = preset"
            />
          </div>
          <el-input v-model="form.icon_bg" placeholder="CSS渐变色" style="margin-top: 8px" />
        </el-form-item>

        <el-form-item label="跳转链接">
          <el-input v-model="form.url" placeholder="https://t.me/xxx" />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="排序">
              <el-input-number v-model="form.sort_order" :min="0" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="预览">
          <div class="group-preview">
            <div class="preview-icon" :style="{ background: form.icon_bg }">
              <img v-if="form.icon_type === 'custom' && form.icon_image" :src="form.icon_image" class="preview-custom-icon" />
              <component v-else :is="getIconComponent(form.icon_type)" />
            </div>
            <span class="preview-name">{{ form.name || '群组名称' }}</span>
            <el-button type="primary" size="small" round>立即加入</el-button>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="dialog.loading" @click="submitForm">
          {{ dialog.isEdit ? '保存' : '添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'

const loading = ref(false)
const groups = ref([])
const filterType = ref('')

const dialog = ref({
  visible: false,
  isEdit: false,
  loading: false
})

const form = ref({
  id: null,
  name: '',
  group_type: 'community',
  icon_type: 'rocket',
  icon_image: '',
  icon_bg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  url: '',
  sort_order: 0,
  is_active: true
})

// 图片上传配置
const uploadUrl = '/api/v1/ads/upload/image'
const uploadHeaders = {
  Authorization: `Bearer ${localStorage.getItem('token')}`
}

const handleIconUploadSuccess = (response) => {
  if (response.url) {
    form.value.icon_image = response.url
    ElMessage.success('图标上传成功')
  }
}

const beforeUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2
  
  if (!isImage) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB')
    return false
  }
  return true
}

const bgPresets = [
  'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  'linear-gradient(135deg, #00b4db 0%, #0083b0 100%)',
  'linear-gradient(135deg, #f43f5e 0%, #ec4899 100%)',
  'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)',
  'linear-gradient(135deg, #10b981 0%, #059669 100%)',
  'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)'
]

// 图标组件映射
const iconComponents = {
  rocket: () => h('svg', { viewBox: '0 0 24 24', fill: 'currentColor', style: 'width: 24px; height: 24px; color: #fff' }, [
    h('path', { d: 'M12.75 3.94c.3-.29.71-.44 1.13-.44.87 0 1.62.57 1.88 1.37l1.01 3.04 2.53 2.53c.29.29.45.68.45 1.09v.94c0 .83-.67 1.5-1.5 1.5h-.94c-.41 0-.8-.16-1.09-.45l-2.53-2.53-3.04-1.01c-.8-.26-1.37-1.01-1.37-1.88 0-.42.15-.83.44-1.13l2.97-2.97c.01-.02.04-.04.06-.06zm-2.53 8.53L8.69 14l1.53 1.53c.29.29.45.68.45 1.09v.88c0 .83-.67 1.5-1.5 1.5H8.5c-.41 0-.8-.16-1.09-.45L6 17.14l-2.47 2.47c-.29.29-.68.45-1.09.45h-.94c-.83 0-1.5-.67-1.5-1.5v-.94c0-.41.16-.8.45-1.09L2.86 14l-1.41-1.41c-.29-.29-.45-.68-.45-1.09v-.88c0-.83.67-1.5 1.5-1.5h.88c.41 0 .8.16 1.09.45L6 11.1l1.53-1.53' })
  ]),
  telegram: () => h('svg', { viewBox: '0 0 24 24', fill: 'currentColor', style: 'width: 24px; height: 24px; color: #fff' }, [
    h('path', { d: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69.01-.03.01-.14-.07-.2-.08-.06-.19-.04-.27-.02-.12.03-1.99 1.27-5.62 3.72-.53.36-1.01.54-1.44.53-.47-.01-1.38-.27-2.06-.49-.83-.27-1.49-.42-1.43-.88.03-.24.37-.49 1.02-.74 3.99-1.74 6.65-2.89 7.99-3.45 3.8-1.6 4.59-1.88 5.1-1.89.11 0 .37.03.54.17.14.12.18.28.2.45-.01.06.01.24 0 .38z' })
  ]),
  briefcase: () => h('svg', { viewBox: '0 0 24 24', fill: 'currentColor', style: 'width: 24px; height: 24px; color: #fff' }, [
    h('path', { d: 'M20 7h-4V5c0-1.1-.9-2-2-2h-4c-1.1 0-2 .9-2 2v2H4c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V9c0-1.1-.9-2-2-2zM10 5h4v2h-4V5zm10 14H4v-7h4v1c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-1h4v7zm-6-7h-4v-2h4v2z' })
  ]),
  heart: () => h('svg', { viewBox: '0 0 24 24', fill: 'currentColor', style: 'width: 24px; height: 24px; color: #fff' }, [
    h('path', { d: 'M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z' })
  ])
}

const getIconComponent = (iconType) => {
  return iconComponents[iconType] || iconComponents.rocket
}

const filteredGroups = computed(() => {
  if (!filterType.value) return groups.value
  return groups.value.filter(g => g.group_type === filterType.value)
})

const fetchGroups = async () => {
  loading.value = true
  try {
    const res = await api.get('/ads/groups/admin')
    groups.value = res.data || res || []
  } catch (error) {
    console.error('获取群组列表失败:', error)
    ElMessage.error('获取群组列表失败')
  } finally {
    loading.value = false
  }
}

const showDialog = (group = null) => {
  if (group) {
    dialog.value.isEdit = true
    form.value = {
      id: group.id,
      name: group.name,
      group_type: group.group_type,
      icon_type: group.icon_type,
      icon_image: group.icon_image || '',
      icon_bg: group.icon_bg,
      url: group.url || '',
      sort_order: group.sort_order,
      is_active: group.is_active
    }
  } else {
    dialog.value.isEdit = false
    form.value = {
      id: null,
      name: '',
      group_type: 'community',
      icon_type: 'rocket',
      icon_image: '',
      icon_bg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      url: '',
      sort_order: 0,
      is_active: true
    }
  }
  dialog.value.visible = true
}

const submitForm = async () => {
  if (!form.value.name) {
    ElMessage.warning('请输入群组名称')
    return
  }

  dialog.value.loading = true
  try {
    if (dialog.value.isEdit) {
      await api.put(`/ads/groups/${form.value.id}`, form.value)
      ElMessage.success('更新成功')
    } else {
      await api.post('/ads/groups', form.value)
      ElMessage.success('添加成功')
    }
    dialog.value.visible = false
    fetchGroups()
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    dialog.value.loading = false
  }
}

const toggleStatus = async (group) => {
  try {
    await api.put(`/ads/groups/${group.id}`, { is_active: group.is_active })
    ElMessage.success('状态更新成功')
  } catch (error) {
    group.is_active = !group.is_active
    ElMessage.error('状态更新失败')
  }
}

const deleteGroup = async (group) => {
  try {
    await ElMessageBox.confirm('确定要删除该群组吗？', '确认删除', {
      type: 'warning'
    })
    await api.delete(`/ads/groups/${group.id}`)
    ElMessage.success('删除成功')
    fetchGroups()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchGroups()
})
</script>

<style lang="scss" scoped>
.group-manage {
  padding: 20px;
  background: #f0f2f5;
  min-height: calc(100vh - 60px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background: #fff;
  padding: 16px 20px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);

  h2 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #333;
  }
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  background: #fff;
  padding: 16px 20px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.icon-preview {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  
  .custom-icon-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.icon-upload-area {
  .icon-uploader {
    :deep(.el-upload) {
      border: 2px dashed #d9d9d9;
      border-radius: 8px;
      cursor: pointer;
      position: relative;
      overflow: hidden;
      transition: border-color 0.3s;
      
      &:hover {
        border-color: #6366f1;
      }
    }
  }
  
  .uploaded-icon {
    width: 80px;
    height: 80px;
    object-fit: cover;
  }
  
  .upload-placeholder {
    width: 80px;
    height: 80px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #999;
    font-size: 12px;
    
    .el-icon {
      font-size: 24px;
      margin-bottom: 4px;
    }
  }
  
  .upload-tips {
    margin-top: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
    
    span {
      font-size: 12px;
      color: #666;
      max-width: 200px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
  
  .upload-hint {
    margin-top: 8px;
    font-size: 12px;
    color: #999;
  }
}

.bg-presets {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;

  .bg-preset-item {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    cursor: pointer;
    border: 2px solid transparent;
    transition: all 0.2s;

    &.active {
      border-color: #6366f1;
      box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.3);
    }

    &:hover {
      transform: scale(1.1);
    }
  }
}

.group-preview {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 12px;
  border: 1px solid #e5e5e5;

  .preview-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    
    .preview-custom-icon {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }

  .preview-name {
    flex: 1;
    font-size: 14px;
    color: #333;
  }
}

:deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

:deep(.el-dialog) {
  border-radius: 12px;
  
  .el-dialog__header {
    padding: 16px 20px;
    border-bottom: 1px solid #eee;
  }

  .el-dialog__body {
    padding: 20px;
  }

  .el-dialog__footer {
    padding: 12px 20px;
    border-top: 1px solid #eee;
  }
}

:deep(.el-tag--primary) {
  background-color: rgba(99, 102, 241, 0.1);
  border-color: rgba(99, 102, 241, 0.2);
  color: #6366f1;
}

:deep(.el-tag--warning) {
  background-color: rgba(245, 158, 11, 0.1);
  border-color: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}
</style>

