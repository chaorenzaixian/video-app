"""
Celery 异步任务配置
用于处理耗时任务如视频转码、邮件发送等
"""
import os
from celery import Celery
from kombu import Queue

# Redis URL
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 创建 Celery 应用
celery_app = Celery(
    "video_app",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.tasks.video_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.cleanup_tasks",
    ]
)

# Celery 配置
celery_app.conf.update(
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # 时区
    timezone="Asia/Shanghai",
    enable_utc=True,
    
    # 任务结果过期时间（1天）
    result_expires=86400,
    
    # 任务确认
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # 并发控制
    worker_prefetch_multiplier=1,
    worker_concurrency=2,
    
    # 任务路由
    task_queues=(
        Queue("default", routing_key="default"),
        Queue("video", routing_key="video.#"),
        Queue("notification", routing_key="notification.#"),
        Queue("cleanup", routing_key="cleanup.#"),
    ),
    task_default_queue="default",
    task_default_routing_key="default",
    
    task_routes={
        "app.tasks.video_tasks.*": {"queue": "video"},
        "app.tasks.notification_tasks.*": {"queue": "notification"},
        "app.tasks.cleanup_tasks.*": {"queue": "cleanup"},
    },
    
    # 任务重试
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # 定时任务
    beat_schedule={
        # 每小时清理过期订单
        "cleanup-expired-orders": {
            "task": "app.tasks.cleanup_tasks.cleanup_expired_orders",
            "schedule": 3600.0,
        },
        # 每天凌晨清理临时文件
        "cleanup-temp-files": {
            "task": "app.tasks.cleanup_tasks.cleanup_temp_files",
            "schedule": 86400.0,
        },
        # 每天检查VIP过期
        "check-vip-expiry": {
            "task": "app.tasks.notification_tasks.check_vip_expiry",
            "schedule": 86400.0,
        },
    },
)


def get_celery_app() -> Celery:
    """获取 Celery 应用实例"""
    return celery_app
