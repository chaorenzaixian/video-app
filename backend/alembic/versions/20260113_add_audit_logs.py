"""add audit logs table

Revision ID: 20260113_audit
Revises: add_comment_indexes
Create Date: 2026-01-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260113_audit'
down_revision = 'add_comment_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建审计日志表
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='操作用户ID'),
        sa.Column('username', sa.String(100), nullable=True, comment='操作用户名'),
        sa.Column('action', sa.String(50), nullable=False, comment='操作类型'),
        sa.Column('resource_type', sa.String(50), nullable=True, comment='资源类型'),
        sa.Column('resource_id', sa.Integer(), nullable=True, comment='资源ID'),
        sa.Column('ip_address', sa.String(50), nullable=True, comment='IP地址'),
        sa.Column('user_agent', sa.String(500), nullable=True, comment='User-Agent'),
        sa.Column('request_method', sa.String(10), nullable=True, comment='请求方法'),
        sa.Column('request_path', sa.String(500), nullable=True, comment='请求路径'),
        sa.Column('details', sa.JSON(), nullable=True, comment='操作详情'),
        sa.Column('old_value', sa.JSON(), nullable=True, comment='修改前的值'),
        sa.Column('new_value', sa.JSON(), nullable=True, comment='修改后的值'),
        sa.Column('status', sa.String(20), server_default='success', comment='操作状态'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('idx_audit_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_created_at', 'audit_logs', ['created_at'])


def downgrade() -> None:
    op.drop_index('idx_audit_created_at', table_name='audit_logs')
    op.drop_index('idx_audit_resource', table_name='audit_logs')
    op.drop_index('idx_audit_action', table_name='audit_logs')
    op.drop_index('idx_audit_user_id', table_name='audit_logs')
    op.drop_table('audit_logs')
