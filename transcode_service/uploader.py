"""
SCP上传模块 - 使用paramiko
"""
import os
import paramiko
from typing import Optional
import logging

from config import MAIN_SERVER

logger = logging.getLogger(__name__)


class Uploader:
    def __init__(self):
        self.host = MAIN_SERVER["host"]
        self.upload_base = MAIN_SERVER["upload_base"]
        self._client = None
        self._sftp = None
    
    def _connect(self):
        """建立SSH连接"""
        if self._client is not None:
            try:
                self._client.exec_command('echo ok', timeout=5)
                return True
            except:
                self._close()
        
        try:
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 尝试使用密钥文件
            key_path = MAIN_SERVER.get("ssh_key")
            if key_path and os.path.exists(key_path):
                self._client.connect(self.host, username='root', key_filename=key_path, timeout=30)
            else:
                # 使用默认密钥
                self._client.connect(self.host, username='root', timeout=30)
            
            self._sftp = self._client.open_sftp()
            logger.info(f"SSH连接成功: {self.host}")
            return True
        except Exception as e:
            logger.error(f"SSH连接失败: {e}")
            self._close()
            return False
    
    def _close(self):
        """关闭连接"""
        if self._sftp:
            try:
                self._sftp.close()
            except:
                pass
            self._sftp = None
        if self._client:
            try:
                self._client.close()
            except:
                pass
            self._client = None
    
    def _run_ssh(self, command: str) -> bool:
        """执行SSH命令"""
        if not self._connect():
            return False
        try:
            stdin, stdout, stderr = self._client.exec_command(command, timeout=60)
            stdout.read()
            return True
        except Exception as e:
            logger.error(f"SSH命令失败: {e}")
            return False
    
    def _mkdir_p(self, remote_path: str):
        """递归创建远程目录"""
        if not self._connect():
            return
        
        dirs = []
        while remote_path and remote_path != '/':
            try:
                self._sftp.stat(remote_path)
                break
            except:
                dirs.append(remote_path)
                remote_path = os.path.dirname(remote_path)
        
        for d in reversed(dirs):
            try:
                self._sftp.mkdir(d)
            except:
                pass
    
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """上传单个文件"""
        if not os.path.exists(local_path):
            logger.warning(f"文件不存在: {local_path}")
            return False
        
        if not self._connect():
            return False
        
        try:
            # 确保远程目录存在
            remote_dir = os.path.dirname(remote_path)
            self._mkdir_p(remote_dir)
            
            # 上传文件
            self._sftp.put(local_path, remote_path)
            logger.info(f"上传成功: {os.path.basename(local_path)}")
            return True
        except Exception as e:
            logger.error(f"上传失败: {local_path} - {e}")
            return False
    
    def upload_directory(self, local_dir: str, remote_dir: str) -> int:
        """上传整个目录，返回成功上传的文件数"""
        if not os.path.exists(local_dir):
            logger.warning(f"目录不存在: {local_dir}")
            return 0
        
        if not self._connect():
            return 0
        
        # 创建远程目录
        self._mkdir_p(remote_dir)
        
        upload_count = 0
        
        for root, dirs, files in os.walk(local_dir):
            for filename in files:
                local_path = os.path.join(root, filename)
                relative_path = os.path.relpath(local_path, local_dir)
                remote_path = f"{remote_dir}/{relative_path}".replace("\\", "/")
                
                try:
                    # 确保子目录存在
                    remote_subdir = os.path.dirname(remote_path)
                    self._mkdir_p(remote_subdir)
                    
                    # 上传
                    self._sftp.put(local_path, remote_path)
                    upload_count += 1
                except Exception as e:
                    logger.error(f"上传失败: {filename} - {e}")
        
        logger.info(f"目录上传完成: {upload_count} 个文件")
        return upload_count
    
    def set_permissions(self, remote_path: str, owner: str = "www:www"):
        """设置远程文件权限"""
        self._run_ssh(f'chown -R {owner} "{remote_path}"')
    
    def upload_hls(self, local_hls_dir: str, video_id: str) -> Optional[str]:
        """上传HLS目录，返回远程URL路径"""
        remote_dir = f"{self.upload_base}/hls/{video_id}"
        
        count = self.upload_directory(local_hls_dir, remote_dir)
        
        if count > 0:
            self.set_permissions(remote_dir)
            return f"/uploads/hls/{video_id}/master.m3u8"
        
        return None
    
    def upload_covers(self, local_covers_dir: str, video_id: str) -> Optional[str]:
        """上传封面目录"""
        remote_dir = f"{self.upload_base}/hls/{video_id}/covers"
        
        count = self.upload_directory(local_covers_dir, remote_dir)
        
        if count > 0:
            return f"/uploads/hls/{video_id}/covers"
        
        return None
    
    def upload_preview(self, local_preview: str) -> Optional[str]:
        """上传预览视频"""
        if not local_preview or not os.path.exists(local_preview):
            return None
        
        filename = os.path.basename(local_preview)
        remote_path = f"{self.upload_base}/previews/{filename}"
        
        if self.upload_file(local_preview, remote_path):
            self.set_permissions(f"{self.upload_base}/previews")
            return f"/uploads/previews/{filename}"
        
        return None

    # ========== 暗网视频上传方法 ==========
    
    def upload_darkweb_hls(self, local_hls_dir: str, video_id: str) -> Optional[str]:
        """上传暗网HLS目录，返回远程URL路径"""
        remote_dir = f"{self.upload_base}/darkweb_hls/{video_id}"
        
        count = self.upload_directory(local_hls_dir, remote_dir)
        
        if count > 0:
            self.set_permissions(remote_dir)
            return f"/uploads/darkweb_hls/{video_id}/master.m3u8"
        
        return None
    
    def upload_darkweb_covers(self, local_covers_dir: str, video_id: str) -> Optional[str]:
        """上传暗网封面目录"""
        remote_dir = f"{self.upload_base}/darkweb_hls/{video_id}/covers"
        
        count = self.upload_directory(local_covers_dir, remote_dir)
        
        if count > 0:
            return f"/uploads/darkweb_hls/{video_id}/covers"
        
        return None
    
    def upload_darkweb_preview(self, local_preview: str, video_id: str) -> Optional[str]:
        """上传暗网预览视频"""
        if not local_preview or not os.path.exists(local_preview):
            return None
        
        filename = os.path.basename(local_preview)
        remote_path = f"{self.upload_base}/darkweb_previews/{video_id}_{filename}"
        
        if self.upload_file(local_preview, remote_path):
            self.set_permissions(f"{self.upload_base}/darkweb_previews")
            return f"/uploads/darkweb_previews/{video_id}_{filename}"
        
        return None
