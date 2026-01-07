<template>
  <div class="admin-page">
    <div class="page-header">
      <h1>评论管理</h1>
      <p class="page-desc">管理社区帖子评论，审核、删除违规内容</p>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-select v-model="filter.status" placeholder="状态" clearable style="width: 120px">
        <el-option label="正常" value="visible" />
        <el-option label="已隐藏" value="hidden" />
        <el-option label="已删除" value="deleted" />
      </el-select>
      <el-input v-model="filter.keyword" placeholder="搜索评论内容" clearable style="width: 200px" @keyup.enter="fetchComments" />
      <el-button type="primary" @click="fetchComments">查询</el-button>
      <el-button @click="resetFilter">重置</el-button>
      <el-button type="danger" :disabled="!selectedIds.length" @click="batchDelete">批量删除</el-button>
    </div>

    <!-- 评论列表 -->
    <div class="table-container">
      <el-table :data="comments" stripe border v-loading="loading" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" />
        
        <el-table-column label="评论内容" min-width="300">
          <template #default="{ row }">
            <div class="comment-cell">
              <div class="comment-user" v-if="row.user">
                <img :src="row.user.avatar || '/images/default-avatar.webp'" class="user-avatar" />
                <span class="user-name">{{ row.user.nickname || row.user.username }}</span>
              </div>
              <p class="comment-text">{{ row.content }}</p>
              <div class="comment-images" v-if="row.images?.length">
                <img v-for="(img, idx) in row.images" :key="idx" :src="img" />
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="所属帖子" width="200">
          <template #default="{ row }">
            <div class="post-preview" v-if="row.post">
              <span class="post-content">{{ row.post.content }}</span>
            </div>
            <span v-else class="text-gray">帖子已删除</span>
          </template>
        </el-table-column>
        
        <el-table-column label="互动" width="100" align="center">
          <template #default="{ row }">
            <div class="stats-cell">
              <span>👍 {{ row.like_count }}</span>
              <span>💬 {{ row.reply_count }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="时间" width="160" align="center">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>

        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <el-button v-if="row.status !== 'visible'" size="small" type="success" @click="updateStatus(row, 'visible')">恢复</el-button>
            <el-button v-if="row.status === 'visible'" size="small" type="warning" @click="updateStatus(row, 'hidden')">隐藏</el-button>
            <el-button v-if="row.status !== 'deleted'" size="small" type="danger" @click="deleteComment(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        :page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, prev, pager, next, jumper"
        @current-change="fetchComments"
        class="pagination"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'

const loading = ref(false)
const comments = ref([])
const selectedIds = ref([])

const filter = reactive({
  status: '',
  keyword: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const getStatusType = (status) => {
  const types = { visible: 'success', hidden: 'warning', deleted: 'danger' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { visible: '正常', hidden: '已隐藏', deleted: '已删除' }
  return texts[status] || status
}

const formatTime = (time) => {
  if (!time) return '-'
  const d = new Date(time)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

const fetchComments = async () => {
  loading.value = true
  try {
    const params = { page: pagination.page, page_size: pagination.pageSize }
    if (filter.status) params.status = filter.status
    if (filter.keyword) params.keyword = filter.keyword
    
    const res = await api.get('/admin/community/comments', { params })
    comments.value = res.data?.items || []
    pagination.total = res.data?.total || 0
  } catch (e) {
    comments.value = []
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filter.status = ''
  filter.keyword = ''
  pagination.page = 1
  fetchComments()
}

const handleSelectionChange = (selection) => {
  selectedIds.value = selection.map(item => item.id)
}

const updateStatus = async (row, status) => {
  try {
    await api.put(`/admin/community/comments/${row.id}/status?status=${status}`)
    ElMessage.success('操作成功')
    fetchComments()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const deleteComment = async (row) => {
  try {
    await ElMessageBox.confirm('确定删除该评论？', '确认删除')
    await api.delete(`/admin/community/comments/${row.id}`)
    ElMessage.success('删除成功')
    fetchComments()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('操作失败')
  }
}

const batchDelete = async () => {
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedIds.value.length} 条评论？`, '确认删除')
    await api.post('/admin/community/comments/batch-delete', { comment_ids: selectedIds.value })
    ElMessage.success('删除成功')
    fetchComments()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('操作失败')
  }
}

onMounted(() => {
  fetchComments()
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
  h1 { font-size: 24px; font-weight: 600; color: #303133; margin: 0 0 8px; }
  .page-desc { color: #909399; font-size: 14px; margin: 0; }
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

.comment-cell {
  .comment-user {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    
    .user-avatar {
      width: 24px;
      height: 24px;
      border-radius: 50%;
    }
    
    .user-name {
      font-size: 13px;
      color: #606266;
    }
  }
  
  .comment-text {
    margin: 0;
    color: #303133;
    line-height: 1.5;
  }
  
  .comment-images {
    display: flex;
    gap: 4px;
    margin-top: 8px;
    
    img {
      width: 50px;
      height: 50px;
      object-fit: cover;
      border-radius: 4px;
    }
  }
}

.post-preview {
  .post-content {
    font-size: 12px;
    color: #909399;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
}

.stats-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
  color: #606266;
}

.text-gray {
  color: #c0c4cc;
  font-size: 12px;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-table) {
  border-radius: 8px;
  th { background: #f5f7fa !important; font-weight: 600; }
}
</style>
