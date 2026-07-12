"""Read-side use cases for infrastructure entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.application.exceptions import ResourceNotFoundError

if TYPE_CHECKING:
    from app.core.utils.types import EntityId
    from app.domain.entities.infrastructure import (
        Building,
        Classroom,
        ClassroomAvailability,
        Resource,
    )
    from app.domain.interfaces.unit_of_work import UnitOfWork


class GetBuilding:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, building_id: EntityId) -> Building:
        with self._uow:
            entity = self._uow.buildings.get_by_id(building_id)
            if entity is None:
                raise ResourceNotFoundError("Building", building_id)
            return entity


class ListBuildings:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, campus_id: EntityId) -> list[Building]:
        with self._uow:
            return self._uow.buildings.list_by_campus(campus_id)


class GetClassroom:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, classroom_id: EntityId) -> Classroom:
        with self._uow:
            entity = self._uow.classrooms.get_by_id(classroom_id)
            if entity is None:
                raise ResourceNotFoundError("Classroom", classroom_id)
            return entity


class ListClassrooms:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, institution_id: EntityId) -> list[Classroom]:
        with self._uow:
            return self._uow.classrooms.list_by_institution(institution_id)


class ListClassroomsByBuilding:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, building_id: EntityId) -> list[Classroom]:
        with self._uow:
            return self._uow.classrooms.list_by_building(building_id)


class ListClassroomsByCapacity:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self, institution_id: EntityId, min_capacity: int,
    ) -> list[Classroom]:
        with self._uow:
            return self._uow.classrooms.list_by_min_capacity(
                institution_id, min_capacity,
            )


class GetClassroomAvailability:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        classroom_id: EntityId,
        period_id: EntityId | None = None,
    ) -> list[ClassroomAvailability]:
        with self._uow:
            return self._uow.classroom_availabilities.list_by_classroom(
                classroom_id, period_id,
            )


class GetResource:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, resource_id: EntityId) -> Resource:
        with self._uow:
            entity = self._uow.resources.get_by_id(resource_id)
            if entity is None:
                raise ResourceNotFoundError("Resource", resource_id)
            return entity


class ListResources:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, institution_id: EntityId) -> list[Resource]:
        with self._uow:
            return self._uow.resources.list_all()


class ListClassroomResources:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, classroom_id: EntityId) -> list[Resource]:
        with self._uow:
            return self._uow.resources.list_by_classroom(classroom_id)
