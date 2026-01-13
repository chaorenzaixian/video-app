<template>
  <div class="icon-ads-page">
    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-row" v-if="stats">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ stats.total_ads }}</div>
          <div class="stat-label">总广告数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card active">
          <div class="stat-value">{{ stats.active_ads }}</div>
          <div class="stat-label">启用中</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card clicks">
          <div class="stat-value">{{ formatNumber(stats.total_clicks) }}</div>
          <div class="stat-label">总点击</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card ctr">
          <div class="stat-value">{{ stats.avg_ctr }}%</div>
          <div class="stat-label">平均点击率</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>图标广告位管理</span>
          <div class="header-actions">
            <el-button @click="fetchStats" :loading="statsLoading">
              <el-icon><DataAnalysis /></el-icon> 刷新统计
            </el-button>
            <el-button type="primary" @click="initAds" :loading="initLoading">
              <el-icon><Refresh /></el-icon> 初始化默认数据
            </el-button>
            <el-button type="success" @click="showAddDialog">
              <el-icon><Plus /></el-icon> 新增广告位
            </el-button>
          </div>
        </div>
      </template>

      <!-- 广告位列表 - 支持拖拽排序 -->
      <el-table 
        :data="ads" 
        v-loading="loading" 
        stripe 
        row-key="id"
        @row-drop="handleDrop"
      >
        <el-table-column label="拖拽" width="60">
          <template #default>
            <el-icon class="drag-handle" style="cursor: move;"><Rank /></el-icon>
          </template>
        </el-table-column>
        
        <el-table-column label="排序" width="70" prop="sort_order" />
        
        <el-table-column label="预览" width="80">
          <template #default="{ row }">
            <div class="ad-preview">
              <img v-if="row.image" :src="row.image" />
              <span v-else>{{ row.icon }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="名称" prop="name" width="120" />
        
        <el-table-column label="跳转链接" prop="link" min-width="180" show-overflow-tooltip />
        
        <el-table-column label="展示" width="90" sortable>
          <template #default="{ row }">
            <span class="stat-num">{{ formatNumber(row.impression_count || 0) }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="点击" width="90" sortable>
          <template #default="{ row }">
            <span class="stat-num clicks">{{ formatNumber(row.click_count || 0) }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="点击率" width="90">
          <template #default="{ row }">
            <span class="stat-num ctr">{{ calcCTR(row) }}%</span>
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="70">
          <template #default="{ row }">
            <el-switch 
              v-model="row.is_active" 
              @change="updateAdStatus(row)"
              size="small"
            />
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="editAd(row)">编辑</el-button>
            <el-button link type="success" @click="copyAd(row)" :loading="row._copying">复制</el-button>
            <el-popconfirm title="确定删除这个广告位吗？" @confirm="deleteAd(row.id)">
              <template #reference>
                <el-button link type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 保存排序按钮 -->
      <div class="sort-actions" v-if="sortChanged">
        <el-button type="primary" @click="saveSortOrder" :loading="sortSaving">
          保存排序
        </el-button>
        <el-button @click="resetSort">取消</el-button>
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? '编辑广告位' : '新增广告位'"
      width="600px"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="显示在图标下方" />
        </el-form-item>
        
        <el-form-item label="图标">
          <el-input v-model="form.icon" placeholder="emoji图标，如 🔥" />
          <div class="form-tip">支持emoji表情，如：🔥 💊 🎰 🌊 🅿 🏝 ❌ ⚡ 🎀 🔒</div>
        </el-form-item>
        
        <el-form-item label="图片">
          <div class="upload-section">
            <el-upload
              class="image-uploader"
              :action="uploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="handleUploadSuccess"
              :on-error="handleUploadError"
              :before-upload="beforeUpload"
              accept="image/*"
            >
              <div v-if="form.image" class="uploaded-image">
                <img :src="form.image" />
                <div class="image-actions">
                  <el-icon @click.stop="form.image = ''"><Delete /></el-icon>
                </div>
              </div>
              <div v-else class="upload-placeholder">
                <el-icon><Plus /></el-icon>
                <span>上传图片</span>
              </div>
            </el-upload>
            <div class="form-tip">建议尺寸：200x200，支持PNG/JPG/WEBP，图片优先于图标显示</div>
          </div>
        </el-form-item>
        
        <el-form-item label="图片链接">
          <el-input v-model="form.image" placeholder="直接输入图片URL地址" clearable />
          <div class="form-tip">可直接粘贴图片链接，与上传二选一</div>
        </el-form-item>
        
        <el-form-item label="跳转链接">
          <el-input v-model="form.link" placeholder="点击跳转的URL" />
        </el-form-item>
        
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="1" :max="100" />
          <div class="form-tip">数字越小越靠前</div>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      
      <!-- 预览 -->
      <div class="preview-section">
        <div class="preview-title">预览效果</div>
        <div class="preview-wrapper">
          <div class="ad-preview-large">
            <img v-if="form.image" :src="form.image" />
            <span v-else class="preview-icon">{{ form.icon || '?' }}</span>
          </div>
          <span class="preview-name">{{ form.name || '名称' }}</span>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveAd" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete, DataAnalysis, Rank } from '@element-plus/icons-vue'
import Sortable from 'sortablejs'
import api from '@/utils/api'

const loading = ref(false)
const initLoading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const ads = ref([])
const originalAds = ref([])
const sortChanged = ref(false)
const sortSaving = ref(false)
const stats = ref(null)
const statsLoading = ref(false)

// 上传配置
const uploadUrl = '/api/v1/ads/upload/image'
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`
}))

const form = reactive({
  id: null,
  name: '',
  icon: '',
  image: '',
  link: '',
  sort_order: 1,
  is_active: true
})

// 格式化数字
const formatNumber = (num) => {
  if (num >= 10000) return (num / 10000).toFixed(1) + 'w'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k'
  return num
}

// 计算点击率
const calcCTR = (row) => {
  const impressions = row.impression_count || 0
  const clicks = row.click_count || 0
  if (impressions === 0) return '0.00'
  return ((clicks / impressions) * 100).toFixed(2)
}

const fetchAds = async () => {
  loading.value = true
  try {
    const res = await api.get('/ads/icons/admin')
    ads.value = (res.data || res || []).map(ad => ({ ...ad, _copying: false }))
    originalAds.value = JSON.parse(JSON.stringify(ads.value))
    sortChanged.value = false
    // 初始化拖拽
    initSortable()
  } catch (error) {
    ads.value = []
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  statsLoading.value = true
  try {
    const res = await api.get('/ads/icons/stats')
    stats.value = res.data || res
  } catch (error) {
    console.error('获取统计失败', error)
  } finally {
    statsLoading.value = false
  }
}

// 初始化拖拽排序
const initSortable = () => {
  const table = document.querySelector('.el-table__body-wrapper tbody')
  if (table) {
    Sortable.create(table, {
      handle: '.drag-handle',
      animation: 150,
      onEnd: ({ oldIndex, newIndex }) => {
        if (oldIndex !== newIndex) {
          const movedItem = ads.value.splice(oldIndex, 1)[0]
          ads.value.splice(newIndex, 0, movedItem)
          // 更新排序值
          ads.value.forEach((ad, index) => {
            ad.sort_order = index + 1
          })
          sortChanged.value = true
        }
      }
    })
  }
}

// 保存排序
const saveSortOrder = async () => {
  sortSaving.value = true
  try {
    const items = ads.value.map(ad => ({
      id: ad.id,
      sort_order: ad.sort_order
    }))
    await api.put('/ads/icons/sort', { items })
    ElMessage.success('排序保存成功')
    originalAds.value = JSON.parse(JSON.stringify(ads.value))
    sortChanged.value = false
  } catch (error) {
    ElMessage.error('保存排序失败')
  } finally {
    sortSaving.value = false
  }
}

// 重置排序
const resetSort = () => {
  ads.value = JSON.parse(JSON.stringify(originalAds.value))
  sortChanged.value = false
}

// 复制广告位
const copyAd = async (row) => {
  row._copying = true
  try {
    await api.post(`/ads/icons/${row.id}/copy`)
    ElMessage.success('复制成功')
    fetchAds()
    fetchStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '复制失败')
  } finally {
    row._copying = false
  }
}

const initAds = async () => {
  initLoading.value = true
  try {
    await api.post('/ads/icons/init')
    ElMessage.success('初始化成功')
    fetchAds()
    fetchStats()
  } catch (error) {
    ElMessage.warning(error.response?.data?.detail || '初始化失败')
  } finally {
    initLoading.value = false
  }
}

const showAddDialog = () => {
  isEdit.value = false
  Object.assign(form, {
    id: null,
    name: '',
    icon: '🔥',
    image: '',
    link: '',
    sort_order: ads.value.length + 1,
    is_active: true
  })
  dialogVisible.value = true
}

const editAd = (row) => {
  isEdit.value = true
  Object.assign(form, {
    id: row.id,
    name: row.name,
    icon: row.icon || '',
    image: row.image || '',
    link: row.link || '',
    sort_order: row.sort_order || 1,
    is_active: row.is_active !== false
  })
  dialogVisible.value = true
}

// 上传前验证
const beforeUpload = (file) => {
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

// 上传成功
const handleUploadSuccess = (response) => {
  if (response.url) {
    form.image = response.url
    ElMessage.success('上传成功')
  } else {
    ElMessage.error('上传失败')
  }
}

// 上传失败
const handleUploadError = () => {
  ElMessage.error('上传失败，请重试')
}

const saveAd = async () => {
  if (!form.name) {
    ElMessage.warning('请输入名称')
    return
  }
  
  saving.value = true
  try {
    const data = {
      name: form.name,
      icon: form.icon,
      image: form.image,
      link: form.link,
      sort_order: form.sort_order,
      is_active: form.is_active
    }
    
    if (isEdit.value) {
      await api.put(`/ads/icons/${form.id}`, data)
      ElMessage.success('更新成功')
    } else {
      await api.post('/ads/icons', data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchAds()
    fetchStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const updateAdStatus = async (row) => {
  try {
    await api.put(`/ads/icons/${row.id}`, { is_active: row.is_active })
    ElMessage.success(row.is_active ? '已启用' : '已禁用')
    fetchStats()
  } catch (error) {
    row.is_active = !row.is_active
    ElMessage.error('操作失败')
  }
}

const deleteAd = async (id) => {
  try {
    await api.delete(`/ads/icons/${id}`)
    ElMessage.success('删除成功')
    fetchAds()
    fetchStats()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  fetchAds()
  fetchStats()
})
</script>

<style lang="scss" scoped>
.icon-ads-page {
  .stats-row {
    margin-bottom: 20px;
    
    .stat-card {
      text-align: center;
      
      .stat-value {
        font-size: 28px;
        font-weight: bold;
        color: #303133;
      }
      
      .stat-label {
        font-size: 14px;
        color: #909399;
        margin-top: 8px;
      }
      
      &.active .stat-value { color: #67c23a; }
      &.clicks .stat-value { color: #409eff; }
      &.ctr .stat-value { color: #e6a23c; }
    }
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .header-actions {
      display: flex;
      gap: 12px;
    }
  }
  
  .stat-num {
    font-weight: 500;
    &.clicks { color: #409eff; }
    &.ctr { color: #e6a23c; }
  }
  
  .ad-preview {
    width: 50px;
    height: 50px;
    border-radius: 10px;
    display: flex;
    justify-content: center;
    align-items: center;
    position: relative;
    overflow: hidden;
    background: #f5f5f5;
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    
    span {
      font-size: 24px;
    }
  }
  
  .sort-actions {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #eee;
    display: flex;
    gap: 12px;
  }
  
  .form-tip {
    font-size: 12px;
    color: #999;
    margin-top: 5px;
  }
  
  .upload-section {
    width: 100%;
    
    .image-uploader {
      :deep(.el-upload) {
        width: 120px;
        height: 120px;
        border: 1px dashed #d9d9d9;
        border-radius: 8px;
        cursor: pointer;
        overflow: hidden;
        transition: border-color 0.3s;
        
        &:hover {
          border-color: #409eff;
        }
      }
    }
    
    .uploaded-image {
      width: 120px;
      height: 120px;
      position: relative;
      
      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
      
      .image-actions {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        opacity: 0;
        transition: opacity 0.3s;
        
        .el-icon {
          font-size: 24px;
          color: #fff;
          cursor: pointer;
          
          &:hover {
            color: #f56c6c;
          }
        }
      }
      
      &:hover .image-actions {
        opacity: 1;
      }
    }
    
    .upload-placeholder {
      width: 120px;
      height: 120px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      color: #999;
      
      .el-icon {
        font-size: 28px;
        margin-bottom: 8px;
      }
      
      span {
        font-size: 12px;
      }
    }
  }
  
  .preview-section {
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid #eee;
    
    .preview-title {
      font-size: 14px;
      color: #666;
      margin-bottom: 15px;
    }
    
    .preview-wrapper {
      display: flex;
      flex-direction: column;
      align-items: center;
      width: fit-content;
      
      .ad-preview-large {
        width: 64px;
        height: 64px;
        border-radius: 14px;
        display: flex;
        justify-content: center;
        align-items: center;
        position: relative;
        overflow: hidden;
        background: #f5f5f5;
        
        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
        
        .preview-icon {
          font-size: 28px;
        }
      }
      
      .preview-name {
        margin-top: 8px;
        font-size: 12px;
        color: #333;
      }
    }
  }
}
</style>
