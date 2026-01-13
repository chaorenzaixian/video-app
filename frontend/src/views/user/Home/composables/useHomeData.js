/**
 * 首页数据获取逻辑
 */
import { ref, computed } from 'vue'
import axios from 'axios'

// 缓存Key
const CACHE_KEY = 'home_data_cache'
const CACHE_EXPIRE = 30 * 60 * 1000 // 30分钟过期

export function useHomeData(abortSignal) {
  // 网站设置
  const siteSettings = ref({
    siteName: '视频站',
    logo: ''
  })

  // 分类数据
  const categories = ref([
    { id: 0, name: '推荐' },
    { id: 1, name: '国产' },
    { id: 2, name: '日韩' },
    { id: 3, name: '欧美' },
    { id: 4, name: '动漫' },
    { id: 5, name: '直播' }
  ])
  const activeCategory = ref(0)
  const featuredCategories = ref([])

  // 功能入口
  const funcItems = ref([])

  // 广告位
  const adRow1 = ref([])
  const adRow2 = ref([])

  // 公告
  const announcements = ref([])
  const announcementText = ref('限时"尊享永久卡" 消费一次终身受益 还送10次AI脱衣 🎁 女神视频永久免费看')

  // 轮播广告
  const banners = ref([])

  // 视频列表
  const videos = ref([])
  const loadingVideos = ref(false)

  // 离线状态
  const isOffline = ref(false)
  const hasCache = ref(false)

  // 视频筛选
  const videoFilters = [
    { label: '热门推荐', key: 'hot' },
    { label: '最新上架', key: 'created_at' },
    { label: '最多观看', key: 'view_count' },
    { label: '最多收藏', key: 'favorite_count' }
  ]
  const activeVideoFilter = ref(0)

  // 获取当前选中分类的子分类
  const currentSubCategories = computed(() => {
    if (activeCategory.value === 0) {
      return featuredCategories.value
    }
    const currentCat = categories.value.find(cat => cat.id === activeCategory.value)
    return currentCat?.children || []
  })

  // 保存缓存
  const saveCache = (data) => {
    try {
      const cacheData = {
        data,
        timestamp: Date.now()
      }
      localStorage.setItem(CACHE_KEY, JSON.stringify(cacheData))
    } catch (e) {
      console.warn('缓存保存失败', e)
    }
  }

  // 读取缓存
  const loadCache = () => {
    try {
      const cached = localStorage.getItem(CACHE_KEY)
      if (cached) {
        const { data, timestamp } = JSON.parse(cached)
        // 检查是否过期
        if (Date.now() - timestamp < CACHE_EXPIRE) {
          return data
        }
      }
    } catch (e) {
      console.warn('缓存读取失败', e)
    }
    return null
  }

  // 应用数据到状态
  const applyData = (data) => {
    if (!data) return
    
    // 网站设置
    if (data.site_settings) {
      siteSettings.value = {
        siteName: data.site_settings.site_name || '视频站',
        logo: data.site_settings.logo || ''
      }
    }
    
    // 分类
    if (data.categories && data.categories.length > 0) {
      const allCategories = data.categories
      const featured = []
      const extractFeatured = (list) => {
        for (const cat of list) {
          if (cat.is_featured) {
            featured.push({ id: cat.id, name: cat.name })
          }
          if (cat.children && cat.children.length > 0) {
            extractFeatured(cat.children)
          }
        }
      }
      extractFeatured(allCategories)
      featuredCategories.value = featured
      categories.value = [{ id: 0, name: '推荐', children: [] }, ...allCategories]
    }
    
    // 功能入口
    if (data.func_entries && data.func_entries.length > 0) {
      funcItems.value = data.func_entries.map(item => ({ ...item, imageError: false }))
    }
    
    // 图标广告
    if (data.icon_ads) {
      adRow1.value = data.icon_ads.slice(0, 5)
      adRow2.value = data.icon_ads.slice(5, 10)
    }
    
    // 公告
    if (data.announcements && data.announcements.length > 0) {
      announcements.value = data.announcements
      announcementText.value = data.announcements.map(a => a.content).join(' 🔸 ')
    }
    
    // 轮播图
    if (data.banners) {
      banners.value = data.banners
    }
    
    // 视频列表
    if (data.videos) {
      videos.value = data.videos
    }
  }

  // 首页聚合接口
  const fetchHomeInit = async () => {
    loadingVideos.value = true
    isOffline.value = false
    
    try {
      const sortBy = videoFilters[activeVideoFilter.value].key
      const res = await axios.get('/api/v1/home/init', {
        params: {
          category_id: activeCategory.value === 0 ? null : activeCategory.value,
          sort_by: sortBy,
          limit: 20
        },
        signal: abortSignal
      })
      
      const data = res.data
      if (data) {
        applyData(data)
        // 保存到缓存
        saveCache(data)
        hasCache.value = true
      }
    } catch (e) {
      if (e.name !== 'CanceledError' && e.name !== 'AbortError') {
        console.error('获取首页数据失败', e)
        // 网络错误，尝试加载缓存
        isOffline.value = true
        const cachedData = loadCache()
        if (cachedData) {
          applyData(cachedData)
          hasCache.value = true
        } else {
          hasCache.value = false
        }
      }
    } finally {
      loadingVideos.value = false
    }
  }

  // 获取视频列表
  const fetchVideos = async () => {
    loadingVideos.value = true
    try {
      const sortBy = videoFilters[activeVideoFilter.value].key
      const params = { sort_by: sortBy, limit: 20 }
      if (activeCategory.value !== 0) {
        params.category_id = activeCategory.value
      }
      const res = await axios.get('/api/v1/home/videos', { params, signal: abortSignal })
      if (res.data && res.data.videos) {
        videos.value = res.data.videos
      }
    } catch (e) {
      if (e.name !== 'CanceledError' && e.name !== 'AbortError') {
        console.error('获取视频列表失败', e)
      }
    } finally {
      loadingVideos.value = false
    }
  }

  // 切换视频筛选
  const changeVideoFilter = (index) => {
    activeVideoFilter.value = index
    fetchVideos()
  }

  // 选择分类
  const selectCategory = (catId) => {
    activeCategory.value = catId
    fetchVideos()
  }

  // 重试加载
  const retryLoad = () => {
    isOffline.value = false
    fetchHomeInit()
  }

  return {
    siteSettings,
    categories,
    activeCategory,
    featuredCategories,
    currentSubCategories,
    funcItems,
    adRow1,
    adRow2,
    announcements,
    announcementText,
    banners,
    videos,
    loadingVideos,
    isOffline,
    hasCache,
    videoFilters,
    activeVideoFilter,
    fetchHomeInit,
    fetchVideos,
    changeVideoFilter,
    selectCategory,
    retryLoad
  }
}
