"""Read-side use cases for offering and scheduling entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.application.exceptions.application_exceptions import ResourceNotFoundError

if TYPE_CHECKING:
    from uuid import UUID

    from app.domain.entities.offering import AcademicOffering, OfferingLine
    from app.domain.entities.scheduling import Group, ScheduleType
    from app.domain.interfaces.unit_of_work import UnitOfWork

__all__ = [
    "GetOffering",
    "ListOfferings",
    "GetOfferingDetail",
    "ListOfferingLines",
    "ListScheduleTypes",
    "GetScheduleType",
    "ListGroups",
    "GetGroup",
]


# -- AcademicOffering --------------------------------------------------------


class GetOffering:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, offering_id: UUID) -> AcademicOffering:
        with self._uow:
            entity = self._uow.offerings.get_by_id(offering_id)
            if entity is None:
                raise ResourceNotFoundError("AcademicOffering", offering_id)
            return entity


class ListOfferings:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self, institution_id: UUID, period_id: UUID,
    ) -> list[AcademicOffering]:
        with self._uow:
            return self._uow.offerings.list_by_period(institution_id, period_id)


class GetOfferingDetail:
    """Return an offering together with its lines."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self, offering_id: UUID,
    ) -> tuple[AcademicOffering, list[OfferingLine]]:
        with self._uow:
            entity = self._uow.offerings.get_by_id(offering_id)
            if entity is None:
                raise ResourceNotFoundError("AcademicOffering", offering_id)
            lines = self._uow.offering_lines.list_by_offering(offering_id)
            return entity, lines


# -- OfferingLine -------------------------------------------------------------


class ListOfferingLines:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, offering_id: UUID) -> list[OfferingLine]:
        with self._uow:
            return self._uow.offering_lines.list_by_offering(offering_id)


# -- ScheduleType -------------------------------------------------------------


class ListScheduleTypes:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, institution_id: UUID) -> list[ScheduleType]:
        with self._uow:
            return self._uow.schedule_types.list_by_institution(institution_id)


class GetScheduleType:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, st_id: UUID) -> ScheduleType:
        with self._uow:
            entity = self._uow.schedule_types.get_by_id(st_id)
            if entity is None:
                raise ResourceNotFoundError("ScheduleType", st_id)
            return entity


# -- Group --------------------------------------------------------------------


class ListGroups:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, institution_id: UUID, period_id: UUID) -> list[Group]:
        with self._uow:
            return self._uow.groups.list_by_period(institution_id, period_id)


class GetGroup:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, group_id: UUID) -> Group:
        with self._uow:
            entity = self._uow.groups.get_by_id(group_id)
            if entity is None:
                raise ResourceNotFoundError("Group", group_id)
            return entity
