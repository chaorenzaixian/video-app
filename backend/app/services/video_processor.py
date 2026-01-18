"""
视频处理服务
负责视频转码、生成缩略图、AI分析等
支持 GPU 服务器转码（可选）
"""
import os
import subprocess
import json
import asyncio
from typing import Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.video import Video, VideoStatus, VideoQuality
from app.core.redis import RedisCache
from app.services.ai_service import AIService

# 线程池用于执行阻塞的FFmpeg操作
# 动态设置：根据CPU核心数调整，最小2，最大8
_cpu_count = multiprocessing.cpu_count()
_max_workers = max(2, min(8, _cpu_count))
_executor = ThreadPoolExecutor(max_workers=_max_workers)

# 并发控制信号量：限制同时处理的视频数量，防止服务器过载
# 最多同时处理2个视频（转码是CPU密集型操作）
_processing_semaphore = asyncio.Semaphore(2)


class VideoProcessor:
    """视频处理器"""
    
    @staticmethod
    async def process_video(video_id: int, file_path: str, skip_thumbnail: bool = False):
        """
        处理视频：
        1. 检查是否启用 GPU 转码
        2. 如果启用 GPU，推送到 GPU 服务器处理
        3. 否则本地处理（获取视频信息、生成缩略图、转码为HLS、AI分析）
        
        使用信号量控制并发，防止服务器过载
        """
        # 检查是否启用 GPU 转码
        try:
            from app.services.gpu_transcode_service import GPUTranscodeService
            if GPUTranscodeService.is_enabled():
                # 推送到 GPU 服务器处理
                success = await GPUTranscodeService.push_to_gpu(video_id, file_path)
                if success:
                    print(f"[GPU] 视频已推送到GPU服务器: video_id={video_id}")
                    return
                else:
                    print(f"[GPU] GPU推送失败，回退到本地处理: video_id={video_id}")
        except ImportError:
            pass
        except Exception as e:
            print(f"[GPU] GPU服务异常，回退到本地处理: {e}")
        
        # 本地处理
        async with _processing_semaphore:
            await VideoProcessor._do_process_video(video_id, file_path, skip_thumbnail)
    
    @staticmethod
    async def _do_process_video(video_id: int, file_path: str, skip_thumbnail: bool = False):
        """实际的视频处理逻辑"""
        async with AsyncSessionLocal() as db:
            try:
                # 获取视频记录
                from sqlalchemy import select
                result = await db.execute(select(Video).where(Video.id == video_id))
                video = result.scalar_one_or_none()
                
                if not video:
                    return
                
                # 更新进度（Redis可选）
                try:
                    await RedisCache.set(f"video_process:{video_id}", "10", expire=3600)
                except:
                    pass
                
                # 1. 获取视频信息
                video_info = await VideoProcessor.get_video_info(file_path)
                video.duration = video_info.get("duration", 0)
                video.quality = VideoProcessor.detect_quality(video_info)
                
                try:
                    await RedisCache.set(f"video_process:{video_id}", "20", expire=3600)
                except:
                    pass
                
                # 2. 生成缩略图（传入时长用于智能采样），若已有自定义封面则跳过
                thumbnail_path = None
                if not skip_thumbnail:
                    thumbnail_path = await VideoProcessor.generate_thumbnail(video_id, file_path, video.duration)
                    video.cover_url = thumbnail_path
                    print(f"[Thumbnail] Video {video_id} thumbnail generated")
                else:
                    print(f"[Thumbnail] Video {video_id} using custom cover, skip")
                    thumbnail_path = video.cover_url  # 使用已设置的自定义封面路径
                
                try:
                    await RedisCache.set(f"video_process:{video_id}", "30", expire=3600)
                except:
                    pass
                
                # 3. 生成视频预览（悬停播放）- 无论是否有自定义封面都要生成
                print(f"[Preview] Video {video_id} generating preview...")
                preview_path = await VideoProcessor.generate_preview(video_id, file_path, video.duration)
                video.preview_url = preview_path
                if preview_path:
                    print(f"[Preview] Video {video_id} preview OK: {preview_path}")
                else:
                    print(f"[WARN] Video {video_id} preview generation failed")
                
                try:
                    await RedisCache.set(f"video_process:{video_id}", "40", expire=3600)
                except:
                    pass
                
                # 4. 应用水印（如果配置了）
                try:
                    from app.services.watermark_service import WatermarkService
                    watermark_configs = WatermarkService.get_default_watermark_configs()
                    if watermark_configs:
                        watermarked_path = file_path.replace('.mp4', '_wm.mp4').replace('.MP4', '_wm.mp4')
                        watermark_success = await WatermarkService.apply_multi_watermark(
                            file_path,
                            watermarked_path,
                            watermark_configs
                        )
                        if watermark_success and os.path.exists(watermarked_path):
                            file_path = watermarked_path
                            print(f"[Watermark] Video {video_id} watermark OK")
                except Exception as e:
                    print(f"[WARN] Video {video_id} watermark failed (continue): {e}")
                
                # 5. 转码为HLS（自适应码率）
                video_height = video_info.get("height", 720)
                hls_path = await VideoProcessor.transcode_to_hls(video_id, file_path, video_height)
                video.hls_url = hls_path
                
                try:
                    await RedisCache.set(f"video_process:{video_id}", "80", expire=3600)
                except:
                    pass
                
                # 5. AI分析（如果启用）
                if settings.OPENAI_API_KEY:
                    try:
                        ai_result = await AIService.analyze_video(
                            video.title,
                            video.description,
                            thumbnail_path
                        )
                        video.ai_summary = ai_result.get("summary")
                        video.ai_tags = ai_result.get("tags")
                    except Exception as e:
                        print(f"AI分析失败: {e}")
                
                try:
                    await RedisCache.set(f"video_process:{video_id}", "100", expire=3600)
                except:
                    pass
                
                # 更新状态为已发布
                video.status = VideoStatus.PUBLISHED
                video.published_at = datetime.utcnow()
                
                await db.commit()
                print(f"[OK] Video {video_id} processing complete")
                
            except Exception as e:
                import traceback
                print(f"[ERROR] Video processing failed: {e}")
                print(traceback.format_exc())
                # 更新状态为失败
                try:
                    video.status = VideoStatus.FAILED
                    await db.commit()
                except:
                    pass
    
    @staticmethod
    def _run_ffprobe(file_path: str) -> dict:
        """同步执行ffprobe（在线程池中运行）"""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            if result.returncode != 0:
                print(f"ffprobe错误: {result.stderr.decode('utf-8', errors='ignore')}")
                return {"duration": 0, "width": 0, "height": 0}
            
            info = json.loads(result.stdout.decode('utf-8', errors='ignore'))
            
            duration = float(info.get("format", {}).get("duration", 0))
            
            video_stream = None
            for stream in info.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_stream = stream
                    break
            
            width = video_stream.get("width", 0) if video_stream else 0
            height = video_stream.get("height", 0) if video_stream else 0
            
            return {
                "duration": duration,
                "width": width,
                "height": height
            }
        except Exception as e:
            print(f"获取视频信息失败: {e}")
            return {"duration": 0, "width": 0, "height": 0}
    
    @staticmethod
    async def get_video_info(file_path: str) -> dict:
        """获取视频信息（非阻塞）"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, VideoProcessor._run_ffprobe, file_path)
    
    @staticmethod
    def detect_quality(video_info: dict) -> VideoQuality:
        """检测视频质量"""
        height = video_info.get("height", 0)
        
        if height >= 2160:
            return VideoQuality.UHD
        elif height >= 1440:
            return VideoQuality.QHD
        elif height >= 1080:
            return VideoQuality.FHD
        elif height >= 720:
            return VideoQuality.HD
        else:
            return VideoQuality.SD
    
    @staticmethod
    def _analyze_frame_quality(image_path: str) -> dict:
        """
        使用OpenCV分析帧质量
        返回: {score, sharpness, colorfulness, brightness, has_face}
        """
        try:
            import cv2
            import numpy as np
            
            img = cv2.imread(image_path)
            if img is None:
                return {"score": 0}
            
            # 1. 清晰度评分 (Laplacian方差)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # 2. 色彩丰富度 (颜色标准差)
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            colorfulness = np.std(hsv[:,:,0]) + np.std(hsv[:,:,1])
            
            # 3. 亮度适中度 (偏离128的程度，越小越好)
            brightness = np.mean(gray)
            brightness_score = 100 - abs(brightness - 128) * 0.5
            
            # 4. 避免纯黑/纯白帧
            if brightness < 20 or brightness > 235:
                return {"score": 0, "reason": "太暗或太亮"}
            
            # 5. 人脸检测 (可选，加分项)
            has_face = False
            try:
                face_cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                )
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                has_face = len(faces) > 0
            except:
                pass
            
            # 综合评分
            score = (
                sharpness * 0.4 +           # 清晰度权重40%
                colorfulness * 0.3 +         # 色彩权重30%
                brightness_score * 0.2 +     # 亮度权重20%
                (50 if has_face else 0)      # 人脸加分50
            )
            
            return {
                "score": score,
                "sharpness": sharpness,
                "colorfulness": colorfulness,
                "brightness": brightness,
                "has_face": has_face
            }
        except Exception as e:
            print(f"帧分析失败: {e}")
            return {"score": 0}
    
    @staticmethod
    def _run_thumbnail(video_id: int, file_path: str, thumbnail_path: str, duration: float = 0) -> str:
        """
        AI智能生成缩略图（在线程池中运行）
        策略：从多个时间点采样，使用AI分析选择最佳帧
        """
        import tempfile
        import shutil
        
        # 计算采样时间点（避开片头片尾）
        if duration > 30:
            # 长视频：5个采样点
            sample_points = [
                duration * 0.10,
                duration * 0.25,
                duration * 0.40,
                duration * 0.55,
                duration * 0.70,
            ]
        elif duration > 10:
            # 中等视频：3个采样点
            sample_points = [
                duration * 0.15,
                duration * 0.40,
                duration * 0.65,
            ]
        elif duration > 3:
            # 短视频：2个采样点
            sample_points = [duration * 0.30, duration * 0.60]
        else:
            # 极短视频：中间位置
            sample_points = [duration * 0.5]
        
        temp_dir = tempfile.mkdtemp()
        candidates = []
        
        try:
            print(f"[Video] AI智能缩略图分析开始 (视频时长: {duration:.1f}秒)")
            
            # 从多个时间点截取候选缩略图
            for i, time_point in enumerate(sample_points):
                temp_path = os.path.join(temp_dir, f"thumb_{i}.jpg")
                time_str = f"{int(time_point // 3600):02d}:{int((time_point % 3600) // 60):02d}:{time_point % 60:06.3f}"
                
                cmd = [
                    "ffmpeg",
                    "-ss", time_str,
                    "-i", file_path,
                    "-vframes", "1",
                    "-vf", "scale=640:-1",
                    "-q:v", "2",
                    "-y",
                    temp_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, timeout=30)
                if result.returncode == 0 and os.path.exists(temp_path):
                    # AI美学评分（高级版）
                    try:
                        from app.services.aesthetic_scorer import analyze_aesthetic
                        analysis = analyze_aesthetic(temp_path)
                        score = analysis.get("aesthetic_score", 0)
                    except ImportError:
                        # 回退到基础分析
                        analysis = VideoProcessor._analyze_frame_quality(temp_path)
                        score = analysis.get("score", 0)
                    
                    candidates.append({
                        "path": temp_path,
                        "time": time_point,
                        "score": score,
                        "analysis": analysis
                    })
                    
                    # 显示评分详情
                    comp = analysis.get("composition_score", 0)
                    color = analysis.get("color_harmony", 0)
                    print(f"  [Thumb] {time_str}: 美学={score:.1f} 构图={comp:.1f} 色彩={color:.1f}")
            
            if not candidates:
                print("[FAIL] 智能采样失败，回退到第1秒")
                cmd = [
                    "ffmpeg", "-i", file_path,
                    "-ss", "00:00:01", "-vframes", "1",
                    "-vf", "scale=640:-1", "-y", thumbnail_path
                ]
                subprocess.run(cmd, capture_output=True, timeout=30)
                return f"/uploads/thumbnails/{video_id}.jpg" if os.path.exists(thumbnail_path) else ""
            
            # 选择AI评分最高的帧
            best = max(candidates, key=lambda x: x["score"])
            shutil.copy(best["path"], thumbnail_path)
            
            analysis = best["analysis"]
            print(f"[OK] AI智能缩略图生成成功!")
            print(f"   🏆 选择时间点: {best['time']:.1f}秒")
            print(f"   📊 美学评分: {best['score']:.1f}/100")
            print(f"   🎯 构图质量: {analysis.get('composition_score', 0):.1f}")
            print(f"   🎨 色彩和谐: {analysis.get('color_harmony', 0):.1f}")
            print(f"   🔍 清晰度: {analysis.get('clarity_score', analysis.get('sharpness', 0)):.1f}")
            print(f"   ✨ 特征丰富: {analysis.get('feature_richness', 0):.1f}")
            
            return f"/uploads/thumbnails/{video_id}.jpg"
            
        except Exception as e:
            print(f"生成缩略图失败: {e}")
            import traceback
            traceback.print_exc()
            return ""
        finally:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
    
    @staticmethod
    def _run_thumbnail_webp(video_id: int, file_path: str, thumbnail_path: str, duration: float = 0) -> str:
        """
        生成 WebP 格式缩略图（更小体积，更好质量）
        """
        import tempfile
        import shutil
        
        # 计算采样时间点（避开片头片尾）
        if duration > 30:
            sample_points = [
                duration * 0.10,
                duration * 0.25,
                duration * 0.40,
                duration * 0.55,
                duration * 0.70,
            ]
        elif duration > 10:
            sample_points = [
                duration * 0.15,
                duration * 0.40,
                duration * 0.65,
            ]
        elif duration > 3:
            sample_points = [duration * 0.30, duration * 0.60]
        else:
            sample_points = [duration * 0.5 if duration > 0 else 1]
        
        temp_dir = tempfile.mkdtemp()
        candidates = []
        
        try:
            print(f"[Video] WebP智能缩略图分析开始 (视频时长: {duration:.1f}秒)")
            
            # 从多个时间点截取候选缩略图
            for i, time_point in enumerate(sample_points):
                temp_path = os.path.join(temp_dir, f"thumb_{i}.webp")
                time_str = f"{int(time_point // 3600):02d}:{int((time_point % 3600) // 60):02d}:{time_point % 60:06.3f}"
                
                # 使用 FFmpeg 直接输出 WebP 格式
                cmd = [
                    "ffmpeg",
                    "-ss", time_str,
                    "-i", file_path,
                    "-vframes", "1",
                    "-vf", "scale=640:-1",
                    "-c:v", "libwebp",
                    "-quality", "85",  # WebP 质量参数
                    "-y",
                    temp_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, timeout=30)
                if result.returncode == 0 and os.path.exists(temp_path):
                    # 简单评分：基于文件大小和基础分析
                    try:
                        import cv2
                        img = cv2.imread(temp_path)
                        if img is not None:
                            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
                            brightness = gray.mean()
                            
                            # 避免过暗或过亮
                            if brightness < 20 or brightness > 235:
                                score = 0
                            else:
                                score = min(100, sharpness / 10 + img.std() / 2)
                        else:
                            score = os.path.getsize(temp_path) / 5000
                    except:
                        score = os.path.getsize(temp_path) / 5000
                    
                    candidates.append({
                        "path": temp_path,
                        "time": time_point,
                        "score": score
                    })
                    print(f"  [Thumb] WebP {time_str}: 评分={score:.1f}")
            
            if not candidates:
                print("[FAIL] WebP智能采样失败")
                return ""
            
            # 选择评分最高的帧
            best = max(candidates, key=lambda x: x["score"])
            shutil.copy(best["path"], thumbnail_path)
            
            # 对比文件大小
            webp_size = os.path.getsize(thumbnail_path)
            print(f"[OK] WebP缩略图生成成功: {webp_size/1024:.1f}KB (选择时间点: {best['time']:.1f}秒)")
            
            return f"/uploads/thumbnails/{video_id}.webp"
            
        except Exception as e:
            print(f"生成WebP缩略图失败: {e}")
            return ""
        finally:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
    
    @staticmethod
    async def generate_thumbnail(video_id: int, file_path: str, duration: float = 0) -> str:
        """生成缩略图（非阻塞，WebP格式）"""
        # 优先使用 WebP 格式（更小体积，更好质量）
        thumbnail_filename = f"{video_id}.webp"
        thumbnail_path = os.path.join(settings.THUMBNAIL_DIR, thumbnail_filename)
        os.makedirs(settings.THUMBNAIL_DIR, exist_ok=True)
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            _executor, 
            VideoProcessor._run_thumbnail_webp, 
            video_id, file_path, thumbnail_path, duration
        )
        
        # 如果 WebP 生成失败，回退到 JPG
        if not result or not os.path.exists(thumbnail_path):
            thumbnail_filename = f"{video_id}.jpg"
            thumbnail_path = os.path.join(settings.THUMBNAIL_DIR, thumbnail_filename)
            result = await loop.run_in_executor(
                _executor, 
                VideoProcessor._run_thumbnail, 
                video_id, file_path, thumbnail_path, duration
            )
        
        return result
    
    @staticmethod
    def _run_transcode(video_id: int, file_path: str, hls_dir: str, output_path: str) -> str:
        """同步转码（在线程池中运行）- 单码率版本，支持硬件加速"""
        # 检测可用的硬件加速
        hw_encoder = VideoProcessor._detect_hw_encoder()
        
        if hw_encoder == "qsv":
            # Intel QSV 硬件加速
            cmd = [
                "ffmpeg",
                "-hwaccel", "qsv",
                "-i", file_path,
                "-c:v", "h264_qsv",
                "-c:a", "aac",
                "-preset", "fast",
                "-global_quality", "22",
                "-hls_time", "10",
                "-hls_list_size", "0",
                "-hls_segment_filename", os.path.join(hls_dir, "segment_%03d.ts"),
                "-y",
                output_path
            ]
        elif hw_encoder == "nvenc":
            # NVIDIA NVENC 硬件加速
            cmd = [
                "ffmpeg",
                "-hwaccel", "cuda",
                "-i", file_path,
                "-c:v", "h264_nvenc",
                "-c:a", "aac",
                "-preset", "fast",
                "-cq", "22",
                "-hls_time", "10",
                "-hls_list_size", "0",
                "-hls_segment_filename", os.path.join(hls_dir, "segment_%03d.ts"),
                "-y",
                output_path
            ]
        else:
            # 软件编码（CPU）
            cmd = [
                "ffmpeg",
                "-i", file_path,
                "-c:v", "libx264",
                "-c:a", "aac",
                "-preset", "fast",
                "-crf", "22",
                "-threads", "0",
                "-hls_time", "10",
                "-hls_list_size", "0",
                "-hls_segment_filename", os.path.join(hls_dir, "segment_%03d.ts"),
                "-y",
                output_path
            ]
        
        try:
            print(f"[Video] 转码命令 ({hw_encoder or 'cpu'}): {' '.join(cmd[:8])}...")
            result = subprocess.run(cmd, capture_output=True, timeout=1800)  # 30分钟超时
            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8', errors='ignore')
                print(f"转码错误: {error_msg[:500]}")
                # 如果硬件加速失败，回退到软件编码
                if hw_encoder:
                    print(f"[WARN] 硬件加速失败，回退到CPU编码...")
                    return VideoProcessor._run_transcode_cpu(video_id, file_path, hls_dir, output_path)
                return ""
            print(f"[OK] 转码成功 ({hw_encoder or 'cpu'}): {output_path}")
            return f"/uploads/hls/{video_id}/playlist.m3u8"
        except Exception as e:
            print(f"转码失败: {e}")
            return ""
    
    @staticmethod
    def _run_transcode_cpu(video_id: int, file_path: str, hls_dir: str, output_path: str) -> str:
        """纯CPU软件转码（回退方案）"""
        cmd = [
            "ffmpeg",
            "-i", file_path,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-preset", "fast",
            "-crf", "22",
            "-threads", "0",
            "-hls_time", "10",
            "-hls_list_size", "0",
            "-hls_segment_filename", os.path.join(hls_dir, "segment_%03d.ts"),
            "-y",
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=1800)
            if result.returncode != 0:
                print(f"CPU转码错误: {result.stderr.decode('utf-8', errors='ignore')[:500]}")
                return ""
            return f"/uploads/hls/{video_id}/playlist.m3u8"
        except Exception as e:
            print(f"CPU转码失败: {e}")
            return ""
    
    @staticmethod
    def _detect_hw_encoder() -> str:
        """检测可用的硬件编码器"""
        # 检测 Intel QSV
        try:
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True, timeout=10
            )
            encoders = result.stdout.decode('utf-8', errors='ignore')
            
            if "h264_qsv" in encoders:
                # 进一步验证QSV是否真正可用
                test_result = subprocess.run(
                    ["ffmpeg", "-hide_banner", "-init_hw_device", "qsv=hw", "-f", "lavfi", "-i", "nullsrc=s=256x256:d=1", "-c:v", "h264_qsv", "-f", "null", "-"],
                    capture_output=True, timeout=10
                )
                if test_result.returncode == 0:
                    print("[HW] Intel QSV 硬件加速可用")
                    return "qsv"
            
            if "h264_nvenc" in encoders:
                print("[HW] NVIDIA NVENC 硬件加速可用")
                return "nvenc"
            
            if "h264_amf" in encoders:
                print("[HW] AMD AMF 硬件加速可用")
                return "amf"
                
        except Exception as e:
            print(f"[WARN] 硬件加速检测失败: {e}")
        
        print("[HW] 使用CPU软件编码")
        return ""

    @staticmethod
    def _run_transcode_adaptive(video_id: int, file_path: str, hls_dir: str, video_height: int) -> str:
        """
        自适应码率转码（多清晰度HLS）
        根据源视频质量生成多个清晰度版本，支持硬件加速
        """
        # 检测硬件加速
        hw_encoder = VideoProcessor._detect_hw_encoder()
        
        # 根据源视频高度决定生成哪些清晰度
        qualities = []
        if video_height >= 1080:
            qualities = [
                {"name": "1080p", "height": 1080, "bitrate": "5000k", "audio": "192k"},
                {"name": "720p", "height": 720, "bitrate": "2500k", "audio": "128k"},
                {"name": "480p", "height": 480, "bitrate": "1000k", "audio": "96k"},
            ]
        elif video_height >= 720:
            qualities = [
                {"name": "720p", "height": 720, "bitrate": "2500k", "audio": "128k"},
                {"name": "480p", "height": 480, "bitrate": "1000k", "audio": "96k"},
            ]
        else:
            qualities = [
                {"name": "480p", "height": 480, "bitrate": "1000k", "audio": "96k"},
            ]
        
        master_playlist_content = "#EXTM3U\n#EXT-X-VERSION:3\n"
        success_count = 0
        
        for q in qualities:
            quality_name = q["name"]
            quality_dir = os.path.join(hls_dir, quality_name)
            os.makedirs(quality_dir, exist_ok=True)
            
            output_playlist = os.path.join(quality_dir, "playlist.m3u8")
            
            # 根据硬件加速类型构建命令
            if hw_encoder == "qsv":
                cmd = [
                    "ffmpeg",
                    "-hwaccel", "qsv",
                    "-i", file_path,
                    "-c:v", "h264_qsv",
                    "-c:a", "aac",
                    "-vf", f"scale_qsv=-1:{q['height']}",
                    "-b:v", q["bitrate"],
                    "-b:a", q["audio"],
                    "-hls_time", "10",
                    "-hls_list_size", "0",
                    "-hls_segment_filename", os.path.join(quality_dir, "segment_%03d.ts"),
                    "-y",
                    output_playlist
                ]
            elif hw_encoder == "nvenc":
                cmd = [
                    "ffmpeg",
                    "-hwaccel", "cuda",
                    "-i", file_path,
                    "-c:v", "h264_nvenc",
                    "-c:a", "aac",
                    "-vf", f"scale=-2:{q['height']}",
                    "-b:v", q["bitrate"],
                    "-b:a", q["audio"],
                    "-hls_time", "10",
                    "-hls_list_size", "0",
                    "-hls_segment_filename", os.path.join(quality_dir, "segment_%03d.ts"),
                    "-y",
                    output_playlist
                ]
            else:
                cmd = [
                    "ffmpeg",
                    "-i", file_path,
                    "-c:v", "libx264",
                    "-c:a", "aac",
                    "-preset", "fast",
                    "-threads", "0",
                    "-vf", f"scale=-2:{q['height']}",
                    "-b:v", q["bitrate"],
                    "-b:a", q["audio"],
                    "-hls_time", "10",
                    "-hls_list_size", "0",
                    "-hls_segment_filename", os.path.join(quality_dir, "segment_%03d.ts"),
                    "-y",
                    output_playlist
                ]
            
            try:
                print(f"[Video] 转码 {quality_name} ({hw_encoder or 'cpu'}): video_id={video_id}")
                result = subprocess.run(cmd, capture_output=True, timeout=1800)
                
                if result.returncode == 0:
                    # 计算带宽（大约）
                    bandwidth = int(q["bitrate"].replace("k", "")) * 1000
                    master_playlist_content += f"#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION=-x{q['height']}\n"
                    master_playlist_content += f"{quality_name}/playlist.m3u8\n"
                    success_count += 1
                    print(f"[OK] {quality_name} 转码成功")
                else:
                    print(f"[FAIL] {quality_name} 转码失败: {result.stderr.decode('utf-8', errors='ignore')[:200]}")
            except Exception as e:
                print(f"[FAIL] {quality_name} 转码异常: {e}")
        
        if success_count == 0:
            return ""
        
        # 写入主播放列表
        master_playlist_path = os.path.join(hls_dir, "master.m3u8")
        with open(master_playlist_path, "w") as f:
            f.write(master_playlist_content)
        
        print(f"[OK] 自适应码率转码完成 ({hw_encoder or 'cpu'}): {success_count}/{len(qualities)} 个清晰度")
        return f"/uploads/hls/{video_id}/master.m3u8"

    @staticmethod
    async def transcode_to_hls(video_id: int, file_path: str, video_height: int = 720) -> str:
        """
        转码为HLS格式（非阻塞）
        支持自适应码率（多清晰度）
        """
        hls_dir = os.path.join(settings.HLS_DIR, str(video_id))
        os.makedirs(hls_dir, exist_ok=True)
        
        loop = asyncio.get_event_loop()
        
        # 如果源视频较高清晰度，使用自适应码率
        if video_height >= 720:
            result = await loop.run_in_executor(
                _executor,
                VideoProcessor._run_transcode_adaptive,
                video_id, file_path, hls_dir, video_height
            )
            if result:
                return result
        
        # 回退到单码率转码
        output_path = os.path.join(hls_dir, "playlist.m3u8")
        return await loop.run_in_executor(
            _executor,
            VideoProcessor._run_transcode,
            video_id, file_path, hls_dir, output_path
        )
    
    @staticmethod
    def _run_preview(video_id: int, file_path: str, preview_path: str, duration: float) -> str:
        """
        生成视频预览（WebM格式，分段预览）
        10段，每段1秒，均匀分布在整个视频中
        """
        try:
            # 10段预览，每段1秒，均匀分布
            num_segments = 10
            seg_duration = 1.0  # 每段1秒
            
            if duration < 10:
                # 短视频：按视频时长平均分段
                num_segments = max(1, int(duration))
                seg_duration = min(1.0, duration / num_segments)
            
            segments = []
            for i in range(num_segments):
                # 计算每段的起始位置（均匀分布）
                # 从5%开始到95%结束，避免片头片尾
                position = 0.05 + (0.9 * i / (num_segments - 1)) if num_segments > 1 else 0.5
                start_time = duration * position
                
                # 确保不超过视频末尾
                if start_time + seg_duration > duration:
                    start_time = max(0, duration - seg_duration)
                
                segments.append((start_time, seg_duration))
            
            temp_files = []
            preview_dir = os.path.dirname(preview_path)
            
            # 生成每个分段的临时文件
            for i, (start_time, seg_duration) in enumerate(segments):
                # 确保不超过视频末尾
                if start_time + seg_duration > duration:
                    start_time = max(0, duration - seg_duration)
                
                time_str = f"{int(start_time // 3600):02d}:{int((start_time % 3600) // 60):02d}:{start_time % 60:06.3f}"
                temp_path = os.path.join(preview_dir, f"temp_{video_id}_{i}.webm")
                temp_files.append(temp_path)
                
                cmd = [
                    "ffmpeg",
                    "-ss", time_str,
                    "-i", file_path,
                    "-t", str(seg_duration),
                    "-c:v", "libvpx-vp9",
                    "-b:v", "500k",
                    "-vf", "scale=480:-1",  # 宽度480px
                    "-an",
                    "-y",
                    temp_path
                ]
                
                print(f"[Video] 生成预览片段 {i+1}/{len(segments)}: {time_str} 开始，{seg_duration}秒")
                result = subprocess.run(cmd, capture_output=True, timeout=60)
                
                if result.returncode != 0:
                    print(f"片段 {i+1} 生成失败: {result.stderr.decode('utf-8', errors='ignore')[:200]}")
            
            # 创建拼接列表文件（Windows需要用正斜杠）
            concat_file = os.path.join(preview_dir, f"concat_{video_id}.txt")
            with open(concat_file, 'w', encoding='utf-8') as f:
                for temp_path in temp_files:
                    if os.path.exists(temp_path):
                        # Windows路径转换为正斜杠格式
                        safe_path = temp_path.replace('\\', '/')
                        f.write(f"file '{safe_path}'\n")
            
            # 拼接所有片段
            concat_cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c:v", "libvpx-vp9",
                "-b:v", "500k",
                "-y",
                preview_path
            ]
            
            print(f"[Concat] 拼接 {len(segments)} 个预览片段...")
            concat_result = subprocess.run(concat_cmd, capture_output=True, timeout=120)
            
            # 清理临时文件
            for temp_path in temp_files:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            if os.path.exists(concat_file):
                os.remove(concat_file)
            
            if concat_result.returncode != 0:
                print(f"拼接错误: {concat_result.stderr.decode('utf-8', errors='ignore')[:200]}")
                return ""
            
            # 检查文件大小
            if os.path.exists(preview_path):
                size_kb = os.path.getsize(preview_path) / 1024
                total_duration = sum(seg[1] for seg in segments)
                print(f"[OK] 分段预览生成成功: {len(segments)}段，共{total_duration}秒，{size_kb:.1f}KB")
                return f"/uploads/previews/{video_id}.webm"
            
            return ""
            
        except Exception as e:
            import traceback
            print(f"预览生成异常: {e}")
            print(traceback.format_exc())
            return ""
    
    @staticmethod
    async def generate_preview(video_id: int, file_path: str, duration: float = 0) -> str:
        """生成视频预览（非阻塞）"""
        preview_dir = os.path.join(settings.UPLOAD_DIR, "previews")
        os.makedirs(preview_dir, exist_ok=True)
        preview_path = os.path.join(preview_dir, f"{video_id}.webm")
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor,
            VideoProcessor._run_preview,
            video_id, file_path, preview_path, duration
        )
