"""
社交功能API
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User, UserVIP
from app.models.video import Video
from app.models.social import (
    PrivateMessage, MessageConversation, VideoDanmaku,
    Playlist, PlaylistVideo, UserNotification
)
from app.models.creator import UserFollow
from app.models.coins import UserCoins, CoinTransaction

router = APIRouter(prefix="/social", tags=["社交功能"])

# 私信消费金币数
MESSAGE_COIN_COST = 100


# ==================== Schemas ====================

class SendMessageRequest(BaseModel):
    receiver_id: int
    content: str
    message_type: str = "text"


class DanmakuRequest(BaseModel):
    content: str
    time_offset: float
    color: str = "#FFFFFF"
    position: str = "scroll"


class CreatePlaylistRequest(BaseModel):
    title: str
    description: Optional[str] = None
    is_public: bool = False


# ==================== 私信 ====================

@router.get("/messages/conversations")
async def get_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取会话列表"""
    query = select(MessageConversation).where(
        or_(
            MessageConversation.user1_id == current_user.id,
            MessageConversation.user2_id == current_user.id
        )
    ).order_by(MessageConversation.last_message_at.desc())
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    
    conversations = []
    for conv in result.scalars().all():
        # 获取对方用户信息
        other_user_id = conv.user2_id if conv.user1_id == current_user.id else conv.user1_id
        user_result = await db.execute(select(User).where(User.id == other_user_id))
        other_user = user_result.scalar_one_or_none()
        
        # 获取对方用户的VIP信息
        vip_level = 0
        is_vip = False
        if other_user:
            try:
                vip_result = await db.execute(
                    select(UserVIP).where(
                        UserVIP.user_id == other_user.id,
                        UserVIP.is_active == True
                    )
                )
                user_vip = vip_result.scalar_one_or_none()
                if user_vip and user_vip.expire_date and user_vip.expire_date > datetime.utcnow():
                    is_vip = True
                    vip_level = user_vip.vip_level or 1
            except Exception:
                pass  # 忽略VIP查询错误
        
        # 获取未读数
        unread = conv.user1_unread if conv.user1_id == current_user.id else conv.user2_unread
        
        # 获取最后一条消息
        last_msg = None
        if conv.last_message_id:
            msg_result = await db.execute(
                select(PrivateMessage).where(PrivateMessage.id == conv.last_message_id)
            )
            last_msg = msg_result.scalar_one_or_none()
        
        conversations.append({
            "id": conv.id,
            "other_user": {
                "id": other_user.id if other_user else 0,
                "nickname": other_user.nickname if other_user else "未知用户",
                "avatar": other_user.avatar if other_user else None,
                "is_vip": is_vip,
                "vip_level": vip_level
            },
            "last_message": last_msg.content if last_msg else None,
            "last_message_at": conv.last_message_at,
            "unread_count": unread
        })
    
    return conversations


@router.get("/messages/cost")
async def get_message_cost():
    """获取私信消费金币数"""
    return {"cost": MESSAGE_COIN_COST}


@router.get("/messages/{user_id}")
async def get_messages(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取与某用户的消息记录"""
    query = select(PrivateMessage).where(
        or_(
            and_(PrivateMessage.sender_id == current_user.id, PrivateMessage.receiver_id == user_id),
            and_(PrivateMessage.sender_id == user_id, PrivateMessage.receiver_id == current_user.id)
        )
    ).order_by(PrivateMessage.created_at.desc())
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    
    messages = [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "content": m.content,
            "message_type": m.message_type,
            "is_mine": m.sender_id == current_user.id,
            "created_at": m.created_at
        }
        for m in result.scalars().all()
    ]
    
    # 标记已读
    await db.execute(
        PrivateMessage.__table__.update().where(
            and_(
                PrivateMessage.sender_id == user_id,
                PrivateMessage.receiver_id == current_user.id,
                PrivateMessage.is_read == False
            )
        ).values(is_read=True, read_at=datetime.utcnow())
    )
    await db.commit()
    
    return messages[::-1]  # 返回正序


@router.post("/messages")
async def send_message(
    data: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """发送私信（消耗金币）"""
    if data.receiver_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能给自己发私信")
    
    # 检查接收者是否存在
    receiver_result = await db.execute(select(User).where(User.id == data.receiver_id))
    receiver = receiver_result.scalar_one_or_none()
    if not receiver:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查用户金币余额
    coins_result = await db.execute(
        select(UserCoins).where(UserCoins.user_id == current_user.id)
    )
    user_coins = coins_result.scalar_one_or_none()
    
    if not user_coins or user_coins.balance < MESSAGE_COIN_COST:
        raise HTTPException(
            status_code=400, 
            detail=f"金币余额不足，发送私信需要{MESSAGE_COIN_COST}金币"
        )
    
    # 扣除金币
    user_coins.balance -= MESSAGE_COIN_COST
    user_coins.total_spent += MESSAGE_COIN_COST
    
    # 记录金币变动
    coin_transaction = CoinTransaction(
        user_id=current_user.id,
        amount=-MESSAGE_COIN_COST,
        balance_after=user_coins.balance,
        transaction_type="message",
        source_type="private_message",
        source_id=data.receiver_id,
        description=f"发送私信给: {receiver.nickname or receiver.username}"
    )
    db.add(coin_transaction)
    
    # 创建消息
    message = PrivateMessage(
        sender_id=current_user.id,
        receiver_id=data.receiver_id,
        content=data.content,
        message_type=data.message_type
    )
    db.add(message)
    await db.flush()
    
    # 更新或创建会话
    user1_id = min(current_user.id, data.receiver_id)
    user2_id = max(current_user.id, data.receiver_id)
    
    conv_result = await db.execute(
        select(MessageConversation).where(
            MessageConversation.user1_id == user1_id,
            MessageConversation.user2_id == user2_id
        )
    )
    conv = conv_result.scalar_one_or_none()
    
    if conv:
        conv.last_message_id = message.id
        conv.last_message_at = datetime.utcnow()
        # 增加对方未读数
        if current_user.id == user1_id:
            conv.user2_unread += 1
        else:
            conv.user1_unread += 1
    else:
        conv = MessageConversation(
            user1_id=user1_id,
            user2_id=user2_id,
            last_message_id=message.id,
            last_message_at=datetime.utcnow(),
            user1_unread=1 if current_user.id == user2_id else 0,
            user2_unread=1 if current_user.id == user1_id else 0
        )
        db.add(conv)
    
    await db.commit()
    
    return {
        "message": "发送成功", 
        "message_id": message.id,
        "coins_cost": MESSAGE_COIN_COST,
        "balance": user_coins.balance
    }


# ==================== 弹幕 ====================

@router.get("/danmaku/{video_id}")
async def get_danmakus(
    video_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取视频弹幕"""
    result = await db.execute(
        select(VideoDanmaku).where(
            VideoDanmaku.video_id == video_id,
            VideoDanmaku.is_visible == True
        ).order_by(VideoDanmaku.time_offset)
    )
    
    return [
        {
            "id": d.id,
            "content": d.content,
            "time": d.time_offset,
            "color": d.color,
            "position": d.position
        }
        for d in result.scalars().all()
    ]


@router.post("/danmaku/{video_id}")
async def send_danmaku(
    video_id: int,
    data: DanmakuRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """发送弹幕"""
    # 检查视频是否存在
    video = await db.execute(select(Video).where(Video.id == video_id))
    if not video.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="视频不存在")
    
    if len(data.content) > 50:
        raise HTTPException(status_code=400, detail="弹幕内容过长")
    
    danmaku = VideoDanmaku(
        video_id=video_id,
        user_id=current_user.id,
        content=data.content,
        time_offset=data.time_offset,
        color=data.color,
        position=data.position
    )
    db.add(danmaku)
    await db.commit()
    
    return {"message": "弹幕发送成功", "id": danmaku.id}


# ==================== 播放列表 ====================

@router.get("/playlists")
async def get_my_playlists(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取我的播放列表"""
    result = await db.execute(
        select(Playlist).where(Playlist.user_id == current_user.id)
        .order_by(Playlist.updated_at.desc())
    )
    
    return [
        {
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "cover_image": p.cover_image,
            "video_count": p.video_count,
            "is_public": p.is_public
        }
        for p in result.scalars().all()
    ]


@router.post("/playlists")
async def create_playlist(
    data: CreatePlaylistRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建播放列表"""
    playlist = Playlist(
        user_id=current_user.id,
        title=data.title,
        description=data.description,
        is_public=data.is_public
    )
    db.add(playlist)
    await db.commit()
    
    return {"message": "创建成功", "playlist_id": playlist.id}


@router.post("/playlists/{playlist_id}/videos/{video_id}")
async def add_video_to_playlist(
    playlist_id: int,
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """添加视频到播放列表"""
    # 验证播放列表
    playlist = await db.execute(
        select(Playlist).where(
            Playlist.id == playlist_id,
            Playlist.user_id == current_user.id
        )
    )
    playlist = playlist.scalar_one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="播放列表不存在")
    
    # 检查视频是否已在列表中
    existing = await db.execute(
        select(PlaylistVideo).where(
            PlaylistVideo.playlist_id == playlist_id,
            PlaylistVideo.video_id == video_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="视频已在列表中")
    
    # 添加视频
    pv = PlaylistVideo(
        playlist_id=playlist_id,
        video_id=video_id,
        sort_order=playlist.video_count
    )
    db.add(pv)
    playlist.video_count += 1
    
    await db.commit()
    
    return {"message": "添加成功"}


@router.delete("/playlists/{playlist_id}/videos/{video_id}")
async def remove_video_from_playlist(
    playlist_id: int,
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """从播放列表移除视频"""
    playlist = await db.execute(
        select(Playlist).where(
            Playlist.id == playlist_id,
            Playlist.user_id == current_user.id
        )
    )
    playlist = playlist.scalar_one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="播放列表不存在")
    
    pv = await db.execute(
        select(PlaylistVideo).where(
            PlaylistVideo.playlist_id == playlist_id,
            PlaylistVideo.video_id == video_id
        )
    )
    pv = pv.scalar_one_or_none()
    if pv:
        await db.delete(pv)
        playlist.video_count = max(0, playlist.video_count - 1)
        await db.commit()
    
    return {"message": "已移除"}


# ==================== 通知 ====================

@router.get("/notifications")
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取通知列表"""
    query = select(UserNotification).where(
        UserNotification.user_id == current_user.id
    ).order_by(UserNotification.created_at.desc())
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    
    return [
        {
            "id": n.id,
            "type": n.notification_type,
            "title": n.title,
            "content": n.content,
            "is_read": n.is_read,
            "created_at": n.created_at
        }
        for n in result.scalars().all()
    ]


@router.get("/notifications/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取未读通知数"""
    result = await db.execute(
        select(func.count(UserNotification.id)).where(
            UserNotification.user_id == current_user.id,
            UserNotification.is_read == False
        )
    )
    return {"count": result.scalar() or 0}


@router.post("/notifications/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """标记所有通知已读"""
    await db.execute(
        UserNotification.__table__.update().where(
            UserNotification.user_id == current_user.id,
            UserNotification.is_read == False
        ).values(is_read=True, read_at=datetime.utcnow())
    )
    await db.commit()
    return {"message": "已全部标记已读"}
