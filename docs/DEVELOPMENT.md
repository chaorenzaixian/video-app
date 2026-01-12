# 开发指南

## 本地开发环境搭建

### 1. 克隆代码
```bash
git clone https://github.com/chaorenzaixian/video-app.git
cd video-app
```

### 2. 后端设置
```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 复制环境配置
cp env.example .env
# 编辑 .env 配置数据库等

# 运行迁移
alembic upgrade head

# 启动开发服务器
python run.py
```

### 3. 前端设置
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 项目结构

```
video-app/
├── backend/
│   ├── app/
│   │   ├── api/           # API路由
│   │   ├── core/          # 核心配置
│   │   ├── models/        # 数据模型
│   │   ├── schemas/       # Pydantic模式
│   │   ├── services/      # 业务服务
│   │   └── tasks/         # Celery任务
│   ├── alembic/           # 数据库迁移
│   ├── tests/             # 测试
│   └── uploads/           # 上传文件
├── frontend/
│   ├── src/
│   │   ├── views/         # 页面组件
│   │   ├── components/    # 公共组件
│   │   ├── composables/   # 组合式函数
│   │   ├── utils/         # 工具函数
│   │   └── constants/     # 常量定义
│   └── public/
├── docs/                  # 文档
└── scripts/               # 脚本工具
```

## 代码规范

### Python
- 使用 Black 格式化代码
- 使用 isort 排序导入
- 遵循 PEP 8 规范
- 类型注解

### JavaScript/Vue
- 使用 ESLint + Prettier
- 组件使用 Composition API
- 遵循 Vue 3 最佳实践

## 数据库迁移

### 创建新迁移
```bash
cd backend
alembic revision -m "描述"
```

### 运行迁移
```bash
alembic upgrade head
```

### 回滚迁移
```bash
alembic downgrade -1
```

## 测试

### 运行后端测试
```bash
cd backend
pytest
```

### 运行前端测试
```bash
cd frontend
npm run test
```

## 常用服务

### CacheService - 缓存服务
```python
from app.services.cache_service import CacheService, cache_aside

# 获取缓存
data = await CacheService.get("key")

# 设置缓存
await CacheService.set("key", data, ttl=300)

# 使用装饰器
@cache_aside("user:vip:{user_id}", ttl=300)
async def get_user_vip(user_id: int):
    ...
```

### AuditService - 审计日志
```python
from app.services.audit_service import AuditService, AuditAction

# 记录操作
await AuditService.log(
    db=db,
    action=AuditAction.VIDEO_DELETE,
    user_id=user.id,
    resource_type="video",
    resource_id=video_id
)
```

### CommentService - 评论服务
```python
from app.services.comment_service import CommentService

# 批量获取VIP等级
vip_map = await CommentService.batch_get_user_vip_levels(db, user_ids)

# 获取视频评论
result = await CommentService.get_video_comments(
    db, video_id, page=1, page_size=20
)
```

## Git 工作流

### 分支命名
- `main` - 主分支，生产环境
- `develop` - 开发分支
- `feature/xxx` - 功能分支
- `fix/xxx` - 修复分支

### 提交信息格式
```
<type>: <description>

类型:
- feat: 新功能
- fix: 修复
- docs: 文档
- style: 格式
- refactor: 重构
- test: 测试
- chore: 构建/工具
```

### 示例
```bash
git commit -m "feat: 添加视频评论功能"
git commit -m "fix: 修复登录验证问题"
```

## 环境变量

### 后端 (.env)
```env
# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/video_app

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# 环境
ENVIRONMENT=development
DEBUG=true
```

## 调试技巧

### 后端调试
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 或使用 print
print(f"Debug: {variable}")
```

### 数据库查询日志
```python
# 在 .env 中设置
SQLALCHEMY_ECHO=true
```

### 前端调试
```javascript
console.log('Debug:', data)
// 或使用 Vue Devtools
```
