<template>
  <div v-if="visible" class="records-modal" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <span>充值记录</span>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>
      <div class="modal-body">
        <div v-for="record in records" :key="record.id" class="record-item">
          <div class="record-info">
            <span class="record-name">{{ record.card_name }}</span>
            <span class="record-time">{{ formatDate(record.created_at) }}</span>
          </div>
          <span class="record-amount">¥{{ record.amount }}</span>
        </div>
        <div v-if="records.length === 0" class="empty-state">暂无充值记录</div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  records: { type: Array, default: () => [] }
})

defineEmits(['close'])

const formatDate = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
</script>

<style lang="scss" scoped>
.records-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: flex-end;
  z-index: 200;
}

.modal-content {
  width: 100%;
  max-height: 60vh;
  background: #1a1a2e;
  border-radius: 20px 20px 0 0;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);

  span { font-size: 18px; font-weight: 600; color: #fff; }

  .close-btn {
    width: 30px;
    height: 30px;
    background: rgba(255, 255, 255, 0.1);
    border: none;
    border-radius: 50%;
    color: #fff;
    font-size: 20px;
    cursor: pointer;
  }
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 0 20px;
}

.record-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);

  .record-info {
    display: flex;
    flex-direction: column;
    gap: 4px;

    .record-name { font-size: 14px; color: #fff; }
    .record-time { font-size: 12px; color: rgba(255, 255, 255, 0.4); }
  }

  .record-amount { font-size: 16px; font-weight: 600; color: #a855f7; }
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: rgba(255, 255, 255, 0.4);
}
</style>
