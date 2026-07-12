"""Concrete repositories for physical infrastructure aggregates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.utils.types import EntityId
from app.domain.entities.infrastructure import (
    Building,
    Classroom,
    ClassroomAvailability,
    Resource,
)
from app.domain.interfaces.repositories import (
    BuildingRepository,
    ClassroomAvailabilityRepository,
    ClassroomRepository,
    ResourceRepository,
)
from app.infrastructure.persistence.repositories.base import SqlAlchemyRepository

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class SqlBuildingRepository(
    SqlAlchemyRepository[Building],
    BuildingRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.infrastructure_models import (
            BuildingModel,
        )

        self._model_cls = BuildingModel
        self._entity_cls = Building
        super().__init__(session)

    def list_by_campus(self, campus_id: EntityId) -> list[Building]:
        models = (
            self._query()
            .filter(self._model_cls.campus_id == campus_id)
            .all()
        )
        return [self._to_entity(m) for m in models]


class SqlClassroomRepository(
    SqlAlchemyRepository[Classroom],
    ClassroomRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.infrastructure_models import (
            ClassroomModel,
        )

        self._model_cls = ClassroomModel
        self._entity_cls = Classroom
        super().__init__(session)

    def list_by_institution(
        self, institution_id: EntityId,
    ) -> list[Classroom]:
        models = (
            self._query()
            .filter(self._model_cls.institution_id == institution_id)
            .all()
        )
        return [self._to_entity(m) for m in models]

    def list_by_min_capacity(
        self,
        institution_id: EntityId,
        min_capacity: int,
    ) -> list[Classroom]:
        models = (
            self._query()
            .filter(
                self._model_cls.institution_id == institution_id,
                self._model_cls.capacity >= min_capacity,
            )
            .all()
        )
        return [self._to_entity(m) for m in models]

    def list_by_building(self, building_id: EntityId) -> list[Classroom]:
        models = (
            self._query()
            .filter(self._model_cls.building_id == building_id)
            .all()
        )
        return [self._to_entity(m) for m in models]


class SqlClassroomAvailabilityRepository(
    SqlAlchemyRepository[ClassroomAvailability],
    ClassroomAvailabilityRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.infrastructure_models import (
            ClassroomAvailabilityModel,
        )

        self._model_cls = ClassroomAvailabilityModel
        self._entity_cls = ClassroomAvailability
        super().__init__(session)

    def list_by_classroom(
        self,
        classroom_id: EntityId,
        period_id: EntityId | None = None,
    ) -> list[ClassroomAvailability]:
        query = self._query().filter(
            self._model_cls.classroom_id == classroom_id,
        )
        if period_id is not None:
            query = query.filter(self._model_cls.period_id == period_id)
        return [self._to_entity(m) for m in query.all()]

    def bulk_save(self, entries: list[ClassroomAvailability]) -> int:
        count = 0
        for entry in entries:
            model = self._to_model(entry)
            self._session.merge(model)
            count += 1
        self._session.flush()
        return count


class SqlResourceRepository(
    SqlAlchemyRepository[Resource],
    ResourceRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.infrastructure_models import (
            ResourceModel,
        )

        self._model_cls = ResourceModel
        self._entity_cls = Resource
        super().__init__(session)

    def list_by_classroom(self, classroom_id: EntityId) -> list[Resource]:
        from app.infrastructure.persistence.models.infrastructure_models import (
            RoomResourceModel,
        )

        resource_ids = (
            self._session.query(RoomResourceModel.resource_id)
            .filter(RoomResourceModel.classroom_id == classroom_id)
            .subquery()
        )
        models = (
            self._query()
            .filter(self._model_cls.id.in_(resource_ids))
            .all()
        )
        return [self._to_entity(m) for m in models]

    def list_required_by_subject(
        self, subject_id: EntityId,
    ) -> list[Resource]:
        from app.infrastructure.persistence.models.infrastructure_models import (
            SubjectResourceRequirementModel,
        )

        resource_ids = (
            self._session.query(
                SubjectResourceRequirementModel.resource_id,
            )
            .filter(
                SubjectResourceRequirementModel.subject_id == subject_id,
                SubjectResourceRequirementModel.is_mandatory.is_(True),
            )
            .subquery()
        )
        models = (
            self._query()
            .filter(self._model_cls.id.in_(resource_ids))
            .all()
        )
        return [self._to_entity(m) for m in models]

    def list_preferred_by_subject(
        self, subject_id: EntityId,
    ) -> list[Resource]:
        from app.infrastructure.persistence.models.infrastructure_models import (
            SubjectResourceRequirementModel,
        )

        resource_ids = (
            self._session.query(
                SubjectResourceRequirementModel.resource_id,
            )
            .filter(
                SubjectResourceRequirementModel.subject_id == subject_id,
                SubjectResourceRequirementModel.is_mandatory.is_(False),
            )
            .subquery()
        )
        models = (
            self._query()
            .filter(self._model_cls.id.in_(resource_ids))
            .all()
        )
        return [self._to_entity(m) for m in models]
