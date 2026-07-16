"""add area_id to subjects

Revision ID: a1b2c3d4e5f6
Revises: eb652a056aeb
Create Date: 2026-07-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'eb652a056aeb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('subjects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('area_id', sa.Uuid(), nullable=True))
        batch_op.create_index(batch_op.f('ix_subjects_area_id'), ['area_id'], unique=False)
        batch_op.create_foreign_key(
            'fk_subjects_area_id', 'academic_areas', ['area_id'], ['id'],
        )


def downgrade() -> None:
    with op.batch_alter_table('subjects', schema=None) as batch_op:
        batch_op.drop_constraint('fk_subjects_area_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_subjects_area_id'))
        batch_op.drop_column('area_id')
