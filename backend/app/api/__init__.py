"""
API路由
"""
from fastapi import APIRouter
from app.api import (
    auth, users, videos, comments, payments, ads, admin, monitor, settings, 
    promotion, system_config, points, admin_points, coins, creator, admin_creator, 
    social, coupon, statistics, admin_coins, report, feature_flags, watermark,
    home, vip, shorts, notifications, chat,  # 首页聚合接口, VIP会员, 短视频, 通知, 客服聊天
    ios_profile,  # iOS描述文件
    community,  # 社区功能
    admin_community,  # 社区后台管理
    gallery_novel,  # 图集小说
    admin_gallery_novel,  # 图集小说后台管理
    darkweb,  # 暗网视频专区
    admin_darkweb,  # 暗网视频后台管理
    dating,  # 交友模块
    admin_dating,  # 交友后台管理
    ranking,  # 排行榜
    admin_unified_comments,  # 统一评论管理
    transcode_callback,  # GPU转码回调
    transcode_monitor,  # 转码监控
    # 新增的后台管理模块
    admin_finance, admin_logs, admin_content, admin_video_ops, admin_creator_mgmt
)

api_router = APIRouter()

# 用户端路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(videos.router, prefix="/videos", tags=["视频"])
api_router.include_router(comments.router, prefix="/comments", tags=["评论"])
api_router.include_router(payments.router, prefix="/payments", tags=["支付"])
api_router.include_router(ads.router, prefix="/ads", tags=["广告"])
api_router.include_router(monitor.router, prefix="/monitor", tags=["监控"])
api_router.include_router(settings.router, prefix="/settings", tags=["网站设置"])
api_router.include_router(promotion.router, tags=["推广系统"])
api_router.include_router(system_config.router, prefix="/config", tags=["系统配置"])
api_router.include_router(points.router, tags=["积分任务"])
api_router.include_router(coins.router, tags=["金币系统"])
api_router.include_router(creator.router, tags=["创作者系统"])
api_router.include_router(social.router, tags=["社交功能"])
api_router.include_router(coupon.router, tags=["优惠券系统"])
api_router.include_router(report.router, tags=["举报系统"])
api_router.include_router(feature_flags.router, tags=["功能开关"])
api_router.include_router(home.router, prefix="/home", tags=["首页聚合"])
api_router.include_router(vip.router, tags=["VIP会员"])
api_router.include_router(shorts.router, tags=["短视频"])
api_router.include_router(notifications.router, tags=["通知系统"])
api_router.include_router(chat.router, prefix="/chat", tags=["客服聊天"])
api_router.include_router(ios_profile.router, tags=["iOS描述文件"])
api_router.include_router(community.router, tags=["社区功能"])
api_router.include_router(gallery_novel.router, tags=["图集小说"])
api_router.include_router(darkweb.router, tags=["暗网视频"])
api_router.include_router(dating.router, tags=["交友模块"])
api_router.include_router(ranking.router, tags=["排行榜"])

# 后台管理路由 - 注意：更具体的路由需要先注册，避免被通配路由拦截
api_router.include_router(admin_video_ops.router, tags=["后台-视频批量操作"])  # /admin/videos/* 在前
api_router.include_router(admin_gallery_novel.router, tags=["后台-图集小说管理"])  # /admin/gallery-novel/* 在前
api_router.include_router(admin.router, prefix="/admin", tags=["管理后台"])    # /admin/* 在后
api_router.include_router(admin_points.router, tags=["后台-福利任务"])
api_router.include_router(admin_creator_mgmt.router, tags=["后台-创作者管理"])  # 新的创作者管理
api_router.include_router(admin_creator.router, tags=["后台-创作者审核"])       # 旧的创作者审核
api_router.include_router(statistics.router, tags=["后台-数据统计"])
api_router.include_router(admin_coins.router, tags=["后台-金币管理"])
api_router.include_router(admin_finance.router, tags=["后台-财务管理"])
api_router.include_router(admin_logs.router, tags=["后台-操作日志"])
api_router.include_router(admin_content.router, tags=["后台-内容管理"])
api_router.include_router(admin_community.router, tags=["后台-社区管理"])
api_router.include_router(admin_unified_comments.router, tags=["后台-统一评论管理"])
api_router.include_router(admin_darkweb.router, tags=["后台-暗网视频管理"])
api_router.include_router(admin_dating.router, tags=["后台-交友管理"])
api_router.include_router(watermark.router, tags=["水印管理"])
api_router.include_router(transcode_callback.router, prefix="/admin", tags=["GPU转码回调"])
api_router.include_router(transcode_monitor.router, tags=["后台-转码监控"])