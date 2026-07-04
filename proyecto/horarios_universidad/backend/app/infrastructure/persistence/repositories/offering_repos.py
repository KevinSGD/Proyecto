"""Concrete repositories for offering and scheduling aggregates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.utils.types import EntityId
from app.domain.entities.offering import AcademicOffering, OfferingLine
from app.domain.entities.scheduling import Group, ScheduleType
from app.domain.interfaces.repositories import (
    GroupRepository,
    OfferingLineRepository,
    OfferingRepository,
    ScheduleTypeRepository,
)
from app.infrastructure.persistence.repositories.base import SqlAlchemyRepository

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class SqlOfferingRepository(
    SqlAlchemyRepository[AcademicOffering],
    OfferingRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.offering import (
            AcademicOfferingModel,
        )

        self._model_cls = AcademicOfferingModel
        self._entity_cls = AcademicOffering
        super().__init__(session)

    def list_by_period(
        self,
        institution_id: EntityId,
        period_id: EntityId,
    ) -> list[AcademicOffering]:
        models = (
            self._query()
            .filter(
                self._model_cls.institution_id == institution_id,
                self._model_cls.period_id == period_id,
            )
            .all()
        )
        return [self._to_entity(m) for m in models]


class SqlOfferingLineRepository(
    SqlAlchemyRepository[OfferingLine],
    OfferingLineRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.offering import (
            OfferingLineModel,
        )

        self._model_cls = OfferingLineModel
        self._entity_cls = OfferingLine
        super().__init__(session)

    def list_by_offering(
        self, offering_id: EntityId,
    ) -> list[OfferingLine]:
        models = (
            self._query()
            .filter(self._model_cls.offering_id == offering_id)
            .all()
        )
        return [self._to_entity(m) for m in models]


class SqlGroupRepository(
    SqlAlchemyRepository[Group],
    GroupRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.scheduling import GroupModel

        self._model_cls = GroupModel
        self._entity_cls = Group
        super().__init__(session)

    def list_by_offering(self, offering_id: EntityId) -> list[Group]:
        from app.infrastructure.persistence.models.offering import (
            OfferingLineModel,
        )

        line_ids = (
            self._session.query(OfferingLineModel.id)
            .filter(OfferingLineModel.offering_id == offering_id)
            .subquery()
        )
        models = (
            self._query()
            .filter(self._model_cls.offering_line_id.in_(line_ids))
            .all()
        )
        return [self._to_entity(m) for m in models]

    def list_by_period(
        self,
        institution_id: EntityId,
        period_id: EntityId,
    ) -> list[Group]:
        from app.infrastructure.persistence.models.offering import (
            AcademicOfferingModel,
            OfferingLineModel,
        )

        offering_ids = (
            self._session.query(AcademicOfferingModel.id)
            .filter(
                AcademicOfferingModel.institution_id == institution_id,
                AcademicOfferingModel.period_id == period_id,
            )
            .subquery()
        )
        line_ids = (
            self._session.query(OfferingLineModel.id)
            .filter(OfferingLineModel.offering_id.in_(offering_ids))
            .subquery()
        )
        models = (
            self._query()
            .filter(self._model_cls.offering_line_id.in_(line_ids))
            .all()
        )
        return [self._to_entity(m) for m in models]


class SqlScheduleTypeRepository(
    SqlAlchemyRepository[ScheduleType],
    ScheduleTypeRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.scheduling import (
            ScheduleTypeModel,
        )

        self._model_cls = ScheduleTypeModel
        self._entity_cls = ScheduleType
        super().__init__(session)

    def list_by_institution(
        self, institution_id: EntityId,
    ) -> list[ScheduleType]:
        models = (
            self._query()
            .filter(self._model_cls.institution_id == institution_id)
            .all()
        )
        return [self._to_entity(m) for m in models]
