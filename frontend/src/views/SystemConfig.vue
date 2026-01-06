<template>
  <div class="system-config-page">
    <div class="page-header">
      <h2>系统配置</h2>
      <el-button type="primary" @click="saveAll" :loading="saving">
        保存全部
      </el-button>
    </div>

    <!-- 配置分组 -->
    <el-tabs v-model="activeGroup" @tab-change="fetchConfigs">
      <el-tab-pane 
        v-for="group in groups" 
        :key="group.key" 
        :label="group.name" 
        :name="group.key"
      />
    </el-tabs>

    <!-- 配置列表 -->
    <div class="config-list" v-loading="loading">
      <div class="config-item" v-for="config in configs" :key="config.key">
        <div class="config-info">
          <label class="config-label">{{ config.description || config.key }}</label>
          <span class="config-key">{{ config.key }}</span>
        </div>
        <div class="config-value">
          <el-input
            v-if="!isTextarea(config.key)"
            v-model="config.value"
            :placeholder="config.description"
          />
          <el-input
            v-else
            v-model="config.value"
            type="textarea"
            :rows="3"
            :placeholder="config.description"
          />
        </div>
      </div>

      <el-empty v-if="!loading && configs.length === 0" description="暂无配置项" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const loading = ref(false)
const saving = ref(false)
const activeGroup = ref('credential')
const groups = ref([])
const configs = ref([])

// 需要使用textarea的配置项
const textareaKeys = ['credential_tip', 'share_desc', 'withdraw_rule_1', 'withdraw_rule_2', 'withdraw_rule_3', 'withdraw_rule_4']

const isTextarea = (key) => {
  return textareaKeys.includes(key)
}

// 获取配置分组
const fetchGroups = async () => {
  try {
    const res = await api.get('/config/groups')
    groups.value = res.data || []
    if (groups.value.length > 0 && !groups.value.find(g => g.key === activeGroup.value)) {
      activeGroup.value = groups.value[0].key
    }
  } catch (error) {
    console.error('获取分组失败:', error)
    // 使用默认分组
    groups.value = [
      { key: 'credential', name: '账号凭证' },
      { key: 'basic', name: '基础配置' },
      { key: 'share', name: '分享配置' }
    ]
  }
}

// 获取配置
const fetchConfigs = async () => {
  loading.value = true
  try {
    const res = await api.get('/config/', { params: { group_name: activeGroup.value } })
    configs.value = res.data || []
  } catch (error) {
    console.error('获取配置失败:', error)
    ElMessage.error('获取配置失败')
  } finally {
    loading.value = false
  }
}

// 保存全部
const saveAll = async () => {
  saving.value = true
  try {
    const configData = {}
    configs.value.forEach(c => {
      configData[c.key] = c.value || ''
    })
    
    await api.post('/config/batch', configData)
    ElMessage.success('保存成功')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchGroups()
  fetchConfigs()
})
</script>

<style lang="scss" scoped>
.system-config-page {
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

.config-list {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  min-height: 300px;
}

.config-item {
  display: flex;
  align-items: flex-start;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
  
  &:last-child {
    border-bottom: none;
  }
  
  .config-info {
    width: 200px;
    flex-shrink: 0;
    padding-right: 20px;
    
    .config-label {
      display: block;
      font-weight: 500;
      color: #333;
      margin-bottom: 4px;
    }
    
    .config-key {
      font-size: 12px;
      color: #999;
      font-family: monospace;
    }
  }
  
  .config-value {
    flex: 1;
  }
}

:deep(.el-tabs__nav-wrap) {
  margin-bottom: 20px;
}
</style>
