<template>
  <div class="report-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>举报审核管理</span>
          <el-button type="primary" @click="fetchStats">刷新统计</el-button>
        </div>
      </template>

      <!-- 统计信息 -->
      <el-row :gutter="16" class="stats-row">
        <el-col :span="6">
          <div class="stat-item pending">
            <div class="stat-value">{{ stats.pending || 0 }}</div>
            <div class="stat-label">待处理</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item processed">
            <div class="stat-value">{{ stats.processed || 0 }}</div>
            <div class="stat-label">已处理</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item accepted">
            <div class="stat-value">{{ stats.accepted || 0 }}</div>
            <div class="stat-label">已采纳</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item rejected">
            <div class="stat-value">{{ stats.rejected || 0 }}</div>
            <div class="stat-label">已驳回</div>
          </div>
        </el-col>
      </el-row>

      <!-- 筛选栏 -->
      <div class="filter-bar">
        <el-select v-model="filter.status" placeholder="处理状态" clearable style="width: 120px">
          <el-option label="待处理" value="pending" />
          <el-option label="已处理" value="processed" />
          <el-option label="已采纳" value="accepted" />
          <el-option label="已驳回" value="rejected" />
        </el-select>
        <el-select v-model="filter.targetType" placeholder="举报类型" clearable style="width: 120px">
          <el-option label="视频" value="video" />
          <el-option label="评论" value="comment" />
          <el-option label="用户" value="user" />
        </el-select>
        <el-select v-model="filter.categoryId" placeholder="举报原因" clearable style="width: 140px">
          <el-option
            v-for="cat in categories"
            :key="cat.id"
            :label="cat.name"
            :value="cat.id"
          />
        </el-select>
        <el-date-picker
          v-model="filter.dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 240px"
        />
        <el-button type="primary" @click="fetchReports">查询</el-button>
        <el-button @click="resetFilter">重置</el-button>
      </div>

      <!-- 举报列表 -->
      <el-table :data="reports" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="reporter_name" label="举报人" width="120" />
        <el-table-column prop="target_type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="getTargetTypeTag(row.target_type)" size="small">
              {{ getTargetTypeText(row.target_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target_id" label="目标ID" width="100" />
        <el-table-column label="目标信息" min-width="200">
          <template #default="{ row }">
            <div class="target-info">
              <template v-if="row.target_type === 'video'">
                <el-image
                  v-if="row.target_cover"
                  :src="row.target_cover"
                  class="target-cover"
                  fit="cover"
                />
                <span class="target-title">{{ row.target_title || `视频#${row.target_id}` }}</span>
              </template>
              <template v-else-if="row.target_type === 'comment'">
                <span class="target-content">{{ row.target_content || `评论#${row.target_id}` }}</span>
              </template>
              <template v-else>
                <span>{{ row.target_name || `用户#${row.target_id}` }}</span>
              </template>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="category_name" label="举报原因" width="120" />
        <el-table-column prop="reason" label="详细说明" min-width="150" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTag(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="举报时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button size="small" @click="viewTarget(row)">查看</el-button>
              <el-button size="small" type="success" @click="handleReport(row, 'accepted')">采纳</el-button>
              <el-button size="small" type="danger" @click="handleReport(row, 'rejected')">驳回</el-button>
            </template>
            <template v-else>
              <el-button size="small" @click="viewDetail(row)">详情</el-button>
            </template>
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
        @size-change="fetchReports"
        @current-change="fetchReports"
      />
    </el-card>

    <!-- 处理对话框 -->
    <el-dialog v-model="handleDialog.visible" :title="handleDialog.title" width="500px">
      <el-form label-width="100px">
        <el-form-item label="举报内容">
          <div class="report-content">
            <p><strong>类型：</strong>{{ getTargetTypeText(handleDialog.report?.target_type) }}</p>
            <p><strong>原因：</strong>{{ handleDialog.report?.category_name }}</p>
            <p><strong>说明：</strong>{{ handleDialog.report?.reason || '无' }}</p>
          </div>
        </el-form-item>
        <el-form-item label="处理方式" v-if="handleDialog.action === 'accepted'">
          <el-checkbox-group v-model="handleForm.actions">
            <el-checkbox label="delete_target">删除被举报内容</el-checkbox>
            <el-checkbox label="warn_user">警告被举报用户</el-checkbox>
            <el-checkbox label="ban_user">封禁被举报用户</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="处理说明">
          <el-input
            v-model="handleForm.note"
            type="textarea"
            rows="3"
            placeholder="可选，输入处理说明"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="handleDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitHandle" :loading="handleDialog.loading">确认处理</el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailDialog.visible" title="举报详情" width="600px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="举报ID">{{ detailDialog.data?.id }}</el-descriptions-item>
        <el-descriptions-item label="举报人">{{ detailDialog.data?.reporter_name }}</el-descriptions-item>
        <el-descriptions-item label="举报类型">
          <el-tag :type="getTargetTypeTag(detailDialog.data?.target_type)">
            {{ getTargetTypeText(detailDialog.data?.target_type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="目标ID">{{ detailDialog.data?.target_id }}</el-descriptions-item>
        <el-descriptions-item label="举报原因">{{ detailDialog.data?.category_name }}</el-descriptions-item>
        <el-descriptions-item label="详细说明">{{ detailDialog.data?.reason || '无' }}</el-descriptions-item>
        <el-descriptions-item label="举报时间">{{ formatDate(detailDialog.data?.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="处理状态">
          <el-tag :type="getStatusTag(detailDialog.data?.status)">
            {{ getStatusText(detailDialog.data?.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="处理人">{{ detailDialog.data?.handler_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="处理时间">{{ formatDate(detailDialog.data?.handled_at) || '-' }}</el-descriptions-item>
        <el-descriptions-item label="处理说明">{{ detailDialog.data?.handle_note || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'

const loading = ref(false)
const reports = ref([])
const categories = ref([])
const stats = ref({})

const filter = reactive({
  status: '',
  targetType: '',
  categoryId: '',
  dateRange: null
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const handleDialog = reactive({
  visible: false,
  loading: false,
  title: '',
  action: '',
  report: null
})

const handleForm = reactive({
  actions: [],
  note: ''
})

const detailDialog = reactive({
  visible: false,
  data: null
})

// 获取举报列表
const fetchReports = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      status: filter.status || undefined,
      target_type: filter.targetType || undefined,
      category_id: filter.categoryId || undefined
    }
    if (filter.dateRange) {
      params.start_date = filter.dateRange[0]
      params.end_date = filter.dateRange[1]
    }
    const res = await api.get('/reports/admin/list', { params })
    reports.value = res.data?.items || res.items || []
    pagination.total = res.data?.total || res.total || 0
  } catch (error) {
    ElMessage.error('获取举报列表失败')
  } finally {
    loading.value = false
  }
}

// 获取统计
const fetchStats = async () => {
  try {
    const res = await api.get('/reports/admin/stats')
    stats.value = res.data || res
  } catch (error) {
    console.error('获取统计失败:', error)
  }
}

// 获取举报分类
const fetchCategories = async () => {
  try {
    const res = await api.get('/reports/categories')
    categories.value = res.data || res || []
  } catch (error) {
    console.error('获取分类失败:', error)
  }
}

// 重置筛选
const resetFilter = () => {
  filter.status = ''
  filter.targetType = ''
  filter.categoryId = ''
  filter.dateRange = null
  pagination.page = 1
  fetchReports()
}

// 查看目标
const viewTarget = (row) => {
  const type = row.target_type
  const id = row.target_id
  if (type === 'video') {
    window.open(`/user/video/${id}`, '_blank')
  } else if (type === 'user') {
    window.open(`/users?id=${id}`, '_blank')
  }
}

// 处理举报
const handleReport = (row, action) => {
  handleDialog.report = row
  handleDialog.action = action
  handleDialog.title = action === 'accepted' ? '采纳举报' : '驳回举报'
  handleForm.actions = []
  handleForm.note = ''
  handleDialog.visible = true
}

// 提交处理
const submitHandle = async () => {
  handleDialog.loading = true
  try {
    await api.post(`/reports/admin/${handleDialog.report.id}/handle`, {
      status: handleDialog.action,
      actions: handleForm.actions,
      handle_note: handleForm.note
    })
    ElMessage.success('处理成功')
    handleDialog.visible = false
    fetchReports()
    fetchStats()
  } catch (error) {
    ElMessage.error('处理失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    handleDialog.loading = false
  }
}

// 查看详情
const viewDetail = (row) => {
  detailDialog.data = row
  detailDialog.visible = true
}

// 辅助函数
const formatDate = (date) => {
  if (!date) return ''
  return new Date(date).toLocaleString('zh-CN')
}

const getTargetTypeTag = (type) => {
  const map = { video: 'primary', comment: 'warning', user: 'danger' }
  return map[type] || 'info'
}

const getTargetTypeText = (type) => {
  const map = { video: '视频', comment: '评论', user: '用户' }
  return map[type] || type
}

const getStatusTag = (status) => {
  const map = { pending: 'warning', processed: 'info', accepted: 'success', rejected: 'danger' }
  return map[status] || ''
}

const getStatusText = (status) => {
  const map = { pending: '待处理', processed: '已处理', accepted: '已采纳', rejected: '已驳回' }
  return map[status] || status
}

onMounted(() => {
  fetchReports()
  fetchStats()
  fetchCategories()
})
</script>

<style lang="scss" scoped>
.report-manage {
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
    padding: 20px;
    border-radius: 8px;
    color: #fff;

    &.pending { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    &.processed { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    &.accepted { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    &.rejected { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }

    .stat-value {
      font-size: 32px;
      font-weight: 600;
    }

    .stat-label {
      font-size: 14px;
      margin-top: 4px;
      opacity: 0.9;
    }
  }
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.target-info {
  display: flex;
  align-items: center;
  gap: 8px;

  .target-cover {
    width: 60px;
    height: 40px;
    border-radius: 4px;
    flex-shrink: 0;
  }

  .target-title,
  .target-content {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}

.report-content {
  p {
    margin: 8px 0;
  }
}
</style>





















