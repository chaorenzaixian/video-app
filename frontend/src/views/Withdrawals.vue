<template>
  <div class="withdrawals-page">
    <div class="page-header">
      <h2>提现管理</h2>
      <div class="stats-cards">
        <div class="stat-card pending">
          <span class="stat-value">{{ stats.pending_withdrawals }}</span>
          <span class="stat-label">待处理</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">¥{{ stats.total_withdrawn.toFixed(2) }}</span>
          <span class="stat-label">已提现</span>
        </div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-select v-model="filters.status" placeholder="状态筛选" clearable @change="fetchWithdrawals">
        <el-option label="全部" value="" />
        <el-option label="待审核" value="pending" />
        <el-option label="处理中" value="processing" />
        <el-option label="已完成" value="success" />
        <el-option label="已拒绝" value="rejected" />
        <el-option label="失败" value="failed" />
      </el-select>
      <div class="filter-actions">
        <el-button type="success" :disabled="!selectedWithdrawals.length" @click="batchApprove">
          批量通过 ({{ selectedWithdrawals.length }})
        </el-button>
        <el-button type="danger" :disabled="!selectedWithdrawals.length" @click="batchRejectDialog = true">
          批量拒绝
        </el-button>
        <el-button @click="exportWithdrawals">导出数据</el-button>
      </div>
    </div>

    <!-- 提现列表 -->
    <el-table :data="withdrawals" v-loading="loading" stripe @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="50" />
      <el-table-column prop="username" label="用户名" width="120" />
      <el-table-column prop="amount" label="提现金额" width="120">
        <template #default="{ row }">
          <span class="amount">¥{{ row.amount.toFixed(2) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="fee" label="手续费" width="100">
        <template #default="{ row }">
          ¥{{ row.fee.toFixed(2) }}
        </template>
      </el-table-column>
      <el-table-column prop="actual_amount" label="实际到账" width="120">
        <template #default="{ row }">
          <span class="actual-amount">¥{{ row.actual_amount.toFixed(2) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="withdraw_type" label="提现方式" width="100">
        <template #default="{ row }">
          {{ getTypeName(row.withdraw_type) }}
        </template>
      </el-table-column>
      <el-table-column prop="account_name" label="账户名" width="120" />
      <el-table-column prop="account_number" label="账号" width="180">
        <template #default="{ row }">
          <span class="account-number">{{ maskAccount(row.account_number) }}</span>
          <el-button type="text" size="small" @click="showAccount(row)">查看</el-button>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusName(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="申请时间" width="160">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'pending'">
            <el-button type="success" size="small" @click="approveWithdraw(row)">通过</el-button>
            <el-button type="danger" size="small" @click="rejectWithdraw(row)">拒绝</el-button>
          </template>
          <template v-else>
            <span class="processed-time">{{ row.processed_at ? formatTime(row.processed_at) : '' }}</span>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="page"
      v-model:page-size="pageSize"
      :total="total"
      layout="total, prev, pager, next"
      @current-change="fetchWithdrawals"
    />

    <!-- 拒绝弹窗 -->
    <el-dialog v-model="rejectDialogVisible" title="拒绝提现" width="400px">
      <el-form :model="rejectForm" label-width="80px">
        <el-form-item label="拒绝原因">
          <el-input 
            v-model="rejectForm.reason" 
            type="textarea" 
            :rows="3" 
            placeholder="请输入拒绝原因"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="submitReject">确认拒绝</el-button>
      </template>
    </el-dialog>

    <!-- 批量拒绝弹窗 -->
    <el-dialog v-model="batchRejectDialog" title="批量拒绝提现" width="400px">
      <p>将拒绝 {{ selectedWithdrawals.filter(w => w.status === 'pending').length }} 笔提现申请</p>
      <el-form label-width="80px">
        <el-form-item label="拒绝原因">
          <el-input 
            v-model="batchRejectReason" 
            type="textarea" 
            :rows="3" 
            placeholder="请输入统一的拒绝原因"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchRejectDialog = false">取消</el-button>
        <el-button type="danger" @click="submitBatchReject">确认批量拒绝</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'
import dayjs from 'dayjs'

const loading = ref(false)
const withdrawals = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filters = ref({ status: '' })
const stats = ref({ pending_withdrawals: 0, total_withdrawn: 0 })
const selectedWithdrawals = ref([])
const batchRejectDialog = ref(false)
const batchRejectReason = ref('')

const rejectDialogVisible = ref(false)
const currentWithdraw = ref(null)
const rejectForm = ref({ reason: '' })

// 获取统计数据
const fetchStats = async () => {
  try {
    const res = await api.get('/admin/promotion/stats')
    const data = res.data || res
    stats.value = {
      pending_withdrawals: data.pending_withdrawals,
      total_withdrawn: data.total_withdrawn
    }
  } catch (error) {
    console.error('获取统计失败:', error)
  }
}

// 获取提现列表
const fetchWithdrawals = async () => {
  loading.value = true
  try {
    const res = await api.get('/admin/withdrawals', {
      params: {
        page: page.value,
        page_size: pageSize.value,
        status: filters.value.status || undefined
      }
    })
    const data = res.data || res
    withdrawals.value = data.items
    total.value = data.total
  } catch (error) {
    ElMessage.error('获取提现列表失败')
  } finally {
    loading.value = false
  }
}

// 通过提现
const approveWithdraw = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定通过该提现申请？\n金额：¥${row.amount.toFixed(2)}\n实际到账：¥${row.actual_amount.toFixed(2)}`,
      '确认通过',
      { type: 'warning' }
    )
    await api.post(`/admin/withdrawals/${row.id}/process`, { action: 'approve' })
    ElMessage.success('已通过')
    fetchWithdrawals()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '操作失败')
    }
  }
}

// 拒绝提现
const rejectWithdraw = (row) => {
  currentWithdraw.value = row
  rejectForm.value = { reason: '' }
  rejectDialogVisible.value = true
}

const submitReject = async () => {
  if (!rejectForm.value.reason) {
    ElMessage.warning('请输入拒绝原因')
    return
  }
  try {
    await api.post(`/admin/withdrawals/${currentWithdraw.value.id}/process`, {
      action: 'reject',
      reject_reason: rejectForm.value.reason
    })
    ElMessage.success('已拒绝')
    rejectDialogVisible.value = false
    fetchWithdrawals()
    fetchStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

// 显示完整账号
const showAccount = (row) => {
  ElMessageBox.alert(
    `账户名：${row.account_name}\n账号：${row.account_number}${row.bank_name ? '\n银行：' + row.bank_name : ''}`,
    '账户信息'
  )
}

// 辅助函数
const getTypeName = (type) => {
  const names = { alipay: '支付宝', wechat: '微信', bank: '银行卡' }
  return names[type] || type
}

const getStatusName = (status) => {
  const names = { pending: '待审核', processing: '处理中', success: '已完成', failed: '失败', rejected: '已拒绝' }
  return names[status] || status
}

const getStatusType = (status) => {
  const types = { pending: 'warning', processing: '', success: 'success', failed: 'danger', rejected: 'info' }
  return types[status] || 'info'
}

const maskAccount = (account) => {
  if (!account) return ''
  if (account.length <= 8) return account.replace(/.(?=.{4})/g, '*')
  return account.slice(0, 4) + '****' + account.slice(-4)
}

const formatTime = (time) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

// 选择变化
const handleSelectionChange = (selection) => {
  selectedWithdrawals.value = selection
}

// 批量通过
const batchApprove = async () => {
  const pendingItems = selectedWithdrawals.value.filter(w => w.status === 'pending')
  if (pendingItems.length === 0) {
    ElMessage.warning('请选择待审核的提现')
    return
  }
  
  const totalAmount = pendingItems.reduce((sum, w) => sum + w.amount, 0)
  
  try {
    await ElMessageBox.confirm(
      `确定批量通过 ${pendingItems.length} 笔提现？\n总金额：¥${totalAmount.toFixed(2)}`,
      '确认批量通过',
      { type: 'warning' }
    )
    
    for (const item of pendingItems) {
      await api.post(`/admin/withdrawals/${item.id}/process`, { action: 'approve' })
    }
    ElMessage.success(`成功通过 ${pendingItems.length} 笔提现`)
    fetchWithdrawals()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

// 批量拒绝
const submitBatchReject = async () => {
  const pendingItems = selectedWithdrawals.value.filter(w => w.status === 'pending')
  if (!batchRejectReason.value) {
    ElMessage.warning('请输入拒绝原因')
    return
  }
  
  try {
    for (const item of pendingItems) {
      await api.post(`/admin/withdrawals/${item.id}/process`, {
        action: 'reject',
        reject_reason: batchRejectReason.value
      })
    }
    ElMessage.success(`成功拒绝 ${pendingItems.length} 笔提现`)
    batchRejectDialog.value = false
    batchRejectReason.value = ''
    fetchWithdrawals()
    fetchStats()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 导出数据
const exportWithdrawals = () => {
  const data = withdrawals.value.map(w => ({
    用户名: w.username,
    提现金额: w.amount.toFixed(2),
    手续费: w.fee.toFixed(2),
    实际到账: w.actual_amount.toFixed(2),
    提现方式: getTypeName(w.withdraw_type),
    账户名: w.account_name,
    账号: w.account_number,
    状态: getStatusName(w.status),
    申请时间: formatTime(w.created_at),
    处理时间: w.processed_at ? formatTime(w.processed_at) : ''
  }))
  
  const headers = Object.keys(data[0] || {}).join(',')
  const rows = data.map(row => Object.values(row).join(','))
  const csv = [headers, ...rows].join('\n')
  
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `提现记录_${dayjs().format('YYYYMMDD')}.csv`
  a.click()
  URL.revokeObjectURL(url)
  
  ElMessage.success('导出成功')
}

onMounted(() => {
  fetchStats()
  fetchWithdrawals()
})
</script>

<style lang="scss" scoped>
.withdrawals-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  h2 {
    margin: 0;
  }
  
  .stats-cards {
    display: flex;
    gap: 20px;
  }
  
  .stat-card {
    background: #f5f5f5;
    padding: 12px 24px;
    border-radius: 8px;
    text-align: center;
    
    .stat-value {
      display: block;
      font-size: 24px;
      font-weight: 700;
      color: #67c23a;
    }
    
    .stat-label {
      font-size: 12px;
      color: #999;
    }
    
    &.pending .stat-value {
      color: #e6a23c;
    }
  }
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  align-items: center;
  
  .filter-actions {
    margin-left: auto;
    display: flex;
    gap: 8px;
  }
}

.amount {
  font-weight: 600;
  color: #f56c6c;
}

.actual-amount {
  font-weight: 600;
  color: #67c23a;
}

.account-number {
  font-family: monospace;
  font-size: 12px;
  color: #666;
}

.processed-time {
  font-size: 12px;
  color: #999;
}

.el-pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>
