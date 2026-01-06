# 🎬 VOD Platform - 视频点播全栈分布式系统

## 📋 项目概述

一个完整的视频点播平台，包含以下功能模块：

| 模块 | 功能 |
|------|------|
| 视频系统 | 上传、转码HLS、AI分析、播放 |
| 评论系统 | 评论、回复、点赞 |
| 会员系统 | 包月/包季/包年/永久VIP |
| 邀请系统 | 邀请送VIP天数 |
| 转码系统 | H264 HLS自动转码、缩略图生成 |
| 广告系统 | 多位置广告投放 |
| 支付系统 | 支付宝/微信/Stripe接口 |
| 监控系统 | 服务器实时监控 |

## 🛠️ 技术栈

- **后端**: FastAPI + PostgreSQL + Redis + Celery
- **前端**: Vue 3 + Element Plus + ECharts
- **移动端**: Flutter (待开发)
- **视频处理**: FFmpeg
- **AI**: OpenAI API
- **部署**: Docker + Nginx

---

## 🚀 快速开始

### 方式一：Docker 一键部署（推荐）

```bash
# 1. 克隆项目
cd 视频app

# 2. 启动所有服务
docker-compose up -d

# 3. 访问
# 前端: http://localhost:3000
# 后端API: http://localhost:8000/api/docs
```

### 方式二：本地开发

#### 1️⃣ 环境准备

```bash
# 安装 PostgreSQL 15+
# 安装 Redis 7+
# 安装 FFmpeg
# 安装 Python 3.11+
# 安装 Node.js 18+
```

#### 2️⃣ 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
copy env.example .env
# 编辑 .env 文件，配置数据库等

# 启动服务
uvicorn app.main:app --reload --port 8000
```

#### 3️⃣ 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

#### 4️⃣ 访问系统

- 管理后台: http://localhost:3000
- API文档: http://localhost:8000/api/docs

---

## 📁 项目结构

```
视频app/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据库模型
│   │   ├── schemas/        # Pydantic模式
│   │   ├── services/       # 业务服务
│   │   └── main.py         # 入口文件
│   ├── uploads/            # 上传文件目录
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/               # Vue 前端
│   ├── src/
│   │   ├── views/         # 页面组件
│   │   ├── layouts/       # 布局组件
│   │   ├── stores/        # Pinia状态
│   │   ├── router/        # 路由配置
│   │   └── utils/         # 工具函数
│   ├── package.json
│   └── Dockerfile
│
├── flutter_app/           # Flutter 移动端 (待开发)
├── docker-compose.yml     # Docker编排
└── README.md
```

---

## 📝 开发流程

### 第一阶段：环境搭建（1天）
- [x] 安装 PostgreSQL、Redis、FFmpeg
- [x] 配置开发环境
- [x] 创建数据库

### 第二阶段：后端开发（5-7天）
- [x] 用户认证系统（注册/登录/JWT）
- [x] 视频上传与管理
- [x] 视频转码服务（FFmpeg HLS）
- [x] 评论系统
- [x] 会员系统
- [x] 邀请奖励系统
- [x] 广告系统
- [x] 支付接口预留
- [x] 管理后台API

### 第三阶段：前端开发（5-7天）
- [x] 管理后台框架
- [x] 登录页面
- [x] 仪表盘
- [x] 视频管理
- [x] 用户管理
- [x] 订单管理
- [x] 广告管理
- [x] 系统监控
- [ ] 用户端网页 (可选)

### 第四阶段：移动端开发（7-10天）
- [ ] Flutter 项目搭建
- [ ] 用户登录/注册
- [ ] 视频列表/播放
- [ ] 会员购买
- [ ] 个人中心

### 第五阶段：测试与部署（3-5天）
- [ ] 功能测试
- [ ] 性能优化
- [ ] Docker 部署
- [ ] 域名/SSL 配置

---

## 🔧 API 接口

### 认证
| 方法 | 路径 | 说明 |
|-----|------|------|
| POST | /api/v1/auth/register | 用户注册 |
| POST | /api/v1/auth/login | 用户登录 |
| POST | /api/v1/auth/refresh | 刷新令牌 |

### 视频
| 方法 | 路径 | 说明 |
|-----|------|------|
| POST | /api/v1/videos/upload | 上传视频 |
| GET | /api/v1/videos | 视频列表 |
| GET | /api/v1/videos/{id} | 视频详情 |

### 支付
| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | /api/v1/payments/prices | VIP价格 |
| POST | /api/v1/payments/orders | 创建订单 |

完整API文档: http://localhost:8000/api/docs

---

## ⚙️ 配置说明

### 环境变量 (.env)

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/vod

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT密钥
JWT_SECRET_KEY=your-secret-key

# OpenAI (可选，用于AI分析)
OPENAI_API_KEY=sk-xxx

# VIP价格（分）
VIP_PRICE_MONTHLY=2900
VIP_PRICE_YEARLY=19900
```

---

## 📞 技术支持

如有问题，请提交 Issue 或联系开发者。

## 📄 License

MIT License









