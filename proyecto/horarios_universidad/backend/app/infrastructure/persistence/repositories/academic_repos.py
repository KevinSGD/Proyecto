"""Concrete repositories for academic structure aggregates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.utils.types import EntityId
from app.domain.entities.academic import (
    AcademicArea,
    Department,
    PlanSubject,
    StudyPlan,
    Subject,
)
from app.domain.interfaces.repositories import (
    AcademicAreaRepository,
    DepartmentRepository,
    PlanSubjectRepository,
    StudyPlanRepository,
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


class SqlDepartmentRepository(
    SqlAlchemyRepository[Department],
    DepartmentRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.academic import (
            DepartmentModel,
        )

        self._model_cls = DepartmentModel
        self._entity_cls = Department
        super().__init__(session)

    def list_by_area(self, area_id: EntityId) -> list[Department]:
        models = (
            self._query()
            .filter(self._model_cls.area_id == area_id)
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

    def list_by_study_plan(
        self, study_plan_id: EntityId,
    ) -> list[Subject]:
        from app.infrastructure.persistence.models.academic import (
            PlanSubjectModel,
        )

        subject_ids = (
            self._session.query(PlanSubjectModel.subject_id)
            .filter(PlanSubjectModel.study_plan_id == study_plan_id)
            .subquery()
        )
        models = (
            self._query()
            .filter(self._model_cls.id.in_(subject_ids))
            .all()
        )
        return [self._to_entity(m) for m in models]


class SqlStudyPlanRepository(
    SqlAlchemyRepository[StudyPlan],
    StudyPlanRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.academic import StudyPlanModel

        self._model_cls = StudyPlanModel
        self._entity_cls = StudyPlan
        super().__init__(session)

    def list_by_program(self, program_id: EntityId) -> list[StudyPlan]:
        models = (
            self._query()
            .filter(self._model_cls.program_id == program_id)
            .all()
        )
        return [self._to_entity(m) for m in models]

    def get_active(self, program_id: EntityId) -> StudyPlan | None:
        model = (
            self._query()
            .filter(
                self._model_cls.program_id == program_id,
                self._model_cls.is_active.is_(True),
            )
            .first()
        )
        return self._to_entity(model) if model else None


class SqlPlanSubjectRepository(
    SqlAlchemyRepository[PlanSubject],
    PlanSubjectRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.academic import (
            PlanSubjectModel,
        )

        self._model_cls = PlanSubjectModel
        self._entity_cls = PlanSubject
        super().__init__(session)

    def list_by_study_plan(
        self, study_plan_id: EntityId,
    ) -> list[PlanSubject]:
        models = (
            self._query()
            .filter(self._model_cls.study_plan_id == study_plan_id)
            .all()
        )
        return [self._to_entity(m) for m in models]

    def list_by_semester(
        self,
        study_plan_id: EntityId,
        semester: int,
    ) -> list[PlanSubject]:
        models = (
            self._query()
            .filter(
                self._model_cls.study_plan_id == study_plan_id,
                self._model_cls.semester == semester,
            )
            .all()
        )
        return [self._to_entity(m) for m in models]
