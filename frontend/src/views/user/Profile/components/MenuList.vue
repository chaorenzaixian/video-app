<template>
  <div class="menu-section">
    <div v-for="item in menuItems" :key="item.path" class="menu-row" @click="handleClick(item)">
      <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" v-html="item.icon"></svg>
      <span class="menu-text">{{ item.label }}</span>
      <span v-if="item.badge" class="menu-badge" :class="item.badge.type">{{ item.badge.text }}</span>
      <svg class="menu-arrow" viewBox="0 0 24 24" fill="currentColor"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/></svg>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
const emit = defineEmits(['check-update'])

const menuItems = [
  { path: '/user/creator-center', label: '创作中心', icon: '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>' },
  { path: '/user/follows', label: '关注/粉丝', icon: '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>' },
  { path: '/user/account-credential', label: '账号凭证', icon: '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/><path d="M9 16l2 2 4-4"/>' },
  { path: '/user/lock', label: '锁屏密码', icon: '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>' },
  { path: '/user/invite-share', label: '邀请分享', icon: '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>' },
  { path: '/user/promotion', label: '推广中心', icon: '<path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"/>', badge: { text: '赚VIP', type: 'hot' } },
  { path: '/user/downloads', label: '我的下载', icon: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>' },
  { path: '/user/likes', label: '我的喜欢', icon: '<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>' },
  { path: '/user/redeem', label: '领取兑换', icon: '<path d="M21 5H3a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h18a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2z"/><path d="M12 12m-3 0a3 3 0 1 0 6 0a3 3 0 1 0-6 0"/><path d="M3 9h2M19 9h2M3 15h2M19 15h2"/>' },
  { path: '/user/app-recommend', label: '应用推荐', icon: '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>' },
  { path: '/user/customer-service', label: '联系客服', icon: '<path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/>' },
  { path: '/user/groups', label: '官方群组', icon: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>' },
  { path: 'check-update', label: '检查更新', icon: '<polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>' }
]

const handleClick = (item) => {
  if (item.path === 'check-update') {
    emit('check-update')
  } else {
    router.push(item.path)
  }
}
</script>

<style lang="scss" scoped>
.menu-section {
  margin: 0 clamp(12px, 4vw, 20px);
  background: rgba(255, 255, 255, 0.03);
  border-radius: clamp(10px, 3.5vw, 16px);
  overflow: hidden;
}

.menu-row {
  display: flex;
  align-items: center;
  padding: clamp(12px, 4vw, 18px) clamp(14px, 4.5vw, 20px);
  cursor: pointer;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  transition: background 0.2s;
  &:hover { background: rgba(255, 255, 255, 0.03); }
  &:last-child { border-bottom: none; }
}

.menu-icon {
  width: clamp(18px, 5.5vw, 24px);
  height: clamp(18px, 5.5vw, 24px);
  color: rgba(255, 255, 255, 0.55);
  margin-right: clamp(10px, 3.5vw, 16px);
}

.menu-text {
  flex: 1;
  font-size: clamp(14px, 3.5vw, 14px);
  color: rgba(255, 255, 255, 0.85);
}

.menu-arrow {
  width: clamp(16px, 5vw, 22px);
  height: clamp(16px, 5vw, 22px);
  color: rgba(255, 255, 255, 0.25);
}

.menu-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  margin-right: 8px;

  &.hot {
    background: linear-gradient(135deg, #f97316, #ea580c);
    color: #fff;
  }
}
</style>
