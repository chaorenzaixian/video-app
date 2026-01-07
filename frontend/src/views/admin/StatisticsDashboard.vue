<template>
  <div class="admin-page">
    <div class="page-header">
      <h1>数据统计</h1>
      <p class="page-desc">平台核心数据指标概览与分析</p>
    </div>

    <!-- 核心指标卡片 -->
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-icon users">👥</div>
        <div class="kpi-content">
          <span class="kpi-value">{{ overview.users?.total || 0 }}</span>
          <span class="kpi-label">总用户数</span>
          <span class="kpi-change up">今日 +{{ overview.users?.today || 0 }}</span>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icon videos">🎬</div>
        <div class="kpi-content">
          <span class="kpi-value">{{ overview.videos?.total || 0 }}</span>
          <span class="kpi-label">视频总数</span>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icon creators">✨</div>
        <div class="kpi-content">
          <span class="kpi-value">{{ overview.creators?.total || 0 }}</span>
          <span class="kpi-label">创作者数</span>
        </div>
      </div>
      <div class="kpi-card highlight">
        <div class="kpi-icon revenue">💰</div>
        <div class="kpi-content">
          <span class="kpi-value">¥{{ overview.revenue?.today_recharge || 0 }}</span>
          <span class="kpi-label">今日充值</span>
          <span class="kpi-change">本月 ¥{{ overview.revenue?.month_recharge || 0 }}</span>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-row">
      <!-- 收入趋势 -->
      <div class="chart-card">
        <div class="chart-header">
          <h3>收入趋势</h3>
          <el-radio-group v-model="revenueDays" size="small" @change="fetchRevenueChart">
            <el-radio-button :label="7">近7天</el-radio-button>
            <el-radio-button :label="30">近30天</el-radio-button>
          </el-radio-group>
        </div>
        <div class="chart-body">
          <div ref="revenueChartRef" class="chart-container"></div>
        </div>
      </div>

      <!-- 用户增长 -->
      <div class="chart-card">
        <div class="chart-header">
          <h3>用户增长</h3>
          <el-radio-group v-model="userDays" size="small" @change="fetchUsersChart">
            <el-radio-button :label="7">近7天</el-radio-button>
            <el-radio-button :label="30">近30天</el-radio-button>
          </el-radio-group>
        </div>
        <div class="chart-body">
          <div ref="usersChartRef" class="chart-container"></div>
        </div>
      </div>
    </div>

    <!-- 排行榜区域 -->
    <div class="rankings-row">
      <!-- 热门视频 -->
      <div class="ranking-card">
        <div class="ranking-header">
          <h3>🔥 热门视频 TOP10</h3>
          <el-select v-model="videoDays" size="small" @change="fetchTopVideos" style="width: 100px">
            <el-option label="近7天" :value="7" />
            <el-option label="近30天" :value="30" />
          </el-select>
        </div>
        <div class="ranking-body">
          <div v-for="(video, index) in topVideos" :key="video.id" class="ranking-item">
            <span class="rank" :class="{ top3: index < 3 }">{{ index + 1 }}</span>
            <div class="item-cover">
              <img :src="video.cover_url || '/images/default-cover.webp'" alt="">
            </div>
            <div class="item-info">
              <span class="item-title">{{ video.title }}</span>
              <span class="item-meta">播放 {{ formatNumber(video.view_count) }}</span>
            </div>
            <span class="item-value">{{ formatNumber(video.view_count) }}</span>
          </div>
          <div v-if="topVideos.length === 0" class="empty-state">暂无数据</div>
        </div>
      </div>

      <!-- 创作者排行 -->
      <div class="ranking-card">
        <div class="ranking-header">
          <h3>👑 创作者收益榜 TOP10</h3>
          <el-select v-model="creatorMetric" size="small" @change="fetchTopCreators" style="width: 100px">
            <el-option label="收益" value="income" />
            <el-option label="粉丝" value="followers" />
            <el-option label="视频" value="videos" />
          </el-select>
        </div>
        <div class="ranking-body">
          <div v-for="(creator, index) in topCreators" :key="creator.id" class="ranking-item">
            <span class="rank" :class="{ top3: index < 3 }">{{ index + 1 }}</span>
            <el-avatar :size="36" :src="creator.avatar" />
            <div class="item-info">
              <span class="item-title">{{ creator.display_name || creator.nickname }}</span>
              <span class="item-meta">
                <template v-if="creatorMetric === 'income'">粉丝 {{ creator.total_followers }}</template>
                <template v-else-if="creatorMetric === 'followers'">视频 {{ creator.total_videos }}</template>
                <template v-else>粉丝 {{ creator.total_followers }}</template>
              </span>
            </div>
            <span class="item-value">
              <template v-if="creatorMetric === 'income'">{{ creator.total_income }} 金币</template>
              <template v-else-if="creatorMetric === 'followers'">{{ creator.total_followers }}</template>
              <template v-else>{{ creator.total_videos }} 个</template>
            </span>
          </div>
          <div v-if="topCreators.length === 0" class="empty-state">暂无数据</div>
        </div>
      </div>
    </div>

    <!-- 交易汇总 -->
    <div class="summary-card">
      <div class="summary-header">
        <h3>📊 交易汇总</h3>
        <el-date-picker 
          v-model="summaryDateRange" 
          type="daterange" 
          start-placeholder="开始日期" 
          end-placeholder="结束日期"
          size="small"
          @change="fetchSummary"
          style="width: 240px"
        />
      </div>
      <div class="summary-body">
        <div class="summary-item">
          <div class="summary-icon recharge">💳</div>
          <div class="summary-info">
            <span class="summary-label">充值收入</span>
            <span class="summary-value">¥{{ summary.recharge?.total || 0 }}</span>
            <span class="summary-meta">{{ summary.recharge?.orders || 0 }} 笔订单 · {{ summary.recharge?.users || 0 }} 人</span>
          </div>
        </div>
        <div class="summary-item">
          <div class="summary-icon tips">🎁</div>
          <div class="summary-info">
            <span class="summary-label">打赏流水</span>
            <span class="summary-value">{{ summary.tips?.total_coins || 0 }} 金币</span>
            <span class="summary-meta">{{ summary.tips?.count || 0 }} 次打赏</span>
          </div>
        </div>
        <div class="summary-item">
          <div class="summary-icon withdrawal">💸</div>
          <div class="summary-info">
            <span class="summary-label">创作者提现</span>
            <span class="summary-value">¥{{ summary.withdrawals?.total || 0 }}</span>
            <span class="summary-meta">{{ summary.withdrawals?.count || 0 }} 笔</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import api from '@/utils/api'

const overview = ref({})
const revenueDays = ref(7)
const userDays = ref(7)
const videoDays = ref(7)
const creatorMetric = ref('income')
const summaryDateRange = ref(null)

const revenueChartRef = ref(null)
const usersChartRef = ref(null)

const revenueChartData = ref([])
const usersChartData = ref([])
const topVideos = ref([])
const topCreators = ref([])
const summary = ref({})

let revenueChart = null
let usersChart = null

const formatNumber = (num) => {
  if (num >= 10000) return (num / 10000).toFixed(1) + 'w'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k'
  return num
}

const fetchOverview = async () => {
  try {
    const res = await api.get('/admin/statistics/overview')
    overview.value = res.data
  } catch (error) {
    console.error('获取概览数据失败:', error)
  }
}

const fetchRevenueChart = async () => {
  try {
    const res = await api.get('/admin/statistics/revenue/chart', { params: { days: revenueDays.value } })
    revenueChartData.value = res.data || []
    await nextTick()
    renderRevenueChart()
  } catch (error) {
    revenueChartData.value = []
  }
}

const fetchUsersChart = async () => {
  try {
    const res = await api.get('/admin/statistics/users/chart', { params: { days: userDays.value } })
    usersChartData.value = res.data || []
    await nextTick()
    renderUsersChart()
  } catch (error) {
    usersChartData.value = []
  }
}

const fetchTopVideos = async () => {
  try {
    const res = await api.get('/admin/statistics/videos/top', { params: { days: videoDays.value, limit: 10 } })
    topVideos.value = res.data || []
  } catch (error) {
    topVideos.value = []
  }
}

const fetchTopCreators = async () => {
  try {
    const res = await api.get('/admin/statistics/creators/top', { params: { metric: creatorMetric.value, limit: 10 } })
    topCreators.value = res.data || []
  } catch (error) {
    topCreators.value = []
  }
}

const fetchSummary = async () => {
  try {
    const params = {}
    if (summaryDateRange.value) {
      params.start_date = summaryDateRange.value[0]?.toISOString()?.split('T')[0]
      params.end_date = summaryDateRange.value[1]?.toISOString()?.split('T')[0]
    }
    const res = await api.get('/admin/statistics/transactions/summary', { params })
    summary.value = res.data
  } catch (error) {
    summary.value = {}
  }
}

const renderRevenueChart = () => {
  if (!revenueChartRef.value) return
  
  // 简单的CSS图表渲染
  const container = revenueChartRef.value
  const data = revenueChartData.value
  
  if (data.length === 0) {
    container.innerHTML = '<div class="chart-empty">暂无数据</div>'
    return
  }
  
  const maxAmount = Math.max(...data.map(d => d.amount)) || 1
  
  let html = '<div class="simple-chart">'
  data.forEach(d => {
    const height = (d.amount / maxAmount) * 100
    html += `
      <div class="chart-bar-wrapper">
        <div class="chart-bar" style="height: ${height}%"></div>
        <span class="chart-label">${d.date.slice(5)}</span>
      </div>
    `
  })
  html += '</div>'
  container.innerHTML = html
}

const renderUsersChart = () => {
  if (!usersChartRef.value) return
  
  const container = usersChartRef.value
  const data = usersChartData.value
  
  if (data.length === 0) {
    container.innerHTML = '<div class="chart-empty">暂无数据</div>'
    return
  }
  
  const maxUsers = Math.max(...data.map(d => d.new_users)) || 1
  
  let html = '<div class="simple-chart">'
  data.forEach(d => {
    const height = (d.new_users / maxUsers) * 100
    html += `
      <div class="chart-bar-wrapper">
        <div class="chart-bar users" style="height: ${height}%"></div>
        <span class="chart-label">${d.date.slice(5)}</span>
      </div>
    `
  })
  html += '</div>'
  container.innerHTML = html
}

onMounted(async () => {
  await fetchOverview()
  await fetchRevenueChart()
  await fetchUsersChart()
  await fetchTopVideos()
  await fetchTopCreators()
  await fetchSummary()
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

// KPI卡片
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.kpi-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  
  &.highlight {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    
    .kpi-content {
      .kpi-value, .kpi-label, .kpi-change { color: #fff; }
      .kpi-change { opacity: 0.8; }
    }
  }
  
  .kpi-icon {
    width: 60px;
    height: 60px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    
    &.users { background: linear-gradient(135deg, #667eea20, #764ba220); }
    &.videos { background: linear-gradient(135deg, #f093fb20, #f5576c20); }
    &.creators { background: linear-gradient(135deg, #4facfe20, #00f2fe20); }
    &.revenue { background: rgba(255, 255, 255, 0.2); }
  }
  
  .kpi-content {
    .kpi-value {
      display: block;
      font-size: 28px;
      font-weight: 700;
      color: #303133;
    }
    
    .kpi-label {
      font-size: 14px;
      color: #909399;
    }
    
    .kpi-change {
      display: block;
      font-size: 12px;
      color: #909399;
      margin-top: 4px;
      
      &.up { color: #67c23a; }
      &.down { color: #f56c6c; }
    }
  }
}

// 图表区域
.charts-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.chart-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  
  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }
  }
  
  .chart-body {
    .chart-container {
      height: 200px;
    }
  }
}

// 排行榜
.rankings-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.ranking-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  
  .ranking-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }
  }
  
  .ranking-body {
    max-height: 400px;
    overflow-y: auto;
  }
  
  .ranking-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 0;
    border-bottom: 1px solid #f0f0f0;
    
    &:last-child { border-bottom: none; }
    
    .rank {
      width: 24px;
      height: 24px;
      border-radius: 6px;
      background: #f0f0f0;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      font-weight: 600;
      color: #909399;
      
      &.top3 {
        background: linear-gradient(135deg, #ffd700, #ffb347);
        color: #fff;
      }
    }
    
    .item-cover {
      width: 48px;
      height: 32px;
      border-radius: 4px;
      overflow: hidden;
      
      img { width: 100%; height: 100%; object-fit: cover; }
    }
    
    .item-info {
      flex: 1;
      min-width: 0;
      
      .item-title {
        display: block;
        font-size: 14px;
        color: #303133;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      
      .item-meta {
        font-size: 12px;
        color: #909399;
      }
    }
    
    .item-value {
      font-size: 13px;
      font-weight: 500;
      color: #e6a23c;
    }
  }
}

// 汇总卡片
.summary-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  
  .summary-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }
  }
  
  .summary-body {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
  }
  
  .summary-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px;
    background: #f9f9f9;
    border-radius: 10px;
    
    .summary-icon {
      width: 50px;
      height: 50px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      
      &.recharge { background: linear-gradient(135deg, #667eea20, #764ba220); }
      &.tips { background: linear-gradient(135deg, #f093fb20, #f5576c20); }
      &.withdrawal { background: linear-gradient(135deg, #4facfe20, #00f2fe20); }
    }
    
    .summary-info {
      .summary-label {
        display: block;
        font-size: 13px;
        color: #909399;
      }
      
      .summary-value {
        display: block;
        font-size: 22px;
        font-weight: 600;
        color: #303133;
        margin: 4px 0;
      }
      
      .summary-meta {
        font-size: 12px;
        color: #c0c4cc;
      }
    }
  }
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #c0c4cc;
}

// 简单图表样式
:deep(.simple-chart) {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  height: 180px;
  padding: 10px 0;
  
  .chart-bar-wrapper {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    height: 100%;
    
    .chart-bar {
      width: 60%;
      background: linear-gradient(180deg, #667eea, #764ba2);
      border-radius: 4px 4px 0 0;
      min-height: 4px;
      
      &.users {
        background: linear-gradient(180deg, #4facfe, #00f2fe);
      }
    }
    
    .chart-label {
      margin-top: 8px;
      font-size: 11px;
      color: #909399;
    }
  }
}

:deep(.chart-empty) {
  height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
}
</style>

