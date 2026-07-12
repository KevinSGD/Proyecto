"""Read-side use cases for institution entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.application.exceptions.application_exceptions import ResourceNotFoundError

if TYPE_CHECKING:
    from uuid import UUID

    from app.domain.entities.institution import AcademicPeriod, Campus, Institution
    from app.domain.interfaces.unit_of_work import UnitOfWork


class GetInstitution:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, institution_id: UUID) -> Institution:
        with self._uow:
            entity = self._uow.institutions.get_by_id(institution_id)
            if entity is None:
                raise ResourceNotFoundError("Institution", institution_id)
            return entity


class ListInstitutions:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self) -> list[Institution]:
        with self._uow:
            return self._uow.institutions.list_all()


class GetCampus:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, campus_id: UUID) -> Campus:
        with self._uow:
            entity = self._uow.campuses.get_by_id(campus_id)
            if entity is None:
                raise ResourceNotFoundError("Campus", campus_id)
            return entity


class ListCampuses:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, institution_id: UUID) -> list[Campus]:
        with self._uow:
            return self._uow.campuses.list_by_institution(institution_id)


class GetAcademicPeriod:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, period_id: UUID) -> AcademicPeriod:
        with self._uow:
            entity = self._uow.academic_periods.get_by_id(period_id)
            if entity is None:
                raise ResourceNotFoundError("AcademicPeriod", period_id)
            return entity


class ListAcademicPeriods:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, institution_id: UUID) -> list[AcademicPeriod]:
        with self._uow:
            return self._uow.academic_periods.list_by_institution(institution_id)


class GetActiveAcademicPeriod:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, institution_id: UUID) -> AcademicPeriod:
        with self._uow:
            entity = self._uow.academic_periods.get_active(institution_id)
            if entity is None:
                raise ResourceNotFoundError("AcademicPeriod", f"active for {institution_id}")
            return entity
