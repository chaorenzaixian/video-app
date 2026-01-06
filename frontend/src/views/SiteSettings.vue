<template>
  <div class="site-settings-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>网站设置</span>
        </div>
      </template>

      <el-form :model="form" label-width="120px" class="settings-form">
        <!-- Logo设置 -->
        <el-divider content-position="left">
          <el-icon><Picture /></el-icon> Logo设置
        </el-divider>
        
        <el-form-item label="网站Logo">
          <div class="logo-upload">
            <div class="logo-preview" v-if="form.logo">
              <img :src="form.logo" alt="Logo" />
              <div class="logo-actions">
                <el-button type="danger" size="small" @click="deleteLogo">删除</el-button>
              </div>
            </div>
            <el-upload
              v-else
              class="logo-uploader"
              :action="uploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="handleLogoSuccess"
              :on-error="handleLogoError"
              :before-upload="beforeLogoUpload"
              accept="image/*"
            >
              <div class="upload-placeholder">
                <el-icon class="upload-icon"><Plus /></el-icon>
                <span>上传Logo</span>
              </div>
            </el-upload>
          </div>
          <div class="form-tip">建议尺寸：200x50px，支持 PNG/JPG/GIF/WebP/SVG，最大2MB</div>
        </el-form-item>

        <!-- 基本信息 -->
        <el-divider content-position="left">
          <el-icon><InfoFilled /></el-icon> 基本信息
        </el-divider>

        <el-form-item label="网站名称">
          <el-input v-model="form.site_name" placeholder="网站名称" />
        </el-form-item>

        <el-form-item label="网站描述">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            :rows="3"
            placeholder="网站描述，用于SEO" 
          />
        </el-form-item>

        <el-form-item label="关键词">
          <el-input v-model="form.keywords" placeholder="SEO关键词，用逗号分隔" />
        </el-form-item>

        <!-- 联系方式 -->
        <el-divider content-position="left">
          <el-icon><Message /></el-icon> 联系方式
        </el-divider>

        <el-form-item label="联系邮箱">
          <el-input v-model="form.contact_email" placeholder="客服邮箱" />
        </el-form-item>

        <el-form-item label="联系QQ">
          <el-input v-model="form.contact_qq" placeholder="客服QQ" />
        </el-form-item>

        <el-form-item label="Telegram">
          <el-input v-model="form.contact_telegram" placeholder="Telegram用户名" />
        </el-form-item>

        <!-- 底部信息 -->
        <el-divider content-position="left">
          <el-icon><Document /></el-icon> 底部信息
        </el-divider>

        <el-form-item label="底部文字">
          <el-input v-model="form.footer_text" placeholder="底部版权信息" />
        </el-form-item>

        <el-form-item label="备案号">
          <el-input v-model="form.icp_number" placeholder="ICP备案号" />
        </el-form-item>

        <!-- 保存按钮 -->
        <el-form-item>
          <el-button type="primary" @click="saveSettings" :loading="saving" size="large">
            <el-icon><Check /></el-icon> 保存设置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import api from '@/utils/api'

const userStore = useUserStore()
const saving = ref(false)

const form = reactive({
  site_name: 'Soul',
  logo: '',
  description: '',
  keywords: '',
  contact_email: '',
  contact_qq: '',
  contact_telegram: '',
  footer_text: '',
  icp_number: ''
})

const uploadUrl = computed(() => '/api/v1/settings/site/logo')
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${userStore.token}`
}))

const fetchSettings = async () => {
  try {
    const res = await api.get('/settings/site')
    const data = res.data || res
    Object.assign(form, data)
  } catch (error) {
    console.log('使用默认设置')
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    await api.put('/settings/site', {
      site_name: form.site_name,
      description: form.description,
      keywords: form.keywords,
      contact_email: form.contact_email,
      contact_qq: form.contact_qq,
      contact_telegram: form.contact_telegram,
      footer_text: form.footer_text,
      icp_number: form.icp_number
    })
    ElMessage.success('保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const beforeLogoUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2
  
  if (!isImage) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB')
    return false
  }
  return true
}

const handleLogoSuccess = (response) => {
  form.logo = response.logo
  ElMessage.success('Logo上传成功')
}

const handleLogoError = () => {
  ElMessage.error('Logo上传失败')
}

const deleteLogo = async () => {
  try {
    await api.delete('/settings/site/logo')
    form.logo = ''
    ElMessage.success('Logo已删除')
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  fetchSettings()
})
</script>

<style lang="scss" scoped>
.site-settings-page {
  .card-header {
    font-size: 18px;
    font-weight: 600;
  }
  
  .settings-form {
    max-width: 700px;
    
    :deep(.el-divider__text) {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 15px;
      font-weight: 500;
      color: #333;
    }
  }
  
  .logo-upload {
    .logo-preview {
      display: flex;
      align-items: center;
      gap: 20px;
      
      img {
        max-height: 60px;
        max-width: 200px;
        object-fit: contain;
        background: #f5f5f5;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #eee;
      }
    }
    
    .logo-uploader {
      .upload-placeholder {
        width: 200px;
        height: 80px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        gap: 8px;
        border: 2px dashed #ddd;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s;
        
        &:hover {
          border-color: #6366f1;
          background: rgba(99, 102, 241, 0.05);
        }
        
        .upload-icon {
          font-size: 28px;
          color: #999;
        }
        
        span {
          font-size: 13px;
          color: #999;
        }
      }
    }
  }
  
  .form-tip {
    font-size: 12px;
    color: #999;
    margin-top: 8px;
  }
}
</style>


