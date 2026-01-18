<template>
  <div class="transcode-monitor">
    <div class="page-header">
      <h2>转码监控</h2>
      <div class="header-actions">
        <el-button type="primary" :loading="refreshing" @click="refreshAll">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
        <el-button type="warning" @click="restartService" :loading="restarting">
          <el-icon><VideoPlay /></el-icon> 重启服务
        </el-button>
      </div>
    </div>

    <!-- 状态卡片 -->
    <el-row :gutter="20" class="status-cards">
      <el-col :span="6">
        <el-card shadow="hover" :class="['status-card', serviceStatus]">
          <div class="card-content">
            <div class="card-icon">
              <el-icon :size="40"><Monitor /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-title">服务状态</div>
              <div class="card-value">{{ serviceStatusText }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="status-card">
          <div class="card-content">
            <div class="card-icon queue">
              <el-icon :size="40"><List /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-title">待处理队列</div>
              <div class="card-value">{{ queueTotal }} 个</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="status-card">
          <div class="card-content">
            <div class="card-icon processing">
              <el-icon :size="40"><Loading /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-title">正在处理</div>
              <div class="card-value">{{ status?.queue?.processing_count || 0 }} 个</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="status-card">
          <div class="card-content">
            <div class="card-icon completed">
              <el-icon :size="40"><SuccessFilled /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-title">已完成</div>
              <div class="card-value">{{ completedTotal }} 个</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 详细信息 -->
    <el-row :gutter="20" class="detail-section">
      <!-- 队列详情 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>转码队列</span>
              <el-tag :type="queueTotal > 0 ? 'warning' : 'success'">
                {{ queueTotal }} 个待处理
              </el-tag>
            </div>
          </template>
          
          <el-tabs v-model="queueTab">
            <el-tab-pane label="短视频" name="short">
              <div v-if="status?.queue?.short_pending?.length" class="queue-list">
                <div v-for="file in status.queue.short_pending" :key="file" class="queue-item">
                  <el-icon><VideoCamera /></el-icon>
                  <span>{{ file }}</span>
                </div>
              </div>
              <el-empty v-else description="暂无待处理短视频" :image-size="60" />
            </el-tab-pane>
            <el-tab-pane label="长视频" name="long">
              <div v-if="status?.queue?.long_pending?.length" class="queue-list">
                <div v-for="file in status.queue.long_pending" :key="file" class="queue-item">
                  <el-icon><Film /></el-icon>
                  <span>{{ file }}</span>
                </div>
              </div>
              <el-empty v-else description="暂无待处理长视频" :image-size="60" />
            </el-tab-pane>
            <el-tab-pane label="处理中" name="processing">
              <div v-if="status?.queue?.processing?.length" class="queue-list">
                <div v-for="file in status.queue.processing" :key="file" class="queue-item processing">
                  <el-icon class="is-loading"><Loading /></el-icon>
                  <span>{{ file }}</span>
                </div>
              </div>
              <el-empty v-else description="当前无正在处理的视频" :image-size="60" />
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>

      <!-- 磁盘空间 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>磁盘空间</span>
          </template>
          <div v-if="status?.disk?.length" class="disk-list">
            <div v-for="disk in status.disk" :key="disk.drive" class="disk-item">
              <div class="disk-header">
                <span class="disk-drive">{{ disk.drive }}</span>
                <span class="disk-usage">{{ disk.free_gb }} GB 可用 / {{ disk.total_gb }} GB</span>
              </div>
              <el-progress 
                :percentage="disk.used_percent" 
                :color="getDiskColor(disk.used_percent)"
                :stroke-width="20"
              />
            </div>
          </div>
          <el-empty v-else description="无法获取磁盘信息" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 日志区域 -->
    <el-card class="log-section">
      <template #header>
        <div class="card-header">
          <span>转码日志</span>
          <div>
            <el-select v-model="logLines" size="small" style="width: 100px; margin-right: 10px;">
              <el-option :value="20" label="20条" />
              <el-option :value="50" label="50条" />
              <el-option :value="100" label="100条" />
            </el-select>
            <el-switch v-model="autoRefresh" active-text="自动刷新" />
          </div>
        </div>
      </template>
      
      <div class="log-container" ref="logContainer">
        <div 
          v-for="(log, index) in logs" 
          :key="index" 
          :class="['log-entry', log.level]"
        >
          <span class="log-time">{{ log.timestamp }}</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
        <el-empty v-if="!logs.length" description="暂无日志" :image-size="60" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Refresh, VideoPlay, Monitor, List, Loading, SuccessFilled,
  VideoCamera, Film
} from '@element-plus/icons-vue'
import api from '@/utils/api'

const status = ref(null)
const logs = ref([])
const refreshing = ref(false)
const restarting = ref(false)
const queueTab = ref('short')
const logLines = ref(50)
const autoRefresh = ref(false)
const logContainer = ref(null)

let refreshTimer = null

const serviceStatus = computed(() => {
  if (!status.value?.service) return 'unknown'
  return status.value.service.status === 'running' ? 'running' : 'stopped'
})

const serviceStatusText = computed(() => {
  if (!status.value?.service) return '获取中...'
  return status.value.service.status === 'running' ? '运行中' : '已停止'
})

const queueTotal = computed(() => {
  if (!status.value?.queue) return 0
  return (status.value.queue.short_pending_count || 0) + 
         (status.value.queue.long_pending_count || 0)
})

const completedTotal = computed(() => {
  if (!status.value?.completed) return 0
  return (status.value.completed.short_count || 0) + 
         (status.value.completed.long_count || 0)
})

const getDiskColor = (percent) => {
  if (percent >= 90) return '#F56C6C'
  if (percent >= 70) return '#E6A23C'
  return '#67C23A'
}

const fetchStatus = async () => {
  try {
    const res = await api.get('/admin/transcode/status')
    status.value = res.data || res
  } catch (error) {
    console.error('获取状态失败:', error)
  }
}

const fetchLogs = async () => {
  try {
    const res = await api.get('/admin/transcode/logs', {
      params: { lines: logLines.value }
    })
    logs.value = res.data?.logs || res.logs || []
    // 滚动到底部
    if (logContainer.value) {
      setTimeout(() => {
        logContainer.value.scrollTop = logContainer.value.scrollHeight
      }, 100)
    }
  } catch (error) {
    console.error('获取日志失败:', error)
  }
}

const refreshAll = async () => {
  refreshing.value = true
  try {
    await Promise.all([fetchStatus(), fetchLogs()])
    ElMessage.success('刷新成功')
  } finally {
    refreshing.value = false
  }
}

const restartService = async () => {
  try {
    await ElMessageBox.confirm('确定要重启转码服务吗？', '确认', {
      type: 'warning'
    })
    
    restarting.value = true
    const res = await api.post('/admin/transcode/service/restart')
    
    if (res.data?.success || res.success) {
      ElMessage.success(res.data?.message || res.message)
      // 等待几秒后刷新状态
      setTimeout(refreshAll, 3000)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重启服务失败')
    }
  } finally {
    restarting.value = false
  }
}

// 自动刷新
watch(autoRefresh, (val) => {
  if (val) {
    refreshTimer = setInterval(() => {
      fetchStatus()
      fetchLogs()
    }, 5000)
  } else {
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }
})

watch(logLines, () => {
  fetchLogs()
})

onMounted(() => {
  refreshAll()
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.transcode-monitor {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
}

.status-cards {
  margin-bottom: 20px;
}

.status-card {
  border-radius: 8px;
}

.status-card.running {
  border-left: 4px solid #67C23A;
}

.status-card.stopped {
  border-left: 4px solid #F56C6C;
}

.card-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.card-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #67C23A, #85ce61);
  color: white;
}

.card-icon.queue {
  background: linear-gradient(135deg, #E6A23C, #f0c78a);
}

.card-icon.processing {
  background: linear-gradient(135deg, #409EFF, #79bbff);
}

.card-icon.completed {
  background: linear-gradient(135deg, #67C23A, #85ce61);
}

.card-title {
  font-size: 14px;
  color: #909399;
}

.card-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.detail-section {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.queue-list {
  max-height: 300px;
  overflow-y: auto;
}

.queue-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-bottom: 1px solid #EBEEF5;
}

.queue-item:last-child {
  border-bottom: none;
}

.queue-item.processing {
  background: #f0f9eb;
}

.disk-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.disk-item {
  padding: 10px 0;
}

.disk-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.disk-drive {
  font-weight: bold;
  font-size: 16px;
}

.disk-usage {
  color: #909399;
}

.log-section {
  margin-top: 20px;
}

.log-container {
  height: 400px;
  overflow-y: auto;
  background: #1e1e1e;
  border-radius: 4px;
  padding: 10px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
}

.log-entry {
  padding: 4px 8px;
  border-radius: 2px;
  margin-bottom: 2px;
}

.log-entry.info {
  color: #d4d4d4;
}

.log-entry.success {
  color: #4EC9B0;
}

.log-entry.error {
  color: #F14C4C;
  background: rgba(241, 76, 76, 0.1);
}

.log-time {
  color: #808080;
  margin-right: 10px;
}

.log-message {
  color: inherit;
}
</style>
