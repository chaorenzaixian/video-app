<template>
  <div class="gallery-manage">
    <el-card class="category-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>图集分类</span>
          <el-button type="primary" size="small" @click="showCategoryDialog()">
            <el-icon><Plus /></el-icon>添加分类
          </el-button>
        </div>
      </template>
      <el-table :data="categories" size="small">
        <el-table-column prop="name" label="分类名称" />
        <el-table-column prop="gallery_count" label="图集数" width="80" />
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
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
            <el-select v-model="filters.category_id" placeholder="选择分类" clearable style="width: 150px">
              <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
            <el-input v-model="filters.keyword" placeholder="搜索标题" clearable style="width: 200px" />
            <el-button type="primary" @click="loadGalleries">搜索</el-button>
          </div>
          <el-button type="primary" @click="showGalleryDialog()">
            <el-icon><Plus /></el-icon>添加图集
          </el-button>
        </div>
      </template>

      <el-table :data="galleries" v-loading="loading">
        <el-table-column label="封面" width="100">
          <template #default="{ row }">
            <el-image :src="row.cover" style="width: 60px; height: 80px" fit="cover" />
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="150" />
        <el-table-column prop="category_name" label="分类" width="100" />
        <el-table-column prop="image_count" label="图片数" width="80" />
        <el-table-column prop="view_count" label="浏览" width="80" />
        <el-table-column label="热门" width="80">
          <template #default="{ row }">
            <el-switch v-model="row.is_hot" @change="updateGallery(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="showGalleryDialog(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="deleteGallery(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, prev, pager, next"
        @current-change="loadGalleries"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </el-card>

    <!-- 分类弹窗 -->
    <el-dialog v-model="categoryDialogVisible" :title="categoryForm.id ? '编辑分类' : '添加分类'" width="400px">
      <el-form :model="categoryForm" label-width="80px">
        <el-form-item label="分类名称" required>
          <el-input v-model="categoryForm.name" />
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

    <!-- 图集弹窗 -->
    <el-dialog v-model="galleryDialogVisible" :title="galleryForm.id ? '编辑图集' : '添加图集'" width="800px">
      <el-form :model="galleryForm" label-width="80px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="标题" required>
              <el-input v-model="galleryForm.title" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分类">
              <el-select v-model="galleryForm.category_id" placeholder="选择分类" clearable style="width: 100%">
                <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 封面上传 -->
        <el-form-item label="封面" required>
          <div class="cover-upload">
            <el-upload
              class="cover-uploader"
              :action="uploadUrl"
              :headers="uploadHeaders"
              :data="{ subdir: 'gallery' }"
              :show-file-list="false"
              :on-success="handleCoverSuccess"
              :before-upload="beforeImageUpload"
              accept="image/*"
            >
              <el-image v-if="galleryForm.cover" :src="galleryForm.cover" class="cover-preview" fit="cover" />
              <div v-else class="cover-placeholder">
                <el-icon><Plus /></el-icon>
                <span>上传封面</span>
              </div>
            </el-upload>
            <div class="cover-url-input">
              <el-input v-model="galleryForm.cover" placeholder="或输入封面URL" clearable />
            </div>
          </div>
        </el-form-item>

        <!-- 图片列表上传 -->
        <el-form-item label="图片列表">
          <div class="images-upload-area">
            <el-upload
              ref="imagesUploadRef"
              class="images-uploader"
              :action="uploadMultipleUrl"
              :headers="uploadHeaders"
              :data="{ subdir: 'gallery' }"
              :file-list="imageFileList"
              :on-success="handleImagesSuccess"
              :on-remove="handleImageRemove"
              :before-upload="beforeImageUpload"
              :on-error="handleUploadError"
              multiple
              accept="image/*"
              list-type="picture-card"
            >
              <el-icon><Plus /></el-icon>
            </el-upload>
            <div class="images-url-input">
              <el-input 
                v-model="imagesText" 
                type="textarea" 
                :rows="3" 
                placeholder="或手动输入图片URL，每行一个" 
              />
              <el-button size="small" @click="parseImagesText" style="margin-top: 8px">解析URL</el-button>
            </div>
          </div>
          <div class="images-count">已添加 {{ galleryForm.images.length }} 张图片</div>
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="话数">
              <el-input-number v-model="galleryForm.chapter_count" :min="1" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="状态">
              <el-select v-model="galleryForm.status" style="width: 100%">
                <el-option label="连载中" value="ongoing" />
                <el-option label="已完结" value="completed" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="热门">
              <el-switch v-model="galleryForm.is_hot" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="简介">
          <el-input v-model="galleryForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="galleryDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveGallery" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'

const loading = ref(false)
const saving = ref(false)
const categories = ref([])
const galleries = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({ category_id: null, keyword: '' })

const categoryDialogVisible = ref(false)
const categoryForm = reactive({ id: null, name: '', sort_order: 0 })

const galleryDialogVisible = ref(false)
const galleryForm = reactive({
  id: null, category_id: null, title: '', cover: '', images: [],
  description: '', chapter_count: 1, status: 'ongoing', is_hot: false
})

const imagesUploadRef = ref(null)
const imageFileList = ref([])
const imagesText = ref('')

// 上传配置
const uploadUrl = computed(() => `${api.defaults.baseURL}/admin/gallery-novel/upload/image`)
const uploadMultipleUrl = computed(() => `${api.defaults.baseURL}/admin/gallery-novel/upload/image`)
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`
}))

onMounted(() => {
  loadCategories()
  loadGalleries()
})

async function loadCategories() {
  try {
    const { data } = await api.get('/admin/gallery-novel/gallery/categories')
    categories.value = data
  } catch (e) {
    ElMessage.error('加载分类失败')
  }
}

async function loadGalleries() {
  loading.value = true
  try {
    const params = { page: pagination.page, page_size: pagination.pageSize, ...filters }
    const { data } = await api.get('/admin/gallery-novel/galleries', { params })
    galleries.value = data.items
    pagination.total = data.total
  } catch (e) {
    ElMessage.error('加载图集失败')
  } finally {
    loading.value = false
  }
}

function showCategoryDialog(row = null) {
  if (row) {
    Object.assign(categoryForm, row)
  } else {
    Object.assign(categoryForm, { id: null, name: '', sort_order: 0 })
  }
  categoryDialogVisible.value = true
}

async function saveCategory() {
  if (!categoryForm.name) return ElMessage.warning('请输入分类名称')
  try {
    if (categoryForm.id) {
      await api.put(`/admin/gallery-novel/gallery/categories/${categoryForm.id}`, categoryForm)
    } else {
      await api.post('/admin/gallery-novel/gallery/categories', categoryForm)
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
    await api.delete(`/admin/gallery-novel/gallery/categories/${row.id}`)
    ElMessage.success('删除成功')
    loadCategories()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

function showGalleryDialog(row = null) {
  if (row) {
    Object.assign(galleryForm, row)
    // 初始化图片列表显示
    imageFileList.value = (row.images || []).map((url, idx) => ({
      name: `image_${idx}`,
      url: url
    }))
  } else {
    Object.assign(galleryForm, {
      id: null, category_id: null, title: '', cover: '', images: [],
      description: '', chapter_count: 1, status: 'ongoing', is_hot: false
    })
    imageFileList.value = []
  }
  imagesText.value = ''
  galleryDialogVisible.value = true
}

// 上传前验证
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
    galleryForm.cover = response.url
    ElMessage.success('封面上传成功')
  } else {
    ElMessage.error('上传失败')
  }
}

// 图片上传成功
function handleImagesSuccess(response, file, fileList) {
  if (response.url) {
    // 添加到图片列表
    if (!galleryForm.images.includes(response.url)) {
      galleryForm.images.push(response.url)
    }
    // 更新文件列表显示
    file.url = response.url
  }
}

// 移除图片
function handleImageRemove(file) {
  const url = file.url || file.response?.url
  if (url) {
    const idx = galleryForm.images.indexOf(url)
    if (idx > -1) {
      galleryForm.images.splice(idx, 1)
    }
  }
}

// 上传错误
function handleUploadError(error) {
  ElMessage.error('上传失败，请重试')
  console.error('Upload error:', error)
}

// 解析手动输入的URL
function parseImagesText() {
  if (!imagesText.value.trim()) return
  
  const urls = imagesText.value
    .split('\n')
    .map(s => s.trim())
    .filter(s => s && (s.startsWith('http') || s.startsWith('/')))
  
  urls.forEach(url => {
    if (!galleryForm.images.includes(url)) {
      galleryForm.images.push(url)
      imageFileList.value.push({ name: url.split('/').pop(), url })
    }
  })
  
  imagesText.value = ''
  ElMessage.success(`已添加 ${urls.length} 张图片`)
}

async function saveGallery() {
  if (!galleryForm.title || !galleryForm.cover) return ElMessage.warning('请填写标题和封面')
  
  saving.value = true
  try {
    if (galleryForm.id) {
      await api.put(`/admin/gallery-novel/galleries/${galleryForm.id}`, galleryForm)
    } else {
      await api.post('/admin/gallery-novel/galleries', galleryForm)
    }
    ElMessage.success('保存成功')
    galleryDialogVisible.value = false
    loadGalleries()
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function updateGallery(row) {
  try {
    await api.put(`/admin/gallery-novel/galleries/${row.id}`, { is_hot: row.is_hot })
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

async function deleteGallery(row) {
  await ElMessageBox.confirm('确定删除该图集？', '提示')
  try {
    await api.delete(`/admin/gallery-novel/galleries/${row.id}`)
    ElMessage.success('删除成功')
    loadGalleries()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}
</script>

<style lang="scss" scoped>
.gallery-manage {
  .category-card { margin-bottom: 20px; }
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    .filters { display: flex; gap: 10px; }
  }
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
    color: #8c939d;
    
    .el-icon {
      font-size: 28px;
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

.images-upload-area {
  display: flex;
  gap: 16px;
  
  .images-uploader {
    flex: 1;
    
    :deep(.el-upload-list--picture-card) {
      .el-upload-list__item {
        width: 100px;
        height: 100px;
      }
    }
    
    :deep(.el-upload--picture-card) {
      width: 100px;
      height: 100px;
    }
  }
  
  .images-url-input {
    width: 300px;
  }
}

.images-count {
  margin-top: 8px;
  color: #909399;
  font-size: 12px;
}
</style>
