"""add area_id to instructors

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('instructors', schema=None) as batch_op:
        batch_op.add_column(sa.Column('area_id', sa.Uuid(), nullable=True))
        batch_op.create_index(batch_op.f('ix_instructors_area_id'), ['area_id'], unique=False)
        batch_op.create_foreign_key(
            'fk_instructors_area_id', 'academic_areas', ['area_id'], ['id'],
        )


def downgrade() -> None:
    with op.batch_alter_table('instructors', schema=None) as batch_op:
        batch_op.drop_constraint('fk_instructors_area_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_instructors_area_id'))
        batch_op.drop_column('area_id')
