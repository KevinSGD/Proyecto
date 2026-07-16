"""Write-side use cases for infrastructure entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.application.exceptions import ResourceNotFoundError
from app.core.utils.types import generate_id
from app.domain.entities.infrastructure import (
    Building,
    Classroom,
    ClassroomAvailability,
    Resource,
    RoomResource,
)

if TYPE_CHECKING:
    from app.api.schemas.infrastructure import (
        BuildingCreate,
        BuildingUpdate,
        ClassroomCreate,
        ClassroomUpdate,
        ResourceCreate,
        ResourceUpdate,
    )
    from app.core.utils.types import EntityId
    from app.domain.interfaces.unit_of_work import UnitOfWork


class CreateBuilding:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: BuildingCreate) -> Building:
        with self._uow:
            entity = Building(
                id=generate_id(),
                campus_id=data.campus_id,
                name=data.name,
                code=data.code,
                floors=data.floors,
            )
            saved = self._uow.buildings.save(entity)
            self._uow.commit()
            return saved


class UpdateBuilding:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, building_id: EntityId, data: BuildingUpdate) -> Building:
        with self._uow:
            entity = self._uow.buildings.get_by_id(building_id)
            if entity is None:
                raise ResourceNotFoundError("Building", building_id)
            for field in ("name", "code", "floors", "is_active"):
                val = getattr(data, field, None)
                if val is not None:
                    setattr(entity, field, val)
            saved = self._uow.buildings.save(entity)
            self._uow.commit()
            return saved


class DeleteBuilding:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, building_id: EntityId) -> bool:
        from app.infrastructure.persistence.models.infrastructure_models import (
            ClassroomModel,
        )

        with self._uow:
            session = self._uow._session
            session.query(ClassroomModel).filter(
                ClassroomModel.building_id == building_id,
            ).update({"building_id": None}, synchronize_session=False)

            if not self._uow.buildings.delete(building_id):
                raise ResourceNotFoundError("Building", building_id)
            self._uow.commit()
            return True


class CreateClassroom:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: ClassroomCreate) -> Classroom:
        with self._uow:
            entity = Classroom(
                id=generate_id(),
                institution_id=data.institution_id,
                building_id=data.building_id,
                name=data.name,
                code=data.code,
                capacity=data.capacity,
                floor=data.floor,
                is_virtual=data.is_virtual,
            )
            saved = self._uow.classrooms.save(entity)
            self._uow.commit()
            return saved


class UpdateClassroom:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, classroom_id: EntityId, data: ClassroomUpdate) -> Classroom:
        with self._uow:
            entity = self._uow.classrooms.get_by_id(classroom_id)
            if entity is None:
                raise ResourceNotFoundError("Classroom", classroom_id)
            for field in (
                "name", "code", "capacity", "floor",
                "is_virtual", "is_active", "building_id",
            ):
                val = getattr(data, field, None)
                if val is not None:
                    setattr(entity, field, val)
            saved = self._uow.classrooms.save(entity)
            self._uow.commit()
            return saved


class DeleteClassroom:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, classroom_id: EntityId) -> bool:
        from app.infrastructure.persistence.models.infrastructure_models import (
            ClassroomAvailabilityModel,
            RoomResourceModel,
        )
        from app.infrastructure.persistence.models.schedule import (
            SessionBlockModel,
        )

        with self._uow:
            session = self._uow._session
            session.query(RoomResourceModel).filter(
                RoomResourceModel.classroom_id == classroom_id,
            ).delete(synchronize_session=False)
            session.query(ClassroomAvailabilityModel).filter(
                ClassroomAvailabilityModel.classroom_id == classroom_id,
            ).delete(synchronize_session=False)
            session.query(SessionBlockModel).filter(
                SessionBlockModel.classroom_id == classroom_id,
            ).delete(synchronize_session=False)

            if not self._uow.classrooms.delete(classroom_id):
                raise ResourceNotFoundError("Classroom", classroom_id)
            self._uow.commit()
            return True


class SetClassroomAvailability:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        classroom_id: EntityId,
        period_id: EntityId | None,
        slots: list[dict],
    ) -> int:
        with self._uow:
            entries = [
                ClassroomAvailability(
                    id=generate_id(),
                    classroom_id=classroom_id,
                    period_id=period_id,
                    day_of_week=s["day_of_week"],
                    period=s["period"],
                    is_available=s.get("is_available", True),
                )
                for s in slots
            ]
            count = self._uow.classroom_availabilities.bulk_save(entries)
            self._uow.commit()
            return count


class CreateResource:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: ResourceCreate) -> Resource:
        with self._uow:
            entity = Resource(
                id=generate_id(),
                institution_id=data.institution_id,
                name=data.name,
                code=data.code,
                description=data.description,
            )
            saved = self._uow.resources.save(entity)
            self._uow.commit()
            return saved


class UpdateResource:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, resource_id: EntityId, data: ResourceUpdate) -> Resource:
        with self._uow:
            entity = self._uow.resources.get_by_id(resource_id)
            if entity is None:
                raise ResourceNotFoundError("Resource", resource_id)
            for field in ("name", "code", "description"):
                val = getattr(data, field, None)
                if val is not None:
                    setattr(entity, field, val)
            saved = self._uow.resources.save(entity)
            self._uow.commit()
            return saved


class DeleteResource:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, resource_id: EntityId) -> bool:
        from app.infrastructure.persistence.models.infrastructure_models import (
            RoomResourceModel,
            SubjectResourceRequirementModel,
        )

        with self._uow:
            session = self._uow._session
            session.query(RoomResourceModel).filter(
                RoomResourceModel.resource_id == resource_id,
            ).delete(synchronize_session=False)
            session.query(SubjectResourceRequirementModel).filter(
                SubjectResourceRequirementModel.resource_id == resource_id,
            ).delete(synchronize_session=False)

            if not self._uow.resources.delete(resource_id):
                raise ResourceNotFoundError("Resource", resource_id)
            self._uow.commit()
            return True


class AssignResourceToClassroom:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        classroom_id: EntityId,
        resource_id: EntityId,
        quantity: int = 1,
    ) -> RoomResource:
        from app.infrastructure.persistence.models.infrastructure_models import (
            RoomResourceModel,
        )

        entity = RoomResource(
            id=generate_id(),
            classroom_id=classroom_id,
            resource_id=resource_id,
            quantity=quantity,
        )
        with self._uow:
            model = RoomResourceModel(
                id=entity.id,
                classroom_id=entity.classroom_id,
                resource_id=entity.resource_id,
                quantity=entity.quantity,
            )
            self._uow._session.add(model)
            self._uow.commit()
            return entity
