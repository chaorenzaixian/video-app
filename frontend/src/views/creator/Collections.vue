<template>
  <div class="collections-page">
    <div class="nav-header">
      <button class="back-btn" @click="$router.push('/creator')">‹</button>
      <h1>视频合集</h1>
      <button class="add-btn" @click="showCreateModal = true">+创建</button>
    </div>

    <!-- 合集列表 -->
    <div class="collections-list">
      <div v-for="col in collections" :key="col.id" class="collection-item">
        <div class="collection-cover">
          <img :src="col.cover_image || '/images/default-collection.webp'" alt="">
          <span class="video-count">{{ col.total_videos }}集</span>
        </div>
        <div class="collection-info">
          <h3>{{ col.title }}</h3>
          <div class="collection-stats">
            <span>👁 {{ col.view_count }}</span>
            <span>📥 {{ col.subscribe_count }}</span>
            <span v-if="col.pay_type !== 'free'">💰 {{ col.collection_price }}币</span>
          </div>
          <div class="collection-status">
            <span :class="col.status">{{ getStatusText(col.status) }}</span>
            <span v-if="col.is_completed" class="completed">已完结</span>
          </div>
        </div>
        <button class="manage-btn" @click="manageCollection(col)">管理</button>
      </div>

      <div v-if="collections.length === 0" class="empty-state">
        <span>📚</span>
        <p>暂无视频合集</p>
        <button @click="showCreateModal = true">创建合集</button>
      </div>
    </div>

    <!-- 创建合集弹窗 -->
    <div v-if="showCreateModal" class="create-modal" @click.self="showCreateModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <span>创建合集</span>
          <button @click="showCreateModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>合集标题 *</label>
            <input v-model="createForm.title" placeholder="请输入合集标题">
          </div>
          <div class="form-group">
            <label>合集简介</label>
            <textarea v-model="createForm.description" placeholder="介绍一下这个合集" rows="3"></textarea>
          </div>
          <div class="form-group">
            <label>付费设置</label>
            <div class="pay-options">
              <label :class="{ active: createForm.pay_type === 'free' }">
                <input type="radio" v-model="createForm.pay_type" value="free">
                <span>免费</span>
              </label>
              <label :class="{ active: createForm.pay_type === 'coins' }">
                <input type="radio" v-model="createForm.pay_type" value="coins">
                <span>付费</span>
              </label>
            </div>
          </div>
          <div class="form-group" v-if="createForm.pay_type === 'coins'">
            <label>合集价格(金币)</label>
            <input type="number" v-model.number="createForm.collection_price" placeholder="购买整个合集的价格">
          </div>
          <div class="form-group" v-if="createForm.pay_type === 'coins'">
            <label>单集价格(金币)</label>
            <input type="number" v-model.number="createForm.single_video_price" placeholder="购买单集的价格">
          </div>
        </div>
        <div class="modal-footer">
          <button class="cancel-btn" @click="showCreateModal = false">取消</button>
          <button class="submit-btn" @click="handleCreate" :disabled="isCreating">
            {{ isCreating ? '创建中...' : '创建' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const router = useRouter()
const collections = ref([])
const showCreateModal = ref(false)
const isCreating = ref(false)

const createForm = ref({
  title: '',
  description: '',
  pay_type: 'free',
  collection_price: 0,
  single_video_price: 0
})

const getStatusText = (status) => {
  const texts = {
    'draft': '草稿',
    'published': '已发布',
    'hidden': '已隐藏'
  }
  return texts[status] || status
}

const fetchCollections = async () => {
  try {
    const res = await api.get('/creator/collections')
    collections.value = res.data
  } catch (error) {
    console.error('获取合集失败:', error)
  }
}

const handleCreate = async () => {
  if (!createForm.value.title) {
    ElMessage.warning('请输入合集标题')
    return
  }
  
  isCreating.value = true
  try {
    await api.post('/creator/collections', createForm.value)
    ElMessage.success('合集创建成功')
    showCreateModal.value = false
    await fetchCollections()
    createForm.value = { title: '', description: '', pay_type: 'free', collection_price: 0, single_video_price: 0 }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '创建失败')
  } finally {
    isCreating.value = false
  }
}

const manageCollection = (col) => {
  // TODO: 跳转合集管理页面
  ElMessage.info('合集管理功能开发中')
}

onMounted(fetchCollections)
</script>

<style lang="scss" scoped>
.collections-page {
  min-height: 100vh;
  background: #0f0f1a;
}

.nav-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: rgba(0, 0, 0, 0.3);
  
  .back-btn {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.1);
    border: none;
    color: #fff;
    font-size: 24px;
  }
  
  h1 { font-size: 18px; color: #fff; margin: 0; }
  
  .add-btn {
    background: linear-gradient(135deg, #667eea, #764ba2);
    border: none;
    color: #fff;
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 14px;
  }
}

.collections-list {
  padding: 16px;
}

.collection-item {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: rgba(255,255,255,0.05);
  border-radius: 12px;
  margin-bottom: 12px;
  
  .collection-cover {
    width: 100px;
    height: 70px;
    border-radius: 8px;
    overflow: hidden;
    position: relative;
    flex-shrink: 0;
    
    img { width: 100%; height: 100%; object-fit: cover; }
    
    .video-count {
      position: absolute;
      bottom: 4px;
      right: 4px;
      background: rgba(0,0,0,0.7);
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 10px;
      color: #fff;
    }
  }
  
  .collection-info {
    flex: 1;
    min-width: 0;
    
    h3 {
      color: #fff;
      font-size: 14px;
      margin: 0 0 6px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .collection-stats {
      display: flex;
      gap: 10px;
      font-size: 12px;
      color: rgba(255,255,255,0.5);
    }
    
    .collection-status {
      margin-top: 6px;
      
      span {
        font-size: 11px;
        padding: 2px 6px;
        border-radius: 4px;
        margin-right: 6px;
        
        &.draft { background: #faad14; color: #000; }
        &.published { background: #52c41a; color: #fff; }
        &.completed { background: #667eea; color: #fff; }
      }
    }
  }
  
  .manage-btn {
    padding: 8px 16px;
    background: rgba(255,255,255,0.1);
    border: none;
    border-radius: 8px;
    color: #fff;
    font-size: 13px;
    align-self: center;
  }
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: rgba(255,255,255,0.5);
  
  span { font-size: 48px; }
  p { margin: 16px 0; }
  
  button {
    padding: 12px 24px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    border: none;
    border-radius: 8px;
    color: #fff;
  }
}

.create-modal {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 20px;
  
  .modal-content {
    width: 100%;
    max-width: 400px;
    background: #1a1a2e;
    border-radius: 16px;
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    padding: 16px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    
    span { color: #fff; font-size: 16px; font-weight: bold; }
    button { background: none; border: none; color: #fff; font-size: 24px; }
  }
  
  .modal-body {
    padding: 16px;
    
    .form-group {
      margin-bottom: 16px;
      
      label {
        display: block;
        color: rgba(255,255,255,0.8);
        font-size: 14px;
        margin-bottom: 8px;
      }
      
      input, textarea {
        width: 100%;
        padding: 12px;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px;
        color: #fff;
        font-size: 14px;
      }
    }
    
    .pay-options {
      display: flex;
      gap: 12px;
      
      label {
        flex: 1;
        padding: 12px;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px;
        text-align: center;
        cursor: pointer;
        margin: 0;
        
        input { display: none; }
        span { color: rgba(255,255,255,0.6); }
        
        &.active {
          border-color: #667eea;
          span { color: #667eea; }
        }
      }
    }
  }
  
  .modal-footer {
    display: flex;
    gap: 12px;
    padding: 16px;
    border-top: 1px solid rgba(255,255,255,0.1);
    
    .cancel-btn {
      flex: 1;
      padding: 12px;
      background: rgba(255,255,255,0.1);
      border: none;
      border-radius: 8px;
      color: #fff;
    }
    
    .submit-btn {
      flex: 2;
      padding: 12px;
      background: linear-gradient(135deg, #667eea, #764ba2);
      border: none;
      border-radius: 8px;
      color: #fff;
      
      &:disabled { opacity: 0.5; }
    }
  }
}
</style>

