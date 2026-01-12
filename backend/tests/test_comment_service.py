"""
评论服务测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestCommentService:
    """评论服务测试"""
    
    @pytest.mark.asyncio
    async def test_batch_get_user_vip_levels_empty(self):
        """测试空用户列表"""
        from app.services.comment_service import CommentService
        
        mock_db = AsyncMock()
        
        result = await CommentService.batch_get_user_vip_levels(mock_db, [])
        assert result == {}
    
    @pytest.mark.asyncio
    async def test_batch_get_liked_comment_ids_empty(self):
        """测试空评论列表"""
        from app.services.comment_service import CommentService
        
        mock_db = AsyncMock()
        
        result = await CommentService.batch_get_liked_comment_ids(mock_db, [], 1)
        assert result == set()
    
    @pytest.mark.asyncio
    async def test_batch_get_liked_comment_ids_no_user(self):
        """测试无用户ID"""
        from app.services.comment_service import CommentService
        
        mock_db = AsyncMock()
        
        result = await CommentService.batch_get_liked_comment_ids(mock_db, [1, 2, 3], None)
        assert result == set()
    
    def test_build_comment_response(self):
        """测试构建评论响应"""
        from app.services.comment_service import CommentService
        
        # Mock评论对象
        mock_comment = MagicMock()
        mock_comment.id = 1
        mock_comment.content = "测试评论"
        mock_comment.image_url = None
        mock_comment.video_id = 100
        mock_comment.user_id = 10
        mock_comment.parent_id = None
        mock_comment.like_count = 5
        mock_comment.reply_count = 2
        mock_comment.is_pinned = False
        mock_comment.is_official = False
        mock_comment.is_god = False
        mock_comment.created_at = datetime.now()
        
        # Mock用户对象
        mock_user = MagicMock()
        mock_user.nickname = "测试用户"
        mock_user.username = "testuser"
        mock_user.avatar = "/avatar.webp"
        
        result = CommentService.build_comment_response(
            comment=mock_comment,
            user=mock_user,
            vip_level=2,
            is_liked=True
        )
        
        assert result.id == 1
        assert result.content == "测试评论"
        assert result.user_name == "测试用户"
        assert result.user_vip_level == 2
        assert result.is_liked == True
    
    def test_build_comment_dict(self):
        """测试构建评论字典"""
        from app.services.comment_service import CommentService
        
        mock_comment = MagicMock()
        mock_comment.id = 1
        mock_comment.content = "测试评论"
        mock_comment.user_id = 10
        mock_comment.is_hidden = False
        mock_comment.is_pinned = False
        mock_comment.is_official = False
        mock_comment.is_god = False
        mock_comment.like_count = 5
        mock_comment.reply_count = 2
        mock_comment.parent_id = None
        mock_comment.created_at = datetime.now()
        
        mock_user = MagicMock()
        mock_user.nickname = "测试用户"
        mock_user.username = "testuser"
        mock_user.avatar = "/avatar.webp"
        
        result = CommentService.build_comment_dict(
            comment=mock_comment,
            user=mock_user,
            content_type="video",
            content_id=100
        )
        
        assert result["id"] == 1
        assert result["content"] == "测试评论"
        assert result["content_type"] == "video"
        assert result["content_id"] == 100
        assert result["user_name"] == "测试用户"
        assert result["is_hidden"] == False
    
    def test_build_comment_dict_with_status_field(self):
        """测试使用status字段的评论"""
        from app.services.comment_service import CommentService
        
        # 模拟PostComment类型（使用status而非is_hidden）
        mock_comment = MagicMock(spec=['id', 'content', 'user_id', 'status', 
                                       'like_count', 'reply_count', 'created_at'])
        mock_comment.id = 1
        mock_comment.content = "帖子评论"
        mock_comment.user_id = 10
        mock_comment.status = "hidden"
        mock_comment.like_count = 0
        mock_comment.reply_count = 0
        mock_comment.created_at = datetime.now()
        
        # 移除is_hidden属性
        del mock_comment.is_hidden
        
        mock_user = MagicMock()
        mock_user.nickname = "用户"
        mock_user.username = "user"
        mock_user.avatar = None
        
        result = CommentService.build_comment_dict(
            comment=mock_comment,
            user=mock_user,
            content_type="post",
            content_id=50
        )
        
        assert result["is_hidden"] == True  # status == "hidden"


class TestCommentServiceToggleLike:
    """评论点赞测试"""
    
    @pytest.mark.asyncio
    async def test_toggle_like_comment_not_found(self):
        """测试点赞不存在的评论"""
        from app.services.comment_service import CommentService
        
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(ValueError, match="评论不存在"):
            await CommentService.toggle_like(mock_db, 999, 1)
