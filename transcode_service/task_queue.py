"""
SQLite任务队列 - 优化版
支持：并行任务、定时发布、任务排序、历史记录
"""
import sqlite3
import json
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from config import DATABASE_PATH, ensure_dirs


class TaskStatus(Enum):
    PENDING = "pending"
    QUEUED = "queued"        # 排队中
    PROCESSING = "processing"
    UPLOADING = "uploading"
    READY = "ready"          # 转码完成，待发布
    SCHEDULED = "scheduled"  # 定时发布
    COMPLETED = "completed"
    FAILED = "failed"


class TaskType(Enum):
    LONG = "long"
    SHORT = "short"


class TaskQueue:
    def __init__(self, db_path: str = DATABASE_PATH):
        ensure_dirs()
        self.db_path = db_path
        self._init_db()
    
    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def _init_db(self):
        with self._get_conn() as conn:
            # 检查表是否存在
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                conn.execute("""
                    CREATE TABLE tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT NOT NULL,
                        filepath TEXT NOT NULL,
                        task_type TEXT NOT NULL,
                        status TEXT DEFAULT 'pending',
                        progress REAL DEFAULT 0,
                        duration REAL DEFAULT 0,
                        height INTEGER DEFAULT 0,
                        output_dir TEXT,
                        hls_url TEXT,
                        cover_url TEXT,
                        preview_url TEXT,
                        error_message TEXT,
                        retry_count INTEGER DEFAULT 0,
                        priority INTEGER DEFAULT 0,
                        sort_order INTEGER DEFAULT 0,
                        scheduled_at TIMESTAMP,
                        estimated_time REAL DEFAULT 0,
                        worker_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        metadata TEXT
                    )
                """)
            else:
                # 添加新列（如果不存在）
                try:
                    conn.execute("ALTER TABLE tasks ADD COLUMN priority INTEGER DEFAULT 0")
                except: pass
                try:
                    conn.execute("ALTER TABLE tasks ADD COLUMN sort_order INTEGER DEFAULT 0")
                except: pass
                try:
                    conn.execute("ALTER TABLE tasks ADD COLUMN scheduled_at TIMESTAMP")
                except: pass
                try:
                    conn.execute("ALTER TABLE tasks ADD COLUMN estimated_time REAL DEFAULT 0")
                except: pass
                try:
                    conn.execute("ALTER TABLE tasks ADD COLUMN worker_id INTEGER")
                except: pass
            
            # 发布历史表
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='publish_history'")
            if not cursor.fetchone():
                conn.execute("""
                    CREATE TABLE publish_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id INTEGER,
                        filename TEXT,
                        title TEXT,
                        video_id INTEGER,
                        is_short INTEGER,
                        duration REAL,
                        hls_url TEXT,
                        cover_url TEXT,
                        published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT
                    )
                """)
            
            # 索引（忽略错误）
            try:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON tasks(status)")
            except: pass
            try:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_created ON tasks(created_at)")
            except: pass
    
    def add_task(self, filename: str, filepath: str, task_type: TaskType, 
                 priority: int = 0) -> int:
        """添加新任务"""
        with self._get_conn() as conn:
            # 检查是否已存在
            existing = conn.execute(
                "SELECT id FROM tasks WHERE filepath = ? AND status NOT IN ('completed', 'failed')",
                (filepath,)
            ).fetchone()
            
            if existing:
                return existing["id"]
            
            # 获取最大排序号
            max_order = conn.execute(
                "SELECT MAX(sort_order) FROM tasks WHERE status = 'pending'"
            ).fetchone()[0] or 0
            
            cursor = conn.execute(
                """INSERT INTO tasks (filename, filepath, task_type, status, priority, sort_order)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (filename, filepath, task_type.value, TaskStatus.PENDING.value, priority, max_order + 1)
            )
            return cursor.lastrowid
    
    def get_pending_task(self, worker_id: int = 0) -> Optional[Dict[str, Any]]:
        """获取一个待处理任务（支持并行）"""
        with self._get_conn() as conn:
            # 先检查定时任务
            scheduled = conn.execute(
                """SELECT * FROM tasks 
                   WHERE status = ? AND scheduled_at <= datetime('now')
                   ORDER BY scheduled_at ASC LIMIT 1""",
                (TaskStatus.SCHEDULED.value,)
            ).fetchone()
            
            if scheduled:
                conn.execute(
                    "UPDATE tasks SET status = ?, worker_id = ? WHERE id = ?",
                    (TaskStatus.PENDING.value, worker_id, scheduled["id"])
                )
                return dict(scheduled)
            
            # 获取普通待处理任务
            row = conn.execute(
                """SELECT * FROM tasks 
                   WHERE status = ? AND (worker_id IS NULL OR worker_id = 0)
                   ORDER BY priority DESC, sort_order ASC LIMIT 1""",
                (TaskStatus.PENDING.value,)
            ).fetchone()
            
            if row:
                # 标记worker
                conn.execute(
                    "UPDATE tasks SET worker_id = ? WHERE id = ?",
                    (worker_id, row["id"])
                )
                return dict(row)
            return None
    
    def get_pending_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取多个待处理任务（用于并行）"""
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT * FROM tasks 
                   WHERE status = ? AND (worker_id IS NULL OR worker_id = 0)
                   ORDER BY priority DESC, sort_order ASC LIMIT ?""",
                (TaskStatus.PENDING.value, limit)
            ).fetchall()
            return [dict(row) for row in rows]
    
    def update_status(self, task_id: int, status: TaskStatus, **kwargs):
        """更新任务状态"""
        with self._get_conn() as conn:
            updates = ["status = ?"]
            values = [status.value]
            
            if status == TaskStatus.PROCESSING:
                updates.append("started_at = ?")
                values.append(datetime.now().isoformat())
            elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                updates.append("completed_at = ?")
                values.append(datetime.now().isoformat())
                updates.append("worker_id = NULL")
            
            for key, value in kwargs.items():
                if key in ("progress", "duration", "height", "output_dir", 
                          "hls_url", "cover_url", "preview_url", "error_message", 
                          "retry_count", "estimated_time", "worker_id"):
                    updates.append(f"{key} = ?")
                    values.append(value)
            
            values.append(task_id)
            conn.execute(
                f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?",
                values
            )
    
    def update_progress(self, task_id: int, progress: float):
        """更新转码进度"""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE tasks SET progress = ? WHERE id = ?",
                (progress, task_id)
            )
    
    def update_sort_order(self, task_ids: List[int]):
        """更新任务排序（拖拽排序）"""
        with self._get_conn() as conn:
            for i, task_id in enumerate(task_ids):
                conn.execute(
                    "UPDATE tasks SET sort_order = ? WHERE id = ?",
                    (i, task_id)
                )
    
    def schedule_task(self, task_id: int, scheduled_at: datetime):
        """设置定时发布"""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE tasks SET status = ?, scheduled_at = ? WHERE id = ?",
                (TaskStatus.SCHEDULED.value, scheduled_at.isoformat(), task_id)
            )
    
    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """获取任务详情"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
            return dict(row) if row else None
    
    def get_processing_tasks(self) -> List[Dict[str, Any]]:
        """获取所有正在处理的任务"""
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT * FROM tasks 
                   WHERE status IN (?, ?) 
                   ORDER BY started_at DESC""",
                (TaskStatus.PROCESSING.value, TaskStatus.UPLOADING.value)
            ).fetchall()
            return [dict(row) for row in rows]
    
    def reset_stuck_tasks(self):
        """重置卡住的任务（服务重启时调用）"""
        with self._get_conn() as conn:
            conn.execute(
                """UPDATE tasks SET status = ?, retry_count = retry_count + 1, worker_id = NULL
                   WHERE status IN (?, ?)""",
                (TaskStatus.PENDING.value, 
                 TaskStatus.PROCESSING.value, 
                 TaskStatus.UPLOADING.value)
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._get_conn() as conn:
            stats = {}
            for status in TaskStatus:
                count = conn.execute(
                    "SELECT COUNT(*) FROM tasks WHERE status = ?",
                    (status.value,)
                ).fetchone()[0]
                stats[status.value] = count
            
            stats["total"] = conn.execute(
                "SELECT COUNT(*) FROM tasks"
            ).fetchone()[0]
            
            # 预计完成时间
            pending_duration = conn.execute(
                "SELECT SUM(estimated_time) FROM tasks WHERE status IN ('pending', 'queued')"
            ).fetchone()[0] or 0
            stats["estimated_minutes"] = round(pending_duration / 60, 1)
            
            return stats
    
    def get_recent_tasks(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取最近的任务"""
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT * FROM tasks 
                   ORDER BY created_at DESC LIMIT ?""",
                (limit,)
            ).fetchall()
            return [dict(row) for row in rows]
    
    def get_queue_with_eta(self) -> List[Dict[str, Any]]:
        """获取队列及预计完成时间"""
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT * FROM tasks 
                   WHERE status IN ('pending', 'queued', 'processing')
                   ORDER BY 
                       CASE status 
                           WHEN 'processing' THEN 0 
                           WHEN 'queued' THEN 1 
                           ELSE 2 
                       END,
                       priority DESC, sort_order ASC"""
            ).fetchall()
            
            tasks = []
            cumulative_time = 0
            
            for row in rows:
                task = dict(row)
                if task["status"] == "processing":
                    # 正在处理的任务，计算剩余时间
                    remaining = task["estimated_time"] * (1 - task["progress"] / 100)
                    task["eta_seconds"] = remaining
                else:
                    cumulative_time += task["estimated_time"]
                    task["eta_seconds"] = cumulative_time
                tasks.append(task)
            
            return tasks
    
    # ============ 发布历史 ============
    
    def add_publish_history(self, task_id: int, filename: str, title: str,
                           video_id: int, is_short: bool, duration: float,
                           hls_url: str, cover_url: str, metadata: dict = None, is_darkweb: bool = False):
        """添加发布历史"""
        meta = metadata or {}
        meta['is_darkweb'] = is_darkweb
        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO publish_history 
                   (task_id, filename, title, video_id, is_short, duration, hls_url, cover_url, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (task_id, filename, title, video_id, 1 if is_short else 0, 
                 duration, hls_url, cover_url, json.dumps(meta))
            )
    
    def get_publish_history(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """获取发布历史"""
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT * FROM publish_history 
                   ORDER BY published_at DESC LIMIT ? OFFSET ?""",
                (limit, offset)
            ).fetchall()
            return [dict(row) for row in rows]
    
    def get_history_stats(self) -> Dict[str, Any]:
        """获取历史统计"""
        with self._get_conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM publish_history").fetchone()[0]
            today = conn.execute(
                "SELECT COUNT(*) FROM publish_history WHERE date(published_at) = date('now')"
            ).fetchone()[0]
            this_week = conn.execute(
                "SELECT COUNT(*) FROM publish_history WHERE published_at >= datetime('now', '-7 days')"
            ).fetchone()[0]
            
            return {
                "total": total,
                "today": today,
                "this_week": this_week
            }
    
    def cleanup_old_tasks(self, days: int = 30):
        """清理旧任务记录"""
        with self._get_conn() as conn:
            conn.execute(
                """DELETE FROM tasks 
                   WHERE status = ? 
                   AND completed_at < datetime('now', ?)""",
                (TaskStatus.COMPLETED.value, f"-{days} days")
            )
