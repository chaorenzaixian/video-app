<template>
  <div class="audio-novel-manage">
    <!-- 顶部操作栏 -->
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar">
        <div class="filters">
          <el-select v-model="filters.category_id" placeholder="选择分类" clearable style="width: 150px">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
          <el-select v-model="filters.status" placeholder="状态" clearable style="width: 100px">
            <el-option label="连载中" value="ongoing" />
            <el-option label="已完结" value="completed" />
          </el-select>
          <el-input v-model="filters.keyword" placeholder="搜索标题" clearable style="width: 180px" @keyup.enter="loadNovels" />
          <el-button type="primary" @click="loadNovels">搜索</el-button>
        </div>
        <div class="actions">
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>添加有声小说
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 有声小说列表 -->
    <el-card shadow="never">
      <el-table :data="novels" v-loading="loading">
        <el-table-column label="封面" width="80">
          <template #default="{ row }">
            <el-image :src="row.cover" style="width: 50px; height: 70px" fit="cover" />
          </template>
        </el-table-column>
        <el-table-column label="小说信息" min-width="200">
          <template #default="{ row }">
            <div class="novel-cell">
              <div class="title">{{ row.title }}</div>
              <div class="meta">
                <span>作者: {{ row.author || '佚名' }}</span>
                <span>分类: {{ row.category_name || '未分类' }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="章节/音频" width="150">
          <template #default="{ row }">
            <div class="chapter-info">
              <span>{{ row.chapter_count }}章</span>
              <el-tag :type="row.audio_count === row.chapter_count ? 'success' : 'warning'" size="small">
                {{ row.audio_count || 0 }}个音频
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="数据" width="120">
          <template #default="{ row }">
            <div class="stats-cell">
              <span>👁 {{ row.view_count || 0 }}</span>
              <span>❤️ {{ row.like_count || 0 }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'completed' ? 'success' : 'primary'" size="small">
              {{ row.status === 'completed' ? '已完结' : '连载中' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="showEditDialog(row)">编辑</el-button>
            <el-button type="success" link size="small" @click="showAudioManager(row)">音频管理</el-button>
            <el-button type="danger" link size="small" @click="deleteNovel(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, prev, pager, next"
        @current-change="loadNovels"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </el-card>

    <!-- 添加/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑有声小说' : '添加有声小说'" width="650px">
      <el-form :model="form" label-width="80px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="标题" required>
              <el-input v-model="form.title" placeholder="小说标题" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="作者">
              <el-input v-model="form.author" placeholder="作者名" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="分类">
          <el-select v-model="form.category_id" placeholder="选择分类" clearable style="width: 100%">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="封面" required>
          <div class="cover-upload-area">
            <el-upload
              class="cover-uploader"
              :action="uploadImageUrl"
              :headers="uploadHeaders"
              :data="{ subdir: 'novel' }"
              :show-file-list="false"
              :on-success="handleCoverSuccess"
              :before-upload="beforeImageUpload"
              accept="image/*"
            >
              <el-image v-if="form.cover" :src="form.cover" class="cover-preview" fit="cover" />
              <div v-else class="cover-placeholder">
                <el-icon><Plus /></el-icon>
                <span>上传封面</span>
              </div>
            </el-upload>
            <el-input v-model="form.cover" placeholder="或输入封面URL" style="margin-top: 8px" />
          </div>
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="form.status" style="width: 100%">
                <el-option label="连载中" value="ongoing" />
                <el-option label="已完结" value="completed" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="热门">
              <el-switch v-model="form.is_hot" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="推荐">
              <el-switch v-model="form.is_recommended" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="简介">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="小说简介" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveNovel" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 音频管理弹窗 -->
    <el-dialog v-model="audioManagerVisible" :title="'音频管理 - ' + currentNovel?.title" width="900px">
      <div class="audio-manager">
        <div class="manager-toolbar">
          <el-button type="primary" size="small" @click="showAddChapterDialog">
            <el-icon><Plus /></el-icon>添加章节
          </el-button>
          <el-button size="small" @click="showBatchUploadDialog">批量上传音频</el-button>
        </div>

        <el-table :data="chapters" size="small" max-height="400">
          <el-table-column prop="chapter_num" label="章节" width="70" />
          <el-table-column prop="title" label="标题" min-width="150" />
          <el-table-column label="音频" width="200">
            <template #default="{ row }">
              <div v-if="row.audio_url" class="audio-cell">
                <audio :src="row.audio_url" controls style="height: 30px; width: 150px"></audio>
              </div>
              <el-tag v-else type="info" size="small">未上传</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="免费" width="70">
            <template #default="{ row }">
              <el-switch v-model="row.is_free" size="small" @change="updateChapter(row)" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-upload
                :action="uploadAudioUrl"
                :headers="uploadHeaders"
                :show-file-list="false"
                :on-success="(res) => handleAudioUploadSuccess(res, row)"
                :before-upload="beforeAudioUpload"
                accept=".mp3,.wav,.ogg,.m4a"
                style="display: inline-block"
              >
                <el-button type="primary" link size="small">{{ row.audio_url ? '更换音频' : '上传音频' }}</el-button>
              </el-upload>
              <el-button type="primary" link size="small" @click="showEditChapterDialog(row)">编辑</el-button>
              <el-button type="danger" link size="small" @click="deleteChapter(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="manager-footer">
          <span>共 {{ chapters.length }} 章</span>
          <span>已上传音频: {{ chapters.filter(c => c.audio_url).length }} 个</span>
        </div>
      </div>
    </el-dialog>

    <!-- 添加章节弹窗 -->
    <el-dialog v-model="chapterDialogVisible" title="添加章节" width="500px">
      <el-form :model="chapterForm" label-width="80px">
        <el-form-item label="章节号">
          <el-input-number v-model="chapterForm.chapter_num" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="标题" required>
          <el-input v-model="chapterForm.title" placeholder="章节标题" />
        </el-form-item>
        <el-form-item label="音频URL">
          <el-input v-model="chapterForm.audio_url" placeholder="音频文件URL（可选）" />
        </el-form-item>
        <el-form-item label="免费">
          <el-switch v-model="chapterForm.is_free" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="chapterDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveChapter" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 编辑章节弹窗 -->
    <el-dialog v-model="editChapterDialogVisible" title="编辑章节" width="500px">
      <el-form :model="editChapterForm" label-width="80px">
        <el-form-item label="章节号">
          <el-input-number v-model="editChapterForm.chapter_num" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="标题" required>
          <el-input v-model="editChapterForm.title" placeholder="章节标题" />
        </el-form-item>
        <el-form-item label="音频URL">
          <el-input v-model="editChapterForm.audio_url" placeholder="音频文件URL" />
        </el-form-item>
        <el-form-item label="免费">
          <el-switch v-model="editChapterForm.is_free" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editChapterDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="updateEditChapter" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 批量上传音频弹窗 -->
    <el-dialog v-model="batchUploadVisible" title="批量上传音频" width="600px">
      <el-alert type="info" :closable="false" style="margin-bottom: 16px">
        <template #title>
          <div>上传规则：音频文件名需包含章节号，如 "第1章.mp3"、"001.mp3"、"chapter_1.mp3"</div>
          <div>系统会自动匹配章节号并关联音频</div>
        </template>
      </el-alert>
      
      <el-upload
        ref="batchUploadRef"
        :action="uploadAudioUrl"
        :headers="uploadHeaders"
        :on-success="handleBatchAudioSuccess"
        :before-upload="beforeAudioUpload"
        accept=".mp3,.wav,.ogg,.m4a"
        multiple
        :auto-upload="false"
        drag
      >
        <el-icon class="el-icon--upload"><Upload /></el-icon>
        <div class="el-upload__text">拖拽音频文件到此处，或<em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">支持 mp3, wav, ogg, m4a 格式</div>
        </template>
      </el-upload>

      <div v-if="batchUploadResults.length" class="batch-results">
        <div class="result-title">上传结果：</div>
        <div v-for="(r, i) in batchUploadResults" :key="i" class="result-item">
          <el-icon :color="r.success ? '#67c23a' : '#f56c6c'">
            <component :is="r.success ? 'CircleCheck' : 'CircleClose'" />
          </el-icon>
          <span>{{ r.filename }} - {{ r.message }}</span>
        </div>
      </div>

      <template #footer>
        <el-button @click="batchUploadVisible = false">关闭</el-button>
        <el-button type="primary" @click="submitBatchUpload" :loading="batchUploading">开始上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import request from '@/utils/request'

const API_BASE = import.meta.env.VITE_API_BASE || ''

// 状态
const loading = ref(false)
const saving = ref(false)
const novels = ref([])
const categories = ref([])
const chapters = ref([])
const currentNovel = ref(null)

// 筛选
const filters = reactive({
  category_id: '',
  status: '',
  keyword: ''
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 弹窗状态
const dialogVisible = ref(false)
const audioManagerVisible = ref(false)
const chapterDialogVisible = ref(false)
const editChapterDialogVisible = ref(false)
const batchUploadVisible = ref(false)

// 表单
const form = reactive({
  id: null,
  title: '',
  author: '',
  cover: '',
  description: '',
  category_id: null,
  status: 'ongoing',
  is_hot: false,
  is_recommended: false,
  novel_type: 'audio'
})

const chapterForm = reactive({
  chapter_num: 1,
  title: '',
  audio_url: '',
  is_free: true
})

const editChapterForm = reactive({
  id: null,
  chapter_num: 1,
  title: '',
  audio_url: '',
  is_free: true
})

// 批量上传
const batchUploadRef = ref(null)
const batchUploading = ref(false)
const batchUploadResults = ref([])

// 上传配置
const uploadImageUrl = computed(() => `${API_BASE}/api/upload/image`)
const uploadAudioUrl = computed(() => `${API_BASE}/api/upload/file`)
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`
}))

// 加载分类
const loadCategories = async () => {
  try {
    const res = await request.get('/api/admin/gallery-novel/categories', { params: { type: 'novel' } })
    categories.value = res.data || []
  } catch (e) {
    console.error('加载分类失败', e)
  }
}

// 加载有声小说列表
const loadNovels = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      novel_type: 'audio',
      ...filters
    }
    const res = await request.get('/api/admin/gallery-novel/novels', { params })
    novels.value = res.data?.items || []
    pagination.total = res.data?.total || 0
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

// 显示添加弹窗
const showAddDialog = () => {
  Object.assign(form, {
    id: null,
    title: '',
    author: '',
    cover: '',
    description: '',
    category_id: null,
    status: 'ongoing',
    is_hot: false,
    is_recommended: false,
    novel_type: 'audio'
  })
  dialogVisible.value = true
}

// 显示编辑弹窗
const showEditDialog = (row) => {
  Object.assign(form, {
    id: row.id,
    title: row.title,
    author: row.author,
    cover: row.cover,
    description: row.description,
    category_id: row.category_id,
    status: row.status,
    is_hot: row.is_hot,
    is_recommended: row.is_recommended,
    novel_type: 'audio'
  })
  dialogVisible.value = true
}

// 保存小说
const saveNovel = async () => {
  if (!form.title) {
    ElMessage.warning('请输入标题')
    return
  }
  saving.value = true
  try {
    if (form.id) {
      await request.put(`/api/admin/gallery-novel/novel/${form.id}`, form)
      ElMessage.success('更新成功')
    } else {
      await request.post('/api/admin/gallery-novel/novel', form)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    loadNovels()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

// 删除小说
const deleteNovel = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除《${row.title}》？`, '提示', { type: 'warning' })
    await request.delete(`/api/admin/gallery-novel/novel/${row.id}`)
    ElMessage.success('删除成功')
    loadNovels()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

// 显示音频管理
const showAudioManager = async (row) => {
  currentNovel.value = row
  audioManagerVisible.value = true
  await loadChapters(row.id)
}

// 加载章节
const loadChapters = async (novelId) => {
  try {
    const res = await request.get(`/api/admin/gallery-novel/novel/${novelId}/chapters`)
    chapters.value = res.data || []
  } catch (e) {
    ElMessage.error('加载章节失败')
  }
}

// 显示添加章节弹窗
const showAddChapterDialog = () => {
  const maxNum = chapters.value.length > 0 ? Math.max(...chapters.value.map(c => c.chapter_num)) : 0
  Object.assign(chapterForm, {
    chapter_num: maxNum + 1,
    title: '',
    audio_url: '',
    is_free: true
  })
  chapterDialogVisible.value = true
}

// 保存章节
const saveChapter = async () => {
  if (!chapterForm.title) {
    ElMessage.warning('请输入章节标题')
    return
  }
  saving.value = true
  try {
    await request.post(`/api/admin/gallery-novel/novel/${currentNovel.value.id}/chapter`, {
      ...chapterForm,
      content: '' // 有声小说不需要文字内容
    })
    ElMessage.success('添加成功')
    chapterDialogVisible.value = false
    loadChapters(currentNovel.value.id)
  } catch (e) {
    ElMessage.error('添加失败')
  } finally {
    saving.value = false
  }
}

// 显示编辑章节弹窗
const showEditChapterDialog = (row) => {
  Object.assign(editChapterForm, {
    id: row.id,
    chapter_num: row.chapter_num,
    title: row.title,
    audio_url: row.audio_url || '',
    is_free: row.is_free
  })
  editChapterDialogVisible.value = true
}

// 更新编辑的章节
const updateEditChapter = async () => {
  if (!editChapterForm.title) {
    ElMessage.warning('请输入章节标题')
    return
  }
  saving.value = true
  try {
    await request.put(`/api/admin/gallery-novel/chapter/${editChapterForm.id}`, editChapterForm)
    ElMessage.success('更新成功')
    editChapterDialogVisible.value = false
    loadChapters(currentNovel.value.id)
  } catch (e) {
    ElMessage.error('更新失败')
  } finally {
    saving.value = false
  }
}

// 更新章节（免费开关）
const updateChapter = async (row) => {
  try {
    await request.put(`/api/admin/gallery-novel/chapter/${row.id}`, {
      is_free: row.is_free
    })
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

// 删除章节
const deleteChapter = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除章节"${row.title}"？`, '提示', { type: 'warning' })
    await request.delete(`/api/admin/gallery-novel/chapter/${row.id}`)
    ElMessage.success('删除成功')
    loadChapters(currentNovel.value.id)
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

// 封面上传成功
const handleCoverSuccess = (res) => {
  if (res.url) {
    form.cover = res.url
  }
}

// 图片上传前检查
const beforeImageUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt5M = file.size / 1024 / 1024 < 5
  if (!isImage) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过5MB')
    return false
  }
  return true
}

// 音频上传前检查
const beforeAudioUpload = (file) => {
  const validTypes = ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp4', 'audio/x-m4a']
  const isAudio = validTypes.includes(file.type) || /\.(mp3|wav|ogg|m4a)$/i.test(file.name)
  const isLt100M = file.size / 1024 / 1024 < 100
  if (!isAudio) {
    ElMessage.error('只能上传音频文件')
    return false
  }
  if (!isLt100M) {
    ElMessage.error('音频大小不能超过100MB')
    return false
  }
  return true
}

// 单个音频上传成功
const handleAudioUploadSuccess = async (res, row) => {
  if (res.url) {
    try {
      await request.put(`/api/admin/gallery-novel/chapter/${row.id}`, {
        audio_url: res.url
      })
      row.audio_url = res.url
      ElMessage.success('音频上传成功')
    } catch (e) {
      ElMessage.error('保存音频URL失败')
    }
  }
}

// 显示批量上传弹窗
const showBatchUploadDialog = () => {
  batchUploadResults.value = []
  batchUploadVisible.value = true
}

// 批量上传音频成功处理
const handleBatchAudioSuccess = async (res, file) => {
  if (!res.url) {
    batchUploadResults.value.push({
      filename: file.name,
      success: false,
      message: '上传失败'
    })
    return
  }

  // 从文件名提取章节号
  const chapterNum = extractChapterNum(file.name)
  if (!chapterNum) {
    batchUploadResults.value.push({
      filename: file.name,
      success: false,
      message: '无法识别章节号'
    })
    return
  }

  // 查找对应章节
  const chapter = chapters.value.find(c => c.chapter_num === chapterNum)
  if (!chapter) {
    batchUploadResults.value.push({
      filename: file.name,
      success: false,
      message: `未找到第${chapterNum}章`
    })
    return
  }

  // 更新章节音频
  try {
    await request.put(`/api/admin/gallery-novel/chapter/${chapter.id}`, {
      audio_url: res.url
    })
    chapter.audio_url = res.url
    batchUploadResults.value.push({
      filename: file.name,
      success: true,
      message: `已关联到第${chapterNum}章`
    })
  } catch (e) {
    batchUploadResults.value.push({
      filename: file.name,
      success: false,
      message: '保存失败'
    })
  }
}

// 从文件名提取章节号
const extractChapterNum = (filename) => {
  // 匹配各种格式：第1章、001、chapter_1、1.mp3 等
  const patterns = [
    /第(\d+)章/,
    /chapter[_\-]?(\d+)/i,
    /^(\d+)\./,
    /^(\d{2,3})[_\-]/,
    /[_\-](\d+)\./
  ]
  for (const pattern of patterns) {
    const match = filename.match(pattern)
    if (match) {
      return parseInt(match[1])
    }
  }
  return null
}

// 提交批量上传
const submitBatchUpload = () => {
  batchUploading.value = true
  batchUploadRef.value?.submit()
  setTimeout(() => {
    batchUploading.value = false
  }, 1000)
}

onMounted(() => {
  loadCategories()
  loadNovels()
})
</script>

<style scoped>
.audio-novel-manage {
  padding: 20px;
}

.toolbar-card {
  margin-bottom: 16px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.filters {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.novel-cell .title {
  font-weight: 500;
  margin-bottom: 4px;
}

.novel-cell .meta {
  font-size: 12px;
  color: #909399;
}

.novel-cell .meta span {
  margin-right: 12px;
}

.chapter-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stats-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 13px;
}

.cover-upload-area {
  width: 100%;
}

.cover-uploader {
  width: 120px;
  height: 160px;
  border: 1px dashed #dcdfe6;
  border-radius: 6px;
  cursor: pointer;
  overflow: hidden;
}

.cover-uploader:hover {
  border-color: #409eff;
}

.cover-preview {
  width: 120px;
  height: 160px;
}

.cover-placeholder {
  width: 120px;
  height: 160px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.cover-placeholder .el-icon {
  font-size: 28px;
  margin-bottom: 8px;
}

.audio-manager {
  min-height: 300px;
}

.manager-toolbar {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
}

.manager-footer {
  margin-top: 16px;
  display: flex;
  gap: 20px;
  color: #909399;
  font-size: 13px;
}

.audio-cell audio {
  vertical-align: middle;
}

.batch-results {
  margin-top: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
}

.result-title {
  font-weight: 500;
  margin-bottom: 8px;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 13px;
}
</style>
