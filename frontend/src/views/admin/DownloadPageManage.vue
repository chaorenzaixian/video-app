<template>
  <div class="download-page-manage">
    <el-card class="page-header">
      <div class="header-content">
        <h2>下载页管理</h2>
        <el-button type="primary" @click="saveConfig" :loading="saving">保存配置</el-button>
      </div>
    </el-card>

    <el-row :gutter="20">
      <!-- Android 下载链接 -->
      <el-col :span="12">
        <el-card class="config-card">
          <template #header>
            <div class="card-header">
              <span>Android 下载链接</span>
              <el-button type="primary" size="small" @click="addAndroidLink">添加链接</el-button>
            </div>
          </template>
          
          <!-- APK 上传区域 -->
          <div class="apk-upload-section">
            <el-divider content-position="left">上传 APK 安装包</el-divider>
            <el-upload
              ref="apkUploadRef"
              :action="apkUploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="handleApkUploadSuccess"
              :on-error="handleApkUploadError"
              :on-progress="handleApkUploadProgress"
              :before-upload="beforeApkUpload"
              accept=".apk"
            >
              <el-button type="success" :loading="apkUploading">
                <el-icon><Upload /></el-icon>
                {{ apkUploading ? '上传中...' : '选择 APK 文件' }}
              </el-button>
            </el-upload>
            <el-progress 
              v-if="apkUploadProgress > 0 && apkUploadProgress < 100" 
              :percentage="apkUploadProgress" 
              :stroke-width="10"
              style="margin-top: 10px"
            />
            <div v-if="lastUploadedApk" class="uploaded-apk-info">
              <el-tag type="success">
                已上传: {{ lastUploadedApk.filename }} ({{ lastUploadedApk.size_mb }}MB)
              </el-tag>
              <el-button size="small" type="primary" text @click="useUploadedApk">
                使用此链接
              </el-button>
            </div>
            <el-divider />
          </div>
          
          <el-table :data="config.android_links" style="width: 100%">
            <el-table-column prop="name" label="名称" width="100">
              <template #default="{ row }">
                <el-input v-model="row.name" size="small" />
              </template>
            </el-table-column>
            <el-table-column prop="url" label="下载链接">
              <template #default="{ row }">
                <el-input v-model="row.url" size="small" placeholder="https://..." />
              </template>
            </el-table-column>
            <el-table-column label="主链接" width="70" align="center">
              <template #default="{ row }">
                <el-switch v-model="row.is_primary" @change="setPrimaryLink(row)" />
              </template>
            </el-table-column>
            <el-table-column label="启用" width="70" align="center">
              <template #default="{ row }">
                <el-switch v-model="row.is_active" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="60" align="center">
              <template #default="{ row, $index }">
                <el-button type="danger" size="small" text @click="removeAndroidLink($index)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- iOS 下载链接 -->
      <el-col :span="12">
        <el-card class="config-card">
          <template #header>
            <span>iOS 下载链接</span>
          </template>
          
          <!-- IPA 上传区域 -->
          <div class="ipa-upload-section">
            <el-divider content-position="left">上传 IPA 安装包</el-divider>
            <el-upload
              ref="ipaUploadRef"
              :action="ipaUploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="handleIpaUploadSuccess"
              :on-error="handleIpaUploadError"
              :on-progress="handleIpaUploadProgress"
              :before-upload="beforeIpaUpload"
              accept=".ipa"
            >
              <el-button type="success" :loading="ipaUploading">
                <el-icon><Upload /></el-icon>
                {{ ipaUploading ? '上传中...' : '选择 IPA 文件' }}
              </el-button>
            </el-upload>
            <el-progress 
              v-if="ipaUploadProgress > 0 && ipaUploadProgress < 100" 
              :percentage="ipaUploadProgress" 
              :stroke-width="10"
              style="margin-top: 10px"
            />
            <div v-if="lastUploadedIpa" class="uploaded-ipa-info">
              <el-tag type="success">
                已上传: {{ lastUploadedIpa.filename }} ({{ lastUploadedIpa.size_mb }}MB)
              </el-tag>
              <el-button size="small" type="primary" text @click="useUploadedIpa">
                使用此链接
              </el-button>
            </div>
            <el-divider />
          </div>
          
          <!-- Mobileconfig 上传区域 -->
          <div class="mobileconfig-upload-section">
            <el-divider content-position="left">上传 Mobileconfig 配置文件</el-divider>
            <el-upload
              :action="mobileconfigUploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="handleMobileconfigUploadSuccess"
              :on-error="handleMobileconfigUploadError"
              :on-progress="handleMobileconfigUploadProgress"
              :before-upload="beforeMobileconfigUpload"
              accept=".mobileconfig"
            >
              <el-button type="success" :loading="mobileconfigUploading">
                <el-icon><Upload /></el-icon>
                {{ mobileconfigUploading ? '上传中...' : '选择 Mobileconfig 文件' }}
              </el-button>
            </el-upload>
            <el-progress 
              v-if="mobileconfigUploadProgress > 0 && mobileconfigUploadProgress < 100" 
              :percentage="mobileconfigUploadProgress" 
              :stroke-width="10"
              style="margin-top: 10px"
            />
            <div v-if="lastUploadedMobileconfig" class="uploaded-mobileconfig-info">
              <el-tag type="success">
                已上传: {{ lastUploadedMobileconfig.filename }} ({{ lastUploadedMobileconfig.size_kb }}KB)
              </el-tag>
              <el-button size="small" type="primary" text @click="useUploadedMobileconfig">
                使用此链接
              </el-button>
            </div>
            <el-divider />
          </div>
          
          <el-form label-width="120px">
            <el-form-item label="App Store">
              <el-input v-model="config.ios_links.appstore" placeholder="https://apps.apple.com/..." />
              <el-switch v-model="config.ios_links.appstore_active" style="margin-left: 10px" />
            </el-form-item>
            <el-form-item label="Mobileconfig">
              <el-input v-model="config.ios_links.mobileconfig" placeholder="https://..." />
              <el-switch v-model="config.ios_links.mobileconfig_active" style="margin-left: 10px" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <!-- Logo 管理 -->
      <el-col :span="12">
        <el-card class="config-card">
          <template #header>
            <span>Logo 管理</span>
          </template>
          <el-form label-width="100px">
            <el-form-item label="PC端 Logo">
              <div class="upload-area">
                <el-input v-model="config.logos.pc" placeholder="Logo URL" style="flex: 1" />
                <el-upload
                  :action="uploadUrl"
                  :headers="uploadHeaders"
                  :data="{ type: 'logo_pc' }"
                  :show-file-list="false"
                  :on-success="(res) => handleUploadSuccess(res, 'logos', 'pc')"
                  accept="image/*"
                >
                  <el-button size="small" type="primary">上传</el-button>
                </el-upload>
              </div>
              <el-image v-if="config.logos.pc" :src="getFullUrl(config.logos.pc)" style="height: 50px; margin-top: 10px" fit="contain" />
            </el-form-item>
            <el-form-item label="移动端 Logo">
              <div class="upload-area">
                <el-input v-model="config.logos.mobile" placeholder="Logo URL" style="flex: 1" />
                <el-upload
                  :action="uploadUrl"
                  :headers="uploadHeaders"
                  :data="{ type: 'logo_mobile' }"
                  :show-file-list="false"
                  :on-success="(res) => handleUploadSuccess(res, 'logos', 'mobile')"
                  accept="image/*"
                >
                  <el-button size="small" type="primary">上传</el-button>
                </el-upload>
              </div>
              <el-image v-if="config.logos.mobile" :src="getFullUrl(config.logos.mobile)" style="height: 50px; margin-top: 10px" fit="contain" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 二维码生成 -->
      <el-col :span="12">
        <el-card class="config-card">
          <template #header>
            <span>二维码配置</span>
          </template>
          <el-form label-width="100px">
            <el-form-item label="目标 URL">
              <el-input v-model="config.qrcode.url" placeholder="扫码后跳转的地址" />
            </el-form-item>
            <el-form-item label="颜色">
              <el-color-picker v-model="config.qrcode.color" />
            </el-form-item>
            <el-form-item label="尺寸">
              <el-slider v-model="config.qrcode.size" :min="100" :max="500" :step="50" show-input />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="generateQRCode" :loading="generatingQR">生成二维码</el-button>
              <el-button v-if="qrcodeImage" @click="downloadQRCode">下载二维码</el-button>
            </el-form-item>
            <el-form-item v-if="qrcodeImage">
              <el-image :src="qrcodeImage" style="max-width: 200px" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <!-- 背景图管理 -->
      <el-col :span="24">
        <el-card class="config-card">
          <template #header>
            <div class="card-header">
              <span>背景图管理</span>
              <el-radio-group v-model="config.active_bg_version" size="small">
                <el-radio-button label="v1">版本1</el-radio-button>
                <el-radio-button label="v2">版本2</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <el-tabs>
            <el-tab-pane label="版本1 (V1)">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="PC端背景">
                    <div class="upload-area">
                      <el-input v-model="config.backgrounds_v1.pc" placeholder="背景图 URL 或颜色值 (#000000)" style="flex: 1" />
                      <el-upload
                        :action="uploadUrl"
                        :headers="uploadHeaders"
                        :data="{ type: 'bg_v1_pc' }"
                        :show-file-list="false"
                        :on-success="(res) => handleUploadSuccess(res, 'backgrounds_v1', 'pc')"
                        accept="image/*"
                      >
                        <el-button size="small" type="primary">上传</el-button>
                      </el-upload>
                    </div>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="移动端背景">
                    <div class="upload-area">
                      <el-input v-model="config.backgrounds_v1.mobile" placeholder="背景图 URL 或颜色值" style="flex: 1" />
                      <el-upload
                        :action="uploadUrl"
                        :headers="uploadHeaders"
                        :data="{ type: 'bg_v1_mobile' }"
                        :show-file-list="false"
                        :on-success="(res) => handleUploadSuccess(res, 'backgrounds_v1', 'mobile')"
                        accept="image/*"
                      >
                        <el-button size="small" type="primary">上传</el-button>
                      </el-upload>
                    </div>
                  </el-form-item>
                </el-col>
              </el-row>
            </el-tab-pane>
            <el-tab-pane label="版本2 (V2)">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="PC端背景">
                    <div class="upload-area">
                      <el-input v-model="config.backgrounds_v2.pc" placeholder="背景图 URL 或颜色值" style="flex: 1" />
                      <el-upload
                        :action="uploadUrl"
                        :headers="uploadHeaders"
                        :data="{ type: 'bg_v2_pc' }"
                        :show-file-list="false"
                        :on-success="(res) => handleUploadSuccess(res, 'backgrounds_v2', 'pc')"
                        accept="image/*"
                      >
                        <el-button size="small" type="primary">上传</el-button>
                      </el-upload>
                    </div>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="移动端背景">
                    <div class="upload-area">
                      <el-input v-model="config.backgrounds_v2.mobile" placeholder="背景图 URL 或颜色值" style="flex: 1" />
                      <el-upload
                        :action="uploadUrl"
                        :headers="uploadHeaders"
                        :data="{ type: 'bg_v2_mobile' }"
                        :show-file-list="false"
                        :on-success="(res) => handleUploadSuccess(res, 'backgrounds_v2', 'mobile')"
                        accept="image/*"
                      >
                        <el-button size="small" type="primary">上传</el-button>
                      </el-upload>
                    </div>
                  </el-form-item>
                </el-col>
              </el-row>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>

    <!-- 预览按钮 -->
    <el-card style="margin-top: 20px">
      <el-button type="success" @click="previewPage">预览下载页</el-button>
      <span style="margin-left: 20px; color: #909399">下载页地址: http://38.47.218.230/</span>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import { Upload } from '@element-plus/icons-vue'
import api from '@/utils/api'

const config = reactive({
  android_links: [],
  ios_links: { appstore: '', mobileconfig: '', appstore_active: true, mobileconfig_active: true },
  logos: { pc: '', mobile: '' },
  backgrounds_v1: { pc: '', mobile: '' },
  backgrounds_v2: { pc: '', mobile: '' },
  qrcode: { url: '', logo: null, color: '#000000', size: 300 },
  active_bg_version: 'v1'
})

const saving = ref(false)
const generatingQR = ref(false)
const qrcodeImage = ref('')
const apkUploading = ref(false)
const apkUploadProgress = ref(0)
const lastUploadedApk = ref(null)
const apkUploadRef = ref(null)
const ipaUploading = ref(false)
const ipaUploadProgress = ref(0)
const lastUploadedIpa = ref(null)
const ipaUploadRef = ref(null)
const mobileconfigUploading = ref(false)
const mobileconfigUploadProgress = ref(0)
const lastUploadedMobileconfig = ref(null)

const uploadUrl = computed(() => '/api/v1/download-page/admin/upload')
const apkUploadUrl = computed(() => '/api/v1/download-page/admin/upload-apk')
const ipaUploadUrl = computed(() => '/api/v1/download-page/admin/upload-ipa')
const mobileconfigUploadUrl = computed(() => '/api/v1/download-page/admin/upload-mobileconfig')
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`
}))

const getFullUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `http://38.47.218.137${url}`
}

const loadConfig = async () => {
  try {
    const res = await api.get('/download-page/admin/config')
    Object.assign(config, res)
  } catch (e) {
    ElMessage.error('加载配置失败')
  }
}

const saveConfig = async () => {
  saving.value = true
  try {
    await api.put('/download-page/admin/config', config)
    ElMessage.success('配置保存成功')
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

const addAndroidLink = () => {
  config.android_links.push({
    id: Date.now().toString(36),
    name: '新链接',
    url: '',
    is_primary: config.android_links.length === 0,
    is_active: true,
    sort_order: config.android_links.length
  })
}

const removeAndroidLink = (index) => {
  config.android_links.splice(index, 1)
}

const setPrimaryLink = (row) => {
  if (row.is_primary) {
    config.android_links.forEach(link => {
      if (link !== row) link.is_primary = false
    })
  }
}

const handleUploadSuccess = (res, category, field) => {
  if (res.url) {
    config[category][field] = res.url
    ElMessage.success('上传成功')
  }
}

// APK 上传相关方法
const beforeApkUpload = (file) => {
  const isApk = file.name.toLowerCase().endsWith('.apk')
  if (!isApk) {
    ElMessage.error('只能上传 APK 格式文件')
    return false
  }
  const isLt200M = file.size / 1024 / 1024 < 200
  if (!isLt200M) {
    ElMessage.error('APK 文件大小不能超过 200MB')
    return false
  }
  apkUploading.value = true
  apkUploadProgress.value = 0
  return true
}

const handleApkUploadProgress = (event) => {
  apkUploadProgress.value = Math.round(event.percent || 0)
}

const handleApkUploadSuccess = (res) => {
  apkUploading.value = false
  apkUploadProgress.value = 100
  if (res.url) {
    lastUploadedApk.value = res
    ElMessage.success(`APK 上传成功: ${res.filename} (${res.size_mb}MB)`)
  }
}

const handleApkUploadError = (error) => {
  apkUploading.value = false
  apkUploadProgress.value = 0
  ElMessage.error('APK 上传失败: ' + (error.message || '未知错误'))
}

const useUploadedApk = () => {
  if (!lastUploadedApk.value) return
  
  // 查找主链接或第一个链接，更新其 URL
  const primaryLink = config.android_links.find(link => link.is_primary)
  if (primaryLink) {
    primaryLink.url = lastUploadedApk.value.url
    ElMessage.success('已更新主下载链接')
  } else if (config.android_links.length > 0) {
    config.android_links[0].url = lastUploadedApk.value.url
    ElMessage.success('已更新第一个下载链接')
  } else {
    // 没有链接，创建一个新的
    config.android_links.push({
      id: Date.now().toString(36),
      name: 'APK下载',
      url: lastUploadedApk.value.url,
      is_primary: true,
      is_active: true,
      sort_order: 0
    })
    ElMessage.success('已创建新的下载链接')
  }
}

// IPA 上传相关方法
const beforeIpaUpload = (file) => {
  const isIpa = file.name.toLowerCase().endsWith('.ipa')
  if (!isIpa) {
    ElMessage.error('只能上传 IPA 格式文件')
    return false
  }
  const isLt500M = file.size / 1024 / 1024 < 500
  if (!isLt500M) {
    ElMessage.error('IPA 文件大小不能超过 500MB')
    return false
  }
  ipaUploading.value = true
  ipaUploadProgress.value = 0
  return true
}

const handleIpaUploadProgress = (event) => {
  ipaUploadProgress.value = Math.round(event.percent || 0)
}

const handleIpaUploadSuccess = (res) => {
  ipaUploading.value = false
  ipaUploadProgress.value = 100
  if (res.url) {
    lastUploadedIpa.value = res
    ElMessage.success(`IPA 上传成功: ${res.filename} (${res.size_mb}MB)`)
  }
}

const handleIpaUploadError = (error) => {
  ipaUploading.value = false
  ipaUploadProgress.value = 0
  ElMessage.error('IPA 上传失败: ' + (error.message || '未知错误'))
}

const useUploadedIpa = () => {
  if (!lastUploadedIpa.value) return
  
  // 更新 App Store 链接为 IPA 下载地址
  config.ios_links.appstore = lastUploadedIpa.value.url
  config.ios_links.appstore_active = true
  ElMessage.success('已更新 iOS IPA 下载链接')
}

// Mobileconfig 上传相关方法
const beforeMobileconfigUpload = (file) => {
  const isMobileconfig = file.name.toLowerCase().endsWith('.mobileconfig')
  if (!isMobileconfig) {
    ElMessage.error('只能上传 mobileconfig 格式文件')
    return false
  }
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    ElMessage.error('mobileconfig 文件大小不能超过 10MB')
    return false
  }
  mobileconfigUploading.value = true
  mobileconfigUploadProgress.value = 0
  return true
}

const handleMobileconfigUploadProgress = (event) => {
  mobileconfigUploadProgress.value = Math.round(event.percent || 0)
}

const handleMobileconfigUploadSuccess = (res) => {
  mobileconfigUploading.value = false
  mobileconfigUploadProgress.value = 100
  if (res.url) {
    lastUploadedMobileconfig.value = res
    ElMessage.success(`Mobileconfig 上传成功: ${res.filename} (${res.size_kb}KB)`)
  }
}

const handleMobileconfigUploadError = (error) => {
  mobileconfigUploading.value = false
  mobileconfigUploadProgress.value = 0
  ElMessage.error('Mobileconfig 上传失败: ' + (error.message || '未知错误'))
}

const useUploadedMobileconfig = () => {
  if (!lastUploadedMobileconfig.value) return
  
  // 更新 mobileconfig 链接
  config.ios_links.mobileconfig = lastUploadedMobileconfig.value.url
  config.ios_links.mobileconfig_active = true
  ElMessage.success('已更新 Mobileconfig 链接')
}

const generateQRCode = async () => {
  if (!config.qrcode.url) {
    ElMessage.warning('请输入二维码目标 URL')
    return
  }
  generatingQR.value = true
  try {
    const res = await api.post('/download-page/admin/qrcode', {
      url: config.qrcode.url,
      color: config.qrcode.color,
      size: config.qrcode.size
    })
    qrcodeImage.value = res.image
    ElMessage.success('二维码生成成功')
  } catch (e) {
    ElMessage.error('生成失败: ' + (e.message || '未知错误'))
  } finally {
    generatingQR.value = false
  }
}

const downloadQRCode = () => {
  if (!qrcodeImage.value) return
  const link = document.createElement('a')
  link.href = qrcodeImage.value
  link.download = 'qrcode.png'
  link.click()
}

const previewPage = () => {
  window.open('http://38.47.218.230/', '_blank')
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.download-page-manage {
  padding: 20px;
}
.page-header {
  margin-bottom: 20px;
}
.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-content h2 {
  margin: 0;
}
.config-card {
  height: 100%;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.upload-area {
  display: flex;
  gap: 10px;
  align-items: center;
}
.apk-upload-section {
  margin-bottom: 15px;
}
.uploaded-apk-info {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.ipa-upload-section {
  margin-bottom: 15px;
}
.uploaded-ipa-info {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.mobileconfig-upload-section {
  margin-bottom: 15px;
}
.uploaded-mobileconfig-info {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>
