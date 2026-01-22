"""
转码工作线程 - 优化版
支持：并行转码、磁盘监控、任务恢复、预计时间
"""
import os
import shutil
import time
import logging
import threading
from datetime import datetime
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import DIRS, SERVICE, PARALLEL, ensure_dirs, check_disk_space
from task_queue import TaskQueue, TaskStatus, TaskType
from transcoder import Transcoder
from uploader import Uploader
from callback import CallbackClient

logger = logging.getLogger(__name__)


class TranscodeWorker:
    def __init__(self):
        ensure_dirs()
        self.queue = TaskQueue()
        self.uploader = Uploader()
        self.callback = CallbackClient()
        self.running = False
        self.current_tasks = {}
        self.executor = None
        self.lock = threading.Lock()
    
    def scan_downloads(self):
        """扫描下载目录，添加新任务"""
        try:
            for filename in os.listdir(DIRS["downloads_long"]):
                if filename.lower().endswith(".mp4"):
                    filepath = os.path.join(DIRS["downloads_long"], filename)
                    if self._is_file_complete(filepath):
                        self.queue.add_task(filename, filepath, TaskType.LONG)
                        logger.info(f"发现长视频: {filename}")
        except Exception as e:
            logger.error(f"扫描长视频目录失败: {e}")
        
        try:
            for filename in os.listdir(DIRS["downloads_short"]):
                if filename.lower().endswith(".mp4"):
                    filepath = os.path.join(DIRS["downloads_short"], filename)
                    if self._is_file_complete(filepath):
                        self.queue.add_task(filename, filepath, TaskType.SHORT)
                        logger.info(f"发现短视频: {filename}")
        except Exception as e:
            logger.error(f"扫描短视频目录失败: {e}")
    
    def _is_file_complete(self, filepath: str) -> bool:
        try:
            initial_size = os.path.getsize(filepath)
            time.sleep(2)
            current_size = os.path.getsize(filepath)
            return initial_size == current_size and initial_size > 0
        except:
            return False
    
    def process_task(self, task: dict, worker_id: int = 0) -> bool:
        task_id = task["id"]
        filename = task["filename"]
        filepath = task["filepath"]
        task_type = task["task_type"]
        is_short = task_type == TaskType.SHORT.value
        name = os.path.splitext(filename)[0]
        
        if is_short:
            output_dir = os.path.join(DIRS["completed_short"], name)
        else:
            output_dir = os.path.join(DIRS["completed_long"], name)
        
        processing_path = os.path.join(DIRS["processing"], f"{worker_id}_{filename}")
        
        logger.info(f"[W{worker_id}] 开始: {filename}")
        
        try:
            ok, msg = check_disk_space()
            if not ok:
                raise Exception(msg)
            
            if os.path.exists(filepath):
                shutil.move(filepath, processing_path)
            elif not os.path.exists(processing_path):
                raise FileNotFoundError(f"源文件不存在: {filepath}")
            
            os.makedirs(output_dir, exist_ok=True)
            self.queue.update_status(task_id, TaskStatus.PROCESSING, 
                                     output_dir=output_dir, worker_id=worker_id)
            
            with self.lock:
                self.current_tasks[worker_id] = task
            
            def progress_callback(progress):
                self.queue.update_progress(task_id, progress)
            
            transcoder = Transcoder(progress_callback, is_short=is_short)
            duration, height = transcoder.get_video_info(processing_path)
            estimated_time = transcoder.estimate_transcode_time(duration, height)
            
            self.queue.update_status(task_id, TaskStatus.PROCESSING, 
                                     duration=duration, height=height,
                                     estimated_time=estimated_time)
            
            hls_dir = transcoder.generate_hls(processing_path, output_dir, duration, height)
            covers_dir, best_cover = transcoder.generate_covers(processing_path, output_dir, duration)
            
            preview_path = None
            if not is_short:
                preview_path = transcoder.generate_preview(processing_path, output_dir, duration, name)
            
            self.queue.update_status(task_id, TaskStatus.UPLOADING)
            video_id = f"{'short_' if is_short else ''}{datetime.now().strftime('%Y%m%d%H%M%S')}_{worker_id}"
            
            hls_url = self.uploader.upload_hls(hls_dir, video_id)
            self.uploader.upload_covers(covers_dir, video_id)
            cover_url = f"/uploads/hls/{video_id}/covers/cover_{best_cover}.webp"
            
            preview_url = ""
            if preview_path:
                preview_url = self.uploader.upload_preview(preview_path) or ""
            
            result = self.callback.send_completion(
                filename=name, title=name, is_short=is_short,
                duration=duration, hls_url=hls_url or "",
                cover_url=cover_url, preview_url=preview_url
            )
            
            self.queue.add_publish_history(
                task_id=task_id, filename=filename, title=name,
                video_id=result.get("video_id") if result else None,
                is_short=is_short, duration=duration,
                hls_url=hls_url, cover_url=cover_url
            )
            
            if os.path.exists(processing_path):
                os.remove(processing_path)
            
            self.queue.update_status(task_id, TaskStatus.COMPLETED,
                                     hls_url=hls_url, cover_url=cover_url, preview_url=preview_url)
            
            with self.lock:
                self.current_tasks.pop(worker_id, None)
            
            logger.info(f"[W{worker_id}] 完成: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"[W{worker_id}] 失败: {e}", exc_info=True)
            
            if os.path.exists(processing_path):
                try:
                    shutil.move(processing_path, filepath)
                except:
                    pass
            
            retry_count = task.get("retry_count", 0) + 1
            if retry_count < SERVICE["max_retries"]:
                self.queue.update_status(task_id, TaskStatus.PENDING,
                                         error_message=str(e), retry_count=retry_count)
            else:
                self.queue.update_status(task_id, TaskStatus.FAILED,
                                         error_message=str(e), retry_count=retry_count)
            
            with self.lock:
                self.current_tasks.pop(worker_id, None)
            return False
    
    def run_parallel(self):
        max_workers = PARALLEL["max_workers"]
        logger.info(f"并行模式，工作线程: {max_workers}")
        
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        futures = {}
        
        while self.running:
            try:
                self.scan_downloads()
                
                done_futures = [f for f in futures if f.done()]
                for f in done_futures:
                    try:
                        f.result()
                    except Exception as e:
                        logger.error(f"任务异常: {e}")
                    futures.pop(f, None)
                
                active_count = len([f for f in futures if not f.done()])
                available_slots = max_workers - active_count
                
                if available_slots > 0:
                    tasks = self.queue.get_pending_tasks(available_slots)
                    for i, task in enumerate(tasks):
                        worker_id = active_count + i + 1
                        future = self.executor.submit(self.process_task, task, worker_id)
                        futures[future] = task["id"]
                
                time.sleep(1 if futures else SERVICE["check_interval"])
                    
            except Exception as e:
                logger.error(f"循环错误: {e}", exc_info=True)
                time.sleep(30)
        
        self.executor.shutdown(wait=True)
    
    def run(self):
        self.running = True
        logger.info("转码工作线程启动")
        self.queue.reset_stuck_tasks()
        
        if PARALLEL["enabled"] and PARALLEL["max_workers"] > 1:
            self.run_parallel()
        else:
            self.run_single()
    
    def run_single(self):
        while self.running:
            try:
                self.scan_downloads()
                task = self.queue.get_pending_task()
                if task:
                    self.process_task(task, worker_id=1)
                else:
                    time.sleep(SERVICE["check_interval"])
            except Exception as e:
                logger.error(f"循环错误: {e}", exc_info=True)
                time.sleep(30)
    
    def stop(self):
        self.running = False
        if self.executor:
            self.executor.shutdown(wait=False)
        logger.info("转码工作线程停止")
    
    def get_status(self) -> dict:
        with self.lock:
            return {
                "running": self.running,
                "active_tasks": len(self.current_tasks),
                "current_tasks": list(self.current_tasks.values()),
                "stats": self.queue.get_stats()
            }
