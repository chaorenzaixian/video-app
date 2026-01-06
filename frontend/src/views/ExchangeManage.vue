<template>
  <div class="exchange-manage">
    <div class="page-header">
      <h2>积分兑换管理</h2>
      <el-button type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>
        新增商品
      </el-button>
    </div>

    <!-- 商品列表 -->
    <el-card>
      <el-table :data="items" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="卡片图片" width="120">
          <template #default="{ row }">
            <el-image 
              v-if="row.image_url"
              :src="getImageUrl(row.image_url)" 
              fit="cover"
              style="width: 80px; height: 50px; border-radius: 6px;"
            />
            <span v-else class="no-image">未上传</span>
          </template>
        </el-table-column>
        <el-table-column prop="item_name" label="商品名称" width="150" />
        <el-table-column prop="item_desc" label="商品描述" min-width="200" />
        <el-table-column prop="item_type" label="商品类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeColor(row.item_type)">{{ getTypeName(row.item_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="points_cost" label="所需积分" width="100">
          <template #default="{ row }">
            <span class="points-cost">{{ row.points_cost }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="item_value" label="商品价值" width="100" />
        <el-table-column prop="stock" label="库存" width="100">
          <template #default="{ row }">
            <el-tag :type="row.stock > 10 ? 'success' : row.stock > 0 ? 'warning' : 'danger'">
              {{ row.stock === -1 ? '无限' : row.stock }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-switch 
              v-model="row.is_active" 
              @change="toggleStatus(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="editItem(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteItem(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? '编辑商品' : '新增商品'"
      width="550px"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="卡片图片" prop="image_url">
          <div class="image-upload-wrapper">
            <el-upload
              class="card-image-uploader"
              :action="uploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="handleImageSuccess"
              :on-error="handleImageError"
              :before-upload="beforeImageUpload"
              accept="image/*"
            >
              <div v-if="form.image_url" class="uploaded-image">
                <img :src="getImageUrl(form.image_url)" />
                <div class="image-actions">
                  <el-icon><Plus /></el-icon>
                  <span>更换</span>
                </div>
              </div>
              <div v-else class="upload-placeholder">
                <el-icon><Plus /></el-icon>
                <span>上传卡片图片</span>
              </div>
            </el-upload>
            <span class="form-tip">建议尺寸: 400x200，票券风格背景图</span>
          </div>
        </el-form-item>
        <el-form-item label="商品名称" prop="item_name">
          <el-input v-model="form.item_name" placeholder="输入商品名称" />
        </el-form-item>
        <el-form-item label="商品描述" prop="item_desc">
          <el-input v-model="form.item_desc" type="textarea" :rows="2" placeholder="输入商品描述" />
        </el-form-item>
        <el-form-item label="商品类型" prop="item_type">
          <el-select v-model="form.item_type" placeholder="选择商品类型">
            <el-option label="VIP体验卡" value="vip_card" />
            <el-option label="AI科技券" value="ai_ticket" />
            <el-option label="情趣盲盒" value="blind_box" />
            <el-option label="优惠券" value="coupon" />
            <el-option label="实物商品" value="physical" />
            <el-option label="虚拟商品" value="virtual" />
          </el-select>
        </el-form-item>
        <el-form-item label="所需积分" prop="points_cost">
          <el-input-number v-model="form.points_cost" :min="1" :max="100000" />
        </el-form-item>
        <el-form-item label="商品价值" prop="item_value">
          <el-input-number v-model="form.item_value" :min="0" />
          <span class="form-tip">如VIP天数、优惠金额等</span>
        </el-form-item>
        <el-form-item label="库存数量" prop="stock">
          <el-input-number v-model="form.stock" :min="-1" />
          <span class="form-tip">-1表示无限库存</span>
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '@/utils/api'

const loading = ref(false)
const submitting = ref(false)
const items = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)

// 图片上传配置 - 使用相对路径让Vite代理处理
const uploadUrl = '/api/v1/ads/upload/image'
const uploadHeaders = computed(() => ({
  'Authorization': `Bearer ${localStorage.getItem('token')}`
}))

const defaultForm = {
  item_name: '',
  item_desc: '',
  item_type: 'vip_card',
  points_cost: 100,
  item_value: 1,
  stock: -1,
  is_active: true,
  image_url: ''
}

const form = ref({ ...defaultForm })

// 获取图片完整URL
const getImageUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  // /images/ 开头的是前端静态资源，直接返回
  if (url.startsWith('/images/')) return url
  // /uploads/ 开头的需要通过代理或后端URL
  if (import.meta.env.DEV) {
    return url
  }
  const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
  return `${baseUrl}${url}`
}

// 图片上传成功
const handleImageSuccess = (response) => {
  if (response.url) {
    form.value.image_url = response.url
    ElMessage.success('图片上传成功')
  } else {
    ElMessage.error('上传失败：无效的响应')
  }
}

// 图片上传失败
const handleImageError = (error) => {
  console.error('图片上传失败:', error)
  ElMessage.error('图片上传失败，请重试')
}

// 上传前验证
const beforeImageUpload = (file) => {
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

const rules = {
  item_name: [{ required: true, message: '请输入商品名称', trigger: 'blur' }],
  item_type: [{ required: true, message: '请选择商品类型', trigger: 'change' }],
  points_cost: [{ required: true, message: '请输入所需积分', trigger: 'blur' }]
}

const typeMap = {
  vip_card: { name: 'VIP体验卡', color: 'warning' },
  ai_ticket: { name: 'AI科技券', color: 'danger' },
  blind_box: { name: '情趣盲盒', color: 'success' },
  coupon: { name: '优惠券', color: 'success' },
  physical: { name: '实物商品', color: 'primary' },
  virtual: { name: '虚拟商品', color: 'info' }
}

const getTypeName = (type) => typeMap[type]?.name || type
const getTypeColor = (type) => typeMap[type]?.color || 'info'

// 获取商品列表
const fetchItems = async () => {
  loading.value = true
  try {
    const res = await api.get('/admin/exchange-items')
    items.value = res.data || []
  } catch (error) {
    console.error('获取商品列表失败:', error)
    ElMessage.error('获取商品列表失败')
  } finally {
    loading.value = false
  }
}

// 显示新增对话框
const showAddDialog = () => {
  isEdit.value = false
  form.value = { ...defaultForm }
  dialogVisible.value = true
}

// 编辑商品
const editItem = (row) => {
  isEdit.value = true
  form.value = { ...row }
  dialogVisible.value = true
}

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      if (isEdit.value) {
        await api.put(`/admin/exchange-items/${form.value.id}`, form.value)
        ElMessage.success('更新成功')
      } else {
        await api.post('/admin/exchange-items', form.value)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      fetchItems()
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

// 切换状态
const toggleStatus = async (row) => {
  try {
    await api.put(`/admin/exchange-items/${row.id}`, { is_active: row.is_active })
    ElMessage.success(row.is_active ? '已启用' : '已禁用')
  } catch (error) {
    row.is_active = !row.is_active
    ElMessage.error('操作失败')
  }
}

// 删除商品
const deleteItem = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该商品吗？', '提示', {
      type: 'warning'
    })
    await api.delete(`/admin/exchange-items/${row.id}`)
    ElMessage.success('删除成功')
    fetchItems()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchItems()
})
</script>

<style lang="scss" scoped>
.exchange-manage {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  h2 {
    margin: 0;
    font-size: 20px;
  }
}

.points-cost {
  color: #e6a23c;
  font-weight: 600;
}

.no-image {
  color: #999;
  font-size: 12px;
}

.form-tip {
  margin-left: 10px;
  color: #999;
  font-size: 12px;
}

.image-upload-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
  
  .form-tip {
    margin-left: 0;
  }
}

.card-image-uploader {
  :deep(.el-upload) {
    width: 200px;
    height: 100px;
    border: 2px dashed #dcdfe6;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s;
    overflow: hidden;
    
    &:hover {
      border-color: #409eff;
    }
  }
}

.uploaded-image {
  position: relative;
  width: 100%;
  height: 100%;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  .image-actions {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 4px;
    color: #fff;
    opacity: 0;
    transition: opacity 0.3s;
    
    .el-icon {
      font-size: 20px;
    }
    
    span {
      font-size: 12px;
    }
  }
  
  &:hover .image-actions {
    opacity: 1;
  }
}

.upload-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #999;
  
  .el-icon {
    font-size: 24px;
    color: #dcdfe6;
  }
  
  span {
    font-size: 12px;
  }
}
</style>
