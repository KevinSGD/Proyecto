"""Write-side use cases for institution entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.application.exceptions.application_exceptions import ResourceNotFoundError
from app.core.utils.types import generate_id
from app.domain.entities.institution import AcademicPeriod, Institution

if TYPE_CHECKING:
    from uuid import UUID

    from app.api.schemas.institution import (
        AcademicPeriodCreate,
        InstitutionCreate,
        InstitutionUpdate,
    )
    from app.domain.interfaces.unit_of_work import UnitOfWork


class CreateInstitution:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: InstitutionCreate) -> Institution:
        with self._uow:
            entity = Institution(
                id=generate_id(),
                name=data.name,
                abbreviation=data.abbreviation,
                address=data.address or "",
                email=data.email or "",
                phone=data.phone or "",
                website=data.website or "",
                logo_url=data.logo_url or "",
            )
            self._uow.institutions.save(entity)
            self._uow.commit()
            return entity


class UpdateInstitution:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, institution_id: UUID, data: InstitutionUpdate) -> Institution:
        with self._uow:
            entity = self._uow.institutions.get_by_id(institution_id)
            if entity is None:
                raise ResourceNotFoundError("Institution", institution_id)
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(entity, field, value)
            self._uow.institutions.save(entity)
            self._uow.commit()
            return entity


class DeleteInstitution:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, institution_id: UUID) -> bool:
        with self._uow:
            deleted = self._uow.institutions.delete(institution_id)
            if not deleted:
                raise ResourceNotFoundError("Institution", institution_id)
            self._uow.commit()
            return True


class CreateAcademicPeriod:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: AcademicPeriodCreate) -> AcademicPeriod:
        with self._uow:
            entity = AcademicPeriod(
                id=generate_id(),
                institution_id=data.institution_id,
                name=data.name,
                year=data.year,
                period_number=data.period_number,
                start_date=data.start_date,
                end_date=data.end_date,
            )
            self._uow.academic_periods.save(entity)
            self._uow.commit()
            return entity
