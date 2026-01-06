<template>
  <div class="short-category-manage">
    <div class="page-header">
      <h1>短视频分类管理</h1>
      <el-button type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>
        添加分类
      </el-button>
    </div>

    <!-- 分类列表 -->
    <el-table :data="categories" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column label="图标" width="80">
        <template #default="{ row }">
          <div v-if="row.icon" class="category-icon">
            <img v-if="row.icon.startsWith('http') || row.icon.startsWith('/')" :src="row.icon" />
            <span v-else>{{ row.icon }}</span>
          </div>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="分类名称" min-width="150" />
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column prop="sort_order" label="排序" width="80" />
      <el-table-column prop="video_count" label="视频数" width="100" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-switch
            v-model="row.is_active"
            @change="toggleStatus(row)"
          />
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="170">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="showEditDialog(row)">编辑</el-button>
          <el-button type="danger" link @click="deleteCategory(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 添加/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? '编辑分类' : '添加分类'" 
      width="500px"
      @close="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="分类名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="图标">
          <el-input v-model="form.icon" placeholder="图标URL或emoji" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            :rows="3"
            placeholder="分类描述（可选）" 
          />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '@/utils/api'

const loading = ref(false)
const categories = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)
const editingId = ref(null)

const form = reactive({
  name: '',
  icon: '',
  description: '',
  sort_order: 0,
  is_active: true
})

const rules = {
  name: [
    { required: true, message: '请输入分类名称', trigger: 'blur' }
  ]
}

onMounted(() => {
  fetchCategories()
})

const fetchCategories = async () => {
  loading.value = true
  try {
    const res = await api.get('/admin/short-categories')
    categories.value = res.data || res || []
  } catch (error) {
    console.error('获取分类失败:', error)
    ElMessage.error('获取分类失败')
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  isEdit.value = false
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

const showEditDialog = (row) => {
  isEdit.value = true
  editingId.value = row.id
  form.name = row.name
  form.icon = row.icon || ''
  form.description = row.description || ''
  form.sort_order = row.sort_order || 0
  form.is_active = row.is_active
  dialogVisible.value = true
}

const resetForm = () => {
  form.name = ''
  form.icon = ''
  form.description = ''
  form.sort_order = 0
  form.is_active = true
  formRef.value?.resetFields()
}

const submitForm = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (isEdit.value) {
      await api.put(`/admin/short-categories/${editingId.value}`, {
        name: form.name,
        icon: form.icon || null,
        description: form.description || null,
        sort_order: form.sort_order,
        is_active: form.is_active
      })
      ElMessage.success('更新成功')
    } else {
      await api.post('/admin/short-categories', {
        name: form.name,
        icon: form.icon || null,
        description: form.description || null,
        sort_order: form.sort_order,
        is_active: form.is_active
      })
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    fetchCategories()
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    submitting.value = false
  }
}

const toggleStatus = async (row) => {
  try {
    await api.put(`/admin/short-categories/${row.id}`, {
      is_active: row.is_active
    })
    ElMessage.success(row.is_active ? '已启用' : '已禁用')
  } catch (error) {
    console.error('更新状态失败:', error)
    row.is_active = !row.is_active
    ElMessage.error('更新状态失败')
  }
}

const deleteCategory = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除分类"${row.name}"吗？${row.video_count > 0 ? `该分类下还有 ${row.video_count} 个视频！` : ''}`,
      '警告',
      { type: 'warning' }
    )

    await api.delete(`/admin/short-categories/${row.id}`)
    ElMessage.success('删除成功')
    fetchCategories()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style lang="scss" scoped>
.short-category-manage {
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
  
  .category-icon {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    
    img {
      max-width: 100%;
      max-height: 100%;
      object-fit: contain;
    }
    
    span {
      font-size: 20px;
    }
  }
  
  .text-muted {
    color: #999;
  }
}
</style>





