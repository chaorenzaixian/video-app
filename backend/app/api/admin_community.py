"""
社区后台管理API - 帖子、话题、评论管理
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, case
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_admin
from app.models.user import User
from app.models.community import Post, PostComment, Topic, PostLike, TopicFollow

router = APIRouter(prefix="/admin/community", tags=["社区管理"])


# ========== Schemas ==========

class TopicCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None  # 父级ID，为空表示顶级分类
    icon: Optional[str] = None  # 顶级分类图标
    cover: Optional[str] = None
    description: Optional[str] = None
    is_hot: bool = False
    is_recommended: bool = False
    sort_order: int = 0

class TopicUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    cover: Optional[str] = None
    description: Optional[str] = None
    is_hot: Optional[bool] = None
    is_recommended: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class PostAuditRequest(BaseModel):
    status: str  # published/hidden/deleted
    reason: Optional[str] = None

class PostFeatureRequest(BaseModel):
    is_top: Optional[bool] = None
    is_hot: Optional[bool] = None
    is_recommended: Optional[bool] = None

class PostCreateRequest(BaseModel):
    content: str
    images: List[str] = []
    video_url: Optional[str] = None
    topic_ids: List[int] = []
    is_top: bool = False
    is_hot: bool = False
    is_recommended: bool = False
    status: str = "published"


class BatchAuditRequest(BaseModel):
    post_ids: List[int]
    status: str


# ========== 统计API ==========

@router.get("/stats")
async def get_community_stats(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取社区统计数据"""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)
    
    # 帖子统计
    total_posts = await db.scalar(select(func.count(Post.id)))
    today_posts = await db.scalar(
        select(func.count(Post.id)).where(Post.created_at >= today)
    )
    pending_posts = await db.scalar(
        select(func.count(Post.id)).where(Post.status == "pending")
    )
    
    # 评论统计
    total_comments = await db.scalar(select(func.count(PostComment.id)))
    today_comments = await db.scalar(
        select(func.count(PostComment.id)).where(PostComment.created_at >= today)
    )
    
    # 话题统计
    total_topics = await db.scalar(select(func.count(Topic.id)))
    active_topics = await db.scalar(
        select(func.count(Topic.id)).where(Topic.is_active == True)
    )
    
    # 7天趋势
    trends = []
    for i in range(7):
        day = today - timedelta(days=6-i)
        next_day = day + timedelta(days=1)
        
        day_posts = await db.scalar(
            select(func.count(Post.id)).where(
                and_(Post.created_at >= day, Post.created_at < next_day)
            )
        )
        day_comments = await db.scalar(
            select(func.count(PostComment.id)).where(
                and_(PostComment.created_at >= day, PostComment.created_at < next_day)
            )
        )
        
        trends.append({
            "date": day.strftime("%m-%d"),
            "posts": day_posts or 0,
            "comments": day_comments or 0
        })
    
    return {
        "posts": {
            "total": total_posts or 0,
            "today": today_posts or 0,
            "pending": pending_posts or 0
        },
        "comments": {
            "total": total_comments or 0,
            "today": today_comments or 0
        },
        "topics": {
            "total": total_topics or 0,
            "active": active_topics or 0
        },
        "trends": trends
    }


# ========== 帖子管理API ==========

@router.get("/posts")
async def get_admin_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    user_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    is_top: Optional[bool] = None,
    is_hot: Optional[bool] = None,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取帖子列表（管理员）"""
    query = select(Post)
    count_query = select(func.count(Post.id))
    
    # 筛选条件
    if status:
        query = query.where(Post.status == status)
        count_query = count_query.where(Post.status == status)
    
    if keyword:
        query = query.where(Post.content.contains(keyword))
        count_query = count_query.where(Post.content.contains(keyword))
    
    if user_id:
        query = query.where(Post.user_id == user_id)
        count_query = count_query.where(Post.user_id == user_id)
    
    if is_top is not None:
        query = query.where(Post.is_top == is_top)
        count_query = count_query.where(Post.is_top == is_top)
    
    if is_hot is not None:
        query = query.where(Post.is_hot == is_hot)
        count_query = count_query.where(Post.is_hot == is_hot)
    
    total = await db.scalar(count_query)
    
    query = query.order_by(desc(Post.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    posts = result.scalars().all()
    
    items = []
    for post in posts:
        # 获取用户信息
        user_result = await db.execute(select(User).where(User.id == post.user_id))
        user = user_result.scalar_one_or_none()
        
        items.append({
            "id": post.id,
            "user": {
                "id": user.id if user else 0,
                "username": user.username if user else "已删除",
                "nickname": user.nickname if user else None,
                "avatar": user.avatar if user else None
            } if user else None,
            "content": post.content[:100] + "..." if len(post.content) > 100 else post.content,
            "full_content": post.content,
            "images": post.images or [],
            "video_url": post.video_url,
            "topic_ids": post.topic_ids or [],
            "like_count": post.like_count,
            "comment_count": post.comment_count,
            "view_count": post.view_count,
            "is_top": post.is_top,
            "is_hot": post.is_hot,
            "is_recommended": post.is_recommended,
            "status": post.status,
            "visibility": post.visibility,
            "created_at": post.created_at.isoformat() if post.created_at else None
        })
    
    return {
        "items": items,
        "total": total or 0,
        "page": page,
        "page_size": page_size
    }


@router.put("/posts/{post_id}/audit")
async def audit_post(
    post_id: int,
    req: PostAuditRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """审核帖子"""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    if req.status not in ["published", "hidden", "deleted", "pending"]:
        raise HTTPException(status_code=400, detail="无效的状态")
    
    post.status = req.status
    await db.commit()
    
    return {"message": "操作成功", "status": req.status}


@router.put("/posts/{post_id}/feature")
async def feature_post(
    post_id: int,
    req: PostFeatureRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """设置帖子特性（置顶/热门/推荐）"""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    if req.is_top is not None:
        post.is_top = req.is_top
    if req.is_hot is not None:
        post.is_hot = req.is_hot
    if req.is_recommended is not None:
        post.is_recommended = req.is_recommended
    
    await db.commit()
    
    return {
        "message": "操作成功",
        "is_top": post.is_top,
        "is_hot": post.is_hot,
        "is_recommended": post.is_recommended
    }


@router.delete("/posts/{post_id}")
async def delete_post_admin(
    post_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除帖子（管理员）- 真实删除"""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 先删除关联数据
    await db.execute(
        PostComment.__table__.delete().where(PostComment.post_id == post_id)
    )
    await db.execute(
        PostLike.__table__.delete().where(PostLike.post_id == post_id)
    )
    
    await db.delete(post)
    await db.commit()
    
    return {"message": "删除成功"}


@router.post("/posts")
async def create_post_admin(
    req: PostCreateRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """管理员发布帖子"""
    post = Post(
        user_id=admin.id,
        content=req.content,
        images=req.images,
        video_url=req.video_url,
        topic_ids=req.topic_ids,
        is_top=req.is_top,
        is_hot=req.is_hot,
        is_recommended=req.is_recommended,
        status=req.status
    )
    db.add(post)
    
    # 更新话题帖子数
    if req.topic_ids:
        for topic_id in req.topic_ids:
            topic_result = await db.execute(select(Topic).where(Topic.id == topic_id))
            topic = topic_result.scalar_one_or_none()
            if topic:
                topic.post_count = (topic.post_count or 0) + 1
    
    await db.commit()
    await db.refresh(post)
    
    return {"id": post.id, "message": "发布成功"}


@router.post("/posts/batch-audit")
async def batch_audit_posts(
    req: BatchAuditRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """批量审核帖子"""
    if req.status not in ["published", "hidden", "deleted"]:
        raise HTTPException(status_code=400, detail="无效的状态")
    
    result = await db.execute(select(Post).where(Post.id.in_(req.post_ids)))
    posts = result.scalars().all()
    
    if req.status == "deleted":
        # 真实删除 - 先删除关联数据
        for post in posts:
            # 删除帖子的评论
            await db.execute(
                PostComment.__table__.delete().where(PostComment.post_id == post.id)
            )
            # 删除帖子的点赞
            await db.execute(
                PostLike.__table__.delete().where(PostLike.post_id == post.id)
            )
            # 删除帖子
            await db.delete(post)
    else:
        for post in posts:
            post.status = req.status
    
    await db.commit()
    
    return {"message": f"已处理 {len(posts)} 条帖子"}



# ========== 评论管理API ==========

@router.get("/comments")
async def get_admin_comments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    post_id: Optional[int] = None,
    user_id: Optional[int] = None,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取评论列表（管理员）"""
    query = select(PostComment)
    count_query = select(func.count(PostComment.id))
    
    if status:
        query = query.where(PostComment.status == status)
        count_query = count_query.where(PostComment.status == status)
    
    if keyword:
        query = query.where(PostComment.content.contains(keyword))
        count_query = count_query.where(PostComment.content.contains(keyword))
    
    if post_id:
        query = query.where(PostComment.post_id == post_id)
        count_query = count_query.where(PostComment.post_id == post_id)
    
    if user_id:
        query = query.where(PostComment.user_id == user_id)
        count_query = count_query.where(PostComment.user_id == user_id)
    
    total = await db.scalar(count_query)
    
    query = query.order_by(desc(PostComment.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    comments = result.scalars().all()
    
    items = []
    for comment in comments:
        # 获取用户信息
        user_result = await db.execute(select(User).where(User.id == comment.user_id))
        user = user_result.scalar_one_or_none()
        
        # 获取帖子信息
        post_result = await db.execute(select(Post).where(Post.id == comment.post_id))
        post = post_result.scalar_one_or_none()
        
        items.append({
            "id": comment.id,
            "user": {
                "id": user.id if user else 0,
                "username": user.username if user else "已删除",
                "nickname": user.nickname if user else None,
                "avatar": user.avatar if user else None
            } if user else None,
            "post": {
                "id": post.id if post else 0,
                "content": (post.content[:50] + "...") if post and len(post.content) > 50 else (post.content if post else "已删除")
            } if post else None,
            "content": comment.content,
            "images": comment.images or [],
            "like_count": comment.like_count,
            "reply_count": comment.reply_count,
            "status": comment.status,
            "is_top": comment.is_top,
            "parent_id": comment.parent_id,
            "created_at": comment.created_at.isoformat() if comment.created_at else None
        })
    
    return {
        "items": items,
        "total": total or 0,
        "page": page,
        "page_size": page_size
    }


@router.put("/comments/{comment_id}/status")
async def update_comment_status(
    comment_id: int,
    status: str,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新评论状态"""
    if status not in ["visible", "hidden", "deleted"]:
        raise HTTPException(status_code=400, detail="无效的状态")
    
    result = await db.execute(select(PostComment).where(PostComment.id == comment_id))
    comment = result.scalar_one_or_none()
    
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    old_status = comment.status
    comment.status = status
    
    # 如果删除评论，更新帖子评论数
    if status == "deleted" and old_status != "deleted":
        post_result = await db.execute(select(Post).where(Post.id == comment.post_id))
        post = post_result.scalar_one_or_none()
        if post:
            post.comment_count = max(0, post.comment_count - 1)
    
    await db.commit()
    
    return {"message": "操作成功", "status": status}


@router.delete("/comments/{comment_id}")
async def delete_comment_admin(
    comment_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除评论（管理员）"""
    result = await db.execute(select(PostComment).where(PostComment.id == comment_id))
    comment = result.scalar_one_or_none()
    
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    # 更新帖子评论数
    if comment.status != "deleted":
        post_result = await db.execute(select(Post).where(Post.id == comment.post_id))
        post = post_result.scalar_one_or_none()
        if post:
            post.comment_count = max(0, post.comment_count - 1)
    
    comment.status = "deleted"
    await db.commit()
    
    return {"message": "删除成功"}


@router.post("/comments/batch-delete")
async def batch_delete_comments(
    comment_ids: List[int],
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """批量删除评论"""
    result = await db.execute(select(PostComment).where(PostComment.id.in_(comment_ids)))
    comments = result.scalars().all()
    
    # 统计需要更新的帖子
    post_updates = {}
    for comment in comments:
        if comment.status != "deleted":
            post_updates[comment.post_id] = post_updates.get(comment.post_id, 0) + 1
        comment.status = "deleted"
    
    # 更新帖子评论数
    for post_id, count in post_updates.items():
        post_result = await db.execute(select(Post).where(Post.id == post_id))
        post = post_result.scalar_one_or_none()
        if post:
            post.comment_count = max(0, post.comment_count - count)
    
    await db.commit()
    
    return {"message": f"已删除 {len(comments)} 条评论"}


# ========== 话题管理API ==========

@router.get("/topics/tree")
async def get_topics_tree(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取话题树形结构"""
    # 获取所有话题
    result = await db.execute(
        select(Topic).where(Topic.is_active == True).order_by(desc(Topic.sort_order), Topic.id)
    )
    all_topics = result.scalars().all()
    
    # 构建树形结构
    topic_map = {}
    root_topics = []
    
    for topic in all_topics:
        topic_data = {
            "id": topic.id,
            "name": topic.name,
            "parent_id": topic.parent_id,
            "level": topic.level,
            "icon": topic.icon,
            "cover": topic.cover,
            "description": topic.description,
            "post_count": topic.post_count,
            "follow_count": topic.follow_count,
            "children_count": topic.children_count,
            "is_hot": topic.is_hot,
            "is_recommended": topic.is_recommended,
            "is_active": topic.is_active,
            "sort_order": topic.sort_order,
            "children": []
        }
        topic_map[topic.id] = topic_data
    
    # 组装树
    for topic in all_topics:
        topic_data = topic_map[topic.id]
        if topic.parent_id and topic.parent_id in topic_map:
            topic_map[topic.parent_id]["children"].append(topic_data)
        else:
            root_topics.append(topic_data)
    
    return root_topics


@router.get("/topics/categories")
async def get_topic_categories(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取顶级分类列表（用于下拉选择）"""
    result = await db.execute(
        select(Topic).where(
            Topic.is_active == True,
            Topic.level == 1
        ).order_by(desc(Topic.sort_order), Topic.id)
    )
    categories = result.scalars().all()
    
    return [
        {"id": c.id, "name": c.name, "icon": c.icon}
        for c in categories
    ]


@router.get("/topics")
async def get_admin_topics(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    parent_id: Optional[int] = Query(None, description="父级ID，0表示顶级分类"),
    level: Optional[int] = Query(None, description="层级：1=顶级，2=二级"),
    keyword: Optional[str] = None,
    is_active: Optional[bool] = Query(True, description="是否只显示活跃的，默认True"),
    is_hot: Optional[bool] = None,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取话题列表（管理员）"""
    query = select(Topic)
    count_query = select(func.count(Topic.id))
    
    # 默认只显示活跃的
    if is_active is not None:
        query = query.where(Topic.is_active == is_active)
        count_query = count_query.where(Topic.is_active == is_active)
    
    # 按父级筛选
    if parent_id is not None:
        if parent_id == 0:
            query = query.where(Topic.parent_id == None)
            count_query = count_query.where(Topic.parent_id == None)
        else:
            query = query.where(Topic.parent_id == parent_id)
            count_query = count_query.where(Topic.parent_id == parent_id)
    
    # 按层级筛选
    if level is not None:
        query = query.where(Topic.level == level)
        count_query = count_query.where(Topic.level == level)
    
    if keyword:
        query = query.where(Topic.name.contains(keyword))
        count_query = count_query.where(Topic.name.contains(keyword))
    
    if is_hot is not None:
        query = query.where(Topic.is_hot == is_hot)
        count_query = count_query.where(Topic.is_hot == is_hot)
    
    total = await db.scalar(count_query)
    
    query = query.order_by(desc(Topic.sort_order), desc(Topic.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    topics = result.scalars().all()
    
    items = []
    for topic in topics:
        # 获取父级名称
        parent_name = None
        if topic.parent_id:
            parent_result = await db.execute(select(Topic).where(Topic.id == topic.parent_id))
            parent = parent_result.scalar_one_or_none()
            if parent:
                parent_name = parent.name
        
        items.append({
            "id": topic.id,
            "name": topic.name,
            "parent_id": topic.parent_id,
            "parent_name": parent_name,
            "level": topic.level,
            "icon": topic.icon,
            "cover": topic.cover,
            "description": topic.description,
            "post_count": topic.post_count,
            "follow_count": topic.follow_count,
            "view_count": topic.view_count,
            "children_count": topic.children_count,
            "is_hot": topic.is_hot,
            "is_recommended": topic.is_recommended,
            "is_active": topic.is_active,
            "sort_order": topic.sort_order,
            "created_at": topic.created_at.isoformat() if topic.created_at else None
        })
    
    return {
        "items": items,
        "total": total or 0,
        "page": page,
        "page_size": page_size
    }


@router.post("/topics")
async def create_topic(
    topic_in: TopicCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """创建话题"""
    # 检查名称是否重复（同一父级下的活跃话题）
    existing_query = select(Topic).where(
        Topic.name == topic_in.name,
        Topic.is_active == True  # 只检查活跃的
    )
    if topic_in.parent_id:
        existing_query = existing_query.where(Topic.parent_id == topic_in.parent_id)
    else:
        existing_query = existing_query.where(Topic.parent_id == None)
    
    existing = await db.execute(existing_query)
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="同级下话题名称已存在")
    
    # 确定层级
    level = 1
    parent = None
    if topic_in.parent_id:
        parent_result = await db.execute(select(Topic).where(Topic.id == topic_in.parent_id))
        parent = parent_result.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=400, detail="父级分类不存在")
        if parent.level >= 2:
            raise HTTPException(status_code=400, detail="最多支持两级分类")
        level = parent.level + 1
    
    topic = Topic(
        name=topic_in.name,
        parent_id=topic_in.parent_id,
        level=level,
        icon=topic_in.icon,
        cover=topic_in.cover,
        description=topic_in.description,
        is_hot=topic_in.is_hot,
        is_recommended=topic_in.is_recommended,
        sort_order=topic_in.sort_order
    )
    db.add(topic)
    
    # 更新父级的子话题数量
    if topic_in.parent_id:
        parent.children_count = (parent.children_count or 0) + 1
    
    await db.commit()
    await db.refresh(topic)
    
    return {
        "id": topic.id,
        "name": topic.name,
        "level": topic.level,
        "message": "创建成功"
    }


@router.put("/topics/{topic_id}")
async def update_topic(
    topic_id: int,
    topic_in: TopicUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新话题"""
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()
    
    if not topic:
        raise HTTPException(status_code=404, detail="话题不存在")
    
    # 检查名称是否重复（只检查活跃的）
    if topic_in.name and topic_in.name != topic.name:
        existing_query = select(Topic).where(
            Topic.name == topic_in.name,
            Topic.is_active == True
        )
        if topic.parent_id:
            existing_query = existing_query.where(Topic.parent_id == topic.parent_id)
        else:
            existing_query = existing_query.where(Topic.parent_id == None)
        existing = await db.execute(existing_query)
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="同级下话题名称已存在")
    
    if topic_in.name is not None:
        topic.name = topic_in.name
    if topic_in.icon is not None:
        topic.icon = topic_in.icon
    if topic_in.cover is not None:
        topic.cover = topic_in.cover
    if topic_in.description is not None:
        topic.description = topic_in.description
    if topic_in.is_hot is not None:
        topic.is_hot = topic_in.is_hot
    if topic_in.is_recommended is not None:
        topic.is_recommended = topic_in.is_recommended
    if topic_in.is_active is not None:
        topic.is_active = topic_in.is_active
    if topic_in.sort_order is not None:
        topic.sort_order = topic_in.sort_order
    
    await db.commit()
    
    return {"message": "更新成功"}


@router.put("/topics/{topic_id}/move")
async def move_topic(
    topic_id: int,
    new_parent_id: Optional[int] = None,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """移动话题到其他分类"""
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()
    
    if not topic:
        raise HTTPException(status_code=404, detail="话题不存在")
    
    old_parent_id = topic.parent_id
    
    # 验证新父级
    if new_parent_id:
        if new_parent_id == topic_id:
            raise HTTPException(status_code=400, detail="不能移动到自身")
        
        new_parent_result = await db.execute(select(Topic).where(Topic.id == new_parent_id))
        new_parent = new_parent_result.scalar_one_or_none()
        if not new_parent:
            raise HTTPException(status_code=400, detail="目标分类不存在")
        if new_parent.level >= 2:
            raise HTTPException(status_code=400, detail="目标分类层级过深")
        
        topic.parent_id = new_parent_id
        topic.level = new_parent.level + 1
        new_parent.children_count = (new_parent.children_count or 0) + 1
    else:
        topic.parent_id = None
        topic.level = 1
    
    # 更新旧父级的子话题数量
    if old_parent_id:
        old_parent_result = await db.execute(select(Topic).where(Topic.id == old_parent_id))
        old_parent = old_parent_result.scalar_one_or_none()
        if old_parent:
            old_parent.children_count = max(0, (old_parent.children_count or 0) - 1)
    
    await db.commit()
    
    return {"message": "移动成功"}


@router.delete("/topics/{topic_id}")
async def delete_topic(
    topic_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除话题"""
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()
    
    if not topic:
        raise HTTPException(status_code=404, detail="话题不存在")
    
    # 检查是否有子话题
    children_result = await db.execute(
        select(func.count(Topic.id)).where(Topic.parent_id == topic_id, Topic.is_active == True)
    )
    children_count = children_result.scalar() or 0
    if children_count > 0:
        raise HTTPException(status_code=400, detail=f"该分类下还有 {children_count} 个子话题，请先删除或移动")
    
    # 软删除
    topic.is_active = False
    
    # 更新父级的子话题数量
    if topic.parent_id:
        parent_result = await db.execute(select(Topic).where(Topic.id == topic.parent_id))
        parent = parent_result.scalar_one_or_none()
        if parent:
            parent.children_count = max(0, (parent.children_count or 0) - 1)
    
    await db.commit()
    
    return {"message": "删除成功"}


# ========== 热门排行API ==========

@router.get("/hot-posts")
async def get_hot_posts(
    limit: int = Query(10, ge=1, le=50),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取热门帖子排行"""
    query = select(Post).where(Post.status == "published")
    query = query.order_by(desc(Post.like_count + Post.comment_count * 2 + Post.view_count / 10))
    query = query.limit(limit)
    
    result = await db.execute(query)
    posts = result.scalars().all()
    
    items = []
    for i, post in enumerate(posts):
        user_result = await db.execute(select(User).where(User.id == post.user_id))
        user = user_result.scalar_one_or_none()
        
        items.append({
            "rank": i + 1,
            "id": post.id,
            "content": post.content[:50] + "..." if len(post.content) > 50 else post.content,
            "user": {
                "id": user.id if user else 0,
                "nickname": user.nickname or user.username if user else "已删除"
            },
            "like_count": post.like_count,
            "comment_count": post.comment_count,
            "view_count": post.view_count,
            "score": post.like_count + post.comment_count * 2 + post.view_count // 10
        })
    
    return items


@router.get("/active-users")
async def get_active_users(
    limit: int = Query(10, ge=1, le=50),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取活跃用户排行"""
    # 统计用户发帖数
    query = select(
        Post.user_id,
        func.count(Post.id).label("post_count")
    ).where(Post.status == "published")
    query = query.group_by(Post.user_id)
    query = query.order_by(desc("post_count"))
    query = query.limit(limit)
    
    result = await db.execute(query)
    user_stats = result.fetchall()
    
    items = []
    for i, (user_id, post_count) in enumerate(user_stats):
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        
        if user:
            items.append({
                "rank": i + 1,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "nickname": user.nickname,
                    "avatar": user.avatar
                },
                "post_count": post_count
            })
    
    return items
