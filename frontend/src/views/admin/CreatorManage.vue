<template>
  <div class="admin-page">
    <div class="page-header">
      <h1>创作者管理</h1>
      <p class="page-desc">审核创作者申请、管理创作者账号</p>
    </div>

    <el-tabs v-model="activeTab" class="main-tabs">
      <!-- 申请审核 -->
      <el-tab-pane label="申请审核" name="applications">
        <div class="tab-header">
          <el-select v-model="appFilter.status" placeholder="状态" clearable style="width: 120px">
            <el-option label="待审核" value="pending" />
            <el-option label="已通过" value="approved" />
            <el-option label="已拒绝" value="rejected" />
          </el-select>
          <el-input v-model="appFilter.keyword" placeholder="搜索用户" clearable style="width: 180px" />
          <el-button type="primary" @click="fetchApplications">查询</el-button>
        </div>

        <el-table :data="applications" stripe border v-loading="loading">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column label="申请人" width="180">
            <template #default="{ row }">
              <div class="user-cell">
                <el-avatar :size="36" :src="row.avatar" />
                <div class="user-info">
                  <span class="user-name">{{ row.nickname || row.username }}</span>
                  <span class="user-id">ID: {{ row.user_id }}</span>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="real_name" label="真实姓名" width="100" />
          <el-table-column prop="phone" label="联系电话" width="130" />
          <el-table-column prop="introduction" label="个人介绍" min-width="200" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="getAppStatusType(row.status)" size="small">
                {{ getAppStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="申请时间" width="160">
            <template #default="{ row }">
              {{ formatTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right" align="center">
            <template #default="{ row }">
              <template v-if="row.status === 'pending'">
                <el-button type="success" size="small" @click="handleAppApprove(row)">通过</el-button>
                <el-button type="danger" size="small" @click="showAppRejectDialog(row)">拒绝</el-button>
              </template>
              <el-button size="small" @click="viewAppDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-model:current-page="appPagination.page"
          :page-size="appPagination.pageSize"
          :total="appPagination.total"
          layout="total, prev, pager, next"
          @current-change="fetchApplications"
          class="pagination"
        />
      </el-tab-pane>

      <!-- 创作者列表 -->
      <el-tab-pane label="创作者列表" name="creators">
        <div class="tab-header">
          <el-input v-model="creatorFilter.keyword" placeholder="搜索创作者" clearable style="width: 180px" />
          <el-select v-model="creatorFilter.verified" placeholder="认证状态" clearable style="width: 120px">
            <el-option label="已认证" :value="true" />
            <el-option label="未认证" :value="false" />
          </el-select>
          <el-button type="primary" @click="fetchCreators">查询</el-button>
        </div>

        <el-table :data="creators" stripe border>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column label="创作者" width="200">
            <template #default="{ row }">
              <div class="user-cell">
                <el-avatar :size="40" :src="row.avatar" />
                <div class="user-info">
                  <span class="user-name">{{ row.display_name || row.nickname }}</span>
                  <span class="user-id">Lv.{{ row.creator_level }}</span>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="认证" width="100" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.is_verified" type="success" size="small">已认证</el-tag>
              <el-tag v-else type="info" size="small">未认证</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="total_videos" label="视频数" width="90" align="center" />
          <el-table-column prop="total_followers" label="粉丝数" width="100" align="center" />
          <el-table-column label="总收益" width="120" align="right">
            <template #default="{ row }">
              <span class="coins-text">{{ row.total_coins_earned }}</span>
            </template>
          </el-table-column>
          <el-table-column label="可提现" width="120" align="right">
            <template #default="{ row }">
              <span class="coins-text">{{ row.available_coins }}</span>
            </template>
          </el-table-column>
          <el-table-column label="分成比例" width="100" align="center">
            <template #default="{ row }">
              {{ ((1 - row.platform_share_ratio) * 100).toFixed(0) }}%
            </template>
          </el-table-column>
          <el-table-column label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.is_banned" type="danger" size="small">封禁</el-tag>
              <el-tag v-else-if="row.is_active" type="success" size="small">正常</el-tag>
              <el-tag v-else type="info" size="small">停用</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right" align="center">
            <template #default="{ row }">
              <el-button size="small" @click="editCreator(row)">编辑</el-button>
              <el-button v-if="!row.is_banned" size="small" type="danger" @click="banCreator(row)">封禁</el-button>
              <el-button v-else size="small" type="success" @click="unbanCreator(row)">解封</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-model:current-page="creatorPagination.page"
          :page-size="creatorPagination.pageSize"
          :total="creatorPagination.total"
          layout="total, prev, pager, next"
          @current-change="fetchCreators"
          class="pagination"
        />
      </el-tab-pane>
    </el-tabs>

    <!-- 拒绝原因弹窗 -->
    <el-dialog v-model="rejectDialog.visible" title="拒绝申请" width="400px">
      <el-input v-model="rejectDialog.reason" type="textarea" rows="4" placeholder="请输入拒绝原因" />
      <template #footer>
        <el-button @click="rejectDialog.visible = false">取消</el-button>
        <el-button type="danger" @click="handleAppReject">确认拒绝</el-button>
      </template>
    </el-dialog>

    <!-- 申请详情弹窗 -->
    <el-dialog v-model="detailDialog.visible" title="申请详情" width="500px">
      <el-descriptions :column="1" border v-if="detailDialog.app">
        <el-descriptions-item label="用户ID">{{ detailDialog.app.user_id }}</el-descriptions-item>
        <el-descriptions-item label="用户名">{{ detailDialog.app.username }}</el-descriptions-item>
        <el-descriptions-item label="真实姓名">{{ detailDialog.app.real_name }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ detailDialog.app.phone }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ detailDialog.app.email || '-' }}</el-descriptions-item>
        <el-descriptions-item label="擅长领域">{{ detailDialog.app.expertise || '-' }}</el-descriptions-item>
        <el-descriptions-item label="个人介绍">{{ detailDialog.app.introduction }}</el-descriptions-item>
        <el-descriptions-item label="申请时间">{{ formatTime(detailDialog.app.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getAppStatusType(detailDialog.app.status)">{{ getAppStatusText(detailDialog.app.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="拒绝原因" v-if="detailDialog.app.reject_reason">
          {{ detailDialog.app.reject_reason }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 编辑创作者弹窗 -->
    <el-dialog v-model="editDialog.visible" title="编辑创作者" width="450px">
      <el-form :model="editForm" label-width="100px" v-if="editDialog.visible">
        <el-form-item label="创作者等级">
          <el-input-number v-model="editForm.creator_level" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="认证状态">
          <el-switch v-model="editForm.is_verified" />
        </el-form-item>
        <el-form-item label="认证类型" v-if="editForm.is_verified">
          <el-select v-model="editForm.verification_type">
            <el-option label="个人认证" value="personal" />
            <el-option label="企业认证" value="company" />
            <el-option label="官方认证" value="official" />
          </el-select>
        </el-form-item>
        <el-form-item label="分成比例">
          <el-slider v-model="editForm.creator_share" :min="50" :max="90" :format-tooltip="val => val + '%'" />
          <span class="share-tip">创作者获得 {{ editForm.creator_share }}%，平台抽成 {{ 100 - editForm.creator_share }}%</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="saveCreator">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'

const activeTab = ref('applications')
const loading = ref(false)

// 申请数据
const applications = ref([])
const appFilter = reactive({ status: 'pending', keyword: '' })
const appPagination = reactive({ page: 1, pageSize: 15, total: 0 })

// 创作者数据
const creators = ref([])
const creatorFilter = reactive({ keyword: '', verified: null })
const creatorPagination = reactive({ page: 1, pageSize: 15, total: 0 })

// 弹窗
const rejectDialog = reactive({ visible: false, app: null, reason: '' })
const detailDialog = reactive({ visible: false, app: null })
const editDialog = reactive({ visible: false, creator: null })
const editForm = ref({ creator_level: 1, is_verified: false, verification_type: 'personal', creator_share: 70 })

const getAppStatusType = (status) => {
  const types = { pending: 'warning', approved: 'success', rejected: 'danger' }
  return types[status] || 'info'
}

const getAppStatusText = (status) => {
  const texts = { pending: '待审核', approved: '已通过', rejected: '已拒绝' }
  return texts[status] || status
}

const formatTime = (time) => {
  if (!time) return '-'
  const d = new Date(time)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

const fetchApplications = async () => {
  loading.value = true
  try {
    const res = await api.get('/admin/creator-applications', {
      params: { status: appFilter.status, page: appPagination.page }
    })
    applications.value = res.data?.items || []
    appPagination.total = res.data?.total || 0
  } catch (error) {
    applications.value = []
  } finally {
    loading.value = false
  }
}

const fetchCreators = async () => {
  try {
    const res = await api.get('/admin/creators', {
      params: { keyword: creatorFilter.keyword, page: creatorPagination.page }
    })
    creators.value = res.data?.items || []
    creatorPagination.total = res.data?.total || 0
  } catch (error) {
    creators.value = []
  }
}

const handleAppApprove = async (app) => {
  try {
    await ElMessageBox.confirm('确定通过此创作者申请?', '提示')
    await api.post(`/admin/creator-applications/${app.id}/approve`)
    ElMessage.success('已通过')
    await fetchApplications()
  } catch (e) {}
}

const showAppRejectDialog = (app) => {
  rejectDialog.app = app
  rejectDialog.reason = ''
  rejectDialog.visible = true
}

const handleAppReject = async () => {
  if (!rejectDialog.reason) {
    ElMessage.warning('请输入拒绝原因')
    return
  }
  try {
    await api.post(`/admin/creator-applications/${rejectDialog.app.id}/reject`, {
      reason: rejectDialog.reason
    })
    ElMessage.success('已拒绝')
    rejectDialog.visible = false
    await fetchApplications()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const viewAppDetail = (app) => {
  detailDialog.app = app
  detailDialog.visible = true
}

const editCreator = (creator) => {
  editDialog.creator = creator
  editForm.value = {
    creator_level: creator.creator_level,
    is_verified: creator.is_verified,
    verification_type: creator.verification_type || 'personal',
    creator_share: Math.round((1 - creator.platform_share_ratio) * 100)
  }
  editDialog.visible = true
}

const saveCreator = async () => {
  try {
    await api.put(`/admin/creators/${editDialog.creator.id}`, {
      creator_level: editForm.value.creator_level,
      is_verified: editForm.value.is_verified,
      verification_type: editForm.value.verification_type,
      platform_share_ratio: (100 - editForm.value.creator_share) / 100
    })
    ElMessage.success('保存成功')
    editDialog.visible = false
    await fetchCreators()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const banCreator = async (creator) => {
  try {
    await ElMessageBox.prompt('请输入封禁原因', '封禁创作者', { type: 'warning' })
      .then(async ({ value }) => {
        await api.post(`/admin/creators/${creator.id}/ban`, { reason: value })
        ElMessage.success('已封禁')
        await fetchCreators()
      })
  } catch (e) {}
}

const unbanCreator = async (creator) => {
  try {
    await ElMessageBox.confirm('确定解除封禁?', '提示')
    await api.post(`/admin/creators/${creator.id}/unban`)
    ElMessage.success('已解封')
    await fetchCreators()
  } catch (e) {}
}

onMounted(() => {
  fetchApplications()
})
</script>

<style lang="scss" scoped>
.admin-page {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 20px;
  
  h1 {
    font-size: 24px;
    font-weight: 600;
    color: #303133;
    margin: 0 0 8px;
  }
  
  .page-desc {
    color: #909399;
    font-size: 14px;
    margin: 0;
  }
}

.main-tabs {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.tab-header {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  
  .user-info {
    display: flex;
    flex-direction: column;
    
    .user-name {
      font-weight: 500;
      color: #303133;
    }
    
    .user-id {
      font-size: 12px;
      color: #909399;
    }
  }
}

.coins-text {
  color: #e6a23c;
  font-weight: 600;
}

.share-tip {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-table) {
  border-radius: 8px;
  
  th {
    background: #f5f7fa !important;
    font-weight: 600;
  }
}

:deep(.el-tabs__item) {
  font-size: 15px;
}
</style>

