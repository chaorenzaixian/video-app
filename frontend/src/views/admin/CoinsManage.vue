<template>
  <div class="admin-page">
    <div class="page-header">
      <h1>金币管理</h1>
      <p class="page-desc">管理充值套餐、查看订单记录、调整用户金币</p>
    </div>

    <!-- 功能标签页 -->
    <el-tabs v-model="activeTab" class="main-tabs">
      <!-- 充值套餐 -->
      <el-tab-pane label="充值套餐" name="packages">
        <div class="tab-header">
          <el-button type="primary" @click="showPackageDialog()">
            <el-icon><Plus /></el-icon> 添加套餐
          </el-button>
        </div>
        
        <el-table :data="packages" stripe border>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="name" label="套餐名称" width="150" />
          <el-table-column prop="coins" label="金币数" width="100">
            <template #default="{ row }">
              <span class="coins-text">{{ row.coins }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="bonus_coins" label="赠送" width="80">
            <template #default="{ row }">
              <span v-if="row.bonus_coins" class="bonus-text">+{{ row.bonus_coins }}</span>
              <span v-else class="text-gray">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="price" label="价格(元)" width="100">
            <template #default="{ row }">
              ¥{{ row.price }}
            </template>
          </el-table-column>
          <el-table-column prop="tag" label="标签" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.tag" size="small" :type="getTagType(row.tag)">{{ row.tag }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_hot" label="热门" width="80">
            <template #default="{ row }">
              <el-tag v-if="row.is_hot" type="danger" size="small">热门</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_first_charge" label="首充" width="80">
            <template #default="{ row }">
              <el-tag v-if="row.is_first_charge" type="warning" size="small">首充</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                {{ row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="sort_order" label="排序" width="70" />
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="showPackageDialog(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="deletePackage(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 充值订单 -->
      <el-tab-pane label="充值订单" name="orders">
        <div class="tab-header">
          <el-input v-model="orderFilter.keyword" placeholder="订单号/用户名" clearable style="width: 200px" />
          <el-select v-model="orderFilter.status" placeholder="订单状态" clearable style="width: 120px">
            <el-option label="待支付" value="pending" />
            <el-option label="已支付" value="paid" />
            <el-option label="已失败" value="failed" />
          </el-select>
          <el-date-picker v-model="orderFilter.dateRange" type="daterange" start-placeholder="开始日期" end-placeholder="结束日期" style="width: 240px" />
          <el-button type="primary" @click="fetchOrders">查询</el-button>
          <el-button @click="exportOrders">导出</el-button>
        </div>

        <el-table :data="orders" stripe border>
          <el-table-column prop="order_no" label="订单号" width="200" />
          <el-table-column label="用户" width="150">
            <template #default="{ row }">
              <span>{{ row.user?.nickname || row.user?.username }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="coins" label="金币" width="100">
            <template #default="{ row }">
              {{ row.coins }}<span v-if="row.bonus_coins" class="bonus-text">+{{ row.bonus_coins }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="amount" label="金额" width="100">
            <template #default="{ row }">
              <span class="price-text">¥{{ row.amount }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="payment_method" label="支付方式" width="100">
            <template #default="{ row }">
              {{ row.payment_method === 'alipay' ? '支付宝' : row.payment_method === 'wechat' ? '微信' : row.payment_method }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getOrderStatusType(row.status)" size="small">
                {{ getOrderStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="paid_at" label="支付时间" width="160">
            <template #default="{ row }">
              {{ formatTime(row.paid_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="160">
            <template #default="{ row }">
              {{ formatTime(row.created_at) }}
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-model:current-page="orderPagination.page"
          :page-size="orderPagination.pageSize"
          :total="orderPagination.total"
          layout="total, prev, pager, next"
          @current-change="fetchOrders"
          class="pagination"
        />
      </el-tab-pane>

      <!-- 用户金币 -->
      <el-tab-pane label="用户金币" name="users">
        <div class="tab-header">
          <el-input v-model="userFilter.keyword" placeholder="用户名/昵称" clearable style="width: 200px" />
          <el-button type="primary" @click="fetchUserCoins">查询</el-button>
        </div>

        <el-table :data="userCoins" stripe border>
          <el-table-column prop="user_id" label="用户ID" width="80" />
          <el-table-column label="用户" width="150">
            <template #default="{ row }">
              {{ row.nickname || row.username }}
            </template>
          </el-table-column>
          <el-table-column prop="balance" label="当前余额" width="120">
            <template #default="{ row }">
              <span class="coins-text">{{ row.balance }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="total_recharged" label="累计充值" width="120" />
          <el-table-column prop="total_spent" label="累计消费" width="120" />
          <el-table-column prop="total_earned" label="累计赚取" width="120" />
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="showTransactions(row)">明细</el-button>
              <el-button size="small" type="primary" @click="showAdjustDialog(row)">调整</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-model:current-page="userPagination.page"
          :page-size="userPagination.pageSize"
          :total="userPagination.total"
          layout="total, prev, pager, next"
          @current-change="fetchUserCoins"
          class="pagination"
        />
      </el-tab-pane>
    </el-tabs>

    <!-- 套餐编辑弹窗 -->
    <el-dialog v-model="packageDialog.visible" :title="packageDialog.isEdit ? '编辑套餐' : '添加套餐'" width="500px">
      <el-form :model="packageForm" label-width="100px">
        <el-form-item label="套餐名称">
          <el-input v-model="packageForm.name" placeholder="请输入套餐名称" />
        </el-form-item>
        <el-form-item label="金币数量">
          <el-input-number v-model="packageForm.coins" :min="1" />
        </el-form-item>
        <el-form-item label="赠送金币">
          <el-input-number v-model="packageForm.bonus_coins" :min="0" />
        </el-form-item>
        <el-form-item label="价格(元)">
          <el-input-number v-model="packageForm.price" :min="0.01" :precision="2" />
        </el-form-item>
        <el-form-item label="原价(元)">
          <el-input-number v-model="packageForm.original_price" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="packageForm.tag" placeholder="如: 热门、推荐" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="packageForm.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="选项">
          <el-checkbox v-model="packageForm.is_hot">热门推荐</el-checkbox>
          <el-checkbox v-model="packageForm.is_first_charge">首充专享</el-checkbox>
          <el-checkbox v-model="packageForm.is_active">启用</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="packageDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="savePackage">保存</el-button>
      </template>
    </el-dialog>

    <!-- 金币调整弹窗 -->
    <el-dialog v-model="adjustDialog.visible" title="调整用户金币" width="400px">
      <el-form :model="adjustForm" label-width="80px">
        <el-form-item label="用户">
          <span>{{ adjustDialog.user?.nickname || adjustDialog.user?.username }}</span>
        </el-form-item>
        <el-form-item label="当前余额">
          <span class="coins-text">{{ adjustDialog.user?.balance }}</span>
        </el-form-item>
        <el-form-item label="调整类型">
          <el-radio-group v-model="adjustForm.type">
            <el-radio label="add">增加</el-radio>
            <el-radio label="reduce">扣减</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="金币数量">
          <el-input-number v-model="adjustForm.amount" :min="1" />
        </el-form-item>
        <el-form-item label="调整原因">
          <el-input v-model="adjustForm.reason" type="textarea" rows="2" placeholder="请输入调整原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="adjustDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="confirmAdjust">确认调整</el-button>
      </template>
    </el-dialog>

    <!-- 交易明细弹窗 -->
    <el-dialog v-model="transDialog.visible" title="金币交易明细" width="700px">
      <div class="trans-header">
        <span>用户: {{ transDialog.user?.nickname || transDialog.user?.username }}</span>
        <span>当前余额: <b class="coins-text">{{ transDialog.user?.balance }}</b></span>
      </div>
      <el-table :data="transactions" stripe border max-height="400">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="transaction_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTransType(row.transaction_type).type" size="small">
              {{ getTransType(row.transaction_type).text }}
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
        <el-table-column prop="description" label="说明" min-width="150" show-overflow-tooltip />
        <el-table-column prop="created_at" label="时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-model:current-page="transPagination.page"
        :page-size="transPagination.pageSize"
        :total="transPagination.total"
        layout="total, prev, pager, next"
        @current-change="fetchTransactions"
        class="pagination"
        style="margin-top: 16px"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '@/utils/api'

const activeTab = ref('packages')

// 套餐数据
const packages = ref([])
const packageDialog = reactive({ visible: false, isEdit: false })
const packageForm = ref({
  name: '',
  coins: 100,
  bonus_coins: 0,
  price: 10,
  original_price: null,
  tag: '',
  sort_order: 0,
  is_hot: false,
  is_first_charge: false,
  is_active: true
})

// 订单数据
const orders = ref([])
const orderFilter = reactive({ keyword: '', status: '', dateRange: null })
const orderPagination = reactive({ page: 1, pageSize: 20, total: 0 })

// 用户金币
const userCoins = ref([])
const userFilter = reactive({ keyword: '' })
const userPagination = reactive({ page: 1, pageSize: 20, total: 0 })

// 调整金币
const adjustDialog = reactive({ visible: false, user: null })
const adjustForm = ref({ type: 'add', amount: 0, reason: '' })

// 交易明细
const transDialog = reactive({ visible: false, user: null })
const transactions = ref([])
const transPagination = reactive({ page: 1, pageSize: 10, total: 0 })

const getTagType = (tag) => {
  if (tag?.includes('热')) return 'danger'
  if (tag?.includes('推荐')) return 'warning'
  if (tag?.includes('首充')) return 'success'
  return 'info'
}

const getOrderStatusType = (status) => {
  const types = { pending: 'warning', paid: 'success', failed: 'danger' }
  return types[status] || 'info'
}

const getOrderStatusText = (status) => {
  const texts = { pending: '待支付', paid: '已支付', failed: '已失败' }
  return texts[status] || status
}

const formatTime = (time) => {
  if (!time) return '-'
  const d = new Date(time)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

const fetchPackages = async () => {
  try {
    const res = await api.get('/admin/recharge-packages')
    packages.value = res.data || []
  } catch (error) {
    // 使用模拟数据
    packages.value = [
      { id: 1, name: '体验包', coins: 60, bonus_coins: 0, price: 6, tag: '体验', sort_order: 1, is_active: true },
      { id: 2, name: '超值套餐', coins: 300, bonus_coins: 50, price: 30, tag: '热门', is_hot: true, sort_order: 2, is_active: true },
      { id: 3, name: '首充礼包', coins: 100, bonus_coins: 100, price: 6, original_price: 10, tag: '首充2倍', is_first_charge: true, sort_order: 0, is_active: true }
    ]
  }
}

const fetchOrders = async () => {
  try {
    const res = await api.get('/admin/recharge-orders', { params: { page: orderPagination.page } })
    orders.value = res.data?.items || []
    orderPagination.total = res.data?.total || 0
  } catch (error) {
    orders.value = []
  }
}

const fetchUserCoins = async () => {
  try {
    const res = await api.get('/admin/user-coins', { params: { search: userFilter.keyword, page: userPagination.page } })
    userCoins.value = res.data?.items || []
    userPagination.total = res.data?.total || 0
  } catch (error) {
    userCoins.value = []
  }
}

const showPackageDialog = (pkg = null) => {
  packageDialog.isEdit = !!pkg
  if (pkg) {
    packageForm.value = { ...pkg }
  } else {
    packageForm.value = { name: '', coins: 100, bonus_coins: 0, price: 10, original_price: null, tag: '', sort_order: 0, is_hot: false, is_first_charge: false, is_active: true }
  }
  packageDialog.visible = true
}

const savePackage = async () => {
  try {
    if (packageDialog.isEdit) {
      await api.put(`/admin/recharge-packages/${packageForm.value.id}`, packageForm.value)
    } else {
      await api.post('/admin/recharge-packages', packageForm.value)
    }
    ElMessage.success('保存成功')
    packageDialog.visible = false
    await fetchPackages()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const deletePackage = async (pkg) => {
  try {
    await ElMessageBox.confirm('确定删除此套餐?', '提示', { type: 'warning' })
    await api.delete(`/admin/recharge-packages/${pkg.id}`)
    ElMessage.success('删除成功')
    await fetchPackages()
  } catch (e) {}
}

const showAdjustDialog = (user) => {
  adjustDialog.user = user
  adjustForm.value = { type: 'add', amount: 0, reason: '' }
  adjustDialog.visible = true
}

const confirmAdjust = async () => {
  if (!adjustForm.value.amount || adjustForm.value.amount <= 0) {
    ElMessage.warning('请输入调整数量')
    return
  }
  if (!adjustForm.value.reason) {
    ElMessage.warning('请输入调整原因')
    return
  }
  try {
    await api.post(`/admin/user-coins/${adjustDialog.user.user_id}/adjust`, adjustForm.value)
    ElMessage.success('调整成功')
    adjustDialog.visible = false
    await fetchUserCoins()
  } catch (error) {
    ElMessage.error('调整失败')
  }
}

const exportOrders = () => {
  ElMessage.info('导出功能开发中')
}

// 显示交易明细
const showTransactions = async (user) => {
  transDialog.user = user
  transPagination.page = 1
  transDialog.visible = true
  await fetchTransactions()
}

// 获取交易记录
const fetchTransactions = async () => {
  if (!transDialog.user) return
  try {
    const res = await api.get('/admin/coin-transactions', {
      params: {
        user_id: transDialog.user.user_id,
        page: transPagination.page,
        page_size: transPagination.pageSize
      }
    })
    transactions.value = res.data?.items || []
    transPagination.total = res.data?.total || 0
  } catch (error) {
    transactions.value = []
  }
}

// 交易类型映射
const getTransType = (type) => {
  const map = {
    recharge: { text: '充值', type: 'success' },
    purchase: { text: '购买', type: 'danger' },
    admin: { text: '管理调整', type: 'warning' },
    reward: { text: '奖励', type: 'success' },
    refund: { text: '退款', type: 'info' },
    share: { text: '分享奖励', type: 'success' }
  }
  return map[type] || { text: type, type: 'info' }
}

onMounted(() => {
  fetchPackages()
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

.main-tabs {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.tab-header {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.coins-text {
  color: #e6a23c;
  font-weight: 600;
}

.bonus-text {
  color: #67c23a;
  font-size: 12px;
  margin-left: 4px;
}

.price-text {
  color: #f56c6c;
  font-weight: 600;
}

.text-gray {
  color: #c0c4cc;
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

:deep(.el-tabs__item) {
  font-size: 15px;
}
</style>
