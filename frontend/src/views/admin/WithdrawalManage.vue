<template>
  <div class="admin-page">
    <div class="page-header">
      <h1>提现审核</h1>
      <p class="page-desc">审核创作者提现申请、处理打款</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card pending">
        <div class="stat-icon">⏳</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.pending }}</span>
          <span class="stat-label">待处理</span>
        </div>
      </div>
      <div class="stat-card processing">
        <div class="stat-icon">🔄</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.processing }}</span>
          <span class="stat-label">处理中</span>
        </div>
      </div>
      <div class="stat-card success">
        <div class="stat-icon">✅</div>
        <div class="stat-info">
          <span class="stat-value">¥{{ stats.todayCompleted }}</span>
          <span class="stat-label">今日打款</span>
        </div>
      </div>
      <div class="stat-card info">
        <div class="stat-icon">💰</div>
        <div class="stat-info">
          <span class="stat-value">¥{{ stats.monthTotal }}</span>
          <span class="stat-label">本月累计</span>
        </div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-select v-model="filter.status" placeholder="状态" clearable style="width: 120px">
        <el-option label="待处理" value="pending" />
        <el-option label="处理中" value="processing" />
        <el-option label="已完成" value="completed" />
        <el-option label="已拒绝" value="rejected" />
      </el-select>
      <el-select v-model="filter.paymentMethod" placeholder="收款方式" clearable style="width: 120px">
        <el-option label="支付宝" value="alipay" />
        <el-option label="微信" value="wechat" />
        <el-option label="银行卡" value="bank" />
      </el-select>
      <el-input v-model="filter.keyword" placeholder="创作者昵称" clearable style="width: 160px" />
      <el-date-picker v-model="filter.dateRange" type="daterange" start-placeholder="开始" end-placeholder="结束" style="width: 220px" />
      <el-button type="primary" @click="fetchWithdrawals">查询</el-button>
      <el-button @click="resetFilter">重置</el-button>
    </div>

    <!-- 提现列表 -->
    <div class="table-container">
      <el-table :data="withdrawals" stripe border v-loading="loading">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="申请人" width="180">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :size="36" :src="row.user?.avatar" />
              <div class="user-info">
                <span class="user-name">{{ row.user?.nickname }}</span>
                <span class="user-id">创作者ID: {{ row.creator_id }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="提现金额" width="140" align="right">
          <template #default="{ row }">
            <div class="amount-cell">
              <span class="coins">{{ row.coins_amount }} 金币</span>
              <span class="cash">¥{{ row.cash_amount }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="收款方式" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getPaymentType(row.payment_method)" size="small">
              {{ getPaymentText(row.payment_method) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="收款信息" width="200">
          <template #default="{ row }">
            <div class="payment-info">
              <span>{{ row.payment_name }}</span>
              <span class="account">{{ maskAccount(row.payment_account) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="申请时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button type="success" size="small" @click="showApproveDialog(row)">通过</el-button>
              <el-button type="danger" size="small" @click="showRejectDialog(row)">拒绝</el-button>
            </template>
            <template v-else-if="row.status === 'processing'">
              <el-button type="primary" size="small" @click="showCompleteDialog(row)">确认打款</el-button>
            </template>
            <el-button size="small" @click="viewDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        :page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, prev, pager, next, jumper"
        @current-change="fetchWithdrawals"
        class="pagination"
      />
    </div>

    <!-- 通过弹窗 -->
    <el-dialog v-model="approveDialog.visible" title="通过提现申请" width="400px">
      <div class="dialog-content">
        <p>确认通过以下提现申请？</p>
        <el-descriptions :column="1" border size="small" v-if="approveDialog.withdrawal">
          <el-descriptions-item label="申请人">{{ approveDialog.withdrawal.user?.nickname }}</el-descriptions-item>
          <el-descriptions-item label="提现金额">¥{{ approveDialog.withdrawal.cash_amount }}</el-descriptions-item>
          <el-descriptions-item label="收款方式">{{ getPaymentText(approveDialog.withdrawal.payment_method) }}</el-descriptions-item>
          <el-descriptions-item label="收款账号">{{ approveDialog.withdrawal.payment_account }}</el-descriptions-item>
          <el-descriptions-item label="收款人">{{ approveDialog.withdrawal.payment_name }}</el-descriptions-item>
        </el-descriptions>
        <p class="dialog-tip">通过后，提现状态将变为"处理中"，请尽快完成打款。</p>
      </div>
      <template #footer>
        <el-button @click="approveDialog.visible = false">取消</el-button>
        <el-button type="success" @click="handleApprove">确认通过</el-button>
      </template>
    </el-dialog>

    <!-- 拒绝弹窗 -->
    <el-dialog v-model="rejectDialog.visible" title="拒绝提现" width="400px">
      <el-input v-model="rejectDialog.reason" type="textarea" rows="4" placeholder="请输入拒绝原因" />
      <template #footer>
        <el-button @click="rejectDialog.visible = false">取消</el-button>
        <el-button type="danger" @click="handleReject">确认拒绝</el-button>
      </template>
    </el-dialog>

    <!-- 确认打款弹窗 -->
    <el-dialog v-model="completeDialog.visible" title="确认打款" width="400px">
      <div class="dialog-content">
        <p>请确认已完成以下打款：</p>
        <el-descriptions :column="1" border size="small" v-if="completeDialog.withdrawal">
          <el-descriptions-item label="打款金额">¥{{ completeDialog.withdrawal.cash_amount }}</el-descriptions-item>
          <el-descriptions-item label="收款账号">{{ completeDialog.withdrawal.payment_account }}</el-descriptions-item>
          <el-descriptions-item label="收款人">{{ completeDialog.withdrawal.payment_name }}</el-descriptions-item>
        </el-descriptions>
        <el-form style="margin-top: 16px">
          <el-form-item label="交易流水号">
            <el-input v-model="completeDialog.transactionNo" placeholder="请输入打款流水号(选填)" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="completeDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="handleComplete">确认已打款</el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailDialog.visible" title="提现详情" width="500px">
      <el-descriptions :column="1" border v-if="detailDialog.withdrawal">
        <el-descriptions-item label="提现ID">{{ detailDialog.withdrawal.id }}</el-descriptions-item>
        <el-descriptions-item label="创作者">{{ detailDialog.withdrawal.user?.nickname }}</el-descriptions-item>
        <el-descriptions-item label="提现金币">{{ detailDialog.withdrawal.coins_amount }}</el-descriptions-item>
        <el-descriptions-item label="折合现金">¥{{ detailDialog.withdrawal.cash_amount }}</el-descriptions-item>
        <el-descriptions-item label="兑换比例">1金币 = ¥{{ detailDialog.withdrawal.exchange_rate }}</el-descriptions-item>
        <el-descriptions-item label="收款方式">{{ getPaymentText(detailDialog.withdrawal.payment_method) }}</el-descriptions-item>
        <el-descriptions-item label="收款账号">{{ detailDialog.withdrawal.payment_account }}</el-descriptions-item>
        <el-descriptions-item label="收款人">{{ detailDialog.withdrawal.payment_name }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(detailDialog.withdrawal.status)">{{ getStatusText(detailDialog.withdrawal.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="申请时间">{{ formatTime(detailDialog.withdrawal.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="处理时间" v-if="detailDialog.withdrawal.processed_at">{{ formatTime(detailDialog.withdrawal.processed_at) }}</el-descriptions-item>
        <el-descriptions-item label="交易流水" v-if="detailDialog.withdrawal.transaction_no">{{ detailDialog.withdrawal.transaction_no }}</el-descriptions-item>
        <el-descriptions-item label="拒绝原因" v-if="detailDialog.withdrawal.reject_reason">{{ detailDialog.withdrawal.reject_reason }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const loading = ref(false)
const withdrawals = ref([])
const stats = ref({ pending: 0, processing: 0, todayCompleted: 0, monthTotal: 0 })

const filter = reactive({
  status: 'pending',
  paymentMethod: '',
  keyword: '',
  dateRange: null
})

const pagination = reactive({
  page: 1,
  pageSize: 15,
  total: 0
})

const approveDialog = reactive({ visible: false, withdrawal: null })
const rejectDialog = reactive({ visible: false, withdrawal: null, reason: '' })
const completeDialog = reactive({ visible: false, withdrawal: null, transactionNo: '' })
const detailDialog = reactive({ visible: false, withdrawal: null })

const getPaymentType = (method) => {
  const types = { alipay: 'primary', wechat: 'success', bank: 'info' }
  return types[method] || 'info'
}

const getPaymentText = (method) => {
  const texts = { alipay: '支付宝', wechat: '微信', bank: '银行卡' }
  return texts[method] || method
}

const getStatusType = (status) => {
  const types = { pending: 'warning', processing: 'primary', completed: 'success', rejected: 'danger' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { pending: '待处理', processing: '处理中', completed: '已完成', rejected: '已拒绝' }
  return texts[status] || status
}

const formatTime = (time) => {
  if (!time) return '-'
  const d = new Date(time)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

const maskAccount = (account) => {
  if (!account) return '-'
  if (account.length > 8) {
    return account.slice(0, 4) + '****' + account.slice(-4)
  }
  return account
}

const fetchWithdrawals = async () => {
  loading.value = true
  try {
    const res = await api.get('/admin/creator-withdrawals', {
      params: {
        status: filter.status,
        payment_method: filter.paymentMethod,
        page: pagination.page
      }
    })
    withdrawals.value = res.data?.items || []
    pagination.total = res.data?.total || 0
  } catch (error) {
    withdrawals.value = []
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filter.status = 'pending'
  filter.paymentMethod = ''
  filter.keyword = ''
  filter.dateRange = null
  pagination.page = 1
  fetchWithdrawals()
}

const showApproveDialog = (withdrawal) => {
  approveDialog.withdrawal = withdrawal
  approveDialog.visible = true
}

const handleApprove = async () => {
  try {
    await api.post(`/admin/creator-withdrawals/${approveDialog.withdrawal.id}/approve`)
    ElMessage.success('已通过，请尽快完成打款')
    approveDialog.visible = false
    await fetchWithdrawals()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const showRejectDialog = (withdrawal) => {
  rejectDialog.withdrawal = withdrawal
  rejectDialog.reason = ''
  rejectDialog.visible = true
}

const handleReject = async () => {
  if (!rejectDialog.reason) {
    ElMessage.warning('请输入拒绝原因')
    return
  }
  try {
    await api.post(`/admin/creator-withdrawals/${rejectDialog.withdrawal.id}/reject`, {
      reason: rejectDialog.reason
    })
    ElMessage.success('已拒绝')
    rejectDialog.visible = false
    await fetchWithdrawals()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const showCompleteDialog = (withdrawal) => {
  completeDialog.withdrawal = withdrawal
  completeDialog.transactionNo = ''
  completeDialog.visible = true
}

const handleComplete = async () => {
  try {
    await api.post(`/admin/creator-withdrawals/${completeDialog.withdrawal.id}/complete`, {
      transaction_no: completeDialog.transactionNo
    })
    ElMessage.success('打款完成')
    completeDialog.visible = false
    await fetchWithdrawals()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const viewDetail = (withdrawal) => {
  detailDialog.withdrawal = withdrawal
  detailDialog.visible = true
}

onMounted(() => {
  fetchWithdrawals()
})
</script>

<style lang="scss" scoped>
.admin-page {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 20px;
  
  h1 {
    font-size: 24px;
    font-weight: 600;
    color: #303133;
    margin: 0 0 8px;
  }
  
  .page-desc {
    color: #909399;
    font-size: 14px;
    margin: 0;
  }
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  
  .stat-icon {
    font-size: 32px;
    width: 56px;
    height: 56px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .stat-info {
    .stat-value {
      display: block;
      font-size: 24px;
      font-weight: 600;
      color: #303133;
    }
    
    .stat-label {
      font-size: 14px;
      color: #909399;
    }
  }
  
  &.pending .stat-icon { background: #fdf6ec; }
  &.processing .stat-icon { background: #ecf5ff; }
  &.success .stat-icon { background: #f0f9eb; }
  &.info .stat-icon { background: #f4f4f5; }
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
  background: #fff;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.table-container {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  
  .user-info {
    display: flex;
    flex-direction: column;
    
    .user-name {
      font-weight: 500;
      color: #303133;
    }
    
    .user-id {
      font-size: 12px;
      color: #909399;
    }
  }
}

.amount-cell {
  .coins {
    display: block;
    font-size: 12px;
    color: #909399;
  }
  
  .cash {
    font-size: 16px;
    font-weight: 600;
    color: #f56c6c;
  }
}

.payment-info {
  span {
    display: block;
    
    &.account {
      font-size: 12px;
      color: #909399;
    }
  }
}

.dialog-content {
  p {
    margin: 0 0 12px;
    color: #606266;
  }
  
  .dialog-tip {
    margin-top: 12px;
    font-size: 13px;
    color: #909399;
  }
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-table) {
  border-radius: 8px;
  
  th {
    background: #f5f7fa !important;
    font-weight: 600;
  }
}
</style>

