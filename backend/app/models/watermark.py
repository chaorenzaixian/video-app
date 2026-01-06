"""
水印配置模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text
from app.core.database import Base


class WatermarkConfig(Base):
    """水印配置表"""
    __tablename__ = "watermark_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)  # 配置名称
    
    # 水印类型: image/text/user_id
    watermark_type = Column(String(20), default="image")
    
    # 图片水印设置
    image_url = Column(String(500), nullable=True)  # 水印图片路径
    image_opacity = Column(Float, default=0.5)  # 透明度 0-1
    image_scale = Column(Float, default=0.1)  # 相对视频宽度的比例
    
    # 文字水印设置
    text_template = Column(String(200), nullable=True)  # 文字模板，支持变量 {user_id} {time}
    font_size = Column(Integer, default=24)
    font_color = Column(String(20), default="white")
    text_opacity = Column(Float, default=0.3)
    
    # 位置设置
    position = Column(String(20), default="bottom_right")
    # top_left, top_right, bottom_left, bottom_right, center, moving
    offset_x = Column(Integer, default=20)
    offset_y = Column(Integer, default=20)
    
    # 动态水印设置
    is_moving = Column(Boolean, default=False)  # 是否移动
    move_speed_x = Column(Integer, default=30)  # X方向速度
    move_speed_y = Column(Integer, default=20)  # Y方向速度
    
    # 应用范围
    apply_to = Column(String(50), default="all")  # all/vip_only/free_only/download
    
    # 状态
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # 多水印时的叠加顺序（数字越小越先应用）
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


