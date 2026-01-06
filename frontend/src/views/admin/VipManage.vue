<template>
  <div class="vip-manage">
    <el-tabs v-model="activeTab">
      <!-- VIP卡片管理 -->
      <el-tab-pane label="VIP卡片管理" name="cards">
        <div class="tab-header">
          <el-button type="primary" @click="showCardDialog()">
            <el-icon><Plus /></el-icon>
            添加卡片
          </el-button>
        </div>

        <el-table :data="cards" v-loading="loading.cards" stripe>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column label="背景图" width="120">
            <template #default="{ row }">
              <el-image
                v-if="row.background_image"
                :src="row.background_image"
                :preview-src-list="[row.background_image]"
                class="card-preview"
                fit="cover"
              />
              <span v-else class="text-muted">无</span>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="卡片名称" width="120" />
          <el-table-column prop="level" label="等级" width="120">
            <template #default="{ row }">
              {{ getLevelName(row.level) }}
            </template>
          </el-table-column>
          <el-table-column prop="display_title" label="显示标题" width="150" show-overflow-tooltip />
          <el-table-column prop="badge_text" label="角标" width="100" />
          <el-table-column prop="price" label="售价" width="80">
            <template #default="{ row }">¥{{ row.price }}</template>
          </el-table-column>
          <el-table-column prop="original_price" label="原价" width="80">
            <template #default="{ row }">
              <span v-if="row.original_price">¥{{ row.original_price }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="duration_days" label="有效期" width="80">
            <template #default="{ row }">
              {{ row.duration_days === 0 ? '永久' : row.duration_days + '天' }}
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="80">
            <template #default="{ row }">
              <el-switch v-model="row.is_active" @change="toggleCardStatus(row)" />
            </template>
          </el-table-column>
          <el-table-column prop="sort_order" label="排序" width="80" />
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="showCardDialog(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteCard(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- VIP特权管理 -->
      <el-tab-pane label="VIP特权管理" name="privileges">
        <div class="tab-header">
          <el-button type="primary" @click="showPrivilegeDialog()">
            <el-icon><Plus /></el-icon>
            添加特权
          </el-button>
        </div>

        <el-table :data="privileges" v-loading="loading.privileges" stripe>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column label="图标" width="80">
            <template #default="{ row }">
              <el-image
                v-if="row.icon"
                :src="row.icon"
                class="privilege-icon-preview"
                fit="contain"
              />
              <span v-else class="text-muted">无</span>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="特权名称" width="150" />
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          <el-table-column prop="min_level" label="最低等级" width="140">
            <template #default="{ row }">
              {{ getLevelName(row.min_level) }}+
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="80">
            <template #default="{ row }">
              <el-switch v-model="row.is_active" @change="togglePrivilegeStatus(row)" />
            </template>
          </el-table-column>
          <el-table-column prop="sort_order" label="排序" width="80" />
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="showPrivilegeDialog(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="deletePrivilege(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- VIP卡片编辑对话框 -->
    <el-dialog
      v-model="cardDialog.visible"
      :title="cardDialog.isEdit ? '编辑VIP卡片' : '添加VIP卡片'"
      width="700px"
    >
      <el-form :model="cardForm" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="卡片名称" required>
              <el-input v-model="cardForm.name" placeholder="如：尊享限定卡" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="VIP等级" required>
              <el-select v-model="cardForm.level" placeholder="选择VIP等级" style="width: 100%">
                <el-option
                  v-for="lvl in vipLevels"
                  :key="lvl.level"
                  :label="`${lvl.name} (等级${lvl.level})`"
                  :value="lvl.level"
                >
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <img v-if="lvl.icon && lvl.icon.startsWith('/')" :src="lvl.icon" style="width: 20px; height: 20px;" />
                    <span v-else>💎</span>
                    <span>{{ lvl.name }} (等级{{ lvl.level }})</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="显示标题">
          <el-input
            v-model="cardForm.display_title"
            type="textarea"
            rows="2"
            placeholder="卡片上显示的标题，支持换行"
          />
        </el-form-item>

        <el-form-item label="背景图片">
          <el-upload
            class="card-uploader"
            :action="cardUploadUrl"
            :headers="uploadHeaders"
            :show-file-list="false"
            :on-success="(res) => handleUploadSuccess(res, 'card')"
            :before-upload="beforeUpload"
            accept="image/*"
          >
            <el-image
              v-if="cardForm.background_image"
              :src="cardForm.background_image"
              class="uploaded-card-image"
              fit="cover"
            />
            <el-icon v-else class="upload-icon"><Plus /></el-icon>
          </el-upload>
          <div class="upload-tip">建议尺寸: 400x560px，支持 JPG/PNG/WebP</div>
        </el-form-item>

        <el-form-item label="角标文字">
          <el-input v-model="cardForm.badge_text" placeholder="如：15项特权" style="width: 200px" />
        </el-form-item>

        <el-divider>关联特权（卡片上显示）</el-divider>

        <el-form-item label="选择特权">
          <el-select
            v-model="cardForm.selected_privileges"
            multiple
            filterable
            collapse-tags
            collapse-tags-tooltip
            placeholder="选择要显示的特权"
            style="width: 100%"
          >
            <el-option
              v-for="p in availablePrivileges"
              :key="p.id"
              :label="p.name"
              :value="p.id"
            >
              <div style="display: flex; align-items: center; gap: 8px;">
                <img v-if="p.icon && p.icon.startsWith('/')" :src="p.icon" style="width: 20px; height: 20px;" />
                <span v-else>{{ p.icon }}</span>
                <span>{{ p.name }}</span>
                <el-tag size="small" type="info">LV{{ p.min_level }}+</el-tag>
              </div>
            </el-option>
          </el-select>
          <div class="form-tip">只显示等级要求 ≤ 当前卡片等级的特权，可选择多个</div>
        </el-form-item>

        <el-form-item label="已选特权" v-if="cardForm.selected_privileges.length > 0">
          <div class="selected-privileges">
            <el-tag
              v-for="pId in cardForm.selected_privileges"
              :key="pId"
              closable
              @close="removePrivilege(pId)"
              style="margin: 4px;"
            >
              {{ getPrivilegeName(pId) }}
            </el-tag>
          </div>
        </el-form-item>

        <el-divider>价格设置</el-divider>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="售价" required>
              <el-input-number v-model="cardForm.price" :min="0" :precision="2" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="原价">
              <el-input-number v-model="cardForm.original_price" :min="0" :precision="2" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="有效天数">
              <el-input-number v-model="cardForm.duration_days" :min="0" />
              <div class="form-tip">0表示永久</div>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="排序">
              <el-input-number v-model="cardForm.sort_order" :min="0" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-switch v-model="cardForm.is_active" active-text="启用" inactive-text="禁用" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="cardDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitCard" :loading="cardDialog.loading">确定</el-button>
      </template>
    </el-dialog>

    <!-- VIP特权编辑对话框 -->
    <el-dialog
      v-model="privilegeDialog.visible"
      :title="privilegeDialog.isEdit ? '编辑VIP特权' : '添加VIP特权'"
      width="500px"
    >
      <el-form :model="privilegeForm" label-width="100px">
        <el-form-item label="特权名称" required>
          <el-input v-model="privilegeForm.name" placeholder="如：金币视频免费" />
        </el-form-item>

        <el-form-item label="特权描述">
          <el-input v-model="privilegeForm.description" placeholder="如：全网金币视频免费看" />
        </el-form-item>

        <el-form-item label="图标">
          <el-upload
            class="privilege-uploader"
            :action="privilegeUploadUrl"
            :headers="uploadHeaders"
            :show-file-list="false"
            :on-success="(res) => handleUploadSuccess(res, 'privilege')"
            :before-upload="beforeUpload"
            accept="image/*"
          >
            <el-image
              v-if="privilegeForm.icon"
              :src="privilegeForm.icon"
              class="uploaded-privilege-icon"
              fit="contain"
            />
            <el-icon v-else class="upload-icon"><Plus /></el-icon>
          </el-upload>
          <div class="upload-tip">建议尺寸: 64x64px</div>
        </el-form-item>

        <el-form-item label="最低VIP等级">
          <el-select v-model="privilegeForm.min_level" placeholder="选择最低等级" style="width: 100%">
            <el-option
              v-for="lvl in vipLevels"
              :key="lvl.level"
              :label="`${lvl.name}及以上`"
              :value="lvl.level"
            >
              <div style="display: flex; align-items: center; gap: 8px;">
                <img v-if="lvl.icon && lvl.icon.startsWith('/')" :src="lvl.icon" style="width: 20px; height: 20px;" />
                <span v-else>💎</span>
                <span>{{ lvl.name }}及以上</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="排序">
              <el-input-number v-model="privilegeForm.sort_order" :min="0" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-switch v-model="privilegeForm.is_active" active-text="启用" inactive-text="禁用" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="privilegeDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitPrivilege" :loading="privilegeDialog.loading">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '@/utils/api'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const activeTab = ref('cards')
const cards = ref([])
const privileges = ref([])
const vipLevels = ref([])  // 现有VIP等级配置

const loading = reactive({
  cards: false,
  privileges: false,
  levels: false
})

// 卡片对话框
const cardDialog = reactive({
  visible: false,
  isEdit: false,
  loading: false
})

const cardForm = reactive({
  id: null,
  name: '',
  level: 1,
  display_title: '',
  background_image: '',
  badge_text: '',
  selected_privileges: [],
  price: 0,
  original_price: null,
  duration_days: 30,
  sort_order: 0,
  is_active: true
})

// 特权对话框
const privilegeDialog = reactive({
  visible: false,
  isEdit: false,
  loading: false
})

const privilegeForm = reactive({
  id: null,
  name: '',
  description: '',
  icon: '',
  min_level: 1,
  sort_order: 0,
  is_active: true
})

// 上传URL - 根据类型动态生成 (需要包含 /api/v1 前缀，因为el-upload不经过axios)
const cardUploadUrl = '/api/v1/vip/admin/upload-image?image_type=card'
const privilegeUploadUrl = '/api/v1/vip/admin/upload-image?image_type=privilege'
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${userStore.token}`
}))

// 根据卡片等级筛选可用特权
const availablePrivileges = computed(() => {
  const cardLevel = cardForm.level || 0
  return privileges.value.filter(p => p.min_level <= cardLevel)
})

// 获取特权名称
const getPrivilegeName = (privilegeId) => {
  const p = privileges.value.find(item => item.id === privilegeId)
  return p ? p.name : `特权${privilegeId}`
}

// 移除已选特权
const removePrivilege = (privilegeId) => {
  const index = cardForm.selected_privileges.indexOf(privilegeId)
  if (index > -1) {
    cardForm.selected_privileges.splice(index, 1)
  }
}

// 获取等级名称
const getLevelName = (level) => {
  const lvl = vipLevels.value.find(l => l.level === level)
  return lvl ? lvl.name : `等级${level}`
}

// 获取VIP等级配置（从现有系统）
const fetchVipLevels = async () => {
  loading.levels = true
  try {
    const res = await api.get('/admin/vip-levels')
    vipLevels.value = res.data || res || []
  } catch (error) {
    console.error('获取VIP等级失败:', error)
    // 如果获取失败，使用默认等级
    vipLevels.value = [
      { level: 1, name: '普通VIP', icon: '💎' },
      { level: 2, name: 'VIP1', icon: '💎' },
      { level: 3, name: 'VIP2', icon: '💎' },
      { level: 4, name: 'VIP3', icon: '💎' },
      { level: 5, name: '黄金至尊', icon: '👑' },
      { level: 6, name: '蓝色至尊', icon: '💠' },
      { level: 7, name: '紫色限定至尊', icon: '🔮' }
    ]
  } finally {
    loading.levels = false
  }
}

// 获取卡片列表
const fetchCards = async () => {
  loading.cards = true
  try {
    const res = await api.get('/vip/admin/cards')
    cards.value = res.data || res || []
  } catch (error) {
    ElMessage.error('获取卡片列表失败')
  } finally {
    loading.cards = false
  }
}

// 获取特权列表
const fetchPrivileges = async () => {
  loading.privileges = true
  try {
    const res = await api.get('/vip/admin/privileges')
    privileges.value = res.data || res || []
  } catch (error) {
    ElMessage.error('获取特权列表失败')
  } finally {
    loading.privileges = false
  }
}

// 显示卡片对话框
const showCardDialog = (row = null) => {
  cardDialog.isEdit = !!row
  if (row) {
    Object.assign(cardForm, {
      ...row,
      // 解析特权ID列表（从后端的privilege_ids字段或旧的benefit_line字段）
      selected_privileges: row.privilege_ids || []
    })
  } else {
    Object.assign(cardForm, {
      id: null,
      name: '',
      level: 1,
      display_title: '',
      background_image: '',
      badge_text: '',
      selected_privileges: [],
      price: 0,
      original_price: null,
      duration_days: 30,
      sort_order: 0,
      is_active: true
    })
  }
  cardDialog.visible = true
}

// 显示特权对话框
const showPrivilegeDialog = (row = null) => {
  privilegeDialog.isEdit = !!row
  if (row) {
    Object.assign(privilegeForm, row)
  } else {
    Object.assign(privilegeForm, {
      id: null,
      name: '',
      description: '',
      icon: '',
      min_level: 1,
      sort_order: 0,
      is_active: true
    })
  }
  privilegeDialog.visible = true
}

// 上传成功
const handleUploadSuccess = (res, type) => {
  const url = res.url || res.data?.url
  if (type === 'card') {
    cardForm.background_image = url
  } else {
    privilegeForm.icon = url
  }
  ElMessage.success('上传成功')
}

// 上传前检查
const beforeUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt5M = file.size / 1024 / 1024 < 5
  if (!isImage) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB')
    return false
  }
  return true
}

// 提交卡片
const submitCard = async () => {
  if (!cardForm.name) {
    ElMessage.warning('请输入卡片名称')
    return
  }

  cardDialog.loading = true
  try {
    const data = { 
      ...cardForm,
      // 将选中的特权ID发送给后端
      privilege_ids: cardForm.selected_privileges || []
    }
    delete data.id
    delete data.selected_privileges  // 移除前端用的字段名

    if (cardDialog.isEdit) {
      await api.put(`/vip/admin/cards/${cardForm.id}`, data)
      ElMessage.success('更新成功')
    } else {
      await api.post('/vip/admin/cards', data)
      ElMessage.success('添加成功')
    }

    cardDialog.visible = false
    fetchCards()
  } catch (error) {
    ElMessage.error('操作失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    cardDialog.loading = false
  }
}

// 提交特权
const submitPrivilege = async () => {
  if (!privilegeForm.name) {
    ElMessage.warning('请输入特权名称')
    return
  }

  privilegeDialog.loading = true
  try {
    const data = { ...privilegeForm }
    delete data.id

    if (privilegeDialog.isEdit) {
      await api.put(`/vip/admin/privileges/${privilegeForm.id}`, data)
      ElMessage.success('更新成功')
    } else {
      await api.post('/vip/admin/privileges', data)
      ElMessage.success('添加成功')
    }

    privilegeDialog.visible = false
    fetchPrivileges()
  } catch (error) {
    ElMessage.error('操作失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    privilegeDialog.loading = false
  }
}

// 切换卡片状态
const toggleCardStatus = async (row) => {
  try {
    await api.put(`/vip/admin/cards/${row.id}`, { is_active: row.is_active })
    ElMessage.success(row.is_active ? '已启用' : '已禁用')
  } catch (error) {
    row.is_active = !row.is_active
    ElMessage.error('操作失败')
  }
}

// 切换特权状态
const togglePrivilegeStatus = async (row) => {
  try {
    await api.put(`/vip/admin/privileges/${row.id}`, { is_active: row.is_active })
    ElMessage.success(row.is_active ? '已启用' : '已禁用')
  } catch (error) {
    row.is_active = !row.is_active
    ElMessage.error('操作失败')
  }
}

// 删除卡片
const deleteCard = async (row) => {
  await ElMessageBox.confirm('确定删除该VIP卡片？', '确认删除', { type: 'warning' })
  try {
    await api.delete(`/vip/admin/cards/${row.id}`)
    ElMessage.success('删除成功')
    fetchCards()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

// 删除特权
const deletePrivilege = async (row) => {
  await ElMessageBox.confirm('确定删除该VIP特权？', '确认删除', { type: 'warning' })
  try {
    await api.delete(`/vip/admin/privileges/${row.id}`)
    ElMessage.success('删除成功')
    fetchPrivileges()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  fetchVipLevels()  // 先获取等级配置
  fetchCards()
  fetchPrivileges()
})
</script>

<style lang="scss" scoped>
.vip-manage {
  padding: 20px;
}

.tab-header {
  margin-bottom: 16px;
}

.card-preview {
  width: 80px;
  height: 100px;
  border-radius: 8px;
}

.privilege-icon-preview {
  width: 40px;
  height: 40px;
}

.card-uploader {
  :deep(.el-upload) {
    width: 200px;
    height: 280px;
    border: 1px dashed #d9d9d9;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    background: #fafafa;
    transition: border-color 0.3s;

    &:hover {
      border-color: #409eff;
    }
  }
}

.uploaded-card-image {
  width: 200px;
  height: 280px;
  border-radius: 12px;
}

.privilege-uploader {
  :deep(.el-upload) {
    width: 80px;
    height: 80px;
    border: 1px dashed #d9d9d9;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    background: #fafafa;

    &:hover {
      border-color: #409eff;
    }
  }
}

.uploaded-privilege-icon {
  width: 80px;
  height: 80px;
}

.upload-icon {
  font-size: 32px;
  color: #8c939d;
}

.upload-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.form-tip {
  font-size: 12px;
  color: #909399;
}

.text-muted {
  color: #909399;
}
</style>



















