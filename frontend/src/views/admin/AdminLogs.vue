<template>
  <div class="admin-logs">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>管理员操作日志</span>
          <el-button type="primary" @click="fetchStats">刷新统计</el-button>
        </div>
      </template>

      <!-- 统计信息 -->
      <el-row :gutter="16" class="stats-row">
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">{{ stats.today || 0 }}</div>
            <div class="stat-label">今日操作</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">{{ stats.week || 0 }}</div>
            <div class="stat-label">本周操作</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">{{ stats.month || 0 }}</div>
            <div class="stat-label">本月操作</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">{{ stats.total || 0 }}</div>
            <div class="stat-label">总操作数</div>
          </div>
        </el-col>
      </el-row>

      <!-- 筛选栏 -->
      <div class="filter-bar">
        <el-select v-model="filter.adminId" placeholder="管理员" clearable style="width: 140px">
          <el-option
            v-for="admin in adminList"
            :key="admin.id"
            :label="admin.username"
            :value="admin.id"
          />
        </el-select>
        <el-select v-model="filter.action" placeholder="操作类型" clearable style="width: 140px">
          <el-option label="用户封禁" value="ban_user" />
          <el-option label="用户解封" value="unban_user" />
          <el-option label="删除视频" value="delete_video" />
          <el-option label="审核视频" value="review_video" />
          <el-option label="删除评论" value="delete_comment" />
          <el-option label="处理举报" value="handle_report" />
          <el-option label="调整金币" value="adjust_coins" />
          <el-option label="修改配置" value="update_config" />
          <el-option label="创建管理员" value="create_admin" />
          <el-option label="处理提现" value="handle_withdrawal" />
        </el-select>
        <el-input v-model="filter.targetId" placeholder="目标ID" clearable style="width: 120px" />
        <el-date-picker
          v-model="filter.dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 240px"
        />
        <el-button type="primary" @click="fetchLogs">查询</el-button>
        <el-button @click="resetFilter">重置</el-button>
      </div>

      <!-- 日志列表 -->
      <el-table :data="logs" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="admin_username" label="管理员" width="120" />
        <el-table-column prop="action" label="操作类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getActionTagType(row.action)">
              {{ getActionText(row.action) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target_type" label="目标类型" width="100">
          <template #default="{ row }">
            {{ getTargetTypeText(row.target_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="target_id" label="目标ID" width="100" />
        <el-table-column prop="description" label="操作描述" min-width="250" show-overflow-tooltip />
        <el-table-column prop="ip_address" label="IP地址" width="140" />
        <el-table-column prop="created_at" label="操作时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pagination"
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @size-change="fetchLogs"
        @current-change="fetchLogs"
      />
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailDialog.visible" title="操作详情" width="600px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="日志ID">{{ detailDialog.data?.id }}</el-descriptions-item>
        <el-descriptions-item label="管理员">{{ detailDialog.data?.admin_username }}</el-descriptions-item>
        <el-descriptions-item label="操作类型">
          <el-tag :type="getActionTagType(detailDialog.data?.action)">
            {{ getActionText(detailDialog.data?.action) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="目标类型">{{ getTargetTypeText(detailDialog.data?.target_type) }}</el-descriptions-item>
        <el-descriptions-item label="目标ID">{{ detailDialog.data?.target_id }}</el-descriptions-item>
        <el-descriptions-item label="操作描述">{{ detailDialog.data?.description }}</el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ detailDialog.data?.ip_address }}</el-descriptions-item>
        <el-descriptions-item label="User-Agent">{{ detailDialog.data?.user_agent }}</el-descriptions-item>
        <el-descriptions-item label="操作时间">{{ formatDate(detailDialog.data?.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="额外数据" v-if="detailDialog.data?.extra_data">
          <pre class="extra-data">{{ JSON.stringify(detailDialog.data.extra_data, null, 2) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const loading = ref(false)
const logs = ref([])
const stats = ref({})
const adminList = ref([])

const filter = reactive({
  adminId: '',
  action: '',
  targetId: '',
  dateRange: null
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const detailDialog = reactive({
  visible: false,
  data: null
})

// 获取日志列表
const fetchLogs = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      admin_id: filter.adminId || undefined,
      action: filter.action || undefined,
      target_id: filter.targetId || undefined
    }
    if (filter.dateRange) {
      params.start_date = filter.dateRange[0]
      params.end_date = filter.dateRange[1]
    }
    const res = await api.get('/admin/logs', { params })
    logs.value = res.data?.items || res.items || []
    pagination.total = res.data?.total || res.total || 0
  } catch (error) {
    ElMessage.error('获取日志失败')
  } finally {
    loading.value = false
  }
}

// 获取统计
const fetchStats = async () => {
  try {
    const res = await api.get('/admin/logs/stats')
    stats.value = res.data || res
  } catch (error) {
    console.error('获取统计失败:', error)
  }
}

// 获取管理员列表
const fetchAdminList = async () => {
  try {
    const res = await api.get('/admin/users', { params: { role: 'admin', page_size: 100 } })
    adminList.value = res.data?.items || res.items || []
  } catch (error) {
    console.error('获取管理员列表失败:', error)
  }
}

// 重置筛选
const resetFilter = () => {
  filter.adminId = ''
  filter.action = ''
  filter.targetId = ''
  filter.dateRange = null
  pagination.page = 1
  fetchLogs()
}

// 显示详情
const showDetail = (row) => {
  detailDialog.data = row
  detailDialog.visible = true
}

// 辅助函数
const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

const getActionTagType = (action) => {
  const dangerActions = ['ban_user', 'delete_video', 'delete_comment']
  const warningActions = ['adjust_coins', 'handle_withdrawal']
  const successActions = ['unban_user', 'review_video']
  
  if (dangerActions.includes(action)) return 'danger'
  if (warningActions.includes(action)) return 'warning'
  if (successActions.includes(action)) return 'success'
  return 'info'
}

const getActionText = (action) => {
  const map = {
    ban_user: '封禁用户',
    unban_user: '解封用户',
    delete_video: '删除视频',
    review_video: '审核视频',
    delete_comment: '删除评论',
    handle_report: '处理举报',
    adjust_coins: '调整金币',
    update_config: '修改配置',
    create_admin: '创建管理员',
    handle_withdrawal: '处理提现',
    login: '管理员登录',
    logout: '管理员登出'
  }
  return map[action] || action
}

const getTargetTypeText = (type) => {
  const map = {
    user: '用户',
    video: '视频',
    comment: '评论',
    report: '举报',
    order: '订单',
    config: '配置',
    withdrawal: '提现'
  }
  return map[type] || type || '-'
}

onMounted(() => {
  fetchLogs()
  fetchStats()
  fetchAdminList()
})
</script>

<style lang="scss" scoped>
.admin-logs {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-row {
  margin-bottom: 20px;
  
  .stat-item {
    text-align: center;
    padding: 16px;
    background: #f5f7fa;
    border-radius: 8px;
    
    .stat-value {
      font-size: 28px;
      font-weight: 600;
      color: #303133;
    }
    
    .stat-label {
      font-size: 14px;
      color: #909399;
      margin-top: 4px;
    }
  }
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}

.extra-data {
  margin: 0;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 12px;
  max-height: 200px;
  overflow: auto;
}
</style>





















