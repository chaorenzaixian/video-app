<template>
  <div class="categories-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>分类管理</span>
          <el-button type="primary" @click="openAddDialog()">
            <el-icon><Plus /></el-icon>新增一级分类
          </el-button>
        </div>
      </template>

      <el-table 
        :data="categories" 
        stripe 
        v-loading="loading"
        row-key="id"
        :tree-props="{ children: 'children' }"
        default-expand-all
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="名称" min-width="150">
          <template #default="{ row }">
            <span :class="{ 'sub-category': row.level === 2 }">
              {{ row.name }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="级别" width="100">
          <template #default="{ row }">
            <el-tag :type="row.level === 1 ? 'primary' : 'success'" size="small">
              {{ row.level === 1 ? '一级' : '二级' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="分类类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getCategoryTypeTag(row.category_type)" size="small">
              {{ getCategoryTypeLabel(row.category_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="video_count" label="视频数" width="100" />
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openAddDialog(row)" v-if="row.level === 1">
              添加子分类
            </el-button>
            <el-button link type="primary" @click="editCategory(row)">编辑</el-button>
            <el-popconfirm title="确定删除这个分类吗？" @confirm="deleteCategory(row.id)">
              <template #reference>
                <el-button link type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="450px"
      destroy-on-close
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="级别" v-if="!isEdit">
          <el-tag :type="form.level === 1 ? 'primary' : 'success'">
            {{ form.level === 1 ? '一级分类' : '二级分类' }}
          </el-tag>
          <span v-if="form.parent_id" class="parent-info">
            （父分类：{{ parentName }}）
          </span>
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入分类描述" />
        </el-form-item>
        <el-form-item label="分类类型" prop="category_type">
          <el-radio-group v-model="form.category_type">
            <el-radio value="video">普通视频</el-radio>
            <el-radio value="short">短视频</el-radio>
            <el-radio value="both">两者通用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :max="999" />
        </el-form-item>
        <el-form-item label="父分类" v-if="isEdit && form.level === 2">
          <el-select v-model="form.parent_id" placeholder="选择父分类" style="width: 100%">
            <el-option
              v-for="cat in parentCategories"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveCategory" :loading="saving">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const categories = ref([])
const parentName = ref('')

const form = reactive({
  name: '',
  description: '',
  sort_order: 0,
  parent_id: null,
  level: 1,
  category_type: 'video'  // video/short/both
})

// 分类类型标签颜色
const getCategoryTypeTag = (type) => {
  const map = { 'video': 'primary', 'short': 'success', 'both': 'warning' }
  return map[type] || 'info'
}

// 分类类型标签文字
const getCategoryTypeLabel = (type) => {
  const map = { 'video': '普通视频', 'short': '短视频', 'both': '两者通用' }
  return map[type] || '普通视频'
}

const rules = {
  name: [
    { required: true, message: '请输入分类名称', trigger: 'blur' }
  ]
}

const dialogTitle = computed(() => {
  if (isEdit.value) return '编辑分类'
  return form.level === 1 ? '新增一级分类' : '新增二级分类'
})

// 获取所有一级分类（用于选择父分类）
const parentCategories = computed(() => {
  return categories.value.filter(cat => cat.level === 1)
})

const fetchCategories = async () => {
  loading.value = true
  try {
    const res = await api.get('/videos/categories')
    categories.value = res.data || []
  } catch (e) {
    console.error('获取分类失败', e)
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.name = ''
  form.description = ''
  form.sort_order = 0
  form.parent_id = null
  form.level = 1
  form.category_type = 'video'
}

const openAddDialog = (parent = null) => {
  isEdit.value = false
  editingId.value = null
  resetForm()
  
  if (parent) {
    // 添加子分类
    form.parent_id = parent.id
    form.level = 2
    parentName.value = parent.name
  } else {
    // 添加一级分类
    form.level = 1
    parentName.value = ''
  }
  
  dialogVisible.value = true
}

const editCategory = (row) => {
  isEdit.value = true
  editingId.value = row.id
  form.name = row.name
  form.description = row.description || ''
  form.sort_order = row.sort_order || 0
  form.parent_id = row.parent_id
  form.level = row.level || 1
  form.category_type = row.category_type || 'video'
  
  // 查找父分类名称
  if (row.parent_id) {
    const parent = categories.value.find(c => c.id === row.parent_id)
    parentName.value = parent ? parent.name : ''
  }
  
  dialogVisible.value = true
}

const saveCategory = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    saving.value = true
    try {
      const data = {
        name: form.name,
        description: form.description,
        sort_order: form.sort_order,
        parent_id: form.parent_id,
        level: form.level,
        category_type: form.category_type
      }

      if (isEdit.value && editingId.value) {
        await api.put(`/admin/categories/${editingId.value}`, data)
        ElMessage.success('更新成功')
      } else {
        await api.post('/admin/categories', data)
        ElMessage.success('创建成功')
      }

      dialogVisible.value = false
      fetchCategories()
    } catch (e) {
      console.error('保存失败', e)
      // 显示后端返回的错误信息
      const errorMsg = e.response?.data?.detail || '保存失败，请重试'
      ElMessage.error(errorMsg)
    } finally {
      saving.value = false
    }
  })
}

const deleteCategory = async (id) => {
  try {
    await api.delete(`/admin/categories/${id}`)
    ElMessage.success('删除成功')
    fetchCategories()
  } catch (e) {
    console.error('删除失败', e)
  }
}

onMounted(() => {
  fetchCategories()
})
</script>

<style lang="scss" scoped>
.categories-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .sub-category {
    padding-left: 20px;
    color: #606266;
  }
  
  .parent-info {
    margin-left: 10px;
    color: #909399;
    font-size: 13px;
  }
}
</style>