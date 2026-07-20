"""Concrete repositories for personnel aggregates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.utils.types import EntityId
from app.domain.entities.personnel import (
    Instructor,
    InstructorAvailability,
    InstructorContract,
    InstructorPreference,
    InstructorSpecialty,
)
from app.domain.interfaces.repositories import (
    AvailabilityRepository,
    ContractRepository,
    InstructorRepository,
    PreferenceRepository,
    SpecialtyRepository,
)
from app.infrastructure.persistence.repositories.base import SqlAlchemyRepository

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class SqlInstructorRepository(
    SqlAlchemyRepository[Instructor],
    InstructorRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.personnel import (
            InstructorModel,
        )

        self._model_cls = InstructorModel
        self._entity_cls = Instructor
        super().__init__(session)

    def list_by_institution(
        self, institution_id: EntityId,
    ) -> list[Instructor]:
        models = (
            self._query()
            .filter(self._model_cls.institution_id == institution_id)
            .all()
        )
        return [self._to_entity(m) for m in models]

    def list_by_subject(self, subject_id: EntityId) -> list[Instructor]:
        from app.infrastructure.persistence.models.personnel import (
            InstructorSpecialtyModel,
        )

        instructor_ids = (
            self._session.query(InstructorSpecialtyModel.instructor_id)
            .filter(InstructorSpecialtyModel.subject_id == subject_id)
            .subquery()
        )
        models = (
            self._query()
            .filter(self._model_cls.id.in_(instructor_ids))
            .all()
        )
        return [self._to_entity(m) for m in models]



class SqlAvailabilityRepository(
    SqlAlchemyRepository[InstructorAvailability],
    AvailabilityRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.personnel import (
            InstructorAvailabilityModel,
        )

        self._model_cls = InstructorAvailabilityModel
        self._entity_cls = InstructorAvailability
        super().__init__(session)

    def list_by_instructor(
        self,
        instructor_id: EntityId,
        period_id: EntityId | None = None,
    ) -> list[InstructorAvailability]:
        query = self._query().filter(
            self._model_cls.instructor_id == instructor_id,
        )
        if period_id is not None:
            query = query.filter(self._model_cls.period_id == period_id)
        return [self._to_entity(m) for m in query.all()]

    def bulk_save(self, entries: list[InstructorAvailability]) -> int:
        """Replace availability for every (instructor, period) pair in ``entries``.

        Each call generates fresh ids, so ``session.merge`` (which matches
        on primary key) would insert duplicates instead of updating the
        existing row for a given instructor/period/day/slot — violating the
        unique constraint on a second save. Deleting the prior rows for the
        affected (instructor_id, period_id) pairs first makes this a true
        replace, so re-saving availability is idempotent.
        """
        if not entries:
            return 0
        pairs = {(e.instructor_id, e.period_id) for e in entries}
        for instructor_id, period_id in pairs:
            self._session.query(self._model_cls).filter(
                self._model_cls.instructor_id == instructor_id,
                self._model_cls.period_id == period_id,
            ).delete(synchronize_session=False)
        for entry in entries:
            self._session.add(self._to_model(entry))
        self._session.flush()
        return len(entries)


class SqlSpecialtyRepository(
    SqlAlchemyRepository[InstructorSpecialty],
    SpecialtyRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.personnel import (
            InstructorSpecialtyModel,
        )

        self._model_cls = InstructorSpecialtyModel
        self._entity_cls = InstructorSpecialty
        super().__init__(session)

    def list_by_instructor(
        self, instructor_id: EntityId,
    ) -> list[InstructorSpecialty]:
        models = (
            self._query()
            .filter(self._model_cls.instructor_id == instructor_id)
            .all()
        )
        return [self._to_entity(m) for m in models]

    def list_by_subject(
        self, subject_id: EntityId,
    ) -> list[InstructorSpecialty]:
        models = (
            self._query()
            .filter(self._model_cls.subject_id == subject_id)
            .all()
        )
        return [self._to_entity(m) for m in models]


class SqlContractRepository(
    SqlAlchemyRepository[InstructorContract],
    ContractRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.personnel import (
            InstructorContractModel,
        )

        self._model_cls = InstructorContractModel
        self._entity_cls = InstructorContract
        super().__init__(session)

    def get_active(
        self, instructor_id: EntityId,
    ) -> InstructorContract | None:
        model = (
            self._query()
            .filter(
                self._model_cls.instructor_id == instructor_id,
                self._model_cls.is_active.is_(True),
            )
            .first()
        )
        return self._to_entity(model) if model else None


class SqlPreferenceRepository(
    SqlAlchemyRepository[InstructorPreference],
    PreferenceRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.personnel import (
            InstructorPreferenceModel,
        )

        self._model_cls = InstructorPreferenceModel
        self._entity_cls = InstructorPreference
        super().__init__(session)

    def list_by_instructor(
        self,
        instructor_id: EntityId,
        period_id: EntityId | None = None,
    ) -> list[InstructorPreference]:
        query = self._query().filter(
            self._model_cls.instructor_id == instructor_id,
        )
        if period_id is not None:
            query = query.filter(self._model_cls.period_id == period_id)
        return [self._to_entity(m) for m in query.all()]
