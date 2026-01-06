"""
监控相关API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime, timedelta
from typing import Dict, Any
from pydantic import BaseModel
import psutil

from app.core.database import get_db
from app.api.deps import get_admin_user
from app.models.user import User
from app.models.video import Video, VideoView
from app.models.payment import PaymentOrder, PaymentStatus

router = APIRouter()


class SystemStatus(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    uptime: str


class DatabaseStatus(BaseModel):
    status: str
    connections: int
    response_time_ms: float


class ServerStatus(BaseModel):
    system: SystemStatus
    database: DatabaseStatus
    timestamp: datetime


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@router.get("/status", response_model=ServerStatus)
async def get_server_status(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取服务器状态"""
    # 系统状态
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # 计算运行时间
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    uptime_str = f"{uptime.days}天{uptime.seconds // 3600}小时"
    
    # 数据库状态
    start_time = datetime.now()
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except:
        db_status = "unhealthy"
    response_time = (datetime.now() - start_time).total_seconds() * 1000
    
    return ServerStatus(
        system=SystemStatus(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=disk.percent,
            uptime=uptime_str
        ),
        database=DatabaseStatus(
            status=db_status,
            connections=0,  # 需要查询数据库连接数
            response_time_ms=response_time
        ),
        timestamp=datetime.utcnow()
    )


class RealtimeStats(BaseModel):
    online_users: int
    active_streams: int
    requests_per_minute: int
    bandwidth_mbps: float


@router.get("/realtime", response_model=RealtimeStats)
async def get_realtime_stats(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取实时统计"""
    # 在线用户（最近5分钟有活动）
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
    result = await db.execute(
        select(func.count()).select_from(User).where(User.last_login >= five_minutes_ago)
    )
    online_users = result.scalar() or 0
    
    # 活跃流数量（最近1分钟有观看记录的视频数）
    one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
    result = await db.execute(
        select(func.count(func.distinct(VideoView.video_id))).where(
            VideoView.created_at >= one_minute_ago
        )
    )
    active_streams = result.scalar() or 0
    
    # TODO: 从Redis获取请求数和带宽
    requests_per_minute = 0
    bandwidth_mbps = 0.0
    
    return RealtimeStats(
        online_users=online_users,
        active_streams=active_streams,
        requests_per_minute=requests_per_minute,
        bandwidth_mbps=bandwidth_mbps
    )


class ChartData(BaseModel):
    labels: list[str]
    data: list[int]


@router.get("/charts/users", response_model=ChartData)
async def get_user_chart(
    days: int = 7,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户增长图表数据"""
    labels = []
    data = []
    
    for i in range(days - 1, -1, -1):
        date = datetime.utcnow().date() - timedelta(days=i)
        start = datetime.combine(date, datetime.min.time())
        end = datetime.combine(date, datetime.max.time())
        
        result = await db.execute(
            select(func.count()).select_from(User).where(
                User.created_at >= start,
                User.created_at <= end
            )
        )
        count = result.scalar() or 0
        
        labels.append(date.strftime("%m-%d"))
        data.append(count)
    
    return ChartData(labels=labels, data=data)


@router.get("/charts/revenue", response_model=ChartData)
async def get_revenue_chart(
    days: int = 7,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取收入图表数据"""
    labels = []
    data = []
    
    for i in range(days - 1, -1, -1):
        date = datetime.utcnow().date() - timedelta(days=i)
        start = datetime.combine(date, datetime.min.time())
        end = datetime.combine(date, datetime.max.time())
        
        result = await db.execute(
            select(func.sum(PaymentOrder.amount)).where(
                PaymentOrder.status == PaymentStatus.SUCCESS,
                PaymentOrder.paid_at >= start,
                PaymentOrder.paid_at <= end
            )
        )
        amount = result.scalar() or 0
        
        labels.append(date.strftime("%m-%d"))
        data.append(int(amount))
    
    return ChartData(labels=labels, data=data)









