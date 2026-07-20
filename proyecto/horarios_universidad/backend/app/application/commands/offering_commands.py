"""Write-side use cases for offering and scheduling entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.application.exceptions.application_exceptions import (
    BusinessRuleError,
    ResourceNotFoundError,
)
from app.core.utils.types import generate_id
from app.domain.entities.offering import AcademicOffering, OfferingLine
from app.domain.entities.scheduling import Group, ScheduleType

if TYPE_CHECKING:
    from uuid import UUID

    from app.domain.entities.academic import Subject

    from app.api.schemas.offering import (
        GroupCreate,
        GroupUpdate,
        OfferingCreate,
        OfferingLineCreate,
        OfferingLineUpdate,
        OfferingUpdate,
        ScheduleTypeCreate,
        ScheduleTypeUpdate,
        SubjectGroupCreate,
    )
    from app.domain.interfaces.unit_of_work import UnitOfWork


class CreateOffering:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: OfferingCreate) -> AcademicOffering:
        with self._uow:
            entity = AcademicOffering(
                id=generate_id(),
                institution_id=data.institution_id,
                period_id=data.period_id,
                area_id=data.area_id,
                created_by=data.created_by,
            )
            self._uow.offerings.save(entity)
            self._uow.commit()
            return entity


class UpdateOffering:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, offering_id: UUID, data: OfferingUpdate) -> AcademicOffering:
        with self._uow:
            entity = self._uow.offerings.get_by_id(offering_id)
            if entity is None:
                raise ResourceNotFoundError("AcademicOffering", offering_id)
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(entity, field, value)
            self._uow.offerings.save(entity)
            self._uow.commit()
            return entity


class DeleteOffering:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, offering_id: UUID) -> bool:
        with self._uow:
            deleted = self._uow.offerings.delete(offering_id)
            if not deleted:
                raise ResourceNotFoundError("AcademicOffering", offering_id)
            self._uow.commit()
            return True


class AddOfferingLine:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: OfferingLineCreate) -> OfferingLine:
        with self._uow:
            entity = OfferingLine(
                id=generate_id(),
                offering_id=data.offering_id,
                subject_id=data.subject_id,
                num_groups=data.num_groups,
                expected_enrollment_per_group=data.expected_enrollment_per_group,
                modality=data.modality or "presential",
                schedule_type_id=data.schedule_type_id,
            )
            self._uow.offering_lines.save(entity)
            self._uow.commit()
            return entity


class UpdateOfferingLine:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, line_id: UUID, data: OfferingLineUpdate) -> OfferingLine:
        with self._uow:
            entity = self._uow.offering_lines.get_by_id(line_id)
            if entity is None:
                raise ResourceNotFoundError("OfferingLine", line_id)
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(entity, field, value)
            self._uow.offering_lines.save(entity)
            self._uow.commit()
            return entity


class RemoveOfferingLine:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, line_id: UUID) -> bool:
        with self._uow:
            deleted = self._uow.offering_lines.delete(line_id)
            if not deleted:
                raise ResourceNotFoundError("OfferingLine", line_id)
            self._uow.commit()
            return True


class CreateScheduleType:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: ScheduleTypeCreate) -> ScheduleType:
        with self._uow:
            entity = ScheduleType(
                id=generate_id(),
                institution_id=data.institution_id,
                name=data.name,
                schedule_type=data.schedule_type,
                active_days=data.active_days,
                start_period=data.start_period,
                end_period=data.end_period,
                slot_duration_minutes=data.slot_duration_minutes or 60,
                start_hour=data.start_hour if data.start_hour is not None else 7,
            )
            self._uow.schedule_types.save(entity)
            self._uow.commit()
            return entity


class UpdateScheduleType:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, st_id: UUID, data: ScheduleTypeUpdate) -> ScheduleType:
        with self._uow:
            entity = self._uow.schedule_types.get_by_id(st_id)
            if entity is None:
                raise ResourceNotFoundError("ScheduleType", st_id)
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(entity, field, value)
            self._uow.schedule_types.save(entity)
            self._uow.commit()
            return entity


class DeleteScheduleType:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, st_id: UUID) -> bool:
        with self._uow:
            deleted = self._uow.schedule_types.delete(st_id)
            if not deleted:
                raise ResourceNotFoundError("ScheduleType", st_id)
            self._uow.commit()
            return True


class CreateGroup:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: GroupCreate) -> Group:
        with self._uow:
            entity = Group(
                id=generate_id(),
                offering_line_id=data.offering_line_id,
                subject_id=data.subject_id,
                group_number=data.group_number,
                expected_enrollment=data.expected_enrollment,
                modality=data.modality,
                schedule_type_id=data.schedule_type_id,
                priority=data.priority if data.priority is not None else 2,
            )
            self._uow.groups.save(entity)
            self._uow.commit()
            return entity


class UpdateGroup:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, group_id: UUID, data: GroupUpdate) -> Group:
        with self._uow:
            entity = self._uow.groups.get_by_id(group_id)
            if entity is None:
                raise ResourceNotFoundError("Group", group_id)
            if data.expected_enrollment is not None:
                entity.expected_enrollment = data.expected_enrollment
            if data.modality is not None:
                entity.modality = data.modality
            if data.priority is not None:
                entity.priority = data.priority
            self._uow.groups.save(entity)
            self._uow.commit()
            return entity


class AssignGroupInstructor:
    """Pin (or unpin) a specific instructor to a specific group.

    Lets a coordinator decide exactly who teaches which group of a subject
    (e.g. "Cálculo" has 3 groups — pick a different instructor per group)
    instead of only offering the whole subject to a pool of qualified
    instructors and letting the solver pick. When set, the solver treats it
    as the only candidate for that group (see
    dataset_builder._build_groups); ``None`` clears the pin and returns the
    group to the subject-wide specialty pool.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, group_id: UUID, instructor_id: UUID | None) -> Group:
        with self._uow:
            entity = self._uow.groups.get_by_id(group_id)
            if entity is None:
                raise ResourceNotFoundError("Group", group_id)
            if instructor_id is not None:
                instructor = self._uow.instructors.get_by_id(instructor_id)
                if instructor is None:
                    raise ResourceNotFoundError("Instructor", instructor_id)
            entity.assigned_instructor_id = instructor_id
            self._uow.groups.save(entity)
            self._uow.commit()
            return entity


class DeleteGroup:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, group_id: UUID) -> bool:
        with self._uow:
            entity = self._uow.groups.get_by_id(group_id)
            if entity is None:
                raise ResourceNotFoundError("Group", group_id)
            line = self._uow.offering_lines.get_by_id(entity.offering_line_id)
            deleted = self._uow.groups.delete(group_id)
            if not deleted:
                raise ResourceNotFoundError("Group", group_id)
            if line is not None and line.num_groups > 0:
                line.num_groups -= 1
                self._uow.offering_lines.save(line)
            self._uow.commit()
            return True


class CreateSubjectGroup:
    """Create a group for a subject, right from the Materia form.

    Auto-provisions a draft offering and offering-line for
    (institution, period, subject.area) the first time a group is added for
    that subject/period — the director never has to visit Oferta Académica
    manually just to get a subject schedulable. Each group keeps its own
    ``expected_enrollment``, which the solver already uses as a hard filter
    against classroom capacity (see dataset_builder._find_compatible_classrooms).
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, subject_id: UUID, data: SubjectGroupCreate) -> Group:
        with self._uow:
            subject = self._uow.subjects.get_by_id(subject_id)
            if subject is None:
                raise ResourceNotFoundError("Subject", subject_id)
            if subject.area_id is None:
                raise BusinessRuleError(
                    "La materia debe pertenecer a un área académica antes "
                    "de poder crear grupos.",
                )

            offering = self._find_or_create_offering(
                subject.institution_id, data.period_id, subject.area_id,
            )
            line = self._find_or_create_line(offering, subject)

            existing_for_line = [
                g for g in self._uow.groups.list_by_offering(offering.id)
                if g.offering_line_id == line.id
            ]
            next_number = max(
                (g.group_number for g in existing_for_line), default=0,
            ) + 1

            group = Group(
                id=generate_id(),
                offering_line_id=line.id,
                subject_id=subject.id,
                group_number=next_number,
                expected_enrollment=data.expected_enrollment,
                modality=data.modality or subject.modality_default,
                schedule_type_id=line.schedule_type_id,
                priority=2,
            )
            self._uow.groups.save(group)

            line.num_groups = len(existing_for_line) + 1
            self._uow.offering_lines.save(line)

            self._uow.commit()
            return group

    def _find_or_create_offering(
        self, institution_id: UUID, period_id: UUID, area_id: UUID,
    ) -> AcademicOffering:
        for offering in self._uow.offerings.list_by_period(institution_id, period_id):
            if offering.area_id == area_id:
                return offering
        offering = AcademicOffering(
            id=generate_id(),
            institution_id=institution_id,
            period_id=period_id,
            area_id=area_id,
            status="draft",
        )
        self._uow.offerings.save(offering)
        return offering

    def _find_or_create_line(
        self, offering: AcademicOffering, subject: Subject,
    ) -> OfferingLine:
        for line in self._uow.offering_lines.list_by_offering(offering.id):
            if line.subject_id == subject.id:
                return line
        existing_types = self._uow.schedule_types.list_by_institution(
            offering.institution_id,
        )
        if not existing_types:
            raise BusinessRuleError(
                "No hay ningún tipo de horario configurado para esta "
                "institución. Crea uno en Configuración antes de crear grupos.",
            )
        line = OfferingLine(
            id=generate_id(),
            offering_id=offering.id,
            subject_id=subject.id,
            num_groups=0,
            expected_enrollment_per_group=0,
            modality=subject.modality_default,
            schedule_type_id=existing_types[0].id,
        )
        self._uow.offering_lines.save(line)
        return line


VALID_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["submitted"],
    "submitted": ["approved", "rejected"],
    "rejected": ["draft"],
    "approved": [],
}


class SubmitOffering:
    """Transition offering from draft → submitted."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, offering_id: UUID) -> AcademicOffering:
        with self._uow:
            entity = self._uow.offerings.get_by_id(offering_id)
            if entity is None:
                raise ResourceNotFoundError("AcademicOffering", offering_id)
            if "submitted" not in VALID_TRANSITIONS.get(entity.status, []):
                raise BusinessRuleError(
                    f"Cannot submit an offering with status '{entity.status}'. "
                    "Only draft offerings can be submitted.",
                )
            entity.status = "submitted"
            self._uow.offerings.save(entity)
            self._uow.commit()
            return entity


class ApproveOffering:
    """Transition offering from submitted → approved.

    Also generates groups from the offering's lines right away, so an
    approved area is immediately schedulable on the next solver run instead
    of silently waiting on the separate "Generar Grupos" step, which had no
    entry point in the sidebar and was easy to miss.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, offering_id: UUID) -> AcademicOffering:
        with self._uow:
            entity = self._uow.offerings.get_by_id(offering_id)
            if entity is None:
                raise ResourceNotFoundError("AcademicOffering", offering_id)
            if "approved" not in VALID_TRANSITIONS.get(entity.status, []):
                raise BusinessRuleError(
                    f"Cannot approve an offering with status '{entity.status}'. "
                    "Only submitted offerings can be approved.",
                )
            entity.status = "approved"
            self._uow.offerings.save(entity)

            lines = self._uow.offering_lines.list_by_offering(offering_id)
            if lines:
                _generate_groups_for_lines(self._uow, entity, lines)

            self._uow.commit()
            return entity


class RejectOffering:
    """Transition offering from submitted → rejected (with observations)."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, offering_id: UUID, observations: str = "") -> AcademicOffering:
        with self._uow:
            entity = self._uow.offerings.get_by_id(offering_id)
            if entity is None:
                raise ResourceNotFoundError("AcademicOffering", offering_id)
            if "rejected" not in VALID_TRANSITIONS.get(entity.status, []):
                raise BusinessRuleError(
                    f"Cannot reject an offering with status '{entity.status}'. "
                    "Only submitted offerings can be rejected.",
                )
            entity.status = "rejected"
            entity.observations = observations
            self._uow.offerings.save(entity)
            self._uow.commit()
            return entity


class ResubmitOffering:
    """Transition offering from rejected → draft (allows resubmission)."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, offering_id: UUID) -> AcademicOffering:
        with self._uow:
            entity = self._uow.offerings.get_by_id(offering_id)
            if entity is None:
                raise ResourceNotFoundError("AcademicOffering", offering_id)
            if "draft" not in VALID_TRANSITIONS.get(entity.status, []):
                raise BusinessRuleError(
                    f"Cannot resubmit an offering with status '{entity.status}'. "
                    "Only rejected offerings can be returned to draft.",
                )
            entity.status = "draft"
            entity.observations = ""
            self._uow.offerings.save(entity)
            self._uow.commit()
            return entity


def _generate_groups_for_lines(
    uow: UnitOfWork,
    offering: AcademicOffering,
    lines: list[OfferingLine],
) -> list[Group]:
    """Create any (line, group_number) not yet materialized as a Group.

    Must run inside a ``with uow:`` block already opened by the caller —
    the ``UnitOfWork`` isn't reentrant, so this never opens its own.
    """
    default_schedule_type_id: UUID | None = None
    if any(line.schedule_type_id is None for line in lines):
        existing_types = uow.schedule_types.list_by_institution(
            offering.institution_id,
        )
        if not existing_types:
            raise BusinessRuleError(
                "No hay ningún tipo de horario (ScheduleType) configurado "
                "para esta institución. Crea uno antes de generar grupos."
            )
        default_schedule_type_id = existing_types[0].id

    existing_groups = uow.groups.list_by_offering(offering.id)
    existing_numbers = {
        (g.offering_line_id, g.group_number) for g in existing_groups
    }

    created: list[Group] = []
    for line in lines:
        st_id = line.schedule_type_id or default_schedule_type_id
        for num in range(1, line.num_groups + 1):
            if (line.id, num) in existing_numbers:
                continue
            group = Group(
                id=generate_id(),
                offering_line_id=line.id,
                subject_id=line.subject_id,
                group_number=num,
                expected_enrollment=line.expected_enrollment_per_group,
                modality=line.modality,
                schedule_type_id=st_id,
            )
            uow.groups.save(group)
            created.append(group)
    return created


class GenerateGroupsFromOffering:
    """Auto-create groups from every line in an offering."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, offering_id: UUID) -> list[Group]:
        with self._uow:
            offering = self._uow.offerings.get_by_id(offering_id)
            if offering is None:
                raise ResourceNotFoundError("AcademicOffering", offering_id)
            lines = self._uow.offering_lines.list_by_offering(offering_id)
            if not lines:
                raise BusinessRuleError(
                    "Offering has no lines to generate groups from."
                )
            created = _generate_groups_for_lines(self._uow, offering, lines)
            self._uow.commit()
            return created
