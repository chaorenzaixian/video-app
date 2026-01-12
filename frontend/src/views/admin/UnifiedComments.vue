<template>
  <div class="unified-comments-page">
    <div class="page-header">
      <h1>评论管理中心</h1>
      <p class="page-desc">统一管理所有内容的评论，支持审核、删除、置顶等操作</p>
    </div>

    <!-- 类型切换 Tab -->
    <el-tabs v-model="activeTab" @tab-change="handleTabChange" class="comment-tabs">
      <el-tab-pane label="全部评论" name="all">
        <template #label>
          <span>全部评论 <el-badge :value="stats.all" :max="9999" type="info" /></span>
        </template>
      </el-tab-pane>
      <el-tab-pane label="长视频" name="video">
        <template #label>
          <span>长视频 <el-badge :value="stats.video" :max="9999" type="primary" /></span>
        </template>
      </el-tab-pane>
      <el-tab-pane label="短视频" name="short">
        <template #label>
          <span>短视频 <el-badge :value="stats.short" :max="9999" type="success" /></span>
        </template>
      </el-tab-pane>
      <el-tab-pane label="社区帖子" name="post">
        <template #label>
          <span>社区帖子 <el-badge :value="stats.post" :max="9999" type="warning" /></span>
        </template>
      </el-tab-pane>
      <el-tab-pane label="图集" name="gallery">
        <template #label>
          <span>图集 <el-badge :value="stats.gallery" :max="9999" type="danger" /></span>
        </template>
      </el-tab-pane>
      <el-tab-pane label="小说" name="novel">
        <template #label>
          <span>小说 <el-badge :value="stats.novel" :max="9999" /></span>
        </template>
      </el-tab-pane>
    </el-tabs>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-input v-model="filters.keyword" placeholder="搜索评论内容/用户名" clearable style="width: 220px" @keyup.enter="fetchComments">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-select v-model="filters.status" placeholder="状态" clearable style="width: 120px">
        <el-option label="正常显示" value="visible" />
        <el-option label="已隐藏" value="hidden" />
      </el-select>
      <el-date-picker
        v-model="filters.dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        style="width: 240px"
        value-format="YYYY-MM-DD"
      />
      <el-button type="primary" @click="fetchComments"><el-icon><Search /></el-icon>搜索</el-button>
      <el-button @click="resetFilters">重置</el-button>
      <el-button type="danger" :disabled="!selectedIds.length" @click="batchDelete">
        批量删除 ({{ selectedIds.length }})
      </el-button>
      <el-button type="warning" :disabled="!selectedIds.length" @click="batchHide">
        批量隐藏
      </el-button>
    </div>

    <!-- 评论列表 -->
    <div class="table-container">
      <el-table 
        :data="comments" 
        v-loading="loading" 
        stripe 
        border
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="45" />
        <el-table-column prop="id" label="ID" width="70" align="center" />
        
        <el-table-column label="类型" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.content_type)" size="small">
              {{ getTypeLabel(row.content_type) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="用户" width="150">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :size="32" :src="row.user_avatar || getDefaultAvatar(row.user_id)" />
              <div class="user-info">
                <div class="username">{{ row.user_name || '未知用户' }}</div>
                <div class="user-id">ID: {{ row.user_id }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="评论内容" min-width="280">
          <template #default="{ row }">
            <div class="content-cell">
              <p class="content">{{ row.content }}</p>
              <div class="meta">
                <el-tag v-if="row.parent_id" size="small" type="info">回复</el-tag>
                <span class="content-link" @click="viewContent(row)">
                  {{ getContentLinkText(row) }}
                </span>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="互动" width="90" align="center">
          <template #default="{ row }">
            <div class="stats-cell">
              <span>❤️ {{ row.like_count || 0 }}</span>
              <span>💬 {{ row.reply_count || 0 }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_hidden ? 'danger' : 'success'" size="small">
              {{ row.is_hidden ? '已隐藏' : '正常' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="特殊标记" width="120" align="center">
          <template #default="{ row }">
            <div class="tags-cell">
              <img v-if="row.is_god" src="/images/god_comment.webp" class="god-badge" title="神评" />
              <el-tag v-if="row.is_pinned" type="warning" size="small">置顶</el-tag>
              <el-tag v-if="row.is_official" type="success" size="small">官方</el-tag>
              <span v-if="!row.is_pinned && !row.is_official && !row.is_god" class="text-muted">-</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="发布时间" width="160" align="center">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="260" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button link :type="row.is_god ? 'danger' : 'primary'" size="small" @click="toggleGod(row)">
                {{ row.is_god ? '取消神评' : '神评' }}
              </el-button>
              <el-button link :type="row.is_pinned ? 'info' : 'warning'" size="small" @click="togglePin(row)">
                {{ row.is_pinned ? '取消置顶' : '置顶' }}
              </el-button>
              <el-button link :type="row.is_hidden ? 'success' : 'warning'" size="small" @click="toggleHidden(row)">
                {{ row.is_hidden ? '显示' : '隐藏' }}
              </el-button>
              <el-popconfirm title="确定删除该评论吗？" @confirm="deleteComment(row)">
                <template #reference>
                  <el-button link type="danger" size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-bar">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchComments"
          @current-change="fetchComments"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'
import dayjs from 'dayjs'

const loading = ref(false)
const comments = ref([])
const selectedIds = ref([])
const activeTab = ref('all')

const stats = reactive({
  all: 0,
  video: 0,
  short: 0,
  post: 0,
  gallery: 0,
  novel: 0
})

const filters = reactive({
  keyword: '',
  status: '',
  dateRange: null
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const getDefaultAvatar = (userId) => {
  const totalAvatars = 52
  const index = ((userId || 1) % totalAvatars)
  if (index < 17) {
    return `/images/avatars/icon_avatar_${index + 1}.webp`
  } else if (index < 32) {
    const num = String(index - 17 + 1).padStart(3, '0')
    return `/images/avatars/DM_20251217202131_${num}.JPEG`
  } else {
    const num = String(index - 32 + 1).padStart(3, '0')
    return `/images/avatars/DM_20251217202341_${num}.JPEG`
  }
}

const formatDate = (date) => {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

const getTypeTagType = (type) => {
  const types = {
    video: 'primary',
    short: 'success', 
    post: 'warning',
    gallery: 'danger',
    novel: ''
  }
  return types[type] || 'info'
}

const getTypeLabel = (type) => {
  const labels = {
    video: '长视频',
    short: '短视频',
    post: '社区',
    gallery: '图集',
    novel: '小说'
  }
  return labels[type] || type
}

const getContentLinkText = (row) => {
  const prefixes = {
    video: '视频',
    short: '短视频',
    post: '帖子',
    gallery: '图集',
    novel: '小说'
  }
  return `${prefixes[row.content_type] || '内容'} #${row.content_id}`
}

const viewContent = (row) => {
  const urls = {
    video: `/user/video/${row.content_id}`,
    short: `/shorts/${row.content_id}`,
    post: `/user/community/post/${row.content_id}`,
    gallery: `/user/gallery/${row.content_id}`,
    novel: `/user/novel/${row.content_id}`
  }
  const url = urls[row.content_type]
  if (url) window.open(url, '_blank')
}

const fetchStats = async () => {
  try {
    const res = await api.get('/admin/unified-comments/stats')
    Object.assign(stats, res.data || {})
  } catch (e) {
    console.error('获取统计失败:', e)
  }
}

const fetchComments = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      content_type: activeTab.value === 'all' ? '' : activeTab.value
    }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.status) params.status = filters.status
    if (filters.dateRange?.length === 2) {
      params.start_date = filters.dateRange[0]
      params.end_date = filters.dateRange[1]
    }
    
    const res = await api.get('/admin/unified-comments', { params })
    const data = res.data || res
    comments.value = data.items || []
    pagination.total = data.total || 0
  } catch (error) {
    console.error('获取评论失败:', error)
    ElMessage.error('获取评论失败')
  } finally {
    loading.value = false
  }
}

const handleTabChange = () => {
  pagination.page = 1
  fetchComments()
}

const resetFilters = () => {
  filters.keyword = ''
  filters.status = ''
  filters.dateRange = null
  pagination.page = 1
  fetchComments()
}

const handleSelectionChange = (rows) => {
  selectedIds.value = rows.map(r => ({ id: r.id, type: r.content_type }))
}

const togglePin = async (row) => {
  try {
    await api.put(`/admin/unified-comments/${row.content_type}/${row.id}`, { is_pinned: !row.is_pinned })
    row.is_pinned = !row.is_pinned
    ElMessage.success(row.is_pinned ? '已置顶' : '已取消置顶')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const toggleHidden = async (row) => {
  try {
    await api.put(`/admin/unified-comments/${row.content_type}/${row.id}`, { is_hidden: !row.is_hidden })
    row.is_hidden = !row.is_hidden
    ElMessage.success(row.is_hidden ? '已隐藏' : '已显示')
    fetchStats()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const toggleGod = async (row) => {
  try {
    await api.put(`/admin/unified-comments/${row.content_type}/${row.id}`, { is_god: !row.is_god })
    row.is_god = !row.is_god
    ElMessage.success(row.is_god ? '已设为神评' : '已取消神评')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const deleteComment = async (row) => {
  try {
    await api.delete(`/admin/unified-comments/${row.content_type}/${row.id}`)
    ElMessage.success('删除成功')
    fetchComments()
    fetchStats()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

const batchDelete = async () => {
  if (!selectedIds.value.length) return
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedIds.value.length} 条评论吗？`, '批量删除', { type: 'warning' })
    await api.post('/admin/unified-comments/batch-delete', { items: selectedIds.value })
    ElMessage.success('批量删除成功')
    selectedIds.value = []
    fetchComments()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('批量删除失败')
  }
}

const batchHide = async () => {
  if (!selectedIds.value.length) return
  try {
    await ElMessageBox.confirm(`确定隐藏选中的 ${selectedIds.value.length} 条评论吗？`, '批量隐藏', { type: 'warning' })
    await api.post('/admin/unified-comments/batch-hide', { items: selectedIds.value })
    ElMessage.success('批量隐藏成功')
    selectedIds.value = []
    fetchComments()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('批量隐藏失败')
  }
}

onMounted(() => {
  fetchStats()
  fetchComments()
})
</script>


<style lang="scss" scoped>
.unified-comments-page {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 20px;
  h1 { font-size: 24px; font-weight: 600; color: #303133; margin: 0 0 8px; }
  .page-desc { color: #909399; font-size: 14px; margin: 0; }
}

.comment-tabs {
  background: #fff;
  padding: 16px 16px 0;
  border-radius: 8px 8px 0 0;
  margin-bottom: 0;
  
  :deep(.el-tabs__header) {
    margin: 0;
  }
  
  :deep(.el-badge__content) {
    font-size: 10px;
    height: 16px;
    line-height: 16px;
    padding: 0 5px;
  }
}

.filter-bar {
  display: flex;
  gap: 12px;
  padding: 16px;
  flex-wrap: wrap;
  background: #fff;
  border-radius: 0 0 8px 8px;
  margin-bottom: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.table-container {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .user-info {
    .username {
      font-size: 13px;
      font-weight: 500;
      color: #303133;
    }
    .user-id {
      font-size: 11px;
      color: #909399;
    }
  }
}

.content-cell {
  .content {
    margin: 0 0 6px;
    font-size: 13px;
    line-height: 1.5;
    word-break: break-word;
    color: #303133;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  
  .meta {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .content-link {
      font-size: 12px;
      color: #409eff;
      cursor: pointer;
      
      &:hover {
        text-decoration: underline;
      }
    }
  }
}

.stats-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: #606266;
}

.tags-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: center;
  
  .god-badge {
    width: 32px;
    height: 32px;
    object-fit: contain;
  }
}

.action-btns {
  display: flex;
  gap: 4px;
  justify-content: center;
  flex-wrap: wrap;
}

.pagination-bar {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.text-muted {
  color: #c0c4cc;
  font-size: 12px;
}

:deep(.el-table) {
  border-radius: 8px;
  th { background: #f5f7fa !important; font-weight: 600; }
}
</style>
