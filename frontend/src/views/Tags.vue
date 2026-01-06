<template>
  <div class="tags-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>标签管理</span>
          <el-button type="primary" @click="openAddDialog">
            <el-icon><Plus /></el-icon>新增标签
          </el-button>
        </div>
      </template>

      <el-table :data="tags" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="标签名称" min-width="200">
          <template #default="{ row }">
            <el-tag>{{ row.name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="use_count" label="使用次数" width="120" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="editTag(row)">编辑</el-button>
            <el-popconfirm title="确定删除这个标签吗？" @confirm="deleteTag(row.id)">
              <template #reference>
                <el-button link type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- 空状态 -->
      <el-empty v-if="!loading && tags.length === 0" description="暂无标签" />
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑标签' : '新增标签'"
      width="400px"
      destroy-on-close
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="标签名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入标签名称" maxlength="30" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveTag" :loading="saving">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const tags = ref([])

const form = reactive({
  name: ''
})

const rules = {
  name: [
    { required: true, message: '请输入标签名称', trigger: 'blur' },
    { min: 1, max: 30, message: '标签名称长度在1-30个字符', trigger: 'blur' }
  ]
}

const fetchTags = async () => {
  loading.value = true
  try {
    const res = await api.get('/admin/tags')
    tags.value = res.data || []
  } catch (e) {
    console.error('获取标签失败', e)
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.name = ''
}

const openAddDialog = () => {
  isEdit.value = false
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

const editTag = (row) => {
  isEdit.value = true
  editingId.value = row.id
  form.name = row.name
  dialogVisible.value = true
}

const saveTag = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    saving.value = true
    try {
      if (isEdit.value && editingId.value) {
        await api.put(`/admin/tags/${editingId.value}`, {
          name: form.name
        })
        ElMessage.success('更新成功')
      } else {
        await api.post('/admin/tags', {
          name: form.name
        })
        ElMessage.success('创建成功')
      }

      dialogVisible.value = false
      fetchTags()
    } catch (e) {
      console.error('保存失败', e)
    } finally {
      saving.value = false
    }
  })
}

const deleteTag = async (id) => {
  try {
    await api.delete(`/admin/tags/${id}`)
    ElMessage.success('删除成功')
    fetchTags()
  } catch (e) {
    console.error('删除失败', e)
  }
}

onMounted(() => {
  fetchTags()
})
</script>

<style lang="scss" scoped>
.tags-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}
</style>






