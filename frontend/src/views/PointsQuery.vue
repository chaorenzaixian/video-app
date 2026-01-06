<template>
  <div class="points-query">
    <div class="page-header">
      <h2>用户积分查询</h2>
    </div>

    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="用户ID">
          <el-input v-model="searchForm.user_id" placeholder="输入用户ID" clearable />
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="searchForm.username" placeholder="输入用户名" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="searchUsers">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 用户积分列表 -->
    <el-card>
      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="user_id" label="用户ID" width="100" />
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="nickname" label="昵称" width="150" />
        <el-table-column prop="total_points" label="累计积分" width="120">
          <template #default="{ row }">
            <span class="points-total">{{ row.total_points || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="available_points" label="可用积分" width="120">
          <template #default="{ row }">
            <span class="points-available">{{ row.available_points || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="frozen_points" label="冻结积分" width="120">
          <template #default="{ row }">
            <span class="points-frozen">{{ row.frozen_points || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewLogs(row)">积分明细</el-button>
            <el-button size="small" type="primary" @click="adjustPoints(row)">调整积分</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchUsers"
        @current-change="fetchUsers"
        class="pagination"
      />
    </el-card>

    <!-- 积分明细对话框 -->
    <el-dialog v-model="logsDialogVisible" title="积分明细" width="700px">
      <el-table :data="pointLogs" v-loading="logsLoading" max-height="400">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="log_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.points_change > 0 ? 'success' : 'danger'">
              {{ getLogTypeName(row.log_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="points_change" label="积分变动" width="100">
          <template #default="{ row }">
            <span :class="row.points_change > 0 ? 'points-plus' : 'points-minus'">
              {{ row.points_change > 0 ? '+' : '' }}{{ row.points_change }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column prop="created_at" label="时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 调整积分对话框 -->
    <el-dialog v-model="adjustDialogVisible" title="调整积分" width="400px">
      <el-form :model="adjustForm" :rules="adjustRules" ref="adjustFormRef" label-width="80px">
        <el-form-item label="用户">
          <span>{{ adjustForm.username }} (ID: {{ adjustForm.user_id }})</span>
        </el-form-item>
        <el-form-item label="当前积分">
          <span class="points-available">{{ adjustForm.current_points }}</span>
        </el-form-item>
        <el-form-item label="调整类型" prop="type">
          <el-radio-group v-model="adjustForm.type">
            <el-radio label="add">增加</el-radio>
            <el-radio label="reduce">减少</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="调整数量" prop="amount">
          <el-input-number v-model="adjustForm.amount" :min="1" :max="100000" />
        </el-form-item>
        <el-form-item label="调整原因" prop="reason">
          <el-input v-model="adjustForm.reason" type="textarea" :rows="2" placeholder="输入调整原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="adjustDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAdjust" :loading="adjusting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const loading = ref(false)
const logsLoading = ref(false)
const adjusting = ref(false)
const users = ref([])
const pointLogs = ref([])
const logsDialogVisible = ref(false)
const adjustDialogVisible = ref(false)
const adjustFormRef = ref(null)

const searchForm = ref({
  user_id: '',
  username: ''
})

const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0
})

const adjustForm = ref({
  user_id: null,
  username: '',
  current_points: 0,
  type: 'add',
  amount: 0,
  reason: ''
})

const adjustRules = {
  amount: [{ required: true, message: '请输入调整数量', trigger: 'blur' }],
  reason: [{ required: true, message: '请输入调整原因', trigger: 'blur' }]
}

const logTypeMap = {
  task: '任务奖励',
  exchange: '积分兑换',
  admin_add: '管理员增加',
  admin_reduce: '管理员减少',
  invite: '邀请奖励',
  register: '注册奖励'
}

const getLogTypeName = (type) => logTypeMap[type] || type

const formatTime = (time) => {
  if (!time) return '-'
  const d = new Date(time)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

// 获取用户积分列表
const fetchUsers = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
      ...searchForm.value
    }
    const res = await api.get('/admin/user-points', { params })
    users.value = res.data?.items || res.data || []
    pagination.value.total = res.data?.total || users.value.length
  } catch (error) {
    console.error('获取用户积分列表失败:', error)
    ElMessage.error('获取用户积分列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索用户
const searchUsers = () => {
  pagination.value.page = 1
  fetchUsers()
}

// 重置搜索
const resetSearch = () => {
  searchForm.value = { user_id: '', username: '' }
  pagination.value.page = 1
  fetchUsers()
}

// 查看积分明细
const viewLogs = async (row) => {
  logsDialogVisible.value = true
  logsLoading.value = true
  try {
    const res = await api.get(`/admin/user-points/${row.user_id}/logs`)
    pointLogs.value = res.data || []
  } catch (error) {
    console.error('获取积分明细失败:', error)
    ElMessage.error('获取积分明细失败')
  } finally {
    logsLoading.value = false
  }
}

// 调整积分
const adjustPoints = (row) => {
  adjustForm.value = {
    user_id: row.user_id,
    username: row.username,
    current_points: row.available_points || 0,
    type: 'add',
    amount: 0,
    reason: ''
  }
  adjustDialogVisible.value = true
}

// 提交调整
const submitAdjust = async () => {
  if (!adjustFormRef.value) return
  
  await adjustFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    adjusting.value = true
    try {
      await api.post(`/admin/user-points/${adjustForm.value.user_id}/adjust`, {
        type: adjustForm.value.type,
        amount: adjustForm.value.amount,
        reason: adjustForm.value.reason
      })
      ElMessage.success('调整成功')
      adjustDialogVisible.value = false
      fetchUsers()
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '调整失败')
    } finally {
      adjusting.value = false
    }
  })
}

onMounted(() => {
  fetchUsers()
})
</script>

<style lang="scss" scoped>
.points-query {
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

.search-card {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}

.points-total {
  color: #409eff;
  font-weight: 600;
}

.points-available {
  color: #67c23a;
  font-weight: 600;
}

.points-frozen {
  color: #909399;
  font-weight: 600;
}

.points-plus {
  color: #67c23a;
  font-weight: 600;
}

.points-minus {
  color: #f56c6c;
  font-weight: 600;
}
</style>

