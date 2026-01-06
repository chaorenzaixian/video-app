"""
视频水印服务 - 支持静态/动态/用户专属水印
"""
import os
import subprocess
import asyncio
from typing import Optional, List, Dict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings

_executor = ThreadPoolExecutor(max_workers=2)


class WatermarkPosition:
    """水印位置预设"""
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    CENTER = "center"
    MOVING = "moving"  # 动态移动
    RANDOM = "random"  # 随机位置


class WatermarkConfig:
    """水印配置"""
    
    def __init__(
        self,
        watermark_type: str = "image",  # image, text, user_id
        # 图片水印
        image_path: str = None,
        image_opacity: float = 0.5,  # 透明度 0-1
        image_scale: float = 0.1,  # 相对视频宽度的比例
        # 文字水印
        text: str = None,
        text_template: str = None,  # 支持 {user_id}, {time}, {date}
        font_size: int = 24,
        font_color: str = "white",
        text_opacity: float = 0.3,
        # 位置
        position: str = WatermarkPosition.BOTTOM_RIGHT,
        offset_x: int = 20,
        offset_y: int = 20,
        # 动态水印
        is_moving: bool = False,
        move_speed_x: int = 30,  # 像素/秒
        move_speed_y: int = 20,
        # 应用场景
        apply_to: str = "all"  # all, download, hls
    ):
        self.watermark_type = watermark_type
        self.image_path = image_path
        self.image_opacity = image_opacity
        self.image_scale = image_scale
        self.text = text
        self.text_template = text_template
        self.font_size = font_size
        self.font_color = font_color
        self.text_opacity = text_opacity
        self.position = position
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.is_moving = is_moving
        self.move_speed_x = move_speed_x
        self.move_speed_y = move_speed_y
        self.apply_to = apply_to


class WatermarkService:
    """水印服务"""
    
    # 位置映射（FFmpeg overlay 表达式）
    POSITION_MAP = {
        WatermarkPosition.TOP_LEFT: "(10):(10)",
        WatermarkPosition.TOP_RIGHT: "(main_w-overlay_w-10):(10)",
        WatermarkPosition.BOTTOM_LEFT: "(10):(main_h-overlay_h-10)",
        WatermarkPosition.BOTTOM_RIGHT: "(main_w-overlay_w-10):(main_h-overlay_h-10)",
        WatermarkPosition.CENTER: "(main_w-overlay_w)/2:(main_h-overlay_h)/2",
    }
    
    # 文字位置映射
    TEXT_POSITION_X = {
        WatermarkPosition.TOP_LEFT: "10",
        WatermarkPosition.BOTTOM_LEFT: "10",
        WatermarkPosition.TOP_RIGHT: "w-text_w-10",
        WatermarkPosition.BOTTOM_RIGHT: "w-text_w-10",
        WatermarkPosition.CENTER: "(w-text_w)/2",
    }
    
    TEXT_POSITION_Y = {
        WatermarkPosition.TOP_LEFT: "10",
        WatermarkPosition.TOP_RIGHT: "10",
        WatermarkPosition.BOTTOM_LEFT: "h-text_h-10",
        WatermarkPosition.BOTTOM_RIGHT: "h-text_h-10",
        WatermarkPosition.CENTER: "(h-text_h)/2",
    }
    
    @staticmethod
    def get_default_logo_path() -> str:
        """获取默认Logo路径"""
        logo_path = os.path.join(settings.UPLOAD_DIR, "site", "watermark.png")
        if os.path.exists(logo_path):
            return logo_path
        return None
    
    @staticmethod
    def build_image_filter(config: WatermarkConfig) -> str:
        """
        构建图片水印 FFmpeg 滤镜
        
        返回: filter_complex 字符串
        """
        if config.is_moving:
            # 动态移动水印（防录屏）
            position = (
                f"mod(t*{config.move_speed_x},main_w-overlay_w):"
                f"mod(t*{config.move_speed_y},main_h-overlay_h)"
            )
        elif config.position == WatermarkPosition.RANDOM:
            # 随机位置（每帧随机，视觉上闪烁）
            position = "random(1)*(main_w-overlay_w):random(1)*(main_h-overlay_h)"
        else:
            position = WatermarkService.POSITION_MAP.get(
                config.position,
                f"({config.offset_x}):({config.offset_y})"
            )
        
        # 构建滤镜链：缩放水印 -> 设置透明度 -> 叠加
        filter_str = (
            f"[1:v]scale=iw*{config.image_scale}:-1,"
            f"format=rgba,"
            f"colorchannelmixer=aa={config.image_opacity}[wm];"
            f"[0:v][wm]overlay={position}"
        )
        
        return filter_str
    
    @staticmethod
    def build_text_filter(
        config: WatermarkConfig,
        user_id: int = None,
        username: str = None
    ) -> str:
        """
        构建文字水印 FFmpeg 滤镜
        
        支持变量:
        - {user_id}: 用户ID
        - {username}: 用户名
        - {time}: 当前时间
        - {date}: 当前日期
        """
        # 处理文字模板
        text = config.text or config.text_template or "Sample"
        
        if user_id:
            text = text.replace("{user_id}", str(user_id))
        if username:
            text = text.replace("{username}", username)
        
        now = datetime.now()
        text = text.replace("{time}", now.strftime("%H:%M:%S"))
        text = text.replace("{date}", now.strftime("%Y-%m-%d"))
        
        # FFmpeg 特殊字符转义
        text = text.replace(":", "\\:")
        text = text.replace("'", "\\'")
        
        # 计算位置
        if config.is_moving:
            x = f"mod(t*{config.move_speed_x},w-text_w)"
            y = f"mod(t*{config.move_speed_y},h-text_h)"
        else:
            x = WatermarkService.TEXT_POSITION_X.get(config.position, str(config.offset_x))
            y = WatermarkService.TEXT_POSITION_Y.get(config.position, str(config.offset_y))
        
        # 构建 drawtext 滤镜
        filter_str = (
            f"drawtext=text='{text}':"
            f"fontcolor={config.font_color}@{config.text_opacity}:"
            f"fontsize={config.font_size}:"
            f"x={x}:y={y}"
        )
        
        # 添加阴影效果提高可读性
        filter_str += ":shadowcolor=black@0.5:shadowx=2:shadowy=2"
        
        return filter_str
    
    @staticmethod
    def _apply_watermark_sync(
        input_path: str,
        output_path: str,
        config: WatermarkConfig,
        user_id: int = None,
        username: str = None
    ) -> bool:
        """
        同步应用水印（在线程池中执行）
        """
        try:
            cmd = ["ffmpeg", "-y", "-i", input_path]
            filter_parts = []
            
            if config.watermark_type == "image":
                # 图片水印需要第二个输入
                if not config.image_path or not os.path.exists(config.image_path):
                    print(f"[Watermark] 水印图片不存在: {config.image_path}")
                    return False
                
                cmd.extend(["-i", config.image_path])
                filter_complex = WatermarkService.build_image_filter(config)
                cmd.extend(["-filter_complex", filter_complex])
                
            elif config.watermark_type in ["text", "user_id"]:
                # 文字水印
                if config.watermark_type == "user_id" and user_id:
                    # 用户专属水印
                    config.text_template = config.text_template or "ID:{user_id}"
                
                vf = WatermarkService.build_text_filter(config, user_id, username)
                cmd.extend(["-vf", vf])
            
            # 视频编码参数
            cmd.extend([
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "copy",  # 音频直接复制
                output_path
            ])
            
            print(f"[Watermark] 执行命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=1800  # 30分钟超时
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8', errors='ignore')
                print(f"[Watermark] FFmpeg 错误: {error_msg[:500]}")
                return False
            
            if os.path.exists(output_path):
                print(f"[Watermark] 水印添加成功: {output_path}")
                return True
            
            return False
            
        except subprocess.TimeoutExpired:
            print("[Watermark] 处理超时")
            return False
        except Exception as e:
            print(f"[Watermark] 异常: {e}")
            return False
    
    @staticmethod
    async def apply_watermark(
        input_path: str,
        output_path: str,
        config: WatermarkConfig,
        user_id: int = None,
        username: str = None
    ) -> bool:
        """
        异步应用水印
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor,
            WatermarkService._apply_watermark_sync,
            input_path, output_path, config, user_id, username
        )
    
    @staticmethod
    async def apply_multi_watermark(
        input_path: str,
        output_path: str,
        configs: List[WatermarkConfig],
        user_id: int = None,
        username: str = None
    ) -> bool:
        """
        应用多个水印（叠加）
        """
        if not configs:
            return True
        
        # 临时文件路径
        temp_files = []
        current_input = input_path
        
        try:
            for i, config in enumerate(configs):
                if i < len(configs) - 1:
                    # 中间步骤使用临时文件
                    temp_path = output_path.replace('.mp4', f'_wm_temp_{i}.mp4')
                    temp_files.append(temp_path)
                    result = await WatermarkService.apply_watermark(
                        current_input, temp_path, config, user_id, username
                    )
                else:
                    # 最后一步输出到目标文件
                    result = await WatermarkService.apply_watermark(
                        current_input, output_path, config, user_id, username
                    )
                
                if not result:
                    return False
                
                current_input = temp_path if i < len(configs) - 1 else output_path
            
            return True
            
        finally:
            # 清理临时文件
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
    
    @staticmethod
    def get_default_watermark_configs() -> List[WatermarkConfig]:
        """
        获取默认水印配置列表（同步版本，用于视频处理）
        
        优先从数据库加载，如果没有则返回默认配置
        """
        configs = []
        
        # 尝试从数据库同步加载（用于后台任务）
        try:
            from app.core.database import AsyncSessionLocal
            import asyncio
            
            async def load_from_db():
                async with AsyncSessionLocal() as db:
                    from sqlalchemy import select
                    from app.models.watermark import WatermarkConfig as WMConfigModel
                    
                    result = await db.execute(
                        select(WMConfigModel)
                        .where(WMConfigModel.is_active == True)
                        .order_by(WMConfigModel.priority)
                    )
                    db_configs = result.scalars().all()
                    
                    wm_configs = []
                    for c in db_configs:
                        image_path = None
                        if c.image_url:
                            from app.core.config import settings
                            image_path = os.path.join(
                                settings.UPLOAD_DIR, 
                                c.image_url.replace("/uploads/", "")
                            )
                        
                        wm_configs.append(WatermarkConfig(
                            watermark_type=c.watermark_type,
                            image_path=image_path,
                            image_opacity=c.image_opacity,
                            image_scale=c.image_scale,
                            text_template=c.text_template,
                            font_size=c.font_size,
                            font_color=c.font_color,
                            text_opacity=c.text_opacity,
                            position=c.position,
                            offset_x=c.offset_x,
                            offset_y=c.offset_y,
                            is_moving=c.is_moving,
                            move_speed_x=c.move_speed_x,
                            move_speed_y=c.move_speed_y,
                            apply_to=c.apply_to
                        ))
                    
                    return wm_configs
            
            # 尝试运行异步加载
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果事件循环正在运行，创建新任务
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        configs = pool.submit(asyncio.run, load_from_db()).result()
                else:
                    configs = loop.run_until_complete(load_from_db())
            except RuntimeError:
                configs = asyncio.run(load_from_db())
            
            if configs:
                return configs
                
        except Exception as e:
            print(f"[Watermark] 从数据库加载配置失败: {e}")
        
        # 回退到默认配置
        # Logo 水印（如果存在）
        logo_path = WatermarkService.get_default_logo_path()
        if logo_path:
            configs.append(WatermarkConfig(
                watermark_type="image",
                image_path=logo_path,
                image_opacity=0.6,
                image_scale=0.08,
                position=WatermarkPosition.BOTTOM_RIGHT,
                offset_x=20,
                offset_y=20
            ))
        
        return configs
    
    @staticmethod
    def create_user_watermark(
        user_id: int,
        username: str = None,
        is_moving: bool = True
    ) -> WatermarkConfig:
        """
        创建用户专属水印配置（用于追踪盗录）
        """
        return WatermarkConfig(
            watermark_type="user_id",
            text_template="ID:{user_id}",
            font_size=18,
            font_color="white",
            text_opacity=0.2,  # 低透明度
            position=WatermarkPosition.CENTER,
            is_moving=is_moving,
            move_speed_x=25,
            move_speed_y=15
        )
    
    @staticmethod
    def create_anti_recording_watermark() -> WatermarkConfig:
        """
        创建防录屏动态水印
        """
        return WatermarkConfig(
            watermark_type="text",
            text="VOD Platform",
            font_size=16,
            font_color="white",
            text_opacity=0.15,
            is_moving=True,
            move_speed_x=40,
            move_speed_y=25
        )

