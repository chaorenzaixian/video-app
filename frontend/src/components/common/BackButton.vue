<template>
  <div class="back-btn" @click="handleBack">
    <img src="/images/icons/ic_back.webp" alt="返回" class="back-icon" />
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const handleBack = () => {
  router.back()
}
</script>
