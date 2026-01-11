import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import path from 'path'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
    }),
    Components({
      resolvers: [ElementPlusResolver()],
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        timeout: 300000
      },
      '/uploads': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  // ========== 构建优化 ==========
  build: {
    // 代码分割 - 把大依赖分开打包
    rollupOptions: {
      output: {
        manualChunks: {
          // Vue 核心
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          // Element Plus 单独打包
          'element-plus': ['element-plus', '@element-plus/icons-vue'],
          // 视频播放器
          'video-player': ['artplayer', 'hls.js'],
          // 图表（如果用到）
          'charts': ['echarts', 'vue-echarts'],
          // 工具库
          'utils': ['axios', 'dayjs', 'qrcode']
        }
      }
    },
    // 压缩配置
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,   // 生产环境移除 console
        drop_debugger: true   // 移除 debugger
      }
    },
    // 关闭 sourcemap（生产环境不需要）
    sourcemap: false,
    // chunk 大小警告阈值
    chunkSizeWarningLimit: 1000
  }
})





