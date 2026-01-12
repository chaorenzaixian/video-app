/**
 * 评论系统逻辑
 */
import { ref, computed } from 'vue'
import api from '@/utils/api'

export function useComments(videoId, options = {}) {
  const comments = ref([])
  const commentTotal = ref(0)
  const commentPage = ref(1)
  const commentPageSize = ref(20)
  const commentSortBy = ref('newest')
  const loadingComments = ref(false)
  const hasMoreComments = ref(false)
  const submittingComment = ref(false)
  
  // 回复相关
  const replyTarget = ref(null)
  const newComment = ref('')
  const commentImage = ref(null)
  const commentImagePreview = ref('')
  const showEmojiPicker = ref(false)
  
  // 表情列表
  const emojiList = [
    '😀', '😂', '🤣', '😍', '🥰', '😘', '😋', '🤤',
    '😎', '🤩', '😏', '😒', '😔', '😢', '😭', '😤',
    '🥵', '🥶', '😱', '🤮', '💀', '👻', '👍', '👎',
    '👏', '🙏', '💪', '🔥', '❤️', '💔', '💯', '🎉'
  ]
  
  const fetchComments = async (reset = true, abortSignal = null) => {
    if (!videoId.value) return
    
    if (reset) {
      commentPage.value = 1
      loadingComments.value = true
    }
    
    try {
      const res = await api.get(`/comments/video/${videoId.value}`, {
        params: {
          page: commentPage.value,
          page_size: commentPageSize.value,
          sort_by: commentSortBy.value
        },
        signal: abortSignal
      })
      const data = res.data || res
      
      if (reset) {
        comments.value = data.items || []
      } else {
        comments.value = [...comments.value, ...(data.items || [])]
      }
      
      commentTotal.value = data.total || 0
      hasMoreComments.value = (commentPage.value * commentPageSize.value) < commentTotal.value
    } catch (error) {
      if (error.name !== 'CanceledError' && error.name !== 'AbortError') {
        console.log('获取评论失败:', error)
      }
      if (reset) comments.value = []
    } finally {
      loadingComments.value = false
    }
  }
  
  const loadMoreComments = async () => {
    if (loadingComments.value || !hasMoreComments.value) return
    loadingComments.value = true
    commentPage.value++
    await fetchComments(false)
  }
  
  const changeCommentSort = async (sortBy) => {
    if (commentSortBy.value === sortBy) return
    commentSortBy.value = sortBy
    await fetchComments(true)
  }
  
  const submitComment = async (isVip) => {
    if ((!newComment.value.trim() && !commentImage.value) || submittingComment.value) return
    
    if (!isVip) {
      throw new Error('VIP_REQUIRED')
    }
    
    submittingComment.value = true
    
    try {
      let imageUrl = null
      
      // 先上传图片
      if (commentImage.value) {
        const formData = new FormData()
        formData.append('file', commentImage.value)
        const uploadRes = await api.post('/comments/upload-image', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        imageUrl = uploadRes.data?.url || uploadRes.url
      }
      
      const payload = {
        content: newComment.value.trim(),
        video_id: parseInt(videoId.value),
        parent_id: replyTarget.value?.parent_id || replyTarget.value?.id || null,
        image_url: imageUrl
      }
      
      const res = await api.post('/comments', payload)
      const newCommentData = res.data || res
      
      if (replyTarget.value) {
        const parentId = replyTarget.value.parent_id || replyTarget.value.id
        const parentComment = comments.value.find(c => c.id === parentId)
        if (parentComment) {
          if (!parentComment.replies) parentComment.replies = []
          parentComment.replies.push(newCommentData)
          parentComment.reply_count = (parentComment.reply_count || 0) + 1
        }
      } else {
        const firstNonPinnedIndex = comments.value.findIndex(c => !c.is_pinned)
        if (firstNonPinnedIndex === -1) {
          comments.value.push(newCommentData)
        } else {
          comments.value.splice(firstNonPinnedIndex, 0, newCommentData)
        }
        commentTotal.value++
      }
      
      // 清空输入
      clearCommentInput()
      return newCommentData
    } finally {
      submittingComment.value = false
    }
  }
  
  const likeComment = async (comment) => {
    const wasLiked = comment.is_liked
    const oldCount = comment.like_count || 0
    
    // 乐观更新
    comment.is_liked = !wasLiked
    comment.like_count = wasLiked ? Math.max(0, oldCount - 1) : oldCount + 1
    
    try {
      const res = await api.post(`/comments/${comment.id}/like`)
      const data = res.data || res
      comment.like_count = data.like_count
    } catch (error) {
      // 回滚
      comment.is_liked = wasLiked
      comment.like_count = oldCount
      throw error
    }
  }
  
  const deleteComment = async (comment) => {
    if (!confirm('确定要删除这条评论吗？')) return
    
    try {
      await api.delete(`/comments/${comment.id}`)
      
      // 从列表中移除
      const index = comments.value.findIndex(c => c.id === comment.id)
      if (index > -1) {
        comments.value.splice(index, 1)
        commentTotal.value--
      }
    } catch (error) {
      throw error
    }
  }
  
  const startReply = (parentComment, replyToComment = null) => {
    replyTarget.value = {
      parent_id: parentComment.id,
      id: parentComment.id,
      user_name: replyToComment ? replyToComment.user_name : parentComment.user_name
    }
  }
  
  const cancelReply = () => {
    replyTarget.value = null
    clearCommentInput()
  }
  
  const clearCommentInput = () => {
    newComment.value = ''
    commentImage.value = null
    commentImagePreview.value = ''
    showEmojiPicker.value = false
    replyTarget.value = null
  }
  
  const insertEmoji = (emoji) => {
    newComment.value += emoji
    showEmojiPicker.value = false
  }
  
  const handleImageSelect = (event) => {
    const file = event.target.files[0]
    if (!file) return
    
    if (file.size > 5 * 1024 * 1024) {
      throw new Error('IMAGE_TOO_LARGE')
    }
    
    if (!file.type.startsWith('image/')) {
      throw new Error('INVALID_IMAGE_TYPE')
    }
    
    commentImage.value = file
    commentImagePreview.value = URL.createObjectURL(file)
  }
  
  const removeCommentImage = () => {
    commentImage.value = null
    commentImagePreview.value = ''
  }
  
  return {
    // 状态
    comments,
    commentTotal,
    loadingComments,
    hasMoreComments,
    submittingComment,
    replyTarget,
    newComment,
    commentImage,
    commentImagePreview,
    showEmojiPicker,
    emojiList,
    commentSortBy,
    
    // 方法
    fetchComments,
    loadMoreComments,
    changeCommentSort,
    submitComment,
    likeComment,
    deleteComment,
    startReply,
    cancelReply,
    insertEmoji,
    handleImageSelect,
    removeCommentImage,
    clearCommentInput
  }
}
