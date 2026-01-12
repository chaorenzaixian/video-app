"""
性能监控服务
提供应用性能指标收集和监控功能
"""
import time
import logging
import psutil
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RequestMetrics:
    """请求指标"""
    total_requests: int = 0
    total_errors: int = 0
    total_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    status_codes: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    
    @property
    def avg_response_time(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_response_time / self.total_requests
    
    @property
    def error_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_errors / self.total_requests * 100


class PerformanceMonitor:
    """性能监控器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.start_time = datetime.utcnow()
        self.endpoint_metrics: Dict[str, RequestMetrics] = defaultdict(RequestMetrics)
        self.slow_requests: list = []
        self.slow_threshold = 1.0  # 慢请求阈值（秒）
        self.max_slow_requests = 100  # 最多保留的慢请求记录
    
    def record_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float,
        error: Optional[str] = None
    ) -> None:
        """
        记录请求指标
        
        Args:
            endpoint: API端点
            method: HTTP方法
            status_code: 响应状态码
            response_time: 响应时间（秒）
            error: 错误信息
        """
        key = f"{method}:{endpoint}"
        metrics = self.endpoint_metrics[key]
        
        metrics.total_requests += 1
        metrics.total_response_time += response_time
        metrics.status_codes[status_code] += 1
        
        if response_time < metrics.min_response_time:
            metrics.min_response_time = response_time
        if response_time > metrics.max_response_time:
            metrics.max_response_time = response_time
        
        if status_code >= 400:
            metrics.total_errors += 1
        
        # 记录慢请求
        if response_time > self.slow_threshold:
            self._record_slow_request(endpoint, method, response_time, error)
    
    def _record_slow_request(
        self,
        endpoint: str,
        method: str,
        response_time: float,
        error: Optional[str]
    ) -> None:
        """记录慢请求"""
        self.slow_requests.append({
            "endpoint": endpoint,
            "method": method,
            "response_time": response_time,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # 保持列表大小
        if len(self.slow_requests) > self.max_slow_requests:
            self.slow_requests = self.slow_requests[-self.max_slow_requests:]
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "total_gb": round(memory.total / 1024 / 1024 / 1024, 2),
                    "used_gb": round(memory.used / 1024 / 1024 / 1024, 2),
                    "percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
                    "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
                    "percent": round(disk.percent, 1)
                }
            }
        except Exception as e:
            logger.error(f"获取系统指标失败: {e}")
            return {}
    
    def get_application_metrics(self) -> Dict[str, Any]:
        """获取应用指标"""
        uptime = datetime.utcnow() - self.start_time
        
        total_requests = sum(m.total_requests for m in self.endpoint_metrics.values())
        total_errors = sum(m.total_errors for m in self.endpoint_metrics.values())
        
        return {
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_human": str(uptime).split('.')[0],
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": round(total_errors / total_requests * 100, 2) if total_requests > 0 else 0,
            "endpoints_count": len(self.endpoint_metrics)
        }
    
    def get_endpoint_metrics(self, top_n: int = 10) -> list:
        """获取端点指标（按请求数排序）"""
        sorted_endpoints = sorted(
            self.endpoint_metrics.items(),
            key=lambda x: x[1].total_requests,
            reverse=True
        )[:top_n]
        
        return [
            {
                "endpoint": endpoint,
                "total_requests": metrics.total_requests,
                "avg_response_time_ms": round(metrics.avg_response_time * 1000, 2),
                "min_response_time_ms": round(metrics.min_response_time * 1000, 2) if metrics.min_response_time != float('inf') else 0,
                "max_response_time_ms": round(metrics.max_response_time * 1000, 2),
                "error_rate": round(metrics.error_rate, 2)
            }
            for endpoint, metrics in sorted_endpoints
        ]
    
    def get_slow_requests(self, limit: int = 20) -> list:
        """获取慢请求列表"""
        return self.slow_requests[-limit:]
    
    def get_full_report(self) -> Dict[str, Any]:
        """获取完整监控报告"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system": self.get_system_metrics(),
            "application": self.get_application_metrics(),
            "top_endpoints": self.get_endpoint_metrics(),
            "slow_requests": self.get_slow_requests()
        }
    
    def reset_metrics(self) -> None:
        """重置所有指标"""
        self.endpoint_metrics.clear()
        self.slow_requests.clear()
        self.start_time = datetime.utcnow()


# 全局监控器实例
monitor = PerformanceMonitor()


def track_performance(endpoint_name: str = None):
    """
    性能追踪装饰器
    
    用法:
    @track_performance("get_videos")
    async def get_videos():
        ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            error = None
            status_code = 200
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error = str(e)
                status_code = 500
                raise
            finally:
                response_time = time.time() - start_time
                name = endpoint_name or func.__name__
                monitor.record_request(
                    endpoint=name,
                    method="FUNC",
                    status_code=status_code,
                    response_time=response_time,
                    error=error
                )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            error = None
            status_code = 200
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = str(e)
                status_code = 500
                raise
            finally:
                response_time = time.time() - start_time
                name = endpoint_name or func.__name__
                monitor.record_request(
                    endpoint=name,
                    method="FUNC",
                    status_code=status_code,
                    response_time=response_time,
                    error=error
                )
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class MonitoringMiddleware:
    """
    FastAPI 监控中间件
    
    用法:
    from app.services.monitoring_service import MonitoringMiddleware
    app.add_middleware(MonitoringMiddleware)
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        status_code = 500
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            response_time = time.time() - start_time
            path = scope.get("path", "unknown")
            method = scope.get("method", "unknown")
            
            # 排除健康检查等端点
            if not path.startswith("/api/health"):
                monitor.record_request(
                    endpoint=path,
                    method=method,
                    status_code=status_code,
                    response_time=response_time
                )
