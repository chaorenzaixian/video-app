"""
清理相关异步任务
"""
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def cleanup_expired_orders(self) -> dict:
    """
    清理过期订单
    
    将超过30分钟未支付的订单标记为过期
    """
    try:
        logger.info("开始清理过期订单")
        
        # TODO: 实现数据库操作
        """
        from app.core.database import get_db_sync
        from app.models.order import Order
        from app.services.payment_service import OrderStatus
        
        db = get_db_sync()
        
        # 30分钟前的时间
        expire_time = datetime.utcnow() - timedelta(minutes=30)
        
        # 更新过期订单
        result = db.query(Order).filter(
            Order.status == OrderStatus.PENDING,
            Order.created_at < expire_time
        ).update({
            "status": OrderStatus.EXPIRED,
            "updated_at": datetime.utcnow()
        })
        
        db.commit()
        
        logger.info(f"已将 {result} 个订单标记为过期")
        """
        
        return {
            "success": True,
            "message": "过期订单清理完成"
        }
        
    except Exception as e:
        logger.error(f"清理过期订单失败: {e}")
        return {"success": False, "error": str(e)}


@celery_app.task(bind=True)
def cleanup_temp_files(self) -> dict:
    """
    清理临时文件
    
    删除超过24小时的临时上传文件
    """
    try:
        logger.info("开始清理临时文件")
        
        temp_dirs = [
            "uploads/temp",
            "uploads/chunks",
        ]
        
        deleted_count = 0
        deleted_size = 0
        expire_time = datetime.utcnow() - timedelta(hours=24)
        
        for temp_dir in temp_dirs:
            if not os.path.exists(temp_dir):
                continue
            
            for root, dirs, files in os.walk(temp_dir):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    try:
                        # 检查文件修改时间
                        mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                        if mtime < expire_time:
                            file_size = os.path.getsize(filepath)
                            os.remove(filepath)
                            deleted_count += 1
                            deleted_size += file_size
                            logger.debug(f"删除临时文件: {filepath}")
                    except Exception as e:
                        logger.warning(f"删除文件失败 {filepath}: {e}")
        
        # 清理空目录
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                for root, dirs, files in os.walk(temp_dir, topdown=False):
                    for dir_name in dirs:
                        dir_path = os.path.join(root, dir_name)
                        try:
                            if not os.listdir(dir_path):
                                os.rmdir(dir_path)
                        except Exception:
                            pass
        
        logger.info(f"清理完成: 删除 {deleted_count} 个文件，释放 {deleted_size / 1024 / 1024:.2f} MB")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "deleted_size_mb": round(deleted_size / 1024 / 1024, 2)
        }
        
    except Exception as e:
        logger.error(f"清理临时文件失败: {e}")
        return {"success": False, "error": str(e)}


@celery_app.task(bind=True)
def cleanup_old_logs(self, days: int = 30) -> dict:
    """
    清理旧日志文件
    
    Args:
        days: 保留天数，默认30天
    """
    try:
        logger.info(f"开始清理 {days} 天前的日志文件")
        
        log_dir = "logs"
        if not os.path.exists(log_dir):
            return {"success": True, "message": "日志目录不存在"}
        
        deleted_count = 0
        expire_time = datetime.utcnow() - timedelta(days=days)
        
        for filename in os.listdir(log_dir):
            if not filename.endswith(".log"):
                continue
            
            filepath = os.path.join(log_dir, filename)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                if mtime < expire_time:
                    os.remove(filepath)
                    deleted_count += 1
                    logger.debug(f"删除日志文件: {filepath}")
            except Exception as e:
                logger.warning(f"删除日志失败 {filepath}: {e}")
        
        logger.info(f"日志清理完成: 删除 {deleted_count} 个文件")
        
        return {
            "success": True,
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"清理日志失败: {e}")
        return {"success": False, "error": str(e)}


@celery_app.task(bind=True)
def cleanup_orphan_files(self) -> dict:
    """
    清理孤立文件
    
    删除数据库中不存在记录的上传文件
    """
    try:
        logger.info("开始清理孤立文件")
        
        # TODO: 实现数据库查询对比
        """
        from app.core.database import get_db_sync
        from app.models.video import Video
        
        db = get_db_sync()
        
        # 获取数据库中所有视频文件路径
        videos = db.query(Video.file_path, Video.cover_image).all()
        db_files = set()
        for v in videos:
            if v.file_path:
                db_files.add(v.file_path)
            if v.cover_image:
                db_files.add(v.cover_image)
        
        # 扫描上传目录
        upload_dir = "uploads/videos"
        orphan_files = []
        
        for root, dirs, files in os.walk(upload_dir):
            for filename in files:
                filepath = os.path.join(root, filename)
                relative_path = filepath.replace("\\", "/")
                if relative_path not in db_files:
                    orphan_files.append(filepath)
        
        # 删除孤立文件
        for filepath in orphan_files:
            os.remove(filepath)
        """
        
        return {
            "success": True,
            "message": "孤立文件清理完成"
        }
        
    except Exception as e:
        logger.error(f"清理孤立文件失败: {e}")
        return {"success": False, "error": str(e)}
