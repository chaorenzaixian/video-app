<template>
  <div class="app-recommend-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="$router.push('/user/profile')">‹</div>
      <nav class="header-tabs">
        <span class="tab-item" @click="$router.push('/user/agent')">代理赚钱</span>
        <span class="tab-item" @click="$router.push('/user/tasks')">福利任务</span>
        <span class="tab-item active">应用推荐</span>
      </nav>
    </header>

    <!-- 内容区Tab切换 -->
    <div class="content-tabs">
      <span 
        :class="['tab-item', { active: activeTab === 'apps' }]"
        @click="activeTab = 'apps'"
      >应用</span>
      <span 
        :class="['tab-item', { active: activeTab === 'chess' }]"
        @click="activeTab = 'chess'"
      >棋牌</span>
    </div>

    <!-- 应用Tab内容 -->
    <div v-if="activeTab === 'apps'" class="apps-content">
      <!-- 顶部Banner -->
      <div class="top-banner"></div>

      <!-- 官方推荐 -->
      <div class="section" v-if="officialApps.length > 0">
        <h3 class="section-title">官方推荐</h3>
        <div class="app-grid">
          <div 
            class="app-item" 
            v-for="app in officialApps" 
            :key="app.id"
            @click="openApp(app)"
          >
            <div class="app-icon">
              <img :src="app.icon" :alt="app.name" @error="handleIconError($event)" />
            </div>
            <span class="app-name">{{ app.name }}</span>
          </div>
        </div>
      </div>

      <!-- 热门应用 -->
      <div class="section" v-if="hotApps.length > 0">
        <h3 class="section-title">热门应用</h3>
        <div class="app-list">
          <div 
            class="app-list-item" 
            v-for="app in hotApps" 
            :key="app.id"
            @click="openApp(app)"
          >
            <div class="app-icon-large">
              <img :src="app.icon" :alt="app.name" @error="handleIconError($event)" />
            </div>
            <div class="app-info">
              <span class="app-name">{{ app.name }}</span>
              <span class="app-desc" v-if="app.desc">{{ app.desc }}</span>
            </div>
            <button class="download-btn" @click.stop="openApp(app)">立即下载</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 棋牌Tab内容 -->
    <div v-if="activeTab === 'chess'" class="chess-content">
      <!-- 热门推荐 -->
      <div class="section">
        <h3 class="section-title">热门推荐</h3>
        <div class="chess-list">
          <div 
            class="chess-item" 
            v-for="item in chessApps" 
            :key="item.id"
            @click="openApp(item)"
          >
            <img :src="item.banner" :alt="item.name" class="chess-banner" />
            <span class="chess-name">{{ item.name }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部安全间距 -->
    <div class="bottom-safe"></div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const activeTab = ref('apps')

// 官方推荐应用（从广告位获取）
const officialApps = ref([])

// 热门应用（从广告位获取）
const hotApps = ref([])

// 棋牌应用（从广告位获取）
const chessApps = ref([])

// 获取图标广告
const fetchIconAds = async () => {
  try {
    const res = await axios.get('/api/v1/ads/icons')
    const ads = (res.data || []).filter(ad => ad.is_active !== false)
    
    // 官方推荐使用全部图标广告
    officialApps.value = ads.map(ad => ({
      id: ad.id,
      name: ad.name,
      icon: ad.image,
      url: ad.link || '#'
    }))
    
    // 热门应用取前5个
    hotApps.value = ads.slice(0, 5).map(ad => ({
      id: ad.id,
      name: ad.name,
      icon: ad.image,
      desc: ad.description || '',
      url: ad.link || '#'
    }))
  } catch (error) {
    console.error('获取图标广告失败:', error)
  }
}

// 获取棋牌广告（Banner类型）
const fetchChessAds = async () => {
  try {
    const res = await axios.get('/api/v1/home/banners', { params: { position: 'chess' } })
    const ads = res.data || []
    
    chessApps.value = ads.map(ad => ({
      id: ad.id,
      name: ad.name,
      banner: ad.image,
      url: ad.link || '#'
    }))
    
    // 如果没有棋牌广告，使用默认
    if (chessApps.value.length === 0) {
      chessApps.value = [
        { id: 1, name: '美高梅', banner: '/images/backgrounds/chess_banner_1.webp', url: '#' },
        { id: 2, name: '新葡京', banner: '/images/backgrounds/chess_banner_2.webp', url: '#' }
      ]
    }
  } catch (error) {
    console.error('获取棋牌广告失败:', error)
    // 使用默认
    chessApps.value = [
      { id: 1, name: '美高梅', banner: '/images/backgrounds/chess_banner_1.webp', url: '#' },
      { id: 2, name: '新葡京', banner: '/images/backgrounds/chess_banner_2.webp', url: '#' }
    ]
  }
}

onMounted(() => {
  fetchIconAds()
  fetchChessAds()
})

const handleIconError = (event) => {
  event.target.src = '/images/default-app-icon.webp'
}

const openApp = (app) => {
  if (app.url && app.url !== '#') {
    window.open(app.url, '_blank')
  } else {
    ElMessage.info('敬请期待')
  }
}
</script>

<style lang="scss" scoped>
.app-recommend-page {
  min-height: 100vh;
  background: #0a0a0a;
  color: #fff;
  padding-bottom: 80px;
}

// 顶部导航
.page-header {
  display: flex;
  align-items: center;
  padding: 12px 8px;
  padding-top: calc(env(safe-area-inset-top, 16px) + 12px);
  gap: 12px;
  position: sticky;
  top: 0;
  z-index: 100;
  background: linear-gradient(180deg, rgba(30, 25, 40, 1) 0%, rgba(30, 25, 40, 0.95) 100%);
  
  .back-btn {
    font-size: 33px;
    color: #fff;
    cursor: pointer;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
  }
  
  .header-tabs {
    display: flex;
    flex: 1;
    justify-content: space-around;
    align-items: center;
    
    .tab-item {
      font-size: 15px;
      color: rgba(255, 255, 255, 0.5);
      cursor: pointer;
      position: relative;
      padding-bottom: 6px;
      
      &.active {
        color: #fff;
        font-weight: 600;
        
        &::after {
          content: '';
          position: absolute;
          bottom: 0;
          left: 50%;
          transform: translateX(-50%);
          width: 20px;
          height: 2px;
          background: linear-gradient(90deg, #d4af37, #f5d799);
          border-radius: 1px;
        }
      }
    }
  }
}

// 内容区Tab
.content-tabs {
  display: flex;
  gap: 30px;
  padding: 16px 20px;
  
  .tab-item {
    font-size: 16px;
    color: rgba(255, 255, 255, 0.5);
    cursor: pointer;
    position: relative;
    padding-bottom: 8px;
    
    &.active {
      color: #a855f7;
      font-weight: 600;
      
      &::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: #a855f7;
        border-radius: 1px;
      }
    }
  }
}

// 顶部Banner
.top-banner {
  margin: 0 16px 20px;
  border-radius: 12px;
  overflow: hidden;
  background-image: url('/images/backgrounds/bg_id_card.png');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  height: 120px;
}

// 区块
.section {
  margin-bottom: 24px;
  
  .section-title {
    font-size: 18px;
    font-weight: 600;
    margin: 0 16px 16px;
    color: #fff;
  }
}

// 应用网格
.app-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px 12px;
  padding: 0 16px;
  
  .app-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    
    .app-icon {
      width: 60px;
      height: 60px;
      border-radius: 14px;
      overflow: hidden;
      background: #1a1a1a;
      
      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
    }
    
    .app-name {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.8);
      text-align: center;
      max-width: 60px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    &:active {
      transform: scale(0.95);
    }
  }
}

// 应用列表
.app-list {
  padding: 0 16px;
  
  .app-list-item {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    
    &:last-child {
      border-bottom: none;
    }
    
    .app-icon-large {
      width: 70px;
      height: 70px;
      border-radius: 16px;
      overflow: hidden;
      background: #1a1a1a;
      flex-shrink: 0;
      
      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
    }
    
    .app-info {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 4px;
      min-width: 0;
      
      .app-name {
        font-size: 16px;
        font-weight: 600;
        color: #fff;
      }
      
      .app-desc {
        font-size: 13px;
        color: rgba(255, 255, 255, 0.5);
      }
    }
    
    .download-btn {
      padding: 8px 16px;
      background: linear-gradient(135deg, #8b5cf6, #a855f7);
      border: none;
      border-radius: 25px;
      color: #fff;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      flex-shrink: 0;
      
      &:active {
        transform: scale(0.95);
      }
    }
  }
}

// 棋牌列表
.chess-list {
  padding: 0 16px;
  
  .chess-item {
    margin-bottom: 20px;
    cursor: pointer;
    
    .chess-banner {
      width: 100%;
      height: auto;
      border-radius: 12px;
      display: block;
    }
    
    .chess-name {
      display: block;
      margin-top: 10px;
      font-size: 14px;
      color: rgba(255, 255, 255, 0.7);
    }
    
    &:active {
      transform: scale(0.98);
    }
  }
}

// 底部安全间距
.bottom-safe {
  height: 20px;
}
</style>

