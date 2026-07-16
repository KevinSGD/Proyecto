"""Concrete repositories for academic structure aggregates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.utils.types import EntityId
from app.domain.entities.academic import AcademicArea, Subject
from app.domain.interfaces.repositories import (
    AcademicAreaRepository,
    SubjectRepository,
)
from app.infrastructure.persistence.repositories.base import SqlAlchemyRepository

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class SqlAcademicAreaRepository(
    SqlAlchemyRepository[AcademicArea],
    AcademicAreaRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.academic import (
            AcademicAreaModel,
        )

        self._model_cls = AcademicAreaModel
        self._entity_cls = AcademicArea
        super().__init__(session)

    def list_by_institution(
        self, institution_id: EntityId,
    ) -> list[AcademicArea]:
        models = (
            self._query()
            .filter(self._model_cls.institution_id == institution_id)
            .all()
        )
        return [self._to_entity(m) for m in models]


class SqlSubjectRepository(
    SqlAlchemyRepository[Subject],
    SubjectRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.academic import SubjectModel

        self._model_cls = SubjectModel
        self._entity_cls = Subject
        super().__init__(session)

    def list_by_institution(
        self, institution_id: EntityId,
    ) -> list[Subject]:
        models = (
            self._query()
            .filter(self._model_cls.institution_id == institution_id)
            .all()
        )
        return [self._to_entity(m) for m in models]

    def list_by_area(self, area_id: EntityId) -> list[Subject]:
        models = (
            self._query()
            .filter(self._model_cls.area_id == area_id)
            .all()
        )
        return [self._to_entity(m) for m in models]
