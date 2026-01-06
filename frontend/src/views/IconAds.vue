<template>
  <div class="icon-ads-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>图标广告位管理</span>
          <div class="header-actions">
            <el-button type="primary" @click="initAds" :loading="initLoading">
              <el-icon><Refresh /></el-icon> 初始化默认数据
            </el-button>
            <el-button type="success" @click="showAddDialog">
              <el-icon><Plus /></el-icon> 新增广告位
            </el-button>
          </div>
        </div>
      </template>

      <!-- 广告位列表 -->
      <el-table :data="sortedAds" v-loading="loading" stripe>
        <el-table-column label="排序" width="80" prop="sort_order" sortable />
        
        <el-table-column label="预览" width="100">
          <template #default="{ row }">
            <div 
              class="ad-preview" 
              :style="{ background: row.bg }"
            >
              <img v-if="row.image" :src="row.image" />
              <span v-else>{{ row.icon }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="名称" prop="name" width="120" />
        
        <el-table-column label="图标" prop="icon" width="80" />
        
        <el-table-column label="跳转链接" prop="link" min-width="200" show-overflow-tooltip />
        
        <el-table-column label="点击量" prop="click_count" width="80" />
        
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-switch 
              v-model="row.is_active" 
              @change="updateAdStatus(row)"
              size="small"
            />
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="editAd(row)">编辑</el-button>
            <el-popconfirm title="确定删除这个广告位吗？" @confirm="deleteAd(row.id)">
              <template #reference>
                <el-button link type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
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
        
        <el-form-item label="图片URL">
          <el-input v-model="form.image" placeholder="图片链接（优先于图标）" />
        </el-form-item>
        
        <el-form-item label="背景色" required>
          <el-input v-model="form.bg" placeholder="CSS渐变色" />
          <div class="color-presets">
            <span 
              v-for="color in colorPresets" 
              :key="color.value"
              class="color-item"
              :style="{ background: color.value }"
              @click="form.bg = color.value"
              :title="color.name"
            ></span>
          </div>
        </el-form-item>
        
        <el-form-item label="跳转链接">
          <el-input v-model="form.link" placeholder="点击跳转的URL" />
        </el-form-item>
        
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="1" :max="10" />
          <div class="form-tip">1-10，数字越小越靠前</div>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      
      <!-- 预览 -->
      <div class="preview-section">
        <div class="preview-title">预览效果</div>
        <div class="preview-wrapper">
          <div class="ad-preview-large" :style="{ background: form.bg }">
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
import api from '@/utils/api'

const loading = ref(false)
const initLoading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const ads = ref([])

// 按排序字段排序
const sortedAds = computed(() => {
  return [...ads.value].sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
})

const form = reactive({
  id: null,
  name: '',
  icon: '',
  image: '',
  bg: 'linear-gradient(135deg, #667eea, #764ba2)',
  link: '',
  sort_order: 1,
  is_active: true
})

const colorPresets = [
  { name: '红色', value: 'linear-gradient(135deg, #ff6b6b, #ee5a24)' },
  { name: '紫色', value: 'linear-gradient(135deg, #a55eea, #8854d0)' },
  { name: '金色', value: 'linear-gradient(135deg, #fed330, #f7b731)' },
  { name: '蓝色', value: 'linear-gradient(135deg, #45aaf2, #2d98da)' },
  { name: '粉色', value: 'linear-gradient(135deg, #ff9ff3, #f368e0)' },
  { name: '青色', value: 'linear-gradient(135deg, #00d2d3, #01a3a4)' },
  { name: '橙色', value: 'linear-gradient(135deg, #ffa502, #ff7f50)' },
  { name: '绿色', value: 'linear-gradient(135deg, #43e97b, #38f9d7)' }
]

const fetchAds = async () => {
  loading.value = true
  try {
    const res = await api.get('/ads/icons/admin')
    ads.value = res.data || res || []
  } catch (error) {
    // 如果没有数据，显示空列表
    ads.value = []
  } finally {
    loading.value = false
  }
}

const initAds = async () => {
  initLoading.value = true
  try {
    await api.post('/ads/icons/init')
    ElMessage.success('初始化成功')
    fetchAds()
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
    bg: 'linear-gradient(135deg, #667eea, #764ba2)',
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
    bg: row.bg,
    link: row.link || '',
    sort_order: row.sort_order || 1,
    is_active: row.is_active !== false
  })
  dialogVisible.value = true
}

const saveAd = async () => {
  if (!form.name) {
    ElMessage.warning('请输入名称')
    return
  }
  
  saving.value = true
  try {
    if (isEdit.value) {
      await api.put(`/ads/icons/${form.id}`, form)
      ElMessage.success('更新成功')
    } else {
      await api.post('/ads/icons', form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchAds()
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
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  fetchAds()
})
</script>

<style lang="scss" scoped>
.icon-ads-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .header-actions {
      display: flex;
      gap: 12px;
    }
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
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    
    span {
      font-size: 24px;
    }
  }
  
  .form-tip {
    font-size: 12px;
    color: #999;
    margin-top: 5px;
  }
  
  .color-presets {
    display: flex;
    gap: 8px;
    margin-top: 8px;
    flex-wrap: wrap;
    
    .color-item {
      width: 30px;
      height: 30px;
      border-radius: 6px;
      cursor: pointer;
      transition: transform 0.2s;
      
      &:hover {
        transform: scale(1.1);
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


