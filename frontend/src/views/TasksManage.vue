<template>
  <div class="tasks-manage">
    <div class="page-header">
      <h2>任务管理</h2>
      <el-button type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>
        新增任务
      </el-button>
    </div>

    <!-- 任务列表 -->
    <el-card>
      <el-table :data="tasks" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="task_type" label="任务类型" width="120" />
        <el-table-column prop="task_name" label="任务名称" width="150" />
        <el-table-column prop="task_desc" label="任务描述" min-width="200" />
        <el-table-column prop="points_reward" label="积分奖励" width="100">
          <template #default="{ row }">
            <el-tag type="warning">+{{ row.points_reward }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="daily_limit" label="每日限制" width="100" />
        <el-table-column prop="sort_order" label="排序" width="80" />
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
            <el-button size="small" @click="editTask(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteTask(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? '编辑任务' : '新增任务'"
      width="500px"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="任务类型" prop="task_type">
          <el-select v-model="form.task_type" placeholder="选择任务类型" :disabled="isEdit">
            <el-option label="签到" value="checkin" />
            <el-option label="发帖" value="post" />
            <el-option label="帖子评论" value="comment_post" />
            <el-option label="视频评论" value="comment_video" />
            <el-option label="邀请" value="invite" />
            <el-option label="购买VIP" value="buy_vip" />
            <el-option label="下载APP" value="download" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="任务名称" prop="task_name">
          <el-input v-model="form.task_name" placeholder="输入任务名称" />
        </el-form-item>
        <el-form-item label="任务描述" prop="task_desc">
          <el-input v-model="form.task_desc" type="textarea" :rows="2" placeholder="输入任务描述" />
        </el-form-item>
        <el-form-item label="积分奖励" prop="points_reward">
          <el-input-number v-model="form.points_reward" :min="1" :max="10000" />
        </el-form-item>
        <el-form-item label="每日限制" prop="daily_limit">
          <el-input-number v-model="form.daily_limit" :min="1" :max="100" />
          <span class="form-tip">每日可完成次数</span>
        </el-form-item>
        <el-form-item label="图标" prop="icon">
          <el-input v-model="form.icon" placeholder="输入图标(emoji或图片路径)" />
        </el-form-item>
        <el-form-item label="跳转链接" prop="action_url">
          <el-input v-model="form.action_url" placeholder="任务跳转链接(可选)" />
        </el-form-item>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="form.sort_order" :min="0" :max="999" />
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
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '@/utils/api'

const loading = ref(false)
const submitting = ref(false)
const tasks = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)

const defaultForm = {
  task_type: '',
  task_name: '',
  task_desc: '',
  points_reward: 5,
  daily_limit: 1,
  icon: '🎁',
  icon_bg: 'linear-gradient(360deg, #9e52cf, #4d45bf)',
  action_type: 'claim',
  action_url: '',
  sort_order: 0,
  is_active: true
}

const form = ref({ ...defaultForm })

const rules = {
  task_type: [{ required: true, message: '请选择任务类型', trigger: 'change' }],
  task_name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  task_desc: [{ required: true, message: '请输入任务描述', trigger: 'blur' }],
  points_reward: [{ required: true, message: '请输入积分奖励', trigger: 'blur' }]
}

// 获取任务列表
const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await api.get('/admin/tasks')
    tasks.value = res.data || []
  } catch (error) {
    console.error('获取任务列表失败:', error)
    ElMessage.error('获取任务列表失败')
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

// 编辑任务
const editTask = (row) => {
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
        await api.put(`/admin/tasks/${form.value.id}`, form.value)
        ElMessage.success('更新成功')
      } else {
        await api.post('/admin/tasks', form.value)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      fetchTasks()
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
    await api.put(`/admin/tasks/${row.id}`, { is_active: row.is_active })
    ElMessage.success(row.is_active ? '已启用' : '已禁用')
  } catch (error) {
    row.is_active = !row.is_active
    ElMessage.error('操作失败')
  }
}

// 删除任务
const deleteTask = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该任务吗？', '提示', {
      type: 'warning'
    })
    await api.delete(`/admin/tasks/${row.id}`)
    ElMessage.success('删除成功')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchTasks()
})
</script>

<style lang="scss" scoped>
.tasks-manage {
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

.form-tip {
  margin-left: 10px;
  color: #999;
  font-size: 12px;
}
</style>

