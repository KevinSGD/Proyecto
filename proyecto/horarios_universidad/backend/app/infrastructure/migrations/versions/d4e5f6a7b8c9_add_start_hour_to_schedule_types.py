"""add start_hour to schedule_types

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-18 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('schedule_types', schema=None) as batch_op:
        batch_op.add_column(sa.Column('start_hour', sa.Integer(), nullable=False, server_default='7'))


def downgrade() -> None:
    with op.batch_alter_table('schedule_types', schema=None) as batch_op:
        batch_op.drop_column('start_hour')
