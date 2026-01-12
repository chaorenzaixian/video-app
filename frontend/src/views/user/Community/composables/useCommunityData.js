/**
 * 社区数据获取逻辑
 */
import { ref, computed } from 'vue'
import api from '@/utils/api'

export function useCommunityData(signal) {
  // 分类数据
  const categoriesData = ref([])
  const topCategories = ref([])
  const topicsMap = ref({})
  const selectedCategory = ref(null)
  const selectedTopic = ref(null)
  
  // 帖子数据
  const posts = ref([])
  const loading = ref(false)
  const hasMore = ref(true)
  const page = ref(1)
  const activeFilter = ref('recommend')

  // 当前选中分类的子话题
  const currentSubTopics = computed(() => {
    if (!selectedCategory.value) return []
    const cat = categoriesData.value.find(c => c.id === selectedCategory.value)
    return cat?.children || []
  })

  // 获取分类数据
  const fetchCategories = async () => {
    try {
      const res = await api.get('/community/topics/categories', { signal })
      const data = res.data || []
      categoriesData.value = data
      topCategories.value = data.map(c => ({ id: c.id, name: c.name, icon: c.icon }))
      
      if (data.length > 0 && !selectedCategory.value) {
        selectedCategory.value = data[0].id
      }
      
      data.forEach(cat => {
        topicsMap.value[cat.id] = cat.name
        if (cat.children) {
          cat.children.forEach(t => { topicsMap.value[t.id] = t.name })
        }
      })
    } catch (e) {
      if (e.name !== 'AbortError' && e.name !== 'CanceledError') {
        console.error('获取分类失败', e)
        await fetchTopicsLegacy()
      }
    }
  }

  // 兼容旧接口
  const fetchTopicsLegacy = async () => {
    try {
      const res = await api.get('/community/topics', { params: { page_size: 30 }, signal })
      const data = res.data || []
      topCategories.value = data.map(t => ({ id: t.id, name: t.name }))
      if (data.length > 0 && !selectedCategory.value) {
        selectedCategory.value = data[0].id
      }
      data.forEach(t => { topicsMap.value[t.id] = t.name })
    } catch (e) {
      if (e.name !== 'AbortError' && e.name !== 'CanceledError') {
        console.error('获取话题失败', e)
      }
    }
  }

  // 获取帖子列表
  const fetchPosts = async (reset = false) => {
    if (loading.value) return
    if (reset) {
      page.value = 1
      hasMore.value = true
      posts.value = []
    }
    if (!hasMore.value) return

    loading.value = true
    try {
      const params = {
        page: page.value,
        page_size: 20,
        feed_type: activeFilter.value === 'video' ? 'recommend' : activeFilter.value
      }
      if (selectedTopic.value) {
        params.topic_id = selectedTopic.value
      }

      const res = await api.get('/community/posts', { params, signal })
      const data = res.data || []
      
      if (data.length < 20) hasMore.value = false
      posts.value = reset ? data : [...posts.value, ...data]
      page.value++
    } catch (e) {
      if (e.name !== 'AbortError' && e.name !== 'CanceledError') {
        console.error('获取动态失败', e)
      }
    } finally {
      loading.value = false
    }
  }

  // 点赞
  const likePost = async (post) => {
    try {
      const res = await api.post(`/community/posts/${post.id}/like`, null, { signal })
      post.is_liked = res.data.liked
      post.like_count = res.data.like_count
    } catch (e) {
      if (e.name !== 'AbortError' && e.name !== 'CanceledError') {
        console.error('点赞失败', e)
      }
    }
  }

  // 选择分类
  const selectCategory = (cat) => {
    selectedCategory.value = cat.id
    selectedTopic.value = null
    fetchPosts(true)
  }

  return {
    categoriesData,
    topCategories,
    topicsMap,
    selectedCategory,
    selectedTopic,
    currentSubTopics,
    posts,
    loading,
    hasMore,
    activeFilter,
    fetchCategories,
    fetchPosts,
    likePost,
    selectCategory
  }
}
