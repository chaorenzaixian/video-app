<template>
  <div class="promotion-dashboard">
    <h2>推广数据中心</h2>
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <div class="stat-card blue">
          <div class="stat-icon">👥</div>
          <div class="stat-info">
            <span class="stat-value">{{ stats.total_invites }}</span>
            <span class="stat-label">总邀请数</span>
          </div>
          <div class="stat-trend">
            <span class="today">今日 +{{ stats.today_invites || 0 }}</span>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card green">
          <div class="stat-icon">✅</div>
          <div class="stat-info">
            <span class="stat-value">{{ stats.valid_invites }}</span>
            <span class="stat-label">有效邀请</span>
          </div>
          <div class="stat-trend">
            <span>转化率 {{ stats.total_invites ? ((stats.valid_invites / stats.total_invites) * 100).toFixed(1) : 0 }}%</span>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card purple">
          <div class="stat-icon">💎</div>
          <div class="stat-info">
            <span class="stat-value">{{ stats.total_agents }}</span>
            <span class="stat-label">代理总数</span>
          </div>
          <div class="stat-trend">
            <span class="pending">待审核 {{ stats.pending_agents }}</span>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card gold">
          <div class="stat-icon">💰</div>
          <div class="stat-info">
            <span class="stat-value">¥{{ stats.total_commission?.toFixed(2) || '0.00' }}</span>
            <span class="stat-label">累计佣金</span>
          </div>
          <div class="stat-trend">
            <span>已提现 ¥{{ stats.total_withdrawn?.toFixed(2) || '0.00' }}</span>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 第二排统计 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>📈 邀请趋势（近7天）</span>
          </template>
          <div class="trend-chart">
            <div v-for="(day, index) in trendData" :key="index" class="trend-bar">
              <div class="bar" :style="{ height: day.height + '%' }"></div>
              <span class="day-label">{{ day.label }}</span>
              <span class="day-value">{{ day.value }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>🏆 代理排行榜</span>
          </template>
          <div class="ranking-list">
            <div v-for="(agent, index) in topAgents" :key="agent.id" class="ranking-item">
              <span class="rank" :class="'rank-' + (index + 1)">{{ index + 1 }}</span>
              <span class="name">{{ agent.username }}</span>
              <span class="amount">¥{{ agent.total_commission?.toFixed(2) }}</span>
            </div>
            <div v-if="topAgents.length === 0" class="empty-ranking">暂无数据</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>⚠️ 待处理事项</span>
          </template>
          <div class="pending-list">
            <div class="pending-item" @click="$router.push('/agents')">
              <span class="pending-icon">👤</span>
              <span class="pending-text">代理审核</span>
              <el-badge :value="stats.pending_agents" :hidden="!stats.pending_agents" />
            </div>
            <div class="pending-item" @click="$router.push('/withdrawals')">
              <span class="pending-icon">💸</span>
              <span class="pending-text">提现审核</span>
              <el-badge :value="stats.pending_withdrawals" :hidden="!stats.pending_withdrawals" />
            </div>
            <div class="pending-item" @click="showFraudDialog = true">
              <span class="pending-icon">🛡️</span>
              <span class="pending-text">异常检测</span>
              <el-badge :value="fraudStats.total" :hidden="!fraudStats.total" type="danger" />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <el-card class="quick-actions">
      <template #header>
        <span>⚡ 快捷操作</span>
      </template>
      <div class="action-buttons">
        <el-button type="primary" @click="$router.push('/agents')">
          <el-icon><UserFilled /></el-icon>
          代理管理
        </el-button>
        <el-button type="success" @click="$router.push('/withdrawals')">
          <el-icon><Wallet /></el-icon>
          提现管理
        </el-button>
        <el-button type="warning" @click="showConfigDialog = true">
          <el-icon><Setting /></el-icon>
          规则配置
        </el-button>
        <el-button type="danger" @click="showFraudDialog = true">
          <el-icon><Warning /></el-icon>
          风控中心
        </el-button>
        <el-button @click="showMilestoneDialog = true">
          <el-icon><Trophy /></el-icon>
          里程碑配置
        </el-button>
        <el-button @click="exportData">
          <el-icon><Download /></el-icon>
          导出数据
        </el-button>
      </div>
    </el-card>

    <!-- 规则配置弹窗 -->
    <el-dialog v-model="showConfigDialog" title="推广规则配置" width="900px">
      <el-form :model="configForm" label-width="100px" v-loading="configLoading">
        <el-row :gutter="24">
          <el-col :span="12">
            <el-divider content-position="left">邀请奖励</el-divider>
            <el-form-item label="注册奖励">
              <el-input-number v-model="configForm.register_reward_days" :min="0" :max="30" />
              <span style="margin-left: 8px;">天</span>
            </el-form-item>
            <el-form-item label="充值奖励">
              <el-input-number v-model="configForm.recharge_reward_days" :min="0" :max="30" />
              <span style="margin-left: 8px;">天</span>
            </el-form-item>
            
            <el-divider content-position="left">提现规则</el-divider>
            <el-form-item label="最低提现">
              <el-input-number v-model="configForm.min_withdraw" :min="10" :max="1000" :step="10" />
              <span style="margin-left: 8px;">元</span>
            </el-form-item>
            <el-form-item label="最高提现">
              <el-input-number v-model="configForm.max_withdraw" :min="100" :max="100000" :step="100" />
              <span style="margin-left: 8px;">元</span>
            </el-form-item>
            <el-form-item label="手续费">
              <el-input-number v-model="configForm.withdraw_fee" :min="0" :max="50" />
              <span style="margin-left: 8px;">%</span>
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-divider content-position="left">代理等级设置</el-divider>
            <div class="level-config-list">
              <div v-for="level in agentLevels" :key="level.level" class="level-config-item">
                <div class="level-header">
                  <span class="level-name">{{ level.name }}</span>
                  <span class="level-rate">
                    <el-input-number 
                      v-model="level.rate" 
                      :min="1" 
                      :max="100" 
                      size="small"
                      style="width: 80px;"
                    />%
                  </span>
                </div>
                <el-input 
                  v-model="level.condition" 
                  placeholder="升级条件说明"
                  size="small"
                />
                <div class="level-conditions">
                  <el-input-number 
                    v-model="level.min_users" 
                    :min="0" 
                    :max="9999"
                    controls-position="right"
                    size="small"
                    style="width: 110px;"
                  />
                  <span>人充值 +</span>
                  <el-input-number 
                    v-model="level.min_sub_agents" 
                    :min="0" 
                    :max="99"
                    controls-position="right"
                    size="small"
                    style="width: 100px; margin-left: 4px;"
                  />
                  <span>个直属代理</span>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="showConfigDialog = false">取消</el-button>
        <el-button type="primary" @click="saveConfig" :loading="configSaving">保存配置</el-button>
      </template>
    </el-dialog>

    <!-- 风控中心弹窗 -->
    <el-dialog v-model="showFraudDialog" title="🛡️ 风控中心" width="800px">
      <el-tabs>
        <el-tab-pane label="异常检测">
          <div class="fraud-stats">
            <div class="fraud-stat-item">
              <span class="fraud-icon">🌐</span>
              <span class="fraud-label">同IP多次注册</span>
              <span class="fraud-value">{{ fraudStats.same_ip || 0 }} 条</span>
              <el-button size="small" type="danger" @click="handleFraud('ip')">处理</el-button>
            </div>
            <div class="fraud-stat-item">
              <span class="fraud-icon">📱</span>
              <span class="fraud-label">同设备多账号</span>
              <span class="fraud-value">{{ fraudStats.same_device || 0 }} 条</span>
              <el-button size="small" type="danger" @click="handleFraud('device')">处理</el-button>
            </div>
            <div class="fraud-stat-item">
              <span class="fraud-icon">🤖</span>
              <span class="fraud-label">可疑用户名</span>
              <span class="fraud-value">{{ fraudStats.suspicious_name || 0 }} 条</span>
              <el-button size="small" type="danger" @click="handleFraud('name')">处理</el-button>
            </div>
          </div>
        </el-tab-pane>
        <el-tab-pane label="黑名单管理">
          <el-table :data="blacklist" max-height="400">
            <el-table-column prop="type" label="类型" width="100">
              <template #default="{ row }">
                {{ row.type === 'ip' ? 'IP' : row.type === 'device' ? '设备' : '用户' }}
              </template>
            </el-table-column>
            <el-table-column prop="value" label="值" />
            <el-table-column prop="reason" label="原因" />
            <el-table-column prop="created_at" label="添加时间" width="160" />
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button size="small" type="danger" @click="removeFromBlacklist(row)">移除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="add-blacklist">
            <el-select v-model="newBlacklist.type" placeholder="类型" style="width: 100px">
              <el-option label="IP" value="ip" />
              <el-option label="设备" value="device" />
              <el-option label="用户" value="user" />
            </el-select>
            <el-input v-model="newBlacklist.value" placeholder="值" style="width: 200px" />
            <el-input v-model="newBlacklist.reason" placeholder="原因" style="width: 150px" />
            <el-button type="primary" @click="addToBlacklist">添加</el-button>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>

    <!-- 里程碑配置弹窗 -->
    <el-dialog v-model="showMilestoneDialog" title="🏆 里程碑配置" width="700px">
      <el-table :data="milestones" border>
        <el-table-column prop="invite_count" label="邀请人数" width="100" />
        <el-table-column prop="reward_type" label="奖励类型" width="120">
          <template #default="{ row }">
            {{ row.reward_type === 'vip_days' ? 'VIP天数' : '现金' }}
          </template>
        </el-table-column>
        <el-table-column prop="reward_value" label="奖励值" width="100" />
        <el-table-column prop="reward_desc" label="描述" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="deleteMilestone(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="add-milestone">
        <el-input-number v-model="newMilestone.invite_count" placeholder="人数" :min="1" style="width: 100px" />
        <el-select v-model="newMilestone.reward_type" placeholder="类型" style="width: 120px">
          <el-option label="VIP天数" value="vip_days" />
          <el-option label="现金" value="cash" />
        </el-select>
        <el-input-number v-model="newMilestone.reward_value" placeholder="数值" :min="1" style="width: 100px" />
        <el-input v-model="newMilestone.reward_desc" placeholder="描述" style="width: 180px" />
        <el-button type="primary" @click="addMilestone">添加</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { UserFilled, Wallet, Setting, Warning, Trophy, Download } from '@element-plus/icons-vue'
import api from '@/utils/api'
import dayjs from 'dayjs'

// 统计数据
const stats = ref({
  total_invites: 0,
  valid_invites: 0,
  total_agents: 0,
  pending_agents: 0,
  total_commission: 0,
  total_withdrawn: 0,
  pending_withdrawals: 0,
  today_invites: 0
})

// 趋势数据
const trendData = ref([])

// 排行榜
const topAgents = ref([])

// 风控统计
const fraudStats = ref({ total: 0, same_ip: 0, same_device: 0, suspicious_name: 0 })

// 黑名单
const blacklist = ref([])
const newBlacklist = ref({ type: 'ip', value: '', reason: '' })

// 里程碑
const milestones = ref([])
const newMilestone = ref({ invite_count: 10, reward_type: 'vip_days', reward_value: 7, reward_desc: '' })

// 代理等级配置
const agentLevels = ref([])
const configLoading = ref(false)
const configSaving = ref(false)

// 配置
const configForm = ref({
  register_reward_days: 1,
  recharge_reward_days: 7,
  min_withdraw: 250,
  max_withdraw: 10000,
  withdraw_fee: 20
})

// 弹窗控制
const showConfigDialog = ref(false)
const showFraudDialog = ref(false)
const showMilestoneDialog = ref(false)

// 获取统计数据
const fetchStats = async () => {
  try {
    const res = await api.get('/admin/promotion/stats')
    stats.value = res.data || res
  } catch (error) {
    console.error('获取统计失败:', error)
  }
}

// 获取代理排行
const fetchTopAgents = async () => {
  try {
    const res = await api.get('/admin/agents', { params: { page: 1, page_size: 5 } })
    const data = res.data || res
    topAgents.value = (data.items || []).sort((a, b) => b.total_commission - a.total_commission)
  } catch (error) {
    console.error('获取排行失败:', error)
  }
}

// 获取里程碑配置
const fetchMilestones = async () => {
  try {
    const res = await api.get('/admin/promotion/milestones')
    milestones.value = res.data || res
  } catch (error) {
    console.error('获取里程碑失败:', error)
  }
}

// 生成趋势数据
const generateTrendData = () => {
  const days = ['日', '一', '二', '三', '四', '五', '六']
  const data = []
  const today = dayjs()
  
  for (let i = 6; i >= 0; i--) {
    const day = today.subtract(i, 'day')
    const value = Math.floor(Math.random() * 50) + 10 // 模拟数据
    data.push({
      label: days[day.day()],
      value: value,
      height: value * 2
    })
  }
  
  trendData.value = data
}

// 获取配置
const fetchConfig = async () => {
  configLoading.value = true
  try {
    // 获取代理等级配置
    const levelsRes = await api.get('/config/agent-levels')
    const levelsData = levelsRes.data || levelsRes
    if (levelsData.levels) {
      agentLevels.value = levelsData.levels.map(l => ({
        level: l.level,
        name: l.name,
        rate: parseInt(l.rate),
        condition: l.condition || '',
        min_users: l.min_users || 0,
        min_sub_agents: l.min_sub_agents || 0,
        min_sub_level: l.min_sub_level || 0
      }))
    }
    
    // 获取提现配置
    const withdrawRes = await api.get('/config/withdraw')
    const withdrawData = withdrawRes.data || withdrawRes
    configForm.value.min_withdraw = withdrawData.min_amount || 250
    configForm.value.max_withdraw = withdrawData.max_amount || 10000
    configForm.value.withdraw_fee = withdrawData.fee_rate || 20
  } catch (error) {
    console.error('获取配置失败:', error)
  } finally {
    configLoading.value = false
  }
}

// 保存配置
const saveConfig = async () => {
  configSaving.value = true
  try {
    // 保存代理等级配置（比例、条件、升级要求）
    const levelConfigs = {}
    for (const level of agentLevels.value) {
      levelConfigs[`agent_level_${level.level}_rate`] = String(level.rate)
      levelConfigs[`agent_level_${level.level}_condition`] = level.condition || ''
      levelConfigs[`agent_level_${level.level}_min_users`] = String(level.min_users || 0)
      levelConfigs[`agent_level_${level.level}_min_sub_agents`] = String(level.min_sub_agents || 0)
    }
    
    // 保存提现配置
    const withdrawConfigs = {
      withdraw_fee_rate: String(configForm.value.withdraw_fee),
      withdraw_min_amount: String(configForm.value.min_withdraw),
      withdraw_max_amount: String(configForm.value.max_withdraw)
    }
    
    // 批量更新
    await api.post('/config/batch', { ...levelConfigs, ...withdrawConfigs })
    
    ElMessage.success('配置已保存')
    showConfigDialog.value = false
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  } finally {
    configSaving.value = false
  }
}

// 处理风控
const handleFraud = (type) => {
  ElMessage.info(`处理 ${type} 类型的异常记录`)
}

// 添加黑名单
const addToBlacklist = () => {
  if (!newBlacklist.value.value) {
    ElMessage.warning('请输入值')
    return
  }
  blacklist.value.push({
    ...newBlacklist.value,
    created_at: dayjs().format('YYYY-MM-DD HH:mm')
  })
  newBlacklist.value = { type: 'ip', value: '', reason: '' }
  ElMessage.success('已添加到黑名单')
}

// 移除黑名单
const removeFromBlacklist = (row) => {
  const index = blacklist.value.indexOf(row)
  if (index > -1) {
    blacklist.value.splice(index, 1)
    ElMessage.success('已从黑名单移除')
  }
}

// 添加里程碑
const addMilestone = async () => {
  if (!newMilestone.value.invite_count || !newMilestone.value.reward_value) {
    ElMessage.warning('请填写完整信息')
    return
  }
  try {
    await api.post('/admin/promotion/milestones', newMilestone.value)
    ElMessage.success('添加成功')
    fetchMilestones()
    newMilestone.value = { invite_count: 10, reward_type: 'vip_days', reward_value: 7, reward_desc: '' }
  } catch (error) {
    ElMessage.error('添加失败')
  }
}

// 删除里程碑
const deleteMilestone = async (id) => {
  try {
    await api.delete(`/admin/promotion/milestones/${id}`)
    ElMessage.success('删除成功')
    fetchMilestones()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

// 导出数据
const exportData = () => {
  ElMessage.info('导出功能开发中')
}

onMounted(() => {
  fetchStats()
  fetchTopAgents()
  fetchMilestones()
  generateTrendData()
  fetchConfig()
})
</script>

<style lang="scss" scoped>
.promotion-dashboard {
  padding: 20px;
  
  h2 {
    margin-bottom: 20px;
    color: #303133;
  }
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 20px;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 15px;
  
  &.blue { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
  &.green { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
  &.purple { background: linear-gradient(135deg, #a855f7 0%, #7c3aed 100%); }
  &.gold { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
  
  .stat-icon {
    font-size: 40px;
  }
  
  .stat-info {
    flex: 1;
    
    .stat-value {
      display: block;
      font-size: 28px;
      font-weight: 700;
    }
    
    .stat-label {
      font-size: 14px;
      opacity: 0.9;
    }
  }
  
  .stat-trend {
    font-size: 12px;
    opacity: 0.8;
    
    .today {
      background: rgba(255, 255, 255, 0.2);
      padding: 2px 8px;
      border-radius: 10px;
    }
    
    .pending {
      background: rgba(255, 193, 7, 0.3);
      padding: 2px 8px;
      border-radius: 10px;
    }
  }
}

.chart-card {
  height: 280px;
  
  :deep(.el-card__header) {
    padding: 12px 16px;
    font-weight: 600;
  }
  
  :deep(.el-card__body) {
    padding: 16px;
    height: calc(100% - 50px);
  }
}

.trend-chart {
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  height: 100%;
  padding-bottom: 30px;
  
  .trend-bar {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 40px;
    
    .bar {
      width: 30px;
      background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
      border-radius: 4px 4px 0 0;
      min-height: 10px;
      transition: height 0.3s;
    }
    
    .day-label {
      margin-top: 8px;
      font-size: 12px;
      color: #666;
    }
    
    .day-value {
      font-size: 12px;
      color: #999;
    }
  }
}

.ranking-list {
  .ranking-item {
    display: flex;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid #f0f0f0;
    
    &:last-child {
      border-bottom: none;
    }
    
    .rank {
      width: 24px;
      height: 24px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      font-weight: 600;
      margin-right: 12px;
      background: #f0f0f0;
      color: #666;
      
      &.rank-1 { background: #ffd700; color: #fff; }
      &.rank-2 { background: #c0c0c0; color: #fff; }
      &.rank-3 { background: #cd7f32; color: #fff; }
    }
    
    .name {
      flex: 1;
      font-size: 14px;
    }
    
    .amount {
      font-weight: 600;
      color: #f56c6c;
    }
  }
  
  .empty-ranking {
    text-align: center;
    padding: 40px;
    color: #999;
  }
}

.pending-list {
  .pending-item {
    display: flex;
    align-items: center;
    padding: 14px 12px;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.2s;
    
    &:hover {
      background: #f5f7fa;
    }
    
    .pending-icon {
      font-size: 24px;
      margin-right: 12px;
    }
    
    .pending-text {
      flex: 1;
      font-size: 14px;
    }
  }
}

.quick-actions {
  .action-buttons {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    
    .el-button {
      display: flex;
      align-items: center;
      gap: 6px;
    }
  }
}

.fraud-stats {
  .fraud-stat-item {
    display: flex;
    align-items: center;
    padding: 16px;
    border-bottom: 1px solid #f0f0f0;
    
    .fraud-icon {
      font-size: 28px;
      margin-right: 16px;
    }
    
    .fraud-label {
      flex: 1;
      font-size: 14px;
    }
    
    .fraud-value {
      margin-right: 16px;
      font-weight: 600;
      color: #f56c6c;
    }
  }
}

// 等级配置列表
.level-config-list {
  max-height: 400px;
  overflow-y: auto;
  
  .level-config-item {
    padding: 12px;
    margin-bottom: 12px;
    background: #f9f9f9;
    border-radius: 8px;
    border: 1px solid #eee;
    
    .level-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      
      .level-name {
        font-weight: 600;
        color: #333;
      }
      
      .level-rate {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 13px;
        color: #666;
      }
    }
    
    .el-input {
      margin-bottom: 8px;
    }
    
    .level-conditions {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 12px;
      color: #666;
      flex-wrap: wrap;
    }
  }
}

.add-blacklist, .add-milestone {
  display: flex;
  gap: 10px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}
</style>
