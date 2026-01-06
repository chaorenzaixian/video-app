"""
VIP权益统一配置中心 - 兼容层
所有配置已合并到 vip_config.py，此文件保留向后兼容的导入
"""

# 从统一配置中心导入所有内容
from app.core.vip_config import (
    VIPLevel,
    VIPBenefits,
    get_vip_benefits,
    get_vip_discount,
    get_vip_level_name as get_vip_name,
    get_vip_level_icon as get_vip_icon,
    can_watch_free,
    calculate_discounted_price,
    can_download,
    get_daily_download_limit,
    get_all_vip_levels,
    is_ad_free,
    has_priority_support,
    has_exclusive_content,
)

# 保留原有的别名以保持向后兼容
__all__ = [
    'VIPLevel',
    'VIPBenefits',
    'get_vip_benefits',
    'get_vip_discount',
    'get_vip_name',
    'get_vip_icon',
    'can_watch_free',
    'calculate_discounted_price',
    'can_download',
    'get_daily_download_limit',
    'get_all_vip_levels',
    'is_ad_free',
    'has_priority_support',
    'has_exclusive_content',
]
