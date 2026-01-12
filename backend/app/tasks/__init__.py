"""
Celery 异步任务模块
"""
from app.core.celery_app import celery_app

__all__ = ["celery_app"]
