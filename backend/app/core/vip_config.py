"""
VIP等级配置 - 统一配置中心（支持持久化存储）
合并了原来的 vip_config.py 和 vip_benefits.py
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import IntEnum


# 配置文件路径
CONFIG_DIR = Path(__file__).parent.parent.parent / "data"
CONFIG_FILE = CONFIG_DIR / "vip_config.json"


class VIPLevel(IntEnum):
    """VIP等级枚举"""
    NON_VIP = 0
    BASIC = 1       # 普通VIP
    VIP1 = 2        # VIP1
    VIP2 = 3        # VIP2
    VIP3 = 4        # VIP3
    GOLD = 5        # 黄金至尊
    DIAMOND = 6     # 钻石至尊


@dataclass
class VIPBenefits:
    """VIP权益配置"""
    name: str                    # VIP名称
    icon: str                    # VIP图标路径
    color: str                   # VIP主题色
    description: str             # VIP描述
    discount: float              # 购买折扣 (0=免费, 0.9=9折)
    can_download: bool           # 是否可下载
    daily_downloads: int         # 每日下载次数限制
    ad_free: bool                # 是否免广告
    priority_support: bool       # 是否有优先客服
    exclusive_content: bool      # 是否可访问专属内容
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'VIPBenefits':
        return cls(
            name=data.get("name", "未知"),
            icon=data.get("icon", ""),
            color=data.get("color", "#999999"),
            description=data.get("description", ""),
            discount=data.get("discount", 1.0),
            can_download=data.get("can_download", False),
            daily_downloads=data.get("daily_downloads", 0),
            ad_free=data.get("ad_free", False),
            priority_support=data.get("priority_support", False),
            exclusive_content=data.get("exclusive_content", False),
        )


# 默认VIP等级配置（完整权益配置）
DEFAULT_VIP_CONFIG: Dict[int, dict] = {
    0: {
        "name": "非VIP",
        "icon": "",
        "color": "#999999",
        "description": "普通用户",
        "discount": 1.0,
        "can_download": False,
        "daily_downloads": 0,
        "ad_free": False,
        "priority_support": False,
        "exclusive_content": False,
    },
    1: {
        "name": "普通VIP",
        "icon": "/images/backgrounds/vip_gold.webp",
        "color": "#FFD700",
        "description": "基础会员权限",
        "discount": 0.95,
        "can_download": False,
        "daily_downloads": 0,
        "ad_free": True,
        "priority_support": False,
        "exclusive_content": False,
    },
    2: {
        "name": "VIP1",
        "icon": "/images/backgrounds/vip_1.webp",
        "color": "#FF6B6B",
        "description": "VIP1级会员",
        "discount": 0.90,
        "can_download": True,
        "daily_downloads": 5,
        "ad_free": True,
        "priority_support": False,
        "exclusive_content": False,
    },
    3: {
        "name": "VIP2",
        "icon": "/images/backgrounds/vip_2.webp",
        "color": "#4ECDC4",
        "description": "VIP2级会员",
        "discount": 0.85,
        "can_download": True,
        "daily_downloads": 10,
        "ad_free": True,
        "priority_support": True,
        "exclusive_content": False,
    },
    4: {
        "name": "VIP3",
        "icon": "/images/backgrounds/vip_3.webp",
        "color": "#45B7D1",
        "description": "VIP3级会员",
        "discount": 0.80,
        "can_download": True,
        "daily_downloads": 20,
        "ad_free": True,
        "priority_support": True,
        "exclusive_content": True,
    },
    5: {
        "name": "黄金至尊",
        "icon": "/images/backgrounds/super_vip_red.webp",
        "color": "#FF4757",
        "description": "黄金至尊会员，全站免费",
        "discount": 0,  # 0表示全部免费
        "can_download": True,
        "daily_downloads": 50,
        "ad_free": True,
        "priority_support": True,
        "exclusive_content": True,
    },
    6: {
        "name": "紫色限定至尊",
        "icon": "/images/backgrounds/super_vip_blue.webp",
        "color": "#5352ED",
        "description": "紫色限定至尊会员，尊享无限",
        "discount": 0,  # 0表示全部免费
        "can_download": True,
        "daily_downloads": 100,
        "ad_free": True,
        "priority_support": True,
        "exclusive_content": True,
    },
}

# VIP等级配置（运行时使用）
VIP_LEVEL_CONFIG: Dict[int, dict] = {}


def _load_config():
    """从文件加载配置"""
    global VIP_LEVEL_CONFIG
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 将字符串键转为整数键，并合并默认配置
                VIP_LEVEL_CONFIG = {}
                for k, v in data.items():
                    level = int(k)
                    # 合并默认值，确保所有字段存在
                    default = DEFAULT_VIP_CONFIG.get(level, DEFAULT_VIP_CONFIG[0]).copy()
                    default.update(v)
                    VIP_LEVEL_CONFIG[level] = default
                # 确保所有等级都有配置
                for level in DEFAULT_VIP_CONFIG:
                    if level not in VIP_LEVEL_CONFIG:
                        VIP_LEVEL_CONFIG[level] = DEFAULT_VIP_CONFIG[level].copy()
        else:
            VIP_LEVEL_CONFIG = {k: v.copy() for k, v in DEFAULT_VIP_CONFIG.items()}
    except Exception as e:
        print(f"加载VIP配置失败: {e}")
        VIP_LEVEL_CONFIG = {k: v.copy() for k, v in DEFAULT_VIP_CONFIG.items()}


def _save_config():
    """保存配置到文件"""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(VIP_LEVEL_CONFIG, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存VIP配置失败: {e}")


def reload_config():
    """重新加载配置（供外部调用）"""
    _load_config()


# 初始化时加载配置
_load_config()


# ==================== 配置获取函数 ====================

def get_vip_config(level: int) -> dict:
    """获取VIP等级完整配置"""
    return VIP_LEVEL_CONFIG.get(level, VIP_LEVEL_CONFIG.get(0, DEFAULT_VIP_CONFIG[0]))


def get_vip_benefits(level: int) -> VIPBenefits:
    """获取VIP权益配置对象"""
    config = get_vip_config(level)
    return VIPBenefits.from_dict(config)


def get_vip_level_name(level: int) -> str:
    """获取VIP等级名称"""
    return get_vip_config(level).get("name", "非VIP")


def get_vip_level_icon(level: int) -> str:
    """获取VIP等级图标"""
    return get_vip_config(level).get("icon", "")


def get_vip_discount(level: int) -> float:
    """获取VIP折扣率"""
    return get_vip_config(level).get("discount", 1.0)


def get_vip_color(level: int) -> str:
    """获取VIP主题色"""
    return get_vip_config(level).get("color", "#999999")


def can_download(level: int) -> bool:
    """检查是否可以下载"""
    return get_vip_config(level).get("can_download", False)


def get_daily_download_limit(level: int) -> int:
    """获取每日下载限制"""
    return get_vip_config(level).get("daily_downloads", 0)


def is_ad_free(level: int) -> bool:
    """检查是否免广告"""
    return get_vip_config(level).get("ad_free", False)


def has_priority_support(level: int) -> bool:
    """检查是否有优先客服"""
    return get_vip_config(level).get("priority_support", False)


def has_exclusive_content(level: int) -> bool:
    """检查是否可访问专属内容"""
    return get_vip_config(level).get("exclusive_content", False)


# ==================== 业务逻辑函数 ====================

def can_watch_free(vip_level: int, video_vip_free_level: int) -> bool:
    """检查是否可以免费观看"""
    if vip_level >= VIPLevel.GOLD:
        return True  # 黄金及以上全免费
    if video_vip_free_level == 0:
        return False  # 视频不支持VIP免费
    return vip_level >= video_vip_free_level


def calculate_discounted_price(original_price: int, vip_level: int) -> int:
    """计算VIP折扣后的价格"""
    discount = get_vip_discount(vip_level)
    if discount == 0:
        return 0  # 免费
    return int(original_price * discount)


def get_all_vip_levels() -> Dict[int, dict]:
    """获取所有VIP等级信息（用于前端展示）"""
    return {level: config.copy() for level, config in VIP_LEVEL_CONFIG.items()}


# ==================== 配置更新函数 ====================

def update_vip_level_config(level: int, **kwargs) -> bool:
    """更新VIP等级配置并保存到文件"""
    if level not in VIP_LEVEL_CONFIG:
        return False
    
    for key, value in kwargs.items():
        if value is not None:
            VIP_LEVEL_CONFIG[level][key] = value
    
    # 保存到文件
    _save_config()
    return True


def set_vip_level_config(level: int, config: dict) -> bool:
    """设置VIP等级完整配置"""
    if level < 0 or level > 6:
        return False
    
    # 合并默认值
    default = DEFAULT_VIP_CONFIG.get(level, DEFAULT_VIP_CONFIG[0]).copy()
    default.update(config)
    VIP_LEVEL_CONFIG[level] = default
    
    _save_config()
    return True