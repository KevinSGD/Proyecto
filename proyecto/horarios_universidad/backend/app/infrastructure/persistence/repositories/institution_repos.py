"""Concrete repositories for institution-level aggregates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.utils.types import EntityId
from app.domain.entities.institution import AcademicPeriod, Campus, Institution
from app.domain.interfaces.repositories import (
    AcademicPeriodRepository,
    CampusRepository,
    InstitutionRepository,
)
from app.infrastructure.persistence.repositories.base import SqlAlchemyRepository

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class SqlInstitutionRepository(
    SqlAlchemyRepository[Institution],
    InstitutionRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.institution import (
            InstitutionModel,
        )

        self._model_cls = InstitutionModel
        self._entity_cls = Institution
        super().__init__(session)

    def get_by_abbreviation(self, abbreviation: str) -> Institution | None:
        model = (
            self._query()
            .filter(self._model_cls.abbreviation == abbreviation)
            .first()
        )
        return self._to_entity(model) if model else None


class SqlCampusRepository(
    SqlAlchemyRepository[Campus],
    CampusRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.institution import CampusModel

        self._model_cls = CampusModel
        self._entity_cls = Campus
        super().__init__(session)

    def list_by_institution(self, institution_id: EntityId) -> list[Campus]:
        models = (
            self._query()
            .filter(self._model_cls.institution_id == institution_id)
            .all()
        )
        return [self._to_entity(m) for m in models]


class SqlAcademicPeriodRepository(
    SqlAlchemyRepository[AcademicPeriod],
    AcademicPeriodRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.institution import (
            AcademicPeriodModel,
        )

        self._model_cls = AcademicPeriodModel
        self._entity_cls = AcademicPeriod
        super().__init__(session)

    def list_by_institution(
        self, institution_id: EntityId,
    ) -> list[AcademicPeriod]:
        models = (
            self._query()
            .filter(self._model_cls.institution_id == institution_id)
            .all()
        )
        return [self._to_entity(m) for m in models]

    def get_active(self, institution_id: EntityId) -> AcademicPeriod | None:
        model = (
            self._query()
            .filter(
                self._model_cls.institution_id == institution_id,
                self._model_cls.is_active.is_(True),
            )
            .first()
        )
        return self._to_entity(model) if model else None
