<template>
  <el-dialog
    v-model="visible"
    title="发布规则"
    width="600px"
    :close-on-click-modal="false"
  >
    <div class="publish-rules">
      <h3>发布须知</h3>
      <ol>
        <li>请确保您上传的内容符合相关法律法规</li>
        <li>禁止上传违规、侵权内容</li>
        <li>内容将经过审核后发布</li>
        <li>违规内容将被删除，严重者将被封号</li>
      </ol>
    </div>
    <template #footer>
      <el-button @click="visible = false">我知道了</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const visible = ref(props.modelValue)

watch(() => props.modelValue, (val) => {
  visible.value = val
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})
</script>

<style lang="scss" scoped>
.publish-rules {
  h3 {
    font-size: 16px;
    margin-bottom: 16px;
  }
  
  ol {
    padding-left: 20px;
    
    li {
      margin-bottom: 8px;
      line-height: 1.6;
    }
  }
}
</style>





