"""
数据库模型混入类
提供可复用的模型功能
"""
from datetime import datetime
from sqlalchemy import Column, Boolean, DateTime, Integer, event
from sqlalchemy.orm import declared_attr


class SoftDeleteMixin:
    """
    软删除混入类
    
    为模型添加软删除功能，删除时不真正删除数据，而是标记为已删除。
    
    使用方法:
    ```python
    class Video(Base, SoftDeleteMixin):
        __tablename__ = "videos"
        # ... 其他字段
    
    # 软删除
    video.soft_delete(user_id=current_user.id)
    
    # 恢复
    video.restore()
    
    # 查询时自动过滤已删除记录（需要在查询中添加条件）
    query = select(Video).where(Video.is_deleted == False)
    ```
    """
    
    is_deleted = Column(
        Boolean, 
        default=False, 
        index=True, 
        nullable=False,
        comment="是否已删除"
    )
    deleted_at = Column(
        DateTime, 
        nullable=True,
        comment="删除时间"
    )
    deleted_by = Column(
        Integer, 
        nullable=True,
        comment="删除操作者ID"
    )
    
    def soft_delete(self, user_id: int = None) -> None:
        """
        软删除记录
        
        Args:
            user_id: 执行删除操作的用户ID
        """
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by = user_id
    
    def restore(self) -> None:
        """恢复已删除的记录"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
    
    @property
    def is_active(self) -> bool:
        """检查记录是否活跃（未删除）"""
        return not self.is_deleted


class TimestampMixin:
    """
    时间戳混入类
    
    自动管理 created_at 和 updated_at 字段
    """
    
    created_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间"
    )


class AuditMixin(SoftDeleteMixin, TimestampMixin):
    """
    审计混入类
    
    组合软删除和时间戳功能，并添加创建者/更新者追踪
    """
    
    created_by = Column(
        Integer, 
        nullable=True,
        comment="创建者ID"
    )
    updated_by = Column(
        Integer, 
        nullable=True,
        comment="最后更新者ID"
    )
    
    def set_creator(self, user_id: int) -> None:
        """设置创建者"""
        self.created_by = user_id
        self.updated_by = user_id
    
    def set_updater(self, user_id: int) -> None:
        """设置更新者"""
        self.updated_by = user_id
