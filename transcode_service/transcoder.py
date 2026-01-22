"""
FFmpeg转码封装 - 优化版
支持：预设优化、预计时间估算
"""
import os
import subprocess
import re
import shutil
from typing import Callable, Optional, Tuple
from datetime import datetime

from config import FFMPEG, DIRS


class Transcoder:
    def __init__(self, progress_callback: Optional[Callable[[float], None]] = None,
                 is_short: bool = False):
        self.progress_callback = progress_callback
        self.is_short = is_short
        # 根据视频类型选择预设
        self.preset = FFMPEG["preset_short"] if is_short else FFMPEG["preset_long"]
    
    def get_video_info(self, video_path: str) -> Tuple[float, int]:
        """获取视频时长和高度"""
        duration = 0.0
        height = 720
        
        # 获取时长
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", video_path],
                capture_output=True, text=True, encoding="utf-8", timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                duration_str = result.stdout.strip().split('\n')[0]
                duration = float(duration_str)
                print(f"[VideoInfo] Duration: {duration:.2f}s from ffprobe")
            else:
                print(f"[VideoInfo] ffprobe duration failed: returncode={result.returncode}, stderr={result.stderr[:200] if result.stderr else 'none'}")
        except Exception as e:
            print(f"[VideoInfo] Duration error: {e}")
        
        # 如果 format=duration 失败，尝试从流信息获取
        if duration <= 0:
            try:
                result = subprocess.run(
                    ["ffprobe", "-v", "error", "-select_streams", "v:0",
                     "-show_entries", "stream=duration", "-of", "csv=p=0", video_path],
                    capture_output=True, text=True, encoding="utf-8", timeout=30
                )
                if result.returncode == 0 and result.stdout.strip():
                    duration_str = result.stdout.strip().split('\n')[0]
                    if duration_str and duration_str != 'N/A':
                        duration = float(duration_str)
                        print(f"[VideoInfo] Duration from stream: {duration:.2f}s")
            except Exception as e:
                print(f"[VideoInfo] Stream duration error: {e}")
        
        # 如果还是失败，使用 ffprobe 的 -count_frames 方式（较慢但更准确）
        if duration <= 0:
            try:
                result = subprocess.run(
                    ["ffprobe", "-v", "error", "-select_streams", "v:0",
                     "-show_entries", "stream=r_frame_rate,nb_frames", "-of", "csv=p=0", video_path],
                    capture_output=True, text=True, encoding="utf-8", timeout=60
                )
                if result.returncode == 0 and result.stdout.strip():
                    lines = result.stdout.strip().split('\n')
                    if lines:
                        parts = lines[0].split(',')
                        if len(parts) >= 2:
                            fps_str = parts[0]  # e.g., "30/1"
                            nb_frames = parts[1]
                            if '/' in fps_str and nb_frames.isdigit():
                                fps_parts = fps_str.split('/')
                                fps = float(fps_parts[0]) / float(fps_parts[1])
                                duration = int(nb_frames) / fps
                                print(f"[VideoInfo] Duration from frames: {duration:.2f}s (fps={fps}, frames={nb_frames})")
            except Exception as e:
                print(f"[VideoInfo] Frame count error: {e}")
        
        # 获取高度
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0",
                 "-show_entries", "stream=height", "-of", "csv=p=0", video_path],
                capture_output=True, text=True, encoding="utf-8", timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                height = int(result.stdout.strip().split('\n')[0])
                print(f"[VideoInfo] Height: {height}p")
        except Exception as e:
            print(f"[VideoInfo] Height error: {e}")
        
        # 最终检查
        if duration <= 0:
            print(f"[VideoInfo] WARNING: Could not determine duration for {video_path}, using 0")
        
        return duration, height
    
    def estimate_transcode_time(self, duration: float, height: int) -> float:
        """估算转码时间（秒）"""
        # 基础系数：视频时长的倍数
        if self.is_short:
            # 短视频用veryfast，大约0.3-0.5倍实时
            base_factor = 0.4
        else:
            # 长视频用medium，大约0.8-1.2倍实时
            base_factor = 1.0
        
        # 分辨率系数
        if height >= 1080:
            res_factor = 1.5
        elif height >= 720:
            res_factor = 1.0
        else:
            res_factor = 0.7
        
        # 估算时间 = 视频时长 * 基础系数 * 分辨率系数 + 封面生成时间(30s) + 上传时间估算
        estimated = duration * base_factor * res_factor + 30 + (duration * 0.1)
        
        return estimated
    
    def generate_hls(self, video_path: str, output_dir: str, 
                     duration: float, height: int) -> str:
        """生成HLS流"""
        hls_dir = os.path.join(output_dir, "hls")
        os.makedirs(hls_dir, exist_ok=True)
        
        res_name = f"{height}p"
        res_dir = os.path.join(hls_dir, res_name)
        os.makedirs(res_dir, exist_ok=True)
        
        playlist_path = os.path.join(res_dir, "playlist.m3u8")
        segment_pattern = os.path.join(res_dir, "seg_%03d.ts")
        
        # 根据分辨率选择码率
        if height >= 1080:
            bitrate = "4000k"
            maxrate = "4500k"
            bufsize = "8000k"
        elif height >= 720:
            bitrate = "2500k"
            maxrate = "3000k"
            bufsize = "5000k"
        elif height >= 480:
            bitrate = "1200k"
            maxrate = "1500k"
            bufsize = "2400k"
        else:
            bitrate = "800k"
            maxrate = "1000k"
            bufsize = "1600k"
        
        # FFmpeg命令 - 优化版（添加多线程和tune参数）
        cmd = [
            "ffmpeg", "-y", 
            "-threads", str(FFMPEG.get("threads", 0)),  # 多线程解码
            "-i", video_path,
            "-c:v", "libx264", 
            "-preset", self.preset,
            "-tune", "fastdecode",  # 优化解码速度，播放更流畅
            "-crf", str(FFMPEG["crf"]),
            "-maxrate", maxrate,
            "-bufsize", bufsize,
            "-threads", str(FFMPEG.get("threads", 0)),  # 多线程编码
            "-c:a", "aac", "-b:a", FFMPEG["audio_bitrate"],
            "-movflags", "+faststart",
            "-f", "hls", 
            "-hls_time", str(FFMPEG["hls_time"]), 
            "-hls_list_size", "0",
            "-hls_segment_filename", segment_pattern,
            playlist_path
        ]
        
        self._run_ffmpeg_with_progress(cmd, duration, f"HLS {res_name}")
        
        # 创建master.m3u8
        master_path = os.path.join(hls_dir, "master.m3u8")
        bandwidth = int(bitrate.replace("k", "")) * 1000
        width = int(height * 16 / 9)
        
        with open(master_path, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            f.write("#EXT-X-VERSION:3\n")
            f.write(f"#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION={width}x{height}\n")
            f.write(f"{res_name}/playlist.m3u8\n")
        
        return hls_dir
    
    def generate_covers(self, video_path: str, output_dir: str, 
                        duration: float) -> Tuple[str, int]:
        """生成封面图片（并行优化版），返回封面目录和最佳封面索引"""
        import concurrent.futures
        
        covers_dir = os.path.join(output_dir, "covers")
        os.makedirs(covers_dir, exist_ok=True)
        
        count = FFMPEG["cover_count"]
        
        def generate_single_cover(args):
            """生成单张封面"""
            i, position = args
            cover_path = os.path.join(covers_dir, f"cover_{i}.webp")
            
            # -ss 放在 -i 前面可以快速 seek
            cmd = [
                "ffmpeg", "-y", 
                "-ss", str(position),
                "-i", video_path,
                "-vframes", "1", 
                "-vf", "scale=640:-1",
                "-c:v", "libwebp", 
                "-quality", str(FFMPEG["cover_quality"]),
                cover_path
            ]
            
            try:
                subprocess.run(cmd, capture_output=True, timeout=30)
                return i, os.path.exists(cover_path)
            except Exception as e:
                print(f"[Cover] 封面 {i} 生成失败: {e}")
                return i, False
        
        # 准备参数
        tasks = []
        for i in range(1, count + 1):
            position = duration * (i / (count + 1))
            tasks.append((i, position))
        
        # 并行生成（最多4个线程）
        print(f"[Cover] 并行生成 {count} 张封面...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, count)) as executor:
            results = list(executor.map(generate_single_cover, tasks))
        
        success_count = sum(1 for _, ok in results if ok)
        print(f"[Cover] 封面生成完成: {success_count}/{count}")
        
        # 选择最佳封面
        best_cover = self._select_best_cover(covers_dir)
        
        return covers_dir, best_cover
    
    def _select_best_cover(self, covers_dir: str) -> int:
        """
        智能选择最佳封面
        综合评估：清晰度、对比度、亮度、色彩丰富度、位置权重
        """
        try:
            # 尝试使用 PIL 进行图像质量分析
            from PIL import Image
            import numpy as np
            return self._select_best_cover_smart(covers_dir)
        except ImportError:
            print("[Cover] PIL/numpy 未安装，使用简单选择")
            return self._select_best_cover_simple(covers_dir)
    
    def _select_best_cover_simple(self, covers_dir: str) -> int:
        """简单选择（文件大小+位置权重）- 备用方案"""
        best_cover = 5
        max_score = 0
        
        for i in range(1, 11):
            cover_path = os.path.join(covers_dir, f"cover_{i}.webp")
            if os.path.exists(cover_path):
                size = os.path.getsize(cover_path)
                position_bonus = 1.2 if 4 <= i <= 7 else 1.0
                score = size * position_bonus
                
                if score > max_score:
                    max_score = score
                    best_cover = i
        
        return best_cover
    
    def _select_best_cover_smart(self, covers_dir: str) -> int:
        """
        智能封面选择 - 使用图像质量分析
        评分维度：
        1. 清晰度（拉普拉斯方差）- 越高越清晰
        2. 对比度（标准差）- 适中最好
        3. 亮度（平均值）- 适中最好，避免过暗过亮
        4. 色彩丰富度（颜色方差）- 越高越好
        5. 位置权重 - 中间位置加分
        """
        from PIL import Image
        import numpy as np
        
        scores = {}
        details = {}
        
        for i in range(1, 11):
            cover_path = os.path.join(covers_dir, f"cover_{i}.webp")
            if not os.path.exists(cover_path):
                continue
            
            try:
                img = Image.open(cover_path)
                img_array = np.array(img.convert('RGB'))
                gray = np.array(img.convert('L'))
                
                # 1. 清晰度 - 使用简化的拉普拉斯算子
                # 计算相邻像素差异的方差
                dx = np.diff(gray.astype(float), axis=1)
                dy = np.diff(gray.astype(float), axis=0)
                sharpness = np.var(dx) + np.var(dy)
                
                # 2. 对比度 - 灰度标准差
                contrast = np.std(gray)
                
                # 3. 亮度 - 灰度平均值（最佳范围 80-180）
                brightness = np.mean(gray)
                # 亮度评分：越接近130越好
                brightness_score = 100 - abs(brightness - 130) * 0.8
                brightness_score = max(0, brightness_score)
                
                # 4. 色彩丰富度 - RGB通道的方差之和
                color_var = np.var(img_array[:,:,0]) + np.var(img_array[:,:,1]) + np.var(img_array[:,:,2])
                
                # 5. 位置权重 - 中间位置（4-7）加分
                position_bonus = 1.15 if 4 <= i <= 7 else 1.0
                
                # 6. 检测是否为黑屏/白屏/纯色
                is_bad_frame = False
                if contrast < 15:  # 对比度太低，可能是纯色
                    is_bad_frame = True
                if brightness < 30 or brightness > 230:  # 太暗或太亮
                    is_bad_frame = True
                
                # 综合评分（归一化后加权）
                # 清晰度权重最高，其次是色彩和对比度
                score = (
                    sharpness * 0.35 +           # 清晰度 35%
                    contrast * 10 * 0.20 +       # 对比度 20%
                    brightness_score * 10 * 0.15 + # 亮度 15%
                    color_var * 0.001 * 0.20 +   # 色彩 20%
                    100 * 0.10                   # 基础分 10%
                ) * position_bonus
                
                # 坏帧惩罚
                if is_bad_frame:
                    score *= 0.3
                
                scores[i] = score
                details[i] = {
                    'sharpness': sharpness,
                    'contrast': contrast,
                    'brightness': brightness,
                    'color_var': color_var,
                    'is_bad': is_bad_frame
                }
                
            except Exception as e:
                print(f"[Cover] 分析封面 {i} 失败: {e}")
                scores[i] = 0
        
        if not scores:
            return 5
        
        # 选择得分最高的
        best_cover = max(scores, key=scores.get)
        
        # 打印分析结果
        print(f"[Cover] 智能分析结果:")
        for i in sorted(scores.keys()):
            d = details.get(i, {})
            mark = " ★" if i == best_cover else ""
            bad = " [差]" if d.get('is_bad') else ""
            print(f"  封面{i}: 分数={scores[i]:.1f}, 清晰={d.get('sharpness', 0):.0f}, "
                  f"对比={d.get('contrast', 0):.1f}, 亮度={d.get('brightness', 0):.0f}{bad}{mark}")
        
        return best_cover
    
    def generate_preview(self, video_path: str, output_dir: str, 
                         duration: float, name: str) -> Optional[str]:
        """
        生成分段预览视频（优化版）
        5段，每段2秒，均匀分布在整个视频中
        使用 H.264 编码 + 并行生成 + copy模式快速截取
        """
        import concurrent.futures
        import tempfile
        
        preview_path = os.path.join(output_dir, f"{name}_preview.webm")
        
        # 计算分段参数
        num_segments = 5
        seg_duration = 2.0  # 每段2秒
        
        if duration < 10:
            # 短视频：按视频时长调整
            num_segments = max(1, int(duration / 2))
            seg_duration = min(2.0, duration / num_segments) if num_segments > 0 else duration
        
        # 计算每段的起始位置（5%~95%均匀分布，避开片头片尾）
        segments = []
        for i in range(num_segments):
            if num_segments > 1:
                position = 0.05 + (0.9 * i / (num_segments - 1))
            else:
                position = 0.5
            start_time = duration * position
            
            # 确保不超过视频末尾
            if start_time + seg_duration > duration:
                start_time = max(0, duration - seg_duration)
            
            segments.append((i, start_time, seg_duration))
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="preview_")
        temp_files = []
        
        try:
            print(f"[Preview] 生成分段预览: {num_segments}段 x {seg_duration}秒")
            
            # 并行生成各分段（使用 copy 模式快速截取，然后统一编码）
            def generate_segment(args):
                idx, start_time, seg_dur = args
                # 先用 copy 模式快速截取原始片段
                raw_path = os.path.join(temp_dir, f"raw_{idx}.mp4")
                cmd_copy = [
                    "ffmpeg", "-y",
                    "-ss", str(start_time),
                    "-i", video_path,
                    "-t", str(seg_dur),
                    "-c", "copy",  # 直接复制，不重编码
                    "-an",
                    raw_path
                ]
                result = subprocess.run(cmd_copy, capture_output=True, timeout=30)
                
                if result.returncode != 0 or not os.path.exists(raw_path):
                    # copy 失败，直接编码
                    seg_path = os.path.join(temp_dir, f"seg_{idx}.mp4")
                    cmd_encode = [
                        "ffmpeg", "-y",
                        "-ss", str(start_time),
                        "-i", video_path,
                        "-t", str(seg_dur),
                        "-c:v", "libx264",
                        "-preset", "ultrafast",
                        "-crf", "28",
                        "-vf", "scale=480:-2",
                        "-an",
                        seg_path
                    ]
                    subprocess.run(cmd_encode, capture_output=True, timeout=60)
                    return seg_path if os.path.exists(seg_path) else None
                
                # 重编码为统一格式
                seg_path = os.path.join(temp_dir, f"seg_{idx}.mp4")
                cmd_encode = [
                    "ffmpeg", "-y",
                    "-i", raw_path,
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-crf", "28",
                    "-vf", "scale=480:-2",
                    "-an",
                    seg_path
                ]
                subprocess.run(cmd_encode, capture_output=True, timeout=60)
                
                # 清理原始片段
                if os.path.exists(raw_path):
                    os.remove(raw_path)
                
                return seg_path if os.path.exists(seg_path) else None
            
            # 使用线程池并行生成
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, num_segments)) as executor:
                results = list(executor.map(generate_segment, segments))
            
            # 收集成功的分段
            temp_files = [r for r in results if r and os.path.exists(r)]
            
            if not temp_files:
                print("[Preview] 所有分段生成失败")
                return None
            
            print(f"[Preview] 成功生成 {len(temp_files)}/{num_segments} 个分段")
            
            # 创建拼接列表文件
            concat_file = os.path.join(temp_dir, "concat.txt")
            with open(concat_file, 'w', encoding='utf-8') as f:
                for seg_path in sorted(temp_files):
                    # Windows 路径转换
                    safe_path = seg_path.replace('\\', '/')
                    f.write(f"file '{safe_path}'\n")
            
            # 拼接并转换为 WebM（VP9 体积更小，兼容性好）
            concat_cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c:v", "libvpx-vp9",
                "-b:v", "500k",
                "-vf", "scale=480:-2",
                preview_path
            ]
            
            print(f"[Preview] 拼接 {len(temp_files)} 个分段...")
            concat_result = subprocess.run(concat_cmd, capture_output=True, timeout=120)
            
            if concat_result.returncode == 0 and os.path.exists(preview_path):
                size_kb = os.path.getsize(preview_path) / 1024
                total_duration = len(temp_files) * seg_duration
                print(f"[Preview] 分段预览生成成功: {len(temp_files)}段，共{total_duration:.1f}秒，{size_kb:.1f}KB")
                return preview_path
            else:
                print(f"[Preview] 拼接失败: {concat_result.stderr.decode('utf-8', errors='ignore')[:200]}")
                return None
                
        except Exception as e:
            print(f"[Preview] 生成异常: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            # 清理临时文件
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
    
    def _run_ffmpeg_with_progress(self, cmd: list, duration: float, task_name: str):
        """运行FFmpeg并报告进度"""
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding="utf-8",
            errors="replace"
        )
        
        time_pattern = re.compile(r"time=(\d+):(\d+):(\d+\.?\d*)")
        
        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                break
            
            match = time_pattern.search(line)
            if match and self.progress_callback:
                hours, minutes, seconds = match.groups()
                current_time = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                progress = min(100, (current_time / duration) * 100)
                self.progress_callback(progress)
        
        process.wait()
        
        if self.progress_callback:
            self.progress_callback(100)
