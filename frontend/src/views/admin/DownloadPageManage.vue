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

const uploadUrl = computed(() => '/api/v1/download-page/admin/upload')
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
</style>
