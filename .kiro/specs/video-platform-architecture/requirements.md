# Requirements Document

## Introduction

本文档定义了视频平台架构优化的需求规范。基于现有系统分析和历史优化建议，目标是构建一个高效、可扩展、易维护的视频处理和分发系统。

核心优化目标：
1. 优化转码架构，减少网络传输开销 60-70%
2. 提升视频处理效率 50%
3. 增强系统安全性和稳定性
4. 改善代码可维护性

## Glossary

- **Main_Server**: 主服务器 (38.47.218.137)，运行 FastAPI 后端、数据库、Nginx，负责业务逻辑和内容分发
- **Transcode_Server**: 转码服务器 (198.176.60.121)，Windows 系统，配备 NVIDIA GPU，负责视频转码
- **HLS**: HTTP Live Streaming，苹果开发的自适应码率流媒体协议
- **NVENC**: NVIDIA 硬件视频编码器
- **Callback_API**: 转码完成后的回调接口，用于更新数据库状态
- **Preview_Video**: 10秒预览视频，用于鼠标悬停时播放
- **Cover_Image**: 视频封面图片，WebP 格式
- **Video_Processor**: 视频处理服务，负责转码、生成封面和预览

## Requirements

### Requirement 1: 视频上传与存储

**User Story:** As a 管理员, I want to 上传视频文件到平台, so that 用户可以观看视频内容

#### Acceptance Criteria

1. WHEN 管理员上传视频文件 THEN THE Main_Server SHALL 接收文件并保存到本地存储
2. WHEN 视频文件大小超过 5GB THEN THE Main_Server SHALL 返回文件大小超限错误
3. WHEN 视频格式不支持 THEN THE Main_Server SHALL 返回格式不支持错误
4. WHEN 上传成功 THEN THE Main_Server SHALL 创建视频数据库记录并设置状态为 PENDING
5. IF 上传过程中网络中断 THEN THE Main_Server SHALL 清理临时文件并返回上传失败错误

### Requirement 2: 视频转码处理

**User Story:** As a 系统, I want to 自动转码上传的视频, so that 视频可以在各种设备上流畅播放

#### Acceptance Criteria

1. WHEN 视频上传完成 THEN THE Video_Processor SHALL 自动开始处理视频
2. WHEN 视频文件较大（>500MB）且 GPU 转码可用 THEN THE Main_Server SHALL 将视频推送到 Transcode_Server 处理
3. WHEN 视频文件较小（<500MB）THEN THE Main_Server SHALL 在本地使用 CPU 或 QSV 硬件加速处理
4. WHEN 转码开始 THEN THE Video_Processor SHALL 更新视频状态为 PROCESSING
5. WHEN 转码完成 THEN THE Video_Processor SHALL 生成 HLS 格式的多清晰度视频流
6. IF 转码失败 THEN THE Video_Processor SHALL 更新视频状态为 FAILED 并记录错误信息

### Requirement 3: 封面图片生成

**User Story:** As a 用户, I want to 看到视频封面, so that 我可以快速了解视频内容

#### Acceptance Criteria

1. WHEN 视频处理开始 THEN THE Video_Processor SHALL 从视频中智能选取最佳帧作为封面
2. WHEN 生成封面 THEN THE Video_Processor SHALL 输出 WebP 格式图片，宽度 640px，质量 85%
3. WHEN 封面生成完成 THEN THE Video_Processor SHALL 更新数据库中的 cover_url 字段
4. WHERE 管理员上传了自定义封面 THEN THE Video_Processor SHALL 跳过自动封面生成
5. WHEN 智能选帧 THEN THE Video_Processor SHALL 分析多个时间点的帧质量并选择评分最高的帧

### Requirement 4: 预览视频生成

**User Story:** As a 用户, I want to 鼠标悬停时预览视频, so that 我可以快速了解视频内容

#### Acceptance Criteria

1. WHEN 视频处理开始 THEN THE Video_Processor SHALL 生成 10 秒预览视频
2. WHEN 生成预览 THEN THE Video_Processor SHALL 从视频中均匀采样 10 个片段，每段 1 秒
3. WHEN 预览生成完成 THEN THE Video_Processor SHALL 输出 MP4 格式视频，分辨率 720p，无音频
4. WHEN 预览生成完成 THEN THE Video_Processor SHALL 更新数据库中的 preview_url 字段
5. IF 视频时长小于 10 秒 THEN THE Video_Processor SHALL 按比例减少预览片段数量

### Requirement 5: 转码服务器架构

**User Story:** As a 系统架构师, I want to 优化转码服务器架构, so that 减少网络传输并提高处理效率

#### Acceptance Criteria

1. WHEN Transcode_Server 接收到转码任务 THEN THE Transcode_Server SHALL 在本地完成视频转码、封面生成、预览生成
2. WHEN 所有处理完成 THEN THE Transcode_Server SHALL 将转码后的视频、封面、预览一次性上传到 Main_Server
3. WHEN 上传完成 THEN THE Transcode_Server SHALL 调用 Callback_API 通知 Main_Server 更新数据库
4. WHEN 调用 Callback_API THEN THE Transcode_Server SHALL 提供正确的密钥进行身份验证
5. IF 上传失败 THEN THE Transcode_Server SHALL 重试最多 3 次，每次间隔 30 秒

### Requirement 6: 回调接口

**User Story:** As a 系统, I want to 接收转码完成通知, so that 数据库状态可以及时更新

#### Acceptance Criteria

1. WHEN 收到转码成功回调 THEN THE Callback_API SHALL 更新视频的 cover_url、preview_url、hls_url、duration 字段
2. WHEN 收到转码成功回调 THEN THE Callback_API SHALL 更新视频状态为 PUBLISHED 并设置 published_at 时间
3. WHEN 收到转码失败回调 THEN THE Callback_API SHALL 更新视频状态为 FAILED 并记录错误信息
4. IF 回调密钥无效 THEN THE Callback_API SHALL 返回 403 Forbidden 错误
5. IF 视频 ID 不存在 THEN THE Callback_API SHALL 返回 404 Not Found 错误

### Requirement 7: 多清晰度自适应码率

**User Story:** As a 用户, I want to 根据网络状况自动切换视频清晰度, so that 我可以获得最佳观看体验

#### Acceptance Criteria

1. WHEN 源视频分辨率 >= 1080p THEN THE Video_Processor SHALL 生成 1080p、720p、480p 三个清晰度版本
2. WHEN 源视频分辨率 >= 720p 且 < 1080p THEN THE Video_Processor SHALL 生成 720p、480p 两个清晰度版本
3. WHEN 源视频分辨率 < 720p THEN THE Video_Processor SHALL 仅生成 480p 版本
4. WHEN 多清晰度转码完成 THEN THE Video_Processor SHALL 生成 HLS master.m3u8 主播放列表
5. WHEN 播放器请求视频 THEN THE Main_Server SHALL 返回 master.m3u8 供播放器自动选择清晰度

### Requirement 8: 文件清理与存储管理

**User Story:** As a 系统管理员, I want to 自动清理临时文件, so that 服务器存储空间不会被耗尽

#### Acceptance Criteria

1. WHEN 转码完成并上传成功 THEN THE Transcode_Server SHALL 删除本地的原始视频和临时文件
2. WHEN 视频被删除 THEN THE Main_Server SHALL 同时删除关联的 HLS 文件、封面和预览
3. WHEN 磁盘空间低于阈值 THEN THE Main_Server SHALL 发送告警通知
4. WHEN 临时文件超过 24 小时 THEN THE Main_Server SHALL 自动清理这些文件

### Requirement 9: 监控与日志

**User Story:** As a 系统管理员, I want to 监控视频处理状态, so that 我可以及时发现和解决问题

#### Acceptance Criteria

1. WHEN 视频处理开始 THEN THE Video_Processor SHALL 记录处理开始时间和视频信息
2. WHEN 视频处理完成 THEN THE Video_Processor SHALL 记录处理耗时和结果
3. WHEN 处理失败 THEN THE Video_Processor SHALL 记录详细错误信息和堆栈跟踪
4. WHEN 管理员查询 GPU 状态 THEN THE Main_Server SHALL 返回 GPU 使用率、内存使用、处理队列信息
5. WHEN 处理进度更新 THEN THE Video_Processor SHALL 将进度信息存储到 Redis 供前端查询

### Requirement 10: 安全性

**User Story:** As a 系统管理员, I want to 确保系统安全, so that 视频内容和用户数据得到保护

#### Acceptance Criteria

1. WHEN 调用 Callback_API THEN THE Callback_API SHALL 验证 X-Transcode-Key 请求头
2. WHEN 上传视频 THEN THE Main_Server SHALL 验证用户身份和权限
3. WHEN 访问视频文件 THEN THE Main_Server SHALL 通过 Nginx 提供静态文件服务
4. IF 未授权访问 THEN THE Main_Server SHALL 返回 401 或 403 错误
5. WHEN 存储敏感配置 THEN THE Main_Server SHALL 使用环境变量而非硬编码


### Requirement 11: 支付安全增强

**User Story:** As a 系统管理员, I want to 确保支付流程安全可靠, so that 用户资金和平台收入得到保护

#### Acceptance Criteria

1. WHEN 收到支付回调 THEN THE Payment_Service SHALL 使用数据库行锁确保幂等性处理
2. WHEN 处理支付回调 THEN THE Payment_Service SHALL 验证回调金额与订单金额一致（误差 < 0.01）
3. WHEN 订单已处理 THEN THE Payment_Service SHALL 直接返回成功而不重复处理
4. IF 金额不匹配 THEN THE Payment_Service SHALL 记录警告日志并返回失败
5. WHEN 订单超时未支付 THEN THE Payment_Service SHALL 自动关闭订单并释放资源

### Requirement 12: 数据库性能优化

**User Story:** As a 系统, I want to 优化数据库查询性能, so that 用户获得更快的响应速度

#### Acceptance Criteria

1. THE Database SHALL 为视频表添加 (status, created_at) 复合索引
2. THE Database SHALL 为评论表添加 (video_id, is_hidden, created_at) 复合索引
3. THE Database SHALL 为 VIP 表添加 (user_id, is_active, expire_date) 复合索引
4. WHEN 查询大数据量列表 THEN THE API SHALL 使用游标分页而非 OFFSET 分页
5. WHEN 批量查询用户信息 THEN THE API SHALL 使用 IN 查询而非循环单条查询

### Requirement 13: 缓存策略

**User Story:** As a 系统, I want to 合理使用缓存, so that 减少数据库负载并提升响应速度

#### Acceptance Criteria

1. WHEN 查询用户 VIP 信息 THEN THE Cache_Service SHALL 缓存结果 5 分钟
2. WHEN 查询视频列表 THEN THE Cache_Service SHALL 缓存结果 5 分钟
3. WHEN 查询视频详情 THEN THE Cache_Service SHALL 缓存结果 10 分钟
4. WHEN 数据更新 THEN THE Cache_Service SHALL 主动失效相关缓存
5. WHEN 系统启动 THEN THE Cache_Service SHALL 预热热门数据缓存

### Requirement 14: API 限流保护

**User Story:** As a 系统管理员, I want to 防止 API 滥用, so that 系统资源得到保护

#### Acceptance Criteria

1. THE Rate_Limiter SHALL 限制登录接口为 3 次/分钟/IP
2. THE Rate_Limiter SHALL 限制注册接口为 1 次/分钟/IP
3. THE Rate_Limiter SHALL 限制支付接口为 5 次/分钟/用户
4. WHEN 超过限流阈值 THEN THE Rate_Limiter SHALL 返回 429 状态码
5. IF 检测到异常请求模式 THEN THE Rate_Limiter SHALL 临时封禁 IP

### Requirement 15: 异步任务处理

**User Story:** As a 系统, I want to 使用异步任务队列处理耗时操作, so that API 响应更快且系统更稳定

#### Acceptance Criteria

1. WHEN 视频上传完成 THEN THE Task_Queue SHALL 异步处理视频转码任务
2. WHEN 需要发送通知 THEN THE Task_Queue SHALL 异步发送推送通知
3. WHEN 任务失败 THEN THE Task_Queue SHALL 自动重试最多 3 次
4. WHEN 定时任务触发 THEN THE Task_Queue SHALL 执行 VIP 过期检查和临时文件清理
5. THE Task_Queue SHALL 支持任务优先级和延迟执行
