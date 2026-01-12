/**
 * 小说数据获取逻辑
 */
import { ref } from 'vue'
import api from '@/utils/api'

export function useNovelData(signal) {
  const novelCategories = ref([])
  const selectedNovelType = ref('text')
  const selectedNovelCategory = ref(null)
  const novelItems = ref([])
  const loading = ref(false)

  // 获取小说分类
  const fetchNovelCategories = async () => {
    try {
      const res = await api.get('/gallery-novel/novel/categories', { 
        params: { novel_type: selectedNovelType.value },
        signal 
      })
      novelCategories.value = [
        { id: null, name: '全部' },
        ...(res.data || [])
      ]
    } catch (e) {
      if (e.name !== 'AbortError' && e.name !== 'CanceledError') {
        console.error('获取小说分类失败', e)
      }
    }
  }

  // 获取小说列表
  const fetchNovels = async () => {
    loading.value = true
    try {
      const params = { page: 1, page_size: 30, novel_type: selectedNovelType.value }
      if (selectedNovelCategory.value) {
        params.category_id = selectedNovelCategory.value
      }
      const res = await api.get('/gallery-novel/novel/list', { params, signal })
      novelItems.value = (res.data || []).map(n => ({
        id: n.id,
        title: n.title,
        author: n.author || '佚名',
        cover: n.cover,
        chapters: n.chapter_count,
        status: n.status
      }))
    } catch (e) {
      if (e.name !== 'AbortError' && e.name !== 'CanceledError') {
        console.error('获取小说失败', e)
      }
    } finally {
      loading.value = false
    }
  }

  // 切换小说类型
  const switchNovelType = (type) => {
    selectedNovelType.value = type
    selectedNovelCategory.value = null
    fetchNovelCategories()
    fetchNovels()
  }

  // 选择分类
  const selectNovelCategory = (catId) => {
    selectedNovelCategory.value = catId
    fetchNovels()
  }

  return {
    novelCategories,
    selectedNovelType,
    selectedNovelCategory,
    novelItems,
    loading,
    fetchNovelCategories,
    fetchNovels,
    switchNovelType,
    selectNovelCategory
  }
}
