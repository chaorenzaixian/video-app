<template>
  <div class="admin-page">
    <div class="page-header">
      <h1>话题管理</h1>
      <p class="page-desc">管理社区话题分类，支持两级分类结构</p>
    </div>

    <!-- 操作栏 -->
    <div class="filter-bar">
      <el-radio-group v-model="viewMode" @change="handleViewModeChange">
        <el-radio-button value="tree">树形视图</el-radio-button>
        <el-radio-button value="list">列表视图</el-radio-button>
      </el-radio-group>
      <el-select v-model="filter.level" placeholder="层级" clearable style="width: 120px" v-if="viewMode === 'list'">
        <el-option label="顶级分类" :value="1" />
        <el-option label="二级话题" :value="2" />
      </el-select>
      <el-input v-model="filter.keyword" placeholder="搜索话题" clearable style="width: 200px" @keyup.enter="fetchTopics" v-if="viewMode === 'list'" />
      <el-button type="primary" @click="fetchTopics" v-if="viewMode === 'list'">查询</el-button>
      <div style="flex: 1"></div>
      <el-button type="success" @click="showCreateDialog(null)">新建顶级分类</el-button>
    </div>

    <!-- 树形视图 -->
    <div class="table-container" v-if="viewMode === 'tree'">
      <div class="tree-header">
        <span class="col-name">名称</span>
        <span class="col-stats">帖子/关注</span>
        <span class="col-tags">标签</span>
        <span class="col-sort">排序</span>
        <span class="col-actions">操作</span>
      </div>
      <div class="tree-content" v-loading="loading">
        <div v-for="category in treeData" :key="category.id" class="tree-category">
          <!-- 顶级分类 -->
          <div class="tree-item level-1">
            <div class="col-name">
              <el-icon class="expand-icon" @click="toggleExpand(category)">
                <ArrowRight v-if="!category.expanded" />
                <ArrowDown v-else />
              </el-icon>
              <img v-if="category.icon" :src="category.icon" class="topic-icon" />
              <span class="topic-name">{{ category.name }}</span>
              <el-tag size="small" type="info">{{ category.children?.length || 0 }}个子话题</el-tag>
            </div>
            <div class="col-stats">{{ category.post_count }} / {{ category.follow_count }}</div>
            <div class="col-tags">
              <el-tag v-if="category.is_hot" type="danger" size="small">热门</el-tag>
              <el-tag v-if="category.is_recommended" type="success" size="small">推荐</el-tag>
            </div>
            <div class="col-sort">{{ category.sort_order }}</div>
            <div class="col-actions">
              <el-button size="small" type="primary" @click="showCreateDialog(category.id)">添加子话题</el-button>
              <el-button size="small" @click="showEditDialog(category)">编辑</el-button>
              <el-button size="small" type="danger" @click="handleDelete(category)">删除</el-button>
            </div>
          </div>
          <!-- 二级话题 -->
          <div v-show="category.expanded" class="tree-children">
            <div v-for="topic in category.children" :key="topic.id" class="tree-item level-2">
              <div class="col-name">
                <img v-if="topic.cover" :src="topic.cover" class="topic-cover" />
                <span class="topic-name">{{ topic.name }}</span>
              </div>
              <div class="col-stats">{{ topic.post_count }} / {{ topic.follow_count }}</div>
              <div class="col-tags">
                <el-tag v-if="topic.is_hot" type="danger" size="small">热门</el-tag>
                <el-tag v-if="topic.is_recommended" type="success" size="small">推荐</el-tag>
              </div>
              <div class="col-sort">{{ topic.sort_order }}</div>
              <div class="col-actions">
                <el-button size="small" @click="showEditDialog(topic)">编辑</el-button>
                <el-button size="small" @click="showMoveDialog(topic)">移动</el-button>
                <el-button size="small" type="danger" @click="handleDelete(topic)">删除</el-button>
              </div>
            </div>
            <div v-if="!category.children?.length" class="empty-children">暂无子话题</div>
          </div>
        </div>
        <el-empty v-if="!treeData.length && !loading" description="暂无分类" />
      </div>
    </div>

    <!-- 列表视图 -->
    <div class="table-container" v-else>
      <el-table :data="listData" stripe border v-loading="loading">
        <el-table-column label="话题" min-width="250">
          <template #default="{ row }">
            <div class="topic-cell">
              <img :src="row.icon || row.cover || '/images/default-topic.png'" class="topic-cover" />
              <div class="topic-info">
                <span class="topic-name">{{ row.name }}</span>
                <span class="topic-parent" v-if="row.parent_name">所属：{{ row.parent_name }}</span>
                <span class="topic-desc">{{ row.description || '暂无描述' }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="层级" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.level === 1 ? 'primary' : 'success'" size="small">
              {{ row.level === 1 ? '顶级分类' : '二级话题' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="帖子数" width="100" align="center" prop="post_count" />
        <el-table-column label="关注数" width="100" align="center" prop="follow_count" />
        <el-table-column label="排序" width="80" align="center" prop="sort_order" />
        <el-table-column label="标签" width="150" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_hot" type="danger" size="small">热门</el-tag>
            <el-tag v-if="row.is_recommended" type="success" size="small">推荐</el-tag>
            <el-tag v-if="!row.is_active" type="info" size="small">已禁用</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
            <el-button v-if="row.level === 2" size="small" @click="showMoveDialog(row)">移动</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-model:current-page="pagination.page"
        :page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, prev, pager, next"
        @current-change="fetchTopics"
        class="pagination"
      />
    </div>

    <!-- 新建/编辑弹窗 -->
    <el-dialog v-model="formDialog.visible" :title="formDialog.title" width="500px">
      <el-form :model="formDialog.form" label-width="80px">
        <el-form-item label="所属分类" v-if="formDialog.form.parent_id !== undefined || formDialog.isCreate">
          <el-select v-model="formDialog.form.parent_id" placeholder="顶级分类" clearable :disabled="!formDialog.isCreate && formDialog.form.level === 1">
            <el-option label="作为顶级分类" :value="0" />
            <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="formDialog.form.name" placeholder="请输入名称" />
        </el-form-item>
        <el-form-item label="图标" v-if="!formDialog.form.parent_id">
          <div class="upload-with-input">
            <el-upload
              class="icon-uploader"
              :action="uploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="(res) => handleUploadSuccess(res, 'icon')"
              :before-upload="beforeUpload"
              accept="image/*"
            >
              <img v-if="formDialog.form.icon" :src="formDialog.form.icon" class="upload-preview" />
              <el-icon v-else class="upload-icon"><Plus /></el-icon>
            </el-upload>
            <el-input v-model="formDialog.form.icon" placeholder="或输入图标URL" />
          </div>
        </el-form-item>
        <el-form-item label="封面图">
          <div class="upload-with-input">
            <el-upload
              class="cover-uploader"
              :action="uploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="(res) => handleUploadSuccess(res, 'cover')"
              :before-upload="beforeUpload"
              accept="image/*"
            >
              <img v-if="formDialog.form.cover" :src="formDialog.form.cover" class="upload-preview" />
              <el-icon v-else class="upload-icon"><Plus /></el-icon>
            </el-upload>
            <el-input v-model="formDialog.form.cover" placeholder="或输入封面图URL" />
          </div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formDialog.form.description" type="textarea" :rows="3" placeholder="话题描述" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="formDialog.form.sort_order" :min="0" :max="9999" />
          <span class="form-tip">数值越大越靠前</span>
        </el-form-item>
        <el-form-item label="设置">
          <el-checkbox v-model="formDialog.form.is_hot">热门</el-checkbox>
          <el-checkbox v-model="formDialog.form.is_recommended">推荐</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <!-- 移动弹窗 -->
    <el-dialog v-model="moveDialog.visible" title="移动话题" width="400px">
      <p>将 <strong>{{ moveDialog.topic?.name }}</strong> 移动到：</p>
      <el-select v-model="moveDialog.newParentId" placeholder="选择目标分类" style="width: 100%">
        <el-option label="设为顶级分类" :value="0" />
        <el-option v-for="cat in categories.filter(c => c.id !== moveDialog.topic?.parent_id)" :key="cat.id" :label="cat.name" :value="cat.id" />
      </el-select>
      <template #footer>
        <el-button @click="moveDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="handleMove">确定移动</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowRight, ArrowDown, Plus } from '@element-plus/icons-vue'
import api from '@/utils/api'

const loading = ref(false)
const viewMode = ref('tree')
const treeData = ref([])
const listData = ref([])
const categories = ref([])

// 上传配置
const uploadUrl = computed(() => `${api.defaults.baseURL}/admin/gallery-novel/upload/image`)
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`
}))

const beforeUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt5M = file.size / 1024 / 1024 < 5
  if (!isImage) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB')
    return false
  }
  return true
}

const handleUploadSuccess = (response, field) => {
  if (response.url) {
    formDialog.form[field] = response.url
    ElMessage.success('上传成功')
  } else {
    ElMessage.error('上传失败')
  }
}

const filter = reactive({
  level: null,
  keyword: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 50,
  total: 0
})

const formDialog = reactive({
  visible: false,
  title: '',
  isCreate: true,
  editId: null,
  form: {
    name: '',
    parent_id: null,
    icon: '',
    cover: '',
    description: '',
    sort_order: 0,
    is_hot: false,
    is_recommended: false
  }
})

const moveDialog = reactive({
  visible: false,
  topic: null,
  newParentId: null
})

const fetchTreeData = async () => {
  loading.value = true
  try {
    const res = await api.get('/admin/community/topics/tree')
    treeData.value = (res.data || []).map(item => ({ ...item, expanded: true }))
  } catch (e) {
    treeData.value = []
  } finally {
    loading.value = false
  }
}

const fetchTopics = async () => {
  if (viewMode.value === 'tree') {
    await fetchTreeData()
    return
  }
  
  loading.value = true
  try {
    const params = { page: pagination.page, page_size: pagination.pageSize }
    if (filter.level) params.level = filter.level
    if (filter.keyword) params.keyword = filter.keyword
    
    const res = await api.get('/admin/community/topics', { params })
    listData.value = res.data?.items || []
    pagination.total = res.data?.total || 0
  } catch (e) {
    listData.value = []
  } finally {
    loading.value = false
  }
}

const fetchCategories = async () => {
  try {
    const res = await api.get('/admin/community/topics/categories')
    categories.value = res.data || []
  } catch (e) {
    categories.value = []
  }
}

const handleViewModeChange = () => {
  fetchTopics()
}

const toggleExpand = (category) => {
  category.expanded = !category.expanded
}

const showCreateDialog = (parentId) => {
  formDialog.isCreate = true
  formDialog.editId = null
  formDialog.title = parentId ? '添加子话题' : '新建顶级分类'
  formDialog.form = {
    name: '',
    parent_id: parentId || 0,
    icon: '',
    cover: '',
    description: '',
    sort_order: 0,
    is_hot: false,
    is_recommended: false
  }
  formDialog.visible = true
}

const showEditDialog = (row) => {
  formDialog.isCreate = false
  formDialog.editId = row.id
  formDialog.title = row.level === 1 ? '编辑顶级分类' : '编辑话题'
  formDialog.form = {
    name: row.name,
    parent_id: row.parent_id || 0,
    icon: row.icon || '',
    cover: row.cover || '',
    description: row.description || '',
    sort_order: row.sort_order || 0,
    is_hot: row.is_hot,
    is_recommended: row.is_recommended,
    level: row.level
  }
  formDialog.visible = true
}

const submitForm = async () => {
  if (!formDialog.form.name.trim()) {
    ElMessage.warning('请输入名称')
    return
  }
  
  // 转换 parent_id: 0 表示顶级分类，发送给后端时转为 null
  const data = { ...formDialog.form }
  if (data.parent_id === 0) {
    data.parent_id = null
  }
  
  try {
    if (formDialog.isCreate) {
      await api.post('/admin/community/topics', data)
      ElMessage.success('创建成功')
    } else {
      await api.put(`/admin/community/topics/${formDialog.editId}`, data)
      ElMessage.success('更新成功')
    }
    formDialog.visible = false
    fetchTopics()
    fetchCategories()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

const showMoveDialog = (topic) => {
  moveDialog.topic = topic
  moveDialog.newParentId = 0
  moveDialog.visible = true
}

const handleMove = async () => {
  try {
    // 0 表示顶级分类，发送给后端时转为 null
    const newParentId = moveDialog.newParentId === 0 ? null : moveDialog.newParentId
    await api.put(`/admin/community/topics/${moveDialog.topic.id}/move`, null, {
      params: { new_parent_id: newParentId }
    })
    ElMessage.success('移动成功')
    moveDialog.visible = false
    fetchTopics()
    fetchCategories()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '移动失败')
  }
}

const handleDelete = async (row) => {
  const msg = row.level === 1 
    ? `删除顶级分类「${row.name}」前请确保没有子话题，确定删除？` 
    : `确定删除话题「${row.name}」？`
  
  try {
    await ElMessageBox.confirm(msg, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await api.delete(`/admin/community/topics/${row.id}`)
    ElMessage.success('删除成功')
    fetchTopics()
    fetchCategories()
  } catch (e) {
    if (e !== 'cancel') {
      console.error('删除失败:', e)
      ElMessage.error(e.response?.data?.detail || '删除失败')
    }
  }
}

onMounted(() => {
  fetchTopics()
  fetchCategories()
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
  align-items: center;
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

// 树形视图样式
.tree-header {
  display: flex;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 6px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 8px;
}

.tree-content {
  min-height: 200px;
}

.tree-category {
  margin-bottom: 8px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
}

.tree-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  
  &.level-1 {
    background: #fafafa;
    border-bottom: 1px solid #ebeef5;
  }
  
  &.level-2 {
    background: #fff;
    border-bottom: 1px solid #f0f0f0;
    padding-left: 48px;
    
    &:last-child {
      border-bottom: none;
    }
  }
}

.col-name {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  
  .expand-icon {
    cursor: pointer;
    color: #909399;
    transition: transform 0.2s;
    
    &:hover {
      color: #409eff;
    }
  }
  
  .topic-icon {
    width: 32px;
    height: 32px;
    border-radius: 6px;
    object-fit: cover;
  }
  
  .topic-cover {
    width: 40px;
    height: 40px;
    border-radius: 6px;
    object-fit: cover;
  }
  
  .topic-name {
    font-weight: 500;
    color: #303133;
  }
}

.col-stats {
  width: 100px;
  text-align: center;
  color: #606266;
  font-size: 13px;
}

.col-tags {
  width: 120px;
  display: flex;
  gap: 4px;
  justify-content: center;
}

.col-sort {
  width: 60px;
  text-align: center;
  color: #909399;
}

.col-actions {
  width: 240px;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.tree-children {
  background: #fff;
}

.empty-children {
  padding: 24px;
  text-align: center;
  color: #c0c4cc;
  font-size: 13px;
}

// 列表视图样式
.topic-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  
  .topic-cover {
    width: 50px;
    height: 50px;
    border-radius: 8px;
    object-fit: cover;
  }
  
  .topic-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
    
    .topic-name { font-weight: 500; color: #303133; }
    .topic-parent { font-size: 12px; color: #409eff; }
    .topic-desc { font-size: 12px; color: #909399; }
  }
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.form-tip {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}

// 上传样式
.upload-with-input {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  width: 100%;
  
  .el-input {
    flex: 1;
  }
}

.icon-uploader, .cover-uploader {
  :deep(.el-upload) {
    width: 80px;
    height: 80px;
    border: 1px dashed #d9d9d9;
    border-radius: 6px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    transition: border-color 0.2s;
    
    &:hover {
      border-color: #409eff;
    }
  }
}

.upload-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.upload-icon {
  font-size: 24px;
  color: #8c939d;
}

:deep(.el-table) {
  border-radius: 8px;
  th { background: #f5f7fa !important; font-weight: 600; }
}
</style>
