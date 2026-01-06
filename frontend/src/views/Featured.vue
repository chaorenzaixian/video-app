<template>
  <div class="featured-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>推荐管理</span>
        </div>
      </template>
      
      <el-tabs v-model="activeTab">
        <!-- 视频推荐 -->
        <el-tab-pane label="视频推荐" name="videos">
          <div class="tab-header">
            <el-button type="primary" @click="showAddDialog = true">
              <el-icon><Plus /></el-icon>添加推荐视频
            </el-button>
          </div>
          
          <el-table :data="featuredVideos" v-loading="loading" stripe>
            <el-table-column label="封面" width="120">
              <template #default="{ row }">
                <el-image 
                  :src="getCoverUrl(row.cover_url)" 
                  fit="cover"
                  style="width: 100px; height: 56px; border-radius: 4px;"
                >
                  <template #error>
                    <div class="image-error">加载失败</div>
                  </template>
                </el-image>
              </template>
            </el-table-column>
            
            <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
            
            <el-table-column label="分类" width="100">
              <template #default="{ row }">
                {{ row.category_name || '-' }}
              </template>
            </el-table-column>
            
            <el-table-column label="时长" width="80">
              <template #default="{ row }">
                {{ formatDuration(row.duration) }}
              </template>
            </el-table-column>
            
            <el-table-column prop="view_count" label="播放" width="80" />
            
            <el-table-column label="VIP" width="60">
              <template #default="{ row }">
                <el-tag v-if="row.is_vip_only" type="warning" size="small">VIP</el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            
            <el-table-column label="上传时间" width="160">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-popconfirm 
                  title="确定要取消推荐吗？"
                  @confirm="removeFeatured(row)"
                >
                  <template #reference>
                    <el-button type="danger" size="small" link>取消推荐</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
          
          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="pagination.page"
              v-model:page-size="pagination.pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="pagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="fetchFeaturedVideos"
              @current-change="fetchFeaturedVideos"
            />
          </div>
        </el-tab-pane>
        
        <!-- 分类推荐 -->
        <el-tab-pane label="分类推荐" name="categories">
          <div class="category-featured">
            <p class="tip">选择要在首页显示的推荐分类（支持一级和二级分类）</p>
            
            <!-- 一级分类 -->
            <div class="category-section">
              <h4>一级分类</h4>
              <el-checkbox-group v-model="featuredCategoryIds" @change="saveFeaturedCategories">
                <el-checkbox 
                  v-for="cat in topCategories" 
                  :key="cat.id" 
                  :label="cat.id"
                >
                  {{ cat.name }}
                </el-checkbox>
              </el-checkbox-group>
            </div>
            
            <!-- 二级分类 -->
            <div class="category-section" v-for="parent in categoriesWithChildren" :key="parent.id">
              <h4>{{ parent.name }} - 二级分类</h4>
              <el-checkbox-group v-model="featuredCategoryIds" @change="saveFeaturedCategories">
                <el-checkbox 
                  v-for="child in parent.children" 
                  :key="child.id" 
                  :label="child.id"
                >
                  {{ child.name }}
                </el-checkbox>
              </el-checkbox-group>
            </div>
            
            <!-- 已选推荐分类 -->
            <div class="featured-summary" v-if="featuredCategoryNames.length > 0">
              <span class="label">当前推荐分类：</span>
              <el-tag 
                v-for="name in featuredCategoryNames" 
                :key="name"
                type="success"
                style="margin-right: 8px; margin-bottom: 8px;"
              >
                {{ name }}
              </el-tag>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
    
    <!-- 添加推荐视频对话框 -->
    <el-dialog v-model="showAddDialog" title="添加推荐视频" width="800px">
      <div class="search-bar">
        <el-input 
          v-model="searchKeyword" 
          placeholder="搜索视频标题..."
          clearable
          style="width: 300px"
          @keyup.enter="searchVideos"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button type="primary" @click="searchVideos">搜索</el-button>
      </div>
      
      <el-table :data="searchResults" v-loading="searchLoading" stripe style="margin-top: 16px;" max-height="400px">
        <el-table-column label="封面" width="100">
          <template #default="{ row }">
            <el-image 
              :src="getCoverUrl(row.cover_url)" 
              fit="cover"
              style="width: 80px; height: 45px; border-radius: 4px;"
            >
              <template #error>
                <div class="image-error">加载失败</div>
              </template>
            </el-image>
          </template>
        </el-table-column>
        
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        
        <el-table-column label="分类" width="100">
          <template #default="{ row }">
            {{ row.category_name || '-' }}
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_featured" type="success" size="small">已推荐</el-tag>
            <el-tag v-else type="info" size="small">未推荐</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button 
              v-if="!row.is_featured"
              type="primary" 
              size="small" 
              link
              @click="addFeatured(row)"
            >
              添加推荐
            </el-button>
            <span v-else class="text-muted">已推荐</span>
          </template>
        </el-table-column>
      </el-table>
      
      <template #footer>
        <el-button @click="showAddDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'
import dayjs from 'dayjs'

const activeTab = ref('videos')

// 已推荐视频列表
const featuredVideos = ref([])
const loading = ref(false)
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 添加推荐对话框
const showAddDialog = ref(false)
const searchKeyword = ref('')
const searchResults = ref([])
const searchLoading = ref(false)

// 分类数据
const categories = ref([])
const featuredCategoryIds = ref([])

// 一级分类
const topCategories = computed(() => {
  return categories.value.filter(cat => !cat.parent_id || cat.level === 1)
})

// 有子分类的一级分类
const categoriesWithChildren = computed(() => {
  return topCategories.value.filter(cat => cat.children && cat.children.length > 0)
})

// 已选推荐分类名称
const featuredCategoryNames = computed(() => {
  const names = []
  const findName = (list) => {
    for (const cat of list) {
      if (featuredCategoryIds.value.includes(cat.id)) {
        names.push(cat.name)
      }
      if (cat.children) {
        findName(cat.children)
      }
    }
  }
  findName(categories.value)
  return names
})

// 获取封面URL
const getCoverUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `${import.meta.env.VITE_API_BASE_URL || ''}${url}`
}

// 格式化时长
const formatDuration = (seconds) => {
  if (!seconds) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 格式化日期
const formatDate = (date) => {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

// 获取已推荐视频列表
const fetchFeaturedVideos = async () => {
  loading.value = true
  try {
    const res = await api.get('/admin/videos', {
      params: {
        page: pagination.page,
        page_size: pagination.pageSize,
        is_featured: true
      }
    })
    featuredVideos.value = res.data.items || []
    pagination.total = res.data.total || 0
  } catch (error) {
    console.error('获取推荐视频失败:', error)
    ElMessage.error('获取推荐视频失败')
  } finally {
    loading.value = false
  }
}

// 搜索视频
const searchVideos = async () => {
  searchLoading.value = true
  try {
    const params = { page: 1, page_size: 20 }
    if (searchKeyword.value.trim()) {
      params.search = searchKeyword.value
    }
    const res = await api.get('/admin/videos', { params })
    searchResults.value = res.data.items || []
  } catch (error) {
    console.error('搜索视频失败:', error)
    ElMessage.error('搜索视频失败')
  } finally {
    searchLoading.value = false
  }
}

// 添加推荐
const addFeatured = async (video) => {
  try {
    await api.put(`/admin/videos/${video.id}`, { is_featured: true })
    ElMessage.success('添加推荐成功')
    video.is_featured = true
    fetchFeaturedVideos()
  } catch (error) {
    console.error('添加推荐失败:', error)
    ElMessage.error('添加推荐失败')
  }
}

// 取消推荐
const removeFeatured = async (video) => {
  try {
    await api.put(`/admin/videos/${video.id}`, { is_featured: false })
    ElMessage.success('取消推荐成功')
    fetchFeaturedVideos()
  } catch (error) {
    console.error('取消推荐失败:', error)
    ElMessage.error('取消推荐失败')
  }
}

// 获取分类列表
const fetchCategories = async () => {
  try {
    const res = await api.get('/videos/categories')
    categories.value = res.data || []
    // 提取已推荐的分类ID
    extractFeaturedIds(categories.value)
  } catch (error) {
    console.error('获取分类失败:', error)
  }
}

// 提取已推荐的分类ID
const extractFeaturedIds = (list) => {
  for (const cat of list) {
    if (cat.is_featured) {
      featuredCategoryIds.value.push(cat.id)
    }
    if (cat.children) {
      extractFeaturedIds(cat.children)
    }
  }
}

// 保存推荐分类
const saveFeaturedCategories = async () => {
  try {
    await api.post('/admin/categories/featured', {
      category_ids: featuredCategoryIds.value
    })
    ElMessage.success('保存成功')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  }
}

onMounted(() => {
  fetchFeaturedVideos()
  fetchCategories()
})
</script>

<style lang="scss" scoped>
.featured-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tab-header {
  margin-bottom: 16px;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.search-bar {
  display: flex;
  gap: 12px;
  align-items: center;
}

.image-error {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  color: #999;
  font-size: 12px;
}

.text-muted {
  color: #999;
  font-size: 12px;
}

.category-featured {
  .tip {
    color: #666;
    margin-bottom: 20px;
  }
  
  .category-section {
    margin-bottom: 24px;
    
    h4 {
      margin-bottom: 12px;
      color: #333;
      font-size: 14px;
      border-left: 3px solid #409eff;
      padding-left: 8px;
    }
    
    .el-checkbox {
      margin-right: 20px;
      margin-bottom: 8px;
    }
  }
  
  .featured-summary {
    margin-top: 24px;
    padding: 16px;
    background: #f5f7fa;
    border-radius: 8px;
    
    .label {
      font-weight: 500;
      margin-right: 12px;
    }
  }
}
</style>
