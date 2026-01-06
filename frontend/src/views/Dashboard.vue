<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6" v-for="stat in stats" :key="stat.title">
        <div class="stat-card" :style="{ borderTopColor: stat.color }">
          <div class="stat-icon" :style="{ backgroundColor: stat.bgColor }">
            <el-icon :size="24" :color="stat.color"><component :is="stat.icon" /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-title">{{ stat.title }}</div>
          </div>
          <div class="stat-change" :class="stat.changeType">
            <el-icon v-if="stat.changeType === 'up'"><Top /></el-icon>
            <el-icon v-else><Bottom /></el-icon>
            {{ stat.change }}
          </div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>用户增长趋势</span>
              <el-radio-group v-model="chartRange" size="small">
                <el-radio-button label="7">7天</el-radio-button>
                <el-radio-button label="30">30天</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div class="chart-container" ref="userChartRef"></div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>视频分类占比</span>
          </template>
          <div class="chart-container" ref="categoryChartRef"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 最新数据 -->
    <el-row :gutter="20" class="data-row">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最新视频</span>
              <el-link type="primary" @click="$router.push('/videos')">查看更多</el-link>
            </div>
          </template>
          <el-table :data="latestVideos" stripe>
            <el-table-column prop="title" label="标题" show-overflow-tooltip />
            <el-table-column prop="uploader" label="上传者" width="100" />
            <el-table-column prop="views" label="播放" width="80" />
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最新订单</span>
              <el-link type="primary" @click="$router.push('/orders')">查看更多</el-link>
            </div>
          </template>
          <el-table :data="latestOrders" stripe>
            <el-table-column prop="orderNo" label="订单号" show-overflow-tooltip />
            <el-table-column prop="user" label="用户" width="100" />
            <el-table-column prop="amount" label="金额" width="80">
              <template #default="{ row }">
                ¥{{ row.amount }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="getOrderStatusType(row.status)" size="small">
                  {{ getOrderStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import api from '@/utils/api'

const chartRange = ref('7')
const userChartRef = ref(null)
const categoryChartRef = ref(null)
let userChart = null
let categoryChart = null

const stats = ref([
  { title: '总用户数', value: '12,543', icon: 'User', color: '#6366f1', bgColor: '#eef2ff', change: '+12.5%', changeType: 'up' },
  { title: 'VIP用户', value: '2,345', icon: 'Medal', color: '#f59e0b', bgColor: '#fef3c7', change: '+8.2%', changeType: 'up' },
  { title: '视频总数', value: '8,901', icon: 'VideoPlay', color: '#10b981', bgColor: '#d1fae5', change: '+15.3%', changeType: 'up' },
  { title: '今日收入', value: '¥12,890', icon: 'Money', color: '#ef4444', bgColor: '#fee2e2', change: '-2.1%', changeType: 'down' }
])

const latestVideos = ref([
  { title: '精彩视频教程01', uploader: 'admin', views: 1234, status: 'published' },
  { title: '新手入门指南', uploader: 'user1', views: 890, status: 'processing' },
  { title: '高级技巧分享', uploader: 'user2', views: 567, status: 'published' },
  { title: '实战项目演示', uploader: 'admin', views: 2345, status: 'reviewing' }
])

const latestOrders = ref([
  { orderNo: 'VOD202412050001', user: 'user1', amount: 29, status: 'success' },
  { orderNo: 'VOD202412050002', user: 'user2', amount: 79, status: 'pending' },
  { orderNo: 'VOD202412050003', user: 'user3', amount: 199, status: 'success' },
  { orderNo: 'VOD202412050004', user: 'user4', amount: 29, status: 'failed' }
])

const getStatusType = (status) => {
  const types = { published: 'success', processing: 'warning', reviewing: 'info', failed: 'danger' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { published: '已发布', processing: '处理中', reviewing: '审核中', failed: '失败' }
  return texts[status] || status
}

const getOrderStatusType = (status) => {
  const types = { success: 'success', pending: 'warning', failed: 'danger' }
  return types[status] || 'info'
}

const getOrderStatusText = (status) => {
  const texts = { success: '成功', pending: '待支付', failed: '失败' }
  return texts[status] || status
}

const initUserChart = () => {
  if (!userChartRef.value) return
  
  userChart = echarts.init(userChartRef.value)
  userChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: ['12-01', '12-02', '12-03', '12-04', '12-05', '12-06', '12-07']
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: '新增用户',
        type: 'line',
        smooth: true,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(99, 102, 241, 0.3)' },
            { offset: 1, color: 'rgba(99, 102, 241, 0.05)' }
          ])
        },
        lineStyle: { color: '#6366f1', width: 2 },
        itemStyle: { color: '#6366f1' },
        data: [120, 182, 191, 234, 290, 330, 310]
      },
      {
        name: '活跃用户',
        type: 'line',
        smooth: true,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(16, 185, 129, 0.3)' },
            { offset: 1, color: 'rgba(16, 185, 129, 0.05)' }
          ])
        },
        lineStyle: { color: '#10b981', width: 2 },
        itemStyle: { color: '#10b981' },
        data: [820, 932, 901, 934, 1290, 1330, 1320]
      }
    ]
  })
}

const initCategoryChart = () => {
  if (!categoryChartRef.value) return
  
  categoryChart = echarts.init(categoryChartRef.value)
  categoryChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: '5%', left: 'center' },
    series: [
      {
        name: '分类占比',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: false },
        emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
        labelLine: { show: false },
        data: [
          { value: 1048, name: '教育', itemStyle: { color: '#6366f1' } },
          { value: 735, name: '娱乐', itemStyle: { color: '#10b981' } },
          { value: 580, name: '科技', itemStyle: { color: '#f59e0b' } },
          { value: 484, name: '生活', itemStyle: { color: '#ef4444' } },
          { value: 300, name: '其他', itemStyle: { color: '#8b5cf6' } }
        ]
      }
    ]
  })
}

const fetchDashboardData = async () => {
  try {
    const res = await api.get('/admin/dashboard')
    // 更新统计数据
  } catch (error) {
    // 使用默认数据
  }
}

onMounted(() => {
  initUserChart()
  initCategoryChart()
  fetchDashboardData()
  
  window.addEventListener('resize', () => {
    userChart?.resize()
    categoryChart?.resize()
  })
})

watch(chartRange, () => {
  // 重新获取数据并更新图表
})
</script>

<style lang="scss" scoped>
.dashboard {
  .stat-cards {
    margin-bottom: 20px;
    
    .stat-card {
      background: #fff;
      border-radius: 12px;
      padding: 24px;
      display: flex;
      align-items: center;
      gap: 16px;
      border-top: 3px solid;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
      
      .stat-icon {
        width: 56px;
        height: 56px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      
      .stat-info {
        flex: 1;
        
        .stat-value {
          font-size: 24px;
          font-weight: 700;
          color: #1f2937;
        }
        
        .stat-title {
          font-size: 14px;
          color: #6b7280;
          margin-top: 4px;
        }
      }
      
      .stat-change {
        font-size: 13px;
        display: flex;
        align-items: center;
        gap: 2px;
        
        &.up {
          color: #10b981;
        }
        
        &.down {
          color: #ef4444;
        }
      }
    }
  }
  
  .chart-row,
  .data-row {
    margin-bottom: 20px;
  }
  
  .chart-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .chart-container {
      height: 300px;
    }
  }
}
</style>









