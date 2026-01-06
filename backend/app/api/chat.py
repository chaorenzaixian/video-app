"""
客服聊天API - WebSocket实时通讯
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, desc
from typing import Dict, List, Optional
from datetime import datetime
import json
import asyncio
import os
import uuid

from app.core.database import get_db, AsyncSessionLocal
from app.models.chat import ChatSession, ChatMessage, QuickReply
from app.models.user import User, UserRole, UserVIP
from app.api.deps import get_current_user, get_admin_user
from pydantic import BaseModel


router = APIRouter()

# 防刷屏 - 用户消息频率限制
user_message_times: Dict[int, list] = {}  # user_id -> [timestamp1, timestamp2, ...]
MESSAGE_COOLDOWN = 2  # 两条消息之间最少间隔2秒
MAX_MESSAGES_PER_MINUTE = 15  # 每分钟最多15条消息


def check_rate_limit(user_id: int) -> tuple[bool, str]:
    """检查用户发送频率是否超限
    Returns: (is_allowed, error_message)
    """
    now = datetime.utcnow().timestamp()
    
    if user_id not in user_message_times:
        user_message_times[user_id] = []
    
    # 清理1分钟前的记录
    user_message_times[user_id] = [t for t in user_message_times[user_id] if now - t < 60]
    
    times = user_message_times[user_id]
    
    # 检查冷却时间
    if times and now - times[-1] < MESSAGE_COOLDOWN:
        return False, f"发送太快了，请{MESSAGE_COOLDOWN}秒后再试"
    
    # 检查每分钟消息数
    if len(times) >= MAX_MESSAGES_PER_MINUTE:
        return False, "发送消息过于频繁，请稍后再试"
    
    # 记录这次发送
    user_message_times[user_id].append(now)
    return True, ""


# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        # user_id -> WebSocket
        self.user_connections: Dict[int, WebSocket] = {}
        # agent_id -> WebSocket (客服)
        self.agent_connections: Dict[int, WebSocket] = {}
        # session_id -> List[WebSocket] (会话中的连接)
        self.session_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect_user(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.user_connections[user_id] = websocket
    
    async def connect_agent(self, websocket: WebSocket, agent_id: int):
        await websocket.accept()
        self.agent_connections[agent_id] = websocket
    
    def disconnect_user(self, user_id: int):
        if user_id in self.user_connections:
            del self.user_connections[user_id]
    
    def disconnect_agent(self, agent_id: int):
        if agent_id in self.agent_connections:
            del self.agent_connections[agent_id]
    
    async def send_to_user(self, user_id: int, message: dict):
        if user_id in self.user_connections:
            try:
                await self.user_connections[user_id].send_json(message)
            except Exception:
                self.disconnect_user(user_id)
    
    async def send_to_agent(self, agent_id: int, message: dict):
        if agent_id in self.agent_connections:
            try:
                await self.agent_connections[agent_id].send_json(message)
            except Exception:
                self.disconnect_agent(agent_id)
    
    async def broadcast_to_agents(self, message: dict):
        """广播消息给所有在线客服"""
        for agent_id in list(self.agent_connections.keys()):
            await self.send_to_agent(agent_id, message)


manager = ConnectionManager()


# Pydantic模型
class SendMessageRequest(BaseModel):
    session_id: Optional[int] = None
    content: str
    message_type: str = "text"


class SessionResponse(BaseModel):
    id: int
    user_id: int
    agent_id: Optional[int]
    status: str
    title: Optional[str]
    unread_count: int
    user_unread_count: int
    created_at: datetime
    updated_at: datetime
    username: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    is_vip: bool = False
    vip_level: int = 0


class MessageResponse(BaseModel):
    id: int
    session_id: int
    sender_id: int
    is_from_user: bool
    message_type: str
    content: str
    is_read: bool
    created_at: datetime


# ==================== 用户端API ====================

@router.post("/sessions")
async def create_or_get_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取或创建聊天会话"""
    # 查找用户未关闭的会话
    query = select(ChatSession).where(
        and_(
            ChatSession.user_id == current_user.id,
            ChatSession.status != "closed"
        )
    ).order_by(ChatSession.created_at.desc())
    
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    is_new_session = False
    if not session:
        # 创建新会话
        session = ChatSession(
            user_id=current_user.id,
            status="waiting"
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        is_new_session = True
    
    # 对于新会话，直接添加欢迎消息
    if is_new_session:
        # 添加系统欢迎消息
        welcome_msg = ChatMessage(
            session_id=session.id,
            sender_id=current_user.id,
            is_from_user=False,
            message_type="text",
            content="人工客服已上线，您遇到什么问题请详细、清楚描述给客服喔\n请说明问题勿重复发话刷频，避免系统自动关闭，\n并且耐心等候客服给您回覆\n谢谢您。"
        )
        db.add(welcome_msg)
        await db.commit()
    
    if is_new_session:
        # 通知客服有新会话
        await manager.broadcast_to_agents({
            "type": "new_session",
            "session_id": session.id,
            "user_id": current_user.id,
            "username": current_user.username,
            "nickname": current_user.nickname
        })
    
    return {
        "id": session.id,
        "status": session.status,
        "agent_id": session.agent_id,
        "unread_count": session.user_unread_count
    }


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: int,
    page: int = 1,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取会话消息列表"""
    # 验证会话归属
    query = select(ChatSession).where(ChatSession.id == session_id)
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    is_admin = current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
    if not session or (session.user_id != current_user.id and not is_admin):
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 获取消息
    offset = (page - 1) * limit
    query = select(ChatMessage).where(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).offset(offset).limit(limit)
    
    result = await db.execute(query)
    messages = result.scalars().all()
    
    # 标记用户消息为已读
    if session.user_id == current_user.id:
        await db.execute(
            update(ChatMessage).where(
                and_(
                    ChatMessage.session_id == session_id,
                    ChatMessage.is_from_user == False,
                    ChatMessage.is_read == False
                )
            ).values(is_read=True)
        )
        session.user_unread_count = 0
        await db.commit()
    
    return [
        MessageResponse(
            id=m.id,
            session_id=m.session_id,
            sender_id=m.sender_id,
            is_from_user=m.is_from_user,
            message_type=m.message_type,
            content=m.content,
            is_read=m.is_read,
            created_at=m.created_at
        )
        for m in messages
    ]


@router.post("/messages")
async def send_message(
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """发送消息"""
    # 防刷屏检查
    is_allowed, error_msg = check_rate_limit(current_user.id)
    if not is_allowed:
        raise HTTPException(status_code=429, detail=error_msg)
    
    # 获取或创建会话
    if request.session_id:
        query = select(ChatSession).where(ChatSession.id == request.session_id)
        result = await db.execute(query)
        session = result.scalar_one_or_none()
        
        if not session or session.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="会话不存在")
    else:
        # 创建新会话
        session_result = await create_or_get_session(current_user, db)
        session_id = session_result["id"]
        query = select(ChatSession).where(ChatSession.id == session_id)
        result = await db.execute(query)
        session = result.scalar_one_or_none()
    
    # 创建消息
    message = ChatMessage(
        session_id=session.id,
        sender_id=current_user.id,
        is_from_user=True,
        message_type=request.message_type,
        content=request.content
    )
    db.add(message)
    
    # 更新会话
    if not session.title:
        session.title = request.content[:50]
    session.updated_at = datetime.utcnow()
    session.unread_count += 1
    
    await db.commit()
    await db.refresh(message)
    
    # 通过WebSocket发送给客服
    msg_data = {
        "type": "new_message",
        "session_id": session.id,
        "message": {
            "id": message.id,
            "sender_id": message.sender_id,
            "is_from_user": True,
            "content": message.content,
            "message_type": message.message_type,
            "created_at": message.created_at.isoformat()
        },
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "nickname": current_user.nickname
        }
    }
    
    # 发送给指定客服或广播
    if session.agent_id:
        await manager.send_to_agent(session.agent_id, msg_data)
    else:
        await manager.broadcast_to_agents(msg_data)
    
    return MessageResponse(
        id=message.id,
        session_id=message.session_id,
        sender_id=message.sender_id,
        is_from_user=message.is_from_user,
        message_type=message.message_type,
        content=message.content,
        is_read=message.is_read,
        created_at=message.created_at
    )


# ==================== 客服端API ====================

@router.get("/admin/sessions")
async def get_all_sessions(
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取所有聊天会话（客服用）"""
    query = select(ChatSession)
    
    if status:
        query = query.where(ChatSession.status == status)
    
    query = query.order_by(
        desc(ChatSession.unread_count),
        desc(ChatSession.updated_at)
    )
    
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    # 获取用户信息
    response = []
    for s in sessions:
        user_query = select(User).where(User.id == s.user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        # 获取VIP信息
        is_vip = False
        vip_level = 0
        if user:
            vip_query = select(UserVIP).where(UserVIP.user_id == user.id)
            vip_result = await db.execute(vip_query)
            user_vip = vip_result.scalar_one_or_none()
            if user_vip and user_vip.is_active:
                is_vip = True
                vip_level = user_vip.vip_level or 0
        
        response.append(SessionResponse(
            id=s.id,
            user_id=s.user_id,
            agent_id=s.agent_id,
            status=s.status,
            title=s.title,
            unread_count=s.unread_count,
            user_unread_count=s.user_unread_count,
            created_at=s.created_at,
            updated_at=s.updated_at,
            username=user.username if user else None,
            nickname=user.nickname if user else None,
            avatar=user.avatar if user else None,
            is_vip=is_vip,
            vip_level=vip_level
        ))
    
    return response


@router.post("/admin/sessions/{session_id}/claim")
async def claim_session(
    session_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """客服接入会话"""
    query = select(ChatSession).where(ChatSession.id == session_id)
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    session.agent_id = current_user.id
    session.status = "active"
    await db.commit()
    
    # 发送系统消息
    system_msg = ChatMessage(
        session_id=session.id,
        sender_id=current_user.id,
        is_from_user=False,
        message_type="system",
        content=f"客服 {current_user.nickname or current_user.username} 已接入会话"
    )
    db.add(system_msg)
    await db.commit()
    
    # 通知用户
    await manager.send_to_user(session.user_id, {
        "type": "agent_joined",
        "session_id": session.id,
        "agent_name": current_user.nickname or current_user.username
    })
    
    return {"message": "已接入会话"}


@router.post("/admin/messages")
async def agent_send_message(
    request: SendMessageRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """客服发送消息"""
    if not request.session_id:
        raise HTTPException(status_code=400, detail="缺少session_id")
    
    query = select(ChatSession).where(ChatSession.id == request.session_id)
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 创建消息
    message = ChatMessage(
        session_id=session.id,
        sender_id=current_user.id,
        is_from_user=False,
        message_type=request.message_type,
        content=request.content
    )
    db.add(message)
    
    # 更新会话
    session.updated_at = datetime.utcnow()
    session.user_unread_count += 1
    
    # 清除客服端未读
    await db.execute(
        update(ChatMessage).where(
            and_(
                ChatMessage.session_id == session.id,
                ChatMessage.is_from_user == True,
                ChatMessage.is_read == False
            )
        ).values(is_read=True)
    )
    session.unread_count = 0
    
    await db.commit()
    await db.refresh(message)
    
    # 通过WebSocket发送给用户
    await manager.send_to_user(session.user_id, {
        "type": "new_message",
        "session_id": session.id,
        "message": {
            "id": message.id,
            "sender_id": message.sender_id,
            "is_from_user": False,
            "content": message.content,
            "message_type": message.message_type,
            "created_at": message.created_at.isoformat()
        }
    })
    
    return MessageResponse(
        id=message.id,
        session_id=message.session_id,
        sender_id=message.sender_id,
        is_from_user=message.is_from_user,
        message_type=message.message_type,
        content=message.content,
        is_read=message.is_read,
        created_at=message.created_at
    )


@router.post("/admin/sessions/{session_id}/close")
async def close_session(
    session_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """关闭会话"""
    query = select(ChatSession).where(ChatSession.id == session_id)
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    session.status = "closed"
    session.closed_at = datetime.utcnow()
    
    # 发送系统消息
    system_msg = ChatMessage(
        session_id=session.id,
        sender_id=current_user.id,
        is_from_user=False,
        message_type="system",
        content="会话已结束，感谢您的咨询！"
    )
    db.add(system_msg)
    await db.commit()
    
    # 通知用户
    await manager.send_to_user(session.user_id, {
        "type": "session_closed",
        "session_id": session.id
    })
    
    return {"message": "会话已关闭"}


# ==================== 快捷回复API ====================

@router.get("/quick-replies")
async def get_quick_replies(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取快捷回复列表"""
    query = select(QuickReply).where(QuickReply.is_active == True)
    
    if category:
        query = query.where(QuickReply.category == category)
    
    query = query.order_by(QuickReply.sort_order.asc())
    
    result = await db.execute(query)
    replies = result.scalars().all()
    
    return [
        {
            "id": r.id,
            "category": r.category,
            "title": r.title,
            "content": r.content
        }
        for r in replies
    ]


# ==================== 图片上传API ====================

@router.post("/upload-image")
async def upload_chat_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传聊天图片（自动转WebP优化）"""
    from app.services.image_service import ImageService
    
    # 验证文件类型
    if file.content_type not in ImageService.SUPPORTED_FORMATS:
        raise HTTPException(status_code=400, detail="不支持的图片格式")
    
    # 读取文件内容
    contents = await file.read()
    
    # 验证图片
    valid, error = ImageService.validate_image(contents, file.content_type)
    if not valid:
        raise HTTPException(status_code=400, detail=error)
    
    try:
        # 使用图片服务处理并保存
        result = await ImageService.save_image(
            content=contents,
            subdir="chat",
            filename=f"chat_{current_user.id}_{uuid.uuid4().hex[:8]}",
            convert_webp=True
        )
        return {"url": result["url"], "filename": result["filename"], "optimized": ImageService.is_available()}
    except Exception as e:
        # 降级处理
        upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "chat")
        os.makedirs(upload_dir, exist_ok=True)
        ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"chat_{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"
        file_path = os.path.join(upload_dir, filename)
        with open(file_path, "wb") as f:
            f.write(contents)
        return {"url": f"/uploads/chat/{filename}", "filename": filename, "optimized": False}


# ==================== 消息已读状态API ====================

@router.post("/sessions/{session_id}/read")
async def mark_messages_read(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """标记消息为已读"""
    # 获取会话
    query = select(ChatSession).where(ChatSession.id == session_id)
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 判断是用户还是客服
    is_user = session.user_id == current_user.id
    
    if is_user:
        # 用户标记客服消息为已读
        await db.execute(
            update(ChatMessage).where(
                and_(
                    ChatMessage.session_id == session_id,
                    ChatMessage.is_from_user == False,
                    ChatMessage.is_read == False
                )
            ).values(is_read=True)
        )
        session.user_unread_count = 0
        
        # 通知客服消息已读
        if session.agent_id:
            await manager.send_to_agent(session.agent_id, {
                "type": "messages_read",
                "session_id": session_id,
                "reader": "user"
            })
    else:
        # 客服标记用户消息为已读
        await db.execute(
            update(ChatMessage).where(
                and_(
                    ChatMessage.session_id == session_id,
                    ChatMessage.is_from_user == True,
                    ChatMessage.is_read == False
                )
            ).values(is_read=True)
        )
        session.unread_count = 0
        
        # 通知用户消息已读
        await manager.send_to_user(session.user_id, {
            "type": "messages_read",
            "session_id": session_id,
            "reader": "agent"
        })
    
    await db.commit()
    
    return {"message": "已标记为已读"}


# ==================== 客服信息API ====================

@router.get("/agent-info/{agent_id}")
async def get_agent_info(
    agent_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取客服信息"""
    query = select(User).where(User.id == agent_id)
    result = await db.execute(query)
    agent = result.scalar_one_or_none()
    
    if not agent:
        return {
            "id": agent_id,
            "name": "客服",
            "avatar": None
        }
    
    return {
        "id": agent.id,
        "name": agent.nickname or agent.username or "客服",
        "avatar": agent.avatar
    }


@router.get("/sessions/{session_id}/info")
async def get_session_info(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取会话详情（包含用户和客服信息）"""
    query = select(ChatSession).where(ChatSession.id == session_id)
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 获取用户信息
    user_query = select(User).where(User.id == session.user_id)
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()
    
    # 获取客服信息
    agent = None
    if session.agent_id:
        agent_query = select(User).where(User.id == session.agent_id)
        agent_result = await db.execute(agent_query)
        agent = agent_result.scalar_one_or_none()
    
    return {
        "id": session.id,
        "status": session.status,
        "user": {
            "id": user.id if user else session.user_id,
            "name": user.nickname or user.username if user else f"用户{session.user_id}",
            "avatar": user.avatar if user else None
        },
        "agent": {
            "id": agent.id,
            "name": agent.nickname or agent.username or "客服",
            "avatar": agent.avatar
        } if agent else None,
        "created_at": session.created_at,
        "updated_at": session.updated_at
    }


# ==================== WebSocket端点 ====================

@router.websocket("/ws/user/{user_id}")
async def websocket_user(websocket: WebSocket, user_id: int, token: str = Query(...)):
    """用户端WebSocket连接"""
    # 验证token (简化处理)
    await manager.connect_user(websocket, user_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # 处理心跳
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue
            
            # 处理消息
            if data.get("type") == "message":
                async with AsyncSessionLocal() as db:
                    # 获取用户
                    user_query = select(User).where(User.id == user_id)
                    user_result = await db.execute(user_query)
                    user = user_result.scalar_one_or_none()
                    
                    if user:
                        # 创建或获取会话
                        session_query = select(ChatSession).where(
                            and_(
                                ChatSession.user_id == user_id,
                                ChatSession.status != "closed"
                            )
                        )
                        session_result = await db.execute(session_query)
                        session = session_result.scalar_one_or_none()
                        
                        if not session:
                            session = ChatSession(user_id=user_id, status="waiting")
                            db.add(session)
                            await db.commit()
                            await db.refresh(session)
                        
                        # 创建消息
                        message = ChatMessage(
                            session_id=session.id,
                            sender_id=user_id,
                            is_from_user=True,
                            content=data.get("content", "")
                        )
                        db.add(message)
                        
                        if not session.title:
                            session.title = data.get("content", "")[:50]
                        session.updated_at = datetime.utcnow()
                        session.unread_count += 1
                        
                        await db.commit()
                        await db.refresh(message)
                        
                        # 发送给客服
                        msg_data = {
                            "type": "new_message",
                            "session_id": session.id,
                            "message": {
                                "id": message.id,
                                "sender_id": message.sender_id,
                                "is_from_user": True,
                                "content": message.content,
                                "created_at": message.created_at.isoformat()
                            }
                        }
                        
                        if session.agent_id:
                            await manager.send_to_agent(session.agent_id, msg_data)
                        else:
                            await manager.broadcast_to_agents(msg_data)
                        
                        # 确认消息已发送
                        await websocket.send_json({
                            "type": "message_sent",
                            "message_id": message.id,
                            "session_id": session.id
                        })
    
    except WebSocketDisconnect:
        manager.disconnect_user(user_id)


@router.websocket("/ws/agent/{agent_id}")
async def websocket_agent(websocket: WebSocket, agent_id: int, token: str = Query(...)):
    """客服端WebSocket连接"""
    # 验证token和权限 (简化处理)
    await manager.connect_agent(websocket, agent_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # 处理心跳
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue
            
            # 处理客服发送的消息
            if data.get("type") == "message":
                session_id = data.get("session_id")
                content = data.get("content", "")
                
                if session_id and content:
                    async with AsyncSessionLocal() as db:
                        session_query = select(ChatSession).where(ChatSession.id == session_id)
                        session_result = await db.execute(session_query)
                        session = session_result.scalar_one_or_none()
                        
                        if session:
                            message = ChatMessage(
                                session_id=session.id,
                                sender_id=agent_id,
                                is_from_user=False,
                                content=content
                            )
                            db.add(message)
                            session.updated_at = datetime.utcnow()
                            session.user_unread_count += 1
                            
                            await db.commit()
                            await db.refresh(message)
                            
                            # 发送给用户
                            await manager.send_to_user(session.user_id, {
                                "type": "new_message",
                                "session_id": session.id,
                                "message": {
                                    "id": message.id,
                                    "sender_id": message.sender_id,
                                    "is_from_user": False,
                                    "content": message.content,
                                    "created_at": message.created_at.isoformat()
                                }
                            })
                            
                            # 确认
                            await websocket.send_json({
                                "type": "message_sent",
                                "message_id": message.id
                            })
    
    except WebSocketDisconnect:
        manager.disconnect_agent(agent_id)

