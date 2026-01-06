<template>
  <div class="monitor-page">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card><el-statistic title="CPU使用率" :value="systemStatus.cpu" suffix="%" /></el-card>
      </el-col>
      <el-col :span="8">
        <el-card><el-statistic title="内存使用率" :value="systemStatus.memory" suffix="%" /></el-card>
      </el-col>
      <el-col :span="8">
        <el-card><el-statistic title="磁盘使用率" :value="systemStatus.disk" suffix="%" /></el-card>
      </el-col>
    </el-row>
    <el-card style="margin-top:20px"><template #header>实时监控</template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="在线用户">{{ realtimeStats.online_users }}</el-descriptions-item>
        <el-descriptions-item label="活跃流">{{ realtimeStats.active_streams }}</el-descriptions-item>
        <el-descriptions-item label="数据库状态"><el-tag type="success">正常</el-tag></el-descriptions-item>
        <el-descriptions-item label="Redis状态"><el-tag type="success">正常</el-tag></el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const systemStatus = ref({ cpu: 45.2, memory: 62.8, disk: 35.5 })
const realtimeStats = ref({ online_users: 128, active_streams: 45 })
</script>









