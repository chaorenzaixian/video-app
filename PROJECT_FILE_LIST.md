# 视频平台项目文件明细

## 项目概述
这是一个完整的视频平台系统，包含：
- 后端API服务 (FastAPI/Python)
- 前端管理后台 (Vue.js)
- 移动端APP (Flutter)
- 视频转码服务 (Windows)

---

## 一、后端服务 (backend/)

### 核心文件
| 文件 | 说明 |
|------|------|
| `backend/app/main.py` | FastAPI应用入口 |
| `backend/run.py` | 启动脚本 |
| `backend/requirements.txt` | Python依赖 |
| `backend/.env` | 环境配置 |
| `backend/alembic.ini` | 数据库迁移配置 |

### API模块 (backend/app/api/)
| 文件 | 说明 |
|------|------|
| `admin.py` | 管理后台API |
| `admin_video_ops.py` | 视频批量操作API |
| `admin_darkweb.py` | 暗网视频管理API |
| `admin_community.py` | 社区管理API |
| `admin_dating.py` | 交友管理API |
| `admin_gallery_novel.py` | 图库/小说管理API |
| `admin_coins.py` | 金币管理API |
| `admin_finance.py` | 财务管理API |
| `auth.py` | 用户认证API |
| `users.py` | 用户API |
| `videos.py` | 视频API |
| `shorts.py` | 短视频API |
| `comments.py` | 评论API |
| `community.py` | 社区API |
| `darkweb.py` | 暗网视频API |
| `dating.py` | 交友API |
| `gallery_novel.py` | 图库/小说API |
| `payments.py` | 支付API |
| `vip.py` | VIP会员API |
| `coins.py` | 金币API |
| `home.py` | 首页API |
| `transcode_callback.py` | 转码回调API |
| `download_page.py` | 下载页管理API |

### 数据模型 (backend/app/models/)
| 文件 | 说明 |
|------|------|
| `user.py` | 用户模型 |
| `video.py` | 视频模型 |
| `comment.py` | 评论模型 |
| `community.py` | 社区模型 |
| `darkweb.py` | 暗网视频模型 |
| `dating.py` | 交友模型 |
| `content.py` | 内容模型 |
| `payment.py` | 支付模型 |
| `vip.py` | VIP模型 |
| `coins.py` | 金币模型 |
| `ad.py` | 广告模型 |

### 服务层 (backend/app/services/)
| 文件 | 说明 |
|------|------|
| `video_processor.py` | 视频处理服务 |
| `payment_service.py` | 支付服务 |
| `cache_service.py` | 缓存服务 |
| `comment_service.py` | 评论服务 |
| `audit_service.py` | 审计服务 |
| `gpu_transcode_service.py` | GPU转码服务 |
| `windows_transcode_service.py` | Windows转码服务 |

### 核心模块 (backend/app/core/)
| 文件 | 说明 |
|------|------|
| `config.py` | 配置管理 |
| `database.py` | 数据库连接 |
| `security.py` | 安全模块 |
| `redis.py` | Redis连接 |
| `vip_config.py` | VIP配置 |

---

## 二、前端管理后台 (frontend/)

### 核心文件
| 文件 | 说明 |
|------|------|
| `frontend/src/main.js` | Vue应用入口 |
| `frontend/src/App.vue` | 根组件 |
| `frontend/package.json` | NPM依赖 |
| `frontend/vite.config.js` | Vite配置 |
| `frontend/index.html` | HTML入口 |

### 主要目录
| 目录 | 说明 |
|------|------|
| `frontend/src/views/` | 页面组件 |
| `frontend/src/components/` | 公共组件 |
| `frontend/src/router/` | 路由配置 |
| `frontend/src/stores/` | 状态管理 |
| `frontend/src/utils/` | 工具函数 |
| `frontend/src/styles/` | 样式文件 |

---

## 三、移动端APP (flutter/)

### 核心文件
| 文件 | 说明 |
|------|------|
| `flutter/lib/main.dart` | Flutter应用入口 |
| `flutter/pubspec.yaml` | Flutter依赖 |

### 主要目录
| 目录 | 说明 |
|------|------|
| `flutter/lib/screens/` | 页面 |
| `flutter/lib/models/` | 数据模型 |
| `flutter/lib/services/` | 服务层 |
| `flutter/lib/providers/` | 状态管理 |
| `flutter/lib/widgets/` | 组件 |
| `flutter/lib/utils/` | 工具 |
| `flutter/lib/core/` | 核心模块 |
| `flutter/lib/features/` | 功能模块 |

### 平台配置
| 目录 | 说明 |
|------|------|
| `flutter/android/` | Android配置 |
| `flutter/ios/` | iOS配置 |
| `flutter/web/` | Web配置 |

---

## 四、转码服务 (transcode_service/) ⭐重要

### 核心文件（部署到Windows转码服务器）
| 文件 | 说明 | 必需 |
|------|------|------|
| `transcode_service/web_ui.py` | Web管理界面和API | ✅ |
| `transcode_service/config.py` | 配置文件 | ✅ |
| `transcode_service/transcoder.py` | 转码核心逻辑 | ✅ |
| `transcode_service/uploader.py` | 文件上传模块 | ✅ |
| `transcode_service/task_queue.py` | 任务队列管理 | ✅ |
| `transcode_service/requirements.txt` | Python依赖 | ✅ |
| `transcode_service/templates/index.html` | Web界面模板 | ✅ |
| `transcode_service/worker.py` | 工作进程 | 可选 |
| `transcode_service/service.py` | Windows服务 | 可选 |
| `transcode_service/callback.py` | 回调处理 | 可选 |

### 转码服务部署说明
```
部署路径: D:\VideoTranscode\service\
访问地址: http://198.176.60.121:8080

目录结构:
D:\VideoTranscode\
├── service/          # 转码服务代码
│   ├── web_ui.py
│   ├── config.py
│   ├── transcoder.py
│   ├── uploader.py
│   ├── task_queue.py
│   ├── requirements.txt
│   └── templates/
│       └── index.html
├── processing/       # 处理中的视频
├── downloads/        # 下载目录
│   ├── long/        # 长视频
│   ├── short/       # 短视频
│   └── darkweb/     # 暗网视频
├── completed/        # 已完成
├── logs/            # 日志
└── data/            # 数据库
```

---

## 五、部署脚本 (scripts/)

### 常用脚本
| 文件 | 说明 |
|------|------|
| `scripts/upload_and_restart.py` | 上传转码服务并重启 |
| `scripts/check_publish_status.py` | 检查发布状态 |
| `scripts/guardian.ps1` | 服务守护进程 |

### 部署文件 (deploy_files/)
| 文件 | 说明 |
|------|------|
| `deploy_files/upload_to_main.ps1` | 上传到主服务器 |
| `deploy_files/watcher.ps1` | 文件监控脚本 |

---

## 六、配置文件

### 服务器密钥
| 文件 | 说明 |
|------|------|
| `server_key_main` | 主服务器SSH密钥 |
| `server_key` | 转码服务器SSH密钥 |

### Docker配置
| 文件 | 说明 |
|------|------|
| `docker-compose.yml` | Docker编排 |
| `docker-compose.dev.yml` | 开发环境Docker |

### Nginx配置
| 文件 | 说明 |
|------|------|
| `nginx_default.conf` | Nginx默认配置 |
| `nginx_transcode_proxy.conf` | 转码代理配置 |

---

## 七、服务器信息

### 主服务器
- IP: `38.47.218.137`
- SSH密钥: `server_key_main`
- 后端路径: `/www/wwwroot/video-app/backend/`
- 后端端口: 5000 (通过Nginx 80端口代理)

### 转码服务器
- IP: `198.176.60.121`
- 用户: `Administrator`
- 密码: `jCkMIjNlnSd7f6GM`
- 服务路径: `D:\VideoTranscode\service\`
- Web端口: 8080

---

## 八、快速部署命令

### 更新转码服务
```bash
python scripts/upload_and_restart.py
```

### 更新后端API
```bash
scp -i server_key_main backend/app/api/xxx.py root@38.47.218.137:/www/wwwroot/video-app/backend/app/api/
# 然后重启uvicorn
```

### 检查服务状态
```bash
python scripts/check_publish_status.py
```

---

## 九、文件统计

| 模块 | 文件数 | 说明 |
|------|--------|------|
| backend/app/api/ | 50+ | API接口 |
| backend/app/models/ | 20+ | 数据模型 |
| backend/app/services/ | 15+ | 服务层 |
| frontend/src/ | 100+ | 前端代码 |
| flutter/lib/ | 80+ | 移动端代码 |
| transcode_service/ | 10 | 转码服务 |
| scripts/ | 150+ | 脚本工具 |

---

*文档生成时间: 2026-01-22*
