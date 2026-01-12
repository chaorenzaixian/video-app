# Video App API 文档

## 概述

视频应用后端 API，基于 FastAPI 构建。

- 基础URL: `/api/v1`
- 认证方式: JWT Bearer Token
- 响应格式: JSON

## 认证

### 登录
```
POST /api/v1/auth/login
```

**请求体:**
```json
{
  "username": "string",
  "password": "string"
}
```

**响应:**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "string",
    "nickname": "string",
    "avatar": "string"
  }
}
```

### 注册
```
POST /api/v1/auth/register
```

### 登出
```
POST /api/v1/auth/logout
```
需要认证，会将当前 token 加入黑名单。

---

## 视频

### 获取视频列表
```
GET /api/v1/videos
```

**查询参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码，默认1 |
| page_size | int | 每页数量，默认20 |
| category_id | int | 分类ID |
| sort_by | string | 排序方式: newest/hottest |

### 获取视频详情
```
GET /api/v1/videos/{video_id}
```

### 上传视频
```
POST /api/v1/videos/upload
```
需要认证，仅管理员可用。

---

## 评论

### 获取视频评论
```
GET /api/v1/comments/video/{video_id}
```

**查询参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| page_size | int | 每页数量 |
| sort_by | string | newest/hottest |

**响应:**
```json
{
  "items": [
    {
      "id": 1,
      "content": "评论内容",
      "user_id": 1,
      "user_name": "用户名",
      "user_avatar": "头像URL",
      "user_vip_level": 0,
      "like_count": 10,
      "reply_count": 2,
      "is_liked": false,
      "created_at": "2026-01-13T00:00:00"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

### 发表评论
```
POST /api/v1/comments
```
需要认证，仅VIP用户可评论。

**请求体:**
```json
{
  "video_id": 1,
  "content": "评论内容",
  "parent_id": null,
  "image_url": null
}
```

### 点赞评论
```
POST /api/v1/comments/{comment_id}/like
```
需要认证。

---

## 用户

### 获取当前用户信息
```
GET /api/v1/users/me
```
需要认证。

### 更新用户信息
```
PUT /api/v1/users/me
```
需要认证。

---

## VIP

### 获取VIP套餐列表
```
GET /api/v1/vip/packages
```

### 购买VIP
```
POST /api/v1/vip/purchase
```
需要认证。

---

## 支付

### 创建支付订单
```
POST /api/v1/payments/create
```
需要认证。

### 支付回调
```
POST /api/v1/payments/callback/{provider}
```
支付平台回调接口。

---

## 通知

### 获取通知列表
```
GET /api/v1/notifications
```
需要认证。

### 标记通知已读
```
PUT /api/v1/notifications/{notification_id}/read
```
需要认证。

---

## 管理后台

### 监控指标
```
GET /api/v1/admin/monitoring/metrics
```
需要管理员权限。

### 系统健康检查
```
GET /api/v1/admin/monitoring/health
```

---

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁 |
| 500 | 服务器错误 |

## 限流

- 普通用户: 60次/分钟
- VIP用户: 120次/分钟
- 管理员: 无限制

超过限制返回 429 状态码。
