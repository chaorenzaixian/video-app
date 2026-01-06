import { createApp } from 'vue'
import { createPinia } from 'pinia'
// Element Plus 按需引入 - 由 unplugin-vue-components 自动处理
// 只需要引入样式和语言包
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { ElConfigProvider } from 'element-plus'
// 导入所有 Element Plus 图标
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import './styles/index.scss'

const app = createApp(App)

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 使用 Pinia 状态管理
app.use(createPinia())

// 使用路由
app.use(router)

// Element Plus 语言配置 - 通过 provide 方式注入
app.provide('locale', zhCn)

// 全局配置组件
app.component('ElConfigProvider', ElConfigProvider)

app.mount('#app')






