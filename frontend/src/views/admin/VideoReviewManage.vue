<template>
  <div class="admin-page">
    <div class="page-header">
      <h1>视频审核</h1>
      <p class="page-desc">审核创作者上传的视频内容，通过后发布</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card pending">
        <div class="stat-icon">⏳</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.pending }}</span>
          <span class="stat-label">待审核</span>
        </div>
      </div>
      <div class="stat-card success">
        <div class="stat-icon">✅</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.todayApproved }}</span>
          <span class="stat-label">今日通过</span>
        </div>
      </div>
      <div class="stat-card danger">
        <div class="stat-icon">❌</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.todayRejected }}</span>
          <span class="stat-label">今日拒绝</span>
        </div>
      </div>
      <div class="stat-card info">
        <div class="stat-icon">📊</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.total }}</span>
          <span class="stat-label">累计审核</span>
        </div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-select v-model="filter.status" placeholder="审核状态" clearable style="width: 120px">
        <el-option label="待审核" value="pending" />
        <el-option label="已通过" value="approved" />
        <el-option label="已拒绝" value="rejected" />
      </el-select>
      <el-input v-model="filter.keyword" placeholder="视频标题/上传者" clearable style="width: 200px" />
      <el-date-picker v-model="filter.dateRange" type="daterange" start-placeholder="开始" end-placeholder="结束" style="width: 220px" />
      <el-button type="primary" @click="fetchReviews">查询</el-button>
      <el-button @click="resetFilter">重置</el-button>
    </div>

    <!-- 审核列表 -->
    <div class="table-container">
      <el-table :data="reviews" stripe border v-loading="loading">
        <el-table-column label="视频信息" min-width="320">
          <template #default="{ row }">
            <div class="video-cell">
              <div class="video-cover">
                <img :src="row.video?.cover_url || '/images/default-cover.webp'" alt="">
                <span class="video-duration">{{ formatDuration(row.video?.duration) }}</span>
              </div>
              <div class="video-detail">
                <div class="video-title">{{ row.video?.title }}</div>
                <div class="video-meta">
                  <span>上传者: {{ row.video?.uploader?.nickname }}</span>
                  <span>提交: {{ formatTime(row.submitted_at) }}</span>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="付费设置" width="120" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.video?.pay_type === 'free'" type="success" size="small">免费</el-tag>
            <div v-else>
              <el-tag type="warning" size="small">{{ row.video?.coin_price }}金币</el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="AI预审" width="100" align="center">
          <template #default="{ row }">
            <template v-if="row.ai_reviewed">
              <el-tag :type="row.ai_score >= 80 ? 'success' : row.ai_score >= 60 ? 'warning' : 'danger'" size="small">
                {{ row.ai_score }}分
              </el-tag>
            </template>
            <span v-else class="text-gray">未审核</span>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="审核信息" width="180">
          <template #default="{ row }">
            <template v-if="row.status !== 'pending'">
              <div class="review-info">
                <span>{{ formatTime(row.reviewed_at) }}</span>
                <span v-if="row.review_note" class="review-note">{{ row.review_note }}</span>
              </div>
            </template>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button type="success" size="small" @click="handleApprove(row)">通过</el-button>
              <el-button type="danger" size="small" @click="showRejectDialog(row)">拒绝</el-button>
            </template>
            <el-button size="small" @click="previewVideo(row)">预览</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        :page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, prev, pager, next, jumper"
        @current-change="fetchReviews"
        class="pagination"
      />
    </div>

    <!-- 拒绝原因弹窗 -->
    <el-dialog v-model="rejectDialog.visible" title="拒绝视频" width="450px">
      <div class="reject-content">
        <p class="reject-title">请选择拒绝原因：</p>
        <el-checkbox-group v-model="rejectDialog.reasons" class="reason-group">
          <el-checkbox label="内容违规" />
          <el-checkbox label="低质量内容" />
          <el-checkbox label="版权问题" />
          <el-checkbox label="虚假信息" />
          <el-checkbox label="标题党/封面党" />
          <el-checkbox label="重复内容" />
          <el-checkbox label="其他原因" />
        </el-checkbox-group>
        <el-input 
          v-model="rejectDialog.note" 
          type="textarea" 
          rows="3" 
          placeholder="补充说明（选填）" 
          style="margin-top: 16px"
        />
      </div>
      <template #footer>
        <el-button @click="rejectDialog.visible = false">取消</el-button>
        <el-button type="danger" @click="handleReject">确认拒绝</el-button>
      </template>
    </el-dialog>

    <!-- 视频预览弹窗 -->
    <el-dialog v-model="previewDialog.visible" title="视频预览" width="800px" destroy-on-close>
      <div class="preview-content">
        <video 
          v-if="previewDialog.video" 
          :src="previewDialog.video.original_url || previewDialog.video.hls_url" 
          controls 
          style="width: 100%; max-height: 450px"
        ></video>
        <div class="preview-info" v-if="previewDialog.video">
          <h3>{{ previewDialog.video.title }}</h3>
          <p>{{ previewDialog.video.description || '暂无简介' }}</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const loading = ref(false)
const reviews = ref([])
const stats = ref({ pending: 0, todayApproved: 0, todayRejected: 0, total: 0 })

const filter = reactive({
  status: 'pending',
  keyword: '',
  dateRange: null
})

const pagination = reactive({
  page: 1,
  pageSize: 15,
  total: 0
})

const rejectDialog = reactive({
  visible: false,
  review: null,
  reasons: [],
  note: ''
})

const previewDialog = reactive({
  visible: false,
  video: null
})

const getStatusType = (status) => {
  const types = { pending: 'warning', approved: 'success', rejected: 'danger' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { pending: '待审核', approved: '已通过', rejected: '已拒绝', revision: '需修改' }
  return texts[status] || status
}

const formatTime = (time) => {
  if (!time) return '-'
  const d = new Date(time)
  return `${d.getMonth()+1}/${d.getDate()} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

const formatDuration = (seconds) => {
  if (!seconds) return '00:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`
}

const fetchReviews = async () => {
  loading.value = true
  try {
    const res = await api.get('/admin/video-reviews', {
      params: {
        status: filter.status,
        keyword: filter.keyword,
        page: pagination.page,
        page_size: pagination.pageSize
      }
    })
    reviews.value = res.data?.items || []
    pagination.total = res.data?.total || 0
  } catch (error) {
    reviews.value = []
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filter.status = 'pending'
  filter.keyword = ''
  filter.dateRange = null
  pagination.page = 1
  fetchReviews()
}

const handleApprove = async (row) => {
  try {
    await api.post(`/admin/video-reviews/${row.id}/approve`)
    ElMessage.success('审核通过')
    await fetchReviews()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const showRejectDialog = (row) => {
  rejectDialog.review = row
  rejectDialog.reasons = []
  rejectDialog.note = ''
  rejectDialog.visible = true
}

const handleReject = async () => {
  if (rejectDialog.reasons.length === 0) {
    ElMessage.warning('请选择拒绝原因')
    return
  }
  try {
    await api.post(`/admin/video-reviews/${rejectDialog.review.id}/reject`, {
      reasons: rejectDialog.reasons,
      note: rejectDialog.note
    })
    ElMessage.success('已拒绝')
    rejectDialog.visible = false
    await fetchReviews()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const previewVideo = (row) => {
  previewDialog.video = row.video
  previewDialog.visible = true
}

onMounted(() => {
  fetchReviews()
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
      font-size: 28px;
      font-weight: 600;
      color: #303133;
    }
    
    .stat-label {
      font-size: 14px;
      color: #909399;
    }
  }
  
  &.pending .stat-icon { background: #fdf6ec; }
  &.success .stat-icon { background: #f0f9eb; }
  &.danger .stat-icon { background: #fef0f0; }
  &.info .stat-icon { background: #ecf5ff; }
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

.video-cell {
  display: flex;
  gap: 12px;
  
  .video-cover {
    width: 120px;
    height: 68px;
    border-radius: 6px;
    overflow: hidden;
    position: relative;
    flex-shrink: 0;
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    
    .video-duration {
      position: absolute;
      bottom: 4px;
      right: 4px;
      background: rgba(0, 0, 0, 0.7);
      color: #fff;
      font-size: 11px;
      padding: 2px 6px;
      border-radius: 3px;
    }
  }
  
  .video-detail {
    flex: 1;
    min-width: 0;
    
    .video-title {
      font-weight: 500;
      color: #303133;
      margin-bottom: 6px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .video-meta {
      display: flex;
      flex-direction: column;
      gap: 2px;
      font-size: 12px;
      color: #909399;
    }
  }
}

.review-info {
  font-size: 12px;
  color: #909399;
  
  .review-note {
    display: block;
    color: #f56c6c;
    margin-top: 4px;
  }
}

.text-gray {
  color: #c0c4cc;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.reject-content {
  .reject-title {
    margin: 0 0 12px;
    font-weight: 500;
  }
  
  .reason-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
}

.preview-content {
  .preview-info {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #ebeef5;
    
    h3 {
      margin: 0 0 8px;
      font-size: 16px;
    }
    
    p {
      margin: 0;
      color: #909399;
      font-size: 14px;
    }
  }
}

:deep(.el-table) {
  border-radius: 8px;
  
  th {
    background: #f5f7fa !important;
    font-weight: 600;
  }
}
</style>

