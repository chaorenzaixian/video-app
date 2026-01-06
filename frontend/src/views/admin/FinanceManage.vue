<template>
  <div class="finance-manage">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon recharge">
              <el-icon><Money /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.totalRecharge?.toLocaleString() || 0 }}</div>
              <div class="stat-label">总充值金币</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon consume">
              <el-icon><ShoppingCart /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.totalConsume?.toLocaleString() || 0 }}</div>
              <div class="stat-label">总消费金币</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon orders">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.orderCount?.toLocaleString() || 0 }}</div>
              <div class="stat-label">充值订单数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon users">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.userCount?.toLocaleString() || 0 }}</div>
              <div class="stat-label">有余额用户</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 标签页 -->
    <el-card class="main-card">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- 金币流水 -->
        <el-tab-pane label="金币流水" name="transactions">
          <div class="filter-bar">
            <el-select v-model="transFilter.type" placeholder="交易类型" clearable style="width: 140px">
              <el-option label="充值" value="recharge" />
              <el-option label="消费" value="consume" />
              <el-option label="退款" value="refund" />
              <el-option label="系统调整" value="adjust" />
              <el-option label="奖励" value="reward" />
            </el-select>
            <el-input v-model="transFilter.userId" placeholder="用户ID" clearable style="width: 140px" />
            <el-date-picker
              v-model="transFilter.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              style="width: 240px"
            />
            <el-button type="primary" @click="fetchTransactions">查询</el-button>
            <el-button @click="exportTransactions">导出</el-button>
          </div>

          <el-table :data="transactions" v-loading="loading.transactions" stripe>
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="user_id" label="用户ID" width="100" />
            <el-table-column prop="username" label="用户名" width="120" />
            <el-table-column prop="transaction_type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag :type="getTransTypeTag(row.transaction_type)">
                  {{ getTransTypeText(row.transaction_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="amount" label="金额" width="100">
              <template #default="{ row }">
                <span :class="row.amount > 0 ? 'text-success' : 'text-danger'">
                  {{ row.amount > 0 ? '+' : '' }}{{ row.amount }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="balance_after" label="余额" width="100" />
            <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
            <el-table-column prop="created_at" label="时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            class="pagination"
            v-model:current-page="transPagination.page"
            v-model:page-size="transPagination.pageSize"
            :total="transPagination.total"
            :page-sizes="[20, 50, 100]"
            layout="total, sizes, prev, pager, next"
            @size-change="fetchTransactions"
            @current-change="fetchTransactions"
          />
        </el-tab-pane>

        <!-- 充值订单 -->
        <el-tab-pane label="充值订单" name="orders">
          <div class="filter-bar">
            <el-select v-model="orderFilter.status" placeholder="订单状态" clearable style="width: 120px">
              <el-option label="待支付" value="pending" />
              <el-option label="已完成" value="completed" />
              <el-option label="已取消" value="cancelled" />
              <el-option label="已过期" value="expired" />
            </el-select>
            <el-input v-model="orderFilter.orderId" placeholder="订单号" clearable style="width: 180px" />
            <el-input v-model="orderFilter.userId" placeholder="用户ID" clearable style="width: 120px" />
            <el-date-picker
              v-model="orderFilter.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              style="width: 240px"
            />
            <el-button type="primary" @click="fetchOrders">查询</el-button>
          </div>

          <el-table :data="orders" v-loading="loading.orders" stripe>
            <el-table-column prop="order_id" label="订单号" width="200" />
            <el-table-column prop="user_id" label="用户ID" width="100" />
            <el-table-column prop="package_name" label="套餐名称" width="120" />
            <el-table-column prop="coins" label="金币数" width="100" />
            <el-table-column prop="amount" label="金额(元)" width="100">
              <template #default="{ row }">
                ¥{{ row.amount }}
              </template>
            </el-table-column>
            <el-table-column prop="payment_method" label="支付方式" width="100" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getOrderStatusTag(row.status)">
                  {{ getOrderStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="paid_at" label="支付时间" width="180">
              <template #default="{ row }">
                {{ row.paid_at ? formatDate(row.paid_at) : '-' }}
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            class="pagination"
            v-model:current-page="orderPagination.page"
            v-model:page-size="orderPagination.pageSize"
            :total="orderPagination.total"
            :page-sizes="[20, 50, 100]"
            layout="total, sizes, prev, pager, next"
            @size-change="fetchOrders"
            @current-change="fetchOrders"
          />
        </el-tab-pane>

        <!-- 用户余额 -->
        <el-tab-pane label="用户余额" name="balances">
          <div class="filter-bar">
            <el-input v-model="balanceFilter.userId" placeholder="用户ID" clearable style="width: 120px" />
            <el-input v-model="balanceFilter.username" placeholder="用户名" clearable style="width: 140px" />
            <el-select v-model="balanceFilter.sortBy" placeholder="排序" style="width: 120px">
              <el-option label="余额降序" value="balance_desc" />
              <el-option label="余额升序" value="balance_asc" />
              <el-option label="总充值" value="total_recharge" />
            </el-select>
            <el-button type="primary" @click="fetchBalances">查询</el-button>
            <el-button type="warning" @click="showAdjustDialog">调整余额</el-button>
          </div>

          <el-table :data="balances" v-loading="loading.balances" stripe>
            <el-table-column prop="user_id" label="用户ID" width="100" />
            <el-table-column prop="username" label="用户名" width="140" />
            <el-table-column prop="balance" label="当前余额" width="120">
              <template #default="{ row }">
                <span class="coin-value">{{ row.balance?.toLocaleString() }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="total_recharge" label="累计充值" width="120" />
            <el-table-column prop="total_consume" label="累计消费" width="120" />
            <el-table-column prop="updated_at" label="最后更新" width="180">
              <template #default="{ row }">
                {{ formatDate(row.updated_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="viewUserTransactions(row.user_id)">
                  查看流水
                </el-button>
                <el-button size="small" type="warning" @click="showAdjustDialog(row)">
                  调整
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            class="pagination"
            v-model:current-page="balancePagination.page"
            v-model:page-size="balancePagination.pageSize"
            :total="balancePagination.total"
            :page-sizes="[20, 50, 100]"
            layout="total, sizes, prev, pager, next"
            @size-change="fetchBalances"
            @current-change="fetchBalances"
          />
        </el-tab-pane>

        <!-- 视频购买记录 -->
        <el-tab-pane label="视频购买" name="purchases">
          <div class="filter-bar">
            <el-input v-model="purchaseFilter.userId" placeholder="用户ID" clearable style="width: 120px" />
            <el-input v-model="purchaseFilter.videoId" placeholder="视频ID" clearable style="width: 120px" />
            <el-date-picker
              v-model="purchaseFilter.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              style="width: 240px"
            />
            <el-button type="primary" @click="fetchPurchases">查询</el-button>
          </div>

          <el-table :data="purchases" v-loading="loading.purchases" stripe>
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="user_id" label="用户ID" width="100" />
            <el-table-column prop="video_id" label="视频ID" width="100" />
            <el-table-column prop="video_title" label="视频标题" min-width="200" show-overflow-tooltip />
            <el-table-column prop="coins_paid" label="支付金币" width="100" />
            <el-table-column prop="created_at" label="购买时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            class="pagination"
            v-model:current-page="purchasePagination.page"
            v-model:page-size="purchasePagination.pageSize"
            :total="purchasePagination.total"
            :page-sizes="[20, 50, 100]"
            layout="total, sizes, prev, pager, next"
            @size-change="fetchPurchases"
            @current-change="fetchPurchases"
          />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 调整余额对话框 -->
    <el-dialog v-model="adjustDialog.visible" title="调整用户余额" width="500px">
      <el-form :model="adjustForm" label-width="100px">
        <el-form-item label="用户ID" required>
          <el-input v-model="adjustForm.userId" :disabled="!!adjustForm.username" />
        </el-form-item>
        <el-form-item label="用户名" v-if="adjustForm.username">
          <el-input v-model="adjustForm.username" disabled />
        </el-form-item>
        <el-form-item label="当前余额" v-if="adjustForm.currentBalance !== undefined">
          <el-input :value="adjustForm.currentBalance" disabled />
        </el-form-item>
        <el-form-item label="调整类型" required>
          <el-radio-group v-model="adjustForm.type">
            <el-radio value="add">增加</el-radio>
            <el-radio value="deduct">扣除</el-radio>
            <el-radio value="set">设置为</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="金币数量" required>
          <el-input-number v-model="adjustForm.amount" :min="0" :max="9999999" />
        </el-form-item>
        <el-form-item label="调整原因" required>
          <el-input v-model="adjustForm.reason" type="textarea" rows="3" placeholder="请输入调整原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="adjustDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitAdjust" :loading="adjustDialog.loading">确认调整</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Money, ShoppingCart, Document, User } from '@element-plus/icons-vue'
import api from '@/utils/api'

// 统计数据
const stats = ref({})

// 标签页
const activeTab = ref('transactions')

// 加载状态
const loading = reactive({
  transactions: false,
  orders: false,
  balances: false,
  purchases: false
})

// 金币流水
const transactions = ref([])
const transFilter = reactive({
  type: '',
  userId: '',
  dateRange: null
})
const transPagination = reactive({ page: 1, pageSize: 20, total: 0 })

// 充值订单
const orders = ref([])
const orderFilter = reactive({
  status: '',
  orderId: '',
  userId: '',
  dateRange: null
})
const orderPagination = reactive({ page: 1, pageSize: 20, total: 0 })

// 用户余额
const balances = ref([])
const balanceFilter = reactive({
  userId: '',
  username: '',
  sortBy: 'balance_desc'
})
const balancePagination = reactive({ page: 1, pageSize: 20, total: 0 })

// 视频购买
const purchases = ref([])
const purchaseFilter = reactive({
  userId: '',
  videoId: '',
  dateRange: null
})
const purchasePagination = reactive({ page: 1, pageSize: 20, total: 0 })

// 调整余额对话框
const adjustDialog = reactive({
  visible: false,
  loading: false
})
const adjustForm = reactive({
  userId: '',
  username: '',
  currentBalance: undefined,
  type: 'add',
  amount: 0,
  reason: ''
})

// 获取统计数据
const fetchStats = async () => {
  try {
    const res = await api.get('/admin/finance/coin-transactions/stats')
    stats.value = res.data || res
  } catch (error) {
    console.error('获取统计失败:', error)
  }
}

// 获取金币流水
const fetchTransactions = async () => {
  loading.transactions = true
  try {
    const params = {
      page: transPagination.page,
      page_size: transPagination.pageSize,
      transaction_type: transFilter.type || undefined,
      user_id: transFilter.userId || undefined
    }
    if (transFilter.dateRange) {
      params.start_date = transFilter.dateRange[0]
      params.end_date = transFilter.dateRange[1]
    }
    const res = await api.get('/admin/finance/coin-transactions', { params })
    transactions.value = res.data?.items || res.items || []
    transPagination.total = res.data?.total || res.total || 0
  } catch (error) {
    ElMessage.error('获取金币流水失败')
  } finally {
    loading.transactions = false
  }
}

// 获取充值订单
const fetchOrders = async () => {
  loading.orders = true
  try {
    const params = {
      page: orderPagination.page,
      page_size: orderPagination.pageSize,
      status: orderFilter.status || undefined,
      order_id: orderFilter.orderId || undefined,
      user_id: orderFilter.userId || undefined
    }
    if (orderFilter.dateRange) {
      params.start_date = orderFilter.dateRange[0]
      params.end_date = orderFilter.dateRange[1]
    }
    const res = await api.get('/admin/finance/recharge-orders', { params })
    orders.value = res.data?.items || res.items || []
    orderPagination.total = res.data?.total || res.total || 0
  } catch (error) {
    ElMessage.error('获取充值订单失败')
  } finally {
    loading.orders = false
  }
}

// 获取用户余额
const fetchBalances = async () => {
  loading.balances = true
  try {
    const params = {
      page: balancePagination.page,
      page_size: balancePagination.pageSize,
      user_id: balanceFilter.userId || undefined,
      username: balanceFilter.username || undefined,
      sort_by: balanceFilter.sortBy
    }
    const res = await api.get('/admin/finance/user-coins', { params })
    balances.value = res.data?.items || res.items || []
    balancePagination.total = res.data?.total || res.total || 0
  } catch (error) {
    ElMessage.error('获取用户余额失败')
  } finally {
    loading.balances = false
  }
}

// 获取视频购买记录
const fetchPurchases = async () => {
  loading.purchases = true
  try {
    const params = {
      page: purchasePagination.page,
      page_size: purchasePagination.pageSize,
      user_id: purchaseFilter.userId || undefined,
      video_id: purchaseFilter.videoId || undefined
    }
    if (purchaseFilter.dateRange) {
      params.start_date = purchaseFilter.dateRange[0]
      params.end_date = purchaseFilter.dateRange[1]
    }
    const res = await api.get('/admin/finance/video-purchases', { params })
    purchases.value = res.data?.items || res.items || []
    purchasePagination.total = res.data?.total || res.total || 0
  } catch (error) {
    ElMessage.error('获取视频购买记录失败')
  } finally {
    loading.purchases = false
  }
}

// 标签页切换
const handleTabChange = (tab) => {
  switch (tab) {
    case 'transactions':
      if (!transactions.value.length) fetchTransactions()
      break
    case 'orders':
      if (!orders.value.length) fetchOrders()
      break
    case 'balances':
      if (!balances.value.length) fetchBalances()
      break
    case 'purchases':
      if (!purchases.value.length) fetchPurchases()
      break
  }
}

// 导出流水
const exportTransactions = () => {
  ElMessage.info('导出功能开发中')
}

// 查看用户流水
const viewUserTransactions = (userId) => {
  activeTab.value = 'transactions'
  transFilter.userId = String(userId)
  fetchTransactions()
}

// 显示调整余额对话框
const showAdjustDialog = (user = null) => {
  if (user) {
    adjustForm.userId = String(user.user_id)
    adjustForm.username = user.username
    adjustForm.currentBalance = user.balance
  } else {
    adjustForm.userId = ''
    adjustForm.username = ''
    adjustForm.currentBalance = undefined
  }
  adjustForm.type = 'add'
  adjustForm.amount = 0
  adjustForm.reason = ''
  adjustDialog.visible = true
}

// 提交调整
const submitAdjust = async () => {
  if (!adjustForm.userId) {
    ElMessage.warning('请输入用户ID')
    return
  }
  if (!adjustForm.amount && adjustForm.type !== 'set') {
    ElMessage.warning('请输入金币数量')
    return
  }
  if (!adjustForm.reason.trim()) {
    ElMessage.warning('请输入调整原因')
    return
  }

  await ElMessageBox.confirm(
    `确认${adjustForm.type === 'add' ? '增加' : adjustForm.type === 'deduct' ? '扣除' : '设置为'} ${adjustForm.amount} 金币？`,
    '确认操作'
  )

  adjustDialog.loading = true
  try {
    await api.post('/admin/finance/adjust-coins', {
      user_id: parseInt(adjustForm.userId),
      adjust_type: adjustForm.type,
      amount: adjustForm.amount,
      reason: adjustForm.reason
    })
    ElMessage.success('调整成功')
    adjustDialog.visible = false
    fetchBalances()
    fetchTransactions()
  } catch (error) {
    ElMessage.error('调整失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    adjustDialog.loading = false
  }
}

// 辅助函数
const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

const getTransTypeTag = (type) => {
  const map = { recharge: 'success', consume: 'warning', refund: 'info', adjust: 'danger', reward: '' }
  return map[type] || ''
}

const getTransTypeText = (type) => {
  const map = { recharge: '充值', consume: '消费', refund: '退款', adjust: '调整', reward: '奖励' }
  return map[type] || type
}

const getOrderStatusTag = (status) => {
  const map = { pending: 'warning', completed: 'success', cancelled: 'info', expired: 'danger' }
  return map[status] || ''
}

const getOrderStatusText = (status) => {
  const map = { pending: '待支付', completed: '已完成', cancelled: '已取消', expired: '已过期' }
  return map[status] || status
}

onMounted(() => {
  fetchStats()
  fetchTransactions()
})
</script>

<style lang="scss" scoped>
.finance-manage {
  padding: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  .stat-content {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .stat-icon {
    width: 56px;
    height: 56px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    color: #fff;

    &.recharge { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    &.consume { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    &.orders { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    &.users { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
  }

  .stat-info {
    .stat-value {
      font-size: 24px;
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

.main-card {
  min-height: 600px;
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

.text-success { color: #67c23a; font-weight: 600; }
.text-danger { color: #f56c6c; font-weight: 600; }
.coin-value { color: #e6a23c; font-weight: 600; }
</style>





















