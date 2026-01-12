/**
 * 图集数据获取逻辑
 */
import { ref } from 'vue'
import api from '@/utils/api'

export function useGalleryData(signal) {
  const galleryCategories = ref([])
  const selectedGalleryCategory = ref(null)
  const galleryItems = ref([])
  const loading = ref(false)

  // 获取图集分类
  const fetchGalleryCategories = async () => {
    try {
      const res = await api.get('/gallery-novel/gallery/categories', { signal })
      galleryCategories.value = [
        { id: null, name: '全部' },
        ...(res.data || [])
      ]
    } catch (e) {
      if (e.name !== 'AbortError' && e.name !== 'CanceledError') {
        console.error('获取图集分类失败', e)
      }
    }
  }

  // 获取图集列表
  const fetchGalleries = async () => {
    loading.value = true
    try {
      const params = { page: 1, page_size: 30 }
      if (selectedGalleryCategory.value) {
        params.category_id = selectedGalleryCategory.value
      }
      const res = await api.get('/gallery-novel/gallery/list', { params, signal })
      galleryItems.value = (res.data || []).map(g => ({
        id: g.id,
        title: g.title,
        cover: g.cover,
        views: g.view_count,
        count: g.image_count,
        status: g.status
      }))
    } catch (e) {
      if (e.name !== 'AbortError' && e.name !== 'CanceledError') {
        console.error('获取图集失败', e)
      }
    } finally {
      loading.value = false
    }
  }

  // 选择分类
  const selectGalleryCategory = (catId) => {
    selectedGalleryCategory.value = catId
    fetchGalleries()
  }

  return {
    galleryCategories,
    selectedGalleryCategory,
    galleryItems,
    loading,
    fetchGalleryCategories,
    fetchGalleries,
    selectGalleryCategory
  }
}
