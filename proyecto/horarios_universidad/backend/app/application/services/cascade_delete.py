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
    "delete_subject_cascade",
    "delete_instructor_cascade",
    "delete_user_cascade",
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


def delete_subject_cascade(session: Session, subject_id: EntityId) -> None:
    """Delete every row referencing a subject, then the subject itself.

    Covers offering lines (cascading down to groups/assignments/session
    blocks), resource requirements, instructor specialties, and standalone
    instructor preferences that reference the subject directly (not just
    through a group) — a gap that let ``DeleteSubject``/``DeleteArea`` raise
    a raw FK ``IntegrityError`` if any such preference existed.
    """
    from app.infrastructure.persistence.models.academic import SubjectModel
    from app.infrastructure.persistence.models.infrastructure_models import (
        SubjectResourceRequirementModel,
    )
    from app.infrastructure.persistence.models.offering import OfferingLineModel
    from app.infrastructure.persistence.models.personnel import (
        InstructorPreferenceModel,
        InstructorSpecialtyModel,
    )

    line_ids = [
        row.id
        for row in session.query(OfferingLineModel.id)
        .filter(OfferingLineModel.subject_id == subject_id)
        .all()
    ]
    delete_offering_lines_cascade(session, line_ids)

    session.query(SubjectResourceRequirementModel).filter(
        SubjectResourceRequirementModel.subject_id == subject_id,
    ).delete(synchronize_session=False)
    session.query(InstructorSpecialtyModel).filter(
        InstructorSpecialtyModel.subject_id == subject_id,
    ).delete(synchronize_session=False)
    session.query(InstructorPreferenceModel).filter(
        InstructorPreferenceModel.subject_id == subject_id,
    ).delete(synchronize_session=False)

    session.query(SubjectModel).filter(
        SubjectModel.id == subject_id,
    ).delete(synchronize_session=False)


def delete_instructor_cascade(session: Session, instructor_id: EntityId) -> None:
    """Delete every row referencing an instructor, then the instructor itself."""
    from app.infrastructure.persistence.models.personnel import (
        InstructorAvailabilityModel,
        InstructorContractModel,
        InstructorModel,
        InstructorPreferenceModel,
        InstructorQualificationModel,
        InstructorSpecialtyModel,
    )
    from app.infrastructure.persistence.models.schedule import (
        AssignmentModel,
        SessionBlockModel,
    )

    assignment_ids = [
        row.id
        for row in session.query(AssignmentModel.id)
        .filter(AssignmentModel.instructor_id == instructor_id)
        .all()
    ]
    if assignment_ids:
        session.query(SessionBlockModel).filter(
            SessionBlockModel.assignment_id.in_(assignment_ids),
        ).delete(synchronize_session=False)
        session.query(AssignmentModel).filter(
            AssignmentModel.id.in_(assignment_ids),
        ).delete(synchronize_session=False)

    session.query(InstructorContractModel).filter(
        InstructorContractModel.instructor_id == instructor_id,
    ).delete(synchronize_session=False)
    session.query(InstructorSpecialtyModel).filter(
        InstructorSpecialtyModel.instructor_id == instructor_id,
    ).delete(synchronize_session=False)
    session.query(InstructorQualificationModel).filter(
        InstructorQualificationModel.instructor_id == instructor_id,
    ).delete(synchronize_session=False)
    session.query(InstructorAvailabilityModel).filter(
        InstructorAvailabilityModel.instructor_id == instructor_id,
    ).delete(synchronize_session=False)
    session.query(InstructorPreferenceModel).filter(
        InstructorPreferenceModel.instructor_id == instructor_id,
    ).delete(synchronize_session=False)

    session.query(InstructorModel).filter(
        InstructorModel.id == instructor_id,
    ).delete(synchronize_session=False)


def delete_user_cascade(session: Session, user_id: EntityId) -> None:
    """Delete a user account and detach it from historical records.

    Rows that are the user's own data (notifications) are deleted. Rows
    that merely record who performed an action (audit logs, schedule
    runs, optimization configs, import sessions, validation reports,
    academic offerings) are kept but have their user reference cleared,
    so removing a user never raises a raw FK ``IntegrityError`` and
    never erases unrelated history.
    """
    from app.infrastructure.persistence.models.auth import UserModel
    from app.infrastructure.persistence.models.import_export import (
        ImportSessionModel,
        ValidationReportModel,
    )
    from app.infrastructure.persistence.models.offering import (
        AcademicOfferingModel,
    )
    from app.infrastructure.persistence.models.schedule import (
        OptimizationConfigModel,
        ScheduleRunModel,
    )
    from app.infrastructure.persistence.models.system import (
        AuditLogModel,
        NotificationModel,
    )

    session.query(NotificationModel).filter(
        NotificationModel.user_id == user_id,
    ).delete(synchronize_session=False)

    session.query(AuditLogModel).filter(
        AuditLogModel.user_id == user_id,
    ).update({"user_id": None}, synchronize_session=False)
    session.query(ImportSessionModel).filter(
        ImportSessionModel.user_id == user_id,
    ).update({"user_id": None}, synchronize_session=False)
    session.query(ValidationReportModel).filter(
        ValidationReportModel.created_by == user_id,
    ).update({"created_by": None}, synchronize_session=False)
    session.query(OptimizationConfigModel).filter(
        OptimizationConfigModel.created_by == user_id,
    ).update({"created_by": None}, synchronize_session=False)
    session.query(ScheduleRunModel).filter(
        ScheduleRunModel.created_by == user_id,
    ).update({"created_by": None}, synchronize_session=False)
    session.query(AcademicOfferingModel).filter(
        AcademicOfferingModel.created_by == user_id,
    ).update({"created_by": None}, synchronize_session=False)

    session.query(UserModel).filter(
        UserModel.id == user_id,
    ).delete(synchronize_session=False)
