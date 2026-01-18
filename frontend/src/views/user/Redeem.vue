<template>
  <div class="redeem-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.back()">
        <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
      </div>
      <h1 class="page-title">领取兑换</h1>
      <div class="header-right"></div>
    </header>

    <!-- 内容区域 -->
    <div class="content">
      <!-- 输入兑换码区域 -->
      <div class="input-section">
        <h2 class="section-title">输入兑换码</h2>
        <p class="section-desc">兑换码只能兑换一次</p>
        
        <div class="input-group">
          <label class="input-label">兑换码</label>
          <input 
            v-model="redeemCode" 
            type="text" 
            class="code-input" 
            placeholder="请输入兑换码（字母大写）"
            @input="redeemCode = redeemCode.toUpperCase()"
          />
        </div>
        
        <p class="tip-text">官方社群领取更多福利</p>
      </div>

      <!-- 兑换记录 -->
      <div class="records-section">
        <h2 class="section-title">兑换记录</h2>
        
        <div class="records-table">
          <div class="table-header">
            <span class="col">兑换码</span>
            <span class="col">兑换类型</span>
            <span class="col">兑换时间</span>
          </div>
          
          <div v-if="records.length > 0" class="table-body">
            <div v-for="record in records" :key="record.id" class="table-row">
              <span class="col">{{ record.code }}</span>
              <span class="col">{{ record.type }}</span>
              <span class="col">{{ record.time }}</span>
            </div>
          </div>
          
          <div v-else class="empty-records">
            <p>暂无兑换记录</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部兑换按钮 -->
    <div class="bottom-bar">
      <button class="redeem-btn" :disabled="!redeemCode || isLoading" @click="handleRedeem">
        {{ isLoading ? '兑换中...' : '立即兑换' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const redeemCode = ref('')
const isLoading = ref(false)
const records = ref([])

// 获取兑换记录
const fetchRecords = async () => {
  try {
    const res = await api.get('/redeem/records')
    records.value = res.data || res || []
  } catch (error) {
    // 404 表示功能未开放，静默处理
    if (error.response?.status !== 404) {
      console.error('获取兑换记录失败:', error)
    }
    records.value = []
  }
}

// 兑换
const handleRedeem = async () => {
  if (!redeemCode.value) {
    ElMessage.warning('请输入兑换码')
    return
  }
  
  isLoading.value = true
  try {
    const res = await api.post('/redeem/use', {
      code: redeemCode.value
    })
    
    ElMessage.success(res.message || '兑换成功')
    redeemCode.value = ''
    fetchRecords()
  } catch (error) {
    if (error.response?.status === 404) {
      ElMessage.warning('兑换功能暂未开放')
    } else {
      ElMessage.error(error.response?.data?.detail || '兑换失败，请检查兑换码是否正确')
    }
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchRecords()
})
</script>

<style lang="scss" scoped>
.redeem-page {
  min-height: 100vh;
  background: #0a0a0a;
  padding-bottom: calc(80px + env(safe-area-inset-bottom));
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: transparent;
  position: sticky;
  top: 0;
  z-index: 100;
  
  .back-btn {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    
    svg {
      width: 24px;
      height: 24px;
      color: #fff;
    }
  }
  
  .page-title {
    font-size: 16px;
    font-weight: 600;
    color: #fff;
    margin: 0;
  }
  
  .header-right {
    width: 32px;
  }
}

.content {
  padding: 16px;
}

.input-section {
  margin-bottom: 32px;
  
  .section-title {
    font-size: 24px;
    font-weight: 700;
    color: #fff;
    margin: 0 0 8px;
  }
  
  .section-desc {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.5);
    margin: 0 0 32px;
  }
  
  .input-group {
    display: flex;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    padding-bottom: 12px;
    margin-bottom: 12px;
    
    .input-label {
      font-size: 13px;
      color: #fff;
      margin-right: 16px;
      white-space: nowrap;
    }
    
    .code-input {
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      font-size: 13px;
      color: #fff;
      
      &::placeholder {
        color: rgba(255, 255, 255, 0.3);
      }
    }
  }
  
  .tip-text {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.5);
    margin: 0;
  }
}

.records-section {
  .section-title {
    font-size: 16px;
    font-weight: 600;
    color: #fff;
    margin: 0 0 16px;
  }
}

.records-table {
  background: #1a1a1a;
  border-radius: 8px;
  overflow: hidden;
  
  .table-header {
    display: flex;
    background: #222;
    padding: 12px 16px;
    
    .col {
      flex: 1;
      font-size: 13px;
      color: rgba(255, 255, 255, 0.7);
      text-align: center;
    }
  }
  
  .table-body {
    .table-row {
      display: flex;
      padding: 12px 16px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      
      &:last-child {
        border-bottom: none;
      }
      
      .col {
        flex: 1;
        font-size: 13px;
        color: #fff;
        text-align: center;
      }
    }
  }
  
  .empty-records {
    padding: 40px 16px;
    text-align: center;
    
    p {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.5);
      margin: 0;
    }
  }
}

.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  padding-bottom: calc(16px + env(safe-area-inset-bottom));
  background: #0a0a0a;
  
  .redeem-btn {
    width: 100%;
    height: 48px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    border: none;
    border-radius: 24px;
    font-size: 15px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    
    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    
    &:not(:disabled):active {
      transform: scale(0.98);
      opacity: 0.9;
    }
  }
}

// 响应式断点
@media (min-width: 768px) {
  .redeem-page {
    max-width: 600px;
    margin: 0 auto;
  }
  
  .page-header {
    max-width: 600px;
    left: 50%;
    transform: translateX(-50%);
  }
  
  .bottom-bar {
    max-width: 600px;
    left: 50%;
    transform: translateX(-50%);
    
    .redeem-btn {
      width: 60%;
      margin: 0 auto;
      display: block;
    }
  }
}

@media (min-width: 1024px) {
  .redeem-page {
    max-width: 700px;
  }
  
  .page-header {
    max-width: 700px;
  }
  
  .bottom-bar {
    max-width: 700px;
    
    .redeem-btn {
      width: 50%;
    }
  }
}

// 触摸设备优化
@media (hover: hover) {
  .redeem-btn:not(:disabled):hover {
    opacity: 0.9;
    transform: translateY(-1px);
  }
  
  .table-row:hover {
    background: rgba(255, 255, 255, 0.03);
  }
}
</style>



