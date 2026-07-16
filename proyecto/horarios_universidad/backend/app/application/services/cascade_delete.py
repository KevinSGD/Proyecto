"""Cascade-delete helpers for entities referenced by scheduling data.

SQLite enforces foreign keys in this project (``PRAGMA foreign_keys=ON``),
so deleting an academic area, subject, or classroom that already has
dependent offerings/groups/schedule data raises a raw ``IntegrityError``
unless the dependent rows are cleaned up first. These helpers walk the
dependency chain (offering -> offering_line -> group -> assignment ->
session_block) so deletes at any level succeed instead of failing with an
unhandled foreign-key violation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.utils.types import EntityId

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

__all__ = [
    "delete_groups_cascade",
    "delete_offering_lines_cascade",
    "delete_offerings_cascade",
]


def delete_groups_cascade(session: Session, group_ids: list[EntityId]) -> None:
    """Delete session blocks, assignments, preferences, and groups for the given group ids."""
    if not group_ids:
        return

    from app.infrastructure.persistence.models.personnel import (
        InstructorPreferenceModel,
    )
    from app.infrastructure.persistence.models.schedule import (
        AssignmentModel,
        SessionBlockModel,
    )
    from app.infrastructure.persistence.models.scheduling import GroupModel

    assignment_ids = [
        row.id
        for row in session.query(AssignmentModel.id)
        .filter(AssignmentModel.group_id.in_(group_ids))
        .all()
    ]
    if assignment_ids:
        session.query(SessionBlockModel).filter(
            SessionBlockModel.assignment_id.in_(assignment_ids),
        ).delete(synchronize_session=False)
        session.query(AssignmentModel).filter(
            AssignmentModel.id.in_(assignment_ids),
        ).delete(synchronize_session=False)

    session.query(InstructorPreferenceModel).filter(
        InstructorPreferenceModel.group_id.in_(group_ids),
    ).delete(synchronize_session=False)

    session.query(GroupModel).filter(GroupModel.id.in_(group_ids)).delete(
        synchronize_session=False,
    )


def delete_offering_lines_cascade(session: Session, line_ids: list[EntityId]) -> None:
    """Delete groups (cascading further) and the offering lines themselves."""
    if not line_ids:
        return

    from app.infrastructure.persistence.models.offering import OfferingLineModel
    from app.infrastructure.persistence.models.scheduling import GroupModel

    group_ids = [
        row.id
        for row in session.query(GroupModel.id)
        .filter(GroupModel.offering_line_id.in_(line_ids))
        .all()
    ]
    delete_groups_cascade(session, group_ids)

    session.query(OfferingLineModel).filter(
        OfferingLineModel.id.in_(line_ids),
    ).delete(synchronize_session=False)


def delete_offerings_cascade(session: Session, offering_ids: list[EntityId]) -> None:
    """Delete offering lines (cascading further) and the offerings themselves."""
    if not offering_ids:
        return

    from app.infrastructure.persistence.models.offering import (
        AcademicOfferingModel,
        OfferingLineModel,
    )

    line_ids = [
        row.id
        for row in session.query(OfferingLineModel.id)
        .filter(OfferingLineModel.offering_id.in_(offering_ids))
        .all()
    ]
    delete_offering_lines_cascade(session, line_ids)

    session.query(AcademicOfferingModel).filter(
        AcademicOfferingModel.id.in_(offering_ids),
    ).delete(synchronize_session=False)
