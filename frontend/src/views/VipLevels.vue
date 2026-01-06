<template>
  <div class="vip-levels-page">
    <!-- VIP等级配置 -->
    <el-card class="level-card">
      <template #header>
        <div class="card-header">
          <span>VIP等级配置</span>
        </div>
      </template>
      
      <el-table :data="vipLevels" v-loading="loadingLevels" stripe>
        <el-table-column prop="level" label="等级" width="60" />
        <el-table-column label="图标" width="70">
          <template #default="{ row }">
            <img v-if="row.icon" :src="row.icon" class="level-icon" />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" width="120" />
        <el-table-column label="颜色" width="70">
          <template #default="{ row }">
            <div class="color-preview" :style="{ backgroundColor: row.color || '#FFD700' }"></div>
          </template>
        </el-table-column>
        <el-table-column label="折扣率" width="80">
          <template #default="{ row }">
            {{ row.discount === 0 ? '免费' : (row.discount * 100).toFixed(0) + '%' }}
          </template>
        </el-table-column>
        <el-table-column label="权益" width="180">
          <template #default="{ row }">
            <div class="benefits-tags">
              <el-tag v-if="row.ad_free" size="small" type="success">免广告</el-tag>
              <el-tag v-if="row.can_download" size="small" type="primary">可下载</el-tag>
              <el-tag v-if="row.priority_support" size="small" type="warning">优先客服</el-tag>
              <el-tag v-if="row.exclusive_content" size="small" type="danger">专属内容</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="120" />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button link type="primary" @click="editLevel(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- VIP用户列表 -->
    <el-card class="users-card">
      <template #header>
        <div class="card-header">
          <span>VIP用户管理</span>
          <div class="header-actions">
            <el-select v-model="filters.vip_level" placeholder="筛选等级" clearable style="width: 120px" @change="fetchVipUsers">
              <el-option v-for="level in vipLevels" :key="level.level" :label="level.name" :value="level.level" />
            </el-select>
            <el-select v-model="filters.is_active" placeholder="状态" clearable style="width: 100px" @change="fetchVipUsers">
              <el-option label="激活" :value="true" />
              <el-option label="过期" :value="false" />
            </el-select>
          </div>
        </div>
      </template>
      
      <el-table :data="vipUsers" v-loading="loadingUsers" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="用户" width="200">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :src="row.avatar || '/images/avatars/icon_avatar_1.png'" :size="32" />
              <div class="user-info">
                <span class="nickname">{{ row.nickname || row.username }}</span>
                <span class="username">@{{ row.username }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="VIP等级" width="150">
          <template #default="{ row }">
            <div class="level-cell">
              <img v-if="getLevelIcon(row.vip_level)" :src="getLevelIcon(row.vip_level)" class="level-icon-sm" />
              <span>{{ row.vip_level_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '激活' : '过期' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="到期时间" width="160">
          <template #default="{ row }">
            <span :class="{ 'expired': !row.is_active }">
              {{ formatDate(row.expire_date) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="total_days" label="累计天数" width="100" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button link type="primary" @click="editUserVip(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchVipUsers"
          @current-change="fetchVipUsers"
        />
      </div>
    </el-card>

    <!-- 编辑等级配置对话框 -->
    <el-dialog v-model="levelDialogVisible" title="编辑VIP等级" width="550px">
      <el-form :model="levelForm" label-width="100px">
        <el-divider content-position="left">基础信息</el-divider>
        <el-form-item label="等级">
          <el-input :value="'Level ' + levelForm.level" disabled />
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model="levelForm.name" />
        </el-form-item>
        <el-form-item label="图标URL">
          <el-input v-model="levelForm.icon" />
        </el-form-item>
        <el-form-item label="等级颜色">
          <el-color-picker v-model="levelForm.color" />
        </el-form-item>
        <el-form-item label="折扣率">
          <el-slider v-model="levelForm.discount" :min="0" :max="1" :step="0.05" :format-tooltip="val => val === 0 ? '免费' : (val * 100).toFixed(0) + '%'" />
          <span class="discount-hint">{{ levelForm.discount === 0 ? '免费' : (levelForm.discount * 100).toFixed(0) + '%' }}</span>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="levelForm.description" type="textarea" />
        </el-form-item>
        
        <el-divider content-position="left">权益配置</el-divider>
        <el-form-item label="免广告">
          <el-switch v-model="levelForm.ad_free" />
        </el-form-item>
        <el-form-item label="可下载">
          <el-switch v-model="levelForm.can_download" />
        </el-form-item>
        <el-form-item label="每日下载次数" v-if="levelForm.can_download">
          <el-input-number v-model="levelForm.daily_downloads" :min="0" :max="1000" />
        </el-form-item>
        <el-form-item label="优先客服">
          <el-switch v-model="levelForm.priority_support" />
        </el-form-item>
        <el-form-item label="专属内容">
          <el-switch v-model="levelForm.exclusive_content" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="levelDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveLevel" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 编辑用户VIP对话框 -->
    <el-dialog v-model="userVipDialogVisible" title="编辑用户VIP" width="450px">
      <el-form :model="userVipForm" label-width="100px">
        <el-form-item label="用户">
          <span>{{ userVipForm.nickname || userVipForm.username }} (@{{ userVipForm.username }})</span>
        </el-form-item>
        <el-form-item label="VIP等级">
          <el-select v-model="userVipForm.vip_level" style="width: 100%">
            <el-option v-for="level in vipLevels" :key="level.level" :label="level.name" :value="level.level" />
          </el-select>
        </el-form-item>
        <el-form-item label="有效期设置">
          <el-radio-group v-model="userVipForm.expire_type">
            <el-radio label="keep">保持不变</el-radio>
            <el-radio label="days">指定天数</el-radio>
            <el-radio label="forever">永久</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="userVipForm.expire_type === 'days'" label="天数">
          <el-input-number v-model="userVipForm.expire_days" :min="1" :max="3650" />
        </el-form-item>
        <el-form-item label="激活状态">
          <el-switch v-model="userVipForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="userVipDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveUserVip" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/utils/api'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'

const loadingLevels = ref(false)
const loadingUsers = ref(false)
const saving = ref(false)

const vipLevels = ref([])
const vipUsers = ref([])

const filters = reactive({
  vip_level: null,
  is_active: null
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 等级编辑
const levelDialogVisible = ref(false)
const levelForm = reactive({
  level: 0,
  name: '',
  icon: '',
  color: '#FFD700',
  discount: 1.0,
  description: '',
  // 权益配置
  can_download: false,
  daily_downloads: 0,
  ad_free: false,
  priority_support: false,
  exclusive_content: false
})

// 用户VIP编辑
const userVipDialogVisible = ref(false)
const userVipForm = reactive({
  user_id: 0,
  username: '',
  nickname: '',
  vip_level: 0,
  expire_type: 'keep',
  expire_days: 30,
  is_active: true
})

// 获取VIP等级配置
const fetchVipLevels = async () => {
  loadingLevels.value = true
  try {
    const res = await api.get('/admin/vip-levels')
    vipLevels.value = res.data || res || []
  } catch (e) {
    console.error('获取VIP等级失败', e)
  } finally {
    loadingLevels.value = false
  }
}

// 获取VIP用户列表
const fetchVipUsers = async () => {
  loadingUsers.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    if (filters.vip_level !== null) params.vip_level = filters.vip_level
    if (filters.is_active !== null) params.is_active = filters.is_active
    
    const res = await api.get('/admin/vip-users', { params })
    vipUsers.value = res.data || res || []
    // 假设后端返回的是列表，总数暂时用列表长度
    pagination.total = vipUsers.value.length
  } catch (e) {
    console.error('获取VIP用户失败', e)
  } finally {
    loadingUsers.value = false
  }
}

// 获取等级图标
const getLevelIcon = (level) => {
  const config = vipLevels.value.find(l => l.level === level)
  return config?.icon || ''
}

// 格式化日期
const formatDate = (date) => {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

// 编辑等级配置
const editLevel = (row) => {
  levelForm.level = row.level
  levelForm.name = row.name
  levelForm.icon = row.icon
  levelForm.color = row.color || '#FFD700'
  levelForm.discount = row.discount ?? 1.0
  levelForm.description = row.description
  // 权益配置
  levelForm.can_download = row.can_download ?? false
  levelForm.daily_downloads = row.daily_downloads ?? 0
  levelForm.ad_free = row.ad_free ?? false
  levelForm.priority_support = row.priority_support ?? false
  levelForm.exclusive_content = row.exclusive_content ?? false
  levelDialogVisible.value = true
}

// 保存等级配置
const saveLevel = async () => {
  saving.value = true
  try {
    await api.put(`/admin/vip-levels/${levelForm.level}`, {
      name: levelForm.name,
      icon: levelForm.icon,
      color: levelForm.color,
      discount: levelForm.discount,
      description: levelForm.description,
      // 权益配置
      can_download: levelForm.can_download,
      daily_downloads: levelForm.daily_downloads,
      ad_free: levelForm.ad_free,
      priority_support: levelForm.priority_support,
      exclusive_content: levelForm.exclusive_content
    })
    ElMessage.success('保存成功')
    levelDialogVisible.value = false
    fetchVipLevels()
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

// 编辑用户VIP
const editUserVip = (row) => {
  userVipForm.user_id = row.id
  userVipForm.username = row.username
  userVipForm.nickname = row.nickname
  userVipForm.vip_level = row.vip_level
  userVipForm.expire_type = 'keep'
  userVipForm.expire_days = 30
  userVipForm.is_active = row.is_active
  userVipDialogVisible.value = true
}

// 保存用户VIP
const saveUserVip = async () => {
  saving.value = true
  try {
    const data = {
      vip_level: userVipForm.vip_level,
      is_active: userVipForm.is_active
    }
    
    if (userVipForm.expire_type === 'days') {
      data.expire_days = userVipForm.expire_days
    } else if (userVipForm.expire_type === 'forever') {
      data.expire_days = 0  // 0表示永久
    }
    // keep 不传 expire_days
    
    await api.put(`/admin/users/${userVipForm.user_id}/vip`, data)
    ElMessage.success('保存成功')
    userVipDialogVisible.value = false
    fetchVipUsers()
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchVipLevels()
  fetchVipUsers()
})
</script>

<style lang="scss" scoped>
.vip-levels-page {
  .level-card {
    margin-bottom: 20px;
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .header-actions {
      display: flex;
      gap: 10px;
    }
  }
  
  .level-icon {
    height: 28px;
    width: auto;
  }
  
  .color-preview {
    width: 40px;
    height: 24px;
    border-radius: 4px;
    border: 1px solid #ddd;
  }
  
  .discount-hint {
    margin-left: 12px;
    color: #6366f1;
    font-weight: 600;
  }
  
  .level-icon-sm {
    height: 20px;
    width: auto;
    margin-right: 6px;
  }
  
  .user-cell {
    display: flex;
    align-items: center;
    gap: 10px;
    
    .user-info {
      display: flex;
      flex-direction: column;
      
      .nickname {
        font-weight: 500;
      }
      
      .username {
        font-size: 12px;
        color: #909399;
      }
    }
  }
  
  .level-cell {
    display: flex;
    align-items: center;
  }
  
  .benefits-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    
    .el-tag {
      font-size: 11px;
    }
  }
  
  .expired {
    color: #f56c6c;
  }
  
  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>

