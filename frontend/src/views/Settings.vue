<template>
  <div class="settings-page">
    <el-card><template #header>系统设置</template>
      <el-form label-width="120px" style="max-width:600px">
        <el-form-item label="站点名称"><el-input v-model="settings.site_name" /></el-form-item>
        <el-form-item label="VIP包月价格"><el-input-number v-model="settings.vip_monthly" :min="1" /> 元</el-form-item>
        <el-form-item label="VIP包年价格"><el-input-number v-model="settings.vip_yearly" :min="1" /> 元</el-form-item>
        <el-form-item label="邀请奖励天数"><el-input-number v-model="settings.invite_days" :min="1" /> 天</el-form-item>
        <el-form-item><el-button type="primary">保存设置</el-button></el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
const settings = reactive({ site_name: 'VOD Platform', vip_monthly: 29, vip_yearly: 199, invite_days: 7 })
</script>









