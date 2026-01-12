"""
统一异常处理
"""
from fastapi import HTTPException, status
from typing import Optional, Any, Dict


class AppException(HTTPException):
    """应用基础异常"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


class BadRequestException(AppException):
    """400 错误请求"""
    
    def __init__(self, detail: str = "请求参数错误", error_code: str = "BAD_REQUEST"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code
        )


class UnauthorizedException(AppException):
    """401 未授权"""
    
    def __init__(self, detail: str = "未授权访问", error_code: str = "UNAUTHORIZED"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code=error_code,
            headers={"WWW-Authenticate": "Bearer"}
        )


class ForbiddenException(AppException):
    """403 禁止访问"""
    
    def __init__(self, detail: str = "没有权限执行此操作", error_code: str = "FORBIDDEN"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code
        )


class NotFoundException(AppException):
    """404 资源不存在"""
    
    def __init__(self, detail: str = "资源不存在", error_code: str = "NOT_FOUND"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code=error_code
        )


class ConflictException(AppException):
    """409 冲突"""
    
    def __init__(self, detail: str = "资源冲突", error_code: str = "CONFLICT"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code=error_code
        )


class TooManyRequestsException(AppException):
    """429 请求过多"""
    
    def __init__(
        self,
        detail: str = "请求过于频繁，请稍后重试",
        retry_after: int = 60,
        error_code: str = "TOO_MANY_REQUESTS"
    ):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code=error_code,
            headers={"Retry-After": str(retry_after)}
        )


class InternalServerException(AppException):
    """500 服务器内部错误"""
    
    def __init__(self, detail: str = "服务器内部错误", error_code: str = "INTERNAL_ERROR"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code=error_code
        )


# 业务异常
class UserNotFoundException(NotFoundException):
    """用户不存在"""
    def __init__(self):
        super().__init__(detail="用户不存在", error_code="USER_NOT_FOUND")


class VideoNotFoundException(NotFoundException):
    """视频不存在"""
    def __init__(self):
        super().__init__(detail="视频不存在", error_code="VIDEO_NOT_FOUND")


class InvalidCredentialsException(UnauthorizedException):
    """凭证无效"""
    def __init__(self):
        super().__init__(detail="用户名或密码错误", error_code="INVALID_CREDENTIALS")


class TokenExpiredException(UnauthorizedException):
    """令牌过期"""
    def __init__(self):
        super().__init__(detail="登录已过期，请重新登录", error_code="TOKEN_EXPIRED")


class InsufficientBalanceException(BadRequestException):
    """余额不足"""
    def __init__(self, detail: str = "余额不足"):
        super().__init__(detail=detail, error_code="INSUFFICIENT_BALANCE")


class VipRequiredException(ForbiddenException):
    """需要VIP权限"""
    def __init__(self):
        super().__init__(detail="需要VIP权限", error_code="VIP_REQUIRED")


class AdminRequiredException(ForbiddenException):
    """需要管理员权限"""
    def __init__(self):
        super().__init__(detail="需要管理员权限", error_code="ADMIN_REQUIRED")
