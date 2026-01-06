<template>
  <div class="watermark-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>水印配置管理</span>
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            添加水印配置
          </el-button>
        </div>
      </template>

      <!-- 水印列表 -->
      <el-table :data="watermarks" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="配置名称" width="150" />
        <el-table-column prop="watermark_type" label="水印类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeTag(row.watermark_type)">
              {{ getTypeText(row.watermark_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="预览" width="150">
          <template #default="{ row }">
            <template v-if="row.watermark_type === 'image'">
              <el-image
                v-if="row.image_url"
                :src="row.image_url"
                :preview-src-list="[row.image_url]"
                class="watermark-preview"
                fit="contain"
              />
            </template>
            <template v-else-if="row.watermark_type === 'text'">
              <span class="text-preview" :style="{ color: row.text_color, fontSize: row.font_size + 'px' }">
                {{ row.text_content }}
              </span>
            </template>
            <template v-else>
              <span class="text-muted">动态用户ID</span>
            </template>
          </template>
        </el-table-column>
        <el-table-column prop="position" label="位置" width="120">
          <template #default="{ row }">
            {{ getPositionText(row.position) }}
          </template>
        </el-table-column>
        <el-table-column prop="opacity" label="透明度" width="100">
          <template #default="{ row }">
            {{ (row.opacity * 100).toFixed(0) }}%
          </template>
        </el-table-column>
        <el-table-column prop="apply_to" label="应用范围" width="120">
          <template #default="{ row }">
            {{ getApplyToText(row.apply_to) }}
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-switch v-model="row.is_active" @change="toggleStatus(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="80" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteWatermark(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialog.visible"
      :title="dialog.isEdit ? '编辑水印配置' : '添加水印配置'"
      width="650px"
    >
      <el-form :model="form" label-width="100px" :rules="formRules" ref="formRef">
        <el-form-item label="配置名称" prop="name">
          <el-input v-model="form.name" placeholder="如：主水印、用户ID水印" />
        </el-form-item>

        <el-form-item label="水印类型" prop="watermark_type">
          <el-radio-group v-model="form.watermark_type">
            <el-radio value="image">图片水印</el-radio>
            <el-radio value="text">文字水印</el-radio>
            <el-radio value="user_id">用户ID水印</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 图片水印选项 -->
        <template v-if="form.watermark_type === 'image'">
          <el-form-item label="水印图片" required>
            <el-upload
              class="watermark-uploader"
              :action="uploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="handleUploadSuccess"
              :before-upload="beforeUpload"
              accept="image/png,image/gif"
            >
              <el-image
                v-if="form.image_url"
                :src="form.image_url"
                class="uploaded-image"
                fit="contain"
              />
              <el-icon v-else class="upload-icon"><Plus /></el-icon>
            </el-upload>
            <div class="upload-tip">建议使用透明PNG图片，尺寸不超过 300x100px</div>
          </el-form-item>
          <el-form-item label="图片宽度">
            <el-input-number v-model="form.image_width" :min="50" :max="500" />
            <span class="form-tip">像素，高度自动缩放</span>
          </el-form-item>
        </template>

        <!-- 文字水印选项 -->
        <template v-if="form.watermark_type === 'text'">
          <el-form-item label="水印文字" prop="text_content">
            <el-input v-model="form.text_content" placeholder="输入水印文字" />
          </el-form-item>
          <el-form-item label="字体大小">
            <el-input-number v-model="form.font_size" :min="12" :max="72" />
          </el-form-item>
          <el-form-item label="文字颜色">
            <el-color-picker v-model="form.text_color" show-alpha />
          </el-form-item>
          <el-form-item label="字体">
            <el-select v-model="form.font_family" style="width: 200px">
              <el-option label="微软雅黑" value="Microsoft YaHei" />
              <el-option label="宋体" value="SimSun" />
              <el-option label="黑体" value="SimHei" />
              <el-option label="Arial" value="Arial" />
            </el-select>
          </el-form-item>
        </template>

        <!-- 用户ID水印选项 -->
        <template v-if="form.watermark_type === 'user_id'">
          <el-form-item label="显示格式">
            <el-input v-model="form.user_id_format" placeholder="ID: {user_id}" />
            <div class="form-tip">使用 {user_id} 作为用户ID占位符</div>
          </el-form-item>
          <el-form-item label="字体大小">
            <el-input-number v-model="form.font_size" :min="12" :max="48" />
          </el-form-item>
          <el-form-item label="文字颜色">
            <el-color-picker v-model="form.text_color" show-alpha />
          </el-form-item>
        </template>

        <el-divider />

        <!-- 通用选项 -->
        <el-form-item label="显示位置">
          <el-select v-model="form.position" style="width: 200px">
            <el-option label="左上角" value="top_left" />
            <el-option label="右上角" value="top_right" />
            <el-option label="左下角" value="bottom_left" />
            <el-option label="右下角" value="bottom_right" />
            <el-option label="居中" value="center" />
            <el-option label="随机移动" value="random" />
          </el-select>
        </el-form-item>

        <el-form-item label="透明度">
          <el-slider v-model="form.opacity" :min="0.1" :max="1" :step="0.1" :format-tooltip="(val) => (val * 100).toFixed(0) + '%'" />
        </el-form-item>

        <el-form-item label="边距">
          <el-input-number v-model="form.margin_x" :min="0" :max="100" />
          <span class="margin-label">水平</span>
          <el-input-number v-model="form.margin_y" :min="0" :max="100" />
          <span class="margin-label">垂直</span>
        </el-form-item>

        <el-form-item label="应用范围">
          <el-select v-model="form.apply_to" style="width: 200px">
            <el-option label="所有视频" value="all" />
            <el-option label="仅付费视频" value="paid" />
            <el-option label="仅免费视频" value="free" />
            <el-option label="仅VIP视频" value="vip" />
          </el-select>
        </el-form-item>

        <el-form-item label="优先级">
          <el-input-number v-model="form.priority" :min="0" :max="100" />
          <span class="form-tip">数值越大优先级越高</span>
        </el-form-item>

        <el-form-item label="启用状态">
          <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="dialog.loading">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '@/utils/api'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const loading = ref(false)
const watermarks = ref([])
const formRef = ref()

const dialog = reactive({
  visible: false,
  isEdit: false,
  loading: false
})

const form = reactive({
  id: null,
  name: '',
  watermark_type: 'image',
  image_url: '',
  image_width: 150,
  text_content: '',
  font_size: 24,
  text_color: 'rgba(255,255,255,0.7)',
  font_family: 'Microsoft YaHei',
  user_id_format: 'ID: {user_id}',
  position: 'bottom_right',
  opacity: 0.7,
  margin_x: 20,
  margin_y: 20,
  apply_to: 'all',
  priority: 10,
  is_active: true
})

const formRules = {
  name: [{ required: true, message: '请输入配置名称', trigger: 'blur' }],
  watermark_type: [{ required: true, message: '请选择水印类型', trigger: 'change' }],
  text_content: [{ required: true, message: '请输入水印文字', trigger: 'blur' }]
}

const uploadUrl = computed(() => '/api/v1/watermark/upload-image')
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${userStore.token}`
}))

// 获取水印列表
const fetchWatermarks = async () => {
  loading.value = true
  try {
    const res = await api.get('/watermark/configs')
    // 处理不同的响应格式，确保返回数组
    let items = []
    if (Array.isArray(res.data)) {
      items = res.data
    } else if (res.data?.items && Array.isArray(res.data.items)) {
      items = res.data.items
    } else if (Array.isArray(res)) {
      items = res
    } else if (res?.items && Array.isArray(res.items)) {
      items = res.items
    }
    watermarks.value = items
    console.log('水印配置加载成功:', items.length, '条')
  } catch (error) {
    console.error('获取水印配置失败:', error)
    ElMessage.error('获取水印配置失败')
    watermarks.value = [] // 确保失败时也是数组
  } finally {
    loading.value = false
  }
}

// 显示添加对话框
const showAddDialog = () => {
  dialog.isEdit = false
  resetForm()
  dialog.visible = true
}

// 显示编辑对话框
const showEditDialog = (row) => {
  dialog.isEdit = true
  Object.assign(form, {
    id: row.id,
    name: row.name,
    watermark_type: row.watermark_type,
    image_url: row.image_url || '',
    image_width: row.image_width || 150,
    text_content: row.text_content || '',
    font_size: row.font_size || 24,
    text_color: row.text_color || 'rgba(255,255,255,0.7)',
    font_family: row.font_family || 'Microsoft YaHei',
    user_id_format: row.user_id_format || 'ID: {user_id}',
    position: row.position,
    opacity: row.opacity,
    margin_x: row.margin_x || 20,
    margin_y: row.margin_y || 20,
    apply_to: row.apply_to || 'all',
    priority: row.priority || 10,
    is_active: row.is_active
  })
  dialog.visible = true
}

// 重置表单
const resetForm = () => {
  form.id = null
  form.name = ''
  form.watermark_type = 'image'
  form.image_url = ''
  form.image_width = 150
  form.text_content = ''
  form.font_size = 24
  form.text_color = 'rgba(255,255,255,0.7)'
  form.font_family = 'Microsoft YaHei'
  form.user_id_format = 'ID: {user_id}'
  form.position = 'bottom_right'
  form.opacity = 0.7
  form.margin_x = 20
  form.margin_y = 20
  form.apply_to = 'all'
  form.priority = 10
  form.is_active = true
}

// 上传成功
const handleUploadSuccess = (res) => {
  form.image_url = res.url || res.data?.url
  ElMessage.success('上传成功')
}

// 上传前检查
const beforeUpload = (file) => {
  const isPNG = file.type === 'image/png' || file.type === 'image/gif'
  const isLt2M = file.size / 1024 / 1024 < 2
  if (!isPNG) {
    ElMessage.error('水印图片只能是 PNG 或 GIF 格式')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB')
    return false
  }
  return true
}

// 提交表单
const submitForm = async () => {
  if (form.watermark_type === 'image' && !form.image_url) {
    ElMessage.warning('请上传水印图片')
    return
  }
  if (form.watermark_type === 'text' && !form.text_content) {
    ElMessage.warning('请输入水印文字')
    return
  }

  dialog.loading = true
  try {
    const data = { ...form }

    if (dialog.isEdit) {
      await api.put(`/watermark/configs/${form.id}`, data)
      ElMessage.success('更新成功')
    } else {
      await api.post('/watermark/configs', data)
      ElMessage.success('添加成功')
    }

    dialog.visible = false
    fetchWatermarks()
  } catch (error) {
    ElMessage.error('操作失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    dialog.loading = false
  }
}

// 切换状态
const toggleStatus = async (row) => {
  try {
    await api.patch(`/watermark/configs/${row.id}/toggle`)
    ElMessage.success(row.is_active ? '已启用' : '已禁用')
  } catch (error) {
    row.is_active = !row.is_active
    ElMessage.error('操作失败')
  }
}

// 删除水印
const deleteWatermark = async (row) => {
  await ElMessageBox.confirm('确定删除该水印配置？', '确认删除', { type: 'warning' })
  try {
    await api.delete(`/watermark/configs/${row.id}`)
    ElMessage.success('删除成功')
    fetchWatermarks()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

// 辅助函数
const getTypeTag = (type) => {
  const map = { image: 'primary', text: 'success', user_id: 'warning' }
  return map[type] || 'info'
}

const getTypeText = (type) => {
  const map = { image: '图片水印', text: '文字水印', user_id: '用户ID' }
  return map[type] || type
}

const getPositionText = (pos) => {
  const map = {
    top_left: '左上角',
    top_right: '右上角',
    bottom_left: '左下角',
    bottom_right: '右下角',
    center: '居中',
    random: '随机移动'
  }
  return map[pos] || pos
}

const getApplyToText = (val) => {
  const map = { all: '所有视频', paid: '付费视频', free: '免费视频', vip: 'VIP视频' }
  return map[val] || val
}

onMounted(() => {
  fetchWatermarks()
})
</script>

<style lang="scss" scoped>
.watermark-manage {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.watermark-preview {
  width: 100px;
  height: 40px;
}

.text-preview {
  font-weight: 600;
}

.text-muted {
  color: #909399;
  font-style: italic;
}

.watermark-uploader {
  :deep(.el-upload) {
    width: 200px;
    height: 80px;
    border: 1px dashed #d9d9d9;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    background: #fafafa;
    transition: border-color 0.3s;

    &:hover {
      border-color: #409eff;
    }
  }
}

.uploaded-image {
  width: 200px;
  height: 80px;
}

.upload-icon {
  font-size: 32px;
  color: #8c939d;
}

.upload-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.form-tip {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}

.margin-label {
  margin: 0 12px 0 8px;
  font-size: 14px;
  color: #606266;
}

:deep(.el-slider) {
  width: 200px;
}
</style>






















