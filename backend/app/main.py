"""
FastAPI 主应用入口
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal
from app.core.redis import close_redis
from app.api import api_router
# 确保所有模型在init_db前被导入，以便创建对应的表
import app.models


async def init_default_tasks():
    """初始化默认任务配置（只添加缺失的任务）"""
    from app.models.points import Task
    from sqlalchemy import select
    
    # 默认任务配置
    default_tasks_config = [
        {
            "task_type": "checkin",
            "task_name": "签到任务",
            "task_desc": "每日签到 +5积分",
            "points_reward": 5,
            "daily_limit": 1,
            "icon": "○",
            "icon_bg": "linear-gradient(360deg, #9e52cf, #4d45bf)",
            "action_type": "claim",
            "sort_order": 1,
            "is_active": True
        },
        {
            "task_type": "post",
            "task_name": "每日发帖",
            "task_desc": "发布帖子 +5积分",
            "points_reward": 5,
            "daily_limit": 1,
            "icon": "📷",
            "icon_bg": "linear-gradient(360deg, #9e52cf, #4d45bf)",
            "action_type": "redirect",
            "action_url": "/user/post",
            "sort_order": 2,
            "is_active": True
        },
        {
            "task_type": "comment_post",
            "task_name": "帖子评论",
            "task_desc": "帖子评论十个字以上 获得5积分",
            "points_reward": 5,
            "daily_limit": 5,
            "icon": "✏️",
            "icon_bg": "linear-gradient(135deg, #22c55e, #10b981)",
            "action_type": "redirect",
            "sort_order": 3,
            "is_active": True
        },
        {
            "task_type": "comment_video",
            "task_name": "视频评论",
            "task_desc": "视频评论十个字以上 获得5积分",
            "points_reward": 5,
            "daily_limit": 5,
            "icon": "✏️",
            "icon_bg": "linear-gradient(135deg, #22c55e, #10b981)",
            "action_type": "redirect",
            "sort_order": 4,
            "is_active": True
        },
        {
            "task_type": "invite",
            "task_name": "每日邀请",
            "task_desc": "每日邀请用户+20积分",
            "points_reward": 20,
            "daily_limit": 10,
            "icon": "👥",
            "icon_bg": "linear-gradient(360deg, #9e52cf, #4d45bf)",
            "action_type": "redirect",
            "action_url": "/user/promotion",
            "sort_order": 5,
            "is_active": True
        },
        {
            "task_type": "buy_vip",
            "task_name": "购买VIP+100积分",
            "task_desc": "购买任意VIP 即可获得100积分",
            "points_reward": 100,
            "daily_limit": 0,
            "icon": "💎",
            "icon_bg": "linear-gradient(360deg, #9e52cf, #4d45bf)",
            "action_type": "redirect",
            "action_url": "/user/vip",
            "sort_order": 6,
            "is_active": True
        },
        {
            "task_type": "download",
            "task_name": "下载APP",
            "task_desc": "下载好色，即可获得20积分",
            "points_reward": 20,
            "daily_limit": 1,
            "icon": "⬇️",
            "icon_bg": "linear-gradient(360deg, #9e52cf, #4d45bf)",
            "action_type": "claim",
            "sort_order": 7,
            "is_active": True
        },
    ]
    
    async with AsyncSessionLocal() as db:
        added_count = 0
        
        for task_config in default_tasks_config:
            # 检查任务是否已存在
            result = await db.execute(
                select(Task).where(Task.task_type == task_config["task_type"])
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                # 任务不存在，添加
                task = Task(**task_config)
                db.add(task)
                added_count += 1
                print(f"  [+] Adding task: {task_config['task_name']}")
            else:
                # 任务存在，确保已激活
                if not existing.is_active:
                    existing.is_active = True
                    added_count += 1
                    print(f"  [*] Activating task: {task_config['task_name']}")
        
        if added_count > 0:
            await db.commit()
            print(f"[OK] Added {added_count} new tasks")
        else:
            print("[OK] All tasks already exist")


async def init_default_exchange_items():
    """初始化默认兑换商品"""
    from app.models.points import ExchangeItem
    from sqlalchemy import select, text, inspect
    
    # 先尝试添加 item_desc 列（如果不存在）- SQLite 兼容方式
    async with AsyncSessionLocal() as db:
        try:
            # 检查列是否存在
            result = await db.execute(text("PRAGMA table_info(exchange_items)"))
            columns = [row[1] for row in result.fetchall()]
            if 'item_desc' not in columns:
                await db.execute(text(
                    "ALTER TABLE exchange_items ADD COLUMN item_desc VARCHAR(255)"
                ))
                await db.commit()
        except Exception as e:
            await db.rollback()
            print(f"[!] Note: Could not add item_desc column: {e}")
    
    # 默认兑换商品列表
    default_items = [
        {
            "item_name": "VIP体验卡1天",
            "item_desc": "畅游全站VIP资源",
            "item_type": "vip_days",
            "item_value": 1,
            "points_cost": 100,
            "stock": -1,
            "daily_limit": 1,
            "is_active": True,
            "sort_order": 1
        },
        {
            "item_name": "情趣盲盒",
            "item_desc": "兑换后联系客服领取!",
            "item_type": "gift",
            "item_value": 1,
            "points_cost": 3000,
            "stock": -1,
            "daily_limit": 1,
            "is_active": True,
            "sort_order": 2
        },
        {
            "item_name": "VIP体验卡7天",
            "item_desc": "畅游全站VIP资源",
            "item_type": "vip_days",
            "item_value": 7,
            "points_cost": 200,
            "stock": -1,
            "daily_limit": 1,
            "is_active": True,
            "sort_order": 3
        },
        {
            "item_name": "Ai科技券",
            "item_desc": "AI脱衣/换脸（图片）10次!",
            "item_type": "coupon",
            "item_value": 10,
            "points_cost": 1000,
            "stock": -1,
            "daily_limit": 1,
            "is_active": True,
            "sort_order": 4
        },
        {
            "item_name": "Ai科技券",
            "item_desc": "AI脱衣/换脸（图片）5次!",
            "item_type": "coupon",
            "item_value": 5,
            "points_cost": 500,
            "stock": -1,
            "daily_limit": 1,
            "is_active": True,
            "sort_order": 5
        },
        {
            "item_name": "VIP体验卡30天",
            "item_desc": "畅游全站VIP资源",
            "item_type": "vip_days",
            "item_value": 30,
            "points_cost": 600,
            "stock": -1,
            "daily_limit": 1,
            "is_active": True,
            "sort_order": 6
        },
    ]
    
    async with AsyncSessionLocal() as db:
        added_count = 0
        
        for item_config in default_items:
            # 检查商品是否已存在（按名称和积分）
            result = await db.execute(
                select(ExchangeItem.id, ExchangeItem.item_name, ExchangeItem.is_active).where(
                    ExchangeItem.item_name == item_config["item_name"],
                    ExchangeItem.points_cost == item_config["points_cost"]
                )
            )
            existing = result.first()
            
            if not existing:
                item = ExchangeItem(**item_config)
                db.add(item)
                added_count += 1
                print(f"  [+] Adding exchange item: {item_config['item_name']}")
        
        if added_count > 0:
            await db.commit()
            print(f"[OK] Added {added_count} new exchange items")
        else:
            print("[OK] All exchange items already exist")


async def init_default_gifts():
    """初始化默认礼物"""
    from app.models.creator import Gift
    from sqlalchemy import select
    
    default_gifts = [
        {"name": "小心心", "icon": "❤️", "coins_price": 1, "sort_order": 1},
        {"name": "棒棒糖", "icon": "🍭", "coins_price": 5, "sort_order": 2},
        {"name": "玫瑰花", "icon": "🌹", "coins_price": 10, "sort_order": 3},
        {"name": "啤酒", "icon": "🍺", "coins_price": 20, "sort_order": 4},
        {"name": "蛋糕", "icon": "🎂", "coins_price": 50, "sort_order": 5},
        {"name": "钻戒", "icon": "💍", "coins_price": 100, "sort_order": 6},
        {"name": "皇冠", "icon": "👑", "coins_price": 200, "sort_order": 7},
        {"name": "火箭", "icon": "🚀", "coins_price": 500, "sort_order": 8},
        {"name": "城堡", "icon": "🏰", "coins_price": 1000, "sort_order": 9},
        {"name": "嘉年华", "icon": "🎪", "coins_price": 5000, "sort_order": 10},
    ]
    
    async with AsyncSessionLocal() as db:
        added_count = 0
        
        for gift_config in default_gifts:
            result = await db.execute(
                select(Gift.id).where(Gift.name == gift_config["name"])
            )
            if not result.first():
                gift = Gift(**gift_config, is_active=True)
                db.add(gift)
                added_count += 1
        
        if added_count > 0:
            await db.commit()
            print(f"[OK] Added {added_count} new gifts")
        else:
            print("[OK] All gifts already exist")


async def init_default_recharge_packages():
    """初始化默认充值套餐"""
    from app.models.coins import RechargePackage
    from sqlalchemy import select
    from decimal import Decimal
    
    default_packages = [
        {
            "name": "体验包",
            "coins": 60,
            "bonus_coins": 0,
            "price": Decimal("6.00"),
            "tag": "体验",
            "sort_order": 1,
            "is_active": True
        },
        {
            "name": "小额充值",
            "coins": 120,
            "bonus_coins": 10,
            "price": Decimal("12.00"),
            "sort_order": 2,
            "is_active": True
        },
        {
            "name": "超值套餐",
            "coins": 300,
            "bonus_coins": 50,
            "price": Decimal("30.00"),
            "tag": "热门",
            "is_hot": True,
            "sort_order": 3,
            "is_active": True
        },
        {
            "name": "畅享套餐",
            "coins": 680,
            "bonus_coins": 150,
            "price": Decimal("68.00"),
            "tag": "推荐",
            "sort_order": 4,
            "is_active": True
        },
        {
            "name": "至尊套餐",
            "coins": 1280,
            "bonus_coins": 400,
            "price": Decimal("128.00"),
            "tag": "超值",
            "sort_order": 5,
            "is_active": True
        },
        {
            "name": "首充礼包",
            "coins": 100,
            "bonus_coins": 100,
            "price": Decimal("6.00"),
            "original_price": Decimal("10.00"),
            "tag": "首充2倍",
            "is_first_charge": True,
            "sort_order": 0,
            "is_active": True
        },
    ]
    
    async with AsyncSessionLocal() as db:
        added_count = 0
        
        for pkg_config in default_packages:
            # 检查是否已存在
            result = await db.execute(
                select(RechargePackage.id).where(
                    RechargePackage.name == pkg_config["name"],
                    RechargePackage.coins == pkg_config["coins"]
                )
            )
            existing = result.first()
            
            if not existing:
                package = RechargePackage(**pkg_config)
                db.add(package)
                added_count += 1
                print(f"  [+] Adding recharge package: {pkg_config['name']}")
        
        if added_count > 0:
            await db.commit()
            print(f"[OK] Added {added_count} new recharge packages")
        else:
            print("[OK] All recharge packages already exist")


async def init_default_official_groups():
    """初始化默认官方群组"""
    from app.models.ad import OfficialGroup, OfficialGroupType
    from sqlalchemy import select
    
    default_groups = [
        {
            "name": "官方土豆群",
            "group_type": OfficialGroupType.COMMUNITY,
            "icon_type": "rocket",
            "icon_bg": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            "url": "https://t.me/example1",
            "sort_order": 1
        },
        {
            "name": "官方飞机群",
            "group_type": OfficialGroupType.COMMUNITY,
            "icon_type": "telegram",
            "icon_bg": "linear-gradient(135deg, #00b4db 0%, #0083b0 100%)",
            "url": "https://t.me/example2",
            "sort_order": 2
        },
        {
            "name": "官方商务",
            "group_type": OfficialGroupType.BUSINESS,
            "icon_type": "briefcase",
            "icon_bg": "linear-gradient(135deg, #00b4db 0%, #0083b0 100%)",
            "url": "https://t.me/business1",
            "sort_order": 1
        },
        {
            "name": "渠道合作",
            "group_type": OfficialGroupType.BUSINESS,
            "icon_type": "heart",
            "icon_bg": "linear-gradient(135deg, #00b4db 0%, #0083b0 100%)",
            "url": "https://t.me/business2",
            "sort_order": 2
        }
    ]
    
    async with AsyncSessionLocal() as db:
        added_count = 0
        
        for group_config in default_groups:
            result = await db.execute(
                select(OfficialGroup.id).where(OfficialGroup.name == group_config["name"])
            )
            if not result.first():
                group = OfficialGroup(**group_config, is_active=True)
                db.add(group)
                added_count += 1
        
        if added_count > 0:
            await db.commit()
            print(f"[OK] Added {added_count} new official groups")
        else:
            print("[OK] All official groups already exist")


async def ensure_video_columns():
    """确保videos表有新增的付费相关字段"""
    from sqlalchemy import text
    
    columns_to_add = [
        ("pay_type", "VARCHAR(20) DEFAULT 'free'"),
        ("coin_price", "INTEGER DEFAULT 0"),
        ("vip_free_level", "INTEGER DEFAULT 0"),
        ("vip_discount", "FLOAT DEFAULT 1.0"),
        ("free_preview_seconds", "INTEGER DEFAULT 30"),
        ("creator_id", "INTEGER"),
        ("revenue_share_ratio", "FLOAT DEFAULT 0.7"),
    ]
    
    async with AsyncSessionLocal() as db:
        try:
            # 获取现有列 - SQLite 兼容方式
            result = await db.execute(text("PRAGMA table_info(videos)"))
            existing_columns = [row[1] for row in result.fetchall()]
            
            for col_name, col_def in columns_to_add:
                if col_name not in existing_columns:
                    try:
                        await db.execute(text(f"ALTER TABLE videos ADD COLUMN {col_name} {col_def}"))
                        await db.commit()
                    except Exception as e:
                        await db.rollback()
                        pass
        except Exception as e:
            pass
        print("[OK] Video columns checked")


async def ensure_customer_service_columns():
    """确保customer_services表有所需字段"""
    from sqlalchemy import text
    
    columns_to_add = [
        ("icon_type", "VARCHAR(50) DEFAULT 'headset'"),
        ("icon_bg", "VARCHAR(50) DEFAULT '#667eea'"),
        ("icon_image", "VARCHAR(500)"),
        ("work_time", "VARCHAR(100)"),
        ("click_count", "INTEGER DEFAULT 0"),
    ]
    
    async with AsyncSessionLocal() as db:
        try:
            # 尝试获取现有列 - 支持 PostgreSQL 和 SQLite
            try:
                # PostgreSQL
                result = await db.execute(text("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'customer_services'
                """))
                existing_columns = [row[0] for row in result.fetchall()]
            except Exception:
                # SQLite
                result = await db.execute(text("PRAGMA table_info(customer_services)"))
                existing_columns = [row[1] for row in result.fetchall()]
            
            for col_name, col_def in columns_to_add:
                if col_name not in existing_columns:
                    try:
                        await db.execute(text(f"ALTER TABLE customer_services ADD COLUMN {col_name} {col_def}"))
                        await db.commit()
                        print(f"[+] Added column {col_name} to customer_services")
                    except Exception as e:
                        await db.rollback()
                        pass
        except Exception as e:
            print(f"[!] Customer service columns check error: {e}")
            pass
        print("[OK] Customer service columns checked")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("[*] Starting VOD Platform...")
    await init_db()
    print("[OK] Database initialized")
    await ensure_video_columns()
    await ensure_customer_service_columns()
    await init_default_tasks()
    await init_default_exchange_items()
    await init_default_recharge_packages()
    await init_default_gifts()
    await init_default_official_groups()
    
    # 启动定时任务
    from app.services.scheduled_tasks import ScheduledTasks
    await ScheduledTasks.start()
    
    yield
    
    # 关闭时
    print("[*] Shutting down...")
    # 停止定时任务
    from app.services.scheduled_tasks import ScheduledTasks
    await ScheduledTasks.stop()
    await close_redis()
    print("[OK] Service closed")


# 创建应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="VOD视频点播平台 - 全栈分布式系统",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip 压缩中间件 - 压缩大于 500 字节的响应
app.add_middleware(GZipMiddleware, minimum_size=500)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    if settings.DEBUG:
        print(f"[>] {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    response.headers["X-Process-Time"] = str(process_time)
    return response


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    print(f"[ERROR] Unhandled exception: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器内部错误: {str(exc)}"}
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
        "status": "running",
        "docs": "/api/docs"
    }


@app.get("/api/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )







