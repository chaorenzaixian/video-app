<template>
  <div class="service-manage">
    <!-- 标题栏 -->
    <div class="page-header">
      <h2>客服管理</h2>
      <el-button type="primary" @click="showDialog()">
        <el-icon><Plus /></el-icon>
        添加客服
      </el-button>
    </div>

    <!-- 客服列表 -->
    <div class="service-card">
      <el-table :data="services" v-loading="loading" style="width: 100%">
        <el-table-column label="客服信息" min-width="200">
          <template #default="{ row }">
            <div class="service-cell">
              <div class="service-icon" :style="{ background: row.icon_bg }">
                <img v-if="row.icon_type === 'custom' && row.icon_image" :src="row.icon_image" class="custom-icon-img" />
                <component v-else :is="getIconComponent(row.icon_type)" />
              </div>
              <div class="service-info">
                <span class="name">{{ row.name }}</span>
                <span class="type">{{ getTypeName(row.service_type) }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="联系方式" prop="contact" min-width="180">
          <template #default="{ row }">
            <span>{{ row.contact || '-' }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="描述" prop="description" min-width="150">
          <template #default="{ row }">
            <span>{{ row.description || '-' }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="工作时间" prop="work_time" width="140">
          <template #default="{ row }">
            <span>{{ row.work_time || '-' }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              @change="toggleStatus(row)"
            />
          </template>
        </el-table-column>
        
        <el-table-column label="排序" prop="sort_order" width="80" />
        
        <el-table-column label="点击量" prop="click_count" width="80" />
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="showDialog(row)">编辑</el-button>
            <el-button link type="danger" @click="deleteService(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑客服' : '添加客服'"
      width="600px"
      destroy-on-close
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="客服名称" required>
          <el-input v-model="form.name" placeholder="请输入客服名称" />
        </el-form-item>
        
        <el-form-item label="客服类型" required>
          <el-select v-model="form.service_type" style="width: 100%">
            <el-option label="在线客服" value="online" />
            <el-option label="Telegram" value="telegram" />
            <el-option label="WhatsApp" value="whatsapp" />
            <el-option label="QQ" value="qq" />
            <el-option label="微信" value="wechat" />
            <el-option label="邮箱" value="email" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="联系方式">
          <el-input v-model="form.contact" :placeholder="getContactPlaceholder(form.service_type)" />
        </el-form-item>
        
        <el-form-item label="描述信息">
          <el-input v-model="form.description" placeholder="如：7x24小时在线" />
        </el-form-item>
        
        <el-form-item label="工作时间">
          <el-input v-model="form.work_time" placeholder="如：09:00 - 22:00" />
        </el-form-item>
        
        <el-form-item label="图标类型">
          <el-radio-group v-model="form.icon_type">
            <el-radio value="headset">🎧 客服</el-radio>
            <el-radio value="telegram">📱 Telegram</el-radio>
            <el-radio value="whatsapp">💬 WhatsApp</el-radio>
            <el-radio value="qq">🐧 QQ</el-radio>
            <el-radio value="wechat">💚 微信</el-radio>
            <el-radio value="email">📧 邮箱</el-radio>
            <el-radio value="custom">📷 自定义图片</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="自定义图标" v-if="form.icon_type === 'custom'">
          <div class="icon-upload-area">
            <el-upload
              :action="uploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="handleIconUploadSuccess"
              :before-upload="beforeUpload"
              accept="image/*"
            >
              <div v-if="form.icon_image" class="uploaded-icon">
                <img :src="form.icon_image" />
              </div>
              <div v-else class="upload-placeholder">
                <el-icon><Plus /></el-icon>
                <span>上传图标</span>
              </div>
            </el-upload>
            <div class="upload-tips">建议尺寸：100x100，支持PNG/JPG/GIF</div>
          </div>
        </el-form-item>
        
        <el-form-item label="图标背景">
          <div class="bg-presets">
            <div 
              v-for="bg in bgPresets" 
              :key="bg"
              class="bg-preset-item"
              :class="{ active: form.icon_bg === bg }"
              :style="{ background: bg }"
              @click="form.icon_bg = bg"
            ></div>
          </div>
          <el-input v-model="form.icon_bg" placeholder="CSS渐变色" style="margin-top: 8px" />
        </el-form-item>
        
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :max="999" />
        </el-form-item>
        
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      
      <!-- 预览 -->
      <div class="preview-section">
        <h4>预览效果</h4>
        <div class="service-preview">
          <div class="preview-icon" :style="{ background: form.icon_bg }">
            <img v-if="form.icon_type === 'custom' && form.icon_image" :src="form.icon_image" class="preview-custom-icon" />
            <component v-else :is="getIconComponent(form.icon_type)" />
          </div>
          <div class="preview-info">
            <span class="preview-name">{{ form.name || '客服名称' }}</span>
            <span class="preview-desc">{{ form.description || '描述信息' }}</span>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, h, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '@/utils/api'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const loading = ref(false)
const services = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const editingId = ref(null)

const form = ref({
  name: '',
  service_type: 'online',
  icon_type: 'headset',
  icon_image: '',
  icon_bg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  contact: '',
  description: '',
  work_time: '',
  sort_order: 0,
  is_active: true
})

// 上传配置
const uploadUrl = computed(() => '/api/v1/ads/upload-image')
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${userStore.token}`
}))

// 背景预设
const bgPresets = [
  'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  'linear-gradient(135deg, #00b4db 0%, #0083b0 100%)',
  'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
  'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)',
  'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)'
]

// 图标组件
const iconComponents = {
  headset: () => h('svg', { viewBox: '0 0 24 24', fill: 'currentColor', style: 'width: 24px; height: 24px; color: #fff;' }, [
    h('path', { d: 'M12 1c-4.97 0-9 4.03-9 9v7c0 1.66 1.34 3 3 3h3v-8H5v-2c0-3.87 3.13-7 7-7s7 3.13 7 7v2h-4v8h3c1.66 0 3-1.34 3-3v-7c0-4.97-4.03-9-9-9z' })
  ]),
  telegram: () => h('svg', { viewBox: '0 0 24 24', fill: 'currentColor', style: 'width: 24px; height: 24px; color: #fff;' }, [
    h('path', { d: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69.01-.03.01-.14-.07-.2-.08-.06-.19-.04-.27-.02-.12.03-1.99 1.27-5.62 3.72-.53.36-1.01.54-1.44.53-.47-.01-1.38-.27-2.06-.49-.83-.27-1.49-.42-1.43-.88.03-.24.37-.49 1.02-.74 3.99-1.74 6.65-2.89 7.99-3.45 3.8-1.6 4.59-1.88 5.1-1.89.11 0 .37.03.54.17.14.12.18.28.2.45-.01.06.01.24 0 .38z' })
  ]),
  whatsapp: () => h('svg', { viewBox: '0 0 24 24', fill: 'currentColor', style: 'width: 24px; height: 24px; color: #fff;' }, [
    h('path', { d: 'M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z' })
  ]),
  qq: () => h('svg', { viewBox: '0 0 24 24', fill: 'currentColor', style: 'width: 24px; height: 24px; color: #fff;' }, [
    h('path', { d: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z' })
  ]),
  wechat: () => h('svg', { viewBox: '0 0 24 24', fill: 'currentColor', style: 'width: 24px; height: 24px; color: #fff;' }, [
    h('path', { d: 'M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 01.213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 00.167-.054l1.903-1.114a.864.864 0 01.717-.098 10.16 10.16 0 002.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348z' })
  ]),
  email: () => h('svg', { viewBox: '0 0 24 24', fill: 'currentColor', style: 'width: 24px; height: 24px; color: #fff;' }, [
    h('path', { d: 'M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z' })
  ]),
  online: () => h('svg', { viewBox: '0 0 24 24', fill: 'currentColor', style: 'width: 24px; height: 24px; color: #fff;' }, [
    h('path', { d: 'M12 1c-4.97 0-9 4.03-9 9v7c0 1.66 1.34 3 3 3h3v-8H5v-2c0-3.87 3.13-7 7-7s7 3.13 7 7v2h-4v8h3c1.66 0 3-1.34 3-3v-7c0-4.97-4.03-9-9-9z' })
  ])
}

const getIconComponent = (iconType) => {
  return iconComponents[iconType] || iconComponents.headset
}

const typeNames = {
  online: '在线客服',
  telegram: 'Telegram',
  whatsapp: 'WhatsApp',
  qq: 'QQ',
  wechat: '微信',
  email: '邮箱'
}

const getTypeName = (type) => typeNames[type] || type

const getContactPlaceholder = (type) => {
  const placeholders = {
    online: '在线客服链接',
    telegram: 'Telegram用户名或链接',
    whatsapp: 'WhatsApp号码',
    qq: 'QQ号码',
    wechat: '微信号',
    email: '邮箱地址'
  }
  return placeholders[type] || '联系方式'
}

// 获取客服列表
const fetchServices = async () => {
  loading.value = true
  try {
    const res = await api.get('/ads/customer-service/admin')
    services.value = res.data || res || []
  } catch (error) {
    console.error('获取客服列表失败:', error)
    ElMessage.error('获取客服列表失败')
  } finally {
    loading.value = false
  }
}

// 显示对话框
const showDialog = (row = null) => {
  isEdit.value = !!row
  editingId.value = row?.id || null
  
  if (row) {
    form.value = {
      name: row.name,
      service_type: row.service_type,
      icon_type: row.icon_type,
      icon_image: row.icon_image || '',
      icon_bg: row.icon_bg,
      contact: row.contact || '',
      description: row.description || '',
      work_time: row.work_time || '',
      sort_order: row.sort_order,
      is_active: row.is_active
    }
  } else {
    form.value = {
      name: '',
      service_type: 'online',
      icon_type: 'headset',
      icon_image: '',
      icon_bg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      contact: '',
      description: '',
      work_time: '',
      sort_order: 0,
      is_active: true
    }
  }
  
  dialogVisible.value = true
}

// 上传图标成功
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
    ElMessage.error('图片大小不能超过2MB')
    return false
  }
  return true
}

// 提交表单
const submitForm = async () => {
  if (!form.value.name) {
    ElMessage.warning('请输入客服名称')
    return
  }
  
  submitting.value = true
  try {
    if (isEdit.value) {
      await api.put(`/ads/customer-service/${editingId.value}`, form.value)
      ElMessage.success('更新成功')
    } else {
      await api.post('/ads/customer-service', form.value)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    fetchServices()
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  } finally {
    submitting.value = false
  }
}

// 切换状态
const toggleStatus = async (row) => {
  try {
    await api.put(`/ads/customer-service/${row.id}`, { is_active: row.is_active })
    ElMessage.success(row.is_active ? '已启用' : '已禁用')
  } catch (error) {
    console.error('更新状态失败:', error)
    row.is_active = !row.is_active
    ElMessage.error('更新状态失败')
  }
}

// 删除客服
const deleteService = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该客服吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.delete(`/ads/customer-service/${row.id}`)
    ElMessage.success('删除成功')
    fetchServices()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchServices()
})
</script>

<style lang="scss" scoped>
.service-manage {
  padding: 20px;
  background: #f0f2f5;
  min-height: 100vh;
  color: #333;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  h2 {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    color: #303133;
  }
}

.service-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

:deep(.el-table) {
  --el-table-bg-color: #fff;
  --el-table-tr-bg-color: #fff;
  --el-table-header-bg-color: #f5f7fa;
  --el-table-row-hover-bg-color: #f5f7fa;
  --el-table-text-color: #333;
  --el-table-header-text-color: #606266;
  --el-table-border-color: #ebeef5;
}

.service-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  
  .service-icon {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    overflow: hidden;
    
    .custom-icon-img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }
  
  .service-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
    
    .name {
      font-weight: 500;
      color: #303133;
    }
    
    .type {
      font-size: 12px;
      color: #909399;
    }
  }
}

:deep(.el-dialog) {
  .el-dialog__header {
    border-bottom: 1px solid #ebeef5;
  }
  
  .el-dialog__title {
    color: #303133;
  }
  
  .el-form-item__label {
    color: #606266;
  }
}

.bg-presets {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  
  .bg-preset-item {
    width: 32px;
    height: 32px;
    border-radius: 6px;
    cursor: pointer;
    border: 2px solid transparent;
    transition: all 0.2s;
    
    &:hover {
      transform: scale(1.1);
    }
    
    &.active {
      border-color: #409eff;
      box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
    }
  }
}

.icon-upload-area {
  .uploaded-icon {
    width: 80px;
    height: 80px;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #dcdfe6;
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }
  
  .upload-placeholder {
    width: 80px;
    height: 80px;
    border: 1px dashed #dcdfe6;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: border-color 0.2s;
    
    &:hover {
      border-color: #409eff;
    }
    
    .el-icon {
      font-size: 24px;
      color: #909399;
    }
    
    span {
      font-size: 12px;
      color: #909399;
      margin-top: 4px;
    }
  }
  
  .upload-tips {
    font-size: 12px;
    color: #909399;
    margin-top: 8px;
  }
}

.preview-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
  
  h4 {
    margin: 0 0 12px;
    font-size: 14px;
    color: #606266;
  }
}

.service-preview {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 12px;
  
  .preview-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    overflow: hidden;
    
    .preview-custom-icon {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }
  
  .preview-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
    
    .preview-name {
      font-size: 15px;
      font-weight: 500;
      color: #303133;
    }
    
    .preview-desc {
      font-size: 12px;
      color: #909399;
    }
  }
}
</style>

