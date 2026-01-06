<template>
  <div class="agents-page">
    <div class="page-header">
      <h2>代理管理</h2>
      <div class="stats-cards">
        <div class="stat-card">
          <span class="stat-value">{{ stats.total_agents }}</span>
          <span class="stat-label">总代理数</span>
        </div>
        <div class="stat-card pending">
          <span class="stat-value">{{ stats.pending_agents }}</span>
          <span class="stat-label">待审核</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">¥{{ stats.total_commission.toFixed(2) }}</span>
          <span class="stat-label">总佣金</span>
        </div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-select v-model="filters.status" placeholder="状态筛选" clearable @change="fetchAgents">
        <el-option label="全部" value="" />
        <el-option label="待审核" value="pending" />
        <el-option label="已激活" value="active" />
        <el-option label="已拒绝" value="rejected" />
        <el-option label="已冻结" value="frozen" />
      </el-select>
      <el-select v-model="filters.level" placeholder="等级筛选" clearable @change="fetchAgents">
        <el-option label="全部等级" value="" />
        <el-option 
          v-for="level in agentLevelOptions.filter(l => l.level > 0)" 
          :key="level.level" 
          :label="level.name" 
          :value="level.level" 
        />
      </el-select>
      <div class="filter-actions">
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon> 添加代理
        </el-button>
        <el-button type="success" :disabled="!selectedAgents.length" @click="batchApprove">
          批量通过 ({{ selectedAgents.length }})
        </el-button>
        <el-button type="danger" :disabled="!selectedAgents.length" @click="batchReject">
          批量拒绝
        </el-button>
        <el-button @click="exportAgents">导出数据</el-button>
      </div>
    </div>

    <!-- 代理列表 -->
    <el-table :data="agents" v-loading="loading" stripe @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="50" />
      <el-table-column prop="username" label="用户名" width="120" />
      <el-table-column prop="agent_level" label="代理等级" width="120">
        <template #default="{ row }">
          <el-tag :type="getLevelType(row.agent_level)">
            {{ getLevelName(row.agent_level) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="agent_status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.agent_status)">
            {{ getStatusName(row.agent_status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="commission_rate" label="佣金比例" width="100">
        <template #default="{ row }">
          {{ (row.commission_rate * 100).toFixed(0) }}%
        </template>
      </el-table-column>
      <el-table-column prop="valid_invites" label="有效邀请" width="100" />
      <el-table-column prop="total_commission" label="累计佣金" width="120">
        <template #default="{ row }">
          ¥{{ row.total_commission.toFixed(2) }}
        </template>
      </el-table-column>
      <el-table-column prop="available_balance" label="可提现" width="120">
        <template #default="{ row }">
          ¥{{ row.available_balance.toFixed(2) }}
        </template>
      </el-table-column>
      <el-table-column prop="agent_applied_at" label="申请时间" width="160">
        <template #default="{ row }">
          {{ row.agent_applied_at ? formatTime(row.agent_applied_at) : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <template v-if="row.agent_status === 'pending'">
            <el-button type="success" size="small" @click="approveAgent(row)">通过</el-button>
            <el-button type="danger" size="small" @click="rejectAgent(row)">拒绝</el-button>
          </template>
          <template v-else>
            <el-button type="primary" size="small" @click="editAgent(row)">编辑</el-button>
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
      @current-change="fetchAgents"
    />

    <!-- 审批弹窗 -->
    <el-dialog v-model="approveDialogVisible" title="审批代理" width="400px">
      <el-form :model="approveForm" label-width="80px">
        <el-form-item label="用户名">
          <span>{{ currentAgent?.username }}</span>
        </el-form-item>
        <el-form-item label="邀请人数">
          <span>{{ currentAgent?.valid_invites }}</span>
        </el-form-item>
        <el-form-item label="代理等级">
          <el-select v-model="approveForm.level">
            <el-option 
              v-for="level in agentLevelOptions.filter(l => l.level > 0)" 
              :key="level.level" 
              :label="`${level.name} (${level.rate}%)`" 
              :value="level.level" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="自定义佣金">
          <el-input-number 
            v-model="approveForm.customRate" 
            :min="1" 
            :max="100" 
            :precision="0"
            style="width: 150px;"
          />
          <span style="margin-left: 8px;">% (留空使用等级默认)</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="approveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitApprove">确认通过</el-button>
      </template>
    </el-dialog>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="editDialogVisible" title="编辑代理" width="450px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="用户名">
          <span>{{ currentAgent?.username }}</span>
        </el-form-item>
        <el-form-item label="代理等级">
          <el-select v-model="editForm.level" @change="onLevelChange">
            <el-option 
              v-for="level in agentLevelOptions" 
              :key="level.level" 
              :label="`${level.name} (${level.rate}%)`" 
              :value="level.level" 
            />
            <el-option label="自定义" :value="-1" />
          </el-select>
        </el-form-item>
        <el-form-item label="自定义佣金" v-if="editForm.level === -1 || editForm.customRate">
          <el-input-number 
            v-model="editForm.customRate" 
            :min="1" 
            :max="100" 
            :precision="0"
            style="width: 150px;"
          />
          <span style="margin-left: 8px;">%</span>
          <div style="color: #909399; font-size: 12px; margin-top: 4px;">
            可设置1%-100%的自定义佣金比例
          </div>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="editForm.status">
            <el-option label="已激活" value="active" />
            <el-option label="已冻结" value="frozen" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 创建代理弹窗 -->
    <el-dialog v-model="showCreateDialog" title="添加代理" width="500px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="选择方式">
          <el-radio-group v-model="createForm.mode">
            <el-radio value="new">新建账号</el-radio>
            <el-radio value="existing">选择现有用户</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 新建账号 -->
        <template v-if="createForm.mode === 'new'">
          <el-form-item label="用户名" required>
            <el-input v-model="createForm.username" placeholder="请输入用户名" />
          </el-form-item>
          <el-form-item label="密码" required>
            <el-input v-model="createForm.password" type="password" placeholder="请输入密码" show-password />
          </el-form-item>
          <el-form-item label="手机号">
            <el-input v-model="createForm.phone" placeholder="可选" />
          </el-form-item>
        </template>

        <!-- 选择现有用户 -->
        <template v-else>
          <el-form-item label="搜索用户" required>
            <el-select
              v-model="createForm.user_id"
              filterable
              remote
              reserve-keyword
              placeholder="输入用户名或手机号搜索"
              :remote-method="searchUsers"
              :loading="searchLoading"
              style="width: 100%"
            >
              <el-option
                v-for="user in searchUserList"
                :key="user.id"
                :label="user.username + (user.phone ? ' (' + user.phone + ')' : '')"
                :value="user.id"
                :disabled="user.is_agent"
              >
                <span>{{ user.username }}</span>
                <span v-if="user.phone" style="color: #999; margin-left: 8px;">{{ user.phone }}</span>
                <el-tag v-if="user.is_agent" size="small" type="warning" style="margin-left: 8px;">已是代理</el-tag>
              </el-option>
            </el-select>
          </el-form-item>
        </template>

        <el-divider content-position="left">代理设置</el-divider>

        <el-form-item label="代理等级">
          <el-select v-model="createForm.agent_level" style="width: 100%">
            <el-option 
              v-for="level in agentLevelOptions.filter(l => l.level > 0)" 
              :key="level.level" 
              :label="`${level.name} (${level.rate}%)`" 
              :value="level.level" 
            />
          </el-select>
        </el-form-item>

        <el-form-item label="自定义佣金">
          <el-input-number v-model="createForm.commission_rate" :min="1" :max="100" :precision="0" />
          <span style="margin-left: 8px;">%（留空使用等级默认比例）</span>
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="createForm.remark" type="textarea" :rows="2" placeholder="可选备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="submitCreate" :loading="createLoading">确认添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '@/utils/api'
import dayjs from 'dayjs'

const loading = ref(false)
const agents = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filters = ref({ status: '', level: '' })
const stats = ref({ total_agents: 0, pending_agents: 0, total_commission: 0 })
const selectedAgents = ref([])

const approveDialogVisible = ref(false)
const editDialogVisible = ref(false)
const currentAgent = ref(null)
const approveForm = ref({ level: 1, customRate: null })
const editForm = ref({ level: 0, status: 'active', customRate: null })

// 代理等级选项（从后端获取）
const agentLevelOptions = ref([
  { level: 0, name: '普通用户', rate: 0 },
  { level: 1, name: '普通级', rate: 40 },
  { level: 2, name: '青铜级', rate: 46 },
  { level: 3, name: '白银级', rate: 52 },
  { level: 4, name: '黄金级', rate: 58 },
  { level: 5, name: '铂金级', rate: 64 },
  { level: 6, name: '钻石级', rate: 70 }
])

// 获取代理等级配置
const fetchAgentLevelConfig = async () => {
  try {
    const res = await api.get('/config/agent-levels')
    const data = res.data || res
    if (data.levels && data.levels.length > 0) {
      agentLevelOptions.value = [
        { level: 0, name: '普通用户', rate: 0 },
        ...data.levels.map(l => ({
          level: l.level,
          name: l.name,
          rate: parseInt(l.rate)
        })).reverse()
      ]
    }
  } catch (error) {
    console.error('获取代理等级配置失败:', error)
  }
}

// 等级变更时
const onLevelChange = (level) => {
  if (level !== -1) {
    const levelConfig = agentLevelOptions.value.find(l => l.level === level)
    if (levelConfig) {
      editForm.value.customRate = null
    }
  } else {
    editForm.value.customRate = 50 // 自定义默认50%
  }
}

// 创建代理
const showCreateDialog = ref(false)
const createLoading = ref(false)
const searchLoading = ref(false)
const searchUserList = ref([])
const createForm = ref({
  mode: 'new',
  username: '',
  password: '',
  phone: '',
  user_id: null,
  agent_level: 2,
  commission_rate: null,
  remark: ''
})

// 获取统计数据
const fetchStats = async () => {
  try {
    const res = await api.get('/admin/promotion/stats')
    stats.value = res.data || res
  } catch (error) {
    console.error('获取统计失败:', error)
  }
}

// 获取代理列表
const fetchAgents = async () => {
  loading.value = true
  try {
    const res = await api.get('/admin/agents', {
      params: {
        page: page.value,
        page_size: pageSize.value,
        status: filters.value.status || undefined,
        level: filters.value.level || undefined
      }
    })
    const data = res.data || res
    agents.value = data.items
    total.value = data.total
  } catch (error) {
    ElMessage.error('获取代理列表失败')
  } finally {
    loading.value = false
  }
}

// 审批代理
const approveAgent = (agent) => {
  currentAgent.value = agent
  approveForm.value = { level: 1, customRate: null }
  approveDialogVisible.value = true
}

const submitApprove = async () => {
  try {
    // 计算佣金比例
    let commissionRate = null
    if (approveForm.value.customRate) {
      commissionRate = approveForm.value.customRate / 100
    }
    
    await api.post(`/admin/agents/${currentAgent.value.user_id}/approve`, null, {
      params: { 
        level: approveForm.value.level,
        commission_rate: commissionRate
      }
    })
    ElMessage.success('审批通过')
    approveDialogVisible.value = false
    fetchAgents()
    fetchStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

// 拒绝代理
const rejectAgent = async (agent) => {
  try {
    await ElMessageBox.confirm('确定拒绝该代理申请?', '提示', { type: 'warning' })
    await api.post(`/admin/agents/${agent.user_id}/reject`)
    ElMessage.success('已拒绝')
    fetchAgents()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

// 编辑代理
const editAgent = (agent) => {
  currentAgent.value = agent
  // 检查是否是自定义佣金比例
  const currentRate = Math.round(agent.commission_rate * 100)
  const levelConfig = agentLevelOptions.value.find(l => l.level === agent.agent_level)
  const isCustomRate = levelConfig && levelConfig.rate !== currentRate
  
  editForm.value = {
    level: isCustomRate ? -1 : agent.agent_level,
    status: agent.agent_status,
    customRate: isCustomRate ? currentRate : null
  }
  editDialogVisible.value = true
}

const submitEdit = async () => {
  try {
    // 计算最终的佣金比例
    let commissionRate
    let actualLevel = editForm.value.level
    
    if (editForm.value.level === -1 && editForm.value.customRate) {
      // 自定义佣金比例
      commissionRate = editForm.value.customRate / 100
      actualLevel = currentAgent.value.agent_level // 保持原等级
    } else {
      // 使用等级对应的比例
      const levelConfig = agentLevelOptions.value.find(l => l.level === editForm.value.level)
      commissionRate = levelConfig ? levelConfig.rate / 100 : 0.4
    }
    
    await api.post(`/admin/agents/${currentAgent.value.user_id}/update`, null, {
      params: {
        level: actualLevel,
        status: editForm.value.status,
        commission_rate: commissionRate
      }
    })
    ElMessage.success('保存成功')
    editDialogVisible.value = false
    fetchAgents()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

// 辅助函数
const getLevelName = (level) => {
  const levelConfig = agentLevelOptions.value.find(l => l.level === level)
  return levelConfig ? levelConfig.name : '普通用户'
}

const getLevelType = (level) => {
  const types = ['info', '', 'success', 'warning', 'danger']
  return types[level] || 'info'
}

const getStatusName = (status) => {
  const names = { inactive: '未激活', pending: '待审核', active: '已激活', frozen: '已冻结', rejected: '已拒绝' }
  return names[status] || status
}

const getStatusType = (status) => {
  const types = { inactive: 'info', pending: 'warning', active: 'success', frozen: 'danger', rejected: 'info' }
  return types[status] || 'info'
}

const formatTime = (time) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

// 选择变化
const handleSelectionChange = (selection) => {
  selectedAgents.value = selection
}

// 批量通过
const batchApprove = async () => {
  const pendingAgents = selectedAgents.value.filter(a => a.agent_status === 'pending')
  if (pendingAgents.length === 0) {
    ElMessage.warning('请选择待审核的代理')
    return
  }
  
  try {
    await ElMessageBox.confirm(`确定批量通过 ${pendingAgents.length} 个代理申请？`, '确认')
    for (const agent of pendingAgents) {
      await api.post(`/admin/agents/${agent.user_id}/approve`, null, {
        params: { level: 2 }
      })
    }
    ElMessage.success(`成功通过 ${pendingAgents.length} 个代理`)
    fetchAgents()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

// 批量拒绝
const batchReject = async () => {
  const pendingAgents = selectedAgents.value.filter(a => a.agent_status === 'pending')
  if (pendingAgents.length === 0) {
    ElMessage.warning('请选择待审核的代理')
    return
  }
  
  try {
    await ElMessageBox.confirm(`确定批量拒绝 ${pendingAgents.length} 个代理申请？`, '确认', { type: 'warning' })
    for (const agent of pendingAgents) {
      await api.post(`/admin/agents/${agent.user_id}/reject`)
    }
    ElMessage.success(`成功拒绝 ${pendingAgents.length} 个代理`)
    fetchAgents()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

// 导出数据
const exportAgents = () => {
  const data = agents.value.map(a => ({
    用户名: a.username,
    等级: getLevelName(a.agent_level),
    状态: getStatusName(a.agent_status),
    佣金比例: (a.commission_rate * 100).toFixed(0) + '%',
    有效邀请: a.valid_invites,
    累计佣金: a.total_commission.toFixed(2),
    可提现: a.available_balance.toFixed(2),
    申请时间: a.agent_applied_at ? formatTime(a.agent_applied_at) : ''
  }))
  
  // 转换为CSV
  const headers = Object.keys(data[0] || {}).join(',')
  const rows = data.map(row => Object.values(row).join(','))
  const csv = [headers, ...rows].join('\n')
  
  // 下载
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `代理列表_${dayjs().format('YYYYMMDD')}.csv`
  a.click()
  URL.revokeObjectURL(url)
  
  ElMessage.success('导出成功')
}

// 搜索用户
const searchUsers = async (keyword) => {
  if (!keyword || keyword.length < 1) {
    searchUserList.value = []
    return
  }
  
  searchLoading.value = true
  try {
    const res = await api.get('/admin/agents/search-users', { params: { keyword } })
    searchUserList.value = res.data
  } catch (error) {
    console.error('搜索用户失败:', error)
  } finally {
    searchLoading.value = false
  }
}

// 提交创建代理
const submitCreate = async () => {
  // 验证
  if (createForm.value.mode === 'new') {
    if (!createForm.value.username || !createForm.value.password) {
      ElMessage.warning('请填写用户名和密码')
      return
    }
  } else {
    if (!createForm.value.user_id) {
      ElMessage.warning('请选择一个用户')
      return
    }
  }
  
  createLoading.value = true
  try {
    const payload = {
      agent_level: createForm.value.agent_level,
      commission_rate: createForm.value.commission_rate,
      remark: createForm.value.remark
    }
    
    if (createForm.value.mode === 'new') {
      payload.username = createForm.value.username
      payload.password = createForm.value.password
      payload.phone = createForm.value.phone || null
    } else {
      payload.user_id = createForm.value.user_id
    }
    
    await api.post('/admin/agents/create', payload)
    ElMessage.success('代理创建成功')
    showCreateDialog.value = false
    
    // 重置表单
    createForm.value = {
      mode: 'new',
      username: '',
      password: '',
      phone: '',
      user_id: null,
      agent_level: 2,
      commission_rate: null,
      remark: ''
    }
    searchUserList.value = []
    
    // 刷新列表
    fetchAgents()
    fetchStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '创建失败')
  } finally {
    createLoading.value = false
  }
}

onMounted(() => {
  fetchStats()
  fetchAgents()
  fetchAgentLevelConfig()
})
</script>

<style lang="scss" scoped>
.agents-page {
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
      color: #409eff;
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
  flex-wrap: wrap;
  
  .filter-actions {
    margin-left: auto;
    display: flex;
    gap: 8px;
  }
}

.el-pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>
