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

    from app.api.schemas.offering import (
        GroupCreate,
        OfferingCreate,
        OfferingLineCreate,
        OfferingLineUpdate,
        OfferingUpdate,
        ScheduleTypeCreate,
        ScheduleTypeUpdate,
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


class DeleteGroup:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, group_id: UUID) -> bool:
        with self._uow:
            deleted = self._uow.groups.delete(group_id)
            if not deleted:
                raise ResourceNotFoundError("Group", group_id)
            self._uow.commit()
            return True


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
            created: list[Group] = []
            for line in lines:
                st_id = line.schedule_type_id or generate_id()
                for num in range(1, line.num_groups + 1):
                    group = Group(
                        id=generate_id(),
                        offering_line_id=line.id,
                        subject_id=line.subject_id,
                        group_number=num,
                        expected_enrollment=line.expected_enrollment_per_group,
                        modality=line.modality,
                        schedule_type_id=st_id,
                    )
                    self._uow.groups.save(group)
                    created.append(group)
            self._uow.commit()
            return created
