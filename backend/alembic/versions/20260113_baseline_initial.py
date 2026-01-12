"""baseline - mark existing database as starting point

Revision ID: baseline_initial
Revises: 
Create Date: 2026-01-13

这是一个空的基线迁移。
数据库已经存在，我们只是将当前状态标记为起点。
后续的迁移将基于此版本进行增量更改。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'baseline_initial'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    空迁移 - 数据库已存在
    这个迁移不执行任何操作，只是作为版本控制的起点
    """
    pass


def downgrade() -> None:
    """
    空迁移 - 无法回退到数据库创建之前
    """
    pass
