"""
定时任务服务
处理订单过期、数据清理等定时任务
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.payment import PaymentOrder, PaymentStatus
from app.models.coins import RechargeOrder


class ScheduledTasks:
    """定时任务管理器"""
    
    _running = False
    _task = None
    
    @classmethod
    async def start(cls):
        """启动定时任务"""
        if cls._running:
            return
        cls._running = True
        cls._task = asyncio.create_task(cls._run_scheduler())
        print("[ScheduledTasks] 定时任务已启动")
    
    @classmethod
    async def stop(cls):
        """停止定时任务"""
        cls._running = False
        if cls._task:
            cls._task.cancel()
            try:
                await cls._task
            except asyncio.CancelledError:
                pass
        print("[ScheduledTasks] 定时任务已停止")
    
    @classmethod
    async def _run_scheduler(cls):
        """运行调度器"""
        while cls._running:
            try:
                # 每分钟执行一次检查
                await cls.cancel_expired_orders()
                await cls.cancel_expired_recharge_orders()
                
                # 每小时执行一次的任务（检查是否是整点）
                if datetime.utcnow().minute == 0:
                    await cls.cleanup_old_temp_files()
                
            except Exception as e:
                print(f"[ScheduledTasks] 任务执行出错: {e}")
            
            # 等待60秒
            await asyncio.sleep(60)
    
    @classmethod
    async def cancel_expired_orders(cls):
        """取消过期的VIP订单"""
        async with AsyncSessionLocal() as db:
            try:
                now = datetime.utcnow()
                
                # 查找过期的待支付订单
                # 注意：PaymentStatus没有EXPIRED状态，改用CANCELLED
                result = await db.execute(
                    update(PaymentOrder)
                    .where(
                        PaymentOrder.status == PaymentStatus.PENDING,
                        PaymentOrder.expire_at < now
                    )
                    .values(status=PaymentStatus.CANCELLED)
                    .returning(PaymentOrder.id)
                )
                
                expired_count = len(result.fetchall())
                if expired_count > 0:
                    await db.commit()
                    print(f"[ScheduledTasks] 已取消 {expired_count} 个过期VIP订单")
                    
            except Exception as e:
                await db.rollback()
                print(f"[ScheduledTasks] 取消过期VIP订单失败: {e}")
    
    @classmethod
    async def cancel_expired_recharge_orders(cls):
        """取消过期的充值订单"""
        async with AsyncSessionLocal() as db:
            try:
                now = datetime.utcnow()
                # 超过2小时未支付的订单自动取消
                expire_threshold = now - timedelta(hours=2)
                
                result = await db.execute(
                    update(RechargeOrder)
                    .where(
                        RechargeOrder.status == "pending",
                        RechargeOrder.created_at < expire_threshold
                    )
                    .values(status="expired")
                    .returning(RechargeOrder.id)
                )
                
                expired_count = len(result.fetchall())
                if expired_count > 0:
                    await db.commit()
                    print(f"[ScheduledTasks] 已取消 {expired_count} 个过期充值订单")
                    
            except Exception as e:
                await db.rollback()
                print(f"[ScheduledTasks] 取消过期充值订单失败: {e}")
    
    @classmethod
    async def cleanup_old_temp_files(cls):
        """清理旧的临时文件"""
        import os
        import shutil
        from app.core.config import settings
        
        try:
            # 清理超过24小时的临时封面
            temp_covers_dir = os.path.join(settings.UPLOAD_DIR, "temp_covers")
            if os.path.exists(temp_covers_dir):
                now = datetime.utcnow().timestamp()
                threshold = 24 * 3600  # 24小时
                
                cleaned_count = 0
                for user_dir in os.listdir(temp_covers_dir):
                    user_path = os.path.join(temp_covers_dir, user_dir)
                    if os.path.isdir(user_path):
                        for filename in os.listdir(user_path):
                            filepath = os.path.join(user_path, filename)
                            if os.path.isfile(filepath):
                                file_age = now - os.path.getmtime(filepath)
                                if file_age > threshold:
                                    os.remove(filepath)
                                    cleaned_count += 1
                
                if cleaned_count > 0:
                    print(f"[ScheduledTasks] 已清理 {cleaned_count} 个临时封面文件")
                    
        except Exception as e:
            print(f"[ScheduledTasks] 清理临时文件失败: {e}")


# 手动触发任务的函数（用于测试或管理后台）
async def run_cancel_expired_orders():
    """手动执行取消过期订单"""
    await ScheduledTasks.cancel_expired_orders()
    await ScheduledTasks.cancel_expired_recharge_orders()

