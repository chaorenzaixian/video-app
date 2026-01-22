"""
Windows服务主程序
可以作为Windows服务运行，也可以直接运行
"""
import sys
import os
import time
import logging
import threading
from logging.handlers import RotatingFileHandler

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DIRS, SERVICE, ensure_dirs
from worker import TranscodeWorker
from web_ui import run_web_ui

# 配置日志
def setup_logging():
    ensure_dirs()
    log_file = os.path.join(DIRS["logs"], "transcode_service.log")
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 文件处理器（轮转）
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return logging.getLogger(__name__)


# Windows服务支持
try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
    
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False


if HAS_WIN32:
    class TranscodeService(win32serviceutil.ServiceFramework):
        _svc_name_ = SERVICE["name"]
        _svc_display_name_ = SERVICE["display_name"]
        _svc_description_ = SERVICE["description"]
        
        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.stop_event = win32event.CreateEvent(None, 0, 0, None)
            self.worker = None
            self.web_thread = None
            self.logger = setup_logging()
        
        def SvcStop(self):
            self.logger.info("服务停止请求")
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.stop_event)
            
            if self.worker:
                self.worker.stop()
        
        def SvcDoRun(self):
            self.logger.info("服务启动")
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )
            self.main()
        
        def main(self):
            # 启动Web界面
            self.web_thread = threading.Thread(
                target=run_web_ui,
                kwargs={'host': '0.0.0.0', 'port': SERVICE['web_port']},
                daemon=True
            )
            self.web_thread.start()
            self.logger.info(f"Web界面已启动: http://localhost:{SERVICE['web_port']}")
            
            # 启动转码工作线程
            self.worker = TranscodeWorker()
            worker_thread = threading.Thread(target=self.worker.run, daemon=True)
            worker_thread.start()
            self.logger.info("转码工作线程已启动")
            
            # 等待停止信号
            while True:
                rc = win32event.WaitForSingleObject(self.stop_event, 5000)
                if rc == win32event.WAIT_OBJECT_0:
                    break
            
            self.logger.info("服务已停止")


def run_standalone():
    """独立运行模式（非服务）"""
    logger = setup_logging()
    logger.info("="*50)
    logger.info("视频转码服务启动（独立模式）")
    logger.info("="*50)
    
    # 启动Web界面
    web_thread = threading.Thread(
        target=run_web_ui,
        kwargs={'host': '0.0.0.0', 'port': SERVICE['web_port']},
        daemon=True
    )
    web_thread.start()
    logger.info(f"Web管理界面: http://localhost:{SERVICE['web_port']}")
    
    # 启动转码工作线程
    worker = TranscodeWorker()
    
    try:
        worker.run()
    except KeyboardInterrupt:
        logger.info("收到停止信号")
        worker.stop()


def install_service():
    """安装Windows服务"""
    if not HAS_WIN32:
        print("错误: 需要安装 pywin32")
        print("运行: pip install pywin32")
        return
    
    try:
        win32serviceutil.InstallService(
            TranscodeService._svc_name_,
            TranscodeService._svc_name_,
            TranscodeService._svc_display_name_,
            startType=win32service.SERVICE_AUTO_START,
            description=TranscodeService._svc_description_
        )
        print(f"服务 {SERVICE['name']} 安装成功")
        print(f"启动服务: net start {SERVICE['name']}")
    except Exception as e:
        print(f"安装失败: {e}")


def uninstall_service():
    """卸载Windows服务"""
    if not HAS_WIN32:
        print("错误: 需要安装 pywin32")
        return
    
    try:
        win32serviceutil.RemoveService(SERVICE['name'])
        print(f"服务 {SERVICE['name']} 已卸载")
    except Exception as e:
        print(f"卸载失败: {e}")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        
        if cmd == 'install':
            install_service()
        elif cmd == 'uninstall':
            uninstall_service()
        elif cmd == 'debug':
            # 调试模式
            run_standalone()
        elif HAS_WIN32 and cmd in ('start', 'stop', 'restart'):
            # 服务控制
            win32serviceutil.HandleCommandLine(TranscodeService)
        else:
            print("用法:")
            print("  python service.py          - 独立运行")
            print("  python service.py install  - 安装为Windows服务")
            print("  python service.py uninstall- 卸载服务")
            print("  python service.py debug    - 调试模式运行")
    else:
        # 默认独立运行
        run_standalone()
