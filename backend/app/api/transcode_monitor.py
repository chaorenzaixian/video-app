"""
转码监控API - 从转码服务器获取实时状态
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
import httpx
import os

from app.api.deps import get_admin_user
from app.models.user import User

router = APIRouter(prefix="/admin/transcode")

# 转码服务器配置
TRANSCODE_SERVER_URL = os.getenv("TRANSCODE_SERVER_URL", "http://198.176.60.121:5001")
TRANSCODE_SECRET_KEY = os.getenv("TRANSCODE_SECRET_KEY", "vYTWoms4FKOqySca1jCLtNHRVz3BAI6U")


async def call_transcode_api(endpoint: str, method: str = "GET", params: dict = None):
    """调用转码服务器API"""
    url = f"{TRANSCODE_SERVER_URL}{endpoint}"
    headers = {"X-Transcode-Key": TRANSCODE_SECRET_KEY}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers, params=params)
            else:
                response = await client.post(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="无法连接到转码服务器")
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="转码服务器响应超时")


@router.get("/status")
async def get_transcode_status(
    current_user: User = Depends(get_admin_user)
):
    """获取转码系统完整状态"""
    return await call_transcode_api("/status")


@router.get("/logs")
async def get_transcode_logs(
    lines: int = 50,
    current_user: User = Depends(get_admin_user)
):
    """获取转码日志"""
    return await call_transcode_api("/logs", params={"lines": lines})


@router.post("/service/restart")
async def restart_watcher_service(
    current_user: User = Depends(get_admin_user)
):
    """重启Watcher服务"""
    return await call_transcode_api("/service/restart", method="POST")


@router.get("/history")
async def get_transcode_history(
    limit: int = 20,
    current_user: User = Depends(get_admin_user)
):
    """获取转码历史记录"""
    # 这个可以从数据库获取
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.video import Video, VideoStatus
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Video)
            .where(Video.status.in_([VideoStatus.REVIEWING, VideoStatus.PUBLISHED]))
            .order_by(Video.created_at.desc())
            .limit(limit)
        )
        videos = result.scalars().all()
        
        history = []
        for v in videos:
            history.append({
                'id': v.id,
                'name': v.title,
                'type': 'short' if v.is_short else 'long',
                'status': v.status.value if hasattr(v.status, 'value') else str(v.status)
            })
        
        return {
            'history': history,
            'total': len(history)
        }
