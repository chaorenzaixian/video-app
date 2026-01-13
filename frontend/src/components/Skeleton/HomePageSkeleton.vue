<template>
  <div class="home-skeleton">
    <!-- 轮播图骨架 -->
    <div class="banner-skeleton skeleton-animate"></div>
    
    <!-- 图标广告骨架 -->
    <div class="icon-ads-skeleton">
      <div class="icon-item" v-for="i in 5" :key="'icon-' + i">
        <div class="icon-circle skeleton-animate"></div>
        <div class="icon-text skeleton-animate"></div>
      </div>
    </div>
    
    <!-- 功能入口骨架 -->
    <div class="func-skeleton">
      <div class="func-item" v-for="i in 5" :key="'func-' + i">
        <div class="func-icon skeleton-animate"></div>
        <div class="func-text skeleton-animate"></div>
      </div>
    </div>
    
    <!-- 筛选栏骨架 -->
    <div class="filter-skeleton">
      <div class="filter-tabs">
        <div class="filter-tab skeleton-animate" v-for="i in 4" :key="'tab-' + i"></div>
      </div>
      <div class="filter-toggle skeleton-animate"></div>
    </div>
    
    <!-- 视频列表骨架 -->
    <div class="video-grid-skeleton">
      <div class="video-card-skeleton" v-for="i in 6" :key="'video-' + i">
        <div class="video-cover skeleton-animate"></div>
        <div class="video-info">
          <div class="video-title skeleton-animate"></div>
          <div class="video-meta">
            <div class="video-tag skeleton-animate"></div>
            <div class="video-views skeleton-animate"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
</script>

<style lang="scss" scoped>
.home-skeleton {
  padding-bottom: 20px;
}

// 骨架动画
.skeleton-animate {
  background: linear-gradient(90deg, 
    rgba(255, 255, 255, 0.03) 25%, 
    rgba(255, 255, 255, 0.08) 50%, 
    rgba(255, 255, 255, 0.03) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite ease-in-out;
}

@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

// 轮播图骨架
.banner-skeleton {
  width: calc(100% - 24px);
  margin: 0 12px;
  height: 140px;
  border-radius: 12px;
}

// 图标广告骨架
.icon-ads-skeleton {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 16px 12px;
  
  .icon-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    
    .icon-circle {
      width: 56px;
      height: 56px;
      border-radius: 14px;
    }
    
    .icon-text {
      width: 40px;
      height: 10px;
      border-radius: 4px;
    }
  }
}

// 功能入口骨架
.func-skeleton {
  display: flex;
  gap: 20px;
  padding: 12px 16px;
  overflow: hidden;
  
  .func-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
    
    .func-icon {
      width: 52px;
      height: 52px;
      border-radius: 14px;
    }
    
    .func-text {
      width: 36px;
      height: 10px;
      border-radius: 4px;
    }
  }
}

// 筛选栏骨架
.filter-skeleton {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 12px;
  margin: 0 6px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 12px 12px 0 0;
  
  .filter-tabs {
    display: flex;
    gap: 20px;
    
    .filter-tab {
      width: 60px;
      height: 14px;
      border-radius: 4px;
      
      &:first-child {
        width: 70px;
      }
    }
  }
  
  .filter-toggle {
    width: 50px;
    height: 24px;
    border-radius: 6px;
  }
}

// 视频列表骨架
.video-grid-skeleton {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  padding: 12px;
  margin: 0 6px;
  background: rgba(255, 255, 255, 0.01);
  border-radius: 0 0 12px 12px;
  
  .video-card-skeleton {
    .video-cover {
      width: 100%;
      aspect-ratio: 16/9;
      border-radius: 8px;
    }
    
    .video-info {
      padding: 8px 4px;
      
      .video-title {
        height: 14px;
        border-radius: 4px;
        margin-bottom: 8px;
      }
      
      .video-meta {
        display: flex;
        justify-content: space-between;
        
        .video-tag {
          width: 50px;
          height: 20px;
          border-radius: 4px;
        }
        
        .video-views {
          width: 40px;
          height: 12px;
          border-radius: 4px;
        }
      }
    }
  }
}
</style>
