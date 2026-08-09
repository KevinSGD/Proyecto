"""sync missing model columns

Revision ID: 4a5beb960da4
Revises: f6a7b8c9d0e1
Create Date: 2026-08-09 23:51:19.051230

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '4a5beb960da4'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('academic_offerings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('observations', sa.String(length=2000), nullable=False, server_default=''))


def downgrade() -> None:
    with op.batch_alter_table('academic_offerings', schema=None) as batch_op:
        batch_op.drop_column('observations')
