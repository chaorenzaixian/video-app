<template>
  <div class="novel-manage">
    <el-card class="category-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>小说分类</span>
          <el-button type="primary" size="small" @click="showCategoryDialog()">
            <el-icon><Plus /></el-icon>添加分类
          </el-button>
        </div>
      </template>
      <el-table :data="categories" size="small">
        <el-table-column prop="name" label="分类名称" />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.novel_type === 'text' ? 'primary' : 'success'" size="small">
              {{ row.novel_type === 'text' ? '文字' : '有声' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="novel_count" label="小说数" width="80" />
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="showCategoryDialog(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="deleteCategory(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <div class="filters">
            <el-select v-model="filters.novel_type" placeholder="类型" clearable style="width: 100px">
              <el-option label="文字" value="text" />
              <el-option label="有声" value="audio" />
            </el-select>
            <el-select v-model="filters.category_id" placeholder="选择分类" clearable style="width: 150px">
              <el-option v-for="c in filteredCategories" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
            <el-input v-model="filters.keyword" placeholder="搜索标题" clearable style="width: 200px" />
            <el-button type="primary" @click="loadNovels">搜索</el-button>
          </div>
          <el-button type="primary" @click="showNovelDialog()">
            <el-icon><Plus /></el-icon>添加小说
          </el-button>
        </div>
      </template>

      <el-table :data="novels" v-loading="loading">
        <el-table-column label="封面" width="80">
          <template #default="{ row }">
            <el-image :src="row.cover" style="width: 50px; height: 70px" fit="cover" />
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="150" />
        <el-table-column prop="author" label="作者" width="100" />
        <el-table-column prop="category_name" label="分类" width="100" />
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.novel_type === 'text' ? 'primary' : 'success'" size="small">
              {{ row.novel_type === 'text' ? '文字' : '有声' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="chapter_count" label="章节" width="80" />
        <el-table-column prop="view_count" label="浏览" width="80" />
        <el-table-column label="热门" width="80">
          <template #default="{ row }">
            <el-switch v-model="row.is_hot" @change="updateNovel(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="showNovelDialog(row)">编辑</el-button>
            <el-button type="success" link size="small" @click="showChaptersDialog(row)">章节</el-button>
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

    <!-- 分类弹窗 -->
    <el-dialog v-model="categoryDialogVisible" :title="categoryForm.id ? '编辑分类' : '添加分类'" width="400px">
      <el-form :model="categoryForm" label-width="80px">
        <el-form-item label="分类名称" required>
          <el-input v-model="categoryForm.name" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="categoryForm.novel_type" style="width: 100%">
            <el-option label="文字小说" value="text" />
            <el-option label="有声小说" value="audio" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="categoryForm.sort_order" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="categoryDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveCategory">保存</el-button>
      </template>
    </el-dialog>

    <!-- 小说弹窗 -->
    <el-dialog v-model="novelDialogVisible" :title="novelForm.id ? '编辑小说' : '添加小说'" width="650px">
      <el-form :model="novelForm" label-width="80px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="标题" required>
              <el-input v-model="novelForm.title" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="作者">
              <el-input v-model="novelForm.author" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="类型" required>
              <el-select v-model="novelForm.novel_type" style="width: 100%">
                <el-option label="文字小说" value="text" />
                <el-option label="有声小说" value="audio" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分类">
              <el-select v-model="novelForm.category_id" placeholder="选择分类" clearable style="width: 100%">
                <el-option v-for="c in novelFormCategories" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 封面上传 -->
        <el-form-item label="封面" required>
          <div class="cover-upload">
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
              <el-image v-if="novelForm.cover" :src="novelForm.cover" class="cover-preview" fit="cover" />
              <div v-else class="cover-placeholder">
                <el-icon><Plus /></el-icon>
                <span>上传封面</span>
              </div>
            </el-upload>
            <div class="cover-url-input">
              <el-input v-model="novelForm.cover" placeholder="或输入封面URL" clearable />
            </div>
          </div>
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="状态">
              <el-select v-model="novelForm.status" style="width: 100%">
                <el-option label="连载中" value="ongoing" />
                <el-option label="已完结" value="completed" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="热门">
              <el-switch v-model="novelForm.is_hot" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="简介">
          <el-input v-model="novelForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="novelDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveNovel" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 章节管理弹窗 -->
    <el-dialog v-model="chaptersDialogVisible" :title="'章节管理 - ' + (currentNovel?.title || '')" width="850px">
      <div class="chapters-header">
        <el-button type="primary" size="small" @click="showChapterDialog()">
          <el-icon><Plus /></el-icon>添加章节
        </el-button>
      </div>
      <el-table :data="chapters" size="small" max-height="400">
        <el-table-column prop="chapter_num" label="章节号" width="80" />
        <el-table-column prop="title" label="标题" />
        <el-table-column label="内容" width="120">
          <template #default="{ row }">
            {{ row.content_length > 0 ? row.content_length + '字' : (row.audio_url ? '有音频' : '无') }}
          </template>
        </el-table-column>
        <el-table-column label="免费" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_free ? 'success' : 'warning'" size="small">
              {{ row.is_free ? '免费' : '付费' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="showChapterDialog(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="deleteChapter(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 章节编辑弹窗 -->
    <el-dialog v-model="chapterDialogVisible" :title="chapterForm.id ? '编辑章节' : '添加章节'" width="700px">
      <el-form :model="chapterForm" label-width="80px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="章节号" required>
              <el-input-number v-model="chapterForm.chapter_num" :min="1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="免费">
              <el-switch v-model="chapterForm.is_free" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="标题" required>
          <el-input v-model="chapterForm.title" />
        </el-form-item>

        <!-- 有声小说：音频上传 -->
        <el-form-item v-if="currentNovel?.novel_type === 'audio'" label="音频">
          <div class="audio-upload">
            <el-upload
              class="audio-uploader"
              :action="uploadAudioUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="handleAudioSuccess"
              :before-upload="beforeAudioUpload"
              :on-progress="handleAudioProgress"
              accept=".mp3,.wav,.ogg,.m4a,.aac"
            >
              <el-button type="primary" :loading="audioUploading">
                <el-icon><Upload /></el-icon>
                {{ audioUploading ? '上传中...' : '上传音频' }}
              </el-button>
            </el-upload>
            <el-input 
              v-model="chapterForm.audio_url" 
              placeholder="或输入音频URL" 
              style="margin-left: 12px; flex: 1" 
            />
          </div>
          <div v-if="chapterForm.audio_url" class="audio-preview">
            <audio :src="chapterForm.audio_url" controls style="width: 100%; margin-top: 8px"></audio>
          </div>
        </el-form-item>

        <!-- 文字小说：内容输入 -->
        <el-form-item v-else label="内容">
          <el-input v-model="chapterForm.content" type="textarea" :rows="12" placeholder="输入章节内容..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="chapterDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveChapter" :loading="savingChapter">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import api from '@/utils/api'

const loading = ref(false)
const saving = ref(false)
const savingChapter = ref(false)
const categories = ref([])
const novels = ref([])
const chapters = ref([])
const currentNovel = ref(null)
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({ category_id: null, novel_type: null, keyword: '' })

const categoryDialogVisible = ref(false)
const categoryForm = reactive({ id: null, name: '', novel_type: 'text', sort_order: 0 })

const novelDialogVisible = ref(false)
const novelForm = reactive({
  id: null, category_id: null, title: '', author: '', cover: '',
  description: '', novel_type: 'text', status: 'ongoing', is_hot: false
})

const chaptersDialogVisible = ref(false)
const chapterDialogVisible = ref(false)
const chapterForm = reactive({
  id: null, chapter_num: 1, title: '', content: '', audio_url: '', is_free: true
})

const audioUploading = ref(false)

// 上传配置
const uploadImageUrl = computed(() => `${api.defaults.baseURL}/admin/gallery-novel/upload/image`)
const uploadAudioUrl = computed(() => `${api.defaults.baseURL}/admin/gallery-novel/upload/audio`)
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`
}))

const filteredCategories = computed(() => {
  if (!filters.novel_type) return categories.value
  return categories.value.filter(c => c.novel_type === filters.novel_type)
})

const novelFormCategories = computed(() => {
  return categories.value.filter(c => c.novel_type === novelForm.novel_type)
})

onMounted(() => {
  loadCategories()
  loadNovels()
})

async function loadCategories() {
  try {
    const { data } = await api.get('/admin/gallery-novel/novel/categories')
    categories.value = data
  } catch (e) {
    ElMessage.error('加载分类失败')
  }
}

async function loadNovels() {
  loading.value = true
  try {
    const params = { page: pagination.page, page_size: pagination.pageSize, ...filters }
    const { data } = await api.get('/admin/gallery-novel/novels', { params })
    novels.value = data.items
    pagination.total = data.total
  } catch (e) {
    ElMessage.error('加载小说失败')
  } finally {
    loading.value = false
  }
}

function showCategoryDialog(row = null) {
  if (row) {
    Object.assign(categoryForm, row)
  } else {
    Object.assign(categoryForm, { id: null, name: '', novel_type: 'text', sort_order: 0 })
  }
  categoryDialogVisible.value = true
}

async function saveCategory() {
  if (!categoryForm.name) return ElMessage.warning('请输入分类名称')
  try {
    if (categoryForm.id) {
      await api.put(`/admin/gallery-novel/novel/categories/${categoryForm.id}`, categoryForm)
    } else {
      await api.post('/admin/gallery-novel/novel/categories', categoryForm)
    }
    ElMessage.success('保存成功')
    categoryDialogVisible.value = false
    loadCategories()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function deleteCategory(row) {
  await ElMessageBox.confirm('确定删除该分类？', '提示')
  try {
    await api.delete(`/admin/gallery-novel/novel/categories/${row.id}`)
    ElMessage.success('删除成功')
    loadCategories()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

function showNovelDialog(row = null) {
  if (row) {
    Object.assign(novelForm, row)
  } else {
    Object.assign(novelForm, {
      id: null, category_id: null, title: '', author: '', cover: '',
      description: '', novel_type: 'text', status: 'ongoing', is_hot: false
    })
  }
  novelDialogVisible.value = true
}

// 图片上传验证
function beforeImageUpload(file) {
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

// 封面上传成功
function handleCoverSuccess(response) {
  if (response.url) {
    novelForm.cover = response.url
    ElMessage.success('封面上传成功')
  } else {
    ElMessage.error('上传失败')
  }
}

async function saveNovel() {
  if (!novelForm.title || !novelForm.cover) return ElMessage.warning('请填写标题和封面')
  saving.value = true
  try {
    if (novelForm.id) {
      await api.put(`/admin/gallery-novel/novels/${novelForm.id}`, novelForm)
    } else {
      await api.post('/admin/gallery-novel/novels', novelForm)
    }
    ElMessage.success('保存成功')
    novelDialogVisible.value = false
    loadNovels()
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function updateNovel(row) {
  try {
    await api.put(`/admin/gallery-novel/novels/${row.id}`, { is_hot: row.is_hot })
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

async function deleteNovel(row) {
  await ElMessageBox.confirm('确定删除该小说？', '提示')
  try {
    await api.delete(`/admin/gallery-novel/novels/${row.id}`)
    ElMessage.success('删除成功')
    loadNovels()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

async function showChaptersDialog(novel) {
  currentNovel.value = novel
  try {
    const { data } = await api.get(`/admin/gallery-novel/novels/${novel.id}/chapters`)
    chapters.value = data
    chaptersDialogVisible.value = true
  } catch (e) {
    ElMessage.error('加载章节失败')
  }
}

function showChapterDialog(row = null) {
  if (row) {
    Object.assign(chapterForm, row)
  } else {
    const maxNum = chapters.value.length > 0 ? Math.max(...chapters.value.map(c => c.chapter_num)) : 0
    Object.assign(chapterForm, {
      id: null, chapter_num: maxNum + 1, title: '', content: '', audio_url: '', is_free: true
    })
  }
  chapterDialogVisible.value = true
}

// 音频上传验证
function beforeAudioUpload(file) {
  const allowedExts = ['.mp3', '.wav', '.ogg', '.m4a', '.aac']
  const ext = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
  if (!allowedExts.includes(ext)) {
    ElMessage.error('只支持 mp3/wav/ogg/m4a/aac 格式')
    return false
  }
  if (file.size / 1024 / 1024 > 100) {
    ElMessage.error('音频文件不能超过 100MB')
    return false
  }
  audioUploading.value = true
  return true
}

function handleAudioProgress() {
  // 上传进度
}

function handleAudioSuccess(response) {
  audioUploading.value = false
  if (response.url) {
    chapterForm.audio_url = response.url
    ElMessage.success('音频上传成功')
  } else {
    ElMessage.error('上传失败')
  }
}

async function saveChapter() {
  if (!chapterForm.title) return ElMessage.warning('请输入章节标题')
  savingChapter.value = true
  try {
    if (chapterForm.id) {
      await api.put(`/admin/gallery-novel/novels/${currentNovel.value.id}/chapters/${chapterForm.id}`, chapterForm)
    } else {
      await api.post(`/admin/gallery-novel/novels/${currentNovel.value.id}/chapters`, chapterForm)
    }
    ElMessage.success('保存成功')
    chapterDialogVisible.value = false
    showChaptersDialog(currentNovel.value)
    loadNovels()
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    savingChapter.value = false
  }
}

async function deleteChapter(row) {
  await ElMessageBox.confirm('确定删除该章节？', '提示')
  try {
    await api.delete(`/admin/gallery-novel/novels/${currentNovel.value.id}/chapters/${row.id}`)
    ElMessage.success('删除成功')
    showChaptersDialog(currentNovel.value)
    loadNovels()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}
</script>

<style lang="scss" scoped>
.novel-manage {
  .category-card { margin-bottom: 20px; }
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    .filters { display: flex; gap: 10px; }
  }
  .chapters-header { margin-bottom: 16px; }
}

.cover-upload {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  
  .cover-uploader {
    :deep(.el-upload) {
      border: 1px dashed #d9d9d9;
      border-radius: 6px;
      cursor: pointer;
      overflow: hidden;
      transition: border-color 0.3s;
      
      &:hover {
        border-color: #409eff;
      }
    }
  }
  
  .cover-preview {
    width: 100px;
    height: 140px;
  }
  
  .cover-placeholder {
    width: 100px;
    height: 140px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #8c939d;
    
    .el-icon {
      font-size: 24px;
      margin-bottom: 8px;
    }
    
    span {
      font-size: 12px;
    }
  }
  
  .cover-url-input {
    flex: 1;
  }
}

.audio-upload {
  display: flex;
  align-items: center;
}

.audio-preview {
  margin-top: 8px;
}
</style>
