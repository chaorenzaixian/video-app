<template>
  <div class="announcement-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>评论区公告设置</span>
        </div>
      </template>

      <el-form :model="form" label-width="100px" style="max-width: 600px;">
        <el-form-item label="启用公告">
          <el-switch v-model="form.enabled" :loading="loading" />
        </el-form-item>

        <el-form-item label="公告名称">
          <el-input v-model="form.name" placeholder="如：Soul官方" />
        </el-form-item>

        <el-form-item label="公告头像">
          <div class="avatar-upload">
            <el-upload
              class="avatar-uploader"
              action=""
              :show-file-list="false"
              :auto-upload="false"
              accept="image/*"
              @change="handleAvatarChange"
            >
              <img v-if="form.avatar" :src="form.avatar" class="avatar-preview" />
              <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
            </el-upload>
            <el-button v-if="form.avatar" type="danger" size="small" @click="form.avatar = ''">
              删除头像
            </el-button>
          </div>
        </el-form-item>

        <el-form-item label="公告内容">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="5"
            placeholder="支持表情符号，如：🔥限时优惠🔥..."
          />
        </el-form-item>

        <el-form-item label="更新时间">
          <span style="color: #999;">{{ formatTime(form.updated_at) }}</span>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="saveAnnouncement" :loading="saving">
            保存设置
          </el-button>
        </el-form-item>
      </el-form>

      </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '@/utils/api'
import dayjs from 'dayjs'

const form = ref({
  enabled: true,
  name: 'Soul官方',
  avatar: '',
  content: '',
  updated_at: null
})

const saving = ref(false)
const loading = ref(true)

const fetchAnnouncement = async () => {
  loading.value = true
  try {
    const res = await api.get('/settings/comment-announcement')
    const data = res.data || res
    console.log('获取公告数据:', data)
    form.value = {
      enabled: data.enabled !== false, // 默认启用
      name: data.name || 'Soul官方',
      avatar: data.avatar || '',
      content: data.content || '',
      updated_at: data.updated_at
    }
  } catch (error) {
    console.log('获取公告失败:', error)
    ElMessage.warning('获取公告设置失败，请确保后端服务已启动')
    // 失败时默认启用
    form.value.enabled = true
  } finally {
    loading.value = false
  }
}

const handleAvatarChange = async (file) => {
  const formData = new FormData()
  formData.append('file', file.raw)
  
  try {
    const res = await api.post('/settings/comment-announcement/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    const data = res.data || res
    form.value.avatar = data.avatar
    ElMessage.success('头像上传成功')
  } catch (error) {
    ElMessage.error('头像上传失败')
  }
}

const saveAnnouncement = async () => {
  saving.value = true
  try {
    const res = await api.put('/settings/comment-announcement', {
      enabled: form.value.enabled,
      name: form.value.name,
      content: form.value.content,
      avatar: form.value.avatar
    })
    const data = res.data || res
    form.value.updated_at = data.updated_at
    ElMessage.success('保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const formatTime = (dateStr) => {
  if (!dateStr) return ''
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

onMounted(() => {
  fetchAnnouncement()
})
</script>

<style lang="scss" scoped>
.announcement-page {
  padding: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 16px;
  font-weight: bold;
}

.avatar-upload {
  display: flex;
  align-items: center;
  gap: 15px;
  
  .avatar-uploader {
    width: 80px;
    height: 80px;
    border: 1px dashed #dcdfe6;
    border-radius: 50%;
    cursor: pointer;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    
    &:hover {
      border-color: #409eff;
    }
  }
  
  .avatar-preview {
    width: 80px;
    height: 80px;
    object-fit: cover;
  }
  
  .avatar-uploader-icon {
    font-size: 28px;
    color: #8c939d;
  }
}

</style>

