import { createApp } from 'vue'
import { createPinia } from 'pinia'
// Element Plus 按需引入 - 由 unplugin-vue-components 自动处理
// 只需要引入样式和语言包
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { ElConfigProvider } from 'element-plus'
// 只导入实际使用的图标（按需引入）
import {
  Search, User, Setting, VideoPlay, Upload, Star, Bell,
  Menu, PriceTag, ChatDotRound, Monitor, DataBoard, Tickets,
  Picture, Wallet, List, Coin, Lock, Warning,
  Document, Money, DataAnalysis, DataLine,
  Grid, Service, Collection, ChatLineSquare, Files, Stamp,
  Medal, Operation, Notification, FolderAdd, VideoCamera,
  UserFilled, ShoppingCart, ArrowRight, ArrowLeft, Close,
  Plus, Minus, Delete, Edit, Refresh, Loading, Check,
  CircleCheck, CircleClose, InfoFilled, WarningFilled,
  SuccessFilled, QuestionFilled, More, MoreFilled,
  House, HomeFilled, View, Hide, Calendar, Clock, Location,
  Phone, Message, Link, Share, Download, Top, Bottom,
  Back, Right, CaretRight, CaretBottom, CaretTop, CaretLeft,
  DArrowRight, DArrowLeft, Sort, SortUp, SortDown, Rank,
  Trophy, Present, Goods, ShoppingBag, CreditCard, Discount,
  Promotion, TrendCharts, PieChart, Histogram, Film, Camera,
  Microphone, Headset, Cellphone, Iphone, Platform, Connection
} from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import './styles/index.scss'
import { setupLazyLoad } from './directives/lazyLoad'

const app = createApp(App)

// 按需注册图标
const icons = {
  Search, User, Setting, VideoPlay, Upload, Star, Bell,
  Menu, PriceTag, ChatDotRound, Monitor, DataBoard, Tickets,
  Picture, Wallet, List, Coin, Lock, Warning,
  Document, Money, DataAnalysis, DataLine,
  Grid, Service, Collection, ChatLineSquare, Files, Stamp,
  Medal, Operation, Notification, FolderAdd, VideoCamera,
  UserFilled, ShoppingCart, ArrowRight, ArrowLeft, Close,
  Plus, Minus, Delete, Edit, Refresh, Loading, Check,
  CircleCheck, CircleClose, InfoFilled, WarningFilled,
  SuccessFilled, QuestionFilled, More, MoreFilled,
  House, HomeFilled, View, Hide, Calendar, Clock, Location,
  Phone, Message, Link, Share, Download, Top, Bottom,
  Back, Right, CaretRight, CaretBottom, CaretTop, CaretLeft,
  DArrowRight, DArrowLeft, Sort, SortUp, SortDown, Rank,
  Trophy, Present, Goods, ShoppingBag, CreditCard, Discount,
  Promotion, TrendCharts, PieChart, Histogram, Film, Camera,
  Microphone, Headset, Cellphone, Iphone, Platform, Connection
}
for (const [key, component] of Object.entries(icons)) {
  app.component(key, component)
}

// 使用 Pinia 状态管理
app.use(createPinia())

// 使用路由
app.use(router)

// 注册懒加载指令
setupLazyLoad(app)

// Element Plus 语言配置 - 通过 provide 方式注入
app.provide('locale', zhCn)

// 全局配置组件
app.component('ElConfigProvider', ElConfigProvider)

app.mount('#app')






