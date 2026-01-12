<template>
  <div class="user-section">
    <div class="user-row">
      <div class="avatar-wrapper">
        <div :class="['avatar-container', { 'is-vip': user.is_vip }]">
          <div class="avatar-frame">
            <img :src="avatarUrl" class="user-avatar" />
          </div>
          <div class="vip-crown" v-if="user.is_vip">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M5 16L3 5l5.5 5L12 4l3.5 6L21 5l-2 11H5zm14 3c0 .6-.4 1-1 1H6c-.6 0-1-.4-1-1v-1h14v1z"/></svg>
          </div>
          <div class="gender-icon">♂</div>
        </div>
      </div>
      <div class="user-info">
        <div class="nickname-row">
          <h2 class="nickname">{{ loading ? '加载中...' : (user.nickname || user.username || '未登录') }}</h2>
          <img v-if="user.vip_level > 0" :src="vipLevelIcon" class="vip-level-badge-inline" :alt="vipLevelName" />
        </div>
        <div class="user-id-row">
          <span class="user-id">{{ loading ? '--------' : user.username }}</span>
          <svg v-if="!loading && user.username" class="copy-btn" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" @click="$emit('copy')">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
          </svg>
        </div>
      </div>
      <div class="sign-btn" :class="{ disabled: signingIn }" @click="$emit('sign')">
        <img src="/images/backgrounds/ic_sign.webp" class="sign-icon-img" alt="签到" />
        <span>{{ signingIn ? '签到中...' : '签到' }}</span>
      </div>
    </div>
    <div class="stats-row" style="height: 50px;"></div>
  </div>
</template>

<script setup>
defineProps({
  user: { type: Object, default: () => ({}) },
  avatarUrl: { type: String, default: '' },
  vipLevelIcon: { type: String, default: '' },
  vipLevelName: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  signingIn: { type: Boolean, default: false }
})

defineEmits(['copy', 'sign'])
</script>

<style lang="scss" scoped>
.user-section {
  position: relative;
  z-index: 10;
  padding: 0 clamp(14px, 5vw, 24px) clamp(4px, 1vw, 8px);
}

.user-row {
  display: flex;
  align-items: flex-start;
  gap: clamp(10px, 3.5vw, 18px);
  margin-bottom: clamp(10px, 3vw, 16px);
}

.avatar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: clamp(4px, 1.5vw, 8px);
}

.avatar-container {
  position: relative;

  .avatar-frame {
    width: clamp(58px, 18vw, 80px);
    height: clamp(58px, 18vw, 80px);
    border-radius: 50%;
    padding: 2px;
    background: rgba(255, 255, 255, 0.1);

    .user-avatar {
      width: 100%;
      height: 100%;
      border-radius: 50%;
      object-fit: cover;
      background: #1a1a1a;
    }
  }

  &.is-vip .avatar-frame {
    padding: 3px;
    background: linear-gradient(135deg, #ffd700 0%, #ffec8b 25%, #daa520 50%, #ffd700 75%, #ffec8b 100%);
    background-size: 200% 200%;
    animation: vip-border-shine 3s ease-in-out infinite;
    box-shadow: 0 0 10px rgba(255, 215, 0, 0.4), 0 0 20px rgba(255, 215, 0, 0.2);
  }

  .vip-crown {
    position: absolute;
    top: -6px;
    right: -4px;
    width: clamp(20px, 6vw, 28px);
    height: clamp(20px, 6vw, 28px);
    background: linear-gradient(135deg, #ffd700, #ffec8b);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 8px rgba(255, 215, 0, 0.5);
    animation: crown-bounce 2s ease-in-out infinite;

    svg { width: clamp(14px, 4vw, 18px); height: clamp(14px, 4vw, 18px); fill: #8b4513; }
  }

  .gender-icon {
    position: absolute;
    bottom: -2px;
    left: -2px;
    width: clamp(18px, 5.5vw, 24px);
    height: clamp(18px, 5.5vw, 24px);
    background: #4a90d9;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: clamp(12px, 3.5vw, 16px);
    border: 2px solid #0d0d0d;
  }
}

.user-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: clamp(58px, 18vw, 80px);

  .nickname-row {
    display: flex;
    align-items: center;
    gap: clamp(6px, 2vw, 10px);
    margin-bottom: clamp(6px, 2vw, 10px);

    .vip-level-badge-inline {
      height: clamp(18px, 5vw, 24px);
      width: auto;
      max-width: clamp(50px, 15vw, 70px);
      object-fit: contain;
      animation: vip-badge-glow 2s ease-in-out infinite;
      flex-shrink: 0;
    }
  }

  .nickname {
    font-size: clamp(14px, 4vw, 18px);
    font-weight: 600;
    margin: 0;
    line-height: 1.5;
    background: linear-gradient(135deg, #ffd700 0%, #ffec8b 30%, #daa520 60%, #ffd700 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .user-id-row {
    display: flex;
    align-items: center;
    gap: clamp(4px, 1.5vw, 8px);

    .user-id {
      font-size: clamp(14px, 3.5vw, 14px);
      color: rgba(255, 255, 255, 0.45);
      &::before { content: '账号: '; color: rgba(255, 255, 255, 0.35); }
    }

    .copy-btn {
      width: clamp(12px, 3.5vw, 16px);
      height: clamp(12px, 3.5vw, 16px);
      color: rgba(255, 255, 255, 0.35);
      cursor: pointer;
      transition: color 0.2s;
      &:hover { color: rgba(255, 255, 255, 0.7); }
      &:active { transform: scale(0.9); }
    }
  }
}

.sign-btn {
  display: flex;
  align-items: center;
  gap: clamp(4px, 1.5vw, 8px);
  padding: clamp(8px, 2.5vw, 12px) clamp(12px, 4vw, 18px);
  background: rgba(255, 255, 255, 0.08);
  border-radius: clamp(6px, 2vw, 10px);
  cursor: pointer;
  font-size: clamp(12px, 3.5vw, 15px);
  transition: background 0.2s;
  &:hover { background: rgba(255, 255, 255, 0.12); }
  &.disabled { opacity: 0.6; pointer-events: none; }

  .sign-icon-img {
    width: clamp(18px, 5vw, 24px);
    height: clamp(18px, 5vw, 24px);
    object-fit: contain;
  }
}

@keyframes vip-border-shine {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

@keyframes crown-bounce {
  0%, 100% { transform: translateY(0) rotate(-5deg); }
  50% { transform: translateY(-3px) rotate(5deg); }
}

@keyframes vip-badge-glow {
  0%, 100% { filter: drop-shadow(0 0 3px rgba(255, 215, 0, 0.4)); transform: scale(1); }
  50% { filter: drop-shadow(0 0 6px rgba(255, 215, 0, 0.7)); transform: scale(1.05); }
}
</style>
