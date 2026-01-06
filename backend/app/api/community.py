"""
社区功能API - 动态、话题、关注
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_user_optional
from app.models.user import User, UserVIP
from app.models.community import Post, PostComment, PostLike, PostCommentLike, Topic, TopicFollow
from app.models.creator import UserFollow

router = APIRouter(prefix="/community", tags=["社区"])


# ========== Schemas ==========

class PostCreate(BaseModel):
    content: str
    images: List[str] = []
    video_url: Optional[str] = None
    video_id: Optional[int] = None
    topic_ids: List[int] = []
    visibility: str = "public"
    location: Optional[str] = None

class PostUpdate(BaseModel):
    content: Optional[str] = None
    images: Optional[List[str]] = None
    topic_ids: Optional[List[int]] = None
    visibility: Optional[str] = None
    allow_comment: Optional[bool] = None

class CommentCreate(BaseModel):
    content: str
    images: List[str] = []
    parent_id: Optional[int] = None
    reply_to_user_id: Optional[int] = None

class UserBriefResponse(BaseModel):
    id: int
    username: str
    nickname: Optional[str]
    avatar: Optional[str]
    is_vip: bool = False
    vip_level: int = 0


class PostResponse(BaseModel):
    id: int
    user: UserBriefResponse
    content: str
    images: List[str]
    video_url: Optional[str]
    video_id: Optional[int]
    topic_ids: List[int]
    like_count: int
    comment_count: int
    share_count: int
    view_count: int
    is_top: bool
    is_hot: bool
    visibility: str
    allow_comment: bool
    location: Optional[str]
    created_at: datetime
    is_liked: bool = False
    is_followed: bool = False

class CommentResponse(BaseModel):
    id: int
    user: UserBriefResponse
    content: str
    images: List[str]
    parent_id: Optional[int]
    reply_to_user: Optional[UserBriefResponse]
    like_count: int
    reply_count: int
    created_at: datetime
    is_liked: bool = False

class TopicResponse(BaseModel):
    id: int
    name: str
    cover: Optional[str]
    description: Optional[str]
    post_count: int
    follow_count: int
    is_hot: bool
    is_followed: bool = False


# ========== 辅助函数 ==========

async def get_user_brief(db: AsyncSession, user: User) -> UserBriefResponse:
    """获取用户简要信息"""
    vip_result = await db.execute(
        select(UserVIP).where(UserVIP.user_id == user.id, UserVIP.is_active == True)
    )
    vip = vip_result.scalar_one_or_none()
    is_vip = vip is not None and vip.expire_date and vip.expire_date > datetime.utcnow()
    vip_level = vip.vip_level if (is_vip and vip) else 0
    
    return UserBriefResponse(
        id=user.id,
        username=user.username,
        nickname=user.nickname,
        avatar=user.avatar,
        is_vip=is_vip,
        vip_level=vip_level
    )

async def check_is_liked(db: AsyncSession, post_id: int, user_id: int) -> bool:
    result = await db.execute(
        select(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == user_id)
    )
    return result.scalar_one_or_none() is not None

async def check_is_followed(db: AsyncSession, follower_id: int, following_id: int) -> bool:
    result = await db.execute(
        select(UserFollow).where(
            UserFollow.follower_id == follower_id,
            UserFollow.following_id == following_id
        )
    )
    return result.scalar_one_or_none() is not None


# ========== 动态API ==========

@router.post("/posts", response_model=PostResponse)
async def create_post(
    post_in: PostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """发布动态"""
    if not post_in.content.strip() and not post_in.images and not post_in.video_url:
        raise HTTPException(status_code=400, detail="动态内容不能为空")
    
    if len(post_in.images) > 9:
        raise HTTPException(status_code=400, detail="最多上传9张图片")
    
    post = Post(
        user_id=current_user.id,
        content=post_in.content,
        images=post_in.images,
        video_url=post_in.video_url,
        video_id=post_in.video_id,
        topic_ids=post_in.topic_ids,
        visibility=post_in.visibility,
        location=post_in.location
    )
    db.add(post)
    
    # 更新话题帖子数
    if post_in.topic_ids:
        await db.execute(
            Topic.__table__.update()
            .where(Topic.id.in_(post_in.topic_ids))
            .values(post_count=Topic.post_count + 1)
        )
    
    await db.commit()
    await db.refresh(post)
    
    user_brief = await get_user_brief(db, current_user)
    
    return PostResponse(
        id=post.id,
        user=user_brief,
        content=post.content,
        images=post.images or [],
        video_url=post.video_url,
        video_id=post.video_id,
        topic_ids=post.topic_ids or [],
        like_count=0,
        comment_count=0,
        share_count=0,
        view_count=0,
        is_top=False,
        is_hot=False,
        visibility=post.visibility,
        allow_comment=post.allow_comment,
        location=post.location,
        created_at=post.created_at,
        is_liked=False,
        is_followed=False
    )


@router.get("/posts")
async def get_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    topic_id: Optional[int] = None,
    user_id: Optional[int] = None,
    feed_type: str = Query("recommend", description="recommend/following/hot/latest"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """获取动态列表"""
    import json as json_lib
    
    query = select(Post).where(Post.status == "published")
    
    # 按类型筛选
    if feed_type == "following" and current_user:
        # 获取关注的用户ID
        following_result = await db.execute(
            select(UserFollow.following_id).where(UserFollow.follower_id == current_user.id)
        )
        following_ids = [r[0] for r in following_result.fetchall()]
        if following_ids:
            query = query.where(Post.user_id.in_(following_ids))
        else:
            return []
    elif feed_type == "hot":
        query = query.where(Post.is_hot == True)
    
    # 按话题筛选
    if topic_id:
        query = query.where(Post.topic_ids.contains([topic_id]))
    
    # 按用户筛选
    if user_id:
        query = query.where(Post.user_id == user_id)
        # 非本人只能看公开动态
        if not current_user or current_user.id != user_id:
            query = query.where(Post.visibility == "public")
    
    # 排序
    if feed_type == "hot":
        query = query.order_by(desc(Post.like_count), desc(Post.created_at))
    else:
        query = query.order_by(desc(Post.is_top), desc(Post.created_at))
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    posts = result.scalars().all()
    
    # 收集所有topic_ids用于批量查询
    all_topic_ids = set()
    for post in posts:
        topic_ids_list = post.topic_ids or []
        if isinstance(topic_ids_list, str):
            try:
                topic_ids_list = json_lib.loads(topic_ids_list)
            except:
                topic_ids_list = []
        for tid in topic_ids_list:
            all_topic_ids.add(tid)
    
    # 批量获取话题信息
    topics_map = {}
    if all_topic_ids:
        topic_result = await db.execute(
            select(Topic).where(Topic.id.in_(list(all_topic_ids)))
        )
        for t in topic_result.scalars().all():
            topics_map[t.id] = {"id": t.id, "name": t.name}
    
    response = []
    for post in posts:
        # 获取用户信息
        user_result = await db.execute(select(User).where(User.id == post.user_id))
        post_user = user_result.scalar_one()
        user_brief = await get_user_brief(db, post_user)
        
        is_liked = False
        is_followed = False
        if current_user:
            is_liked = await check_is_liked(db, post.id, current_user.id)
            is_followed = await check_is_followed(db, current_user.id, post.user_id)
        
        # 获取帖子的话题
        topic_ids_list = post.topic_ids or []
        if isinstance(topic_ids_list, str):
            try:
                topic_ids_list = json_lib.loads(topic_ids_list)
            except:
                topic_ids_list = []
        topics = [topics_map[tid] for tid in topic_ids_list if tid in topics_map]
        
        response.append({
            "id": post.id,
            "user": user_brief,
            "content": post.content,
            "images": post.images or [],
            "video_url": post.video_url,
            "video_id": post.video_id,
            "topic_ids": topic_ids_list,
            "topics": topics,
            "like_count": post.like_count,
            "comment_count": post.comment_count,
            "share_count": post.share_count,
            "view_count": post.view_count,
            "is_top": post.is_top,
            "is_hot": post.is_hot,
            "visibility": post.visibility,
            "allow_comment": post.allow_comment,
            "location": post.location,
            "created_at": post.created_at,
            "is_liked": is_liked,
            "is_followed": is_followed
        })
    
    return response


@router.get("/posts/{post_id}")
async def get_post_detail(
    post_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """获取动态详情"""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post or post.status == "deleted":
        raise HTTPException(status_code=404, detail="动态不存在")
    
    # 权限检查
    if post.visibility == "private" and (not current_user or current_user.id != post.user_id):
        raise HTTPException(status_code=403, detail="无权查看")
    
    # 增加浏览量
    post.view_count += 1
    await db.commit()
    
    user_result = await db.execute(select(User).where(User.id == post.user_id))
    post_user = user_result.scalar_one()
    user_brief = await get_user_brief(db, post_user)
    
    is_liked = False
    is_followed = False
    if current_user:
        is_liked = await check_is_liked(db, post.id, current_user.id)
        is_followed = await check_is_followed(db, current_user.id, post.user_id)
    
    # 获取话题信息
    topics = []
    topic_ids_list = post.topic_ids or []
    # 处理可能是字符串的情况
    if isinstance(topic_ids_list, str):
        import json
        try:
            topic_ids_list = json.loads(topic_ids_list)
        except:
            topic_ids_list = []
    
    if topic_ids_list:
        topic_result = await db.execute(
            select(Topic).where(Topic.id.in_(topic_ids_list))
        )
        topics = [{"id": t.id, "name": t.name} for t in topic_result.scalars().all()]
    
    response_data = {
        "id": post.id,
        "user": user_brief,
        "content": post.content,
        "images": post.images or [],
        "video_url": post.video_url,
        "video_id": post.video_id,
        "topic_ids": post.topic_ids or [],
        "topics": topics,
        "like_count": post.like_count,
        "comment_count": post.comment_count,
        "share_count": post.share_count,
        "view_count": post.view_count,
        "is_top": post.is_top,
        "is_hot": post.is_hot,
        "visibility": post.visibility,
        "allow_comment": post.allow_comment,
        "location": post.location,
        "created_at": post.created_at,
        "is_liked": is_liked,
        "is_followed": is_followed
    }
    
    return response_data


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除动态"""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="动态不存在")
    
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除")
    
    post.status = "deleted"
    await db.commit()
    
    return {"message": "删除成功"}


@router.post("/posts/{post_id}/like")
async def like_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """点赞动态"""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post or post.status == "deleted":
        raise HTTPException(status_code=404, detail="动态不存在")
    
    # 检查是否已点赞
    like_result = await db.execute(
        select(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == current_user.id)
    )
    existing_like = like_result.scalar_one_or_none()
    
    if existing_like:
        # 取消点赞
        await db.delete(existing_like)
        post.like_count = max(0, post.like_count - 1)
        await db.commit()
        return {"liked": False, "like_count": post.like_count}
    else:
        # 点赞
        like = PostLike(post_id=post_id, user_id=current_user.id)
        db.add(like)
        post.like_count += 1
        await db.commit()
        return {"liked": True, "like_count": post.like_count}


# ========== 评论API ==========

@router.post("/posts/{post_id}/comments", response_model=CommentResponse)
async def create_comment(
    post_id: int,
    comment_in: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """发表评论"""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post or post.status == "deleted":
        raise HTTPException(status_code=404, detail="动态不存在")
    
    if not post.allow_comment:
        raise HTTPException(status_code=403, detail="该动态禁止评论")
    
    comment = PostComment(
        post_id=post_id,
        user_id=current_user.id,
        content=comment_in.content,
        images=comment_in.images,
        parent_id=comment_in.parent_id,
        reply_to_user_id=comment_in.reply_to_user_id
    )
    db.add(comment)
    
    # 更新评论数
    post.comment_count += 1
    
    # 如果是回复，更新父评论的回复数
    if comment_in.parent_id:
        parent_result = await db.execute(
            select(PostComment).where(PostComment.id == comment_in.parent_id)
        )
        parent = parent_result.scalar_one_or_none()
        if parent:
            parent.reply_count += 1
    
    await db.commit()
    await db.refresh(comment)
    
    user_brief = await get_user_brief(db, current_user)
    
    reply_to_user = None
    if comment.reply_to_user_id:
        reply_user_result = await db.execute(
            select(User).where(User.id == comment.reply_to_user_id)
        )
        reply_user = reply_user_result.scalar_one_or_none()
        if reply_user:
            reply_to_user = await get_user_brief(db, reply_user)
    
    return CommentResponse(
        id=comment.id,
        user=user_brief,
        content=comment.content,
        images=comment.images or [],
        parent_id=comment.parent_id,
        reply_to_user=reply_to_user,
        like_count=0,
        reply_count=0,
        created_at=comment.created_at,
        is_liked=False
    )


@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
async def get_comments(
    post_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    parent_id: Optional[int] = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """获取评论列表"""
    query = select(PostComment).where(
        PostComment.post_id == post_id,
        PostComment.status == "visible"
    )
    
    if parent_id:
        query = query.where(PostComment.parent_id == parent_id)
    else:
        query = query.where(PostComment.parent_id == None)
    
    query = query.order_by(desc(PostComment.is_top), desc(PostComment.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    comments = result.scalars().all()
    
    response = []
    for comment in comments:
        user_result = await db.execute(select(User).where(User.id == comment.user_id))
        comment_user = user_result.scalar_one()
        user_brief = await get_user_brief(db, comment_user)
        
        reply_to_user = None
        if comment.reply_to_user_id:
            reply_user_result = await db.execute(
                select(User).where(User.id == comment.reply_to_user_id)
            )
            reply_user = reply_user_result.scalar_one_or_none()
            if reply_user:
                reply_to_user = await get_user_brief(db, reply_user)
        
        is_liked = False
        if current_user:
            like_result = await db.execute(
                select(PostCommentLike).where(
                    PostCommentLike.comment_id == comment.id,
                    PostCommentLike.user_id == current_user.id
                )
            )
            is_liked = like_result.scalar_one_or_none() is not None
        
        response.append(CommentResponse(
            id=comment.id,
            user=user_brief,
            content=comment.content,
            images=comment.images or [],
            parent_id=comment.parent_id,
            reply_to_user=reply_to_user,
            like_count=comment.like_count,
            reply_count=comment.reply_count,
            created_at=comment.created_at,
            is_liked=is_liked
        ))
    
    return response


@router.post("/comments/{comment_id}/like")
async def like_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """点赞评论"""
    result = await db.execute(select(PostComment).where(PostComment.id == comment_id))
    comment = result.scalar_one_or_none()
    
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    like_result = await db.execute(
        select(PostCommentLike).where(
            PostCommentLike.comment_id == comment_id,
            PostCommentLike.user_id == current_user.id
        )
    )
    existing_like = like_result.scalar_one_or_none()
    
    if existing_like:
        await db.delete(existing_like)
        comment.like_count = max(0, comment.like_count - 1)
        await db.commit()
        return {"liked": False, "like_count": comment.like_count}
    else:
        like = PostCommentLike(comment_id=comment_id, user_id=current_user.id)
        db.add(like)
        comment.like_count += 1
        await db.commit()
        return {"liked": True, "like_count": comment.like_count}


# ========== 关注API ==========

@router.post("/users/{user_id}/follow")
async def follow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """关注/取消关注用户"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能关注自己")
    
    # 检查用户是否存在
    target_result = await db.execute(select(User).where(User.id == user_id))
    target_user = target_result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查是否已关注
    follow_result = await db.execute(
        select(UserFollow).where(
            UserFollow.follower_id == current_user.id,
            UserFollow.following_id == user_id
        )
    )
    existing_follow = follow_result.scalar_one_or_none()
    
    if existing_follow:
        await db.delete(existing_follow)
        await db.commit()
        return {"followed": False}
    else:
        follow = UserFollow(follower_id=current_user.id, following_id=user_id)
        db.add(follow)
        await db.commit()
        return {"followed": True}


@router.get("/users/{user_id}/followers")
async def get_followers(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """获取粉丝列表"""
    query = select(UserFollow).where(UserFollow.following_id == user_id)
    query = query.order_by(desc(UserFollow.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    follows = result.scalars().all()
    
    response = []
    for follow in follows:
        user_result = await db.execute(select(User).where(User.id == follow.follower_id))
        follower = user_result.scalar_one()
        user_brief = await get_user_brief(db, follower)
        
        is_followed = False
        if current_user:
            is_followed = await check_is_followed(db, current_user.id, follower.id)
        
        response.append({
            "user": user_brief,
            "is_followed": is_followed,
            "followed_at": follow.created_at
        })
    
    return response


@router.get("/users/{user_id}/following")
async def get_following(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """获取关注列表"""
    query = select(UserFollow).where(UserFollow.follower_id == user_id)
    query = query.order_by(desc(UserFollow.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    follows = result.scalars().all()
    
    response = []
    for follow in follows:
        user_result = await db.execute(select(User).where(User.id == follow.following_id))
        following = user_result.scalar_one()
        user_brief = await get_user_brief(db, following)
        
        is_followed = False
        if current_user:
            is_followed = await check_is_followed(db, current_user.id, following.id)
        
        response.append({
            "user": user_brief,
            "is_followed": is_followed,
            "followed_at": follow.created_at
        })
    
    return response


# ========== 话题API ==========

@router.get("/topics/recommended")
async def get_recommended_topics(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """获取推荐话题列表（用于热门推荐二级分类）"""
    result = await db.execute(
        select(Topic).where(
            Topic.is_active == True,
            Topic.is_recommended == True
        ).order_by(desc(Topic.sort_order), desc(Topic.post_count), Topic.id)
    )
    topics = result.scalars().all()
    
    response = []
    for topic in topics:
        is_followed = False
        if current_user:
            follow_result = await db.execute(
                select(TopicFollow).where(
                    TopicFollow.topic_id == topic.id,
                    TopicFollow.user_id == current_user.id
                )
            )
            is_followed = follow_result.scalar_one_or_none() is not None
        
        response.append({
            "id": topic.id,
            "name": topic.name,
            "cover": topic.cover,
            "description": topic.description,
            "post_count": topic.post_count,
            "follow_count": topic.follow_count,
            "is_hot": topic.is_hot,
            "is_followed": is_followed
        })
    
    return response


@router.get("/topics/categories")
async def get_topic_categories(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """获取顶级分类列表（带子话题）"""
    # 获取顶级分类
    result = await db.execute(
        select(Topic).where(
            Topic.is_active == True,
            Topic.level == 1
        ).order_by(desc(Topic.sort_order), Topic.id)
    )
    categories = result.scalars().all()
    
    response = []
    for cat in categories:
        # 获取子话题
        children_result = await db.execute(
            select(Topic).where(
                Topic.is_active == True,
                Topic.parent_id == cat.id
            ).order_by(desc(Topic.sort_order), Topic.id)
        )
        children = children_result.scalars().all()
        
        response.append({
            "id": cat.id,
            "name": cat.name,
            "icon": cat.icon,
            "cover": cat.cover,
            "description": cat.description,
            "post_count": cat.post_count,
            "children": [
                {
                    "id": c.id,
                    "name": c.name,
                    "cover": c.cover,
                    "post_count": c.post_count,
                    "follow_count": c.follow_count,
                    "is_hot": c.is_hot
                }
                for c in children
            ]
        })
    
    return response


@router.get("/topics", response_model=List[TopicResponse])
async def get_topics(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    parent_id: Optional[int] = Query(None, description="父级分类ID"),
    level: Optional[int] = Query(None, description="层级：1=顶级，2=二级"),
    search: Optional[str] = None,
    is_hot: Optional[bool] = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """获取话题列表"""
    query = select(Topic).where(Topic.is_active == True)
    
    if parent_id is not None:
        query = query.where(Topic.parent_id == parent_id)
    
    if level is not None:
        query = query.where(Topic.level == level)
    
    if search:
        query = query.where(Topic.name.contains(search))
    
    if is_hot:
        query = query.where(Topic.is_hot == True)
    
    query = query.order_by(desc(Topic.is_recommended), desc(Topic.is_hot), desc(Topic.sort_order), desc(Topic.post_count))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    topics = result.scalars().all()
    
    response = []
    for topic in topics:
        is_followed = False
        if current_user:
            follow_result = await db.execute(
                select(TopicFollow).where(
                    TopicFollow.topic_id == topic.id,
                    TopicFollow.user_id == current_user.id
                )
            )
            is_followed = follow_result.scalar_one_or_none() is not None
        
        response.append(TopicResponse(
            id=topic.id,
            name=topic.name,
            cover=topic.cover,
            description=topic.description,
            post_count=topic.post_count,
            follow_count=topic.follow_count,
            is_hot=topic.is_hot,
            is_followed=is_followed
        ))
    
    return response


@router.post("/topics/{topic_id}/follow")
async def follow_topic(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """关注/取消关注话题"""
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()
    
    if not topic:
        raise HTTPException(status_code=404, detail="话题不存在")
    
    follow_result = await db.execute(
        select(TopicFollow).where(
            TopicFollow.topic_id == topic_id,
            TopicFollow.user_id == current_user.id
        )
    )
    existing_follow = follow_result.scalar_one_or_none()
    
    if existing_follow:
        await db.delete(existing_follow)
        topic.follow_count = max(0, topic.follow_count - 1)
        await db.commit()
        return {"followed": False, "follow_count": topic.follow_count}
    else:
        follow = TopicFollow(topic_id=topic_id, user_id=current_user.id)
        db.add(follow)
        topic.follow_count += 1
        await db.commit()
        return {"followed": True, "follow_count": topic.follow_count}


# ========== 图片上传 ==========

@router.post("/upload/image")
async def upload_community_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传社区图片（优先使用R2，否则本地存储）"""
    from app.services.image_service import ImageService
    from app.services.r2_service import r2_service
    
    if file.content_type not in ImageService.SUPPORTED_FORMATS:
        raise HTTPException(status_code=400, detail="不支持的图片格式")
    
    content = await file.read()
    valid, error = ImageService.validate_image(content, file.content_type)
    if not valid:
        raise HTTPException(status_code=400, detail=error)
    
    try:
        # 优先使用R2云存储
        if r2_service.is_configured:
            result = await r2_service.upload_file(
                content=content,
                filename=file.filename,
                subdir="community/images",
                content_type=file.content_type
            )
            return {"url": result["url"], "storage": "r2"}
        
        # 回退到本地存储
        result = await ImageService.save_image(
            content=content,
            subdir="community",
            convert_webp=True
        )
        return {"url": result["url"], "storage": "local"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/upload/video")
async def upload_community_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传社区视频（优先使用R2，否则本地存储）"""
    import os
    import uuid
    from datetime import datetime
    from app.services.r2_service import r2_service
    
    # 检查文件类型
    allowed_types = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="不支持的视频格式，请上传MP4、MOV、AVI或WebM格式")
    
    # 检查文件大小 (300MB)
    content = await file.read()
    if len(content) > 300 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="视频大小不能超过300MB")
    
    try:
        # 优先使用R2云存储
        if r2_service.is_configured:
            result = await r2_service.upload_file(
                content=content,
                filename=file.filename,
                subdir="community/videos",
                content_type=file.content_type
            )
            return {"url": result["url"], "storage": "r2"}
        
        # 回退到本地存储
        ext = os.path.splitext(file.filename)[1] or '.mp4'
        filename = f"{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}{ext}"
        
        upload_dir = os.path.join("uploads", "community", "videos")
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(content)
        
        url = f"/uploads/community/videos/{filename}"
        return {"url": url, "storage": "local"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")
