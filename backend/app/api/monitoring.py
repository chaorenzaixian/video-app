"""
监控API端点
提供系统和应用性能指标
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.admin import get_admin_user
from app.models.user import User
from app.services.monitoring_service import monitor

router = APIRouter(prefix="/admin/monitoring", tags=["Monitoring"])


@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "video-app-backend"
    }


@router.get("/metrics")
async def get_metrics(
    current_user: User = Depends(get_admin_user)
):
    """
    获取完整监控指标（仅管理员）
    
    返回系统资源、应用性能、端点统计等信息
    """
    return monitor.get_full_report()


@router.get("/system")
async def get_system_metrics(
    current_user: User = Depends(get_admin_user)
):
    """获取系统资源指标"""
    return monitor.get_system_metrics()


@router.get("/application")
async def get_application_metrics(
    current_user: User = Depends(get_admin_user)
):
    """获取应用性能指标"""
    return monitor.get_application_metrics()


@router.get("/endpoints")
async def get_endpoint_metrics(
    top_n: int = 20,
    current_user: User = Depends(get_admin_user)
):
    """获取端点性能指标"""
    return monitor.get_endpoint_metrics(top_n)


@router.get("/slow-requests")
async def get_slow_requests(
    limit: int = 50,
    current_user: User = Depends(get_admin_user)
):
    """获取慢请求列表"""
    return monitor.get_slow_requests(limit)


@router.post("/reset")
async def reset_metrics(
    current_user: User = Depends(get_admin_user)
):
    """重置监控指标（仅超级管理员）"""
    from app.models.user import UserRole
    
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="仅超级管理员可以重置指标")
    
    monitor.reset_metrics()
    return {"message": "监控指标已重置"}


@router.get("/database")
async def get_database_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """获取数据库统计信息"""
    from sqlalchemy import text
    
    try:
        # PostgreSQL 统计查询
        stats = {}
        
        # 数据库大小
        result = await db.execute(text(
            "SELECT pg_database_size(current_database()) as size"
        ))
        row = result.fetchone()
        stats["database_size_mb"] = round(row[0] / 1024 / 1024, 2) if row else 0
        
        # 活跃连接数
        result = await db.execute(text(
            "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
        ))
        row = result.fetchone()
        stats["active_connections"] = row[0] if row else 0
        
        # 表统计
        result = await db.execute(text("""
            SELECT relname as table_name, 
                   n_live_tup as row_count
            FROM pg_stat_user_tables 
            ORDER BY n_live_tup DESC 
            LIMIT 10
        """))
        stats["top_tables"] = [
            {"table": row[0], "rows": row[1]} 
            for row in result.fetchall()
        ]
        
        return stats
        
    except Exception as e:
        return {"error": str(e)}
