<template>
  <div class="announcements-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>公告管理</span>
          <el-button type="primary" @click="openAddDialog">
            <el-icon><Plus /></el-icon>添加公告
          </el-button>
        </div>
      </template>

      <!-- 公告列表 -->
      <el-table :data="announcements" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        
        <el-table-column prop="content" label="公告内容" min-width="300" show-overflow-tooltip />
        
        <el-table-column prop="link" label="跳转链接" width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.link">{{ row.link }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="sort_order" label="排序" width="80" />
        
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="开始时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.start_date) }}
          </template>
        </el-table-column>
        
        <el-table-column label="结束时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.end_date) }}
          </template>
        </el-table-column>
        
        <el-table-column label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="editAnnouncement(row)">编辑</el-button>
            <el-popconfirm title="确定删除这条公告吗？" @confirm="deleteAnnouncement(row.id)">
              <template #reference>
                <el-button link type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- 空状态 -->
      <el-empty v-if="!loading && announcements.length === 0" description="暂无公告" />
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? '编辑公告' : '添加公告'" 
      width="550px"
      destroy-on-close
    >
      <el-form :model="formData" label-width="100px" :rules="rules" ref="formRef">
        <el-form-item label="公告内容" prop="content">
          <el-input 
            v-model="formData.content" 
            type="textarea" 
            :rows="4" 
            placeholder="请输入公告内容"
          />
        </el-form-item>
        
        <el-form-item label="跳转链接">
          <el-input 
            v-model="formData.link" 
            placeholder="点击公告跳转的链接（可选）"
          />
        </el-form-item>
        
        <el-form-item label="排序">
          <el-input-number 
            v-model="formData.sort_order" 
            :min="0" 
            :max="9999"
            placeholder="数字越大越靠前"
          />
        </el-form-item>
        
        <el-form-item label="状态">
          <el-switch 
            v-model="formData.is_active" 
            active-text="启用" 
            inactive-text="禁用"
          />
        </el-form-item>
        
        <el-form-item label="开始时间">
          <el-date-picker
            v-model="formData.start_date"
            type="datetime"
            placeholder="选择开始时间"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="结束时间">
          <el-date-picker
            v-model="formData.end_date"
            type="datetime"
            placeholder="选择结束时间"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveAnnouncement" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/utils/api'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'

const loading = ref(false)
const saving = ref(false)
const announcements = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const formRef = ref(null)

const formData = reactive({
  content: '',
  link: '',
  sort_order: 0,
  is_active: true,
  start_date: null,
  end_date: null
})

const rules = {
  content: [
    { required: true, message: '请输入公告内容', trigger: 'blur' }
  ]
}

const fetchAnnouncements = async () => {
  loading.value = true
  try {
    const res = await api.get('/ads/announcements/admin')
    announcements.value = res.data
  } catch (error) {
    console.error('获取公告列表失败:', error)
  } finally {
    loading.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

const resetForm = () => {
  formData.content = ''
  formData.link = ''
  formData.sort_order = 0
  formData.is_active = true
  formData.start_date = null
  formData.end_date = null
}

const openAddDialog = () => {
  isEdit.value = false
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

const editAnnouncement = (row) => {
  isEdit.value = true
  editingId.value = row.id
  formData.content = row.content
  formData.link = row.link || ''
  formData.sort_order = row.sort_order
  formData.is_active = row.is_active
  formData.start_date = row.start_date ? new Date(row.start_date) : null
  formData.end_date = row.end_date ? new Date(row.end_date) : null
  dialogVisible.value = true
}

const saveAnnouncement = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    saving.value = true
    try {
      const data = {
        content: formData.content,
        link: formData.link || null,
        sort_order: formData.sort_order,
        is_active: formData.is_active,
        start_date: formData.start_date ? dayjs(formData.start_date).toISOString() : null,
        end_date: formData.end_date ? dayjs(formData.end_date).toISOString() : null
      }

      if (isEdit.value && editingId.value) {
        await api.put(`/ads/announcements/${editingId.value}`, data)
        ElMessage.success('更新成功')
      } else {
        await api.post('/ads/announcements', data)
        ElMessage.success('添加成功')
      }

      dialogVisible.value = false
      fetchAnnouncements()
    } catch (error) {
      console.error('保存公告失败:', error)
      ElMessage.error('保存失败')
    } finally {
      saving.value = false
    }
  })
}

const deleteAnnouncement = async (id) => {
  try {
    await api.delete(`/ads/announcements/${id}`)
    ElMessage.success('删除成功')
    fetchAnnouncements()
  } catch (error) {
    console.error('删除公告失败:', error)
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  fetchAnnouncements()
})
</script>

<style lang="scss" scoped>
.announcements-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .text-muted {
    color: #909399;
  }
}
</style>
