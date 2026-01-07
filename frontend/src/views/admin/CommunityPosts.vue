<template>
  <div class="admin-page">
    <div class="page-header">
      <h1>帖子管理</h1>
      <p class="page-desc">管理社区帖子，审核、置顶、删除等操作</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card info">
        <div class="stat-icon">📝</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.posts?.total || 0 }}</span>
          <span class="stat-label">总帖子</span>
        </div>
      </div>
      <div class="stat-card success">
        <div class="stat-icon">📅</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.posts?.today || 0 }}</span>
          <span class="stat-label">今日新增</span>
        </div>
      </div>
      <div class="stat-card pending">
        <div class="stat-icon">⏳</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.posts?.pending || 0 }}</span>
          <span class="stat-label">待审核</span>
        </div>
      </div>
      <div class="stat-card primary">
        <div class="stat-icon">💬</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.comments?.total || 0 }}</span>
          <span class="stat-label">总评论</span>
        </div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-select v-model="filter.status" placeholder="状态" clearable style="width: 120px">
        <el-option label="已发布" value="published" />
        <el-option label="待审核" value="pending" />
        <el-option label="已隐藏" value="hidden" />
        <el-option label="已删除" value="deleted" />
      </el-select>
      <el-select v-model="filter.feature" placeholder="特性" clearable style="width: 120px">
        <el-option label="置顶" value="is_top" />
        <el-option label="热门" value="is_hot" />
        <el-option label="推荐" value="is_recommended" />
      </el-select>
      <el-input v-model="filter.keyword" placeholder="搜索内容" clearable style="width: 200px" @keyup.enter="fetchPosts" />
      <el-button type="primary" @click="fetchPosts">查询</el-button>
      <el-button @click="resetFilter">重置</el-button>
      <el-button type="danger" :disabled="!selectedIds.length" @click="batchDelete">批量删除</el-button>
      <el-button type="success" @click="showPublishDialog">发布帖子</el-button>
    </div>

    <!-- 帖子列表 -->
    <div class="table-container">
      <el-table :data="posts" stripe border v-loading="loading" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" />
        <el-table-column label="帖子内容" min-width="300">
          <template #default="{ row }">
            <div class="post-cell">
              <div class="post-images" v-if="row.images?.length">
                <img v-for="(img, idx) in row.images.slice(0, 3)" :key="idx" :src="img" @click="previewImage(row.images, idx)" />
                <span v-if="row.images.length > 3" class="more-images">+{{ row.images.length - 3 }}</span>
              </div>
              <div class="post-content">
                <p class="content-text">{{ row.content }}</p>
                <div class="post-meta">
                  <span class="user-info" v-if="row.user">
                    <img :src="row.user.avatar || '/images/default-avatar.webp'" class="user-avatar" />
                    {{ row.user.nickname || row.user.username }}
                  </span>
                  <span>{{ formatTime(row.created_at) }}</span>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="互动数据" width="150" align="center">
          <template #default="{ row }">
            <div class="stats-cell">
              <span>👍 {{ row.like_count }}</span>
              <span>💬 {{ row.comment_count }}</span>
              <span>👁 {{ row.view_count }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="特性" width="120" align="center">
          <template #default="{ row }">
            <div class="feature-tags">
              <el-tag v-if="row.is_top" type="danger" size="small">置顶</el-tag>
              <el-tag v-if="row.is_hot" type="warning" size="small">热门</el-tag>
              <el-tag v-if="row.is_recommended" type="success" size="small">推荐</el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="220" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" @click="showDetail(row)">详情</el-button>
            <el-dropdown trigger="click" @command="(cmd) => handleFeature(row, cmd)">
              <el-button size="small">设置</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :command="{ key: 'is_top', value: !row.is_top }">
                    {{ row.is_top ? '取消置顶' : '置顶' }}
                  </el-dropdown-item>
                  <el-dropdown-item :command="{ key: 'is_hot', value: !row.is_hot }">
                    {{ row.is_hot ? '取消热门' : '设为热门' }}
                  </el-dropdown-item>
                  <el-dropdown-item :command="{ key: 'is_recommended', value: !row.is_recommended }">
                    {{ row.is_recommended ? '取消推荐' : '设为推荐' }}
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-dropdown trigger="click" @command="(cmd) => handleAudit(row, cmd)">
              <el-button size="small" :type="row.status === 'published' ? 'warning' : 'success'">
                {{ row.status === 'published' ? '下架' : '通过' }}
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="published">通过发布</el-dropdown-item>
                  <el-dropdown-item command="hidden">隐藏</el-dropdown-item>
                  <el-dropdown-item command="deleted">删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        :page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, prev, pager, next, jumper"
        @current-change="fetchPosts"
        class="pagination"
      />
    </div>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailDialog.visible" title="帖子详情" width="600px">
      <div class="detail-content" v-if="detailDialog.post">
        <div class="detail-user">
          <img :src="detailDialog.post.user?.avatar || '/images/default-avatar.webp'" class="detail-avatar" />
          <div class="detail-user-info">
            <span class="detail-nickname">{{ detailDialog.post.user?.nickname || detailDialog.post.user?.username }}</span>
            <span class="detail-time">{{ formatTime(detailDialog.post.created_at) }}</span>
          </div>
        </div>
        <div class="detail-text">{{ detailDialog.post.full_content }}</div>
        <div class="detail-images" v-if="detailDialog.post.images?.length">
          <img v-for="(img, idx) in detailDialog.post.images" :key="idx" :src="img" @click="previewImage(detailDialog.post.images, idx)" />
        </div>
        <div class="detail-stats">
          <span>👍 {{ detailDialog.post.like_count }} 点赞</span>
          <span>💬 {{ detailDialog.post.comment_count }} 评论</span>
          <span>👁 {{ detailDialog.post.view_count }} 浏览</span>
        </div>
      </div>
    </el-dialog>

    <!-- 图片预览 -->
    <el-image-viewer v-if="imageViewer.visible" :url-list="imageViewer.images" :initial-index="imageViewer.index" @close="imageViewer.visible = false" />

    <!-- 发布帖子弹窗 -->
    <el-dialog v-model="publishDialog.visible" title="发布帖子" width="700px">
      <el-form :model="publishDialog.form" label-width="80px">
        <el-form-item label="内容" required>
          <el-input v-model="publishDialog.form.content" type="textarea" :rows="5" placeholder="请输入帖子内容" />
        </el-form-item>
        <el-form-item label="图片">
          <div class="images-upload-area">
            <el-upload
              class="images-uploader"
              :action="uploadUrl"
              :headers="uploadHeaders"
              :data="{ subdir: 'community' }"
              :file-list="publishDialog.imageFileList"
              :on-success="handleImageUploadSuccess"
              :on-remove="handleImageRemove"
              :before-upload="beforeImageUpload"
              multiple
              accept="image/*"
              list-type="picture-card"
            >
              <el-icon><Plus /></el-icon>
            </el-upload>
            <div class="images-url-input">
              <el-input v-model="publishDialog.imagesText" type="textarea" :rows="3" placeholder="或手动输入图片URL，每行一个" />
              <el-button size="small" @click="parseImagesText" style="margin-top: 8px">解析URL</el-button>
            </div>
          </div>
          <div class="images-count">已添加 {{ publishDialog.form.images.length }} 张图片</div>
        </el-form-item>
        <el-form-item label="视频">
          <div class="video-upload-area">
            <el-upload
              class="video-uploader"
              :action="uploadVideoUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="handleVideoUploadSuccess"
              :before-upload="beforeVideoUpload"
              :on-progress="handleVideoProgress"
              accept=".mp4,.webm,.mov,.avi,.mkv"
            >
              <el-button type="primary" :loading="publishDialog.videoUploading">
                <el-icon><VideoCamera /></el-icon>
                {{ publishDialog.videoUploading ? `上传中 ${publishDialog.videoProgress}%` : '上传视频' }}
              </el-button>
            </el-upload>
            <el-input 
              v-model="publishDialog.form.video_url" 
              placeholder="或输入视频URL" 
              style="margin-left: 12px; flex: 1" 
              clearable
            />
          </div>
          <div v-if="publishDialog.form.video_url" class="video-preview">
            <video :src="publishDialog.form.video_url" controls style="max-width: 100%; max-height: 200px; margin-top: 8px"></video>
            <el-button type="danger" size="small" @click="publishDialog.form.video_url = ''" style="margin-left: 8px">移除</el-button>
          </div>
          <div class="upload-tip">支持 mp4/webm/mov 格式，最大 500MB</div>
        </el-form-item>
        <el-form-item label="话题">
          <el-select v-model="publishDialog.form.topic_ids" multiple placeholder="选择话题" style="width: 100%">
            <el-option v-for="t in topics" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="置顶">
              <el-switch v-model="publishDialog.form.is_top" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="热门">
              <el-switch v-model="publishDialog.form.is_hot" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="推荐">
              <el-switch v-model="publishDialog.form.is_recommended" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="publishDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitPost" :loading="publishDialog.loading">发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, VideoCamera } from '@element-plus/icons-vue'
import api from '@/utils/api'

const loading = ref(false)
const posts = ref([])
const selectedIds = ref([])
const stats = ref({})
const topics = ref([])

// 上传配置
const uploadUrl = computed(() => `${api.defaults.baseURL}/admin/gallery-novel/upload/image`)
const uploadVideoUrl = computed(() => `${api.defaults.baseURL}/admin/gallery-novel/upload/video`)
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`
}))

const filter = reactive({
  status: '',
  feature: '',
  keyword: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 15,
  total: 0
})

const detailDialog = reactive({
  visible: false,
  post: null
})

const imageViewer = reactive({
  visible: false,
  images: [],
  index: 0
})

const publishDialog = reactive({
  visible: false,
  loading: false,
  imagesText: '',
  imageFileList: [],
  videoUploading: false,
  videoProgress: 0,
  form: {
    content: '',
    images: [],
    video_url: '',
    topic_ids: [],
    is_top: false,
    is_hot: false,
    is_recommended: false
  }
})

const getStatusType = (status) => {
  const types = { published: 'success', pending: 'warning', hidden: 'info', deleted: 'danger' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { published: '已发布', pending: '待审核', hidden: '已隐藏', deleted: '已删除' }
  return texts[status] || status
}

const formatTime = (time) => {
  if (!time) return '-'
  const d = new Date(time)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

const fetchStats = async () => {
  try {
    const res = await api.get('/admin/community/stats')
    stats.value = res.data || {}
  } catch (e) {
    console.error(e)
  }
}

const fetchPosts = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    if (filter.status) params.status = filter.status
    if (filter.keyword) params.keyword = filter.keyword
    if (filter.feature === 'is_top') params.is_top = true
    if (filter.feature === 'is_hot') params.is_hot = true
    
    const res = await api.get('/admin/community/posts', { params })
    posts.value = res.data?.items || []
    pagination.total = res.data?.total || 0
  } catch (e) {
    posts.value = []
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filter.status = ''
  filter.feature = ''
  filter.keyword = ''
  pagination.page = 1
  fetchPosts()
}

const handleSelectionChange = (selection) => {
  selectedIds.value = selection.map(item => item.id)
}

const handleFeature = async (row, cmd) => {
  try {
    await api.put(`/admin/community/posts/${row.id}/feature`, { [cmd.key]: cmd.value })
    ElMessage.success('设置成功')
    fetchPosts()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleAudit = async (row, status) => {
  try {
    await api.put(`/admin/community/posts/${row.id}/audit`, { status })
    ElMessage.success('操作成功')
    fetchPosts()
    fetchStats()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const batchDelete = async () => {
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedIds.value.length} 条帖子？`, '确认删除')
    await api.post('/admin/community/posts/batch-audit', { post_ids: selectedIds.value, status: 'deleted' })
    ElMessage.success('删除成功')
    fetchPosts()
    fetchStats()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('操作失败')
  }
}

const showDetail = (row) => {
  detailDialog.post = row
  detailDialog.visible = true
}

const previewImage = (images, index) => {
  imageViewer.images = images
  imageViewer.index = index
  imageViewer.visible = true
}

const fetchTopics = async () => {
  try {
    const res = await api.get('/admin/community/topics', { params: { page_size: 100 } })
    topics.value = res.data?.items || []
  } catch (e) {
    console.error(e)
  }
}

const showPublishDialog = () => {
  publishDialog.form = {
    content: '',
    images: [],
    video_url: '',
    topic_ids: [],
    is_top: false,
    is_hot: false,
    is_recommended: false
  }
  publishDialog.imagesText = ''
  publishDialog.imageFileList = []
  publishDialog.videoUploading = false
  publishDialog.videoProgress = 0
  publishDialog.visible = true
}

// 图片上传验证
const beforeImageUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isImage) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('图片大小不能超过 10MB')
    return false
  }
  return true
}

// 图片上传成功
const handleImageUploadSuccess = (response, file) => {
  if (response.url) {
    if (!publishDialog.form.images.includes(response.url)) {
      publishDialog.form.images.push(response.url)
    }
    file.url = response.url
  }
}

// 移除图片
const handleImageRemove = (file) => {
  const url = file.url || file.response?.url
  if (url) {
    const idx = publishDialog.form.images.indexOf(url)
    if (idx > -1) {
      publishDialog.form.images.splice(idx, 1)
    }
  }
}

// 解析手动输入的URL
const parseImagesText = () => {
  if (!publishDialog.imagesText.trim()) return
  
  const urls = publishDialog.imagesText
    .split('\n')
    .map(s => s.trim())
    .filter(s => s && (s.startsWith('http') || s.startsWith('/')))
  
  urls.forEach(url => {
    if (!publishDialog.form.images.includes(url)) {
      publishDialog.form.images.push(url)
      publishDialog.imageFileList.push({ name: url.split('/').pop(), url })
    }
  })
  
  publishDialog.imagesText = ''
  ElMessage.success(`已添加 ${urls.length} 张图片`)
}

// 视频上传验证
const beforeVideoUpload = (file) => {
  const allowedExts = ['.mp4', '.webm', '.mov', '.avi', '.mkv']
  const ext = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
  if (!allowedExts.includes(ext)) {
    ElMessage.error('只支持 mp4/webm/mov/avi/mkv 格式')
    return false
  }
  if (file.size / 1024 / 1024 > 500) {
    ElMessage.error('视频文件不能超过 500MB')
    return false
  }
  publishDialog.videoUploading = true
  publishDialog.videoProgress = 0
  return true
}

// 视频上传进度
const handleVideoProgress = (event) => {
  if (event.percent) {
    publishDialog.videoProgress = Math.round(event.percent)
  }
}

// 视频上传成功
const handleVideoUploadSuccess = (response) => {
  publishDialog.videoUploading = false
  publishDialog.videoProgress = 0
  if (response.url) {
    publishDialog.form.video_url = response.url
    ElMessage.success('视频上传成功')
  } else {
    ElMessage.error('上传失败')
  }
}

const submitPost = async () => {
  if (!publishDialog.form.content.trim()) {
    return ElMessage.warning('请输入帖子内容')
  }
  
  publishDialog.loading = true
  try {
    await api.post('/admin/community/posts', {
      ...publishDialog.form
    })
    
    ElMessage.success('发布成功')
    publishDialog.visible = false
    fetchPosts()
    fetchStats()
  } catch (e) {
    ElMessage.error('发布失败')
  } finally {
    publishDialog.loading = false
  }
}

onMounted(() => {
  fetchStats()
  fetchPosts()
  fetchTopics()
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
    .stat-value { display: block; font-size: 28px; font-weight: 600; color: #303133; }
    .stat-label { font-size: 14px; color: #909399; }
  }
  
  &.info .stat-icon { background: #ecf5ff; }
  &.success .stat-icon { background: #f0f9eb; }
  &.pending .stat-icon { background: #fdf6ec; }
  &.primary .stat-icon { background: #f0f9ff; }
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

.post-cell {
  display: flex;
  gap: 12px;
  
  .post-images {
    display: flex;
    gap: 4px;
    flex-shrink: 0;
    
    img {
      width: 60px;
      height: 60px;
      object-fit: cover;
      border-radius: 4px;
      cursor: pointer;
    }
    
    .more-images {
      width: 60px;
      height: 60px;
      background: rgba(0,0,0,0.5);
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 4px;
      font-size: 14px;
    }
  }
  
  .post-content {
    flex: 1;
    min-width: 0;
    
    .content-text {
      margin: 0 0 8px;
      color: #303133;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
    
    .post-meta {
      display: flex;
      gap: 12px;
      font-size: 12px;
      color: #909399;
      
      .user-info {
        display: flex;
        align-items: center;
        gap: 4px;
        
        .user-avatar {
          width: 20px;
          height: 20px;
          border-radius: 50%;
        }
      }
    }
  }
}

.stats-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
  color: #606266;
}

.feature-tags {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: center;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.detail-content {
  .detail-user {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
    
    .detail-avatar {
      width: 48px;
      height: 48px;
      border-radius: 50%;
    }
    
    .detail-user-info {
      display: flex;
      flex-direction: column;
      
      .detail-nickname { font-weight: 500; color: #303133; }
      .detail-time { font-size: 12px; color: #909399; }
    }
  }
  
  .detail-text {
    color: #303133;
    line-height: 1.6;
    margin-bottom: 16px;
    white-space: pre-wrap;
  }
  
  .detail-images {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 16px;
    
    img {
      width: 120px;
      height: 120px;
      object-fit: cover;
      border-radius: 8px;
      cursor: pointer;
    }
  }
  
  .detail-stats {
    display: flex;
    gap: 24px;
    color: #909399;
    font-size: 14px;
    padding-top: 16px;
    border-top: 1px solid #ebeef5;
  }
}

:deep(.el-table) {
  border-radius: 8px;
  th { background: #f5f7fa !important; font-weight: 600; }
}

.images-upload-area {
  display: flex;
  gap: 16px;
  
  .images-uploader {
    flex: 1;
    
    :deep(.el-upload-list--picture-card) {
      .el-upload-list__item {
        width: 80px;
        height: 80px;
      }
    }
    
    :deep(.el-upload--picture-card) {
      width: 80px;
      height: 80px;
    }
  }
  
  .images-url-input {
    width: 250px;
  }
}

.images-count {
  margin-top: 8px;
  color: #909399;
  font-size: 12px;
}

.video-upload-area {
  display: flex;
  align-items: center;
}

.video-preview {
  display: flex;
  align-items: flex-start;
  margin-top: 8px;
}

.upload-tip {
  margin-top: 4px;
  color: #909399;
  font-size: 12px;
}
</style>
