<template>
  <el-container class="admin-layout">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapsed ? '64px' : '240px'" class="sidebar">
      <div class="logo">
        <el-icon size="28" color="#fff"><VideoPlay /></el-icon>
        <span v-show="!isCollapsed" class="logo-text">VOD Platform</span>
      </div>
      
      <el-menu
        :default-active="$route.path"
        :collapse="isCollapsed"
        :collapse-transition="false"
        background-color="#1e1e2d"
        text-color="#a2a3b7"
        active-text-color="#ffffff"
        router
      >
        <!-- 仪表盘 -->
        <el-menu-item index="/admin/dashboard">
          <el-icon><DataBoard /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>
        
        <!-- 内容管理 -->
        <el-sub-menu index="content">
          <template #title>
            <el-icon><VideoPlay /></el-icon>
            <span>内容管理</span>
          </template>
          <el-menu-item index="/admin/videos">视频列表</el-menu-item>
          <el-menu-item index="/admin/short-videos">短视频管理</el-menu-item>
          <el-menu-item index="/admin/short-categories">短视频分类</el-menu-item>
          <el-menu-item index="/admin/categories">长视频分类</el-menu-item>
          <el-menu-item index="/admin/tags">长视频标签</el-menu-item>
          <el-menu-item index="/admin/videos/upload">上传视频</el-menu-item>
          <el-menu-item index="/admin/videos/batch-upload">批量上传</el-menu-item>
          <el-menu-item index="/admin/video-review">视频审核</el-menu-item>
          <el-menu-item index="/admin/pending-videos">待处理视频</el-menu-item>
          <el-menu-item index="/admin/batch-video-ops">批量操作</el-menu-item>
          <el-menu-item index="/admin/featured">推荐管理</el-menu-item>
          <el-menu-item index="/admin/watermark-manage">水印配置</el-menu-item>
        </el-sub-menu>
        
        <!-- 用户管理 -->
        <el-sub-menu index="users">
          <template #title>
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </template>
          <el-menu-item index="/admin/users">用户列表</el-menu-item>
          <el-menu-item index="/admin/creator-manage">创作者管理</el-menu-item>
          <el-menu-item index="/admin/report-manage">举报管理</el-menu-item>
        </el-sub-menu>
        
        <!-- 会员系统 -->
        <el-sub-menu index="vip">
          <template #title>
            <el-icon><Medal /></el-icon>
            <span>会员系统</span>
          </template>
          <el-menu-item index="/admin/vip-levels">VIP等级配置</el-menu-item>
          <el-menu-item index="/admin/vip-manage">VIP卡片管理</el-menu-item>
        </el-sub-menu>
        
        <!-- 财务中心 -->
        <el-sub-menu index="finance">
          <template #title>
            <el-icon><Wallet /></el-icon>
            <span>财务中心</span>
          </template>
          <el-menu-item index="/admin/orders">订单管理</el-menu-item>
          <el-menu-item index="/admin/coins-manage">金币管理</el-menu-item>
          <el-menu-item index="/admin/finance-manage">财务流水</el-menu-item>
          <el-menu-item index="/admin/withdrawal-manage">提现审核</el-menu-item>
          <el-menu-item index="/admin/withdrawals">代理提现</el-menu-item>
        </el-sub-menu>
        
        <!-- 运营推广 -->
        <el-sub-menu index="marketing">
          <template #title>
            <el-icon><Bell /></el-icon>
            <span>运营推广</span>
          </template>
          <el-menu-item index="/admin/banner-manage">轮播图管理</el-menu-item>
          <el-menu-item index="/admin/announcements">公告管理</el-menu-item>
          <el-menu-item index="/admin/ads">广告管理</el-menu-item>
          <el-menu-item index="/admin/icon-ads">图标广告位</el-menu-item>
          <el-menu-item index="/admin/func-entries">功能入口</el-menu-item>
          <el-menu-item index="/admin/group-manage">官方群组</el-menu-item>
          <el-menu-item index="/admin/customer-service-manage">客服管理</el-menu-item>
          <el-menu-item index="/admin/customer-service-chat">在线客服</el-menu-item>
          <el-menu-item index="/admin/promotion-dashboard">推广数据</el-menu-item>
          <el-menu-item index="/admin/agents">代理管理</el-menu-item>
        </el-sub-menu>
        
        <!-- 福利任务 -->
        <el-sub-menu index="welfare">
          <template #title>
            <el-icon><Present /></el-icon>
            <span>福利任务</span>
          </template>
          <el-menu-item index="/admin/tasks-manage">任务管理</el-menu-item>
          <el-menu-item index="/admin/exchange-manage">积分兑换</el-menu-item>
          <el-menu-item index="/admin/points-query">用户积分</el-menu-item>
        </el-sub-menu>
        
        <!-- 互动管理 -->
        <el-sub-menu index="interaction">
          <template #title>
            <el-icon><ChatDotRound /></el-icon>
            <span>互动管理</span>
          </template>
          <el-menu-item index="/admin/unified-comments">评论管理中心</el-menu-item>
          <el-menu-item index="/admin/comment-announcement">评论公告</el-menu-item>
        </el-sub-menu>
        
        <!-- 社区管理 -->
        <el-sub-menu index="community">
          <template #title>
            <el-icon><ChatLineSquare /></el-icon>
            <span>社区管理</span>
          </template>
          <el-menu-item index="/admin/community-posts">帖子管理</el-menu-item>
          <el-menu-item index="/admin/community-topics">话题管理</el-menu-item>
          <el-menu-item index="/admin/gallery-manage">图集管理</el-menu-item>
          <el-menu-item index="/admin/novel-manage">小说管理</el-menu-item>
        </el-sub-menu>
        
        <!-- 暗网专区 -->
        <el-menu-item index="/admin/darkweb-manage">
          <el-icon><Lock /></el-icon>
          <span>暗网视频</span>
        </el-menu-item>
        
        <!-- 交友管理 -->
        <el-menu-item index="/admin/dating-manage">
          <el-icon><ChatDotRound /></el-icon>
          <span>交友管理</span>
        </el-menu-item>
        
        <!-- 数据中心 -->
        <el-sub-menu index="data">
          <template #title>
            <el-icon><DataAnalysis /></el-icon>
            <span>数据中心</span>
          </template>
          <el-menu-item index="/admin/statistics">数据统计</el-menu-item>
          <el-menu-item index="/admin/monitor">系统监控</el-menu-item>
          <el-menu-item index="/admin/transcode-monitor">转码监控</el-menu-item>
          <el-menu-item index="/admin/admin-logs">操作日志</el-menu-item>
        </el-sub-menu>
        
        <!-- 系统设置 -->
        <el-sub-menu index="settings">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </template>
          <el-menu-item index="/admin/site-settings">网站设置</el-menu-item>
          <el-menu-item index="/admin/system-config">系统配置</el-menu-item>
          <el-menu-item index="/admin/settings">其他设置</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>
    
    <el-container class="main-container">
      <!-- 顶部导航 -->
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="isCollapsed = !isCollapsed">
            <Fold v-if="!isCollapsed" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ $route.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <el-tooltip content="刷新" placement="bottom">
            <el-icon class="header-icon" @click="refreshPage"><Refresh /></el-icon>
          </el-tooltip>
          
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="user-info">
              <el-avatar :size="32" :src="userStore.user?.avatar">
                {{ userStore.user?.username?.charAt(0)?.toUpperCase() }}
              </el-avatar>
              <span class="username">{{ userStore.user?.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>个人中心
                </el-dropdown-item>
                <el-dropdown-item command="password">
                  <el-icon><Lock /></el-icon>修改密码
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <!-- 主内容区 -->
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessageBox } from 'element-plus'
import { Fold, Expand, ArrowDown, SwitchButton, Refresh, User, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const isCollapsed = ref(false)

onMounted(() => {
  userStore.fetchUser()
})

const refreshPage = () => {
  location.reload()
}

const handleCommand = (command) => {
  switch (command) {
    case 'profile':
      router.push('/admin/profile')
      break
    case 'password':
      router.push('/admin/password')
      break
    case 'logout':
      ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        userStore.logout()
        router.push('/admin/login')
      })
      break
  }
}
</script>

<style lang="scss" scoped>
.admin-layout {
  height: 100vh;
  
  .sidebar {
    background-color: #1e1e2d;
    transition: width 0.3s;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    height: 100vh;
    
    .logo {
      height: 64px;
      min-height: 64px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
      
      .logo-text {
        color: #fff;
        font-size: 18px;
        font-weight: 600;
        white-space: nowrap;
      }
    }
    
    .el-menu {
      flex: 1;
      overflow-y: auto;
      overflow-x: hidden;
      border-right: none;
      
      &::-webkit-scrollbar {
        width: 6px;
      }
      
      &::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 3px;
      }
      
      .el-menu-item,
      .el-sub-menu__title {
        &:hover {
          background-color: rgba(99, 102, 241, 0.1);
        }
        
        &.is-active {
          background: linear-gradient(90deg, rgba(99, 102, 241, 0.2) 0%, transparent 100%);
          border-left: 3px solid #6366f1;
        }
      }
    }
  }
  
  .main-container {
    background-color: #f0f2f5;
    
    .header {
      background-color: #fff;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 20px;
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
      
      .header-left {
        display: flex;
        align-items: center;
        gap: 16px;
        
        .collapse-btn {
          font-size: 20px;
          cursor: pointer;
          color: #666;
          
          &:hover {
            color: #6366f1;
          }
        }
      }
      
      .header-right {
        display: flex;
        align-items: center;
        gap: 20px;
        
        .header-icon {
          font-size: 18px;
          color: #666;
          cursor: pointer;
          
          &:hover {
            color: #6366f1;
          }
        }
        
        .user-info {
          display: flex;
          align-items: center;
          gap: 8px;
          cursor: pointer;
          
          .username {
            color: #333;
            font-size: 14px;
          }
        }
      }
    }
    
    .main-content {
      padding: 20px;
      overflow-y: auto;
    }
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>