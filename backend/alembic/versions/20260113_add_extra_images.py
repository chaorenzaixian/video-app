"""add extra_images to advertisements

Revision ID: add_extra_images
Revises: 
Create Date: 2026-01-13

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_extra_images'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add extra_images column to advertisements table
    op.add_column('advertisements', sa.Column('extra_images', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('advertisements', 'extra_images')
