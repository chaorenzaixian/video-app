<template>
  <div class="video-review-page">
    <div class="page-header">
      <h1>视频审核</h1>
      <div class="header-stats">
        <span class="stat pending">待审核: {{ stats.pending }}</span>
        <span class="stat approved">今日通过: {{ stats.todayApproved }}</span>
        <span class="stat rejected">今日拒绝: {{ stats.todayRejected }}</span>
      </div>
    </div>

    <!-- 筛选 -->
    <div class="filter-bar">
      <el-select v-model="filter.status" placeholder="审核状态" clearable>
        <el-option label="待审核" value="pending" />
        <el-option label="已通过" value="approved" />
        <el-option label="已拒绝" value="rejected" />
      </el-select>
      <el-input v-model="filter.keyword" placeholder="搜索视频标题" clearable style="width: 200px" />
      <el-button type="primary" @click="fetchReviews">搜索</el-button>
    </div>

    <!-- 审核列表 -->
    <el-table :data="reviews" stripe style="width: 100%">
      <el-table-column label="视频信息" min-width="300">
        <template #default="{ row }">
          <div class="video-info">
            <img :src="row.video?.cover_url || '/images/default-cover.webp'" class="video-cover">
            <div class="video-detail">
              <span class="video-title">{{ row.video?.title }}</span>
              <span class="video-uploader">上传者: {{ row.video?.uploader?.nickname }}</span>
              <span class="video-time">{{ formatTime(row.submitted_at) }}</span>
            </div>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column label="付费设置" width="120">
        <template #default="{ row }">
          <span v-if="row.video?.pay_type === 'free'" class="pay-tag free">免费</span>
          <span v-else class="pay-tag paid">{{ row.video?.coin_price }}金币</span>
        </template>
      </el-table-column>
      
      <el-table-column label="AI审核" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.ai_reviewed" :type="row.ai_score > 80 ? 'success' : 'warning'">
            {{ row.ai_score }}分
          </el-tag>
          <span v-else class="text-gray">未审核</span>
        </template>
      </el-table-column>
      
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'pending'">
            <el-button type="success" size="small" @click="handleApprove(row)">通过</el-button>
            <el-button type="danger" size="small" @click="showRejectDialog(row)">拒绝</el-button>
          </template>
          <el-button size="small" @click="previewVideo(row)">预览</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="pagination.page"
      :page-size="pagination.pageSize"
      :total="pagination.total"
      layout="prev, pager, next"
      @current-change="fetchReviews"
    />

    <!-- 拒绝原因弹窗 -->
    <el-dialog v-model="rejectDialog.visible" title="拒绝原因" width="400px">
      <el-checkbox-group v-model="rejectDialog.reasons">
        <el-checkbox label="内容违规" />
        <el-checkbox label="低质量内容" />
        <el-checkbox label="侵权内容" />
        <el-checkbox label="虚假信息" />
        <el-checkbox label="标题党" />
        <el-checkbox label="其他" />
      </el-checkbox-group>
      <el-input v-model="rejectDialog.note" type="textarea" placeholder="补充说明(选填)" rows="3" style="margin-top: 16px" />
      <template #footer>
        <el-button @click="rejectDialog.visible = false">取消</el-button>
        <el-button type="danger" @click="handleReject">确认拒绝</el-button>
      </template>
    </el-dialog>

    <!-- 视频预览弹窗 -->
    <el-dialog v-model="previewDialog.visible" title="视频预览" width="800px">
      <video v-if="previewDialog.video" :src="previewDialog.video.original_url" controls style="width: 100%"></video>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const reviews = ref([])
const stats = ref({ pending: 0, todayApproved: 0, todayRejected: 0 })

const filter = reactive({
  status: 'pending',
  keyword: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
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
  const texts = { pending: '待审核', approved: '已通过', rejected: '已拒绝' }
  return texts[status] || status
}

const formatTime = (time) => {
  if (!time) return ''
  const d = new Date(time)
  return `${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}`
}

const fetchReviews = async () => {
  try {
    const res = await api.get('/admin/video-reviews', {
      params: {
        status: filter.status,
        keyword: filter.keyword,
        page: pagination.page,
        page_size: pagination.pageSize
      }
    })
    reviews.value = res.data.items || []
    pagination.total = res.data.total || 0
  } catch (error) {
    console.error('获取审核列表失败:', error)
  }
}

const handleApprove = async (row) => {
  try {
    await api.post(`/admin/video-reviews/${row.id}/approve`)
    ElMessage.success('已通过')
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

onMounted(fetchReviews)
</script>

<style lang="scss" scoped>
.video-review-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  h1 {
    font-size: 24px;
    margin: 0;
  }
  
  .header-stats {
    display: flex;
    gap: 16px;
    
    .stat {
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 14px;
      
      &.pending { background: #fff7e6; color: #fa8c16; }
      &.approved { background: #f6ffed; color: #52c41a; }
      &.rejected { background: #fff2f0; color: #ff4d4f; }
    }
  }
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.video-info {
  display: flex;
  gap: 12px;
  
  .video-cover {
    width: 80px;
    height: 50px;
    border-radius: 4px;
    object-fit: cover;
  }
  
  .video-detail {
    display: flex;
    flex-direction: column;
    
    .video-title {
      font-weight: 500;
    }
    
    .video-uploader, .video-time {
      font-size: 12px;
      color: #999;
    }
  }
}

.pay-tag {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  
  &.free { background: #f6ffed; color: #52c41a; }
  &.paid { background: #fff7e6; color: #fa8c16; }
}

.text-gray {
  color: #999;
  font-size: 12px;
}

.el-pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>

