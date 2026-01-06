<template>
  <div class="users-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
        </div>
      </template>
      
      <div class="filter-bar">
        <el-input v-model="filters.search" placeholder="搜索用户名/邮箱" clearable style="width: 250px" @keyup.enter="fetchUsers">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="filters.role" placeholder="角色" clearable style="width: 120px">
          <el-option label="普通用户" value="user" />
          <el-option label="VIP" value="vip" />
          <el-option label="管理员" value="admin" />
          <el-option label="游客" value="guest" />
        </el-select>
        <el-button @click="fetchUsers"><el-icon><Search /></el-icon>搜索</el-button>
      </div>
      
      <el-table :data="users" v-loading="loading" stripe style="width: 100%" size="small" border>
        <el-table-column prop="id" label="ID" width="60" align="center" />
        <el-table-column label="用户信息" width="150">
          <template #default="{ row }">
            <div class="user-cell">
              <div class="username">
                {{ row.username }}
                <el-tag v-if="row.is_guest" type="info" size="small">游客</el-tag>
              </div>
              <div class="nickname">{{ row.nickname || '-' }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120" align="center">
          <template #default="{ row }">
            <div class="status-cell">
            <el-tag :type="getRoleType(row.role)" size="small">{{ getRoleText(row.role) }}</el-tag>
              <el-tag v-if="row.vip_level > 0" :type="getVipLevelType(row.vip_level)" size="small">
                {{ row.vip_level_name || getVipLevelName(row.vip_level) }}
              </el-tag>
              <el-tag v-else-if="row.is_vip" type="warning" size="small">VIP</el-tag>
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="VIP到期" width="140" align="center">
          <template #default="{ row }">
            <template v-if="row.vip_expire_date">
              <span :class="{ 'text-danger': isExpired(row.vip_expire_date), 'text-success': !isExpired(row.vip_expire_date) }">
                {{ formatDate(row.vip_expire_date) }}
              </span>
            </template>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="注册IP / 归属地" width="160">
          <template #default="{ row }">
            <div v-if="row.register_ip" class="ip-cell">
              <div class="ip">{{ row.register_ip }}</div>
              <div class="location">{{ row.register_ip_location || '-' }}</div>
            </div>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="登录IP / 归属地" width="160">
          <template #default="{ row }">
            <div v-if="row.last_login_ip" class="ip-cell">
              <div class="ip">{{ row.last_login_ip }}</div>
              <div class="location">{{ row.last_login_ip_location || '-' }}</div>
            </div>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="注册时间" width="140" align="center">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="最近登录" width="140" align="center">
          <template #default="{ row }">
            {{ formatDate(row.last_login) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button link type="warning" size="small" @click="openVipDialog(row)">VIP</el-button>
              <el-button link :type="row.is_active ? 'danger' : 'success'" size="small" @click="toggleStatus(row)">
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
              <el-popconfirm 
                title="确定删除该用户吗？" 
                confirm-button-text="确定"
                cancel-button-text="取消"
                @confirm="deleteUser(row)"
              >
                <template #reference>
                  <el-button link type="danger" size="small" :disabled="row.role === 'SUPER_ADMIN' || row.role === 'super_admin' || row.role === 'ADMIN' || row.role === 'admin'">删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize" :total="pagination.total" layout="total, prev, pager, next" @current-change="fetchUsers" />
      </div>
    </el-card>
    
    <!-- VIP管理弹窗 -->
    <el-dialog v-model="vipDialogVisible" title="VIP管理" width="500px">
      <div v-if="currentUser" class="vip-dialog-content">
        <div class="user-info-row">
          <span class="label">用户：</span>
          <span>{{ currentUser.username }} ({{ currentUser.nickname || '无昵称' }})</span>
        </div>
        <div class="user-info-row">
          <span class="label">当前状态：</span>
          <el-tag :type="currentUser.is_vip ? 'warning' : 'info'" size="small">
            {{ currentUser.is_vip ? 'VIP' : '普通用户' }}
          </el-tag>
        </div>
        <div class="user-info-row" v-if="currentUser.vip_level > 0">
          <span class="label">VIP等级：</span>
          <el-tag :type="getVipLevelType(currentUser.vip_level)" size="small">
            {{ currentUser.vip_level_name || getVipLevelName(currentUser.vip_level) }}
          </el-tag>
        </div>
        <div class="user-info-row" v-if="currentUser.vip_expire_date">
          <span class="label">到期时间：</span>
          <span :class="{ 'text-danger': isExpired(currentUser.vip_expire_date) }">
            {{ formatTime(currentUser.vip_expire_date) }}
            <span v-if="isExpired(currentUser.vip_expire_date)">(已过期)</span>
          </span>
        </div>
        
        <el-divider />
        
        <el-form :model="vipForm" label-width="100px">
          <el-form-item label="VIP等级">
            <el-select v-model="vipForm.vip_level" placeholder="选择VIP等级" style="width: 100%">
              <el-option 
                v-for="level in vipLevels" 
                :key="level.level" 
                :value="level.level" 
                :label="level.name" 
              />
            </el-select>
          </el-form-item>
          <el-form-item label="设置到期时间">
            <el-date-picker 
              v-model="vipForm.expire_date" 
              type="datetime" 
              placeholder="选择到期时间"
              format="YYYY-MM-DD HH:mm"
              value-format="YYYY-MM-DDTHH:mm:ss"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="或增加天数">
            <el-input-number v-model="vipForm.add_days" :min="0" :max="3650" placeholder="增加VIP天数" style="width: 100%" />
          </el-form-item>
          <el-form-item label="快捷设置">
            <div class="quick-btns">
              <el-button size="small" @click="quickAddDays(30)">+30天</el-button>
              <el-button size="small" @click="quickAddDays(90)">+90天</el-button>
              <el-button size="small" @click="quickAddDays(365)">+1年</el-button>
              <el-button size="small" type="warning" @click="quickAddDays(36500)">永久</el-button>
            </div>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="vipDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveVip" :loading="vipSaving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/utils/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const users = ref([])
const filters = reactive({ search: '', role: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

// VIP管理
const vipDialogVisible = ref(false)
const vipSaving = ref(false)
const currentUser = ref(null)
const vipForm = reactive({
  vip_level: 0,
  expire_date: null,
  add_days: 0
})

// VIP等级配置 - 从API获取
const vipLevels = ref([])

// 获取VIP等级列表
const fetchVipLevels = async () => {
  try {
    const res = await api.get('/admin/vip-levels')
    vipLevels.value = res.data || res || []
  } catch (e) {
    console.error('获取VIP等级失败', e)
    // 降级使用默认值
    vipLevels.value = [
      { level: 0, name: '非VIP' },
      { level: 1, name: '普通VIP' },
      { level: 2, name: 'VIP1' },
      { level: 3, name: 'VIP2' },
      { level: 4, name: 'VIP3' },
      { level: 5, name: '黄金至尊' },
      { level: 6, name: '紫色限定至尊' }
    ]
  }
}

const getVipLevelName = (level) => {
  const found = vipLevels.value.find(v => v.level === level)
  return found?.name || '未知'
}
const getVipLevelType = (level) => {
  const types = {
    0: 'info',
    1: 'warning',
    2: 'warning',
    3: 'warning',
    4: 'warning',
    5: 'success',  // 黄金
    6: 'primary',  // 蓝色
    7: 'danger'    // 紫色/红色
  }
  return types[level] || 'info'
}

// 格式化时间（完整）
const formatTime = (time) => {
  if (!time) return '-'
  const date = new Date(time)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

// 格式化日期（简短）
const formatDate = (time) => {
  if (!time) return '-'
  const date = new Date(time)
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${month}-${day} ${hours}:${minutes}`
}

const fetchUsers = async () => {
  loading.value = true
  try {
    const res = await api.get('/admin/users', { params: { page: pagination.page, page_size: pagination.pageSize, search: filters.search || undefined, role: filters.role || undefined } })
    users.value = res.data.items
    pagination.total = res.data.total
  } catch (e) {
    console.error('获取用户列表失败:', e)
  } finally { loading.value = false }
}

const getRoleType = (role) => ({ SUPER_ADMIN: 'danger', super_admin: 'danger', ADMIN: 'warning', admin: 'warning', VIP: 'success', vip: 'success', USER: 'info', user: 'info' }[role] || 'info')
const getRoleText = (role) => ({ SUPER_ADMIN: '超管', super_admin: '超管', ADMIN: '管理员', admin: '管理员', VIP: 'VIP', vip: 'VIP', USER: '用户', user: '用户' }[role] || role)
const viewUser = (row) => {
  ElMessage.info(`用户详情：${row.username}`)
}
const toggleStatus = async (row) => {
  try {
    await api.put(`/admin/users/${row.id}/status`)
    row.is_active = !row.is_active
    ElMessage.success('操作成功')
  } catch (e) {}
}

const deleteUser = async (row) => {
  try {
    await api.delete(`/admin/users/${row.id}`)
    ElMessage.success('删除成功')
    fetchUsers()  // 刷新列表
  } catch (e) {
    console.error('删除用户失败:', e)
  }
}

// 判断是否过期
const isExpired = (dateStr) => {
  if (!dateStr) return false
  return new Date(dateStr) < new Date()
}

// VIP管理
const openVipDialog = (row) => {
  currentUser.value = row
  vipForm.vip_level = row.vip_level || 0
  vipForm.expire_date = row.vip_expire_date || null
  vipForm.add_days = 0
  vipDialogVisible.value = true
}

const quickAddDays = (days) => {
  vipForm.add_days = days
  vipForm.expire_date = null
}

const saveVip = async () => {
  if (!currentUser.value) return
  
  vipSaving.value = true
  try {
    const data = {}
    
    // 添加VIP等级
    if (vipForm.vip_level !== undefined) {
      data.vip_level = vipForm.vip_level
    }
    
    if (vipForm.expire_date) {
      data.expire_date = vipForm.expire_date
    }
    if (vipForm.add_days > 0) {
      data.add_days = vipForm.add_days
    }
    
    // 如果只设置了等级，不需要时间
    if (data.vip_level === undefined && !data.expire_date && !data.add_days) {
      ElMessage.warning('请设置VIP等级、到期时间或增加天数')
      return
    }
    
    const res = await api.put(`/admin/users/${currentUser.value.id}/vip`, data)
    ElMessage.success('VIP设置成功')
    
    // 更新列表中的数据
    currentUser.value.vip_expire_date = res.data.expire_date
    currentUser.value.is_vip = res.data.is_active
    currentUser.value.vip_level = res.data.vip_level
    currentUser.value.vip_level_name = res.data.vip_level_name
    
    vipDialogVisible.value = false
  } catch (e) {
    console.error('设置VIP失败:', e)
    ElMessage.error('设置VIP失败')
  } finally {
    vipSaving.value = false
  }
}

onMounted(() => {
  fetchUsers()
  fetchVipLevels()
})
</script>

<style lang="scss" scoped>
.users-page {
  .card-header {
    font-size: 16px;
    font-weight: 600;
  }
  
  .filter-bar {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
    flex-wrap: wrap;
  }
  
  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
  
  :deep(.el-table) {
    font-size: 14px;
    
    .el-tag {
      font-size: 12px;
      padding: 0 8px;
      height: 22px;
      line-height: 20px;
    }
    
    .el-table__cell {
      padding: 10px 0;
    }
  }
  
  .user-cell {
    .username {
      font-weight: 500;
      font-size: 14px;
      display: flex;
      align-items: center;
      gap: 4px;
    }
    .nickname {
      font-size: 13px;
      color: #909399;
      margin-top: 2px;
    }
  }
  
  .status-cell {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
  }
  
  .ip-cell {
    .ip {
      font-family: monospace;
      font-size: 13px;
    }
    .location {
      font-size: 13px;
      color: #67c23a;
      margin-top: 2px;
    }
  }
  
  .action-btns {
    display: flex;
    justify-content: center;
    gap: 4px;
    flex-wrap: wrap;
  }
  
  .text-danger {
    color: #f56c6c;
  }
  
  .text-success {
    color: #67c23a;
  }
  
  .text-muted {
    color: #c0c4cc;
  }
}

.vip-dialog-content {
  .user-info-row {
    margin-bottom: 12px;
    
    .label {
      font-weight: 500;
      color: #606266;
      margin-right: 8px;
    }
  }
  
  .quick-btns {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
}
</style>





