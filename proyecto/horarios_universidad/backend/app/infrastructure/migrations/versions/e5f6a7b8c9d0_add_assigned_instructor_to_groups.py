"""add assigned_instructor_id to groups

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-20 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('groups', schema=None) as batch_op:
        batch_op.add_column(sa.Column('assigned_instructor_id', sa.Uuid(), nullable=True))
        batch_op.create_index(batch_op.f('ix_groups_assigned_instructor_id'), ['assigned_instructor_id'], unique=False)
        batch_op.create_foreign_key(
            'fk_groups_assigned_instructor_id', 'instructors', ['assigned_instructor_id'], ['id'],
        )


def downgrade() -> None:
    with op.batch_alter_table('groups', schema=None) as batch_op:
        batch_op.drop_constraint('fk_groups_assigned_instructor_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_groups_assigned_instructor_id'))
        batch_op.drop_column('assigned_instructor_id')
