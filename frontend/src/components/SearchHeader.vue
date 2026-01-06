<template>
  <div class="search-header-wrapper">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="back-btn" @click="goBack">
        <span>‹</span>
      </div>
      <div class="header-tabs">
        <div 
          :class="['tab', { active: currentPage === 'search' || currentPage === 'result' }]"
          @click="goToSearch"
        >
          搜一搜
        </div>
        <div 
          :class="['tab', { active: currentPage === 'library' }]"
          @click="goToLibrary"
        >
          视频库
        </div>
      </div>
    </header>

    <!-- 搜索框（可选显示） -->
    <div class="search-box" v-if="showSearchBox">
      <div class="search-input-wrapper">
        <div class="search-icon">
          <svg viewBox="0 0 24 24" fill="none">
            <circle cx="10" cy="10" r="7" stroke="currentColor" stroke-width="2"/>
            <line x1="15" y1="15" x2="21" y2="21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
        <input 
          v-model="localKeyword" 
          type="text" 
          :placeholder="placeholder"
          @keyup.enter="handleSearch"
        />
        <!-- 清除按钮 -->
        <div class="clear-input" v-if="localKeyword" @click="clearKeyword">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
            <path d="M6 6l12 12M18 6l-12 12"/>
          </svg>
        </div>
        <!-- 搜索按钮在框内 -->
        <button class="search-btn" @click="handleSearch">搜索</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const props = defineProps({
  currentPage: {
    type: String,
    default: 'search' // 'search' | 'result' | 'library'
  },
  showSearchBox: {
    type: Boolean,
    default: true
  },
  keyword: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['search', 'update:keyword'])

const router = useRouter()
const route = useRoute()

const localKeyword = ref(props.keyword)

// 同步外部keyword变化
watch(() => props.keyword, (val) => {
  localKeyword.value = val
})

// 同步本地keyword到外部
watch(localKeyword, (val) => {
  emit('update:keyword', val)
})

const goBack = () => {
  router.push('/user')
}

const goToSearch = () => {
  if (props.currentPage !== 'search' && props.currentPage !== 'result') {
    // 获取上次搜索的关键词
    const lastKeyword = sessionStorage.getItem('lastSearchKeyword')
    if (lastKeyword) {
      router.push({
        path: '/user/search-result',
        query: { keyword: lastKeyword }
      })
    } else {
      router.push('/user/search')
    }
  }
}

const goToLibrary = () => {
  // 保存当前搜索关键词
  if (localKeyword.value && localKeyword.value.trim()) {
    sessionStorage.setItem('lastSearchKeyword', localKeyword.value.trim())
  }
  router.push('/user/video-library')
}

const handleSearch = () => {
  if (localKeyword.value.trim()) {
    // 保存搜索关键词
    sessionStorage.setItem('lastSearchKeyword', localKeyword.value.trim())
    emit('search', localKeyword.value.trim())
    // 如果不在搜索结果页，跳转过去
    if (route.path !== '/user/search-result') {
      router.push({
        path: '/user/search-result',
        query: { keyword: localKeyword.value.trim() }
      })
    }
  }
}

const clearKeyword = () => {
  localKeyword.value = ''
  emit('update:keyword', '')
}
</script>

<style lang="scss" scoped>
.search-header-wrapper {
  background: #0a0a12;
}

// 顶部导航
.page-header {
  display: flex;
  align-items: center;
  padding: 16px;
  background: #0a0a12;
  
  .back-btn {
    font-size: 36px;
    color: #a855f7;
    cursor: pointer;
    font-weight: 400;
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    
    &:active {
      opacity: 0.7;
    }
  }
  
  .header-tabs {
    flex: 1;
    display: flex;
    justify-content: center;
    gap: 32px;
    margin-right: 44px;
    
    .tab {
      font-size: clamp(15px, 4vw, 17px);
      color: rgba(255, 255, 255, 0.5);
      cursor: pointer;
      padding: 8px 0;
      position: relative;
      transition: color 0.3s;
      
      &.active {
        color: #fff;
        font-weight: 600;
        
        &::after {
          content: '';
          position: absolute;
          bottom: 0;
          left: 50%;
          transform: translateX(-50%);
          width: 24px;
          height: 3px;
          background: #a855f7;
          border-radius: 2px;
        }
      }
    }
  }
}

// 搜索框
.search-box {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 24px 8px;
  
  .search-input-wrapper {
    flex: 1;
    max-width: 540px;
    display: flex;
    align-items: center;
    background: #0a0a12;
    border-radius: 22px;
    padding: 0 5px 0 14px;
    height: 44px;
    box-sizing: border-box;
    border: 1px solid #a855f7;
    
    .search-icon {
      width: clamp(16px, 4.5vw, 20px);
      height: clamp(16px, 4.5vw, 20px);
      color: #a855f7;
      margin-right: clamp(6px, 2vw, 10px);
      flex-shrink: 0;
      
      svg {
        width: 100%;
        height: 100%;
      }
    }
    
    input {
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      color: #a855f7;
      font-size: clamp(14px, 3.8vw, 16px);
      padding: clamp(3px, 1vw, 5px) 0;
      
      &::placeholder {
        color: rgba(168, 85, 247, 0.5);
      }
    }
    
    .clear-input {
      width: clamp(20px, 5vw, 26px);
      height: clamp(20px, 5vw, 26px);
      cursor: pointer;
      margin-left: clamp(4px, 1.5vw, 8px);
      margin-right: clamp(18px, 4vw, 28px);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      background: rgba(255, 255, 255, 0.15);
      border-radius: 50%;
      padding: 4px;
      
      svg {
        width: 100%;
        height: 100%;
        color: rgba(255, 255, 255, 0.6);
      }
      
      &:hover {
        background: rgba(255, 255, 255, 0.25);
      }
      
      &:active {
        opacity: 0.7;
      }
    }
    
    .search-btn {
      background: linear-gradient(135deg, #a855f7, #7c3aed);
      border: none;
      color: #fff;
      padding: 0 22px;
      height: 34px !important;
      min-height: 34px !important;
      line-height: 34px;
      border-radius: 17px;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.3s;
      flex-shrink: 0;
      
      &:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.4);
      }
      
      &:active {
        transform: scale(0.98);
      }
    }
  }
}

// 小屏幕
@media (max-width: 480px) {
  .page-header {
    padding: 12px;
    
    .header-tabs {
      gap: 20px;
      .tab { font-size: 15px; }
    }
  }
  
  .search-box {
    padding: 0 16px 8px;
  }
}

// 平板
@media (min-width: 768px) {
  .page-header {
    padding: 20px 24px;
    
    .header-tabs {
      gap: 40px;
      .tab { font-size: 18px; }
    }
  }
  
  .search-box {
    padding: 0 40px 16px;
    
    .search-input-wrapper {
      max-width: 540px;
    }
  }
}
</style>
