"""
业务服务层
"""
from app.services.video_access import (
    VideoAccessResult,
    check_video_access,
    check_video_access_by_id,
    get_user_vip_level,
    get_user_coins,
    check_video_purchased,
)

__all__ = [
    'VideoAccessResult',
    'check_video_access',
    'check_video_access_by_id',
    'get_user_vip_level',
    'get_user_coins',
    'check_video_purchased',
]








