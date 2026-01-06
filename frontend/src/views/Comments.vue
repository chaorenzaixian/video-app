<template>
  <div class="comments-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>评论管理</span>
          <el-button type="danger" size="small" :disabled="!selectedIds.length" @click="batchDelete">
            批量删除 ({{ selectedIds.length }})
          </el-button>
        </div>
      </template>
      
      <div class="filter-bar">
        <el-input v-model="filters.search" placeholder="搜索评论内容/用户名" clearable style="width: 250px" @keyup.enter="fetchComments">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="filters.video_id" placeholder="视频ID" clearable style="width: 120px">
          <el-option v-for="v in videoOptions" :key="v.id" :label="`#${v.id} ${v.title}`" :value="v.id" />
        </el-select>
        <el-select v-model="filters.is_hidden" placeholder="状态" clearable style="width: 100px">
          <el-option label="显示中" :value="false" />
          <el-option label="已隐藏" :value="true" />
        </el-select>
        <el-button type="primary" @click="fetchComments"><el-icon><Search /></el-icon>搜索</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
      
      <el-table 
        :data="comments" 
        v-loading="loading" 
        stripe 
        style="width: 100%" 
        size="small" 
        border
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="40" />
        <el-table-column prop="id" label="ID" width="60" align="center" />
        <el-table-column label="用户" width="140">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :size="28" :src="row.user_avatar || getDefaultAvatar(row.user_id)" />
              <div class="user-info">
                <div class="username">{{ row.user_name }}</div>
                <div class="user-id">ID: {{ row.user_id }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="评论内容" min-width="250">
          <template #default="{ row }">
            <div class="content-cell">
              <p class="content">{{ row.content }}</p>
              <div class="meta">
                <el-tag v-if="row.parent_id" size="small" type="info">回复</el-tag>
                <span class="video-link" @click="viewVideo(row.video_id)">
                  视频 #{{ row.video_id }}
                </span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="互动" width="100" align="center">
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
              {{ row.is_hidden ? '已隐藏' : '显示中' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="置顶" width="70" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_pinned" type="warning" size="small">置顶</el-tag>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="官方" width="70" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_official" type="success" size="small">官方</el-tag>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="发布时间" width="150" align="center">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button link :type="row.is_pinned ? 'info' : 'warning'" size="small" @click="togglePin(row)">
                {{ row.is_pinned ? '取消置顶' : '置顶' }}
              </el-button>
              <el-button link :type="row.is_official ? 'info' : 'success'" size="small" @click="toggleOfficial(row)">
                {{ row.is_official ? '取消官方' : '设为官方' }}
              </el-button>
              <el-button link :type="row.is_hidden ? 'success' : 'warning'" size="small" @click="toggleHidden(row)">
                {{ row.is_hidden ? '显示' : '隐藏' }}
              </el-button>
              <el-popconfirm 
                title="确定删除该评论吗？" 
                confirm-button-text="确定"
                cancel-button-text="取消"
                @confirm="deleteComment(row)"
              >
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
    </el-card>
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
const videoOptions = ref([])
const selectedIds = ref([])

const filters = reactive({
  search: '',
  video_id: null,
  is_hidden: null
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const getDefaultAvatar = (userId) => {
  const totalAvatars = 52
  const index = (userId % totalAvatars)
  
  if (index < 17) {
    return `/images/avatars/icon_avatar_${index + 1}.png`
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

const fetchComments = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    if (filters.search) params.search = filters.search
    if (filters.video_id) params.video_id = filters.video_id
    if (filters.is_hidden !== null) params.is_hidden = filters.is_hidden
    
    const res = await api.get('/admin/comments', { params })
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

const fetchVideos = async () => {
  try {
    const res = await api.get('/admin/videos', { params: { page: 1, page_size: 100 } })
    const data = res.data || res
    videoOptions.value = (data.items || []).map(v => ({ id: v.id, title: v.title?.substring(0, 20) || '未命名' }))
  } catch (error) {
    console.error('获取视频列表失败:', error)
  }
}

const resetFilters = () => {
  filters.search = ''
  filters.video_id = null
  filters.is_hidden = null
  pagination.page = 1
  fetchComments()
}

const handleSelectionChange = (rows) => {
  selectedIds.value = rows.map(r => r.id)
}

const togglePin = async (row) => {
  try {
    await api.put(`/admin/comments/${row.id}`, { is_pinned: !row.is_pinned })
    row.is_pinned = !row.is_pinned
    ElMessage.success(row.is_pinned ? '已置顶' : '已取消置顶')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const toggleOfficial = async (row) => {
  try {
    await api.put(`/admin/comments/${row.id}`, { is_official: !row.is_official })
    row.is_official = !row.is_official
    ElMessage.success(row.is_official ? '已设为官方评论' : '已取消官方评论')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const toggleHidden = async (row) => {
  try {
    await api.put(`/admin/comments/${row.id}`, { is_hidden: !row.is_hidden })
    row.is_hidden = !row.is_hidden
    ElMessage.success(row.is_hidden ? '已隐藏' : '已显示')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const deleteComment = async (row) => {
  try {
    await api.delete(`/admin/comments/${row.id}`)
    ElMessage.success('删除成功')
    fetchComments()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

const batchDelete = async () => {
  if (!selectedIds.value.length) return
  
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedIds.value.length} 条评论吗？`, '批量删除', {
      type: 'warning'
    })
    
    await api.post('/admin/comments/batch-delete', { ids: selectedIds.value })
    ElMessage.success('批量删除成功')
    selectedIds.value = []
    fetchComments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

const viewVideo = (videoId) => {
  window.open(`/user/video/${videoId}`, '_blank')
}

onMounted(() => {
  fetchComments()
  fetchVideos()
})
</script>

<style lang="scss" scoped>
.comments-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .user-info {
    .username {
      font-size: 13px;
      font-weight: 500;
    }
    .user-id {
      font-size: 11px;
      color: #999;
    }
  }
}

.content-cell {
  .content {
    margin: 0 0 6px;
    font-size: 13px;
    line-height: 1.5;
    word-break: break-word;
  }
  
  .meta {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .video-link {
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
  color: #666;
}

.action-btns {
  display: flex;
  gap: 4px;
  justify-content: center;
  flex-wrap: wrap;
}

.pagination-bar {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.text-muted {
  color: #999;
}
</style>
