"""Read-side use cases for academic entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.application.exceptions.application_exceptions import ResourceNotFoundError

if TYPE_CHECKING:
    from uuid import UUID

    from app.domain.entities.academic import AcademicArea, Subject
    from app.domain.interfaces.unit_of_work import UnitOfWork


class ListAreas:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, institution_id: UUID) -> list[AcademicArea]:
        with self._uow:
            return self._uow.academic_areas.list_by_institution(institution_id)


class GetArea:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, area_id: UUID) -> AcademicArea:
        with self._uow:
            entity = self._uow.academic_areas.get_by_id(area_id)
            if entity is None:
                raise ResourceNotFoundError("AcademicArea", area_id)
            return entity


class ListSubjects:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, institution_id: UUID) -> list[Subject]:
        with self._uow:
            return self._uow.subjects.list_by_institution(institution_id)


class GetSubject:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, subject_id: UUID) -> Subject:
        with self._uow:
            entity = self._uow.subjects.get_by_id(subject_id)
            if entity is None:
                raise ResourceNotFoundError("Subject", subject_id)
            return entity
