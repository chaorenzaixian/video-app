<template>
  <div class="orders-page">
    <div class="page-header">
      <h2>订单管理</h2>
      <div class="stats-cards">
        <div class="stat-card">
          <span class="stat-value">{{ stats.total_orders }}</span>
          <span class="stat-label">总订单</span>
        </div>
        <div class="stat-card success">
          <span class="stat-value">¥{{ stats.total_amount.toFixed(2) }}</span>
          <span class="stat-label">总金额</span>
        </div>
        <div class="stat-card warning">
          <span class="stat-value">{{ stats.today_orders }}</span>
          <span class="stat-label">今日订单</span>
        </div>
        <div class="stat-card commission">
          <span class="stat-value">¥{{ stats.total_commission.toFixed(2) }}</span>
          <span class="stat-label">产生佣金</span>
        </div>
      </div>
    </div>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>订单列表</span>
          <div class="filter-bar">
            <el-select v-model="filters.status" placeholder="状态" clearable @change="fetchOrders">
              <el-option label="全部" value="" />
              <el-option label="待支付" value="pending" />
              <el-option label="已支付" value="success" />
              <el-option label="已失败" value="failed" />
            </el-select>
            <el-date-picker
              v-model="filters.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              @change="fetchOrders"
            />
            <el-button @click="exportOrders">导出</el-button>
          </div>
        </div>
      </template>

      <el-table :data="orders" v-loading="loading" stripe>
        <el-table-column prop="order_no" label="订单号" width="180" />
        <el-table-column prop="username" label="用户" width="120" />
        <el-table-column prop="order_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ getTypeText(row.order_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="100">
          <template #default="{ row }">
            <span class="amount">¥{{ row.amount.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="邀请人" width="120">
          <template #default="{ row }">
            <span v-if="row.inviter_name" class="inviter">{{ row.inviter_name }}</span>
            <span v-else class="no-inviter">-</span>
          </template>
        </el-table-column>
        <el-table-column label="产生佣金" width="100">
          <template #default="{ row }">
            <span v-if="row.commission_amount" class="commission">
              ¥{{ row.commission_amount.toFixed(2) }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="payment_method" label="支付方式" width="100">
          <template #default="{ row }">
            {{ getPaymentMethod(row.payment_method) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="paid_at" label="支付时间" width="160">
          <template #default="{ row }">
            {{ row.paid_at ? formatTime(row.paid_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="text" size="small" @click="viewDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="fetchOrders"
        style="margin-top: 16px; justify-content: flex-end;"
      />
    </el-card>

    <!-- 订单详情弹窗 -->
    <el-dialog v-model="detailVisible" title="订单详情" width="600px">
      <el-descriptions :column="2" border v-if="currentOrder">
        <el-descriptions-item label="订单号">{{ currentOrder.order_no }}</el-descriptions-item>
        <el-descriptions-item label="用户">{{ currentOrder.username }}</el-descriptions-item>
        <el-descriptions-item label="订单类型">{{ getTypeText(currentOrder.order_type) }}</el-descriptions-item>
        <el-descriptions-item label="金额">¥{{ currentOrder.amount?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentOrder.status)">{{ getStatusText(currentOrder.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="支付方式">{{ getPaymentMethod(currentOrder.payment_method) }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(currentOrder.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="支付时间">{{ currentOrder.paid_at ? formatTime(currentOrder.paid_at) : '-' }}</el-descriptions-item>
        <el-descriptions-item label="邀请人" :span="2">
          <template v-if="currentOrder.inviter_name">
            <span class="inviter-detail">{{ currentOrder.inviter_name }}</span>
            <el-tag size="small" style="margin-left: 8px;">{{ currentOrder.inviter_level_name }}</el-tag>
          </template>
          <span v-else>无</span>
        </el-descriptions-item>
        <el-descriptions-item label="产生佣金" :span="2" v-if="currentOrder.commission_amount">
          <span class="commission-detail">¥{{ currentOrder.commission_amount?.toFixed(2) }}</span>
          <span class="commission-rate">(佣金比例: {{ (currentOrder.commission_rate * 100).toFixed(0) }}%)</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'
import dayjs from 'dayjs'

const loading = ref(false)
const orders = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filters = ref({ status: '', dateRange: null })
const stats = ref({
  total_orders: 0,
  total_amount: 0,
  today_orders: 0,
  total_commission: 0
})

const detailVisible = ref(false)
const currentOrder = ref(null)

// 获取订单列表
const fetchOrders = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
      status: filters.value.status || undefined
    }
    
    if (filters.value.dateRange) {
      params.start_date = dayjs(filters.value.dateRange[0]).format('YYYY-MM-DD')
      params.end_date = dayjs(filters.value.dateRange[1]).format('YYYY-MM-DD')
    }
    
    const res = await api.get('/admin/orders', { params })
    const data = res.data || res
    orders.value = data.items || []
    total.value = data.total || 0
  } catch (error) {
    console.error('获取订单失败:', error)
    // 使用模拟数据
    orders.value = [
      { 
        id: 1,
        order_no: 'VOD202412050001', 
        username: 'user1', 
        order_type: 'vip_monthly', 
        amount: 29, 
        status: 'success', 
        payment_method: 'alipay',
        created_at: '2024-12-05T10:00:00', 
        paid_at: '2024-12-05T10:01:00',
        inviter_name: '推广员A',
        inviter_level_name: '普通代理',
        commission_amount: 4.35,
        commission_rate: 0.15
      },
      { 
        id: 2,
        order_no: 'VOD202412050002', 
        username: 'user2', 
        order_type: 'vip_yearly', 
        amount: 199, 
        status: 'success',
        payment_method: 'wechat', 
        created_at: '2024-12-05T11:00:00', 
        paid_at: '2024-12-05T11:02:00',
        inviter_name: null,
        commission_amount: 0,
        commission_rate: 0
      },
      { 
        id: 3,
        order_no: 'VOD202412050003', 
        username: 'user3', 
        order_type: 'vip_quarterly', 
        amount: 68, 
        status: 'pending',
        payment_method: 'alipay', 
        created_at: '2024-12-05T14:00:00', 
        paid_at: null,
        inviter_name: '超级代理B',
        inviter_level_name: '超级代理',
        commission_amount: 0,
        commission_rate: 0.5
      }
    ]
    total.value = orders.value.length
  } finally {
    loading.value = false
  }
}

// 获取统计数据
const fetchStats = async () => {
  try {
    const res = await api.get('/admin/orders/stats')
    stats.value = res.data || res
  } catch (error) {
    // 模拟数据
    stats.value = {
      total_orders: 156,
      total_amount: 12580.00,
      today_orders: 8,
      total_commission: 1886.50
    }
  }
}

// 查看详情
const viewDetail = (order) => {
  currentOrder.value = order
  detailVisible.value = true
}

// 导出订单
const exportOrders = () => {
  const data = orders.value.map(o => ({
    订单号: o.order_no,
    用户: o.username,
    类型: getTypeText(o.order_type),
    金额: o.amount?.toFixed(2),
    状态: getStatusText(o.status),
    支付方式: getPaymentMethod(o.payment_method),
    邀请人: o.inviter_name || '',
    佣金: o.commission_amount?.toFixed(2) || '0',
    创建时间: formatTime(o.created_at),
    支付时间: o.paid_at ? formatTime(o.paid_at) : ''
  }))
  
  const headers = Object.keys(data[0] || {}).join(',')
  const rows = data.map(row => Object.values(row).join(','))
  const csv = [headers, ...rows].join('\n')
  
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `订单列表_${dayjs().format('YYYYMMDD')}.csv`
  a.click()
  URL.revokeObjectURL(url)
  
  ElMessage.success('导出成功')
}

// 辅助函数
const getTypeText = (t) => ({
  vip_monthly: '包月VIP',
  vip_quarterly: '包季VIP',
  vip_yearly: '包年VIP',
  vip_lifetime: '永久VIP'
}[t] || t)

const getStatusType = (s) => ({
  success: 'success',
  pending: 'warning',
  failed: 'danger',
  cancelled: 'info'
}[s] || 'info')

const getStatusText = (s) => ({
  success: '已支付',
  pending: '待支付',
  failed: '失败',
  cancelled: '已取消'
}[s] || s)

const getPaymentMethod = (m) => ({
  alipay: '支付宝',
  wechat: '微信',
  card: '银行卡'
}[m] || m || '-')

const formatTime = (time) => {
  if (!time) return '-'
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

onMounted(() => {
  fetchOrders()
  fetchStats()
})
</script>

<style lang="scss" scoped>
.orders-page {
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
    gap: 16px;
  }
  
  .stat-card {
    background: #f5f5f5;
    padding: 12px 20px;
    border-radius: 8px;
    text-align: center;
    min-width: 100px;
    
    .stat-value {
      display: block;
      font-size: 20px;
      font-weight: 700;
      color: #409eff;
    }
    
    .stat-label {
      font-size: 12px;
      color: #999;
    }
    
    &.success .stat-value { color: #67c23a; }
    &.warning .stat-value { color: #e6a23c; }
    &.commission .stat-value { color: #f56c6c; }
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  display: flex;
  gap: 12px;
  align-items: center;
}

.amount {
  font-weight: 600;
  color: #67c23a;
}

.inviter {
  color: #409eff;
}

.no-inviter {
  color: #c0c4cc;
}

.commission {
  color: #f56c6c;
  font-weight: 600;
}

.inviter-detail {
  font-weight: 600;
  color: #409eff;
}

.commission-detail {
  font-size: 18px;
  font-weight: 700;
  color: #f56c6c;
}

.commission-rate {
  color: #909399;
  margin-left: 8px;
}
</style>
