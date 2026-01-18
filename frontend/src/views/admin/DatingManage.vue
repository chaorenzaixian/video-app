<template>
  <div class="dating-manage">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>交友管理</h2>
    </div>

    <!-- 标签页 -->
    <el-tabs v-model="activeTab" class="manage-tabs">
      <!-- 群聊管理 -->
      <el-tab-pane label="群聊管理" name="groups">
        <div class="tab-header">
          <el-button type="primary" @click="showGroupDialog()">
            <el-icon><Plus /></el-icon> 添加群聊
          </el-button>
          <el-button type="danger" @click="batchDeleteGroups" :disabled="!selectedGroups.length">
            <el-icon><Delete /></el-icon> 批量删除 ({{ selectedGroups.length }})
          </el-button>
          <el-button @click="showBatchLinkDialog('group')">
            <el-icon><Link /></el-icon> 批量设置链接
          </el-button>
          <el-select v-model="groupCategory" placeholder="分类筛选" clearable style="width: 120px; margin-left: 10px">
            <el-option label="SOUL群" value="soul" />
          </el-select>
        </div>

        <el-table :data="groups" v-loading="loadingGroups" stripe @selection-change="handleGroupSelectionChange">
          <el-table-column type="selection" width="50" />
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column label="头像" width="80">
            <template #default="{ row }">
              <el-avatar :src="row.avatar" :size="40" />
            </template>
          </el-table-column>
          <el-table-column prop="name" label="群名称" min-width="150" />
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          <el-table-column prop="member_count" label="人数" width="80" />
          <el-table-column prop="coin_cost" label="金币" width="80" />
          <el-table-column label="免费" width="70">
            <template #default="{ row }">
              <el-tag :type="row.is_free ? 'success' : 'info'" size="small">
                {{ row.is_free ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="分类" width="80">
            <template #default="{ row }">
              <el-tag size="small">{{ getCategoryLabel(row.category) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="sort_order" label="排序" width="70" />
          <el-table-column label="状态" width="70">
            <template #default="{ row }">
              <el-switch v-model="row.is_active" @change="toggleGroupStatus(row)" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link @click="showGroupDialog(row)">编辑</el-button>
              <el-button type="danger" link @click="deleteGroup(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-model:current-page="groupPage"
          v-model:page-size="groupPageSize"
          :total="groupTotal"
          layout="total, prev, pager, next"
          @current-change="fetchGroups"
          style="margin-top: 16px"
        />
      </el-tab-pane>

      <!-- 主播管理 -->
      <el-tab-pane label="主播管理" name="hosts">
        <div class="tab-header">
          <el-button type="primary" @click="showHostDialog()">
            <el-icon><Plus /></el-icon> 添加主播
          </el-button>
          <el-button type="danger" @click="batchDeleteHosts" :disabled="!selectedHosts.length">
            <el-icon><Delete /></el-icon> 批量删除 ({{ selectedHosts.length }})
          </el-button>
          <el-button @click="showBatchLinkDialog('host')">
            <el-icon><Link /></el-icon> 批量设置链接
          </el-button>
          <el-select v-model="hostCategory" placeholder="分类筛选" clearable style="width: 120px; margin-left: 10px">
            <el-option label="裸聊" value="chat" />
            <el-option label="直播" value="live" />
          </el-select>
        </div>

        <el-table :data="hosts" v-loading="loadingHosts" stripe @selection-change="handleHostSelectionChange">
          <el-table-column type="selection" width="50" />
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column label="头像" width="80">
            <template #default="{ row }">
              <el-avatar :src="row.avatar" :size="40" />
            </template>
          </el-table-column>
          <el-table-column prop="nickname" label="昵称" width="120" />
          <el-table-column label="资料" min-width="180">
            <template #default="{ row }">
              <span v-if="row.age">{{ row.age }}岁</span>
              <span v-if="row.height"> {{ row.height }}cm</span>
              <span v-if="row.weight"> {{ row.weight }}kg</span>
              <span v-if="row.cup"> {{ row.cup }}罩杯</span>
            </template>
          </el-table-column>
          <el-table-column prop="chat_count" label="聊天数" width="80" />
          <el-table-column label="标签" width="120">
            <template #default="{ row }">
              <el-tag v-if="row.is_vip" type="warning" size="small">VIP</el-tag>
              <el-tag v-if="row.is_ace" type="danger" size="small">王牌</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="sub_category" label="子分类" width="100" />
          <el-table-column prop="sort_order" label="排序" width="70" />
          <el-table-column label="状态" width="70">
            <template #default="{ row }">
              <el-switch v-model="row.is_active" @change="toggleHostStatus(row)" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link @click="showHostDialog(row)">编辑</el-button>
              <el-button type="danger" link @click="deleteHost(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-model:current-page="hostPage"
          v-model:page-size="hostPageSize"
          :total="hostTotal"
          layout="total, prev, pager, next"
          @current-change="fetchHosts"
          style="margin-top: 16px"
        />
      </el-tab-pane>
    </el-tabs>

    <!-- 群聊编辑弹窗 -->
    <el-dialog v-model="groupDialogVisible" :title="editingGroup ? '编辑群聊' : '添加群聊'" width="500px">
      <el-form :model="groupForm" label-width="80px">
        <el-form-item label="群名称" required>
          <el-input v-model="groupForm.name" placeholder="请输入群名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="groupForm.description" type="textarea" :rows="2" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="头像">
          <div class="avatar-upload">
            <el-upload
              :show-file-list="false"
              :http-request="(opts) => uploadAvatar(opts, 'group')"
              accept="image/*"
            >
              <div class="avatar-box">
                <el-avatar v-if="groupForm.avatar" :src="groupForm.avatar" :size="80" />
                <div v-else class="avatar-placeholder">
                  <el-icon :size="24"><Plus /></el-icon>
                  <span>上传头像</span>
                </div>
                <div class="avatar-mask" v-if="groupForm.avatar">
                  <el-icon><Upload /></el-icon>
                </div>
              </div>
            </el-upload>
            <el-input v-model="groupForm.avatar" placeholder="或输入头像URL" style="margin-top: 8px" />
          </div>
        </el-form-item>
        <el-form-item label="跳转链接">
          <el-input v-model="groupForm.join_url" placeholder="加入群聊的跳转链接" />
        </el-form-item>
        <el-form-item label="人数显示">
          <el-input v-model="groupForm.member_count" placeholder="如: 10w" />
        </el-form-item>
        <el-form-item label="金币费用">
          <el-input-number v-model="groupForm.coin_cost" :min="0" />
        </el-form-item>
        <el-form-item label="限时免费">
          <el-switch v-model="groupForm.is_free" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="groupForm.category">
            <el-option label="SOUL群" value="soul" />
            <el-option label="裸聊" value="chat" />
            <el-option label="直播" value="live" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="groupForm.sort_order" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="groupDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveGroup" :loading="savingGroup">保存</el-button>
      </template>
    </el-dialog>

    <!-- 主播编辑弹窗 -->
    <el-dialog v-model="hostDialogVisible" :title="editingHost ? '编辑主播' : '添加主播'" width="500px">
      <el-form :model="hostForm" label-width="80px">
        <el-form-item label="昵称" required>
          <el-input v-model="hostForm.nickname" placeholder="请输入昵称" />
        </el-form-item>
        <el-form-item label="头像">
          <div class="avatar-upload">
            <el-upload
              :show-file-list="false"
              :http-request="(opts) => uploadAvatar(opts, 'host')"
              accept="image/*"
            >
              <div class="avatar-box">
                <el-avatar v-if="hostForm.avatar" :src="hostForm.avatar" :size="80" />
                <div v-else class="avatar-placeholder">
                  <el-icon :size="24"><Plus /></el-icon>
                  <span>上传头像</span>
                </div>
                <div class="avatar-mask" v-if="hostForm.avatar">
                  <el-icon><Upload /></el-icon>
                </div>
              </div>
            </el-upload>
            <el-input v-model="hostForm.avatar" placeholder="或输入头像URL" style="margin-top: 8px" />
          </div>
        </el-form-item>
        <el-form-item label="年龄">
          <el-input-number v-model="hostForm.age" :min="18" :max="99" />
        </el-form-item>
        <el-form-item label="身高(cm)">
          <el-input-number v-model="hostForm.height" :min="140" :max="200" />
        </el-form-item>
        <el-form-item label="体重(kg)">
          <el-input-number v-model="hostForm.weight" :min="30" :max="100" />
        </el-form-item>
        <el-form-item label="罩杯">
          <el-select v-model="hostForm.cup" placeholder="选择罩杯">
            <el-option v-for="c in ['A', 'B', 'C', 'D', 'E', 'F', 'G']" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="聊天人数">
          <el-input-number v-model="hostForm.chat_count" :min="0" />
        </el-form-item>
        <el-form-item label="VIP">
          <el-switch v-model="hostForm.is_vip" />
        </el-form-item>
        <el-form-item label="王牌主播">
          <el-switch v-model="hostForm.is_ace" />
        </el-form-item>
        <el-form-item label="跳转链接">
          <el-input v-model="hostForm.profile_url" placeholder="主播详情页链接" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="hostForm.category">
            <el-option label="裸聊" value="chat" />
            <el-option label="直播" value="live" />
          </el-select>
        </el-form-item>
        <el-form-item label="子分类">
          <el-select v-model="hostForm.sub_category" clearable placeholder="选择子分类">
            <el-option label="学生萝莉" value="学生萝莉" />
            <el-option label="人妻少妇" value="人妻少妇" />
            <el-option label="主播御姐" value="主播御姐" />
            <el-option label="模特兼职" value="模特兼职" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="hostForm.sort_order" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="hostDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveHost" :loading="savingHost">保存</el-button>
      </template>
    </el-dialog>

    <!-- 批量设置链接弹窗 -->
    <el-dialog v-model="batchLinkDialogVisible" title="批量设置跳转链接" width="500px">
      <el-form label-width="100px">
        <el-form-item label="应用范围">
          <el-radio-group v-model="batchLinkScope">
            <el-radio label="selected">仅选中项 ({{ batchLinkType === 'group' ? selectedGroups.length : selectedHosts.length }})</el-radio>
            <el-radio label="all">全部{{ batchLinkType === 'group' ? '群聊' : '主播' }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="跳转链接">
          <el-input v-model="batchLinkUrl" placeholder="请输入跳转链接" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchLinkDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveBatchLink" :loading="savingBatchLink">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload, Delete, Link } from '@element-plus/icons-vue'
import api from '@/utils/api'

const activeTab = ref('groups')

// 群聊相关
const groups = ref([])
const loadingGroups = ref(false)
const groupPage = ref(1)
const groupPageSize = ref(20)
const groupTotal = ref(0)
const groupCategory = ref('')
const groupDialogVisible = ref(false)
const editingGroup = ref(null)
const savingGroup = ref(false)
const selectedGroups = ref([])
const groupForm = ref({
  name: '',
  description: '',
  avatar: '',
  join_url: '',
  member_count: '0',
  coin_cost: 0,
  is_free: false,
  category: 'soul',
  sort_order: 0
})

// 主播相关
const hosts = ref([])
const loadingHosts = ref(false)
const hostPage = ref(1)
const hostPageSize = ref(20)
const hostTotal = ref(0)
const hostCategory = ref('')
const hostDialogVisible = ref(false)
const editingHost = ref(null)
const savingHost = ref(false)
const selectedHosts = ref([])
const hostForm = ref({
  nickname: '',
  avatar: '',
  age: null,
  height: null,
  weight: null,
  cup: '',
  chat_count: 0,
  is_vip: false,
  is_ace: false,
  profile_url: '',
  category: 'chat',
  sub_category: '',
  sort_order: 0
})

// 批量设置链接
const batchLinkDialogVisible = ref(false)
const batchLinkType = ref('group')
const batchLinkScope = ref('selected')
const batchLinkUrl = ref('')
const savingBatchLink = ref(false)

const getCategoryLabel = (cat) => {
  const labels = { soul: 'SOUL群', chat: '裸聊', live: '直播' }
  return labels[cat] || cat
}

// 获取群聊列表
const fetchGroups = async () => {
  loadingGroups.value = true
  try {
    const params = { page: groupPage.value, page_size: groupPageSize.value }
    if (groupCategory.value) params.category = groupCategory.value
    const res = await api.get('/admin/dating/groups', { params })
    const data = res.data || res
    groups.value = data.items || []
    groupTotal.value = data.total || 0
  } catch (e) {
    ElMessage.error('获取群聊列表失败')
  } finally {
    loadingGroups.value = false
  }
}

// 显示群聊弹窗
const showGroupDialog = (group = null) => {
  editingGroup.value = group
  if (group) {
    groupForm.value = { ...group }
  } else {
    groupForm.value = {
      name: '',
      description: '',
      avatar: '',
      join_url: '',
      member_count: '0',
      coin_cost: 0,
      is_free: false,
      category: 'soul',
      sort_order: 0
    }
  }
  groupDialogVisible.value = true
}

// 保存群聊
const saveGroup = async () => {
  if (!groupForm.value.name) {
    ElMessage.warning('请输入群名称')
    return
  }
  savingGroup.value = true
  try {
    if (editingGroup.value) {
      await api.put(`/admin/dating/groups/${editingGroup.value.id}`, groupForm.value)
      ElMessage.success('更新成功')
    } else {
      await api.post('/admin/dating/groups', groupForm.value)
      ElMessage.success('添加成功')
    }
    groupDialogVisible.value = false
    fetchGroups()
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    savingGroup.value = false
  }
}

// 切换群聊状态
const toggleGroupStatus = async (group) => {
  try {
    await api.put(`/admin/dating/groups/${group.id}`, { is_active: group.is_active })
  } catch (e) {
    group.is_active = !group.is_active
    ElMessage.error('操作失败')
  }
}

// 删除群聊
const deleteGroup = async (group) => {
  try {
    await ElMessageBox.confirm('确定删除该群聊？', '提示', { type: 'warning' })
    await api.delete(`/admin/dating/groups/${group.id}`)
    ElMessage.success('删除成功')
    fetchGroups()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

// 获取主播列表
const fetchHosts = async () => {
  loadingHosts.value = true
  try {
    const params = { page: hostPage.value, page_size: hostPageSize.value }
    if (hostCategory.value) params.category = hostCategory.value
    const res = await api.get('/admin/dating/hosts', { params })
    const data = res.data || res
    hosts.value = data.items || []
    hostTotal.value = data.total || 0
  } catch (e) {
    ElMessage.error('获取主播列表失败')
  } finally {
    loadingHosts.value = false
  }
}

// 显示主播弹窗
const showHostDialog = (host = null) => {
  editingHost.value = host
  if (host) {
    hostForm.value = { ...host }
  } else {
    hostForm.value = {
      nickname: '',
      avatar: '',
      age: null,
      height: null,
      weight: null,
      cup: '',
      chat_count: 0,
      is_vip: false,
      is_ace: false,
      profile_url: '',
      category: 'chat',
      sub_category: '',
      sort_order: 0
    }
  }
  hostDialogVisible.value = true
}

// 保存主播
const saveHost = async () => {
  if (!hostForm.value.nickname) {
    ElMessage.warning('请输入昵称')
    return
  }
  savingHost.value = true
  try {
    if (editingHost.value) {
      await api.put(`/admin/dating/hosts/${editingHost.value.id}`, hostForm.value)
      ElMessage.success('更新成功')
    } else {
      await api.post('/admin/dating/hosts', hostForm.value)
      ElMessage.success('添加成功')
    }
    hostDialogVisible.value = false
    fetchHosts()
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    savingHost.value = false
  }
}

// 切换主播状态
const toggleHostStatus = async (host) => {
  try {
    await api.put(`/admin/dating/hosts/${host.id}`, { is_active: host.is_active })
  } catch (e) {
    host.is_active = !host.is_active
    ElMessage.error('操作失败')
  }
}

// 删除主播
const deleteHost = async (host) => {
  try {
    await ElMessageBox.confirm('确定删除该主播？', '提示', { type: 'warning' })
    await api.delete(`/admin/dating/hosts/${host.id}`)
    ElMessage.success('删除成功')
    fetchHosts()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

// 选择变化
const handleGroupSelectionChange = (selection) => {
  selectedGroups.value = selection
}

const handleHostSelectionChange = (selection) => {
  selectedHosts.value = selection
}

// 批量删除群聊
const batchDeleteGroups = async () => {
  if (!selectedGroups.value.length) return
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedGroups.value.length} 个群聊？`, '提示', { type: 'warning' })
    for (const group of selectedGroups.value) {
      await api.delete(`/admin/dating/groups/${group.id}`)
    }
    ElMessage.success('批量删除成功')
    selectedGroups.value = []
    fetchGroups()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('批量删除失败')
  }
}

// 批量删除主播
const batchDeleteHosts = async () => {
  if (!selectedHosts.value.length) return
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedHosts.value.length} 个主播？`, '提示', { type: 'warning' })
    for (const host of selectedHosts.value) {
      await api.delete(`/admin/dating/hosts/${host.id}`)
    }
    ElMessage.success('批量删除成功')
    selectedHosts.value = []
    fetchHosts()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('批量删除失败')
  }
}

// 显示批量设置链接弹窗
const showBatchLinkDialog = (type) => {
  batchLinkType.value = type
  batchLinkScope.value = 'selected'
  batchLinkUrl.value = ''
  batchLinkDialogVisible.value = true
}

// 保存批量链接
const saveBatchLink = async () => {
  if (!batchLinkUrl.value) {
    ElMessage.warning('请输入跳转链接')
    return
  }
  
  savingBatchLink.value = true
  try {
    if (batchLinkType.value === 'group') {
      const items = batchLinkScope.value === 'selected' ? selectedGroups.value : groups.value
      for (const item of items) {
        await api.put(`/admin/dating/groups/${item.id}`, { join_url: batchLinkUrl.value })
      }
      fetchGroups()
    } else {
      const items = batchLinkScope.value === 'selected' ? selectedHosts.value : hosts.value
      for (const item of items) {
        await api.put(`/admin/dating/hosts/${item.id}`, { profile_url: batchLinkUrl.value })
      }
      fetchHosts()
    }
    ElMessage.success('批量设置成功')
    batchLinkDialogVisible.value = false
  } catch (e) {
    ElMessage.error('批量设置失败')
  } finally {
    savingBatchLink.value = false
  }
}

// 上传头像
const uploadAvatar = async (options, type) => {
  const formData = new FormData()
  formData.append('file', options.file)
  
  try {
    const res = await api.post('/admin/dating/upload-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    const data = res.data || res
    const url = data.url
    if (type === 'group') {
      groupForm.value.avatar = url
    } else {
      hostForm.value.avatar = url
    }
    ElMessage.success('上传成功')
  } catch (e) {
    ElMessage.error('上传失败')
  }
}

watch(groupCategory, () => {
  groupPage.value = 1
  fetchGroups()
})

watch(hostCategory, () => {
  hostPage.value = 1
  fetchHosts()
})

onMounted(() => {
  fetchGroups()
  fetchHosts()
})
</script>

<style lang="scss" scoped>
.dating-manage {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  h2 {
    margin: 0;
    font-size: 20px;
  }
}

.manage-tabs {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
}

.tab-header {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
}

.avatar-upload {
  .avatar-box {
    position: relative;
    width: 80px;
    height: 80px;
    cursor: pointer;
    
    .avatar-placeholder {
      width: 80px;
      height: 80px;
      border: 1px dashed #dcdfe6;
      border-radius: 8px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      color: #909399;
      font-size: 12px;
      
      &:hover {
        border-color: #409eff;
        color: #409eff;
      }
    }
    
    .avatar-mask {
      position: absolute;
      top: 0;
      left: 0;
      width: 80px;
      height: 80px;
      border-radius: 50%;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      opacity: 0;
      transition: opacity 0.3s;
    }
    
    &:hover .avatar-mask {
      opacity: 1;
    }
  }
}
</style>
