"""
FastAPI 主应用入口 - 优化版
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging

from app.core.config import settings
from app.core.database import init_db
from app.core.redis import close_redis
from app.core.rate_limiter import RateLimitMiddleware
from app.api import api_router
# 确保所有模型在init_db前被导入
import app.models

# 配置日志
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理 - 精简版"""
    logger.info("Starting VOD Platform...")
    
    # 初始化数据库连接
    await init_db()
    logger.info("Database initialized")
    
    # 启动定时任务
    from app.services.scheduled_tasks import ScheduledTasks
    await ScheduledTasks.start()
    logger.info("Scheduled tasks started")
    
    yield
    
    # 关闭时
    logger.info("Shutting down...")
    from app.services.scheduled_tasks import ScheduledTasks
    await ScheduledTasks.stop()
    await close_redis()
    logger.info("Service closed")


# 创建应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="VOD视频点播平台",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# CORS配置 - 根据环境动态设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time", "X-Request-ID"],
)

# GZip 压缩中间件
app.add_middleware(GZipMiddleware, minimum_size=500)

# API 限流中间件
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(RateLimitMiddleware)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import uuid
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    # 只在调试模式记录详细日志
    if settings.DEBUG:
        logger.debug(f"[{request_id}] {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    response.headers["X-Process-Time"] = f"{process_time:.3f}"
    response.headers["X-Request-ID"] = request_id
    return response


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # 生产环境不暴露详细错误
    if settings.is_production:
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "服务器内部错误，请稍后重试"}
        )
    else:
        import traceback
        logger.error(f"Unhandled exception: {exc}")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)}
        )


# 挂载静态文件
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# 注册API路由
app.include_router(api_router, prefix="/api/v1")


# 根路由
@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/api/health")
async def health():
    """健康检查端点"""
    return {"status": "healthy", "version": settings.APP_VERSION}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
