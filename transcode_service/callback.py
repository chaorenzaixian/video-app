"""
API回调模块
"""
import json
import urllib.request
import urllib.error
import logging
from typing import Optional

from config import MAIN_SERVER

logger = logging.getLogger(__name__)


class CallbackClient:
    def __init__(self):
        self.api_base = MAIN_SERVER["api_base"]
        self.transcode_key = MAIN_SERVER["transcode_key"]
    
    def send_completion(self, filename: str, title: str, is_short: bool,
                        duration: float, hls_url: str = "", cover_url: str = "",
                        preview_url: str = "") -> bool:
        """发送转码完成回调"""
        url = f"{self.api_base}/admin/videos/import-from-transcode"
        
        data = {
            "filename": filename,
            "title": title,
            "is_short": is_short,
            "duration": duration,
        }
        
        if hls_url:
            data["hls_url"] = hls_url
        if cover_url:
            data["cover_url"] = cover_url
        if preview_url:
            data["preview_url"] = preview_url
        
        try:
            json_data = json.dumps(data).encode("utf-8")
            
            request = urllib.request.Request(
                url,
                data=json_data,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "X-Transcode-Key": self.transcode_key,
                },
                method="POST"
            )
            
            with urllib.request.urlopen(request, timeout=30) as response:
                result = response.read().decode("utf-8")
                logger.info(f"回调成功: {result}")
                return True
                
        except urllib.error.HTTPError as e:
            logger.error(f"回调HTTP错误: {e.code} - {e.read().decode()}")
        except urllib.error.URLError as e:
            logger.error(f"回调网络错误: {e.reason}")
        except Exception as e:
            logger.error(f"回调异常: {e}")
        
        return False
    
    def report_progress(self, task_id: int, progress: float, status: str):
        """报告转码进度（可选，用于实时监控）"""
        # 可以扩展为WebSocket或轮询接口
        pass
