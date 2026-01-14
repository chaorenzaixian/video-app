"""
Windows 媒体处理服务
独立部署在 GPU 服务器上
"""
import os
import subprocess
import asyncio
import aiohttp
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uuid
import logging
from pathlib import Path

# 配置
MEDIA_ROOT = Path("D:/media")
UPLOAD_DIR = MEDIA_ROOT / "uploads"
VIDEO_DIR = MEDIA_ROOT / "videos"
HLS_DIR = MEDIA_ROOT / "hls"
THUMBNAIL_DIR = MEDIA_ROOT / "thumbnails"
IMAGE_DIR = MEDIA_ROOT / "images"

# 主服务器回调地址
MAIN_SERVER_CALLBACK = "https://your-main-server.com/api/v1/media/callback"

# 创建目录
for d in [UPLOAD_DIR, VIDEO_DIR, HLS_DIR, THUMBNAIL_DIR, IMAGE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="媒体处理服务")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranscodeRequest(BaseModel):
    video_id: str
    source_url: str  # 原始视频URL或本地路径
    callback_url: Optional[str] = None
    resolutions: list = ["1080p", "720p", "480p"]
    use_gpu: bool = True


class ImageProcessRequest(BaseModel):
    image_id: str
    source_url: str
    operations: list = ["compress", "watermark", "thumbnail"]
    callback_url: Optional[str] = None


# ==================== 视频处理 ====================

def get_ffmpeg_cmd(input_path: str, output_path: str, resolution: str, use_gpu: bool = True):
    """生成 FFmpeg 命令"""
    res_map = {
        "1080p": ("1920", "1080", "5M"),
        "720p": ("1280", "720", "3M"),
        "480p": ("854", "480", "1.5M"),
        "360p": ("640", "360", "800k"),
    }
    
    width, height, bitrate = res_map.get(resolution, res_map["720p"])
    
    if use_gpu:
        # NVIDIA GPU 加速
        cmd = [
            "ffmpeg", "-y",
            "-hwaccel", "cuda",
            "-i", input_path,
            "-c:v", "h264_nvenc",
            "-preset", "fast",
            "-b:v", bitrate,
            "-vf", f"scale={width}:{height}",
            "-c:a", "aac",
            "-b:a", "128k",
            output_path
        ]
    else:
        # CPU 编码
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-c:v", "libx264",
            "-preset", "fast",
            "-b:v", bitrate,
            "-vf", f"scale={width}:{height}",
            "-c:a", "aac",
            "-b:a", "128k",
            output_path
        ]
    
    return cmd


def generate_hls(input_path: str, output_dir: str, use_gpu: bool = True):
    """生成 HLS 切片"""
    os.makedirs(output_dir, exist_ok=True)
    
    if use_gpu:
        cmd = [
            "ffmpeg", "-y",
            "-hwaccel", "cuda",
            "-i", input_path,
            "-c:v", "h264_nvenc",
            "-preset", "fast",
            "-c:a", "aac",
            "-hls_time", "10",
            "-hls_list_size", "0",
            "-hls_segment_filename", f"{output_dir}/segment_%03d.ts",
            f"{output_dir}/playlist.m3u8"
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            "-hls_time", "10",
            "-hls_list_size", "0",
            "-hls_segment_filename", f"{output_dir}/segment_%03d.ts",
            f"{output_dir}/playlist.m3u8"
        ]
    
    subprocess.run(cmd, check=True)
    return f"{output_dir}/playlist.m3u8"


def generate_thumbnail(input_path: str, output_path: str, time: str = "00:00:05"):
    """生成视频缩略图"""
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-ss", time,
        "-vframes", "1",
        "-vf", "scale=320:-1",
        output_path
    ]
    subprocess.run(cmd, check=True)
    return output_path


async def process_video(request: TranscodeRequest):
    """处理视频转码任务"""
    video_id = request.video_id
    logger.info(f"开始处理视频: {video_id}")
    
    try:
        # 下载原始视频
        source_path = UPLOAD_DIR / f"{video_id}_source.mp4"
        if request.source_url.startswith("http"):
            async with aiohttp.ClientSession() as session:
                async with session.get(request.source_url) as resp:
                    with open(source_path, "wb") as f:
                        f.write(await resp.read())
        else:
            source_path = Path(request.source_url)
        
        results = {"video_id": video_id, "files": {}}
        
        # 转码多个分辨率
        for res in request.resolutions:
            output_path = VIDEO_DIR / f"{video_id}_{res}.mp4"
            cmd = get_ffmpeg_cmd(str(source_path), str(output_path), res, request.use_gpu)
            subprocess.run(cmd, check=True)
            results["files"][res] = str(output_path)
            logger.info(f"完成 {res} 转码")
        
        # 生成 HLS
        hls_dir = HLS_DIR / video_id
        hls_path = generate_hls(str(source_path), str(hls_dir), request.use_gpu)
        results["files"]["hls"] = hls_path
        logger.info("完成 HLS 切片")
        
        # 生成缩略图
        thumb_path = THUMBNAIL_DIR / f"{video_id}.jpg"
        generate_thumbnail(str(source_path), str(thumb_path))
        results["files"]["thumbnail"] = str(thumb_path)
        logger.info("完成缩略图生成")
        
        results["status"] = "success"
        
        # 回调主服务器
        if request.callback_url:
            async with aiohttp.ClientSession() as session:
                await session.post(request.callback_url, json=results)
        
        return results
        
    except Exception as e:
        logger.error(f"视频处理失败: {e}")
        error_result = {"video_id": video_id, "status": "failed", "error": str(e)}
        if request.callback_url:
            async with aiohttp.ClientSession() as session:
                await session.post(request.callback_url, json=error_result)
        raise


# ==================== 图片处理 ====================

def compress_image(input_path: str, output_path: str, quality: int = 85):
    """压缩图片"""
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-q:v", str(quality),
        output_path
    ]
    subprocess.run(cmd, check=True)
    return output_path


def add_watermark(input_path: str, output_path: str, watermark_path: str):
    """添加水印"""
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-i", watermark_path,
        "-filter_complex", "overlay=W-w-10:H-h-10",
        output_path
    ]
    subprocess.run(cmd, check=True)
    return output_path


def create_image_thumbnail(input_path: str, output_path: str, size: str = "200x200"):
    """生成图片缩略图"""
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", f"scale={size.replace('x', ':')}:force_original_aspect_ratio=decrease",
        output_path
    ]
    subprocess.run(cmd, check=True)
    return output_path


# ==================== API 接口 ====================

@app.post("/api/transcode")
async def transcode_video(request: TranscodeRequest, background_tasks: BackgroundTasks):
    """提交视频转码任务"""
    background_tasks.add_task(process_video, request)
    return {"message": "任务已提交", "video_id": request.video_id}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件"""
    file_id = str(uuid.uuid4())
    ext = Path(file.filename).suffix
    save_path = UPLOAD_DIR / f"{file_id}{ext}"
    
    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    return {"file_id": file_id, "path": str(save_path)}


@app.get("/api/file/{file_type}/{filename}")
async def get_file(file_type: str, filename: str):
    """获取处理后的文件"""
    dir_map = {
        "video": VIDEO_DIR,
        "hls": HLS_DIR,
        "thumbnail": THUMBNAIL_DIR,
        "image": IMAGE_DIR,
    }
    
    if file_type not in dir_map:
        raise HTTPException(status_code=400, detail="无效的文件类型")
    
    file_path = dir_map[file_type] / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(file_path)


@app.get("/api/health")
async def health_check():
    """健康检查"""
    # 检查 GPU 状态
    try:
        result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
        gpu_available = result.returncode == 0
    except:
        gpu_available = False
    
    return {
        "status": "healthy",
        "gpu_available": gpu_available,
        "storage": {
            "uploads": len(list(UPLOAD_DIR.glob("*"))),
            "videos": len(list(VIDEO_DIR.glob("*"))),
            "thumbnails": len(list(THUMBNAIL_DIR.glob("*"))),
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
